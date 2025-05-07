# Benchmark Setup Guide

This guide explains how to set up new benchmarks for testing with LaZagna. There are two types of benchmarks supported:
1. Verilog Benchmarks
2. BLIF Benchmarks

## Verilog Benchmarks Setup

### Steps:
1. Create a new folder for your benchmarks
2. Add all Verilog files (`.v`) to the folder
3. Specify the top module names in `lazagna/run_interface.py`
   #### Example dictionary format:
   ``` python
   benchmark_tops = {
       'benchmark1.v': 'top_module_name1',
       'benchmark2.v': 'top_module_name2'
   }
   ```
4. Update the `setup_benchmark_files` function in `lazagna/main.py` with your new dictionary

### Note:
- Top module specification is mandatory for synthesis script execution
- See existing examples in `lazagna/run_interface.py` for reference

## BLIF Benchmarks Setup

### Directory Structure:
```
benchmarks/
├── benchmark1/
│   ├── benchmark1.blif
│   └── benchmark1.v    # Optional: Required only for testbench generation
├── benchmark2/
│   ├── benchmark2.blif
│   └── benchmark2.v    # Optional: Required only for testbench generation
```
### Requirements:
- Create a main benchmark folder
- For each benchmark:
  - Create a subdirectory named exactly as the BLIF benchmark
  - Place the `.blif` file inside the subdirectory
  - Include the corresponding `.v` file if testbench generation is needed

### Important:
- Subdirectory names must match the BLIF benchmark names
- Verilog files are optional but required for testbench generation
