# Main scripting file to run 3DFADE
"""
# Options to give 3DFADE:

    1. VTR Architecture File
        If not provided defaults to templates files under "arch_files/templates"

    2. Benchmark Directory
        If not provided defaults to "benchmarks/MCNC_benchmarks"

    3. Benchmark Type
        2 Options: Verilog or BLIF
        If not provided defaults to BLIF

    4. 3D Fabric Width and Height
        If not provided defaults to 4x4

    5. 3D Fabric Layer Count (Hopefully)
        If not provided defaults to 2

    6. 2D Fabric Width and Height
        If not provided defaults to 4x4

    7. Routing Channel Width
        If not provided defaults to 10

    8. 3D Vertical Connection Type
        How the layers are connected together.
        Valid Options:
            * `2d`
                No 3D connections only 1 layer
            * `3d_cb`
                Inputs and Outputs of Grid locations are interlayer
            * `3d_cb_out_only`
                Only outputs of Grid locations are interlayer
            * `3d_sb`
                The Switch Boxes are interlayer
            * `3d_hybrid`
                Both Switch Boxes and Inputs and Outputs are interlayer (combination of `3d_cb` and `3d_sb`)
            * `3d_hybrid_out_only` 
                Both Switch Boxes and Outputs are interlayer (combination of `3d_cb_out_only` and `3d_sb`)
        If not provided defaults to `3d_cb`

    9. 3D Switch Block Connection Pattern
        The connection pattern of the switch blocks in the 3D fabric. Only valid for `3d_sb`, `3d_hybrid`, and `3d_hybrid_out_only` options.
        Valid Options:
            * `subset`
                subset/disjoint pattern
            * `wilton`
                wilton pattern with the following pattern structure (See README for more details): 0123,0123
            * `wilton_2`
                wilton pattern with the following pattern structure (See README for more details): 0000,0123
            * `wilton_3`
                wilton pattern with the following pattern structure (See README for more details): 0000,1111
            * `custom`
                Custom pattern defined using the `--sb_pattern_structure` option (required if `custom` is selected)
        If not provided defaults to `subset`

    10. 3D Switch Block Connection Pattern Structure
        The structure of the switch block connection pattern. Only valid for `3d_sb`, `3d_hybrid`, and `3d_hybrid_out_only` options with `custom` pattern.

    11. 3D Switch Block Vertical Channel Width
        The Vertical Channel Width of the 3D Switch Block. Only valid for `3d_sb`, `3d_hybrid`, and `3d_hybrid_out_only` options.
        This is a float that represents the size of the vertical channel as a percentage of the total channel width.
        If not provided defaults to 1.0

    12. Percentage of 3D Switch Blocks on Grid
        The percentage of Switch Blocks on the grid that are 3D. Only valid for `3d_sb`, `3d_hybrid`, and `3d_hybrid_out_only` options.
        Represented as a float between 0 and 1.
        If not provided defaults to 1.0

    13. 3D Switch Block Placement Strategy
        Where the 3D Switch Blocks are placed on the grid. Only valid for `3d_sb`, `3d_hybrid`, and `3d_hybrid_out_only` options.
        Valid Options:
            * `random`
                Random placement
            * `repeated_interval`
                Repeated interval placement. Location Determined by calculating total number of 3D SBs needed and then evenly distributing them across the grid where the grid is represented in a linearized fashion.
            * `edge`
                Edge placement is prioritized. 3D SBs are placed on the edge of the grid first. Once edge is full the center is filled in a repeated interval fashion.
            * `center`
                Center placement is prioritized. 3D SBs are placed in the center of the grid first. Once center is full the edge is filled in a repeated interval fashion.
        If not provided defaults to `repeated_interval`

    14. VTR Placement Cost Calculation Method:
        The method used to calculate the placement cost in VTR (--place_bounding_box_mode option).
        Valid Options:
            * `cube`
                Equivalent to the `cube_bb` option in VTR
            * `per_layer`
                Equivalent to the `per_layer_bb` option in VTR
        If not provided defaults to `cube`

    15. VTR Placement Random Seed
        The random seed used for VTR placement.
        If not provided defaults to 1

    16. Output File & Directory Name:
        The name of the output file and directory.
        If not provided defaults to the configuration and the benchmark name.

    18. Copy Run Directory 
        Boolean Option. If true, will copy the run directory to the output directory.
        If not provided defaults to False

    19. Copy Route Results
        Boolean Option. If true, will copy the route results (.route file) to the output directory.
        If not provided defaults to False, if Copy Run Directory is True this will be True as well.

    20. Copy Place Results
        Boolean Option. If true, will copy the place results (.place file) to the output directory.
        If not provided defaults to False, if Copy Run Directory is True this will be True as well.

    21. Addtional VPR Options
        Additional options to pass to VPR.
        If not provided defaults to None

    22. Verbose Mode
        If provided, will output more information about the process.
"""