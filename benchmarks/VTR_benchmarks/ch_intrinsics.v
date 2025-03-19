

`define MEMORY_CONTROLLER_TAGS 1
`define MEMORY_CONTROLLER_TAG_SIZE 1
`define TAG__str 1'b0
`define MEMORY_CONTROLLER_ADDR_SIZE 32
`define MEMORY_CONTROLLER_DATA_SIZE 32


module memory_controller
(
	clk,
	memory_controller_address,
	memory_controller_write_enable,
	memory_controller_in,
	memory_controller_out
);
input clk;
input [`MEMORY_CONTROLLER_ADDR_SIZE-1:0] memory_controller_address;
input memory_controller_write_enable;
input [`MEMORY_CONTROLLER_DATA_SIZE-1:0] memory_controller_in;
output  [`MEMORY_CONTROLLER_DATA_SIZE-1:0] memory_controller_out;
reg [`MEMORY_CONTROLLER_DATA_SIZE-1:0] memory_controller_out;


reg [4:0] str_address;
reg str_write_enable;
reg [7:0] str_in;
wire [7:0] str_out;

single_port_ram _str (
	.clk( clk ),
	.addr( str_address ),
	.we( str_write_enable ),
	.data( str_in ),
	.out( str_out )
);


wire  tag;

//must use all wires inside module.....
assign tag = |memory_controller_address & |memory_controller_address & | memory_controller_in;
reg [`MEMORY_CONTROLLER_TAG_SIZE-1:0] prevTag;
always @(posedge clk)
	prevTag <= tag;
always @( tag or memory_controller_address or memory_controller_write_enable or memory_controller_in)
begin

case(tag)

	1'b0:
	begin
		str_address = memory_controller_address[5-1+0:0];
		str_write_enable = memory_controller_write_enable;
		str_in[8-1:0] = memory_controller_in[8-1:0];
	end
endcase

case(prevTag)

	1'b0:
		memory_controller_out = str_out;
endcase
end

endmodule 


module memset
	(
		clk,
		reset,
		start,
		finish,
		return_val,
		m,
		c,
		n,
		memory_controller_write_enable,
		memory_controller_address,
		memory_controller_in,
		memory_controller_out
	);

output[`MEMORY_CONTROLLER_ADDR_SIZE-1:0] return_val;
reg [`MEMORY_CONTROLLER_ADDR_SIZE-1:0] return_val;
input clk;
input reset;
input start;

output finish;
reg finish;

input [`MEMORY_CONTROLLER_ADDR_SIZE-1:0] m;
input [31:0] c;
input [31:0] n;

output [`MEMORY_CONTROLLER_ADDR_SIZE-1:0] memory_controller_address;
reg [`MEMORY_CONTROLLER_ADDR_SIZE-1:0] memory_controller_address;

output  memory_controller_write_enable;
reg memory_controller_write_enable;

output [`MEMORY_CONTROLLER_DATA_SIZE-1:0] memory_controller_in;
reg [`MEMORY_CONTROLLER_DATA_SIZE-1:0] memory_controller_in;
 
output [`MEMORY_CONTROLLER_DATA_SIZE-1:0] memory_controller_out;

reg [3:0] cur_state;

/*
parameter Wait = 4'd0;
parameter entry = 4'd1;
parameter entry_1 = 4'd2;
parameter entry_2 = 4'd3;
parameter bb = 4'd4;
parameter bb_1 = 4'd5;
parameter bb1 = 4'd6;
parameter bb1_1 = 4'd7;
parameter bb_nph = 4'd8;
parameter bb2 = 4'd9;
parameter bb2_1 = 4'd10;
parameter bb2_2 = 4'd11;
parameter bb2_3 = 4'd12;
parameter bb2_4 = 4'd13;
parameter bb4 = 4'd14;
*/

memory_controller memtroll (clk,memory_controller_address, memory_controller_write_enable, memory_controller_in,  memory_controller_out);


reg [31:0] indvar;
reg  var1;
reg [31:0] tmp;
reg [31:0] tmp8;
reg  var2;
reg [31:0] var0;
reg [`MEMORY_CONTROLLER_ADDR_SIZE-1:0] scevgep;
reg [`MEMORY_CONTROLLER_ADDR_SIZE-1:0] s_07;
reg [31:0] indvar_next;
reg  exitcond;

always @(posedge clk)
if (reset)
	cur_state <= 4'b0000;
else
case(cur_state)
	4'b0000:
	begin
		finish <= 1'b0;
		if (start == 1'b1)
			cur_state <= 4'b0001;
		else
			cur_state <= 4'b0000;
	end
	4'b0001:
	begin

		

		var0 <= n & 32'b00000000000000000000000000000011;

		cur_state <= 4'b0010;
	end
	4'b0010:
	begin

		var1 <= 1'b0;
		var0 <= 32'b00000000000000000000000000000000;

		cur_state <= 4'b0011;
	end
	4'b0011:
	begin

		
		if (|var1) begin
			cur_state <= 4'b0110;
		end
		else 
		begin
		
			cur_state <= 4'b0100;
		end
	end
	4'b0100:
	begin
	
		cur_state <= 4'b0101;
	end
	4'b0101:
	begin
		cur_state <= 4'b0110;
	end
	4'b0110:
	begin

		var2 <= | (n [31:4]);

		cur_state <= 4'b0111;
	end
	4'b0111:
	begin
	
		if (|var2) 
		begin
			cur_state <= 4'b1110;
		end
		else
		begin
			cur_state <= 4'b1000;
		end
	end
	4'b1000:
	begin
                 
		tmp <= n ;

		indvar <= 32'b00000000000000000000000000000000;   
		cur_state <= 4'b1001;
	end
	4'b1001:
	begin

		cur_state <= 4'b1010;
	end
	4'b1010:
	begin
	tmp8 <= indvar;
		indvar_next <= indvar;
		cur_state <= 4'b1011;
	end
	4'b1011:
	begin

		scevgep <= (m & tmp8);

		exitcond <= (indvar_next == tmp);

		cur_state <= 4'b1100;
	end
	4'b1100:
	begin

		s_07 <= scevgep;

		cur_state <= 4'b1101;
	end
	4'b1101:
	
	begin


		if (exitcond)
		begin
				cur_state <= 4'b1110;
		end
			else 
		begin
				indvar <= indvar_next;   
				cur_state <= 4'b1001;
		end
	end
	
	
	4'b1110:
	begin

		return_val <= m;
		finish <= 1'b1;
		cur_state <= 4'b0000;
	end
endcase

always @(cur_state)
begin

	case(cur_state)
	4'b1101:
	begin
		memory_controller_address = s_07;
		memory_controller_write_enable = 1'b1;
		memory_controller_in = c;
	end
	endcase
end

endmodule

//---------------------------------------
// A single-port 32x8bit RAM 
// This module is tuned for VTR's benchmarks
//---------------------------------------
module single_port_ram (
	input clk,
	input we,
	input [4:0] addr,
	input [7:0] data,
	output [7:0] out );

	reg [7:0] ram[31:0];
	reg [7:0] internal;

	assign out = internal;

	always @(posedge clk) begin
		if(wen) begin
			ram[addr] <= data;
		end

		if(ren) begin
			internal <= ram[addr];
		end
	end

endmodule

//K-input Look-Up Table
module LUT_K #(
    //The Look-up Table size (number of inputs)
    parameter K = 1, 

    //The lut mask.  
    //Left-most (MSB) bit corresponds to all inputs logic one. 
    //Defaults to always false.
    parameter LUT_MASK={2**K{1'b0}} 
) (
    input [K-1:0] in,
    output out
);

    specify
        (in *> out) = "";
    endspecify

    assign out = LUT_MASK[in];

endmodule

//D-FlipFlop module
module DFF #(
    parameter INITIAL_VALUE=1'b0    
) (
    input clk,
    input D,
    output reg Q
);

    specify
        (clk => Q) = "";
        $setup(D, posedge clk, "");
        $hold(posedge clk, D, "");
    endspecify

    initial begin
        Q <= INITIAL_VALUE;
    end

    always@(posedge clk) begin
        Q <= D;
    end
endmodule

//Routing fpga_interconnect module
module fpga_interconnect(
    input datain,
    output dataout
);

    specify
        (datain=>dataout)="";
    endspecify

    assign dataout = datain;

endmodule


//2-to-1 mux module
module mux(
    input select,
    input x,
    input y,
    output z
);

    assign z = (x & ~select) | (y & select);

endmodule

//n-bit adder
module adder #(
    parameter WIDTH = 1   
) (
    input [WIDTH-1:0] a, 
    input [WIDTH-1:0] b, 
    input cin, 
    output cout, 
    output [WIDTH-1:0] sumout);

   specify
      (a*>sumout)="";
      (b*>sumout)="";
      (cin*>sumout)="";
      (a*>cout)="";
      (b*>cout)="";
      (cin=>cout)="";
   endspecify
   
   assign {cout, sumout} = a + b + cin;
   
endmodule
   
//nxn multiplier module
module multiply #(
    //The width of input signals
    parameter WIDTH = 1
) (
    input [WIDTH-1:0] a,
    input [WIDTH-1:0] b,
    output [2*WIDTH-1:0] out
);

    specify
        (a *> out) = "";
        (b *> out) = "";
    endspecify

    assign out = a * b;

endmodule // mult

//single_port_ram module
(* keep_hierarchy *)
module single_port_ram #(
    parameter ADDR_WIDTH = 1,
    parameter DATA_WIDTH = 1
) (
    input clk,
    input [ADDR_WIDTH-1:0] addr,
    input [DATA_WIDTH-1:0] data,
    input we,
    output reg [DATA_WIDTH-1:0] out
);

    localparam MEM_DEPTH = 2 ** ADDR_WIDTH;

    reg [DATA_WIDTH-1:0] Mem[MEM_DEPTH-1:0];

    specify
        (clk*>out)="";
        $setup(addr, posedge clk, "");
        $setup(data, posedge clk, "");
        $setup(we, posedge clk, "");
        $hold(posedge clk, addr, "");
        $hold(posedge clk, data, "");
        $hold(posedge clk, we, "");
    endspecify
   
    always@(posedge clk) begin
        if(we) begin
            Mem[addr] = data;
        end
    	out = Mem[addr]; //New data read-during write behaviour (blocking assignments)
    end
   
endmodule // single_port_RAM

//dual_port_ram module
(* keep_hierarchy *)
module dual_port_ram #(
    parameter ADDR_WIDTH = 1,
    parameter DATA_WIDTH = 1
) (
    input clk,

    input [ADDR_WIDTH-1:0] addr1,
    input [ADDR_WIDTH-1:0] addr2,
    input [DATA_WIDTH-1:0] data1,
    input [DATA_WIDTH-1:0] data2,
    input we1,
    input we2,
    output reg [DATA_WIDTH-1:0] out1,
    output reg [DATA_WIDTH-1:0] out2
);

    localparam MEM_DEPTH = 2 ** ADDR_WIDTH;

    reg [DATA_WIDTH-1:0] Mem[MEM_DEPTH-1:0];

    specify
        (clk*>out1)="";
        (clk*>out2)="";
        $setup(addr1, posedge clk, "");
        $setup(addr2, posedge clk, "");
        $setup(data1, posedge clk, "");
        $setup(data2, posedge clk, "");
        $setup(we1, posedge clk, "");
        $setup(we2, posedge clk, "");
        $hold(posedge clk, addr1, "");
        $hold(posedge clk, addr2, "");
        $hold(posedge clk, data1, "");
        $hold(posedge clk, data2, "");
        $hold(posedge clk, we1, "");
        $hold(posedge clk, we2, "");
    endspecify
   
    always@(posedge clk) begin //Port 1
        if(we1) begin
            Mem[addr1] = data1;
        end
        out1 = Mem[addr1]; //New data read-during write behaviour (blocking assignments)
    end

    always@(posedge clk) begin //Port 2
        if(we2) begin
            Mem[addr2] = data2;
        end
        out2 = Mem[addr2]; //New data read-during write behaviour (blocking assignments)
    end
   
endmodule // dual_port_ram