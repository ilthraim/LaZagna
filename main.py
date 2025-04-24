# Main scripting file to run 3DFADE
"""
# Options to give 3DFADE:

    1. VTR Architecture File
        If not provided defaults to templates files under "arch_files/templates"

    2. Benchmark Directory
        If not provided defaults to "benchmarks/MCNC_benchmarks"

    3. Benchmark Type
        2 Options: Verilog or BLIF
        If not provided defaults to BLIF

    4. 3D Fabric Width and Height
        If not provided defaults to 4x4

    5. 3D Fabric Layer Count (Hopefully)
        If not provided defaults to 2

    6. 2D Fabric Width and Height
        If not provided defaults to 4x4

    7. Routing Channel Width
        If not provided defaults to 10

    8. 3D Vertical Connection Type
        How the layers are connected together.
        Valid Options:
            * `2d`
                No 3D connections only 1 layer
            * `3d_cb`
                Inputs and Outputs of Grid locations are interlayer
            * `3d_cb_out_only`
                Only outputs of Grid locations are interlayer
            * `3d_sb`
                The Switch Boxes are interlayer
            * `3d_hybrid`
                Both Switch Boxes and Inputs and Outputs are interlayer (combination of `3d_cb` and `3d_sb`)
            * `3d_hybrid_out_only` 
                Both Switch Boxes and Outputs are interlayer (combination of `3d_cb_out_only` and `3d_sb`)
        If not provided defaults to `3d_cb`

    9. 3D Switch Block Connection Pattern
        The connection pattern of the switch blocks in the 3D fabric. Only valid for `3d_sb`, `3d_hybrid`, and `3d_hybrid_out_only` options.
        Valid Options:
            * `subset`
                subset/disjoint pattern
            * `wilton`
                wilton pattern with the following pattern structure (See README for more details): 0123,0123
            * `wilton_2`
                wilton pattern with the following pattern structure (See README for more details): 0000,0123
            * `wilton_3`
                wilton pattern with the following pattern structure (See README for more details): 0000,1111
            * `custom`
                Custom pattern defined using the `--sb_pattern_structure` option (required if `custom` is selected)
        If not provided defaults to `subset`

    10. 3D Switch Block Connection Pattern Structure
        The structure of the switch block connection pattern. Only valid for `3d_sb`, `3d_hybrid`, and `3d_hybrid_out_only` options with `custom` pattern.

    11. 3D Switch Block Vertical Channel Width
        The Vertical Channel Width of the 3D Switch Block. Only valid for `3d_sb`, `3d_hybrid`, and `3d_hybrid_out_only` options.
        This is a float that represents the size of the vertical channel as a percentage of the total channel width.
        If not provided defaults to 1.0

    12. Percentage of 3D Switch Blocks on Grid
        The percentage of Switch Blocks on the grid that are 3D. Only valid for `3d_sb`, `3d_hybrid`, and `3d_hybrid_out_only` options.
        Represented as a float between 0 and 1.
        If not provided defaults to 1.0

    13. 3D Switch Block Placement Strategy
        Where the 3D Switch Blocks are placed on the grid. Only valid for `3d_sb`, `3d_hybrid`, and `3d_hybrid_out_only` options.
        Valid Options:
            * `random`
                Random placement
            * `repeated_interval`
                Repeated interval placement. Location Determined by calculating total number of 3D SBs needed and then evenly distributing them across the grid where the grid is represented in a linearized fashion.
            * `edge`
                Edge placement is prioritized. 3D SBs are placed on the edge of the grid first. Once edge is full the center is filled in a repeated interval fashion.
            * `center`
                Center placement is prioritized. 3D SBs are placed in the center of the grid first. Once center is full the edge is filled in a repeated interval fashion.
        If not provided defaults to `repeated_interval`

    14. VTR Placement Cost Calculation Method:
        The method used to calculate the placement cost in VTR (--place_bounding_box_mode option).
        Valid Options:
            * `cube`
                Equivalent to the `cube_bb` option in VTR
            * `per_layer`
                Equivalent to the `per_layer_bb` option in VTR
        If not provided defaults to `cube`

    15. VTR Placement Random Seed
        The random seed used for VTR placement.
        If not provided defaults to 1

    16. Output File & Directory Name:
        The name of the output file and directory.
        If not provided defaults to the configuration and the benchmark name.

    18. Copy Run Directory 
        Boolean Option. If true, will copy the run directory to the output directory.
        If not provided defaults to False

    19. Copy Route Results
        Boolean Option. If true, will copy the route results (.route file) to the output directory.
        If not provided defaults to False, if Copy Run Directory is True this will be True as well.

    20. Copy Place Results
        Boolean Option. If true, will copy the place results (.place file) to the output directory.
        If not provided defaults to False, if Copy Run Directory is True this will be True as well.

    21. Addtional VPR Options
        Additional options to pass to VPR.
        If not provided defaults to None

    22. Verbose Mode
        If provided, will output more information about the process.
"""

from run_single_test import run_interface, ITD_paper_top_modules, ITD_subset_top_modules, ITD_quick_top_modules, VTR_benchmarks_top_modules
from file_handling import get_files_with_extension
from yaml_file_processing import get_run_params_from_yaml
import os
from concurrent.futures import ProcessPoolExecutor
import psutil
import printing
import time
import argparse

eltwise_top_modules = {"eltwise_layer.v" :"eltwise_layer"}

parser = argparse.ArgumentParser(description="Run 3DFADE tests in parallel using configurations in a yaml file.")

parser.add_argument("-f", "--yaml_file", type=str, required=True, help="Path to the yaml file containing the test parameters.")
parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output.")
parser.add_argument("-j", "--num_workers", type=int, default=4, help="Number of parallel workers to use. Default is 4.")
# the directory of this file
original_dir = os.path.dirname(os.path.abspath(__file__))

def run_job(param):
    # Lower the priority of the current process
    process = psutil.Process(os.getpid())
    process.nice(11)
    
    param_copy = param.copy()
    param_copy['original_dir'] = original_dir
    return run_interface(params=param_copy)

def setup_benchmark_files(run_params):
    for param in run_params:
        is_verilog_benchmarks = param.get("is_verilog_benchmarks", False)
        benchmarks_dir = param.get("benchmarks_dir", original_dir + "/benchmarks/MCNC_benchmarks")

        if is_verilog_benchmarks and benchmarks_dir == original_dir + "/benchmarks/ITD_paper":
            top_module_names = ITD_paper_top_modules
        elif is_verilog_benchmarks and benchmarks_dir == original_dir + "/benchmarks/VTR_benchmarks":
            top_module_names = VTR_benchmarks_top_modules
        elif is_verilog_benchmarks and benchmarks_dir == original_dir + "/benchmarks/ITD_subset":
            top_module_names = ITD_subset_top_modules
        elif is_verilog_benchmarks and benchmarks_dir == original_dir + "/benchmarks/ITD_quick":
            top_module_names = ITD_quick_top_modules
        elif is_verilog_benchmarks and benchmarks_dir == original_dir + "/benchmarks/eltwise":
            top_module_names = eltwise_top_modules
        else:
            top_module_names = {}

        if is_verilog_benchmarks:
            blif_files = get_files_with_extension(benchmarks_dir, ".v")
            verilog_files = get_files_with_extension(benchmarks_dir, ".v")
            act_files = get_files_with_extension(benchmarks_dir, ".v")

        else:
            blif_files = get_files_with_extension(benchmarks_dir, ".blif")
            verilog_files = get_files_with_extension(benchmarks_dir, ".v")
            act_files = get_files_with_extension(benchmarks_dir, ".act")

        param['blif_files'] = blif_files
        param['verilog_files'] = verilog_files
        param['act_files'] = act_files
        param['top_module_names'] = top_module_names

    return run_params


def main():

    start_time = time.time()

    args = parser.parse_args()
    yaml_file = args.yaml_file
    verbose = args.verbose

    # only enable false for debugging, it prints too much, give out every formation tested.
    run_params = get_run_params_from_yaml(yaml_file, verbose=False)

    run_params = setup_benchmark_files(run_params)

    printing.verbose = verbose

    # Determine the number of CPUs to use (leave one free for system responsiveness)
    # num_workers = max(1, psutil.cpu_count(logical=True) - 1)
    num_workers = args.num_workers

    print(f"Running {len(run_params)} jobs in parallel using {num_workers} workers")
        
    
    # Run jobs in parallel using ProcessPoolExecutor
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        results = list(executor.map(run_job, run_params))

    end_time = time.time()

    elapsed_time = (end_time - start_time) * 1000
    print(f"time to run tests: {elapsed_time:.2f} ms")

if __name__ == "__main__":
    main()
