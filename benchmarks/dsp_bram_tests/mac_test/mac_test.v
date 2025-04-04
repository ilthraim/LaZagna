// module mac_test (
//     input wire [7:0] a1, b1,
//     input wire [7:0] a2, b2,
//     input wire [7:0] a3, b3,
//     output wire [23:0] result
// );

//     // Internal wires for the multiplication results
//     wire [15:0] mult_result1;
//     wire [15:0] mult_result2;
//     wire [15:0] mult_result3;

//     // Accumulation wire
//     wire [23:0] acc_result;

//     // Perform multiplications directly
//     assign mult_result1 = a1 * b1;
//     assign mult_result2 = a2 * b2;
//     assign mult_result3 = a3 * b3;

//     // Chain the results through accumulation
//     assign acc_result = mult_result1 + mult_result2 + mult_result3;

//     // Output the final accumulated result
//     assign result = acc_result;

// endmodule

module mac_test (
    input wire [23:0] a1, 
    input wire [23:0] b1,
    output wire [51:0] result
);

    // Perform multiplications directly
    assign result = a1 * b1;

endmodule