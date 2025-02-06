# Call rrg_walker.py for every file in the given directory and count the number of interlayer contacts in each file.
# The results are saved in a csv file.

import os
import sys
import csv
import subprocess
from concurrent.futures import ThreadPoolExecutor

def main():
    if len(sys.argv) != 2:
        print("Usage: python interlayer_counter.py <directory>")
        sys.exit(1)

    directory = sys.argv[1]
    if not os.path.isdir(directory):
        print("Error: Directory not found.")
        sys.exit(1)

    # Create a csv file to store the results
    csv_file = open("interlayer_contacts.csv", "w")
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(["File", "Interlayer contacts"])

    # Call rrg_walker.py for every file in the directory
    def process_file(filename):
        print("Processing", filename)
        if filename.endswith(".xml"):
            p = subprocess.Popen(["python3", "rrg_walker.py", os.path.join(directory, filename), "-i"], stdout=subprocess.PIPE)
            out, err = p.communicate()
            out = out.decode("utf-8")
            out = out.split("\n")
            interlayer_contacts = out[0]
            print("Done Processing", filename)
            return filename, interlayer_contacts
        return None

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(process_file, filename) for filename in os.listdir(directory)]
        for future in futures:
            result = future.result()
            if result:
                csv_writer.writerow(result)

    csv_file.close()

if __name__ == "__main__":
    main()