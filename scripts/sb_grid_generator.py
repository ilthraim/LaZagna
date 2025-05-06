import csv
import os
import argparse

def create_empty_sb_grid_file(width, height, file_path="./"):
    '''
        Create an empty SB csv grid file with the given width and height. The user can use this as a sarting point for their SB grid lcoations.
        Writes a file called "sb_grid.csv" in the `file_path` directory, or current directory if unspecified.
    '''

    grid = [["o" for _ in range(width)] for _ in range(height)]
    with open(file_path + "sb_grid.csv", "w") as f:
        writer = csv.writer(f)
        writer.writerows(grid)

    print(f"Created empty SB grid file at {file_path}sb_grid.csv")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create an empty SB grid file.")
    parser.add_argument("--width", "-x",type=int, help="Width of the FPGA grid", required=True)
    parser.add_argument("--height", "-y",type=int, help="Height of the FPGA grid", required=True)
    parser.add_argument("--file_path", type=str, default="./", help="Path to save the SB grid file (default: current directory)")

    args = parser.parse_args()

    '''
    The SB grid is of dimensions (width - 1) x (height - 1). Since there are no SBs at the top and left edges of the grid. As shown in the example below.

    Example of a 5x5 FPGA grid:

    Legend:
        i = I/O
        o = SB location
        c = grid location (CLB, DSP, BRAM, etc.)
        - = Channel X
        | = Channel Y


                                i   i   i 
                              o - o - o - o 
                            i | c | c | c | i
                              o - o - o - o 
                            i | c | c | c | i
                              o - o - o - o 
                            i | c | c | c | i
                              o - o - o - o 
                                i   i   i 

    
    The grid is 5x5, but the SB locations are 4x4. The SB locations are the "o" characters in the grid.
    '''

    create_empty_sb_grid_file(args.width - 1, args.height - 1, args.file_path)