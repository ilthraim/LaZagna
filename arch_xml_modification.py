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

def update_vertical_delay_ratio(root, new_ratio, sb_3d_switch_name="3D_SB_switch", base_delay_switch="", cb_switches_names = []):
    """Update the vertical_delay_ratio in the architecture XML file.
    Args:
        root (ElementTree): The root element of the XML tree.
        new_ratio (float): The new vertical delay ratio to set.
        sb_3d_switch_name (str): The name of the 3D SB switch.
        base_delay_switch (str): The base delay switch name to base 3D delay adjustment on.
        cb_switches_names (list[str]): List of CB switch names to also have their delays modified.
    """
    
    # Find the switches section
    switches = root.find('.//switchlist')
    if switches is None:
        print("Error: No switchlist element found.")
        exit(1)

    # Find the 3D switch
    sb_switch = switches.find(f".//switch[name='{sb_3d_switch_name}']")
    if sb_switch is None:
        print(f"Error: Switch '{sb_3d_switch_name}' not found.")
        exit(1)

    base_switch = switches.find(f".//switch[name='{base_delay_switch}']")
    if base_switch is None:
        print(f"Error: Base switch '{base_delay_switch}' not found.")
        exit(1)

    base_delay = float(base_switch.get('Tdel'))

    new_delay = base_delay * new_ratio
    sb_switch.set('Tdel', str(new_delay))

    for cb_switch_name in cb_switches_names:
        cb_switch = switches.find(f".//switch[name='{cb_switch_name}']")
        if cb_switch is None:
            print(f"Error: CB switch '{cb_switch_name}' not found.")
            exit(1)
        cb_delay = float(cb_switch.get('Tdel'))
        new_cb_delay = cb_delay * new_ratio
        cb_switch.set('Tdel', str(new_cb_delay))