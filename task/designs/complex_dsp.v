/*
    DSP block inspired by VTR Architecure Complex DSP described in the architecture (and in many more):
        3d_full_OPIN_inter_die_k6FracN10LB_mem20k_complexDSP_customSB_7nm.xml
    
    This block however is missing one of the modes which is the "mult_add_mode_18_19_36" which is not implemented here.
*/

module complex_dsp (
    input wire [73:0] I,
    input wire [2:0] mode,
    output [73:0] result
);

    reg [2:0] mode_reg;
        
    reg [73:0] out_reg;
    reg [73:0] I_reg;
    always @(*) begin
    
        mode_reg = mode;
        I_reg = I;
        // Depending on the mode, we will perform different operations
        case(mode_reg)
            3'b000: begin
                // Mode 0: 27x27 multiplier
                out_reg[53:0] <= I_reg[53:27] * I_reg[26:0];
            end
            3'b001: begin
                // Mode 1: 2 18x19 multipliers
                out_reg[36:0] <= I_reg[17:0] * I_reg[36:18];
                out_reg[73:37] <= I_reg[54:37] * I_reg[73:55];
            end
            // 3'b010: begin
            //     // Mode 2: MAC [ (ax * ay) + (bx * by) + chainin = result, chainout = result ]
            //     result <= (I[17:0] * I[36:18]) + (I[54:37] * I[73:55]) + chainin;
            //     chainout <= result;
            // end
            // 3'b011: begin // TODO: Figure out what that means
            //     // Mode 3: MAC W/ scanin-scanout support ? [ (ax * ay) + b + chainin = result, chainout = result, scanout = result]
            //     result <= I1 / I2;
            // end
            // 3'b100: begin
            //     // Mode 4: 4 MAC operations [ (ax * ay) + (bx * by) + (cx * cy) + (dx * dy) + chainin = result, chainout = result ]
            //     result <= (I[8:0] * I[17:9]) + (I[26:18] * I[35:27]) + (I[44:36] * I[53:45]) + (I[62:54] * I[71:63]) + chainin;
            //     chainout <= result;
            // end
            // 3'b101: begin
            //     // Mode 5: Scan
            //     result <= I1;
            //     scanout <= scanin;
            // end
            default: begin
                // Default: Add
                out_reg <= I_reg;
            end
        endcase
    end
    
    assign result = out_reg;
    
endmodule

