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
  - Description: [description here]

- **linked_params**: `object`
  - Structure containing **type_sb_arch_mapping** parameter:
    - **type_sb**: `string`
      - Description: [description here]
    - **arch_file**: `string`
      - Description: [description here]

- **num_seeds**: `integer`
  - Description: [description here]

- **random_seed**: `boolean`
  - Description: [description here]

- **non_random_seed**: `integer`
  - Description: [description here]

- **additional_vpr_options**: `string`
  - Description: [description here]

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
  - Description: [description here]

- **sb_output_pattern**: `list`
  - Description: [description here]

- **sb_location_pattern**: `list of strings`
  - Description: [description here]

- **sb_grid_csv_path**: `string`
  - Description: [description here]

- **vertical_delay_ratio**: `list of floats`
  - Description: [description here]

- **base_delay_switch**: `string`
  - Description: [description here]

- **switch_interlayer_pairs**: `object`
  - Map with keys and values
    - **L4_driver**: `string`
      - Description: [description here]
    - **L16_driver**: `string`
      - Description: [description here]
    - **ipin_cblock**: `string`
      - Description: [description here]

- **update_arch_delay**: `boolean`
  - Description: Whether the vertical delays in the VTR architecture file should be modified or not. 