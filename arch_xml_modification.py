from lxml import etree

def set_fixed_layout_dimensions(root, width, height):
    """Set the width and height attributes of the fixed_layout element."""
    fixed_layout = root.find('.//fixed_layout') # recursively go through xml looking for fixed_layout node
    if fixed_layout is not None:
        fixed_layout.set('width', str(width))
        fixed_layout.set('height', str(height))
    else:
        print("No fixed_layout element found.")

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
        print(f"Layer with die='{source_die}' not found.")
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
        print("No fixed_layout element found.")
        return False

def add_new_layer(root, base_die=None):
    """Add a new layer by copying an existing layer and incrementing the die number."""
    if base_die is None:
        # Use the first layer if base_die is not specified
        layers = root.findall('.//layer')
        if not layers:
            print("No layers available to copy.")
            return
        base_die = layers[0].get('die')
    
    max_die = get_max_die_number(root)
    new_die = max_die + 1
    success = copy_layer_with_incremented_die(root, source_die=base_die, new_die=new_die)
    if success:
        print(f"New layer added with die='{new_die}'.")
    else:
        print("Failed to add new layer.")
