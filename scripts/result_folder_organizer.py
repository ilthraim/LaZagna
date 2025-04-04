import os
import re
import shutil
import sys

def organize_directories(source_path):
    # Pattern to match the format "*_cw_X_AxB_*"
    pattern = r'.*_cw_(\d+)_(\d+x\d+)_.*'
    
    # Dictionary to store AxB -> X values mapping
    structure = {}
    
    # First pass: identify all unique AxB and X combinations
    for dirname in os.listdir(source_path):
        match = re.match(pattern, dirname)
        if match:
            x_value, axb = match.groups()
            if axb not in structure:
                structure[axb] = set()
            structure[axb].add(x_value)
    
    # Create the new directory structure
    for axb in structure:
        # Create main AxB directory
        axb_path = os.path.join(source_path, axb)
        os.makedirs(axb_path, exist_ok=True)
        
        # Create subdirectories for each X value
        for x in structure[axb]:
            x_path = os.path.join(axb_path, f'CW_{x}')
            os.makedirs(x_path, exist_ok=True)
    
    # Second pass: move directories to their new locations
    for dirname in os.listdir(source_path):
        match = re.match(pattern, dirname)
        if match:
            x_value, axb = match.groups()
            old_path = os.path.join(source_path, dirname)
            new_path = os.path.join(source_path, axb, f'CW_{x_value}', dirname)
            
            try:
                shutil.move(old_path, new_path)
                print(f"Moved {dirname} to {new_path}")
            except Exception as e:
                print(f"Error moving {dirname}: {e}")




def organize_csv_files(source_path):
    # Pattern to match the format "*_cw_X_AxB_*.csv"
    pattern = r'.*_cw_(\d+)_(\d+x\d+)_.*\.csv$'
    
    # Dictionary to store AxB -> X values mapping
    structure = {}
    
    # First pass: identify all unique AxB and X combinations
    for filename in os.listdir(source_path):
        match = re.match(pattern, filename)
        if match:
            x_value, axb = match.groups()
            if axb not in structure:
                structure[axb] = set()
            structure[axb].add(x_value)
    
    # Create the new directory structure
    for axb in structure:
        # Create main AxB directory
        axb_path = os.path.join(source_path, axb)
        os.makedirs(axb_path, exist_ok=True)
        
        # Create subdirectories for each X value
        for x in structure[axb]:
            x_path = os.path.join(axb_path, f'CW_{x}')
            os.makedirs(x_path, exist_ok=True)
    
    # Second pass: move CSV files to their new locations
    for filename in os.listdir(source_path):
        match = re.match(pattern, filename)
        if match:
            x_value, axb = match.groups()
            old_path = os.path.join(source_path, filename)
            new_path = os.path.join(source_path, axb, f'CW_{x_value}', filename)
            
            try:
                shutil.move(old_path, new_path)
                print(f"Moved {filename} to {new_path}")
            except Exception as e:
                print(f"Error moving {filename}: {e}")

# Usage python3 result_folder_organizer.py <source_directory> <source_directory_csvs>

#Check there are 2 arguments given
if len(sys.argv) < 3:
    print("Usage: python3 result_folder_organizer.py <source_directory> <source_directory_csvs>")
    exit(0)

source_directory = sys.argv[1]

source_directory_csvs = sys.argv[2]

organize_directories(source_directory)
organize_csv_files(source_directory_csvs)