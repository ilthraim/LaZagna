from lxml import etree
from collections import namedtuple
import sys
from collections import defaultdict

node_struct = namedtuple("Node", ["id", "type", "layer", "xhigh", "xlow", "yhigh", "ylow", "side", "direction", "ptc", "segment_id"])
edge_struct = namedtuple("Edge", ["src_node", "sink_node", "src_layer", "sink_layer", "switch_id"])

node_data = {}
edge_data = {}

node_ids = defaultdict(int)

def extract_nodes(root):
    rr_nodes = root.find("rr_nodes")
    
    for node in rr_nodes.findall("node"):
        node_id = node.get("id")
        type = node.get("type")
        
        loc = node.find("loc")
        segment_id = "0"

        if type == "CHANX" or type == "CHANY":
            segment = node.find("segment")
            segment_id = segment.get("segment_id")



        layer = loc.get("layer")
        xhigh = loc.get("xhigh")
        xlow = loc.get("xlow")
        yhigh = loc.get("yhigh")
        ylow = loc.get("ylow")
        side = loc.get("side")
        ptc = loc.get("ptc")

        direction = node.get("direction")
        # global node_ids
        # if int(node_id) in node_ids:
        #     print(f"Node id {int(node_id)} already exists")
        #     node_ids[int(node_id)] += 1
        # else:
        #     node_ids[int(node_id)] = 1

        node_data[node_id] = node_struct(node_id, type, layer, xhigh, xlow, yhigh, ylow, side, direction, ptc, segment_id)

def extract_edges(root):
    rr_edges = root.find("rr_edges")
    
    for edge in rr_edges.findall("edge"):
        src_node = edge.get("src_node")
        sink_node = edge.get("sink_node")
        switch_id = edge.get("switch_id")

        src_node_data = node_data[src_node]
        sink_node_data = node_data[sink_node]

        src_layer = src_node_data.layer
        sink_layer = sink_node_data.layer

        edge_data[(src_node, sink_node)] = edge_struct(src_node, sink_node, src_layer, sink_layer, switch_id)

def classify_sb000_edges():
    # objects to hold the edge data
    opin_chan_edge = []
    chan_ipin_edge = []
    chan_chan_edge = []
    src_sink_edges = []
    chan_none_edges = []
    none_chan_edges = []
    none_none_edges = []
    misc_edges = []

    for edge, edge_info in edge_data.items():
        src_node = edge_info.src_node
        sink_node = edge_info.sink_node

        src_node_data = node_data[src_node]
        sink_node_data = node_data[sink_node]

        src_type = src_node_data.type
        sink_type = sink_node_data.type

        src_direction = src_node_data.direction
        sink_direction = sink_node_data.direction

        src_xlow = src_node_data.xlow
        src_ylow = src_node_data.ylow
        sink_xlow = sink_node_data.xlow
        sink_ylow = sink_node_data.ylow

        if src_type != "CHANX" and src_type != "CHANY" and sink_type != "CHANX" and sink_type != "CHANY":
            continue

        # Get sink nodes
        if (src_type == "CHANX" or src_type == "CHANY") and src_direction == "NONE" and sink_direction != "NONE":
            if sink_xlow == "1" and sink_ylow == "0":
                none_chan_edges.append(edge)
            elif sink_xlow == "0" and sink_ylow == "1":
                none_chan_edges.append(edge)

        elif (sink_type == "CHANX" or sink_type == "CHANY") and sink_direction == "NONE" and src_direction != "NONE":
            if src_xlow == "1" and src_ylow == "0":
                chan_none_edges.append(edge)
            elif src_xlow == "0" and src_ylow == "1":
                chan_none_edges.append(edge)

        elif (sink_type == "CHANX" or sink_type == "CHANY") and (src_type == "CHANX" or src_type == "CHANY") and sink_direction == "NONE" and src_direction == "NONE":
            if src_xlow == "1" and src_ylow == "0":
                none_none_edges.append(edge)
            elif src_xlow == "0" and src_ylow == "1":
                none_none_edges.append(edge)


    print(f"OPIN to CHANX/CHANY edges: {len(opin_chan_edge)}")
    print(f"CHANX/CHANY to IPIN edges: {len(chan_ipin_edge)}")
    print(f"CHANX/CHANY to CHANX/CHANY edges: {len(chan_chan_edge)}")
    print(f"Source and Sink edges: {len(src_sink_edges)}")
    print(f"CHANX/CHANY to NONE edges: {len(chan_none_edges)}")
    print(f"NONE to CHANX/CHANY edges: {len(none_chan_edges)}")
    print(f"NONE to NONE edges: {len(none_none_edges)}")
    print(f"Miscellaneous edges: {len(misc_edges)}")

    print("Chan-None edges:")
    for edge in chan_none_edges:
        src_node = edge_data[edge].src_node
        sink_node = edge_data[edge].sink_node
        src_node_data = node_data[src_node]
        sink_node_data = node_data[sink_node]
        print(f"\t{edge} Switch id: {edge_data[edge].switch_id}")
        print(f"\t\tSource node: {src_node} type: {src_node_data.type} layer: {src_node_data.layer} x: {src_node_data.xlow} y: {src_node_data.ylow} side: {src_node_data.side} direction: {src_node_data.direction}")
        print(f"\t\tSink node: {sink_node} type: {sink_node_data.type} layer: {sink_node_data.layer} x: {sink_node_data.xlow} y: {sink_node_data.ylow} side: {sink_node_data.side} direction: {sink_node_data.direction}")

    print()

    print("None-Chan edges:")
    for edge in none_chan_edges:
        src_node = edge_data[edge].src_node
        sink_node = edge_data[edge].sink_node
        src_node_data = node_data[src_node]
        sink_node_data = node_data[sink_node]
        print(f"\t{edge} Switch id: {edge_data[edge].switch_id}")
        print(f"\t\tSource node: {src_node} type: {src_node_data.type} layer: {src_node_data.layer} x: {src_node_data.xlow} y: {src_node_data.ylow} side: {src_node_data.side} direction: {src_node_data.direction}")
        print(f"\t\tSink node: {sink_node} type: {sink_node_data.type} layer: {sink_node_data.layer} x: {sink_node_data.xlow} y: {sink_node_data.ylow} side: {sink_node_data.side} direction: {sink_node_data.direction}")

    print()

    print("None-None edges:")
    for edge in none_none_edges:
        src_node = edge_data[edge].src_node
        sink_node = edge_data[edge].sink_node
        src_node_data = node_data[src_node]
        sink_node_data = node_data[sink_node]
        print(f"\t{edge} Switch id: {edge_data[edge].switch_id}")
        print(f"\t\tSource node: {src_node} type: {src_node_data.type} layer: {src_node_data.layer} x: {src_node_data.xlow} y: {src_node_data.ylow} side: {src_node_data.side} direction: {src_node_data.direction}")
        print(f"\t\tSink node: {sink_node} type: {sink_node_data.type} layer: {sink_node_data.layer} x: {sink_node_data.xlow} y: {sink_node_data.ylow} side: {sink_node_data.side} direction: {sink_node_data.direction}")

def get_sb_nodes_and_edges(x, y, layer):
    #Get all the nodes and edges that pertain to a particular switch block (layer, x, y)
    sb_input_nodes = []
    sb_output_nodes = []
    none_nodes = []
    sb_edges = []

    # how to tell if a node is part of SB
    # if its CHANX or CHANY and its xlow == x and ylow == y and layer == layer
    # if its CHANX and its xlow == x+1 and ylow == y and layer == layer
    # if its CHANY and its xlow == x and ylow == y+1 and layer == layer
    for node_id, node_info in node_data.items():
        if node_info.layer == layer:
            if node_info.type == "CHANX" and int(node_info.xlow) == int(x) and int(node_info.ylow) == int(y):
                if node_info.direction == "INC_DIR":
                    sb_input_nodes.append(node_id)
                elif node_info.direction == "DEC_DIR":
                    sb_output_nodes.append(node_id)
                elif node_info.direction == "NONE":
                    none_nodes.append(node_id)
            elif node_info.type == "CHANY" and int(node_info.xlow) == int(x) and int(node_info.ylow) == int(y):
                if node_info.direction == "INC_DIR":
                    sb_input_nodes.append(node_id)
                elif node_info.direction == "DEC_DIR":
                    sb_output_nodes.append(node_id)
                elif node_info.direction == "NONE":
                    none_nodes.append(node_id)
            elif node_info.type == "CHANX" and int(node_info.xlow) == int(x)+1 and int(node_info.ylow) == int(y):
                if node_info.direction == "DEC_DIR":
                    sb_input_nodes.append(node_id)
                elif node_info.direction == "INC_DIR":
                    sb_output_nodes.append(node_id)
            elif node_info.type == "CHANY" and int(node_info.xlow) == int(x) and int(node_info.ylow) == int(y)+1:
                if node_info.direction == "DEC_DIR":
                    sb_input_nodes.append(node_id)
                elif node_info.direction == "INC_DIR":
                    sb_output_nodes.append(node_id)
                   
    #How to tell if a edge is part of SB
    # if src_node and sink_node are in sb_nodes
    for edge, edge_info in edge_data.items():
        if edge_info.src_node in sb_input_nodes and edge_info.sink_node in sb_output_nodes:
            sb_edges.append(edge)

    #Maybe sort the nodes and edges by type and xlow, ylow
    sb_input_nodes.sort(key=lambda x: (node_data[x].type, node_data[x].xlow, node_data[x].ylow))
    sb_output_nodes.sort(key=lambda x: (node_data[x].type, node_data[x].xlow, node_data[x].ylow))
    none_nodes.sort(key=lambda x: (node_data[x].type, node_data[x].xlow, node_data[x].ylow))
    sb_edges.sort(key=lambda x: (edge_data[x].src_node, edge_data[x].sink_node))


    return sb_input_nodes, sb_output_nodes, none_nodes, sb_edges

# go through each edge in RRG and classfiy it's purpose:
def classify_edges(to_print=False):
    # objects to hold the edge data
    opin_chan_edge = []
    chan_ipin_edge = []
    chan_chan_edge = []
    src_sink_edges = []
    chan_none_edges = []
    none_chan_edges = []
    none_none_edges = []
    misc_edges = []

    for edge, edge_info in edge_data.items():
        src_node = edge_info.src_node
        sink_node = edge_info.sink_node

        src_node_data = node_data[src_node]
        sink_node_data = node_data[sink_node]

        src_type = src_node_data.type
        sink_type = sink_node_data.type

        src_direction = src_node_data.direction
        sink_direction = sink_node_data.direction

        if src_type == "OPIN" and (sink_type == "CHANX" or sink_type == "CHANY"):
            # print edge info
            # print(f"Edge: {edge}")
            # print(f"\tSource node: {src_node} type: {src_type} layer: {src_node_data.layer} x: {src_node_data.xlow} y: {src_node_data.ylow} side: {src_node_data.side} direction: {src_node_data.direction}")
            # print(f"\tSink node: {sink_node} type: {sink_type} layer: {sink_node_data.layer} x: {sink_node_data.xlow} y: {sink_node_data.ylow} side: {sink_node_data.side} direction: {sink_node_data.direction}")
            opin_chan_edge.append(edge)
        elif (src_type == "CHANX" or src_type == "CHANY") and sink_type == "IPIN":
            # print edge info
            # print(f"Edge: {edge}")
            # print(f"\tSource node: {src_node} type: {src_type} layer: {src_node_data.layer} x: {src_node_data.xlow} y: {src_node_data.ylow} side: {src_node_data.side} direction: {src_node_data.direction}")
            # print(f"\tSink node: {sink_node} type: {sink_type} layer: {sink_node_data.layer} x: {sink_node_data.xlow} y: {sink_node_data.ylow} side: {sink_node_data.side} direction: {sink_node_data.direction}")
            chan_ipin_edge.append(edge)
        elif (src_type == "CHANX" or src_type == "CHANY") and (sink_type == "CHANX" or sink_type == "CHANY") and sink_direction != 'NONE' and src_direction != 'NONE':
            # print edge info
            # print(f"Edge: {edge}")
            # print(f"\tSource node: {src_node} type: {src_type} layer: {src_node_data.layer} x: {src_node_data.xlow} y: {src_node_data.ylow} side: {src_node_data.side} direction: {src_node_data.direction}")
            # print(f"\tSink node: {sink_node} type: {sink_type} layer: {sink_node_data.layer} x: {sink_node_data.xlow} y: {sink_node_data.ylow} side: {sink_node_data.side} direction: {sink_node_data.direction}")
            chan_chan_edge.append(edge)
        elif (src_type == "SOURCE" or src_type == "SINK") or (sink_type == "SOURCE" or sink_type == "SINK"):
            # print(f"Edge: {edge}")
            # print(f"\tSource node: {src_node} type: {src_type} layer: {src_node_data.layer} x: {src_node_data.xlow} y: {src_node_data.ylow} side: {src_node_data.side} direction: {src_node_data.direction}")
            # print(f"\tSink node: {sink_node} type: {sink_type} layer: {sink_node_data.layer} x: {sink_node_data.xlow} y: {sink_node_data.ylow} side: {sink_node_data.side} direction: {sink_node_data.direction}")
            src_sink_edges.append(edge)
        elif src_direction != "NONE" and sink_direction == "NONE" and (sink_type == "CHANX" or sink_type == "CHANY") and (src_type == "CHANX" or src_type == "CHANY"):
            # print edge info
            # print(f"Edge: {edge}")
            # print(f"\tSource node: {src_node} type: {src_type} layer: {src_node_data.layer} x: {src_node_data.xlow} y: {src_node_data.ylow} side: {src_node_data.side} direction: {src_node_data.direction}")
            # print(f"\tSink node: {sink_node} type: {sink_type} layer: {sink_node_data.layer} x: {sink_node_data.xlow} y: {sink_node_data.ylow} side: {sink_node_data.side} direction: {sink_node_data.direction}")
            chan_none_edges.append(edge)
        elif src_direction == "NONE" and sink_direction != "NONE" and (sink_type == "CHANX" or sink_type == "CHANY") and (src_type == "CHANX" or src_type == "CHANY"):
            # print edge info
            # print(f"Edge: {edge}")
            # print(f"\tSource node: {src_node} type: {src_type} layer: {src_node_data.layer} x: {src_node_data.xlow} y: {src_node_data.ylow} side: {src_node_data.side} direction: {src_node_data.direction}")
            # print(f"\tSink node: {sink_node} type: {sink_type} layer: {sink_node_data.layer} x: {sink_node_data.xlow} y: {sink_node_data.ylow} side: {sink_node_data.side} direction: {sink_node_data.direction}")
            none_chan_edges.append(edge)
        elif src_direction == "NONE" and sink_direction == "NONE" and (sink_type == "CHANX" or sink_type == "CHANY") and (src_type == "CHANX" or src_type == "CHANY"):
            # print edge info
            # print(f"Edge: {edge}")
            # print(f"\tSource node: {src_node} type: {src_type} layer: {src_node_data.layer} x: {src_node_data.xlow} y: {src_node_data.ylow} side: {src_node_data.side} direction: {src_node_data.direction}")
            # print(f"\tSink node: {sink_node} type: {sink_type} layer: {sink_node_data.layer} x: {sink_node_data.xlow} y: {sink_node_data.ylow} side: {sink_node_data.side} direction: {sink_node_data.direction}")
            none_none_edges.append(edge)
        else:
            # print edge info
            # print(f"Edge: {edge}")
            # print(f"\tSource node: {src_node} type: {src_type} layer: {src_node_data.layer} x: {src_node_data.xlow} y: {src_node_data.ylow} side: {src_node_data.side} direction: {src_node_data.direction}")
            # print(f"\tSink node: {sink_node} type: {sink_type} layer: {sink_node_data.layer} x: {sink_node_data.xlow} y: {sink_node_data.ylow} side: {sink_node_data.side} direction: {sink_node_data.direction}")
            misc_edges.append(edge)

    print(f"OPIN to CHANX/CHANY edges: {len(opin_chan_edge)}")
    print(f"CHANX/CHANY to IPIN edges: {len(chan_ipin_edge)}")
    print(f"CHANX/CHANY to CHANX/CHANY edges: {len(chan_chan_edge)}")
    print(f"Source and Sink edges: {len(src_sink_edges)}")
    print(f"CHANX/CHANY to NONE edges: {len(chan_none_edges)}")
    print(f"NONE to CHANX/CHANY edges: {len(none_chan_edges)}")
    print(f"NONE to NONE edges: {len(none_none_edges)}")
    print(f"Miscellaneous edges: {len(misc_edges)}")

    if to_print:

        print("Chan-None edges:")
        for edge in chan_none_edges:
            src_node = edge_data[edge].src_node
            sink_node = edge_data[edge].sink_node
            src_node_data = node_data[src_node]
            sink_node_data = node_data[sink_node]
            print(f"\t{edge} Switch id: {edge_data[edge].switch_id}")
            print(f"\t\tSource node: {src_node} type: {src_node_data.type} layer: {src_node_data.layer} x: {src_node_data.xlow} y: {src_node_data.ylow} side: {src_node_data.side} direction: {src_node_data.direction} ptc: {src_node_data.ptc}")
            print(f"\t\tSink node: {sink_node} type: {sink_node_data.type} layer: {sink_node_data.layer} x: {sink_node_data.xlow} y: {sink_node_data.ylow} side: {sink_node_data.side} direction: {sink_node_data.direction} ptc: {sink_node_data.ptc}")

        print()

        print("None-Chan edges:")
        for edge in none_chan_edges:
            src_node = edge_data[edge].src_node
            sink_node = edge_data[edge].sink_node
            src_node_data = node_data[src_node]
            sink_node_data = node_data[sink_node]
            print(f"\t{edge} Switch id: {edge_data[edge].switch_id}")
            print(f"\t\tSource node: {src_node} type: {src_node_data.type} layer: {src_node_data.layer} x: {src_node_data.xlow} y: {src_node_data.ylow} side: {src_node_data.side} direction: {src_node_data.direction} ptc: {src_node_data.ptc}")
            print(f"\t\tSink node: {sink_node} type: {sink_node_data.type} layer: {sink_node_data.layer} x: {sink_node_data.xlow} y: {sink_node_data.ylow} side: {sink_node_data.side} direction: {sink_node_data.direction} ptc: {sink_node_data.ptc}")

        print()

        print("None-None edges:")
        for edge in none_none_edges:
            src_node = edge_data[edge].src_node
            sink_node = edge_data[edge].sink_node
            src_node_data = node_data[src_node]
            sink_node_data = node_data[sink_node]
            print(f"\t{edge} Switch id: {edge_data[edge].switch_id}")
            print(f"\t\tSource node: {src_node} type: {src_node_data.type} layer: {src_node_data.layer} x: {src_node_data.xlow} y: {src_node_data.ylow} side: {src_node_data.side} direction: {src_node_data.direction} ptc: {src_node_data.ptc}")
            print(f"\t\tSink node: {sink_node} type: {sink_node_data.type} layer: {sink_node_data.layer} x: {sink_node_data.xlow} y: {sink_node_data.ylow} side: {sink_node_data.side} direction: {sink_node_data.direction} ptc: {sink_node_data.ptc}")

def classify_channel_nodes(to_print=False):
    x_inc_nodes = []
    y_inc_nodes = []
    x_dec_nodes = []
    y_dec_nodes = []
    x_none_nodes = []
    y_none_nodes = []

    for node_id, node_info in node_data.items():
        if node_info.type == "CHANX":
            if node_info.direction == "INC_DIR":
                x_inc_nodes.append(node_id)
            elif node_info.direction == "DEC_DIR":
                x_dec_nodes.append(node_id)
            else:
                x_none_nodes.append(node_id)
        elif node_info.type == "CHANY":
            if node_info.direction == "INC_DIR":
                y_inc_nodes.append(node_id)
            elif node_info.direction == "DEC_DIR":
                y_dec_nodes.append(node_id)
            else:
                y_none_nodes.append(node_id)
    
    print(f"X-Increment nodes: {len(x_inc_nodes)}")
    print(f"Y-Increment nodes: {len(y_inc_nodes)}")
    print(f"X-Decrement nodes: {len(x_dec_nodes)}")
    print(f"Y-Decrement nodes: {len(y_dec_nodes)}")
    print(f"X-None nodes: {len(x_none_nodes)}")
    print(f"Y-None nodes: {len(y_none_nodes)}")

    if to_print:

        # Print none nodes
        print("X-None nodes:")
        for node in x_none_nodes:
            node_info = node_data[node]
            print(f"\tNode id: {node} type: {node_info.type} layer: {node_info.layer} x: {node_info.xlow} y: {node_info.ylow} side: {node_info.side} direction: {node_info.direction} ptc: {node_info.ptc}")
        
        print("Y-None nodes:")
        for node in y_none_nodes:
            node_info = node_data[node]
            print(f"\tNode id: {node} type: {node_info.type} layer: {node_info.layer} x: {node_info.xlow} y: {node_info.ylow} side: {node_info.side} direction: {node_info.direction} ptc: {node_info.ptc}")

def read_structure(file_path):
    try:
        tree = etree.parse(file_path)
        root = tree.getroot()
        return root

    except Exception as e:
        print(f"Error reading XML file: {e}")
        return None
    
def find_num_interlayer_edges():
    interlayer_edges = 0
    for edge, edge_info in edge_data.items():
        src_node = edge_info.src_node
        sink_node = edge_info.sink_node

        src_node_data = node_data[src_node]
        sink_node_data = node_data[sink_node]

        src_layer = src_node_data.layer
        sink_layer = sink_node_data.layer

        if sink_node_data.type == "IPIN" and (src_node_data.type != "CHANX" and src_node_data.type != "CHANY"):
            print(f"Sink IPIN node {sink_node} is driven by {src_node_data.type} node {src_node}")

        if src_layer != sink_layer:
            interlayer_edges += 1

    return interlayer_edges

def find_num_interlayer_nodes():
    #If a node has a sink on a different layer, it is an interlayer node
    # Keep interlyaer nodes in a set to avoid duplicates
    interlayer_nodes_set = set()
    for edge, edge_info in edge_data.items():
        sink_node = edge_info.sink_node
        sink_node_data = node_data[sink_node]

        src_node = edge_info.src_node
        node_info = node_data[src_node]
        if sink_node_data.layer != node_info.layer and src_node not in interlayer_nodes_set:
            interlayer_nodes_set.add(src_node)
    return len(interlayer_nodes_set)

def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py <file_path>")
        sys.exit(1)

    interlayer = False

    chan_only = False

    if len(sys.argv) == 3: #interlayer or chan_only options
        if sys.argv[2] == "-i":
            interlayer = True
        elif sys.argv[2] == "-c":
            chan_only = True
    


    # Get the file path from the command-line argument
    file_path = sys.argv[1]

    root = read_structure(file_path)
    extract_nodes(root)
    extract_edges(root)

    print(f"Number of nodes: {len(node_data)}")
    
    #find largest node id in node_ids
    # print(f"Largest node id: {max(node_ids)}")

    if (interlayer):

        # Get file name
        file_name = file_path.split("/")[-1]
        file_name = file_name.split(".")[0]

        #replace _ in name with -
        file_name = file_name.replace("_", "-")

        print(find_num_interlayer_edges())
        print(find_num_interlayer_nodes())

        sys.exit(0)

    print("\n##########################################################################################\n")

    while True:
        node_id = input("Enter the node id (-1 to exit, -2 for edge info [-20 to print edge info], -3 for node info [-30 to print node info], -4 for specific SB location): ")
        if node_id == "-2":
            classify_edges()
            print(f"\nNumber of interlayer edges: {find_num_interlayer_edges()}")
        elif node_id == "-20":
            classify_edges(True)
        elif node_id == "-3":
            classify_channel_nodes()
        elif node_id == "-30":
            classify_channel_nodes(True)
        elif node_id == "-4":
            print("Enter the SB location (x, y, layer): ")
            x = input("Enter x: ")
            y = input("Enter y: ")
            layer = input("Enter layer: ")
            sb_input_nodes, sb_output_nodes, none_nodes, sb_edges = get_sb_nodes_and_edges(x, y, layer)
            print(f"Switch block nodes: {len(sb_input_nodes) + len(sb_output_nodes)}")
            print(f"Switch block input nodes: {len(sb_input_nodes)}")
            print(f"Switch block output nodes: {len(sb_output_nodes)}")
            print(f"Switch block edges: {len(sb_edges)}")

            print("\nInput nodes:")
            for node in sb_input_nodes:
                node_info = node_data[node]
                print(f"\tNode id: {node} type: {node_info.type} layer: {node_info.layer} xlow: {node_info.xlow} xhigh: {node_info.xhigh} ylow: {node_info.ylow} yhigh: {node_info.yhigh} side: {node_info.side} direction: {node_info.direction} ptc: {node_info.ptc} segment_id: {node_info.segment_id}")

            print()

            print("Output nodes:")
            for node in sb_output_nodes:
                node_info = node_data[node]
                print(f"\tNode id: {node} type: {node_info.type} layer: {node_info.layer} xlow: {node_info.xlow} xhigh: {node_info.xhigh} ylow: {node_info.ylow} yhigh: {node_info.yhigh} side: {node_info.side} direction: {node_info.direction} ptc: {node_info.ptc} segment_id: {node_info.segment_id}")
            
            print()

            print("None nodes:")
            for node in none_nodes:
                node_info = node_data[node]
                print(f"\tNode id: {node} type: {node_info.type} layer: {node_info.layer} xlow: {node_info.xlow} xhigh: {node_info.xhigh} ylow: {node_info.ylow} yhigh: {node_info.yhigh} side: {node_info.side} direction: {node_info.direction} ptc: {node_info.ptc} segment_id: {node_info.segment_id}")
            
            print()

            for edge in sb_edges:
                edge_info = edge_data[edge]
                src_node = edge_info.src_node
                sink_node = edge_info.sink_node
                src_node_info = node_data[src_node]
                sink_node_info = node_data[sink_node]
                print(f"\tEdge: {edge} Switch id: {edge_info.switch_id}")
                print(f"\t\tSource node: {src_node} type: {src_node_info.type} layer: {src_node_info.layer} xlow: {src_node_info.xlow} xhigh: {src_node_info.xhigh} ylow: {src_node_info.ylow} yhigh: {src_node_info.yhigh} side: {src_node_info.side} direction: {src_node_info.direction} ptc: {src_node_info.ptc} segment_id: {src_node_info.segment_id}")
                print(f"\t\tSink node: {sink_node} type: {sink_node_info.type} layer: {sink_node_info.layer}  xlow: {sink_node_info.xlow} xhigh: {sink_node_info.xhigh} ylow: {sink_node_info.ylow} yhigh: {sink_node_info.yhigh} side: {sink_node_info.side} direction: {sink_node_info.direction} ptc: {sink_node_info.ptc} segment_id: {sink_node_info.segment_id}")
                                                                                                                            
        elif node_id != "-1":
            src_nodes = []
            sink_nodes = []
            print(f"\nNode id: {node_id} type: {node_data[node_id].type} layer: {node_data[node_id].layer} xlow: {node_data[node_id].xlow} xhigh: {node_data[node_id].xhigh} ylow: {node_data[node_id].ylow} yhigh: {node_data[node_id].yhigh} side: {node_data[node_id].side} direction: {node_data[node_id].direction} ptc: {node_data[node_id].ptc} segment_id: {node_data[node_id].segment_id}\n")
            for edge, edge_info in edge_data.items():
                if edge_info.src_node == node_id:
                    sink_nodes.append(edge_info.sink_node)
                if edge_info.sink_node == node_id:
                    src_nodes.append(edge_info.src_node)


            print(f"\nSources of node {node_id}:")
            if len(src_nodes) == 0:
                print("\tNo sources\n")
            else:
                for src_node in src_nodes:
                    if chan_only and (node_data[src_node].type != "CHANX" and node_data[src_node].type != "CHANY"):
                        continue
                    print(f"\tNode id: {src_node} type: {node_data[src_node].type} layer: {node_data[src_node].layer} xlow: {node_data[src_node].xlow} xhigh: {node_data[src_node].xhigh} ylow: {node_data[src_node].ylow} yhigh: {node_data[src_node].yhigh} side: {node_data[src_node].side} direction: {node_data[src_node].direction} ptc: {node_data[src_node].ptc} segment_id: {node_data[src_node].segment_id}\n")

            
            print(f"\nSinks of node {node_id}:")
            if len(sink_nodes) == 0:
                print("\tNo sinks\n")
            else:
                for sink_node in sink_nodes:
                    if chan_only and (node_data[sink_node].type != "CHANX" and node_data[sink_node].type != "CHANY"):
                        continue
                    print(f"\tNode id: {sink_node} type: {node_data[sink_node].type} layer: {node_data[sink_node].layer} xlow: {node_data[sink_node].xlow} xhigh: {node_data[sink_node].xhigh} ylow: {node_data[sink_node].ylow} yhigh: {node_data[sink_node].yhigh} side: {node_data[sink_node].side} direction: {node_data[sink_node].direction} ptc: {node_data[sink_node].ptc} segment_id: {node_data[sink_node].segment_id}\n")
            print("##########################################################################################\n")
        elif node_id == "-1":
            break

if __name__ == "__main__":
    main()
        