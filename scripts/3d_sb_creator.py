from lxml import etree
from collections import namedtuple, defaultdict
import itertools
import sys
import os
import operator
import sqlite3
import time
from sizeof import total_size
import random
import numpy as np
# from memory_profiler import profile
import cProfile
import pstats
from copy import deepcopy
import argparse

node_struct = namedtuple("Node", ["id", "type", "layer", "xhigh", "xlow", "yhigh", "ylow", "side", "direction", "ptc"])
edge_struct = namedtuple("Edge", ["src_node", "sink_node", "src_layer", "sink_layer"])

node_data = {}

max_node_id = 0

# Create an index for quick lookups
node_index = defaultdict(list)

ptc_counter = defaultdict(int)

device_max_x = 0
device_max_y = 0
device_max_layer = 0

def print_verbose(*args, **kwargs):
    global verbose
    if verbose:
        print(*args, **kwargs)

def add_node(node):
    node_data[node.id] = node
    if node.direction != "NONE":
        x_low = int(node.xlow)
        y_low = int(node.ylow)
        x_high = int(node.xhigh)
        y_high = int(node.yhigh)

        if x_high == x_low and y_high == y_low:
            key = (node.type, int(node.xlow), int(node.ylow), int(node.layer))
            node_index[key].append(node)
            return

        if x_high != x_low:
            x_range = x_high - x_low
            for x in range (x_low, x_high + 1):
                key = (node.type, x, y_low, int(node.layer))
                node_index[key].append(node)
            return
        
        y_range = y_high - y_low
        for y in range (y_low, y_high + 1):
            key = (node.type, x_low, y, int(node.layer))
            node_index[key].append(node)
        return

def remove_node(node_id):
    node = node_data.pop(node_id, None)
    if node and node.direction != "NONE":
        key = (node.type, int(node.xlow), int(node.ylow), int(node.layer))
        if node in node_index[key]:
            node_index[key].remove(node)
            if not node_index[key]:
                del node_index[key]

def update_node(node):
    # Remove the old node entry if it exists
    old_node = node_data.get(node.id)
    if old_node:
        if old_node.direction != "NONE":
            old_key = (old_node.type, int(old_node.xlow), int(old_node.ylow), int(old_node.layer))
            if old_node in node_index[old_key]:
                node_index[old_key].remove(old_node)
                if not node_index[old_key]:
                    del node_index[old_key]
    
    # Add the updated node
    node_data[node.id] = node
    if node.direction != "NONE":
        new_key = (node.type, int(node.xlow), int(node.ylow), int(node.layer))
        node_index[new_key].append(node)

def read_structure(file_path, parser):
    start_time = time.time()
    try:
        tree = etree.parse(file_path, parser=parser)
        root = tree.getroot()
        end_time = time.time()
        print_verbose(f"Reading XML file took { ((end_time - start_time) * 1000):0.2f} ms")
        return root, tree

    except Exception as e:
        print_verbose(f"Error reading XML file: {e}")
        return None

def extract_nodes(root):
    print_verbose(f"Extracting Nodes")
    start_time = time.time()
    rr_nodes = root.find("rr_nodes")
    
    for node in rr_nodes.findall("node"):
        node_id = node.get("id")

        global max_node_id
        max_node_id = max(max_node_id, int(node_id))

        if int(node_id) % 100000 == 0:
            print_verbose(f"\tProcessed {node_id} nodes")

        type = node.get("type")

        if type != "CHANX" and type != "CHANY":
            continue
        
        loc = node.find("loc")

        layer = loc.get("layer")
        xhigh = loc.get("xhigh")
        xlow = loc.get("xlow")
        yhigh = loc.get("yhigh")
        ylow = loc.get("ylow")
        side = loc.get("side")
        ptc_node = loc.get("ptc")

        global ptc_counter
        key = (int(layer), int(xlow), int(ylow))
        ptc_counter[key] = max(1000, int(ptc_node))

        direction = node.get("direction")

        global device_max_layer, device_max_x, device_max_y
        device_max_layer = max(device_max_layer, int(layer))
        if type == "CHANX":
            device_max_x = max(device_max_x, int(xhigh))
        elif type == "CHANY":
            device_max_y = max(device_max_y, int(xhigh))

        segment = node.find("segment")
        segment_id = segment.get("segment_id")
        if segment_id == "0":
            add_node(node_struct(node_id, type, layer, xhigh, xlow, yhigh, ylow, side, direction, ptc_node))

    
    end_time = time.time()
    print_verbose(f"max_node_id: {max_node_id}")
    print_verbose(f"Extracting all nodes took { ((end_time - start_time) * 1000):0.2f} ms")

def extract_edges(root):
    print_verbose(f"Extracting Edges")
    start_time = time.time()
    rr_edges = root.find("rr_edges")
    count = 0
    for edge in rr_edges.findall("edge"):
        count+=1
        src_node = edge.get("src_node")
        sink_node = edge.get("sink_node")

        if count % 1000000 == 0:
            print_verbose(f"\tProcessed {count} edges")

        if src_node not in node_data or sink_node not in node_data:
            continue

        src_node_data = node_data[src_node]
        sink_node_data = node_data[sink_node]

        src_layer = src_node_data.layer
        sink_layer = sink_node_data.layer     
    
    end_time = time.time()
    print_verbose(f"Extracting Edges took { ((end_time - start_time) * 1000):0.2f} ms")

def create_node(node_id, type, layer, xhigh, xlow, yhigh, ylow, side, direction, ptc_node=0):
    new_node = node_struct(node_id, type, layer, xhigh, xlow, yhigh, ylow, side, direction, ptc_node)
    add_node(new_node)
    return new_node

def node_string(node: node_struct):
    ret = f"""<node capacity=\"1\" type=\"{node.type}\" id=\"{node.id}\" type=\"{node.type}\"><loc layer=\"{node.layer}\" ptc=\"0\" xhigh=\"{node.xhigh}\" xlow=\"{node.xlow}\" yhigh=\"{node.yhigh}\" ylow=\"{node.ylow}\"/>\n<timing C="0" R="0"/>\n<segment segment_id="0"/>\n</node>"""
    return ret

NODE_TEMPLATE = '<node capacity="1" direction="{direction}" id="{id}" type="{type}"/>'
LOC_TEMPLATE = '<loc layer="{layer}" ptc="{ptc}" xhigh="{xhigh}" xlow="{xlow}" yhigh="{yhigh}" ylow="{ylow}"/>'
TIMING_ELEMENT = etree.Element("timing", C="0", R="0")
SEGMENT_ELEMENT = etree.Element("segment", segment_id="0")

def node_xml_element(node):
    
    # key = (node.layer, node.xlow, node.ylow)
    # ptc[key] += 1

    # Create node using string template
    node_str = f'<node capacity="1" direction="{node.direction}" id="{node.id}" type="{node.type}"/>'
    new_node = etree.fromstring(node_str)

    # Create loc using string template
    loc_str = f'<loc layer="{node.layer}" ptc="{node.ptc}" xhigh="{node.xhigh}" xlow="{node.xlow}" yhigh="{node.yhigh}" ylow="{node.ylow}"/>'
    new_node.append(etree.fromstring(loc_str))

    timing = etree.Element("timing", C="0", R="0")
    segment = etree.Element("segment", segment_id="0")

    # Add pre-created elements
    new_node.append(timing)
    new_node.append(segment)

    return new_node

def edge_string(edge: edge_struct):
    return f"""<edge sink_node=\"{edge.sink_node}\" src_node=\"{edge.sink_node}\" switch_id=\"0\"></edge>\n"""

EDGE_TEMPLATE = '<edge sink_node="{sink}" src_node="{src}" switch_id="{switch}"/>'

def edge_xml_element(edge, switch_id="2"):
    return etree.fromstring(
        EDGE_TEMPLATE.format(
            sink=edge.sink_node,
            src=edge.src_node,
            switch=switch_id
        )
    )

def create_edge(src_node, sink_node, src_layer, sink_layer):
    new_edge = edge_struct(src_node, sink_node, src_layer, sink_layer)
    # add_edge((src_node, sink_node), new_edge)
    return new_edge

def find_chan_nodes(x, y):
    chan_nodes = []
    keys = [
        ("CHANX", x, y, 0),
        ("CHANY", x, y, 0),
        ("CHANX", x + 1, y, 0),
        ("CHANY", x, y + 1, 0),
        ("CHANX", x, y, 1),
        ("CHANY", x, y, 1),
        ("CHANX", x + 1, y, 1),
        ("CHANY", x, y + 1, 1)
    ]
    
    for key in keys:
        chan_nodes.extend(node_index.get(key, []))
    
    # Dumb to look at but this is just to remove any duplicates since if there's long wires they can appear at multiple different locations
    return list(set(chan_nodes))

def sort_chan_nodes_into_input_and_output(chan_nodes, x, y):

    layer_1_sb_input_nodes = []
    layer_1_sb_output_nodes = []
    layer_0_sb_input_nodes = []
    layer_0_sb_output_nodes = []


    for node in chan_nodes:
        if node.layer == '1':
            if node.direction == "INC_DIR":
                if (int(node.xlow) == int(x) + 1 and int(node.ylow) == int(y)) or (int(node.xlow) == int(x) and int(node.ylow) == int(y) + 1):
                    layer_1_sb_output_nodes.append(node)

                elif int(node.xhigh) >= int(x) and int(node.yhigh) >=  int(y):
                    layer_1_sb_input_nodes.append(node)

                else:
                    print_verbose(f"ERROR: {node} can't be classified as input or output at location X: {x} Y: {y}")
                    exit(1)

            elif node.direction == "DEC_DIR":
                if int(node.xhigh) == int(x) and int(node.yhigh) == int(y):
                    layer_1_sb_output_nodes.append(node)

                elif (int(node.xlow) <= int(x) + 1 and int(node.ylow) == int(y)) or (int(node.xlow) == int(x) and int(node.ylow) <= int(y) + 1):
                    layer_1_sb_input_nodes.append(node)

                else:
                    print_verbose(f"ERROR: {node} can't be classified as input or output at location X: {x} Y: {y}")
                    exit(1)
            
            else:
                print_verbose(f"ERROR: {node} can't be classified as input or output at location X: {x} Y: {y}")
                exit(1)
            
            
        else:

            if node.direction == "INC_DIR":
                if (int(node.xlow) == int(x) + 1 and int(node.ylow) == int(y)) or (int(node.xlow) == int(x) and int(node.ylow) == int(y) + 1):
                    layer_0_sb_output_nodes.append(node)

                elif int(node.xhigh) >= int(x) and int(node.yhigh) >=  int(y):
                    layer_0_sb_input_nodes.append(node)

                else:
                    print_verbose(f"ERROR: {node} can't be classified as input or output at location X: {x} Y: {y}")
                    exit(1)

            elif node.direction == "DEC_DIR":
                if int(node.xhigh) == int(x) and int(node.yhigh) == int(y):
                    layer_0_sb_output_nodes.append(node)

                elif (int(node.xlow) <= int(x) + 1 and int(node.ylow) == int(y)) or (int(node.xlow) == int(x) and int(node.ylow) <= int(y) + 1):
                    layer_0_sb_input_nodes.append(node)

                else:
                    print_verbose(f"ERROR: {node} can't be classified as input or output at location X: {x} Y: {y}")
                    exit(1)
           
            else:
                print_verbose(f"ERROR: {node} can't be classified as input or output at location X: {x} Y: {y}")
                exit(1)

            

    # A bit dumb to look at but this is just to remove any duplicates since if there's long wires they can appear at multiple different locations
    return list(set(layer_0_sb_input_nodes)), list(set(layer_0_sb_output_nodes)), list(set(layer_1_sb_input_nodes)), list(set(layer_1_sb_output_nodes))

def connect_sb_nodes_full(input_nodes, output_nodes):
    # global max_node_id
    # for input_node in input_nodes:
    #     for output_node in output_nodes:
    #         input_none_node = create_node(max_node_id + 1, input_node.type, input_node.layer, input_node.xhigh, input_node.xlow, input_node.yhigh, input_node.ylow, input_node.side, "NONE")
    #         output_none_node = create_node(max_node_id + 2, output_node.type, output_node.layer, output_node.xhigh, output_node.xlow, output_node.yhigh, output_node.ylow, output_node.side, "NONE")
    #         max_node_id += 2
    #         none_none_edge = create_edge(input_none_node.id, output_none_node.id, input_none_node.layer, output_none_node.layer)
    #         chan_none_edge = create_edge(input_node.id, input_none_node.id, input_node.layer, input_none_node.layer)
    #         none_chan_edge = create_edge(output_none_node.id, output_node.id, output_none_node.layer, output_node.layer)
    #         yield (input_none_node, output_none_node, (none_none_edge, chan_none_edge, none_chan_edge))

    global max_node_id
    new_nodes = []
    new_edges = []

    for input_node in input_nodes:
        for output_node in output_nodes:
            input_none_node = create_node(max_node_id + 1, input_node.type, input_node.layer, input_node.xhigh, input_node.xlow, input_node.yhigh, input_node.ylow, input_node.side, "NONE")
            output_none_node = create_node(max_node_id + 2, output_node.type, output_node.layer, output_node.xhigh, output_node.xlow, output_node.yhigh, output_node.ylow, output_node.side, "NONE")
            max_node_id += 2
            none_none_edge = create_edge(input_none_node.id, output_none_node.id, input_none_node.layer, output_none_node.layer)
            chan_none_edge = create_edge(input_node.id, input_none_node.id, input_node.layer, input_none_node.layer)
            none_chan_edge = create_edge(output_none_node.id, output_node.id, output_none_node.layer, output_node.layer)
            new_nodes.extend((input_none_node, output_none_node))
            new_edges.extend((none_none_edge, chan_none_edge, none_chan_edge))

    return new_nodes, new_edges

def connect_sb_nodes_combined(input_nodes, output_nodes, x, y, input_layer, output_layer):
    global max_node_id

    new_edges = [None] * (len(input_nodes) + len(output_nodes) + 1)
    edge_idx = 0

    key = (int(input_layer), int(x), int(y))
    ptc_val = ptc_counter[key]
    ptc_val += 1
    input_layer_none_nodes =[create_node(max_node_id + 1, "CHANX", input_layer, x, x, y, y, "", "NONE", ptc_val)]
    ptc_val += 1
    output_layer_none_nodes = [create_node(max_node_id + 2, "CHANX", output_layer, x, x, y, y, "", "NONE", ptc_val)]

    ptc_counter[key] = ptc_val
    
    max_node_id += 2

    # connect the input nodes to the none node
    for input_node in input_nodes:
        new_edges[edge_idx] = create_edge(input_node.id, input_layer_none_nodes[0].id, input_node.layer, input_layer_none_nodes[0].layer)
        edge_idx += 1
    
    # connect the none node to the output nodes
    for output_node in output_nodes:
        new_edges[edge_idx] = create_edge(output_layer_none_nodes[0].id, output_node.id, output_layer_none_nodes[0].layer, output_node.layer)
        edge_idx += 1

    # connect the two none nodes
    new_edges[edge_idx] = create_edge(input_layer_none_nodes[0].id, output_layer_none_nodes[0].id, input_layer_none_nodes[0].layer, output_layer_none_nodes[0].layer)

    return input_layer_none_nodes, output_layer_none_nodes, new_edges

def write_sb_nodes(structure, nodes_to_write):
    rr_nodes = structure.find("rr_nodes")
    for node in nodes_to_write:
        new_node = node_xml_element(node)
        rr_nodes.append(new_node)

# @profile    
def write_sb_edges(structure, edges_to_write):
    rr_edges = structure.find("rr_edges")
    for edge in edges_to_write:
        switch_id = 0
        src_data = node_data[edge.src_node]
        sink_data = node_data[edge.sink_node]
        if src_data.direction == "NONE" and sink_data.direction != "NONE":
            switch_id = 2
        new_edge = edge_xml_element(edge, str(2))
        rr_edges.append(new_edge)

def sort_nodes(nodes):
    #sort nodes by id in increasing order
    return sorted(nodes, key=operator.attrgetter("id"))

def create_full_sb(input_nodes, output_nodes, x, y):
    # Each input node will have 2 None nodes created one on each layer, and will connect to each output node that has the correct PTC value
    # Number of connections to be made into output nodes = channel width (CW), AKA the corresponding PTC values

    # For inputs:
    #   - (x, y) CHANs have even ptc values starting from 0 and increasing
    #   - (x + 1, y) & (x, y+1) CHANs have odd ptc values starting from 1 and increasing
    # For outputs:
    #   - (x, y) CHANs have odd ptc values starting from 1 and increasing
    #   - (x + 1, y) & (x, y+1) CHANs have even ptc values starting from 0 and increasing

    # Structure of thsi function:
    # Identify input nodes that correspond to output nodes based on PTC values
    #   * Ex: Inputs with PTC 0 (x,y) Chans and PTC 1 (x+1, y) & (x, y+1) Chans connect with outputs with PTC 1 (x, y) Chans and PTC 0 (x+1, y) & (x, y+1) Chans
    #   * Group those together and call connect_sb_nodes_full for each input with all the outputs identified
    

    # First store the nodes in a list with increasing ptc values
    x_y_chanx_input_nodes = []
    x_y_chany_input_nodes = []
    x_plus_1_y_chanx_input_nodes = []
    x_y_plus_1_chany_input_nodes = []

    x_y_chanx_output_nodes = []
    x_y_chany_output_nodes = []
    x_plus_1_y_chanx_output_nodes = []
    x_y_plus_1_chany_output_nodes = []

    for input_node in input_nodes:
        if input_node.xlow == str(x) and input_node.ylow == str(y):
            if input_node.type == "CHANX":
                x_y_chanx_input_nodes.append(input_node)
            else:
                x_y_chany_input_nodes.append(input_node)
        elif input_node.xlow == str(x + 1) and input_node.ylow == str(y) and input_node.type == "CHANX":
            x_plus_1_y_chanx_input_nodes.append(input_node)
        elif input_node.xlow == str(x) and input_node.ylow == str(y + 1) and input_node.type == "CHANY":
            x_y_plus_1_chany_input_nodes.append(input_node)
        else:
            print_verbose(f"ERROR: Input node is not in the correct location, node: {input_node}")
    
    for output_node in output_nodes:
        if output_node.xlow == str(x) and output_node.ylow == str(y):
            if output_node.type == "CHANX":
                x_y_chanx_output_nodes.append(output_node)
            else:
                x_y_chany_output_nodes.append(output_node)
        elif output_node.xlow == str(x + 1) and output_node.ylow == str(y) and output_node.type == "CHANX":
            x_plus_1_y_chanx_output_nodes.append(output_node)
        elif output_node.xlow == str(x) and output_node.ylow == str(y + 1) and output_node.type == "CHANY":
            x_y_plus_1_chany_output_nodes.append(output_node)
        else:
            print_verbose(f"ERROR: Output node is not in the correct location, node: {output_node}")
    
    # Sort the nodes by ptc
    x_y_chanx_input_nodes = sorted(x_y_chanx_input_nodes, key=lambda x: int(x.ptc))
    x_y_chany_input_nodes = sorted(x_y_chany_input_nodes, key=lambda x: int(x.ptc))
    x_plus_1_y_chanx_input_nodes = sorted(x_plus_1_y_chanx_input_nodes, key=lambda x: int(x.ptc))
    x_y_plus_1_chany_input_nodes = sorted(x_y_plus_1_chany_input_nodes, key=lambda x: int(x.ptc))

    x_y_chanx_output_nodes = sorted(x_y_chanx_output_nodes, key=lambda x: int(x.ptc))
    x_y_chany_output_nodes = sorted(x_y_chany_output_nodes, key=lambda x: int(x.ptc))
    x_plus_1_y_chanx_output_nodes = sorted(x_plus_1_y_chanx_output_nodes, key=lambda x: int(x.ptc))
    x_y_plus_1_chany_output_nodes = sorted(x_y_plus_1_chany_output_nodes, key=lambda x: int(x.ptc))

    input_size = len(x_y_chanx_input_nodes) + len(x_y_chany_input_nodes) + len(x_plus_1_y_chanx_input_nodes) + len(x_y_plus_1_chany_input_nodes)
    output_size = len(x_y_chanx_output_nodes) + len(x_y_chany_output_nodes) + len(x_plus_1_y_chanx_output_nodes) + len(x_y_plus_1_chany_output_nodes)

    assert input_size == output_size
    assert len(x_y_chanx_input_nodes) == len(x_y_chanx_output_nodes)
    assert len(x_y_chany_input_nodes) == len(x_y_chany_output_nodes)
    assert len(x_plus_1_y_chanx_input_nodes) == len(x_plus_1_y_chanx_output_nodes)
    assert len(x_y_plus_1_chany_input_nodes) == len(x_y_plus_1_chany_output_nodes)

    new_nodes = []
    new_edges = []

    max_len = max(len(x_y_chanx_input_nodes), len(x_y_chany_input_nodes), len(x_plus_1_y_chanx_input_nodes), len(x_y_plus_1_chany_input_nodes))

    for i in range(max_len):
        output_nodes = []
        if i < len(x_y_chanx_output_nodes):
            output_nodes.append(x_y_chanx_output_nodes[i])
        if i < len(x_y_chany_output_nodes):
            output_nodes.append(x_y_chany_output_nodes[i])
        if i < len(x_plus_1_y_chanx_output_nodes):
            output_nodes.append(x_plus_1_y_chanx_output_nodes[i])
        if i < len(x_y_plus_1_chany_output_nodes):
            output_nodes.append(x_y_plus_1_chany_output_nodes[i])

        if i < len(x_y_chanx_input_nodes):
            input_nodes = [x_y_chanx_input_nodes[i]]

            created_nodes, created_edges = connect_sb_nodes_full(input_nodes, output_nodes)
            new_nodes.extend(created_nodes)
            new_edges.extend(created_edges)

        if i < len(x_y_chany_input_nodes):
            input_nodes = [x_y_chany_input_nodes[i]]

            created_nodes, created_edges = connect_sb_nodes_full(input_nodes, output_nodes)
            new_nodes.extend(created_nodes)
            new_edges.extend(created_edges)

        if i < len(x_plus_1_y_chanx_input_nodes):
            input_nodes = [x_plus_1_y_chanx_input_nodes[i]]

            created_nodes, created_edges = connect_sb_nodes_full(input_nodes, output_nodes)
            new_nodes.extend(created_nodes)
            new_edges.extend(created_edges)

        if i < len(x_y_plus_1_chany_input_nodes):
            input_nodes = [x_y_plus_1_chany_input_nodes[i]]

            created_nodes, created_edges = connect_sb_nodes_full(input_nodes, output_nodes)
            new_nodes.extend(created_nodes)
            new_edges.extend(created_edges)

    return new_nodes, new_edges

def sort_chan_nodes_by_direction(chan_nodes, x, y):
    '''
        Function to sort the chan nodes into the correct lists based on the location of the node
    '''
    x_y_chanx_chan_nodes = [None] * len(chan_nodes)
    x_y_chany_chan_nodes = [None] * len(chan_nodes)
    x_plus_1_y_chanx_chan_nodes = [None] * len(chan_nodes)
    x_y_plus_1_chany_chan_nodes = [None] * len(chan_nodes)
    
    x_y_chanx_chan_nodes_idx = 0
    x_y_chany_chan_nodes_idx = 0
    x_plus_1_y_chanx_chan_nodes_idx = 0
    x_y_plus_1_chany_chan_nodes_idx = 0

    for input_node in chan_nodes:

        node_type = input_node.type
        node_dir = input_node.direction
        
        if node_type == "CHANX":

            # The only time a INC CHANX node is at location x plus 1 is when it's being driven, 
            if node_dir == "INC_DIR":
                if (int(input_node.xlow) == int(x) + 1 and int(input_node.ylow) == int(y)) or (int(input_node.xlow) == int(x) and int(input_node.ylow) == int(y) + 1):
                    x_plus_1_y_chanx_chan_nodes[x_plus_1_y_chanx_chan_nodes_idx] = input_node
                    x_plus_1_y_chanx_chan_nodes_idx += 1
                else:
                    x_y_chanx_chan_nodes[x_y_chanx_chan_nodes_idx] = input_node
                    x_y_chanx_chan_nodes_idx += 1
            
            # The only time a DEC CHANX node is at location x is when it's being driven
            elif node_dir == "DEC_DIR":
                if int(input_node.xhigh) == int(x) and int(input_node.yhigh) == int(y):
                    x_y_chanx_chan_nodes[x_y_chanx_chan_nodes_idx] = input_node
                    x_y_chanx_chan_nodes_idx += 1
                else:
                    x_plus_1_y_chanx_chan_nodes[x_plus_1_y_chanx_chan_nodes_idx] = input_node
                    x_plus_1_y_chanx_chan_nodes_idx += 1

            else: 
                print_verbose(f"ERROR: Input node is not in the correct location, node: {input_node}")

        elif node_type == "CHANY":

            # The only time a INC CHANY node is at location y plus 1 is when it's being driven,
            if node_dir == "INC_DIR":
                if (int(input_node.xlow) == int(x) + 1 and int(input_node.ylow) == int(y)) or (int(input_node.xlow) == int(x) and int(input_node.ylow) == int(y) + 1):
                    x_y_plus_1_chany_chan_nodes[x_y_plus_1_chany_chan_nodes_idx] = input_node
                    x_y_plus_1_chany_chan_nodes_idx += 1
                else:
                    x_y_chany_chan_nodes[x_y_chany_chan_nodes_idx] = input_node
                    x_y_chany_chan_nodes_idx += 1

            # The only time a DEC CHANY node is at location y is when it's being driven
            elif node_dir == "DEC_DIR":
                if int(input_node.xhigh) == int(x) and int(input_node.yhigh) == int(y):
                    x_y_chany_chan_nodes[x_y_chany_chan_nodes_idx] = input_node
                    x_y_chany_chan_nodes_idx += 1
                else:
                    x_y_plus_1_chany_chan_nodes[x_y_plus_1_chany_chan_nodes_idx] = input_node
                    x_y_plus_1_chany_chan_nodes_idx += 1

            else: 
                print_verbose(f"ERROR: Input node is not in the correct location, node: {input_node}")
        else:
            print_verbose(f"ERROR: Input node is not in the correct location, node: {input_node}")
        
    #sort the nodes by ptc
    x_y_chanx_chan_nodes = sorted(x_y_chanx_chan_nodes[:x_y_chanx_chan_nodes_idx], key=lambda x: int(x.ptc))
    x_y_chany_chan_nodes = sorted(x_y_chany_chan_nodes[:x_y_chany_chan_nodes_idx], key=lambda x: int(x.ptc))
    x_plus_1_y_chanx_chan_nodes = sorted(x_plus_1_y_chanx_chan_nodes[:x_plus_1_y_chanx_chan_nodes_idx], key=lambda x: int(x.ptc))
    x_y_plus_1_chany_chan_nodes = sorted(x_y_plus_1_chany_chan_nodes[:x_y_plus_1_chany_chan_nodes_idx], key=lambda x: int(x.ptc))

    return x_y_chanx_chan_nodes, x_y_chany_chan_nodes, x_plus_1_y_chanx_chan_nodes, x_y_plus_1_chany_chan_nodes

def create_subset_connection_3d_sb(max_output_len, x_y_chanx_input_nodes, x_y_chany_input_nodes, x_plus_1_y_chanx_input_nodes, x_y_plus_1_chany_input_nodes, x_y_chanx_output_nodes, x_y_chany_output_nodes, x_plus_1_y_chanx_output_nodes, x_y_plus_1_chany_output_nodes, x, y, input_layer, output_layer):
    input_layer_none_nodes = []
    output_layer_none_nodes = []
    new_edges = []

    # If there are no outputs then there is no wya to create a 3D SB at a given location
    if len(x_y_chanx_output_nodes) == 0 and len(x_y_chany_output_nodes) == 0 and len(x_plus_1_y_chanx_output_nodes) == 0 and len(x_y_plus_1_chany_output_nodes) == 0:
        return input_layer_none_nodes, output_layer_none_nodes, new_edges

    x_y_chanx_input_nodes_len = len(x_y_chanx_input_nodes)
    x_y_chany_input_nodes_len = len(x_y_chany_input_nodes)
    x_plus_1_y_chanx_input_nodes_len = len(x_plus_1_y_chanx_input_nodes)
    x_y_plus_1_chany_input_nodes_len = len(x_y_plus_1_chany_input_nodes)

    x_y_chanx_output_nodes_len = len(x_y_chanx_output_nodes)
    x_y_chany_output_nodes_len = len(x_y_chany_output_nodes)
    x_plus_1_y_chanx_output_nodes_len = len(x_plus_1_y_chanx_output_nodes)
    x_y_plus_1_chany_output_nodes_len = len(x_y_plus_1_chany_output_nodes)

    for i in range(max_output_len):

        input_nodes_to_send = []
        output_nodes_to_send = []

        if 0 < x_y_chanx_input_nodes_len:
            input_nodes_to_send.append(x_y_chanx_input_nodes[i])
        if 0 < x_y_chany_input_nodes_len:
            input_nodes_to_send.append(x_y_chany_input_nodes[i])
        if 0 < x_plus_1_y_chanx_input_nodes_len:
            input_nodes_to_send.append(x_plus_1_y_chanx_input_nodes[i])
        if 0 < x_y_plus_1_chany_input_nodes_len:
            input_nodes_to_send.append(x_y_plus_1_chany_input_nodes[i])

        if 0 < x_y_chanx_output_nodes_len:
            output_nodes_to_send.append(x_y_chanx_output_nodes[i])
        if 0 < x_y_chany_output_nodes_len:
            output_nodes_to_send.append(x_y_chany_output_nodes[i])
        if 0 < x_plus_1_y_chanx_output_nodes_len:
            output_nodes_to_send.append(x_plus_1_y_chanx_output_nodes[i])
        if 0 < x_y_plus_1_chany_output_nodes_len:
            output_nodes_to_send.append(x_y_plus_1_chany_output_nodes[i])

        input_layer_none_nodes_temp, output_layer_none_nodes_temp, new_edges_temp = connect_sb_nodes_combined(input_nodes_to_send, output_nodes_to_send, x, y, input_layer, output_layer)
        input_layer_none_nodes.extend(input_layer_none_nodes_temp)
        output_layer_none_nodes.extend(output_layer_none_nodes_temp)
        new_edges.extend(new_edges_temp)
    
    return input_layer_none_nodes, output_layer_none_nodes, new_edges

def create_wilton_3_connection_3d_sb(max_output_len, x_y_chanx_input_nodes, x_y_chany_input_nodes, x_plus_1_y_chanx_input_nodes, x_y_plus_1_chany_input_nodes, x_y_chanx_output_nodes, x_y_chany_output_nodes, x_plus_1_y_chanx_output_nodes, x_y_plus_1_chany_output_nodes, x, y, input_layer, output_layer):
    input_layer_none_nodes = []
    output_layer_none_nodes = []
    new_edges = []

    # If there are no outputs then there is no wya to create a 3D SB at a given location
    if len(x_y_chanx_output_nodes) == 0 and len(x_y_chany_output_nodes) == 0 and len(x_plus_1_y_chanx_output_nodes) == 0 and len(x_y_plus_1_chany_output_nodes) == 0:
        return input_layer_none_nodes, output_layer_none_nodes, new_edges

    x_y_chanx_input_nodes_len = len(x_y_chanx_input_nodes)
    x_y_chany_input_nodes_len = len(x_y_chany_input_nodes)
    x_plus_1_y_chanx_input_nodes_len = len(x_plus_1_y_chanx_input_nodes)
    x_y_plus_1_chany_input_nodes_len = len(x_y_plus_1_chany_input_nodes)

    x_y_chanx_output_nodes_len = len(x_y_chanx_output_nodes)
    x_y_chany_output_nodes_len = len(x_y_chany_output_nodes)
    x_plus_1_y_chanx_output_nodes_len = len(x_plus_1_y_chanx_output_nodes)
    x_y_plus_1_chany_output_nodes_len = len(x_y_plus_1_chany_output_nodes)

    for i in range(max_output_len):
        input_nodes_to_send = []
        output_nodes_to_send = []

        if 0 < x_y_chanx_input_nodes_len:
            input_nodes_to_send.append(x_y_chanx_input_nodes[i])
        if 0 < x_y_chany_input_nodes_len:
            input_nodes_to_send.append(x_y_chany_input_nodes[i])
        if 0 < x_plus_1_y_chanx_input_nodes_len:
            input_nodes_to_send.append(x_plus_1_y_chanx_input_nodes[i])
        if 0 < x_y_plus_1_chany_input_nodes_len:
            input_nodes_to_send.append(x_y_plus_1_chany_input_nodes[i])

        if 0 < x_y_chanx_output_nodes_len:
            output_nodes_to_send.append(x_y_chanx_output_nodes[(i+1) % x_y_chanx_output_nodes_len])
        if 0 < x_y_chany_output_nodes_len:
            output_nodes_to_send.append(x_y_chany_output_nodes[(i+1) % x_y_chany_output_nodes_len])
        if 0 < x_plus_1_y_chanx_output_nodes_len:
            output_nodes_to_send.append(x_plus_1_y_chanx_output_nodes[(i+1) % x_plus_1_y_chanx_output_nodes_len])
        if 0 < x_y_plus_1_chany_output_nodes_len:
            output_nodes_to_send.append(x_y_plus_1_chany_output_nodes[(i+1) % x_y_plus_1_chany_output_nodes_len])

        input_layer_none_nodes_temp, output_layer_none_nodes_temp, new_edges_temp = connect_sb_nodes_combined(
            input_nodes_to_send, output_nodes_to_send, x, y, input_layer, output_layer)
        
        input_layer_none_nodes.extend(input_layer_none_nodes_temp)
        output_layer_none_nodes.extend(output_layer_none_nodes_temp)
        new_edges.extend(new_edges_temp)
    
    return input_layer_none_nodes, output_layer_none_nodes, new_edges

def create_wilton_2_connection_3d_sb(max_output_len, x_y_chanx_input_nodes, x_y_chany_input_nodes, x_plus_1_y_chanx_input_nodes, x_y_plus_1_chany_input_nodes, x_y_chanx_output_nodes, x_y_chany_output_nodes, x_plus_1_y_chanx_output_nodes, x_y_plus_1_chany_output_nodes, x, y, input_layer, output_layer):
    input_layer_none_nodes = []
    output_layer_none_nodes = []
    new_edges = []

    # If there are no outputs then there is no wya to create a 3D SB at a given location
    if len(x_y_chanx_output_nodes) == 0 and len(x_y_chany_output_nodes) == 0 and len(x_plus_1_y_chanx_output_nodes) == 0 and len(x_y_plus_1_chany_output_nodes) == 0:
        return input_layer_none_nodes, output_layer_none_nodes, new_edges

    x_y_chanx_input_nodes_len = len(x_y_chanx_input_nodes)
    x_y_chany_input_nodes_len = len(x_y_chany_input_nodes)
    x_plus_1_y_chanx_input_nodes_len = len(x_plus_1_y_chanx_input_nodes)
    x_y_plus_1_chany_input_nodes_len = len(x_y_plus_1_chany_input_nodes)

    x_y_chanx_output_nodes_len = len(x_y_chanx_output_nodes)
    x_y_chany_output_nodes_len = len(x_y_chany_output_nodes)
    x_plus_1_y_chanx_output_nodes_len = len(x_plus_1_y_chanx_output_nodes)
    x_y_plus_1_chany_output_nodes_len = len(x_y_plus_1_chany_output_nodes)

    for i in range(max_output_len):
        input_nodes_to_send = []
        output_nodes_to_send = []

        if 0 < x_y_chanx_input_nodes_len:
            input_nodes_to_send.append(x_y_chanx_input_nodes[i % x_y_chanx_input_nodes_len])
        if 0 < x_y_chany_input_nodes_len:
            input_nodes_to_send.append(x_y_chany_input_nodes[i % x_y_chany_input_nodes_len] )
        if 0 < x_plus_1_y_chanx_input_nodes_len:
            input_nodes_to_send.append(x_plus_1_y_chanx_input_nodes[i % x_plus_1_y_chanx_input_nodes_len] )
        if 0 < x_y_plus_1_chany_input_nodes_len:
            input_nodes_to_send.append(x_y_plus_1_chany_input_nodes[i % x_y_plus_1_chany_input_nodes_len] )

        if 0 < x_y_chanx_output_nodes_len:
            output_nodes_to_send.append(x_y_chanx_output_nodes[(i+1) % x_y_chanx_output_nodes_len])
        if 0 < x_y_chany_output_nodes_len:
            output_nodes_to_send.append(x_y_chany_output_nodes[(i+2) % x_y_chany_output_nodes_len])
        if 0 < x_plus_1_y_chanx_output_nodes_len:
            output_nodes_to_send.append(x_plus_1_y_chanx_output_nodes[(i+3) % x_plus_1_y_chanx_output_nodes_len])
        if 0 < x_y_plus_1_chany_output_nodes_len:
            output_nodes_to_send.append(x_y_plus_1_chany_output_nodes[(i+4) % x_y_plus_1_chany_output_nodes_len])

        input_layer_none_nodes_temp, output_layer_none_nodes_temp, new_edges_temp = connect_sb_nodes_combined(
            input_nodes_to_send, output_nodes_to_send, x, y, input_layer, output_layer)
        
        input_layer_none_nodes.extend(input_layer_none_nodes_temp)
        output_layer_none_nodes.extend(output_layer_none_nodes_temp)
        new_edges.extend(new_edges_temp)
    
    return input_layer_none_nodes, output_layer_none_nodes, new_edges

def create_wilton_connection_3d_sb(max_output_len, x_y_chanx_input_nodes, x_y_chany_input_nodes, x_plus_1_y_chanx_input_nodes, x_y_plus_1_chany_input_nodes, x_y_chanx_output_nodes, x_y_chany_output_nodes, x_plus_1_y_chanx_output_nodes, x_y_plus_1_chany_output_nodes, x, y, input_layer, output_layer):
    input_layer_none_nodes = []
    output_layer_none_nodes = []
    new_edges = []

    # If there are no outputs then there is no wya to create a 3D SB at a given location
    if len(x_y_chanx_output_nodes) == 0 and len(x_y_chany_output_nodes) == 0 and len(x_plus_1_y_chanx_output_nodes) == 0 and len(x_y_plus_1_chany_output_nodes) == 0:
        return input_layer_none_nodes, output_layer_none_nodes, new_edges

    x_y_chanx_input_nodes_len = len(x_y_chanx_input_nodes)
    x_y_chany_input_nodes_len = len(x_y_chany_input_nodes)
    x_plus_1_y_chanx_input_nodes_len = len(x_plus_1_y_chanx_input_nodes)
    x_y_plus_1_chany_input_nodes_len = len(x_y_plus_1_chany_input_nodes)

    x_y_chanx_output_nodes_len = len(x_y_chanx_output_nodes)
    x_y_chany_output_nodes_len = len(x_y_chany_output_nodes)
    x_plus_1_y_chanx_output_nodes_len = len(x_plus_1_y_chanx_output_nodes)
    x_y_plus_1_chany_output_nodes_len = len(x_y_plus_1_chany_output_nodes)

    for i in range(max_output_len):

        input_nodes_to_send = []
        output_nodes_to_send = []

        if 0 < x_y_chanx_input_nodes_len:
            input_nodes_to_send.append(x_y_chanx_input_nodes[i])
        if 0 < x_y_chany_input_nodes_len:
            input_nodes_to_send.append(x_y_chany_input_nodes[(i+1) % len(x_y_chany_input_nodes)])
        if 0 < x_plus_1_y_chanx_input_nodes_len:
            input_nodes_to_send.append(x_plus_1_y_chanx_input_nodes[(i+2) % len(x_plus_1_y_chanx_input_nodes)])
        if 0 < x_y_plus_1_chany_input_nodes_len:
            input_nodes_to_send.append(x_y_plus_1_chany_input_nodes[(i+3) % len(x_y_plus_1_chany_input_nodes)])

        if 0 < x_y_chanx_output_nodes_len:
            output_nodes_to_send.append(x_y_chanx_output_nodes[i])
        if 0 < x_y_chany_output_nodes_len:
            output_nodes_to_send.append(x_y_chany_output_nodes[(i+1) % len(x_y_chany_output_nodes)])
        if 0 < x_plus_1_y_chanx_output_nodes_len:
            output_nodes_to_send.append(x_plus_1_y_chanx_output_nodes[(i+2) % len(x_plus_1_y_chanx_output_nodes)])
        if 0 < x_y_plus_1_chany_output_nodes_len:
            output_nodes_to_send.append(x_y_plus_1_chany_output_nodes[(i+3) % len(x_y_plus_1_chany_output_nodes)])

        input_layer_none_nodes_temp, output_layer_none_nodes_temp, new_edges_temp = connect_sb_nodes_combined(input_nodes_to_send, output_nodes_to_send, x, y, input_layer, output_layer)
        input_layer_none_nodes += input_layer_none_nodes_temp
        output_layer_none_nodes += output_layer_none_nodes_temp
        new_edges += new_edges_temp
    
    return input_layer_none_nodes, output_layer_none_nodes, new_edges

def create_combined_sb(input_nodes, output_nodes, x, y, input_layer, output_layer, connection_type="subset", vertical_connectivity_percentage=1):
    # need to figure out which nodes to connect together for larger than 2 CWs

    accepted_connection_types = ["subset", "wilton", "wilton_2", "wilton_3"]

    assert(connection_type in accepted_connection_types)

    # The way it works is by ptc, intially using a subset connection pattern for interlayer connections
    # To do this need to find the appropriate nodes to connect together based on the ptc value
    # For inputs:
    #   - (x, y) CHANs have even ptc values starting from 0 and increasing
    #   - (x + 1, y) & (x, y+1) CHANs have odd ptc values starting from 1 and increasing
    # For outputs:
    #   - (x, y) CHANs have odd ptc values starting from 1 and increasing
    #   - (x + 1, y) & (x, y+1) CHANs have even ptc values starting from 0 and increasing

    # need to connect for example: 
    # inputs:
    #   CHANX (x, y) with ptc: 0
    #   CHANX (x + 1, y) with ptc: 1
    #   CHANY (x, y) with ptc: 0
    #   CHANY (x, y + 1) with ptc: 1
    # outputs:
    #   CHANX (x, y) with ptc: 1
    #   CHANX (x + 1, y) with ptc: 0
    #   CHANY (x, y) with ptc: 1
    #   CHANY (x, y + 1) with ptc: 0

    # First store the nodes in a list with increasing ptc values
    x_y_chanx_input_nodes, x_y_chany_input_nodes, x_plus_1_y_chanx_input_nodes, x_y_plus_1_chany_input_nodes = sort_chan_nodes_by_direction(input_nodes, x, y)

    x_y_chanx_output_nodes, x_y_chany_output_nodes, x_plus_1_y_chanx_output_nodes, x_y_plus_1_chany_output_nodes = sort_chan_nodes_by_direction(output_nodes, x, y)

    #Print different lens for debugging
    print_verbose(f"{'*' * 10}")
    print_verbose(f"X: {x} Y: {y} Input Layer: {input_layer} Output Layer: {output_layer}")
    print_verbose(f"Input Nodes:                  {len(input_nodes)}                  Output Nodes: {len(output_nodes)}")

    print_verbose(f"x_y_chanx_input_nodes:        {len(x_y_chanx_input_nodes)}        x_y_chanx_output_nodes: {len(x_y_chanx_output_nodes)}")   
    print_verbose(f"x_y_chany_input_nodes:        {len(x_y_chany_input_nodes)}        x_y_chany_output_nodes: {len(x_y_chany_output_nodes)}")    
    print_verbose(f"x_plus_1_y_chanx_input_nodes: {len(x_plus_1_y_chanx_input_nodes)} x_plus_1_y_chanx_output_nodes: {len(x_plus_1_y_chanx_output_nodes)}")
    print_verbose(f"x_y_plus_1_chany_input_nodes: {len(x_y_plus_1_chany_input_nodes)} x_y_plus_1_chany_output_nodes: {len(x_y_plus_1_chany_output_nodes)}")

    print_verbose(f"{'*' * 10}")    
    print_verbose(f"x_y_chanx_input_nodes:  {x_y_chanx_input_nodes}")
    print_verbose(f"x_y_chanx_output_nodes: {x_y_chanx_output_nodes}")

    print_verbose(f"{'*' * 5}")
    print_verbose(f"x_y_chany_input_nodes:  {x_y_chany_input_nodes}")
    print_verbose(f"x_y_chany_output_nodes: {x_y_chany_output_nodes}")

    print_verbose(f"{'*' * 5}")
    print_verbose(f"x_plus_1_y_chanx_input_nodes:  {x_plus_1_y_chanx_input_nodes}")
    print_verbose(f"x_plus_1_y_chanx_output_nodes: {x_plus_1_y_chanx_output_nodes}")

    print_verbose(f"{'*' * 5}")    
    print_verbose(f"x_y_plus_1_chany_input_nodes:  {x_y_plus_1_chany_input_nodes}")
    print_verbose(f"x_y_plus_1_chany_output_nodes: {x_y_plus_1_chany_output_nodes}")

    # assert len(x_y_chanx_input_nodes) == len(x_y_chanx_output_nodes)
    # assert len(x_y_chany_input_nodes) == len(x_y_chany_output_nodes)
    # assert len(x_plus_1_y_chanx_input_nodes) == len(x_plus_1_y_chanx_output_nodes)
    # assert len(x_y_plus_1_chany_input_nodes) == len(x_y_plus_1_chany_output_nodes)

    max_output_len = int(max(len(x_y_chanx_output_nodes), len(x_y_chany_output_nodes), len(x_plus_1_y_chanx_output_nodes), len(x_y_plus_1_chany_output_nodes)) * vertical_connectivity_percentage)

    if connection_type == "subset":
        return create_subset_connection_3d_sb(max_output_len, x_y_chanx_input_nodes, x_y_chany_input_nodes, x_plus_1_y_chanx_input_nodes, x_y_plus_1_chany_input_nodes, x_y_chanx_output_nodes, x_y_chany_output_nodes, x_plus_1_y_chanx_output_nodes, x_y_plus_1_chany_output_nodes, x, y, input_layer, output_layer)
    elif connection_type == "wilton":
        return create_wilton_connection_3d_sb(max_output_len, x_y_chanx_input_nodes, x_y_chany_input_nodes, x_plus_1_y_chanx_input_nodes, x_y_plus_1_chany_input_nodes, x_y_chanx_output_nodes, x_y_chany_output_nodes, x_plus_1_y_chanx_output_nodes, x_y_plus_1_chany_output_nodes, x, y, input_layer, output_layer)
    elif connection_type == "wilton_2":
        return create_wilton_2_connection_3d_sb(max_output_len, x_y_chanx_input_nodes, x_y_chany_input_nodes, x_plus_1_y_chanx_input_nodes, x_y_plus_1_chany_input_nodes, x_y_chanx_output_nodes, x_y_chany_output_nodes, x_plus_1_y_chanx_output_nodes, x_y_plus_1_chany_output_nodes, x, y, input_layer, output_layer)
    elif connection_type == "wilton_3":
        return create_wilton_3_connection_3d_sb(max_output_len, x_y_chanx_input_nodes, x_y_chany_input_nodes, x_plus_1_y_chanx_input_nodes, x_y_plus_1_chany_input_nodes, x_y_chanx_output_nodes, x_y_chany_output_nodes, x_plus_1_y_chanx_output_nodes, x_y_plus_1_chany_output_nodes, x, y, input_layer, output_layer)

def percentage_skip_2d_deterministic(grid_x, grid_y, percent):
    """
    Iterate over a 2D grid in a deterministic pattern, skipping elements
    based on the specified percentage.
    :param grid_x: The range or size of the x-dimension.
    :param grid_y: The range or size of the y-dimension.
    :param percent: The percentage of elements to skip (0.0 to 1.0).
    :yield: Coordinates (x, y) that meet the percentage criteria.
    """
    assert 0 <= percent <= 1, "Percent must be between 0 (inclusive) and 1 (exclusive)."
    
    # Flatten the 2D grid into a linear list of indices
    all_coords = [(x, y) for x in range(grid_x + 1) for y in range(grid_y + 1)]
    total_elements = len(all_coords)
    
    true_count = round(total_elements * percent)
    indices = np.linspace(0, total_elements - 1, true_count, dtype=int)

    for i in indices:
        yield all_coords[i]

def percentage_skip_2d_random(grid_x, grid_y, percent):
    """
    Iterate over a 2D grid while ensuring a percentage of elements are skipped.
    :param grid_x: The range or size of the x-dimension.
    :param grid_y: The range or size of the y-dimension.
    :param percent: The percentage of elements to skip (0.0 to 1.0).
    :yield: Coordinates (x, y) that meet the percentage criteria.
    """
    assert 0 <= percent <= 1, "Percent must be between 0 (inclusive) and 1 (exclusive)."
    
    total_elements = (grid_x + 1) * (grid_y + 1)
    num_to_keep = int(total_elements * (percent))

    # Randomly sample a subset of coordinates to keep
    all_coords = [(x, y) for x in range(grid_x + 1) for y in range(grid_y + 1)]
    selected_coords = random.sample(all_coords, num_to_keep)

    for coord in selected_coords:
        yield coord

def percentage_skip_loop(iterable, percent):
    """
    Iterate through the iterable while skipping a percentage of iterations.
    :param iterable: The collection or range to iterate over.
    :param percent: The percentage of iterations to skip (0.0 to 1.0).
    """
    assert 0 <= percent <= 1, "Percent must be between 0 (inclusive) and 1 (exclusive)."
    
    if percent == 1:
        skip_interval = 1  # Skip all iterations. 

    else:
        skip_interval = int(1 / (1 - percent))  # Determine the skip interval.
    
    for i, item in enumerate(iterable):
        if percent != 1 and (i % skip_interval) < (skip_interval - 1):  # Skip iterations.
            continue
        yield item

def create_sb(structure,  connection_type="subset", vertical_connectivity_percentage=1):
    print_verbose("Creating SB connections")
    
    start_time = time.time()
    # loop over the device and find the highest CHAN x and y
    # device_x, device_y, num_layers = find_device_chan_dim()

    # only create sbs for every other location
    global percent_connectitivty

    edges_to_write = []
    nodes_to_write = []

    num_created = 0

    global device_max_x, device_max_y

    number_sbs = device_max_x * device_max_y * percent_connectitivty
    print_iter = round(number_sbs / 5)
    # For each location, find all relevant chans that either enter or exit th SB
    for x, y in percentage_skip_2d_deterministic(device_max_x, device_max_y, percent_connectitivty):

        print_verbose(f"{'*' * 60}")
        print_verbose("Creating SB for x:", x, "y:", y)
        print_verbose(f"{'*' * 60}")
        num_created += 1
        chan_nodes = find_chan_nodes(x, y)
        layer_0_sb_input_nodes, layer_0_sb_output_nodes, layer_1_sb_input_nodes, layer_1_sb_output_nodes = sort_chan_nodes_into_input_and_output(chan_nodes, x, y)
        input_layer_0_none_nodes = []
        output_layer_1_none_nodes = []
        input_layer_1_none_nodes = []
        output_layer_0_none_nodes = []
        new_edges_0 = []
        new_edges_1 = []

        input_layer_0_none_nodes, output_layer_1_none_nodes, new_edges_0 = create_combined_sb(layer_0_sb_input_nodes, layer_1_sb_output_nodes, x, y, 0, 1, connection_type, vertical_connectivity_percentage)
        input_layer_1_none_nodes, output_layer_0_none_nodes, new_edges_1 = create_combined_sb(layer_1_sb_input_nodes, layer_0_sb_output_nodes, x, y, 1, 0, connection_type, vertical_connectivity_percentage)

        print_verbose(f"{'*' * 10}")

        print_verbose(f"Created {len(input_layer_0_none_nodes)} input none nodes for layer 0 ")
        print_verbose(f"Created {len(output_layer_0_none_nodes)} output none nodes for none nodes for layer 1")
        print_verbose(f"Created {len(input_layer_1_none_nodes)} input none nodes for layer 1")
        print_verbose(f"Created {len(output_layer_1_none_nodes)} output none nodes for layer 0")

        nodes_to_write.extend(input_layer_0_none_nodes)
        nodes_to_write.extend(output_layer_1_none_nodes)
        nodes_to_write.extend(input_layer_1_none_nodes)
        nodes_to_write.extend(output_layer_0_none_nodes)

        print_verbose(f"Created {len(new_edges_0)} edges to connect layer 0 to layer 1")
        print_verbose(f"Created {len(new_edges_1)} edges to connect layer 1 to layer 0")

        edges_to_write.extend(new_edges_0)
        edges_to_write.extend(new_edges_1)

        

        if num_created % print_iter == 0:
            print_verbose(f"Created {round((num_created / number_sbs) * 100)}% of 3D SBs")

        # print_verbose("added", len(nodes_to_write) - node_count_before, "nodes to make", total_size((nodes_to_write, node_data, node_index)) / (1024 * 1024 * 1024), "GiB, added", len(edges_to_write) - edge_count_before, "edges to make", total_size((edges_to_write, edge_data, edges_by_src, edges_by_sink)) / (1024 * 1024 * 1024), "GiB")
    
    print_verbose(f"\nNumber of new nodes: {len(nodes_to_write)}")
    print_verbose(f"Number of new edges: {len(edges_to_write)}\n")

    print_verbose("Sorting Nodes")
    sorting_start_time = time.time()
    nodes_to_write = sort_nodes(nodes_to_write)
    sorting_end_time = time.time()

    print_verbose(f"Sorting Nodes took { ((sorting_end_time - sorting_start_time) * 1000):0.2f} ms")

    print_verbose("Writing SB Nodes and Edges")
    writing_start_time = time.time()
    write_sb_nodes(structure, nodes_to_write)
    write_sb_edges(structure, edges_to_write)

    writing_end_time = time.time()
    print_verbose(f"Writing SB Nodes and Edges took { ((writing_end_time - writing_start_time) * 1000):0.2f} ms")

    end_time = time.time()
    print_verbose(f"Creating SB connections took { ((end_time - start_time) * 1000):0.2f} ms")

    print_verbose(f"Total number of SBs created: {num_created}")

def main():
    args_parser = argparse.ArgumentParser(description="Generate 3D Switch Blocks (SBs) for a given VPR RR Graph without 3D SBs")

    args_parser.add_argument("-f", "--input_file",type=str, help="The file path to the VPR RR Graph XML file", required=True)
    args_parser.add_argument("-o", "--output_path", type=str, help="The file path to the output VPR RR Graph XML file", required=True)
    args_parser.add_argument("-p", "--percent_connectivity", type=float, help="The percentage of SBs on fabric that are 3D. Must be a float between 0 and 1", required=True)
    args_parser.add_argument("-c", "--connection_type", type=str, help="The connection pattern to use for the 3D SBs. Options are: subset, wilton, wilton_2, wilton_3", required=True)
    args_parser.add_argument("-vp", "--vertical_connectivity_percentage", type=float, help="The percentage of channels at each SB that are connected vertically. Must be a float between 0 and 1", default=1.0)
    args_parser.add_argument("-v", "--verbose", help="Whether to print verbose output.", action="store_true")

    args = args_parser.parse_args()

    start_time = time.time()
    
    file_path = args.input_file
    output_file_path = args.output_path

    global percent_connectitivty
    percent_connectitivty = args.percent_connectivity

    connection_type = args.connection_type

    vertical_connectivity_percentage = args.vertical_connectivity_percentage

    global verbose

    verbose = args.verbose

    design_string = f"{file_path} with {(percent_connectitivty * 100):0.1f} SBs, connection type: {connection_type}, vertical connectivity percentage: {vertical_connectivity_percentage} outputting to {output_file_path}"

    print(f"Creating 3D SBs for {design_string}")

    parser = etree.XMLParser(
            remove_blank_text=True,
            remove_comments=True,
            collect_ids=False,
            huge_tree=True,  # Allows for larger trees
            resolve_entities=False  # Saves some memory
        )

    structure, tree = read_structure(file_path, parser)
    extract_nodes(structure)
    create_sb(structure, connection_type, vertical_connectivity_percentage)

    tree.write(output_file_path, pretty_print=False, xml_declaration=True, encoding="UTF-8", compression=None)

    end_time = time.time()
    print(f"Generating SBs took { ((end_time - start_time) * 1000):0.2f} ms")

if __name__ == "__main__":
    main()
