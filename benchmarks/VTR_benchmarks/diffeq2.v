
/*--------------------------------------------------------------------------
--------------------------------------------------------------------------
--	File Name 	: diffeq.v
--	Author(s)	: P. Sridhar
--	Affiliation	: Laboratory for Digital Design Environments
--			  Department of Electrical & Computer Engineering
--			  University of Cincinnati
--	Date Created	: June 1991.
--	Introduction	: Behavioral description of a differential equation
--			  solver written in a synthesizable subset of VHDL.
--	Source		: Written in HardwareC by Rajesh Gupta, Stanford Univ. 
--			  Obtained from the Highlevel Synthesis Workshop
--                        Repository.
--
--	Modified For Synthesis by Jay(anta) Roy, University of Cincinnati.
--	Date Modified	: Sept, 91.
--
--	Disclaimer	: This comes with absolutely no guarantees of any
--			  kind (just stating the obvious ...)
--
--      Acknowledgement : The Distributed Synthesis Systems research at 
--                        the Laboratory for Digital Design Environments,
--                        University of Cincinnati, is sponsored in part 
--                        by the Defense Advanced Research Projects Agency 
--                        under order number 7056 monitored by the Federal 
--                        Bureau of Investigation under contract number 
--                        J-FBI-89-094.
--
--------------------------------------------------------------------------
-------------------------------------------------------------------------*/
module diffeq_f_systemC(aport, dxport, xport, yport, uport, clk, reset);

input clk;
input reset;
input [31:0]aport;
input [31:0]dxport;
output [31:0]xport;
output [31:0]yport;
output [31:0]uport;
reg [31:0]xport;
reg [31:0]yport;
reg [31:0]uport;
wire [31:0]temp;

assign temp = uport * dxport;
always @(posedge clk )
begin
	if (reset == 1'b1)
	begin
		xport <= 0;
		yport <= 0;
		uport <= 0;
	end
else
  	if (xport < aport) 
	begin
		xport <= xport + dxport;
		yport <= yport + temp;//(uport * dxport);
		uport <= (uport - (temp/*(uport * dxport)*/ * (5 * xport))) - (dxport * (3 * yport));
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