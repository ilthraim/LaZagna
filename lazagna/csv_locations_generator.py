import numpy as np
import csv
from PIL import Image
import os

def create_empty_grid(size=99):
    return np.full((size, size), 'o', dtype=str)

def save_grid_to_csv(grid, filename):
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(grid)

def generate_core_pattern(size=99):
    grid = create_empty_grid(size)
    center = size // 2
    square_size = 1
    total_cells = size * size
    filled_cells = 0
    target_cells = total_cells // 2
    
    while filled_cells < target_cells:
        start = center - square_size // 2
        end = center + square_size // 2 + 1
        for i in range(start, end):
            for j in range(start, end):
                if i >= 0 and i < size and j >= 0 and j < size and grid[i][j] == 'o':
                    grid[i][j] = 'x'
                    filled_cells += 1
                    if filled_cells >= target_cells:
                        return grid
        square_size += 2

def generate_perimeter_pattern(size=99):
    grid = create_empty_grid(size)
    layer = 0
    total_cells = size * size
    filled_cells = 0
    target_cells = total_cells // 2
    
    while filled_cells < target_cells:
        for i in range(layer, size - layer):
            for j in range(layer, size - layer):
                if (i == layer or i == size - layer - 1 or 
                    j == layer or j == size - layer - 1):
                    if grid[i][j] == 'o':
                        grid[i][j] = 'x'
                        filled_cells += 1
                        if filled_cells >= target_cells:
                            return grid
        layer += 1

def generate_columns_pattern(size=99):
    grid = create_empty_grid(size)
    for j in range(0, size, 2):
        for i in range(size):
            grid[i][j] = 'x'
    return grid

def generate_rows_pattern(size=99):
    grid = create_empty_grid(size)
    for i in range(0, size, 2):
        for j in range(size):
            grid[i][j] = 'x'
    return grid

def generate_checkerboard_pattern(size=99):
    grid = create_empty_grid(size)
    for i in range(size):
        for j in range(size):
            if (i + j) % 2 == 0:
                grid[i][j] = 'x'
    return grid

def generate_random_pattern(size=99):
    grid = create_empty_grid(size)
    total_cells = size * size
    target_cells = total_cells // 2
    filled_cells = 0
    
    while filled_cells < target_cells:
        i = np.random.randint(0, size)
        j = np.random.randint(0, size)
        if grid[i][j] == 'o':
            grid[i][j] = 'x'
            filled_cells += 1
    return grid

def visualize_pattern(grid, filename):
    # Create a new image with a white background
    size = len(grid)
    img = Image.new('RGB', (size, size), 'white')
    pixels = img.load()
    
    # Fill in black pixels where there are 'x's
    for i in range(size):
        for j in range(size):
            if grid[i][j] == 'x':
                pixels[j, i] = (0, 0, 0)  # Black
            else:
                pixels[j, i] = (255, 255, 255)  # White
    
    # Save the image
    img = img.resize((500, 500), Image.Resampling.NEAREST)  # Resize for better visibility
    img.save(filename)

def main():
    size = 99
    patterns = {
        'core': generate_core_pattern,
        'perimeter': generate_perimeter_pattern,
        'columns': generate_columns_pattern,
        'rows': generate_rows_pattern,
        'checkerboard': generate_checkerboard_pattern,
        'random': generate_random_pattern
    }
    
    # Create output directories if they don't exist
    if not os.path.exists('csv_output'):
        os.makedirs('csv_output')
    if not os.path.exists('image_output'):
        os.makedirs('image_output')
    
    for pattern_name, pattern_func in patterns.items():
        # Generate and save pattern
        grid = pattern_func(size)
        
        # Save CSV
        csv_filename = f'csv_output/{pattern_name}_pattern.csv'
        save_grid_to_csv(grid, csv_filename)
        
        # Save visualization
        img_filename = f'image_output/{pattern_name}_pattern.png'
        visualize_pattern(grid, img_filename)
        
        print(f"Generated {pattern_name} pattern - CSV: {csv_filename}, Image: {img_filename}")

if __name__ == "__main__":
    main()