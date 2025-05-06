module mac_with_bram_test (
    input wire clk,
    output [49:0] result
);

    // BRAM instances
    wire [15:0] bram_data_out [0:5];
    reg [7:0] bram_addr [0:5];
    reg [15:0] bram_data_in [0:5];
    reg bram_we [0:5];

    // MAC inputs and output
    wire [7:0] a1, b1, a2, b2, a3, b3;
    wire [49:0] mac_result;

    // Instantiate 6 BRAMs
    genvar i;
    generate
        for (i = 0; i < 6; i = i + 1) begin : bram_instances
            bram bram_inst (
                .clk(clk),
                .addr_a(bram_addr[i]),
                .data_in_a(bram_data_in[i]),
                .we_a(bram_we[i]),
                .data_out_a(bram_data_out[i])
            );
        end
    endgenerate

    // Instantiate the MAC unit
    mac mac_inst (
        .a1(a1),
        .b1(b1),
        .a2(a2),
        .b2(b2),
        .a3(a3),
        .b3(b3),
        .result(mac_result)
    );

    // Assign MAC inputs from BRAM outputs
    assign a1 = bram_data_out[0][7:0];
    assign b1 = bram_data_out[1][7:0];
    assign a2 = bram_data_out[2][7:0];
    assign b2 = bram_data_out[3][7:0];
    assign a3 = bram_data_out[4][7:0];
    assign b3 = bram_data_out[5][7:0];

    // Control logic
    always @(posedge clk) begin
            // Read values from BRAMs
        bram_addr[0] <= 8'd1;
        bram_addr[1] <= 8'd2;
        bram_addr[2] <= 8'd3;
        bram_addr[3] <= 8'd4;
        bram_addr[4] <= 8'd5;
        bram_addr[5] <= 8'd6;

        // Store MAC result in the first address of the first BRAM
        bram_addr[0] <= 8'd0;
        bram_data_in[0] <= mac_result[15:0]; // Store lower 16 bits
        bram_we[0] <= 1'b1;
    end

    assign result = mac_result;

endmodule


module mac (
    input wire [7:0] a1, b1,
    input wire [7:0] a2, b2,
    input wire [7:0] a3, b3,
    output wire [49:0] result
);

    // Internal wires for the multiplication results
    wire [15:0] mult_result1;
    wire [15:0] mult_result2;
    wire [15:0] mult_result3;

    // Accumulation wire
    wire [23:0] acc_result1;
    wire [23:0] acc_result2;

    wire [49:0] acc_result;

    // Perform multiplications directly
    assign mult_result1 = a1 * b1;
    assign mult_result2 = a2 * b2;
    assign mult_result3 = a3 * b3;

    // Chain the results through accumulation
    assign acc_result1 = mult_result1 + mult_result2 + mult_result3;
    assign acc_result2 = mult_result1 + mult_result2 + a1;

    assign acc_result = acc_result1 * acc_result2;
    
    // Output the final accumulated result
    assign result = acc_result;

endmodule


module bram (
    input wire clk,                    // Clock input
    
    // Port A
    input wire [7:0] addr_a,          // Address for port A
    input wire [15:0] data_in_a,      // Data input for port A
    input wire we_a,                  // Write enable for port A
    output wire [15:0] data_out_a     // Data output for port A
    
);

    // Define the memory array
    reg [15:0] ram [0:255];           // 256 locations x 16 bits

    reg [15:0] out;

    // wire [15:0] out_b;

    // Port A operations
    always @(posedge clk) begin

        if (we_a) begin
            ram[addr_a] <= data_in_a;
        end
        out <= ram[addr_a];
    end

    assign data_out_a = out;


endmodule