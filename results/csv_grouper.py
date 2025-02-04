import os
import csv
import sys

csv_folder = "results_csvs"

# Get input folder from CLI argument or use the script's directory
if len(sys.argv) == 2:
    input_folder = sys.argv[1]
else:
    input_folder = os.path.dirname(os.path.abspath(__file__))

# Remove trailing slash from the input folder path if present
if input_folder.endswith("/"):
    input_folder = input_folder[:-1]

# Define the results folder
results_folder = csv_folder

# Create the results folder if it doesn't exist
os.makedirs(results_folder, exist_ok=True)

# Define the output file path within the results folder
output_file = os.path.join(results_folder, input_folder + "_results.csv")

# Initialize a list to store all rows
all_data = []

# Iterate through all files in the input folder
for filename in os.listdir(input_folder):
    if filename.endswith(".csv"):
        file_path = os.path.join(input_folder, filename)
        
        # Open the CSV file and read its contents
        with open(file_path, mode='r') as file:
            reader = csv.reader(file)
            rows = list(reader)
            
            # Ensure the file has at least two lines (header + data)
            if len(rows) >= 2:
                headers = rows[0]
                data = rows[1]

                # Modify the first data value as specified
                original_value = data[0]
                if original_value.startswith("00_") and original_value.endswith("_Common"):
                    extracted = original_value[3:-7]  # Extract 'XXX' part
                    data[0] = extracted

                # Append the header if it's the first file
                if not all_data:
                    all_data.append(headers)

                # Append the data row
                all_data.append(data)

# Write all concatenated data to the output file
with open(output_file, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerows(all_data)

print(f"Data concatenated into {output_file}")
