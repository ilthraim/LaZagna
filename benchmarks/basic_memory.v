module basic_memory (
    input wire clk,
    input wire rst,
    input wire [7:0] data_in,
    input wire data_valid,
    output reg [15:0] result
);

    // Parameters
    parameter COEFF_WIDTH = 8;
    parameter DATA_WIDTH = 8;
    parameter RESULT_WIDTH = 16;
    parameter NUM_COEFFS = 8;

    // BRAM to store coefficients
    reg [COEFF_WIDTH-1:0] coeffs [0:NUM_COEFFS-1];

    // Internal signals
    reg [DATA_WIDTH-1:0] data_buffer [0:NUM_COEFFS-1];
    integer i;

    // Initialize coefficients (example values)
    initial begin
        coeffs[0] = 8'd1;
        coeffs[1] = 8'd2;
        coeffs[2] = 8'd3;
        coeffs[3] = 8'd4;
        coeffs[4] = 8'd5;
        coeffs[5] = 8'd6;
        coeffs[6] = 8'd7;
        coeffs[7] = 8'd8;
    end

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            result <= 0;
            for (i = 0; i < NUM_COEFFS; i = i + 1) begin
                data_buffer[i] <= 0;
            end
        end else if (data_valid) begin
            // Shift data buffer and insert new data
            for (i = NUM_COEFFS-1; i > 0; i = i - 1) begin
                data_buffer[i] <= data_buffer[i-1];
            end
            data_buffer[0] <= data_in;

            // Perform convolution
            result <= 0;
            for (i = 0; i < NUM_COEFFS; i = i + 1) begin
                result <= result + data_buffer[i] * coeffs[i];
            end
        end
    end

endmodule