import os
import re

original_path = os.getcwd()
# Get all directories and subdirectories
all_folders = []
for root, dirs, files in os.walk("./"):
    for dir in dirs:
        folder_path = os.path.join(root, dir)
        # Convert to relative path
        rel_path = os.path.relpath(folder_path, "./")
        if os.path.basename(rel_path).startswith("3d_"):
            all_folders.append(rel_path)

folder_pattern = re.compile(r".*_cw_(\d+)_(\d+x\d+)_.+")

for folder in all_folders:
    # Check if the folder name matches the pattern
    match = folder_pattern.match(os.path.basename(folder))
    if match:
        
        cw = match.group(1)

        axb = match.group(2)

        #check if result file exists
        # Check if result file exists anywhere in results_csvs directory
        csv_found = False
        if os.path.exists("./results_csvs"):
            for root, dirs, files in os.walk("./results_csvs/" + axb + "/CW_" + cw):
                if f"{os.path.basename(folder)}_results.csv" in files:
                    csv_found = True
                    break
        
        if not csv_found:
            command = ["python3", original_path + "/csv_grouper.py", folder]
            os.system(" ".join(command))

            print(f"{folder} data concatenated into ./results_csvs/{os.path.basename(folder)}_results.csv")

    else:
        print(f"Folder {folder} does not match the expected pattern *_cw_X_AxB_*")
        continue

# Organize directory and CSV files
command = ["python3", original_path + "/result_folder_organizer.py", "./", "./results_csvs/"]
os.system(" ".join(command))
exit(0)

