import tempfile
import os
import time
from concurrent.futures import ThreadPoolExecutor
import random
from script_editing import update_config_simple, update_config_verilog
from run_flow import *

def run_one_benchmark(i, blif_file="", verilog_file="", act_file="", original_dir="", width="", height="", channel_width="", type_sb="full", percent_connectivity=0.5, place_algorithm="cube_bb", verilog_benchmarks=False, connection_type="subset", benchmark_top_name="", output_folder_name="", run_number=1):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_task_dir = os.path.join(temp_dir, "task")
        # copy config
        os.makedirs(temp_task_dir, exist_ok=True)

        command = ["cp", "-r", original_dir + "/task/config", temp_task_dir + "/config"]
        run_command_in_temp_dir(command, original_dir)

        os.makedirs(temp_task_dir + "/designs", exist_ok=True)

        # copy script and designs
        command = ["cp", original_dir + "/task/designs/bitstream_script.openfpga", original_dir + "/task/designs/vtr_arch.xml", original_dir + "/task/designs/openfpga_arch.xml", original_dir + "/task/designs/auto_sim_openfpga.xml", temp_task_dir + "/designs/"]
        run_command_in_temp_dir(command, original_dir)

        # design_variables file
        command = ["cp", original_dir + "/task/design_variables.yml", temp_task_dir]
        run_command_in_temp_dir(command, original_dir)

        if verilog_benchmarks:
            update_config_verilog(temp_task_dir + "/config/task.conf", verilog_file, benchmark_top_name)
        else:
            update_config_simple(temp_task_dir + "/config/task.conf", blif_file, extract_file_name(blif_file), act_file, verilog_file)

        print(f"Running Benchmark: {i} {extract_file_name(verilog_file)} with Width: {width}, Height: {height}, Channel Width: {channel_width}")

        start_time = time.time()
        run_flow(original_dir=original_dir, width=width, height=height, channel_width=channel_width, benchmark_name=extract_file_name(verilog_file), temp_dir=temp_task_dir, type_sb=type_sb, percent_connectivity=percent_connectivity, place_algorithm=place_algorithm, connection_type=connection_type, run_num=run_number)
        end_time = time.time()

        elapsed_time_ms = (end_time - start_time) * 1000
        print(f"\tBenchmark {extract_file_name(verilog_file)} took {elapsed_time_ms:.2f} ms")

        # # Make sure tasks_run folder exists
        # os.makedirs(original_dir + "/tasks_run", exist_ok=True)

        # # copy task folder for reference
        # command = ["cp", "-r", temp_task_dir, output_folder_name + "/task_" + extract_file_name(verilog_file)]
        # run_command_in_temp_dir(command, original_dir)

ITD_paper_top_modules = {"attention_layer.v":"attention_layer",
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
                         "softmax.v" :"SoftMax",
                         "spmv.v" :"spmv",
                         "tdarknet_like.large.v" :"td_fused_top",
                         "tpu_like.large.os.v" :"top",
                         "tpu_like.large.ws.v" :"top",
                         "tpu_like.small.ws.v":"top"}

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
    percents_to_test = [1, 0.66, 0.33]
    place_algs = ["cube_bb", "per_layer_bb"]
    connection_types = ["wilton", "wilton_2"]
    # type_sbs = ["2d", "3d_cb",  "3d_cb_out_only", "combined"]
    type_sbs = ["combined"]
    random_seed_array = [random.randint(0, 100000) for _ in range(0, 400)]

    tasks_start_time = time.time()

    for type_sb in type_sbs:
        for k in range(len(connection_types)):
            for j in range(len(percents_to_test)):
                for i in range(len(place_algs)):
                    run_num = 101

                    if connection_types[k] == "wilton" and ((place_algs[i] == "cube_bb" and percents_to_test[j] == 0.66) or percents_to_test[j] == 1):
                        continue

                    if connection_types[k] == "wilton" and percents_to_test[j] == 0.66:
                        run_num = 200

                    
                    
                    for l in random_seed_array:
                        if run_num == 501:
                            continue

                        main_start_time = time.time()

                        original_dir = os.getcwd()

                        verilog_benchmarks = False # True if using verilog benchmarks (Koios), False if using blif benchmarks (MCNC)
                        benchmarks_dir = original_dir + "/benchmarks" + "/MCNC_benchmarks" # "/MCNC_benchmarks" or "/koios" or "/ITD_paper" or "/VTR_benchmarks" (need to retrieve)

                        top_module_names = {}
                        if verilog_benchmarks and benchmarks_dir == original_dir + "/benchmarks/ITD_paper":
                            top_module_names = ITD_paper_top_modules
                        elif verilog_benchmarks and benchmarks_dir == original_dir + "/benchmarks/VTR_benchmarks":
                            top_module_names = VTR_benchmarks_top_modules


                        if verilog_benchmarks:
                            blif_files = get_files_with_extension(benchmarks_dir, ".v")
                            verilog_files = get_files_with_extension(benchmarks_dir, ".v")
                            act_files = get_files_with_extension(benchmarks_dir, ".v")
                        else:
                            blif_files = get_files_with_extension(benchmarks_dir, ".blif")
                            verilog_files = get_files_with_extension(benchmarks_dir, ".v")
                            act_files = get_files_with_extension(benchmarks_dir, ".act")



                        new_width = 25     # Set your desired width
                        new_height = 25   # Set your desired height

                        channel_width = 150
                        # type_sb = "combined" # "full" or "combined" or "3d_cb" or "2d" or "3d_cb_out_only"
                        percent_connectivity = percents_to_test[j]
                        place_algorithm = place_algs[i] # "cube_bb" or "per_layer_bb"

                        if (type_sb == "3d_cb" or type_sb == "3d_cb_out_only" or type_sb == "2d") and percent_connectivity != 1:
                            print(f"3D CB and 3D CB Out Only only support 100% connectivity. Skipping {percent_connectivity}% connectivity")
                            continue

                        connection_type = connection_types[k] # "subset" or "wilton" or "wilton_2"

                        if (type_sb == "3d_cb" or type_sb == "3d_cb_out_only" or type_sb == "2d") and connection_type != "subset":
                            print(f"3D CB and 3D CB Out don't care about connection type. Skipping {connection_type} connection type since it's not subset")
                            continue

                        
                        # connection_type = "subset"

                        if type_sb == "2d":
                            new_width=35
                            new_height=35

                        # arch_file = original_dir + "/arch_files/koios_3d/3d_template_inter_die_k6FracN10LB_mem20k_complexDSP_customSB_7nm.xml"

                        arch_file = ""

                        legal_choices = ["full", "combined", "3d_cb", "2d", "3d_cb_out_only"]
                        if type_sb not in legal_choices:    
                            print(f"Invalid SB type: {type_sb}. Please choose from {legal_choices}")
                            return

                        task_run_folder = setup_flow(original_dir, new_width, new_height, channel_width, type_sb, percent_connectivity=percent_connectivity, place_algorithm=place_algorithm, verilog_benchmarks=verilog_benchmarks, connection_type=connection_type, arch_file=arch_file, random_seed=l, run_num=run_num)

                        # Parallelized
                        with ThreadPoolExecutor() as executor:
                            futures = [
                                executor.submit(run_one_benchmark, i, blif_files[i], verilog_files[i], act_files[i], original_dir, new_width, new_height, channel_width, type_sb, percent_connectivity, place_algorithm, verilog_benchmarks, connection_type, 
                                                top_module_names[os.path.basename(verilog_files[i])] if verilog_benchmarks else [], task_run_folder, run_num)
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

                        run_num += 1

    print("All tasks completed.")
    tasks_end_time = time.time()
    tasks_runtime = (tasks_end_time - tasks_start_time) * 1000
    print(f"Total runtime: {tasks_runtime:.2f} ms")
    
if __name__ == "__main__":
    main()
