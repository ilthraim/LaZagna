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

def append_random_seed_to_script(script_path, random_seed):
    with open(script_path, 'r') as file:
        lines = file.readlines()

    with open(script_path, 'w') as file:
        for line in lines:
            if line.startswith("vpr"):
                # Append the string to the line
                line = line.rstrip('\n') + " " + "--seed " + str(random_seed) + "\n"
            file.write(line)

def append_extra_vpr_option_to_script(script_path, string_to_add):
    with open(script_path, 'r') as file:
        lines = file.readlines()

    with open(script_path, 'w') as file:
        for line in lines:
            if line.startswith("vpr"):
                # Append the string to the line
                line = line.rstrip('\n') + " "  + str(string_to_add) + "\n"
            file.write(line)

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
                line = line.rstrip('\n') + " --route_chan_width " + string_to_add + "\n"
            file.write(line)

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

def update_config_verilog(config_path, benchmark_verilog, benchmark_top_name):
    
    with open(config_path, 'r') as file:
        lines = file.readlines()

    updated_lines = []
    for line in lines:
        # Replace lines with the matching keys
        if line.strip().startswith("bench0="):
            updated_lines.append(f"bench0={benchmark_verilog}\n")
        elif line.strip().startswith("bench0_top="):
            updated_lines.append(f"bench0_top={benchmark_top_name}\n")
        else:
            updated_lines.append(line)

    # Write the updated lines back to the file
    with open(config_path, 'w') as file:
        file.writelines(updated_lines)
