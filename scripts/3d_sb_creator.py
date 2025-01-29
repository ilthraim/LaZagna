from lxml import etree
from lxml.etree import xmlfile
from collections import namedtuple, defaultdict
import itertools
import sys
import os
import operator
from memory_profiler import profile
import sqlite3
import time
from sizeof import total_size
import random

node_struct = namedtuple("Node", ["id", "type", "layer", "xhigh", "xlow", "yhigh", "ylow", "side", "direction", "ptc"])
edge_struct = namedtuple("Edge", ["src_node", "sink_node", "src_layer", "sink_layer"])

node_data = {}

max_node_id = 0

# Create an index for quick lookups
node_index = defaultdict(list)

def add_node(node):
    node_data[node.id] = node
    if node.direction != "NONE":
        key = (node.type, int(node.xlow), int(node.ylow), int(node.layer))
        node_index[key].append(node)

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

def read_structure(file_path):
    start_time = time.time()
    try:
        tree = etree.parse(file_path)
        root = tree.getroot()
        end_time = time.time()
        print(f"Reading XML file took { ((end_time - start_time) * 1000):0.2f} ms")
        return root, tree

    except Exception as e:
        print(f"Error reading XML file: {e}")
        return None

def extract_nodes(root):
    print(f"Extracting Nodes")
    start_time = time.time()
    rr_nodes = root.find("rr_nodes")
    
    for node in rr_nodes.findall("node"):
        node_id = node.get("id")

        global max_node_id
        max_node_id = max(max_node_id, int(node_id))

        if int(node_id) % 100000 == 0:
            print(f"\tProcessed {node_id} nodes")

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

        direction = node.get("direction")

        add_node(node_struct(node_id, type, layer, xhigh, xlow, yhigh, ylow, side, direction, ptc_node))

    
    end_time = time.time()
    print(f"Extracting all nodes took { ((end_time - start_time) * 1000):0.2f} ms")

def extract_edges(root):
    print(f"Extracting Edges")
    start_time = time.time()
    rr_edges = root.find("rr_edges")
    count = 0
    for edge in rr_edges.findall("edge"):
        count+=1
        src_node = edge.get("src_node")
        sink_node = edge.get("sink_node")

        if count % 1000000 == 0:
            print(f"\tProcessed {count} edges")

        if src_node not in node_data or sink_node not in node_data:
            continue

        src_node_data = node_data[src_node]
        sink_node_data = node_data[sink_node]

        src_layer = src_node_data.layer
        sink_layer = sink_node_data.layer     
    
    end_time = time.time()
    print(f"Extracting Edges took { ((end_time - start_time) * 1000):0.2f} ms")

def create_node(node_id, type, layer, xhigh, xlow, yhigh, ylow, side, direction, ptc_node=0):
    new_node = node_struct(node_id, type, layer, xhigh, xlow, yhigh, ylow, side, direction, ptc_node)
    add_node(new_node)
    return new_node

def node_string(node: node_struct):
    ret = f"""<node capacity=\"1\" type=\"{node.type}\" id=\"{node.id}\" type=\"{node.type}\"><loc layer=\"{node.layer}\" ptc=\"0\" xhigh=\"{node.xhigh}\" xlow=\"{node.xlow}\" yhigh=\"{node.yhigh}\" ylow=\"{node.ylow}\"/>\n<timing C="0" R="0"/>\n<segment segment_id="0"/>\n</node>"""
    return ret

def node_xml_element(node):
    global ptc
    key = (int(node.layer), int(node.xlow), int(node.ylow))
    ptc[key] += 1  # Increment the ptc count for this location

    new_node = etree.Element("node", capacity="1", direction=str(node.direction), id=str(node.id), type=str(node.type))

    # Create the <loc> sub-element
    loc = etree.SubElement(new_node, "loc", layer=str(node.layer), ptc=str(ptc[key]), xhigh=str(node.xhigh), xlow=str(node.xlow), yhigh=str(node.yhigh), ylow=str(node.ylow))

    # Create the <timing> sub-element
    timing = etree.SubElement(new_node, "timing", C="0", R="0")

    segment = etree.SubElement(new_node, "segment", segment_id="0")

    return new_node

def edge_string(edge: edge_struct):
    return f"""<edge sink_node=\"{edge.sink_node}\" src_node=\"{edge.sink_node}\" switch_id=\"0\"></edge>\n"""

def edge_xml_element(edge, switch_id="2"):
    new_edge = etree.Element("edge", sink_node=str(edge.sink_node), src_node=str(edge.src_node), switch_id=switch_id)
    return new_edge

def create_edge(src_node, sink_node, src_layer, sink_layer):
    new_edge = edge_struct(src_node, sink_node, src_layer, sink_layer)
    # add_edge((src_node, sink_node), new_edge)
    return new_edge

def find_sb_nodes_one_way():
    sb_driver_nodes = []
    sb_sink_nodes = []
    
    # Define keys with integers
    driver_keys = [
        ("CHANX", "INC_DIR", 1, 1, 0),
        ("CHANY", "INC_DIR", 1, 1, 0),
        ("CHANX", "DEC_DIR", 2, 1, 0),
        ("CHANY", "DEC_DIR", 1, 2, 0),
    ]
    
    sink_keys = [
        ("CHANX", "DEC_DIR", 1, 1, 1),
        ("CHANY", "DEC_DIR", 1, 1, 1),
        ("CHANX", "INC_DIR", 2, 1, 1),
        ("CHANY", "INC_DIR", 1, 2, 1),
    ]
    
    # Retrieve sb_driver_nodes
    for key in driver_keys:
        sb_driver_nodes.extend(node_index.get(key, []))
    
    # Retrieve sb_sink_nodes
    for key in sink_keys:
        sb_sink_nodes.extend(node_index.get(key, []))
    
    return sb_driver_nodes, sb_sink_nodes

def find_device_chan_dim():
    max_x = 0
    max_y = 0
    max_layer = 0
    for node in node_data.values():
        if int(node.layer) > max_layer:
            max_layer = int(node.layer)
        if node.type == "CHANX" and int(node.xlow) > max_x:
            max_x = int(node.xlow)
        if node.type == "CHANY" and int(node.ylow) > max_y:
            max_y = int(node.ylow)
    return max_x, max_y, max_layer

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
    
    return chan_nodes

def sort_chan_nodes_into_input_and_output(chan_nodes, x, y):
    layer_0_nodes = []
    layer_1_nodes = []
    for node in chan_nodes:
        if node.layer == '0':
            layer_0_nodes.append(node)
        else:
            layer_1_nodes.append(node)
    
    layer_1_sb_input_nodes = []
    layer_1_sb_output_nodes = []

    for node in layer_1_nodes:
        if node.direction == "INC_DIR" and node.xlow == str(x) and node.ylow == str(y):
            layer_1_sb_input_nodes.append(node)
        elif node.direction == "DEC_DIR" and ((node.xlow == str(x + 1) and node.ylow == str(y)) or (node.xlow == str(x) and node.ylow == str(y + 1))):
            layer_1_sb_input_nodes.append(node)
        elif node.direction == "DEC_DIR" and node.xlow == str(x) and node.ylow == str(y):
            layer_1_sb_output_nodes.append(node)
        elif node.direction == "INC_DIR" and ((node.xlow == str(x + 1) and node.ylow == str(y)) or (node.xlow == str(x) and node.ylow == str(y + 1))):
            layer_1_sb_output_nodes.append(node)
    
    layer_0_sb_input_nodes = []
    layer_0_sb_output_nodes = []

    for node in layer_0_nodes:
        if node.direction == "INC_DIR" and node.xlow == str(x) and node.ylow == str(y):
            layer_0_sb_input_nodes.append(node)
        elif node.direction == "DEC_DIR" and ((node.xlow == str(x + 1) and node.ylow == str(y)) or (node.xlow == str(x) and node.ylow == str(y + 1))):
            layer_0_sb_input_nodes.append(node)
        elif node.direction == "DEC_DIR" and node.xlow == str(x) and node.ylow == str(y):
            layer_0_sb_output_nodes.append(node)
        elif node.direction == "INC_DIR" and ((node.xlow == str(x + 1) and node.ylow == str(y)) or (node.xlow == str(x) and node.ylow == str(y + 1))):
            layer_0_sb_output_nodes.append(node)

    return layer_0_sb_input_nodes, layer_0_sb_output_nodes, layer_1_sb_input_nodes, layer_1_sb_output_nodes
 
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
    output_layer_none_nodes = []
    input_layer_none_nodes =[]
    new_edges = []

    none_input_node = create_node(max_node_id + 1, "CHANX", input_layer, x, x, y, y, "", "NONE")
    none_output_node = create_node(max_node_id + 2, "CHANX", output_layer, x, x, y, y, "", "NONE")
    max_node_id += 2

    output_layer_none_nodes.append(none_output_node)
    input_layer_none_nodes.append(none_input_node)

    # connect the input nodes to the none node
    for input_node in input_nodes:
        chan_none_edge = create_edge(input_node.id, none_input_node.id, input_node.layer, none_input_node.layer)
        new_edges.append(chan_none_edge)
    
    # connect the none node to the output nodes
    for output_node in output_nodes:
        none_chan_edge = create_edge(none_output_node.id, output_node.id, none_output_node.layer, output_node.layer)
        new_edges.append(none_chan_edge)

    # connect the two none nodes
    none_none_edge = create_edge(none_input_node.id, none_output_node.id, none_input_node.layer, none_output_node.layer)
    new_edges.append(none_none_edge)

    return input_layer_none_nodes, output_layer_none_nodes, new_edges

def write_sb_nodes(structure, nodes_to_write):
    rr_nodes = structure.find("rr_nodes")
    for node in nodes_to_write:
        new_node = node_xml_element(node)
        rr_nodes.append(new_node)
    
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
            print(f"ERROR: Input node is not in the correct location, node: {input_node}")
    
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
            print(f"ERROR: Output node is not in the correct location, node: {output_node}")
    
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

def create_combined_sb(input_nodes, output_nodes, x, y, input_layer, output_layer):
    # need to figure out which nodes to connect together for larger than 2 CWs

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
            print(f"ERROR: Input node is not in the correct location, node: {input_node}")
        
    #sort the nodes by ptc
    x_y_chanx_input_nodes = sorted(x_y_chanx_input_nodes, key=lambda x: int(x.ptc))
    x_y_chany_input_nodes = sorted(x_y_chany_input_nodes, key=lambda x: int(x.ptc))
    x_plus_1_y_chanx_input_nodes = sorted(x_plus_1_y_chanx_input_nodes, key=lambda x: int(x.ptc))
    x_y_plus_1_chany_input_nodes = sorted(x_y_plus_1_chany_input_nodes, key=lambda x: int(x.ptc))

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
            print(f"ERROR: Output node is not in the correct location, node: {output_node}")
    
    #sort the nodes by ptc
    x_y_chanx_output_nodes = sorted(x_y_chanx_output_nodes, key=lambda x: int(x.ptc))
    x_y_chany_output_nodes = sorted(x_y_chany_output_nodes, key=lambda x: int(x.ptc))
    x_plus_1_y_chanx_output_nodes = sorted(x_plus_1_y_chanx_output_nodes, key=lambda x: int(x.ptc))
    x_y_plus_1_chany_output_nodes = sorted(x_y_plus_1_chany_output_nodes, key=lambda x: int(x.ptc))

    assert len(x_y_chanx_input_nodes) == len(x_y_chanx_output_nodes)
    assert len(x_y_chany_input_nodes) == len(x_y_chany_output_nodes)
    assert len(x_plus_1_y_chanx_input_nodes) == len(x_plus_1_y_chanx_output_nodes)
    assert len(x_y_plus_1_chany_input_nodes) == len(x_y_plus_1_chany_output_nodes)

    # Now do a round robin connection between the input and output nodes
    # take an input node from each list (if one exists) and store it in a new list to be sent to function
    # maybe pop the elemnts from the list to keep track of which ones have been connected
    # Do the same for the output nodes

    # we will call connect_sb_nodes_combined for each set of input and output nodes
    input_layer_none_nodes = []
    output_layer_none_nodes = []
    new_edges = []

    max_len = max(len(x_y_chanx_input_nodes), len(x_y_chany_input_nodes), len(x_plus_1_y_chanx_input_nodes), len(x_y_plus_1_chany_input_nodes))

    for i in range(max_len):

        input_nodes_to_send = []
        output_nodes_to_send = []

        if i < len(x_y_chanx_input_nodes):
            input_nodes_to_send.append(x_y_chanx_input_nodes[i])
        if i < len(x_y_chany_input_nodes):
            input_nodes_to_send.append(x_y_chany_input_nodes[i])
        if i < len(x_plus_1_y_chanx_input_nodes):
            input_nodes_to_send.append(x_plus_1_y_chanx_input_nodes[i])
        if i < len(x_y_plus_1_chany_input_nodes):
            input_nodes_to_send.append(x_y_plus_1_chany_input_nodes[i])

        if i < len(x_y_chanx_output_nodes):
            output_nodes_to_send.append(x_y_chanx_output_nodes[i])
        if i < len(x_y_chany_output_nodes):
            output_nodes_to_send.append(x_y_chany_output_nodes[i])
        if i < len(x_plus_1_y_chanx_output_nodes):
            output_nodes_to_send.append(x_plus_1_y_chanx_output_nodes[i])
        if i < len(x_y_plus_1_chany_output_nodes):
            output_nodes_to_send.append(x_y_plus_1_chany_output_nodes[i])

        input_layer_none_nodes_temp, output_layer_none_nodes_temp, new_edges_temp = connect_sb_nodes_combined(input_nodes_to_send, output_nodes_to_send, x, y, input_layer, output_layer)
        input_layer_none_nodes += input_layer_none_nodes_temp
        output_layer_none_nodes += output_layer_none_nodes_temp
        new_edges += new_edges_temp

    return input_layer_none_nodes, output_layer_none_nodes, new_edges

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
    
    # Determine the step interval for selecting elements
    step = int(1 / (percent))

    # Select every `step`-th element
    for i in range(0, total_elements, step):
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

def create_sb(structure, is_combined=False):
    print("Creating SB connections")
    start_time = time.time()
    # loop over the device and find the highest CHAN x and y
    device_x, device_y, num_layers = find_device_chan_dim()

    # only create sbs for every other location
    global percent_connectitivty

    edges_to_write = []
    nodes_to_write = []

    num_created = 0

    # For each location, find all relevant chans that either enter or exit th SB
    for x, y in percentage_skip_2d_random(device_x, device_y, percent_connectitivty):
        num_created += 1
        print(f"Creating SB at location ({x}, {y})")
        iter_start_time = time.time()

        chan_nodes = find_chan_nodes(x, y)
        layer_0_sb_input_nodes, layer_0_sb_output_nodes, layer_1_sb_input_nodes, layer_1_sb_output_nodes = sort_chan_nodes_into_input_and_output(chan_nodes, x, y)
        input_layer_0_none_nodes = []
        output_layer_1_none_nodes = []
        input_layer_1_none_nodes = []
        output_layer_0_none_nodes = []
        new_edges_0 = []
        new_edges_1 = []

        # node_count_before = len(nodes_to_write)
        # edge_count_before = len(edges_to_write)
        if is_combined:
            input_layer_0_none_nodes, output_layer_1_none_nodes, new_edges_0 = create_combined_sb(layer_0_sb_input_nodes, layer_1_sb_output_nodes, x, y, 0, 1)
            input_layer_1_none_nodes, output_layer_0_none_nodes, new_edges_1 = create_combined_sb(layer_1_sb_input_nodes, layer_0_sb_output_nodes, x, y, 1, 0)
            nodes_to_write = nodes_to_write + input_layer_0_none_nodes + output_layer_1_none_nodes + input_layer_1_none_nodes + output_layer_0_none_nodes
            edges_to_write = edges_to_write + new_edges_0 + new_edges_1
        else:
            # for input_layer_node, output_layer_node, new_edges in itertools.chain(
            #     connect_sb_nodes_full(layer_0_sb_input_nodes, layer_1_sb_output_nodes),
            #     connect_sb_nodes_full(layer_1_sb_input_nodes, layer_0_sb_output_nodes),
            # ):
            #     nodes_to_write.extend((input_layer_node, output_layer_node))
            #     edges_to_write.extend(new_edges)
            
            new_nodes, new_edges = create_full_sb(layer_0_sb_input_nodes, layer_1_sb_output_nodes, x, y)
            nodes_to_write.extend(new_nodes)
            edges_to_write.extend(new_edges)

            new_nodes, new_edges = create_full_sb(layer_1_sb_input_nodes, layer_0_sb_output_nodes, x, y)
            nodes_to_write.extend(new_nodes)
            edges_to_write.extend(new_edges)

        iter_end_time = time.time()
        print(f"Creating SB at location ({x}, {y}) took {((iter_end_time - iter_start_time) * 1000):0.2f} ms")
        # print("added", len(nodes_to_write) - node_count_before, "nodes to make", total_size((nodes_to_write, node_data, node_index)) / (1024 * 1024 * 1024), "GiB, added", len(edges_to_write) - edge_count_before, "edges to make", total_size((edges_to_write, edge_data, edges_by_src, edges_by_sink)) / (1024 * 1024 * 1024), "GiB")
    
    print(f"\nNumber of new nodes: {len(nodes_to_write)}")
    print(f"Number of new edges: {len(edges_to_write)}\n")

    print("Sorting Nodes")
    sorting_start_time = time.time()
    nodes_to_write = sort_nodes(nodes_to_write)
    sorting_end_time = time.time()

    print(f"Sorting Nodes took { ((sorting_end_time - sorting_start_time) * 1000):0.2f} ms")

    print("Writing SB Nodes and Edges")
    writing_start_time = time.time()
    write_sb_nodes(structure, nodes_to_write)
    write_sb_edges(structure, edges_to_write)

    writing_end_time = time.time()
    print(f"Writing SB Nodes and Edges took { ((writing_end_time - writing_start_time) * 1000):0.2f} ms")

    end_time = time.time()
    print(f"Creating SB connections took { ((end_time - start_time) * 1000):0.2f} ms")

    print(f"Total number of SBs created: {num_created}")
    
def setup_ptc(structure):
    print(f"Setting up PTC array")
    start_time=time.time()

    rr_nodes = structure.find("rr_nodes")

    global ptc
    ptc = defaultdict(int)

    for node in rr_nodes.findall("node"):
        type = node.get("type")

        if type != "CHANX" and type != "CHANY":
            continue

        loc = node.find("loc")
        xlow = int(loc.get("xlow"))
        ylow = int(loc.get("ylow"))
        layer = int(loc.get("layer"))
        ptc_node = int(loc.get("ptc"))

        key = (layer, xlow, ylow)
        ptc[key] = max(ptc[key], ptc_node)

    end_time = time.time()
    print(f"Setting up PTC array took { ((end_time - start_time) * 1000):0.2f} ms")

def main():
    if len(sys.argv) < 3:
        print("Usage: python script.py <file_path> <output_file_path> <is_combined_sb> <percent_connectivity>")
        sys.exit(1)

    start_time = time.time()

    # Get the file path from the command-line argument
    file_path = sys.argv[1]
    output_file_path = sys.argv[2]
    is_combined_sb = True

    is_combined_sb = bool(int(sys.argv[3])) # Only 0 is seen as false
    
    global percent_connectitivty
    percent_connectitivty = float(sys.argv[4])

    print(f"Percent Connectivity: {percent_connectitivty}")

    print(f"Creating { 'combined' if is_combined_sb else 'full' } SBs for file {file_path}")
    structure, tree = read_structure(file_path)
    setup_ptc(structure)
    extract_nodes(structure)
    create_sb(structure, is_combined_sb)

    tree.write(output_file_path, pretty_print=True, xml_declaration=True, encoding="UTF-8")

    end_time = time.time()
    print(f"Generating SBs took { ((end_time - start_time) * 1000):0.2f} ms")
    
if __name__ == "__main__":
    main()
    # node_data.close()
    # edge_data.close()
