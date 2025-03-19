import subprocess
import tempfile
import os
import time
from arch_xml_modification import *
from file_handling import *
from script_editing import *

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

def run_task(original_dir, temp_dir=""):

    run_command = ["python3",
               original_dir + "/OpenFPGA/openfpga_flow/scripts/run_fpga_task.py",
               temp_dir]
    
    run_command_in_temp_dir(run_command, original_dir, handle_error=False, verbose=False)

def run_flow(original_dir, width, height, channel_width, benchmark_name="", temp_dir ="", type_sb="full", arch_path="", rrg_3d_path="", percent_connectivity=0.5, place_algorithm="cube_bb", connection_type="subset", run_num=1):
    print(f"Temp Dir for benchmark {benchmark_name}: {temp_dir}")

    start_time = time.time()
    run_task(original_dir, temp_dir)
    end_time = time.time()

    run_time = (end_time - start_time) * 1000
    print(f"\tRunning OpenFPGA task for benchmark {benchmark_name} took {run_time:0.2f} ms")

    # Now copy results into somewhere else maybe?
    # Feels a bit sketch should automate it so the reuslts are auto placed into nice named area but oh well
    task_result_path = "/run001/task_result.csv"
    results_path = "/results/3d_" + type_sb + "_cw_" + output_file_name(channel_width=channel_width, width=width, height=height, percent_connectivity=percent_connectivity, place_algorithm=place_algorithm, connection_type=connection_type, run_num=run_num) + "/"
    result_file_name = benchmark_name + "_results_cw_" + output_file_name(channel_width=channel_width, width=width, height=height, percent_connectivity=percent_connectivity, place_algorithm=place_algorithm, connection_type=connection_type, run_num=run_num) + ".csv"

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

def setup_flow(original_dir, width, height, channel_width, type_sb="full", percent_connectivity=0.5, place_algorithm="cube_bb", verilog_benchmarks=False, connection_type="subset", arch_file="", random_seed=1, run_num=1):
    
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
    
    if arch_file != "":
        input_file = arch_file
        output_file = original_dir + "/arch_files/vtr_arch_" + str(width) + "x" + str(height) + ".xml"   # Replace with your desired output file path

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
        create_custom_3d_rrg(rrg_path, rrg_3d_path, original_dir, percent_connectivity, connection_type)
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

    #append random seed to script
    append_random_seed_to_script(original_dir + "/task" + script_path, random_seed)

    # Make tasks_run directory
    #Output folder name based on parameters and time of run
    curr_time = time.strftime("%H:%M:%S", time.localtime())
    folder_name = "3d_" + type_sb + "_cw_" + output_file_name(channel_width=channel_width, width=width, height=height, percent_connectivity=percent_connectivity, place_algorithm=place_algorithm, connection_type=connection_type, run_num=run_num) + curr_time
    os.makedirs(original_dir + "/tasks_run/" + folder_name, exist_ok=True)
    return original_dir + "/tasks_run/" + folder_name

def cleanup_flow(original_dir):
    script_path ="/task/designs/bitstream_script.openfpga"

    start_time = time.time()
    remove_rr_graph_from_script(original_dir + script_path)
    remove_place_algorithm_from_script(original_dir + script_path)
    remove_cw_from_script(original_dir + script_path)
    remove_random_seed_from_script(original_dir + script_path)
    end_time = time.time()

    run_time = (end_time - start_time) * 1000
    print(f"\tCleaning Script took {run_time:0.2f} ms")

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

def create_custom_3d_rrg(base_arch_path, output_file_path, original_dir, percent_connectivity=0.5, connection_type="subset"):

    # Make sure the output directory exists
    os.makedirs(os.path.dirname(original_dir + output_file_path), exist_ok=True)

    command = ["python3", 
               original_dir + "/scripts/3d_sb_creator.py",
               "-f", original_dir + base_arch_path,
               "-o", original_dir + output_file_path,
               "-p", str(percent_connectivity),
               "-c", connection_type]
    
    run_command_in_temp_dir(command, original_dir, verbose=True)

def copy_results(original_dir, task_result_path, results_path, result_name, temp_dir=""):
        
    os.makedirs(os.path.dirname(original_dir + results_path), exist_ok=True)

    command = ["cp",
               temp_dir + task_result_path, 
               original_dir + results_path + result_name]
    
    run_command_in_temp_dir(command, original_dir)
