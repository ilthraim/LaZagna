import os

original_path = os.getcwd()

for folder in os.listdir("./"):
    if os.path.isdir(folder):
        if folder == "results_csvs" or folder == "pngs":
            continue

        #check if result file exists
        if not os.path.exists(f"./results_csvs/{folder}_results.csv"):
            command = ["python3", original_path + "/csv_grouper.py", folder]
            os.system(" ".join(command))

            print(f"{folder} data concatenated into ./results_csvs/{folder}_results.csv")



exit(0)

