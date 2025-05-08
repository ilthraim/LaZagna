# <img src="./images/LaZagna_logo_1_no_bg.png" alt="Logo" width="100" style="vertical-align:middle; margin-right:8px;"> LaZagna: 3D FPGA Architecture Exploration Tool 

> ⚠️ **Note**: Repository organization and documentation are currently under development. :construction_worker: :construction:

LaZagna is an open-source framework for the automated design and exploration of 3D FPGA architectures. It provides an end-to-end flow that includes high-level architectural specification, synthesizable RTL generation, and bitstream production. LaZagna supports a broad and customizable 3D design space, including flexible vertical interconnect strategies, 3D switch block patterns and placement, and heterogeneous configurations. By enabling both architectural modeling and functional validation, LaZagna serves as a versatile tool for advancing research and development in 3D FPGA design.

## Table of Contents

- [Building](#building)
- [Usage](#usage)
- [Directory Structure](#directory-structure)
- [License](#license)

## Building

Build the project using make:
```bash
make all
```

For faster build times, use parallel processing with the -j flag:

```bash
make all -j4  # Uses 4 cores
```
# Usage
## Running LaZagna
Execute the tool using:

```bash
python3 lazagna/main.py -f <path_to_setup_file>
```

Optional flag:
    `-v`: Enable verbose output

## Setup Files
Configuration is done through setup files. See the `setup_files` directory for:

1. Setup file format
2. Available options
3. Example configurations

## Output Structure

LaZagna generates two types of output:

1. `tasks_run/`: Contains detailed results and analysis
2. `results/`: CSV files with placement and routing results for each benchmark

## Cleaning Up
Clean specific outputs:

```bash

# Remove output files
make clean_files

# Clean OpenFPGA build
make clean_openfpga

# Clean everything
make clean
```

## Directory Structure
To Do

## License
This project is licensed under the MIT License

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Copyright (c) 2025 Ismael Youssef

See the [LICENSE](./LICENSE) file for full license details.