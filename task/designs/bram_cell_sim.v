module spram512x40(
  input clk,
  input [0:8] addr,
  input [0:39] datain,
  input we,
  output [0:39] dataout
);

  reg [0:39] mem [0:511];

  reg [0:39] out;

  always @(posedge clk) begin
    if (we) begin
      mem[addr] <= datain;
    end
    out <= mem[addr];
  end

  assign dataout = out;

endmodule

module spram1024x20(
  input clk,
  input [0:9] addr,
  input [0:19] datain,
  input we,
  output [0:19] dataout
);

  reg [0:19] mem [0:1023];

  reg [0:19] out;

  always @(posedge clk) begin
    if (we) begin
      mem[addr] <= datain;
    end
    out <= mem[addr];
  end

  assign dataout = out;

endmodule

module spram2048x10(
  input clk,
  input [0:10] addr,
  input [0:9] datain,
  input we,
  output [0:9] dataout
);

  reg [0:9] mem [0:2047];

  reg [0:9] out;

  always @(posedge clk) begin
    if (we) begin
      mem[addr] <= datain;
    end
    out <= mem[addr];
  end

  assign dataout = out;

endmodule


// module spram (
// 	input clk,
// 	input [10:0] addr1,
// 	input [39:0] din,
// 	input we1,
// 	output reg [39:0] dout,
// 	input [3:0] mode
// );

// 	reg [9:0] mem [0:2047]; // Memory array with 2048 entries of 10 bits each

// 	always @(posedge clk) begin
// 		case (mode)
// 			4'b0000: begin
// 				// Mode 0: 512x40 Single Port RAM
// 				if (we1) begin
// 					mem[{addr1[8:0], 2'b00}] <= din[9:0];
// 					mem[{addr1[8:0], 2'b01}] <= din[19:10];
// 					mem[{addr1[8:0], 2'b10}] <= din[29:20];
// 					mem[{addr1[8:0], 2'b11}] <= din[39:30];
// 				end
// 				dout <= {mem[{addr1[8:0], 2'b11}], mem[{addr1[8:0], 2'b10}], mem[{addr1[8:0], 2'b01}], mem[{addr1[8:0], 2'b00}]};
// 			end
// 			4'b0001: begin
// 				// Mode 1: 1024x20 Single Port RAM
// 				if (we1) begin
// 					mem[{addr1[9:0], 1'b0}] <= din[9:0];
// 					mem[{addr1[9:0], 1'b1}] <= din[19:10];
// 				end
// 				dout <= {20'b0, mem[{addr1[9:0], 1'b1}], mem[{addr1[9:0], 1'b0}]};
// 			end
// 			4'b0010: begin
// 				// Mode 2: 2048x10 Single Port RAM
// 				if (we1) begin
// 					mem[addr1] <= din[9:0];
// 				end
// 				dout <= {30'b0, mem[addr1]};
// 			end
			
// 		endcase
// 	end

// endmodule



// 27x27 multiplier
module one_mult_27x27(
  input [0:26] A,
  input [0:26] B,
  output [0:53] Y
);

assign Y = A * B;

endmodule

// 18x19 multiplier
module two_mult_18x19(
  input [0:17] A,
  input [0:18] B,
  output [0:36] Y
);

assign Y = A * B;

endmodule