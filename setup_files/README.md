# Structure of YAML Config File for LaZagna

## How It Works
LaZagna accepts multiple options to run. There are default values for each item in the file `default_options.yaml`. If a particular field is not specified, then the value is pulled from this file.

## Input Parameters:

- **width**: `integer`
  - Description: Width of desired 3D FPGA fabric

- **height**: `integer`
  - Description: Height of desired 3D FPGA fabric

- **width_2d**: `integer`
  - Description: Width of 2D FPGA fabric if `2d` is specified as one of the SB types. This is used to allow the user to specify the size of the 2D Fabric to compare against the 3D fabric. Since a 50x50 2 layer FPGA has twice as many grid locations as the 50x50 1 layer FPGA, so the user can set this parameter to make the 2 fabrics the same equivalent size.

- **height_2d**: `integer`
  - Description: Height of 2D FPGA fabric if `2d` is specified as one of the SB types. This is used to allow the user to specify the size of the 2D Fabric to compare against the 3D fabric. Since a 50x50 2 layer FPGA has twice as many grid locations as the 50x50 1 layer FPGA, so the user can set this parameter to make the 2 fabrics the same equivalent size.

- **channel_width**: `integer`
  - Description: Channel width to use for FPGA fabric. This only applies to the 2D channel width. The vertical channel width is currently modified by adjsuting the number of 3D SBs, and number of interlayer grid pins. (3D vertical channel width option to be added soon!)

- **percent_connectivity**: `list of integers`
  - Description: Percentage of the SBs on the FPGA that are 3D.

- **place_algorithm**: `list of strings`
  - Description: Bounding Box computation method for 3D FPGA when using VTR. Options are: "cube_bb" and "per_layer_bb", see VTR documentation to understand the difference. 

- **connection_type**: `list of strings`
  - Description: Pattern to use for 3D SBs. Available options: `subset`, `custom`. If `custom` is chosen then `sb_3d_pattern` needs to be set. 

- **linked_params**: `object`
  - Structure containing **type_sb_arch_mapping** parameter: Liking each vertical connection type to it's VTR architecture XML file.
    - **type_sb**: `string`
      - Description: Vertical Connection type to use. Options are: `2d`, `3d_cb`, `3d_cb_out_only`, `3d_cb_in_only`, `hybrid_cb`, `hybrid_cb_out`, `hybrid_cb_in`, `3d_sb`. New options can be added by modifying the code. 
    - **arch_file**: `string`
      - Description: Path to VTR architecture XML that links to the type_sb specified

- **num_seeds**: `integer`
  - Description: Number of random seeds to test. Only used when `random_seed` is `True`

- **random_seed**: `boolean`
  - Description: Boolean to describe whether to use a random seed for placement or not.

- **non_random_seed**: `integer`
  - Description: Seed to use for placement if `random_seed` is `False`.

- **additional_vpr_options**: `string`
  - Description: Additional options to run with VPR. See [VPR Command Line Options Documentation](https://docs.verilogtorouting.org/en/latest/vpr/command_line_usage/) for more details on options available.

- **cur_loop_identifier**: `string`
  - Description: [description here]

- **is_verilog_benchmarks**: `boolean`
  - Description: Boolean indicator to tell if the benchmarks being run are verilog or BLIF format. If verilog yosys is invoked to synthesize the benchmarks otherwise, this step is skipped. Note: if the user desires to generate the testbench for the fabric then the verilog of the benchmarks is also required to generate the correct testbench.

- **benchmarks_dir**: `string`
  - Description: Directory containing the benchmarks to be run. See `benchmarks` directory to understand setup of this directory.

- **vertical_connectivity**: `integer`
  - Description: **To Be Implemented** Option to decide number of channels that connect vertically.

- **sb_switch_name**: `string`
  - Description: Base switch name in vtr architecture xml file to use for vertical delay calculation. The switch's delay is used as the base delay value and then multiplied by the `vertical_delay_ratio` if specified.

- **sb_segment_name**: `string`
  - Description: Segment in vtr architecture xml file to use for 3D SB interlayer connections.

- **sb_input_pattern**: `list`
  - Description: Pattern to use for 3D SB inputs.

- **sb_output_pattern**: `list`
  - Description: Patternt to use for 3D SB outputs.

- **sb_location_pattern**: `list[str]`
  - Specifies the pattern for SB locations. Available pattern options are:
    - `core`
    - `perimeter`
    - `rows`
    - `columns`
    - `repeated_interval`
    - `custom`
  
  Note: When selecting `custom`, you must also provide the `sb_grid_csv_path` parameter.

- **sb_grid_csv_path**: `str`
  - Path to a CSV file defining custom SB location patterns
  - The CSV should contain a grid of 'X' and 'O' characters where:
    - 'X' represents a 3D SB location
    - 'O' represents a 2D SB location
  - Example patterns for 100x100 grids can be found in the `csv_patterns` directory

- **vertical_delay**: `list of floats`
  - Description: List of all vertical delays to test. This is the exact delay to be used for vertical connections. Note: Provide the delay in scientific notation. For example: 1ns would be 1e-9

- **vertical_delay_ratio**: `list of floats`
  - Description: List of all the vertical delay ratios desired to be tested. 

- **base_delay_switch**: `string`
  - Description: Switch name in VTR architecture XML file to use when calculating the vertical delay based on a ratio.

- **switch_interlayer_pairs**: `object`
  - Maps each 2D switch in the VTR Architecture XML to it's 3D equivalent. This is used for calculating new vertical delay ratios to use.
    

- **update_arch_delay**: `boolean`
  - Description: Whether the vertical delays in the VTR architecture file should be modified or not. 