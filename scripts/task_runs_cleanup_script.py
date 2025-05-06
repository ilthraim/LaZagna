import os
import re
from datetime import datetime
import shutil
import argparse

def parse_directory_name(dir_name):
    # Regular expression to extract the required components
    pattern = r'3d_(\w+)_cw_(\d+)_(\d+x\d+)_.*?_(\d{4}-\d{2}-\d{2})_'
    
    match = re.search(pattern, dir_name)
    if match:
        type_name = match.group(1)
        cw = match.group(2)
        axb = match.group(3)
        date = match.group(4)
        return {
            'type': type_name,
            'cw': cw,
            'axb': axb,
            'date': date
        }
    return None

def organize_directories(start_dir):
    # Get all subdirectories in the start directory
    subdirs = [d for d in os.listdir(start_dir) if os.path.isdir(os.path.join(start_dir, d))]
    
    for subdir in subdirs:
        # Parse the directory name
        components = parse_directory_name(subdir)
        
        if components:
            # Create the new path structure
            new_path = os.path.join(
                start_dir,
                components['date'],
                components['axb'],
                f"cw{components['cw']}",
                components['type'],
                subdir
            )
            
            # Create all necessary parent directories
            os.makedirs(os.path.dirname(new_path), exist_ok=True)
            
            # Move the directory to its new location
            old_path = os.path.join(start_dir, subdir)
            if old_path != new_path:  # Avoid moving if already in correct location
                try:
                    shutil.move(old_path, new_path)
                    print(f"Moved {subdir} to {new_path}")
                except Exception as e:
                    print(f"Error moving {subdir}: {e}")
            # print(f"start_dir: {start_dir}, date: {components['date']}, axb: {components['axb']}, cw: {components['cw']}, type: {components['type']}")
        else:
            print(f"Could not parse directory name: {subdir}")

# Usage
if __name__ == "__main__":
    start_dir = "/home/Ismael/3DFADE/tasks_run"  # Replace with your actual directory path
    organize_directories(start_dir)