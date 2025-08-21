from lxml import etree
from printing import print_verbose

def set_fixed_layout_dimensions(root, width, height):
    """Set the width and height attributes of the fixed_layout element."""
    fixed_layout = root.find('.//fixed_layout') # recursively go through xml looking for fixed_layout node
    if fixed_layout is not None:
        fixed_layout.set('width', str(width))
        fixed_layout.set('height', str(height))
    else:
        print_verbose("No fixed_layout element found.")

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
        print_verbose(f"Layer with die='{source_die}' not found.")
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
        print_verbose("No fixed_layout element found.")
        return False

def add_new_layer(root, base_die=None):
    """Add a new layer by copying an existing layer and incrementing the die number."""
    if base_die is None:
        # Use the first layer if base_die is not specified
        layers = root.findall('.//layer')
        if not layers:
            print_verbose("No layers available to copy.")
            return
        base_die = layers[0].get('die')
    
    max_die = get_max_die_number(root)
    new_die = max_die + 1
    success = copy_layer_with_incremented_die(root, source_die=base_die, new_die=new_die)
    if success:
        print_verbose(f"New layer added with die='{new_die}'.")
    else:
        print_verbose("Failed to add new layer.")

def update_vertical_delay_ratio(root, vertical_delay_ratio, sb_3d_switch_name="3D_SB_switch", base_delay_switch="", switch_interlayer_pairs = {}):
    """Update the vertical_delay_ratio in the architecture XML file.
    Args:
        root (ElementTree): The root element of the XML tree.
        vertical_delay_ratio (float): The new vertical delay ratio to set.
        sb_3d_switch_name (str): The name of the 3D SB switch.
        base_delay_switch (str): The base delay switch name to base 3D delay adjustment on.
        switch_interlayer_pairs (Dict[str, str]): Dictionary of horizontal 2D switches and tthe 3D switch name corresponding to it to have their delay modified.
                                                    Key is the 2D switch name and value is the 3D switch name. 2D switch name is needed since the 3D switch delay = 2D switch delay + (vertical_delay_ratio * base_delay_switch delay).
    """
    
    # Find the switches section
    switches = root.find('.//switchlist')
    if switches is None:
        print("Error: No switchlist element found.")
        exit(1)

    # Find the 3D switch
    # Print all switch names
    print_verbose("All switches in the switchlist:")
    for switch in switches.findall(".//switch"):
        print_verbose(f"- {switch.get('name')}")
    
    # Find the 3D switch
    sb_switch = switches.find(f".//switch[@name='{sb_3d_switch_name}']")

    if sb_switch is None:
        print(f"Error: Switch '{sb_3d_switch_name}' not found.")
        exit(1)

    if base_delay_switch == "":
        # Get the first switch in the switchlist as the base delay switch
        base_delay_switch = switches.find('.//switch').get('name')
        print_verbose(f"Base delay switch not specified. Using first switch '{base_delay_switch}' as base delay switch.")

    base_switch = switches.find(f".//switch[@name='{base_delay_switch}']")
    if base_switch is None:

        print(f"Error: Base switch '{base_delay_switch}' not found.")
        exit(1)

    base_delay = float(base_switch.get('Tdel'))

    interlayer_delay = base_delay * vertical_delay_ratio

    # The delay of the 3D SB switch is 1/3 of the desired delay since there are 3 switches in series to drive interlayer connections. Since interlayer SB connections are like the following:
    
    #                 Horizontal Routing Channel on layer X -> None node at layer X -> None node at layer X+1 -> Vertical Routing Channel on layer X+1

    # Notice the 3 switches in series, the first one is the horizontal routing channel on layer X, the second one is the None node at layer X, and the third one is the None node at layer X+1.
    new_delay = interlayer_delay / 2

    sb_switch.set('Tdel', str(new_delay))

    print_verbose(f"Updated delay for 3D SB switch '{sb_3d_switch_name}' to be {new_delay} based on base delay of {base_delay} and vertical delay ratio of {vertical_delay_ratio}.")

    # Update the delay for the interlayer pairs
    for key, value in switch_interlayer_pairs.items():
        # Find the 2D switch
        switch_2d = switches.find(f".//switch[@name='{key}']")

        if switch_2d is None:
            print(f"Error: Switch '{key}' not found.")
            exit(1)

        # Find the 3D switch
        switch_3d = switches.find(f".//switch[@name='{value}']")

        if switch_3d is None:
            print(f"Error: Switch '{value}' not found.")
            exit(1)

        # Update the delay for the 3D switch based on the 2D switch delay and vertical delay ratio
        delay_2d = float(switch_2d.get('Tdel'))
        new_delay = delay_2d + interlayer_delay
        switch_3d.set('Tdel', str(new_delay))

        print_verbose(f"Updated delay for 3D switch '{value}' to be {new_delay} based on 2D switch '{key}' delay of {delay_2d} and interlayer delay of {interlayer_delay}.")