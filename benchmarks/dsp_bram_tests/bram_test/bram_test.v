module bram_test (
    input wire clk,                    // Clock input
    input wire rst,                    // Reset input
    
    // Port A
    input wire [7:0] addr_a,          // Address for port A
    input wire [15:0] data_in_a,      // Data input for port A
    input wire we_a,                  // Write enable for port A
    output reg [15:0] data_out_a,     // Data output for port A
    
);

    // Define the memory array
    reg [15:0] ram [0:255];           // 256 locations x 16 bits

    wire [15:0] out;

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