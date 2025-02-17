import os
from lxml import etree
import csv

def load_xml(file_path):
    """Load an XML file and return the tree and root elements."""
    tree = etree.parse(file_path)
    root = tree.getroot()
    return tree, root

def save_xml(tree, file_path):
    """Save the XML tree to a file."""

    # Make sure the directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    tree.write(file_path, pretty_print=True, xml_declaration=True, encoding='UTF-8')

def generate_empty_results(original_dir, result_path, result_file_name, benchmark_name):
    csv_headers = ["name", "TotalRunTime", "average_net_length", "clb_blocks", "critical_path", "io_blocks", "packing_time", "placement_time", "routing_time", "total_logic_block_area", "total_routing_area", "total_routing_time", "total_wire_length"]
    csv_results = ["00_" + benchmark_name + "_Common", 0,0,0,0,0,0,0,0,0,0,0,0]

    os.makedirs(os.path.dirname(original_dir + result_path), exist_ok=True)

    with open(original_dir + result_path + result_file_name, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(csv_headers)  # Write headers
        writer.writerow(csv_results)  # Write data

def get_files_with_extension(directory, extension):
    """
    Recursively finds all files with the '.blif' extension in the given directory.
    
    Args:
        directory (str): The path to the directory to search.
        
    Returns:
        list: A list of full paths to each '.blif' file.
    """
    blif_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(extension):
                blif_files.append(os.path.join(root, file))
    return blif_files

def extract_file_name(file_path):
    base_name = os.path.basename(file_path)
    name_without_extension = os.path.splitext(base_name)[0]
    return name_without_extension

def output_file_name(channel_width, width, height, percent_connectivity, place_algorithm,  connection_type):
    return str(channel_width) + "_" + str(width) + "x" + str(height) + "_" + str(int(percent_connectivity * 100)) + "percent_" + place_algorithm + "_" + connection_type
