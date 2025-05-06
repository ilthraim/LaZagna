import re
import sys
import argparse
from collections import defaultdict

def read_file(fn):
    with open(fn) as f:
        return f.read().splitlines()

def write_file(fn, lines):
    with open(fn, 'w') as f:
        f.write('\n'.join(lines)+'\n')

def debug_dump_head(lines, n=10):
    print(f"=== first {n} lines of the file ===")
    for i,l in enumerate(lines[:n]):
        print(f"{i+1:2d}: {l!r}")
    print("==================================\n")

def find_layers(lines):
    """Return sorted list of layer‐IDs found in any wire or instance name."""
    layer_set = set()
    pat = re.compile(r'_layer_(\d+)_')
    for l in lines:
        for m in pat.finditer(l):
            layer_set.add(int(m.group(1)))
    return sorted(layer_set)

def collect_wires(lines):
    """Return dict wire_name -> declaration line"""
    wires = {}
    pat = re.compile(r'^\s*wire\s+([^;]+);\s*$')
    for l in lines:
        m = pat.match(l)
        if m:
            name = m.group(1).strip().split()[-1]
            wires[name] = l

    # debug print
    print(f"Collected {len(wires)} wire declarations (showing up to 5):")
    for i,(nm,decl) in enumerate(wires.items()):
        if i>=5: break
        print(f"  {nm:40s} -> {decl}")
    print()
    return wires


def collect_instances(lines):
    """
    Scan for ANY instantiation that contains '_layer_<N>_' 
    in its module or instance name, grab the entire block
    from the line with the '(' down through the matching ');'
    """
    insts = []
    buf = []
    paren_depth = 0

    # match a line like "   grid_io_top grid_io_top_1_9_layer_0_ ("
    start_pat = re.compile(r'^\s*\w+\s+\w+.*_layer_\d+_.*\(')

    for l in lines:
        if not buf:
            # are we at the start of a layer‐qualified instance?
            if start_pat.match(l):
                buf = [l]
                # compute initial parenthesis depth
                paren_depth = l.count('(') - l.count(')')
                # if it closed on the same line, flush it immediately
                if paren_depth == 0:
                    insts.append(''.join(buf))
                    buf = []
        else:
            # we are inside an inst block; keep accumulating
            buf.append(l)
            paren_depth += l.count('(') - l.count(')')
            # once we've balanced all parentheses, that's the end
            if paren_depth == 0:
                insts.append(''.join(buf))
                buf = []

    # debug
    print(f"Collected {len(insts)} layer‐qualified instantiations.")
    if insts:
        print("=== sample instance ===")
        print(insts[0])
        print("=======================\n")
    return insts

def layer_of_name(name):
    """Return layer id embedded in name, or None."""
    m = re.search(r'_layer_(\d+)_', name)
    return int(m.group(1)) if m else None

def group_wires_by_layer(wires):
    by_layer = defaultdict(dict)
    for nm, decl in wires.items():
        L = layer_of_name(nm)
        if L is not None:
            by_layer[L][nm] = decl
    return by_layer

def group_insts_by_layer(instances):
    by_layer = defaultdict(list)
    for inst in instances:
        # look for any *_layer_N_ in the instance text
        Ls = set(int(m) for m in re.findall(r'_layer_(\d+)_ \(', inst))
        if len(Ls)==1:
            by_layer[Ls.pop()].append(inst)
        else:
            # ambiguous or global; assign to None
            by_layer[None].append(inst)
    return by_layer

def find_cross_wires(insts_by_layer):
    """
    Build a map net -> set(layers) by scanning all '(net)' occurrences
    in each instance.  A net is cross-layer if it shows up in >=2 layers.
    """
    usage = defaultdict(set)

    cross_sizes = defaultdict()

    # find every (...) and grab the inside as a net name
    pat = re.compile(r'\s*\w+\((\w+)(\[\d+:\d+\])?\s*')

    for layer, inst_list in insts_by_layer.items():
        for inst in inst_list:
            for m in pat.finditer(inst):
                net = m.group(1)
                size = m.group(2) or '[0:0]'
                usage[net].add(layer)
                if net not in cross_sizes.keys():
                    cross_sizes[net] = size
                else:
                    size_regex = re.compile(r'\[(\d+):(\d+)\]')
                    found_size = size_regex.match(cross_sizes[net])
                    new_size = size_regex.match(size)
                    if found_size and new_size:
                        size_str = '['
                        # check if the sizes are the same
                        if int(found_size.group(1)) > int(new_size.group(1)):
                            size_str += new_size.group(1) + ':'
                        else:
                            size_str += found_size.group(1) + ':'

                        if int(found_size.group(2)) < int(new_size.group(2)):
                            size_str += new_size.group(2) + ']'
                        else:
                            size_str += found_size.group(2) + ']'

                        cross_sizes[net] = size_str
    # debug: print the first few nets and their layer‐usage
    print(f"Total distinct nets seen in instances: {len(usage)}")
    for i,(net,lset) in enumerate(usage.items()):
        if i >= 10: break
        print(f"  {net:30s} with size: {cross_sizes[net]} used in layers {sorted(lset)}")
    print()

    # now pick nets that appear in 2+ real layers
    cross = { net:[L for L in lset if L is not None] for net,lset in usage.items()
              if len({L for L in lset if L is not None}) > 1 }
    
    # Keep only the cross sizes for the cross wires
    cross_sizes_ret = { net: cross_sizes[net] for net in cross if net in cross_sizes.keys() }

    # debug print first few cross wires and their sizes
    print(f"Found {len(cross_sizes_ret)} cross-layer wires (showing up to 10):")
    for i,(net,size) in enumerate(cross_sizes_ret.items()):
        if i >= 5: break
        print(f"  {net:30s} with size: {size}")

    # print first 5 elements of cross 
    print(f"Found {len(cross)} cross-layer wires (showing up to 5):")
    for i,net in enumerate(cross):
        if i >= 5: break
        print(" ", net, "layers=", sorted(usage[net]))
    print()

    # print(f"Found {len(cross)} cross-layer wires (showing up to 10):")
    # for net in sorted(cross)[:10]:
    #     print(" ", net, "layers=", sorted(usage[net]))
    # print()
    return cross, cross_sizes_ret

def make_submodule(layer, wires, instances, cross_wires, cross_sizes, global_ports):
    """
    Generate the text of fpga_layer_{layer}.v
     - global_ports is a list of (direction, name, width) from the original top module
    """
    name = f"fpga_layer_{layer}"
    lines = []
    # ports: 
    #  * all global_ports (pReset, prog_clk, ...) always passed down
    #  * all cross_wires that belong to this layer: 
    ports = []
    for direction,name0,width in global_ports:
        ports.append(f"{direction} {width} {name0}")
    # add cross-layer wires as ports
    for w, wire_layers in cross.items():
        if layer in wire_layers:
            # Default to "inout" for now
            wire_direction = "inout"

            if f"layer_{layer}_" in w:
                # this wire is local to this layer, so it's an output to another layer
                wire_direction = "output"
            else:
                # this wire is cross-layer, so it's an input to this layer
                wire_direction = "input"
            ports.append(f"{wire_direction} {cross_sizes[w]} {w}")
    # module header
    pl = ',\n    '.join(ports)
    lines.append(f"module {name}(\n    {pl}\n);")
    lines.append("")
    # internal wires = all wires assigned to this layer minus cross
    for w,decl in wires.items():
        if w not in cross_wires:
            lines.append("  " + decl)
    lines.append("")
    # instances
    for inst in instances:
        lines.append("  " + inst.replace("\n", "\n  "))
        lines.append("")
    lines.append(f"endmodule // {name}")
    return lines

def extract_global_ports(lines):
    """
    1) Gather all lines between 'module fpga_top(' and the matching ');'
    2) Split on commas to get the ordered list of port names
    3) For each port name, find its input/output/inout declaration elsewhere
       and record (direction, name, width)
    """
    # --- 1) Grab the header lines ---
    header_lines = []
    in_hdr = False
    for l in lines:
        # strip comments for safety
        code = l.split('//',1)[0]
        if not in_hdr:
            if re.match(r'\s*module\s+fpga_top\s*\(', code):
                in_hdr = True
                # drop everything up to "("
                code = code[code.index('(')+1:]
            else:
                continue
        # we are inside the header
        # if this line ends the header, clip off the ');'
        if ');' in code:
            code = code[:code.index(');')]
            header_lines.append(code)
            break
        header_lines.append(code)

    hdr = " ".join(header_lines)
    # --- 2) Split on commas to get port names ---
    port_names = [p.strip() for p in hdr.split(',') if p.strip()]
    if not port_names:
        print("ERROR: could not parse module header ports.")
        return []

    print("Header port list:", port_names)

    # --- 3) For each name, find its direction & width ---
    decl_pat = re.compile(r'^(input|output|inout)\s*(\[\d+:+\d+\])?\s*(\w+);')
    ports = []
    for nm in port_names:
        found = False
        for l in lines:
            m = decl_pat.match(l.split('//',1)[0])
            if m and m.group(3)==nm:
                direction = m.group(1)
                width     = m.group(2) or ""
                ports.append((direction, nm, width))
                found = True
                break
        if not found:
            print(f"WARNING: no decl line for port '{nm}'; defaulting to input")
            ports.append(("input", nm, ""))

    print(f"Found {len(ports)} top-level ports:")
    for d,nm,w in ports:
        print(f"  {d:6s} {w:8s} {nm}")
    print()
    return ports

if __name__=="__main__":
    import argparse, os
    from collections import defaultdict

    p = argparse.ArgumentParser()
    p.add_argument("-i","--input",   required=True, help="fpga_top.v")
    p.add_argument("-o","--output_dir", default="layers", help="where to put split files")
    args = p.parse_args()

    # read
    lines = open(args.input).read().splitlines()

    # debug: make sure we see your actual text
    # debug_dump_head(lines, n=50)

    # extract ports & wires
    global_ports = extract_global_ports(lines)
    wires_all    = collect_wires(lines)

    # rest of your logic follows…
    layers       = find_layers(lines)
    print("Detected layers:", layers, "\n")

    wires_by_layer = group_wires_by_layer(wires_all)
    instances      = collect_instances(lines)
    insts_by_layer = group_insts_by_layer(instances)

    # print("=== sample instance for layer 0 ===")
    # print(insts_by_layer[0][0])
    # print("===================================\n")

    # debug #1: print how many instances in each bucket
    for L, inst_list in insts_by_layer.items():
        print(f"Layer {L!r} has {len(inst_list)} instances")

    cross, cross_sizes = find_cross_wires(insts_by_layer)
    # print("Cross-layer wires:", sorted(cross), "\n")

    for _, portname, _ in global_ports:
        if portname in cross.keys():
            del cross[portname]  # remove global ports from cross wires
            del cross_sizes[portname]

    wire_to_layers = defaultdict(set)
    for L, wdict in wires_by_layer.items():
        for w in wdict:
            wire_to_layers[w].add(L)

    os.makedirs(args.output_dir, exist_ok=True)

    # emit layer modules
    for L in layers:
        sub = make_submodule(L, wires_by_layer[L], insts_by_layer.get(L,[]),
                             cross, cross_sizes, global_ports)
        fn  = os.path.join(args.output_dir, f"fpga_layer_{L}.v")
        write_file(fn, sub)
        print("Wrote", fn)

    # emit new top
    top = [f"module fpga_top({','.join([pname for _, pname, _ in global_ports])});",""]
    for global_port in global_ports:
        direction, pname, width = global_port
        top.append(f"  {direction} {width} {pname};")
    top.append("")
    for w in sorted(cross.keys()):
        top.append("  " + wires_all[w]) if w in wires_all else top.append(f"  wire {w};")
    top.append("")
    for L in layers:
        name = f"fpga_layer_{L}"
        inst = [f"  {name} U_layer_{L}("]
        conns = []
        for direction,pname,width in global_ports:
            conns.append(f".{pname}({pname})")
        for w, layers in cross.items():
            if L in layers:
                conns.append(f".{w}({w})")
        inst.append("    " + ",\n    ".join(conns))
        inst.append("  );\n")
        top.extend(inst)
    top.append("endmodule")
    write_file(os.path.join(args.output_dir,"fpga_top_split.v"), top)
    print("Wrote fpga_top_split.v in", args.output_dir)