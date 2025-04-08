import tempfile
import os
import time
from concurrent.futures import ThreadPoolExecutor
import random
from script_editing import update_config_simple, update_config_verilog
from run_flow import *
from printing import print_verbose
import printing

def run_one_benchmark(i, blif_file="", verilog_file="", act_file="", original_dir="", width="", height="", channel_width="", type_sb="full", percent_connectivity=0.5, place_algorithm="cube_bb", verilog_benchmarks=False, connection_type="subset", benchmark_top_name="", output_folder_name="", run_number=1, output_additional_info="", temp_template_dir=""):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_task_dir = os.path.join(temp_dir, "task")
        # copy config
        os.makedirs(temp_task_dir, exist_ok=True)

        command = ["cp", "-r", temp_template_dir + "/task/config", temp_task_dir + "/config"]
        run_command_in_temp_dir(command, original_dir)

        os.makedirs(temp_task_dir + "/designs", exist_ok=True)

        # copy script and designs
        command = ["cp", temp_template_dir + "/task/designs/bitstream_script.openfpga", temp_template_dir + "/task/designs/vtr_arch.xml", temp_template_dir + "/task/designs/openfpga_arch.xml", temp_template_dir + "/task/designs/auto_sim_openfpga.xml", temp_task_dir + "/designs/"]
        run_command_in_temp_dir(command, original_dir)

        # design_variables file
        command = ["cp", temp_template_dir + "/task/design_variables.yml", temp_task_dir]
        run_command_in_temp_dir(command, original_dir)

        if verilog_benchmarks:
            update_config_verilog(temp_task_dir + "/config/task.conf", verilog_file, benchmark_top_name)
        else:
            update_config_simple(temp_task_dir + "/config/task.conf", blif_file, extract_file_name(blif_file), act_file, verilog_file)

        print_verbose(f"Running Benchmark: {i} {extract_file_name(verilog_file)} with Width: {width}, Height: {height}, Channel Width: {channel_width}")

        start_time = time.time()
        run_flow(original_dir=original_dir, width=width, height=height, channel_width=channel_width, benchmark_name=extract_file_name(verilog_file), temp_dir=temp_task_dir, type_sb=type_sb, percent_connectivity=percent_connectivity, place_algorithm=place_algorithm, connection_type=connection_type, run_num=run_number, output_additional_info=output_additional_info)
        end_time = time.time()

        elapsed_time_ms = (end_time - start_time) * 1000
        print_verbose(f"\tBenchmark {extract_file_name(verilog_file)} took {elapsed_time_ms:.2f} ms")

        # Make sure tasks_run folder exists
        os.makedirs(original_dir + "/tasks_run", exist_ok=True)

        # copy task folder for reference

        # interesting files for me
        route_file_path = temp_task_dir + f"/latest/vtr_arch/{extract_file_name(verilog_file)}/Common/{extract_file_name(verilog_file)}.route"
        place_file_path = temp_task_dir + f"/latest/vtr_arch/{extract_file_name(verilog_file)}/Common/{extract_file_name(verilog_file)}.place"
        timing_results_path = temp_task_dir + f"/latest/vtr_arch/{extract_file_name(verilog_file)}/Common/report_timing.setup.rpt"

        os.makedirs(output_folder_name + "/task_" + extract_file_name(verilog_file), exist_ok=True)

        command = ["cp", "-f", route_file_path, output_folder_name + "/task_" + extract_file_name(verilog_file) + "/"]
        run_command_in_temp_dir(command, original_dir)

        command = ["cp", "-f", place_file_path, output_folder_name + "/task_" + extract_file_name(verilog_file) + "/"]
        run_command_in_temp_dir(command, original_dir)

        command = ["cp", "-f", timing_results_path, output_folder_name + "/task_" + extract_file_name(verilog_file) + "/"]
        run_command_in_temp_dir(command, original_dir)

        # command = ["cp", "-r", temp_task_dir, output_folder_name + "/task_" + extract_file_name(verilog_file)]
        # run_command_in_temp_dir(command, original_dir)

ITD_paper_top_modules = {
                         "attention_layer.v":"attention_layer",
                         "bnn.v":"bnn",
                         "bwave_like.fixed.large.v" :"NPU",
                         "bwave_like.fixed.small.v" :"NPU",
                         "clstm_like.large.v" :"C_LSTM_datapath",
                         "clstm_like.medium.v" :"C_LSTM_datapath",
                         "clstm_like.small.v" :"C_LSTM_datapath",
                         "conv_layer_hls.v":"top",
                         "conv_layer.v":"conv_layer",
                         "dla_like.medium.v" :"DLA",
                         "dla_like.small.v" :"DLA",
                         "dnnweaver.v" :"dnnweaver2_controller",
                         "eltwise_layer.v" :"eltwise_layer",
                         "lenet.v" :"myproject",
                         "lstm.v" :"top",
                         "proxy.5.v" :"top",
                         "proxy.7.v" :"top",
                         "reduction_layer.v" :"reduction_layer",
                         "robot_rl.v":"robot_maze",
                         "softmax.v" :"softmax",
                         "spmv.v" :"spmv",
                         "tdarknet_like.large.v" :"td_fused_top",
                         "tpu_like.large.os.v" :"top",
                         "tpu_like.large.ws.v" :"top",
                         "tpu_like.small.ws.v":"top"
                         }

ITD_subset_top_modules = {
                         "attention_layer.v":"attention_layer",
                         "bnn.v":"bnn",
                         "bwave_like.fixed.large.v" :"NPU",
                         "bwave_like.fixed.small.v" :"NPU",
                         "conv_layer_hls.v":"top",
                         "conv_layer.v":"conv_layer",
                         "dla_like.medium.v" :"DLA",
                         "dla_like.small.v" :"DLA",
                         "dnnweaver.v" :"dnnweaver2_controller",
                         "eltwise_layer.v" :"eltwise_layer",
                         "lstm.v" :"top",
                         "proxy.5.v" :"top",
                         "reduction_layer.v" :"reduction_layer",
                         "robot_rl.v":"robot_maze",
                         "softmax.v" :"softmax",
                         "spmv.v" :"spmv",
                         "tpu_like.large.os.v" :"top",
                         "tpu_like.large.ws.v" :"top",
                         "tpu_like.small.ws.v":"top"
                         }

ITD_quick_top_modules = {
                         "attention_layer.v":"attention_layer",
                         "bwave_like.fixed.small.v" :"NPU",
                         "conv_layer_hls.v":"top",
                         "conv_layer.v":"conv_layer",
                         "dnnweaver.v" :"dnnweaver2_controller",
                         "eltwise_layer.v" :"eltwise_layer",
                         "reduction_layer.v" :"reduction_layer",
                         "robot_rl.v":"robot_maze",
                         "softmax.v" :"softmax",
                         "spmv.v" :"spmv",
                         "tpu_like.small.ws.v":"top"
                         }

VTR_benchmarks_top_modules = {"arm_core.v":"arm_core",
                              "bgm.v":"bgm",
                              "blob_merge.v":"RLE_BlobMerging",
                              "boundtop.v":"paj_boundtop_hierarchy_no_mem",
                              "ch_intrinsics.v":"memory_controller",
                              "diffeq1.v":"diffeq_paj_convert",
                              "diffeq2.v":"diffeq_f_systemC",
                              "LU8PEEng.v":"LU8PEEng",
                              "LU32PEEng.v":"LU32PEEng",
                              "LU64PEEng.v":"LU64PEEng" ,
                              "mcml.v":"mcml",
                              "mkDelayWorker32B.v":"mkDelayWorker32B",
                              "mkPktMerge.v":"mkPktMerge",
                              "mkSMAdapter4B.v":"mkSMAdapter4B",
                              "multiclock_output_and_latch.v":"multiclock_output_and_latch",
                              "multiclock_reader_writer.v":"multiclock_reader_writer",
                              "multiclock_separate_and_latch.v":"multiclock_separate_and_latch",
                              "or1200.v":"or1200_flat",
                              "raygentop.v":"paj_raygentop_hierarchy_no_mem",
                              "sha.v":"sha1",
                              "spree.v":"system" ,
                              "stereovision0.v":"sv_chip0_hierarchy_no_mem",
                              "stereovision1.v":"sv_chip1_hierarchy_no_mem",
                              "stereovision2.v":"sv_chip2_hierarchy_no_mem",
                              "stereovision3.v":"sv_chip3_hierarchy_no_mem",
                              "matmul_8x8_fp16.v":"matrix_multiplication",
                              "tpu.16x16.int8.v":"top",
                              "tpu.32x32.int8.v":"top"}

def main():
    percents_to_test = [1.0, 0.66, 0.33]
    # percents_to_test = [1.0]

    place_algs = ["cube_bb", "per_layer_bb"]
    # place_algs = ["cube_bb"]

    connection_types = ["subset", "wilton_2"]
    # connection_types = ["subset"]

    type_sbs = ["2d", "3d_cb", "3d_cb_out_only", "combined"]
    # type_sbs = ["combined"]

    random_seed_array = [random.randint(0, 100000) for _ in range(0, 10)]
    # random_seed_array = [1]

    tasks_start_time = time.time()

    printing.verbose = True

    inner_num_to_test = [0.5]

    width = 25

    height = 25

    width_2d = 35

    height_2d = 35

    channel_width = 100

    vertical_connectivity = 1

    sb_switch_name = ""

    sb_segment_name = ""

    sb_input_pattern = []
    sb_output_pattern = []

    sb_location_pattern = "repeated_interval"

    sb_grid_csv_path=""

    # TO BE ADDED AS A PARAMETER
    vertical_delay_ratio = 1

    original_dir = os.getcwd()

    is_verilog_benchmarks = False # True if using verilog benchmarks (Koios), False if using blif benchmarks (MCNC)
    benchmarks_dir = original_dir + "/benchmarks" + "/MCNC_benchmarks" # "/MCNC_benchmarks" or "/koios" or "/ITD_paper" or "/ITD_subset" or "/ITD_quick" or "/VTR_benchmarks"
    
    # arch_file = "/home/Ismael/3DFADE/arch_files/templates/dsp_bram/vtr_3d_cb_arch_dsp_bram.xml"

    identifier_string = "dsp_bram_random_seeds_run"
    identifier_string = "multi_run_test"
    
    vpr_options = "--inner_num"

    for l in inner_num_to_test:
        for k in range(len(connection_types)):
            for j in range(len(percents_to_test)):
                for place_algorithm in place_algs:
                    

                    for type_sb in type_sbs:

                        run_num = 1

                        for seed in random_seed_array:
                            

                            main_start_time = time.time()

                            cur_loop_identifier = identifier_string + str(l) 
                            cur_loop_vpr_options = vpr_options + " " + str(l)

                            top_module_names = {}

                            if is_verilog_benchmarks and benchmarks_dir == original_dir + "/benchmarks/ITD_paper":
                                top_module_names = ITD_paper_top_modules
                            elif is_verilog_benchmarks and benchmarks_dir == original_dir + "/benchmarks/VTR_benchmarks":
                                top_module_names = VTR_benchmarks_top_modules
                            elif is_verilog_benchmarks and benchmarks_dir == original_dir + "/benchmarks/ITD_subset":
                                top_module_names = ITD_subset_top_modules
                            elif is_verilog_benchmarks and benchmarks_dir == original_dir + "/benchmarks/ITD_quick":
                                top_module_names = ITD_quick_top_modules

                            if is_verilog_benchmarks:
                                blif_files = get_files_with_extension(benchmarks_dir, ".v")
                                verilog_files = get_files_with_extension(benchmarks_dir, ".v")
                                act_files = get_files_with_extension(benchmarks_dir, ".v")

                            else:
                                blif_files = get_files_with_extension(benchmarks_dir, ".blif")
                                verilog_files = get_files_with_extension(benchmarks_dir, ".v")
                                act_files = get_files_with_extension(benchmarks_dir, ".act")

                            percent_connectivity = percents_to_test[j]

                            connection_type = connection_types[k]

                            if (type_sb == "3d_cb" or type_sb == "3d_cb_out_only" or type_sb == "2d") and (percent_connectivity != 1 or connection_types[k] != "subset"):
                                print_verbose(f"2D, 3D CB, and 3D CB Out Only only support 100% connectivity with subset SB connection. Skipping {percent_connectivity}% connectivity and {connection_types[k]} connection type")
                                continue

                            if (type_sb == "2d" and place_algorithm != "cube_bb"):
                                print_verbose(f"2D,doesn't care about placement algorithm cost function. Skipping {place_algorithm} since it's not cube_bb")
                                continue
                            
                            if type_sb == "2d":
                                width = width_2d
                                height = height_2d
                            
                            arch_file = ""
                            if type_sb == "3d_cb":
                                arch_file = "/home/Ismael/3DFADE/arch_files/templates/dsp_bram/vtr_3d_cb_arch_dsp_bram.xml"

                            elif type_sb == "3d_cb_out_only":
                                arch_file = "/home/Ismael/3DFADE/arch_files/templates/dsp_bram/vtr_3d_cb_out_only_arch_dsp_bram.xml"

                            elif type_sb == "2d":
                                arch_file = "/home/Ismael/3DFADE/arch_files/templates/dsp_bram/vtr_2d_arch_dsp_bram.xml"

                            elif type_sb == "combined":
                                arch_file = "/home/Ismael/3DFADE/arch_files/templates/dsp_bram/vtr_arch_dsp_bram.xml"


                            legal_choices = ["combined", "3d_cb", "2d", "3d_cb_out_only"]
                            if type_sb not in legal_choices:    
                                print(f"ERROR: Invalid SB type: {type_sb}. Please choose from {legal_choices}")
                                exit(1)

                            print(f"Running with options: Width: {width}, Height: {height}, Channel Width: {channel_width}, Percent Connectivity: {percent_connectivity}, Place Algorithm: {place_algorithm}, Connection Type: {connection_type}, SB Type: {type_sb} with extra VPR options: {cur_loop_vpr_options} and identifier: {cur_loop_identifier}")

                            with tempfile.TemporaryDirectory() as outer_temp_dir:

                                task_run_folder = setup_flow(
                                                            original_dir=original_dir, 
                                                            width=width, 
                                                            height=height, 
                                                            channel_width=channel_width, 
                                                            type_sb=type_sb, 
                                                            percent_connectivity=percent_connectivity, 
                                                            place_algorithm=place_algorithm, 
                                                            is_verilog_benchmarks=is_verilog_benchmarks, 
                                                            connection_type=connection_type, 
                                                            arch_file=arch_file, 
                                                            random_seed=seed, 
                                                            run_num=run_num, 
                                                            extra_vpr_options=cur_loop_vpr_options, 
                                                            output_additional_info=cur_loop_identifier, 
                                                            temp_dir=outer_temp_dir,
                                                            vertical_connectivity=vertical_connectivity,
                                                            sb_switch_name=sb_switch_name,
                                                            sb_segment_name=sb_segment_name,
                                                            sb_input_pattern=sb_input_pattern,
                                                            sb_output_pattern=sb_output_pattern,
                                                            sb_location_pattern=sb_location_pattern,
                                                            sb_grid_csv_path=sb_grid_csv_path
                                                            )  

                                # Parallelized
                                with ThreadPoolExecutor() as executor:
                                    futures = []
                                    for i in range(len(blif_files)):
                                        futures.append(
                                            executor.submit(
                                                run_one_benchmark,
                                                i,                                                            # benchmark index
                                                blif_file=blif_files[i],                                      # blif file path
                                                verilog_file=verilog_files[i],                                # verilog file path
                                                act_file=act_files[i],                                        # activity file path
                                                original_dir=original_dir,                                    # original directory
                                                width=width,                                              # width parameter
                                                height=height,                                            # height parameter
                                                channel_width=channel_width,                                  # channel width
                                                type_sb=type_sb,                                              # switch block type
                                                percent_connectivity=percent_connectivity,                    # connectivity percentage
                                                place_algorithm=place_algorithm,                              # placement algorithm
                                                verilog_benchmarks=is_verilog_benchmarks,                        # using verilog benchmarks?
                                                connection_type=connection_type,                              # connection type
                                                benchmark_top_name=top_module_names.get(os.path.basename(verilog_files[i]), ""),  # top module name
                                                output_folder_name=task_run_folder,                           # output folder
                                                run_number=run_num,                                           # run number
                                                output_additional_info=cur_loop_identifier,                   # additional info
                                                temp_template_dir=outer_temp_dir                              # template directory
                                            )
                                        )

                                    for future in futures:
                                        future.result()

                            # Serialized
                            # for i in range(len(blif_files)):
                            #     run_one_benchmark(i, blif_files[i], verilog_files[i], act_files[i], original_dir, new_width, height, channel_width, type_sb, percent_connectivity, place_algorithm, verilog_benchmarks, connection_type)
                            
                            main_end_time = time.time()

                            main_runtime = (main_end_time - main_start_time) * 1000

                            print(f"\nRunning all tasks took: {main_runtime:.2f} ms\n")

                            run_num += 1

    print("All tasks completed.")
    tasks_end_time = time.time()
    tasks_runtime = (tasks_end_time - tasks_start_time) * 1000
    print(f"Total runtime: {tasks_runtime:.2f} ms")
    
if __name__ == "__main__":
    main()
