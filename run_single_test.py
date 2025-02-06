import subprocess
import tempfile
import os
import shutil
from lxml import etree
import time
from concurrent.futures import ThreadPoolExecutor
import csv

and2_blif_path = "/benchmarks/and2/and2.blif"

def run_command_in_temp_dir(command, original_dir, handle_error=True, verbose=False):
    """
    Run a command in a temporary directory.
    
    Args:
        command (list): Command to execute
        original_dir (str): Original working directory
    
    Returns:
        subprocess.CompletedProcess: Result of the command execution
    """
    if verbose:
        print("Running Command: ")
        command_string = " ".join(command)
        print(f"\t{command_string}")
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temporary_dir:
        try:
            # Change to the temporary directory
            os.chdir(temporary_dir)
            
            # Execute the command
            result = subprocess.run(command, 
                                  capture_output=True,
                                  text=True,
                                  check=True)
            if verbose:
                print("Command output:")
                print(result.stdout)
            
            return result
            
        except subprocess.CalledProcessError as e:
            if verbose:
                print(f"Command failed with error code {e.returncode}")
                print("Error output:")
                print(e.stdout)
                print(e.stderr)
            if handle_error:
                raise
        except FileNotFoundError:
            print(os.getcwd())
            print("Command not found. Please check the path and permissions.")
            raise
        finally:
            # Always change back to the original directory
            os.chdir(original_dir)

def create_base_rrg(original_dir:str, path_to_arch:str, channel_width=2, path_to_write_rrg="/base_rrg/rr_graph.xml", path_to_benchmark=and2_blif_path):
    
    # Make sure the output directory exists
    os.makedirs(os.path.dirname(original_dir + path_to_write_rrg), exist_ok=True)

    command = [original_dir + "/OpenFPGA/build/vtr-verilog-to-routing/vpr/vpr", 
                      original_dir + path_to_arch, 
                      original_dir + path_to_benchmark, 
                      "--route_chan_width", 
                      str(channel_width), 
                      "--write_rr_graph", 
                      original_dir + path_to_write_rrg,
                      "--clock_modeling",
                      "route"]
    
    run_command_in_temp_dir(command, original_dir, handle_error=False, verbose=False)

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

def set_fixed_layout_dimensions(root, width, height):
    """Set the width and height attributes of the fixed_layout element."""
    fixed_layout = root.find('.//fixed_layout') # recursively go through xml looking for fixed_layout node
    if fixed_layout is not None:
        fixed_layout.set('width', str(width))
        fixed_layout.set('height', str(height))
    else:
        print("No fixed_layout element found.")

def get_max_die_number(root):
    """Get the maximum die number among existing layers."""
    die_numbers = [int(layer.get('die')) for layer in root.findall('.//layer') if layer.get('die') is not None]
    return max(die_numbers) if die_numbers else -1  # Return -1 if no layers are found

def copy_layer_with_incremented_die(root, source_die, new_die):
    """Copy a layer with die=source_die and add a new layer with die=new_die."""
    layers = root.findall('.//layer')
    
    # Find the layer with die=source_die
    source_layer = None
    for layer in layers:
        if layer.get('die') == str(source_die):
            source_layer = layer
            break
    
    if source_layer is None:
        print(f"Layer with die='{source_die}' not found.")
        return False
    
    # Deep copy the source layer
    new_layer = etree.Element("layer", die=str(new_die))
    for element in source_layer:
        new_layer.append(etree.fromstring(etree.tostring(element)))
    
    # Append the new layer to fixed_layout
    fixed_layout = root.find('.//fixed_layout')
    if fixed_layout is not None:
        fixed_layout.append(new_layer)
        return True
    else:
        print("No fixed_layout element found.")
        return False

def add_new_layer(root, base_die=None):
    """Add a new layer by copying an existing layer and incrementing the die number."""
    if base_die is None:
        # Use the first layer if base_die is not specified
        layers = root.findall('.//layer')
        if not layers:
            print("No layers available to copy.")
            return
        base_die = layers[0].get('die')
    
    max_die = get_max_die_number(root)
    new_die = max_die + 1
    success = copy_layer_with_incremented_die(root, source_die=base_die, new_die=new_die)
    if success:
        print(f"New layer added with die='{new_die}'.")
    else:
        print("Failed to add new layer.")

def create_custom_3d_rrg(base_arch_path, output_file_path, original_dir, type_sb="full", percent_connectivity=0.5, connection_type="subset"):
    sb_type = "0" if type_sb == "full" else "1"

    # Make sure the output directory exists
    os.makedirs(os.path.dirname(original_dir + output_file_path), exist_ok=True)

    command = ["python3", 
               original_dir + "/scripts/3d_sb_creator.py",
               original_dir + base_arch_path,
               original_dir + output_file_path,
               sb_type,
               str(percent_connectivity),
               connection_type]
    
    run_command_in_temp_dir(command, original_dir, verbose=True)

def run_task(original_dir, temp_dir=""):

    run_command = ["python3",
               original_dir + "/OpenFPGA/openfpga_flow/scripts/run_fpga_task.py",
               temp_dir]
    
    run_command_in_temp_dir(run_command, original_dir, handle_error=False, verbose=False)

def append_cw_to_script(file_path, string_to_add):
    """
    Appends the Channel width to the line that starts with 'vpr' in the script file.

    Args:
        file_path (str): Path to the file to modify.
        string_to_add (str): String to append to the 'vpr' line.
    """
    with open(file_path, 'r') as file:
        lines = file.readlines()

    with open(file_path, 'w') as file:
        for line in lines:
            if line.startswith("vpr"):
                # Append the string to the line
                line = line.rstrip('\n') + " " + string_to_add + "\n"
            file.write(line)

def remove_cw_from_script(file_path):
    """
    Removes the last word from the line that starts with 'vpr' in the script file.

    Allows to run multiple CW automatically, not a perfect solution, 
    could be made more robust by auto generating the script instead of adding and removing to it
    TODO: Come back to this and make it more robust

    Args:
        file_path (str): Path to the file to modify.
    """
    with open(file_path, 'r') as file:
        lines = file.readlines()

    with open(file_path, 'w') as file:
        for line in lines:
            if line.startswith("vpr"):
                # Split the line into words, remove the last word, and rejoin
                words = line.rstrip('\n').split()
                if len(words) > 1:
                    line = " ".join(words[:-1]) + "\n"
                else:
                    line = ""  # If only "vpr" exists, remove the line entirely
            file.write(line)

def remove_rr_graph_from_script(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
    
    with open(file_path, 'w') as file:
        for line in lines:
            if line.startswith("vpr"):
                # Split the line into words, remove the last 2 word, and rejoin
                words = line.rstrip('\n').split()
                if len(words) > 1:
                    line = " ".join(words[:-2]) + "\n"
                else:
                    line = ""  # If only "vpr" exists, remove the line entirely
            file.write(line)

def remove_place_algorithm_from_script(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
    
    with open(file_path, 'w') as file:
        for line in lines:
            if line.startswith("vpr"):
                # Split the line into words, remove the last 2 word, and rejoin
                words = line.rstrip('\n').split()
                if len(words) > 1:
                    line = " ".join(words[:-2]) + "\n"
                else:
                    line = ""  # If only "vpr" exists, remove the line entirely
            file.write(line)

def copy_results(original_dir, task_result_path, results_path, result_name, temp_dir=""):
    if not os.path.exists(original_dir + results_path):
        mkdir_command = ["mkdir", original_dir + results_path]
        run_command_in_temp_dir(mkdir_command, original_dir)
        
    command = ["cp",
               temp_dir + task_result_path, 
               original_dir + results_path + result_name]
    
    run_command_in_temp_dir(command, original_dir)

def generate_empty_results(original_dir, result_path, result_file_name, benchmark_name):
    csv_headers = ["name", "TotalRunTime", "average_net_length", "clb_blocks", "critical_path", "io_blocks", "packing_time", "placement_time", "routing_time", "total_logic_block_area", "total_routing_area", "total_routing_time", "total_wire_length"]
    csv_results = ["00_" + benchmark_name + "_Common", 0,0,0,0,0,0,0,0,0,0,0,0]

    os.makedirs(os.path.dirname(original_dir + result_path), exist_ok=True)

    with open(original_dir + result_path + result_file_name, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(csv_headers)  # Write headers
        writer.writerow(csv_results)  # Write data

def run_flow(original_dir, width, height, channel_width, benchmark_name="", temp_dir ="", type_sb="full", arch_path="", rrg_3d_path="", percent_connectivity=0.5, place_algorithm="cube_bb", connection_type="subset"):
    print(f"Temp Dir for benchmark {benchmark_name}: {temp_dir}")

    start_time = time.time()
    run_task(original_dir, temp_dir)
    end_time = time.time()

    run_time = (end_time - start_time) * 1000
    print(f"\tRunning OpenFPGA task for benchmark {benchmark_name} took {run_time:0.2f} ms")

    # Now copy results into somewhere else maybe?
    # Feels a bit sketch should automate it so the reuslts are auto placed into nice named area but oh well
    task_result_path = "/run001/task_result.csv"
    results_path = "/results/3d_" + type_sb + "_cw_" + output_file_name(channel_width=channel_width, width=width, height=height, percent_connectivity=percent_connectivity, place_algorithm=place_algorithm, connection_type=connection_type) + "/"
    result_file_name = benchmark_name + "_results_cw_" + output_file_name(channel_width=channel_width, width=width, height=height, percent_connectivity=percent_connectivity, place_algorithm=place_algorithm, connection_type=connection_type) + ".csv"

    print(f"\Trying to copy for benchmark {benchmark_name} the results to {original_dir + results_path + result_file_name} from {temp_dir + task_result_path}")

    # Make sure the results directory exists
    os.makedirs(original_dir + "/results", exist_ok=True)

    if os.path.exists(temp_dir + task_result_path):
        start_time = time.time()
        copy_results(original_dir, task_result_path, results_path, result_file_name, temp_dir)
        end_time = time.time()

        run_time = (end_time - start_time) * 1000
        print(f"\tCopying the results for benchmark {benchmark_name} to {original_dir + results_path + result_file_name} took {run_time:0.2f} ms")
    else:
        start_time = time.time()
        generate_empty_results(original_dir, results_path, result_file_name, benchmark_name)
        end_time = time.time()

        run_time = (end_time - start_time) * 1000
        print(f"\tGenerating Empty Results file and writing to {original_dir + results_path + result_file_name} took {run_time:0.2f} ms")

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

def update_config_simple(config_path, benchmark_blif, benchmark_name, benchmark_act, benchmark_verilog):
    """
    Updates specific keys in the configuration file: 'bench0', 'bench0_top',
    'bench0_act', and 'bench0_verilog'.

    Args:
        config_path (str): Path to the configuration file.
        bench_file (str): New value for 'bench0'.
        bench_top (str): New value for 'bench0_top'.
        bench_act (str): New value for 'bench0_act'.
        bench_verilog (str): New value for 'bench0_verilog'.
    """
    with open(config_path, 'r') as file:
        lines = file.readlines()

    updated_lines = []
    for line in lines:
        # Replace lines with the matching keys
        if line.strip().startswith("bench0="):
            updated_lines.append(f"bench0={benchmark_blif}\n")
        elif line.strip().startswith("bench0_top="):
            updated_lines.append(f"bench0_top={benchmark_name}\n")
        elif line.strip().startswith("bench0_act="):
            updated_lines.append(f"bench0_act={benchmark_act}\n")
        elif line.strip().startswith("bench0_verilog="):
            updated_lines.append(f"bench0_verilog={benchmark_verilog}\n")
        else:
            updated_lines.append(line)

    # Write the updated lines back to the file
    with open(config_path, 'w') as file:
        file.writelines(updated_lines)

def update_config_verilog(config_path, benchmark_verilog, benchmark_name):
    
    with open(config_path, 'r') as file:
        lines = file.readlines()

    updated_lines = []
    for line in lines:
        # Replace lines with the matching keys
        if line.strip().startswith("bench0="):
            updated_lines.append(f"bench0={benchmark_verilog}\n")
        elif line.strip().startswith("bench0_top="):
            updated_lines.append(f"bench0_top=top\n")
        else:
            updated_lines.append(line)

    # Write the updated lines back to the file
    with open(config_path, 'w') as file:
        file.writelines(updated_lines)

def output_file_name(channel_width, width, height, percent_connectivity, place_algorithm,  connection_type):
    return str(channel_width) + "_" + str(width) + "x" + str(height) + "_" + str(int(percent_connectivity * 100)) + "percent_" + place_algorithm + "_" + connection_type

def run_one_benchmark(i, blif_file="", verilog_file="", act_file="", original_dir="", width="", height="", channel_width="", type_sb="full", percent_connectivity=0.5, place_algorithm="cube_bb", verilog_benchmarks=False, connection_type="subset"):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_task_dir = os.path.join(temp_dir, "task")
        # copy config
        command = ["mkdir", temp_task_dir]
        run_command_in_temp_dir(command, original_dir)


        command = ["cp", "-r", original_dir + "/task/config", temp_task_dir + "/config"]
        run_command_in_temp_dir(command, original_dir)
    
        # make designs folder
        command = ["mkdir", temp_task_dir + "/designs"]
        run_command_in_temp_dir(command, original_dir)

        # copy script and designs
        command = ["cp", original_dir + "/task/designs/bitstream_script.openfpga", original_dir + "/task/designs/vtr_arch.xml", original_dir + "/task/designs/openfpga_arch.xml", original_dir + "/task/designs/auto_sim_openfpga.xml", temp_task_dir + "/designs/"]
        run_command_in_temp_dir(command, original_dir)

        # design_variables file
        command = ["cp", original_dir + "/task/design_variables.yml", temp_task_dir]
        run_command_in_temp_dir(command, original_dir)

        if verilog_benchmarks:
            update_config_verilog(temp_task_dir + "/config/task.conf", verilog_file, extract_file_name(verilog_file))
        else:
            update_config_simple(temp_task_dir + "/config/task.conf", blif_file, extract_file_name(blif_file), act_file, verilog_file)

        print(f"Running Benchmark: {i} {extract_file_name(verilog_file)} with Width: {width}, Height: {height}, Channel Width: {channel_width}")

        start_time = time.time()
        run_flow(original_dir=original_dir, width=width, height=height, channel_width=channel_width, benchmark_name=extract_file_name(verilog_file), temp_dir=temp_task_dir, type_sb=type_sb, percent_connectivity=percent_connectivity, place_algorithm=place_algorithm, connection_type=connection_type)
        end_time = time.time()

        elapsed_time_ms = (end_time - start_time) * 1000
        print(f"\tBenchmark {extract_file_name(verilog_file)} took {elapsed_time_ms:.2f} ms")

        # Make sure tasks_run folder exists
        os.makedirs(original_dir + "/tasks_run", exist_ok=True)

        # copy task folder for reference
        command = ["cp", "-r", temp_task_dir, original_dir + "/tasks_run/task_" + extract_file_name(verilog_file) + "_cw_" + output_file_name(channel_width=channel_width, width=width, height=height, percent_connectivity=percent_connectivity, place_algorithm=place_algorithm, connection_type=connection_type)]
        run_command_in_temp_dir(command, original_dir)

def append_rrg_to_script(script_path, rrg_path):
    with open(script_path, 'r') as file:
        lines = file.readlines()

    with open(script_path, 'w') as file:
        for line in lines:
            if line.startswith("vpr"):
                # Append the string to the line
                line = line.rstrip('\n') + " " + "--read_rr_graph " + rrg_path + "\n"
            file.write(line)

def append_place_algorithm_to_script(script_path, place_algorithm="cube_bb"):
    assert(place_algorithm == "cube_bb" or place_algorithm == "per_layer_bb")

    with open(script_path, 'r') as file:
        lines = file.readlines()

    with open(script_path, 'w') as file:
        for line in lines:
            if line.startswith("vpr"):
                # Append the string to the line
                line = line.rstrip('\n') + " " + "--place_bounding_box_mode " + place_algorithm + "\n"
            file.write(line)

def setup_flow(original_dir, width, height, channel_width, type_sb="full", percent_connectivity=0.5, place_algorithm="cube_bb", verilog_benchmarks=False, connection_type="subset"):
    
    # copy template script to designs
    command = ["cp", original_dir + "/task/config_templates/bitstream_script_template.openfpga", original_dir + "/task/designs/bitstream_script.openfpga"]
    run_command_in_temp_dir(command, original_dir)

    script_path ="/designs/bitstream_script.openfpga"

    if type_sb == "3d_cb":
        input_file = original_dir + "/arch_files/templates/vtr_3d_cb_arch.xml"     # Replace with your input file path
        output_file = original_dir + "/arch_files/3d_cb_arch/vtr_3d_cb_arch_" + str(width) + "x" + str(height) + ".xml"   # Replace with your desired output file path
    elif type_sb == "2d":
        input_file = original_dir + "/arch_files/templates/vtr_2d_arch.xml"     # Replace with your input file path
        output_file = original_dir + "/arch_files/2d_arch/vtr_2d_arch_" + str(width) + "x" + str(height) + ".xml"   # Replace with your desired output file path
    elif type_sb == "3d_cb_out_only":
        input_file = original_dir + "/arch_files/templates/vtr_3d_cb_out_only_arch.xml"     # Replace with your input file path
        output_file = original_dir + "/arch_files/3d_cb_arch/vtr_3d_cb_out_only_arch_" + str(width) + "x" + str(height) + ".xml"   # Replace with your desired output file path
    else:
        # Load the XML file
        input_file = original_dir + "/arch_files/templates/vtr_arch.xml"     # Replace with your input file path
        output_file = original_dir + "/arch_files/3d_arch/vtr_arch_" + str(width) + "x" + str(height) + ".xml"   # Replace with your desired output file path
    
    # Check if the modified Arch XML already exists, if not make it
    if not os.path.exists(original_dir + output_file):

        start_time = time.time()
        tree, root = load_xml(input_file)
        end_time = time.time()

        run_time = (end_time - start_time) * 1000
        print(f"\tLoading Base Arch XML took {run_time:0.2f} ms")

        start_time = time.time()
        set_fixed_layout_dimensions(root, width=width, height=height)
        end_time = time.time()

        run_time = (end_time - start_time) * 1000
        print(f"\tModifiying Base Arch XML took {run_time:0.2f} ms")

        start_time = time.time()
        save_xml(tree, output_file)
        end_time = time.time()

        run_time = (end_time - start_time) * 1000
        print(f"\tSaving the modified Arch XML took {run_time:0.2f} ms")
    else:
        print(f"\tModified Arch XML previously generated")
    
    # copy the modified arch file into the task
    command = ["cp", output_file, original_dir + "/task/designs/vtr_arch.xml"]
    run_command_in_temp_dir(command, original_dir)

    relative_arch_path = os.path.relpath(output_file, original_dir)
    relative_arch_path = "/" + relative_arch_path

    start_time = time.time()
    append_cw_to_script(original_dir + "/task" + script_path, str(channel_width))
    end_time = time.time()

    run_time = (end_time - start_time) * 1000
    print(f"\tAdding Channel Width to execution script took {run_time:0.2f} ms")

    start_time = time.time()
    append_place_algorithm_to_script(original_dir + "/task" + script_path, place_algorithm)
    end_time = time.time()

    run_time = (end_time - start_time) * 1000
    print(f"\tAdding Placement Algorithm to execution script took {run_time:0.2f} ms")

    rrg_path = "/base_rrg/rrg_cw_" + str(channel_width) + "_" + os.path.basename(relative_arch_path)

    rrg_3d_path = "/rrg_3d/rrg_3d_" + type_sb + "_cw_" + str(channel_width) + "_" + str(int(percent_connectivity * 100)) + "percent_" + connection_type + "_" + os.path.basename(relative_arch_path)

    # if base rrg does not exist, create it (AKA run VTR)
    if not os.path.exists(original_dir + rrg_path):
        start_time = time.time()
        create_base_rrg(original_dir, relative_arch_path, channel_width=channel_width, path_to_write_rrg=rrg_path)
        end_time = time.time()

        run_time = (end_time - start_time) * 1000
        print(f"\tGenerating Base RRG took {run_time:0.2f} ms")
    else:
        print(f"\tBase RRG previously generated")

    # if 3d rrg does not exist, create it
    if not os.path.exists(original_dir + rrg_3d_path) and type_sb != "3d_cb" and type_sb != "2d" and type_sb != "3d_cb_out_only":
        start_time = time.time()
        create_custom_3d_rrg(rrg_path, rrg_3d_path, original_dir, type_sb, percent_connectivity, connection_type)
        end_time = time.time()

        run_time = (end_time - start_time) * 1000
        print(f"\tGenerating 3D RRG from Base RRG took {run_time:0.2f} ms")    
    else:
        print(f"\t3D RRG previously generated")

    if type_sb == "3d_cb" or type_sb == "2d" or type_sb == "3d_cb_out_only":
    # Copy 3D RRG into task
        command = ["cp", original_dir + rrg_path, original_dir + "/task/designs/rr_graph.xml"]
        run_command_in_temp_dir(command, original_dir)
    else:
        command = ["cp", original_dir + rrg_3d_path, original_dir + "/task/designs/rr_graph.xml"]
        run_command_in_temp_dir(command, original_dir)

    # add the 3D RRG to the script
    append_rrg_to_script(original_dir + "/task" + script_path, original_dir + "/task/designs/rr_graph.xml")

    if verilog_benchmarks:
        command = ["cp", original_dir + "/task/config_templates/verilog_task.conf", original_dir + "/task/config/task.conf"]
        run_command_in_temp_dir(command, original_dir)
    else:
        command = ["cp", original_dir + "/task/config_templates/blif_task.conf", original_dir + "/task/config/task.conf"]
        run_command_in_temp_dir(command, original_dir)

def cleanup_flow(original_dir):
    script_path ="/task/designs/bitstream_script.openfpga"

    start_time = time.time()
    remove_rr_graph_from_script(original_dir + script_path)
    remove_place_algorithm_from_script(original_dir + script_path)
    remove_cw_from_script(original_dir + script_path)
    end_time = time.time()

    run_time = (end_time - start_time) * 1000
    print(f"\tCleaning Script took {run_time:0.2f} ms")


ITD_paper_top_modules = [{"attention_layer.v":"attention_layer"},{ "bnn.v":"bnn"},{"bwave_like.fixed.large.v" :"NPU"},{"bwave_like.fixed.small.v" :"NPU"},
                         {"clstm_like.large.v" :"C_LSTM_datapath"},{"clstm_like.medium.v" :"C_LSTM_datapath"},{"clstm_like.small.v" :"C_LSTM_datapath"}, 
                        { "conv_layer_hls.v":"top"},{ "conv_layer.v":"conv_layer"},{"dla_like.medium.v" :"DLA"},{"dla_like.small.v" :"DLA"},
                        {"dnnweaver.v" :"dnnweaver2_controller"}, {"eltwise_layer.v" :"eltwise_layer"},{"lenet.v" :"myproject"},
                        {"lstm.v" :"top"},{"proxy.5.v" :"top"},{"proxy.7.v" :"top"}, 
                        {"reduction_layer.v" :"reduction_layer"},{ "robot_rl.v":"robot_maze"},{"softmax.v" :"SoftMax"},{"spmv.v" :"spmv"},
                        {"tdarknet_like.large.v" :"td_fused_top"},{"tpu_like.large.os.v" :"top"},{"tpu_like.large.ws.v" :"top"},{ "tpu_like.small.ws.v":"top"}]

def main():
    percents_to_test = [1]
    place_algs = ["per_layer_bb"]
    connection_types = ["subset"]
    # type_sbs = ["3d_cb", "2d", "3d_cb_out_only"]

    for k in range(len(percents_to_test)):
        for j in range(len(connection_types)):
            for i in range(len(place_algs)):
                main_start_time = time.time()

                original_dir = os.getcwd()

                verilog_benchmarks = True # True if using verilog benchmarks (Koios), False if using blif benchmarks (MCNC)
                benchmarks_dir = original_dir + "/benchmarks" + "/ITD_paper" # "/MCNC_benchmarks" or "/koios" (need to retrieve)

                if verilog_benchmarks:
                    blif_files = get_files_with_extension(benchmarks_dir, ".v")
                    verilog_files = get_files_with_extension(benchmarks_dir, ".v")
                    act_files = get_files_with_extension(benchmarks_dir, ".v")
                else:
                    blif_files = get_files_with_extension(benchmarks_dir, ".blif")
                    verilog_files = get_files_with_extension(benchmarks_dir, ".v")
                    act_files = get_files_with_extension(benchmarks_dir, ".act")



                new_width = 200    # Set your desired width
                new_height = 200   # Set your desired height

                channel_width = 500
                type_sb = "2d" # "full" or "combined" or "3d_cb" or "2d" or "3d_cb_out_only"
                percent_connectivity = percents_to_test[k]
                place_algorithm = place_algs[i]

                connection_type = connection_types[j] # "subset" or "wilton"


                legal_choices = ["full", "combined", "3d_cb", "2d", "3d_cb_out_only"]
                if type_sb not in legal_choices:    
                    print(f"Invalid SB type: {type_sb}. Please choose from {legal_choices}")
                    return

                setup_flow(original_dir, new_width, new_height, channel_width, type_sb, percent_connectivity=percent_connectivity, place_algorithm=place_algorithm, verilog_benchmarks=verilog_benchmarks, connection_type=connection_type)

                # Parallelized
                with ThreadPoolExecutor() as executor:
                    futures = [
                        executor.submit(run_one_benchmark, i, blif_files[i], verilog_files[i], act_files[i], original_dir, new_width, new_height, channel_width, type_sb, percent_connectivity, place_algorithm, verilog_benchmarks, connection_type)
                        for i in range(len(blif_files))
                    ]

                    for future in futures:
                        future.result()

                # Serialized
                # for i in range(len(blif_files)):
                #     run_one_benchmark(i, blif_files[i], verilog_files[i], act_files[i], original_dir, new_width, new_height, channel_width, type_sb, percent_connectivity, place_algorithm, verilog_benchmarks, connection_type)
                
                cleanup_flow(original_dir)

                main_end_time = time.time()

                main_runtime = (main_end_time - main_start_time) * 1000

                print(f"\nRunning all tasks took: {main_runtime:.2f} ms")

if __name__ == "__main__":
    main()
