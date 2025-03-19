/////////////////////////////////////////////////////////////////////
////                                                             ////
////  SHA-160                                                    ////
////  Secure Hash Algorithm (SHA-160)                            ////
////                                                             ////
////  Author: marsgod                                            ////
////          marsgod@opencores.org                              ////
////                                                             ////
////                                                             ////
////  Downloaded from: http://www.opencores.org/cores/sha_core/  ////
////                                                             ////
/////////////////////////////////////////////////////////////////////
////                                                             ////
//// Copyright (C) 2002-2004 marsgod                             ////
////                         marsgod@opencores.org               ////
////                                                             ////
////                                                             ////
//// This source file may be used and distributed without        ////
//// restriction provided that this copyright statement is not   ////
//// removed from the file and that any derivative work contains ////
//// the original copyright notice and the associated disclaimer.////
////                                                             ////
////     THIS SOFTWARE IS PROVIDED ``AS IS'' AND WITHOUT ANY     ////
//// EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED   ////
//// TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS   ////
//// FOR A PARTICULAR PURPOSE. IN NO EVENT SHALL THE AUTHOR      ////
//// OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,         ////
//// INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES    ////
//// (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE   ////
//// GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR        ////
//// BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF  ////
//// LIABILITY, WHETHER IN  CONTRACT, STRICT LIABILITY, OR TORT  ////
//// (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT  ////
//// OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE         ////
//// POSSIBILITY OF SUCH DAMAGE.                                 ////
////                                                             ////
/////////////////////////////////////////////////////////////////////

`define SHA1_H0 32'h67452301
`define SHA1_H1 32'hefcdab89
`define SHA1_H2 32'h98badcfe
`define SHA1_H3 32'h10325476
`define SHA1_H4 32'hc3d2e1f0

`define SHA1_K0 32'h5a827999
`define SHA1_K1 32'h6ed9eba1
`define SHA1_K2 32'h8f1bbcdc
`define SHA1_K3 32'hca62c1d6

module sha1 (clk_i, rst_i, text_i, text_o, cmd_i, cmd_w_i, cmd_o);

	input		clk_i; 	// global clock input
	input		rst_i; 	// global reset input , active high
	
	input	[31:0]	text_i;	// text input 32bit
	output	[31:0]	text_o;	// text output 32bit
	
	input	[2:0]	cmd_i;	// command input
	input		cmd_w_i;// command input write enable
	output	[3:0]	cmd_o;	// command output(status)

	/*
		cmd
		Busy Round W R

		bit3 bit2  bit1 bit0
		Busy Round W    R
		
		Busy:
		0	idle
		1	busy
		
		Round:
		0	first round
		1	internal round
		
		W:
		0       No-op
		1	write data
		
		R:
		0	No-op
		1	read data
			
	*/
	

    	reg	[3:0]	cmd;
    	wire	[3:0]	cmd_o;
    	
    	reg	[31:0]	text_o;
    	
    	reg	[6:0]	round;
    	wire	[6:0]	round_plus_1;
    	
    	reg	[2:0]	read_counter;
    	
    	reg	[31:0]	H0,H1,H2,H3,H4;
    	reg	[31:0]	W0,W1,W2,W3,W4,W5,W6,W7,W8,W9,W10,W11,W12,W13,W14;
    	reg	[31:0]	Wt,Kt;
    	reg	[31:0]	A,B,C,D,E;

    	reg		busy;
    	
    	assign cmd_o = cmd;
    	always @ (posedge clk_i)
    	begin
    		if (rst_i)
    			cmd <= 4'b0000;
    		else
    		if (cmd_w_i)
    			cmd[2:0] <= cmd_i[2:0];		// busy bit can't write
    		else
    		begin
    			cmd[3] <= busy;			// update busy bit
    			if (~busy)
    				cmd[1:0] <= 2'b00;	// hardware auto clean R/W bits
    		end
    	end
    	
    	// Hash functions
	wire [31:0] SHA1_f1_BCD,SHA1_f2_BCD,SHA1_f3_BCD,SHA1_Wt_1;
	wire [31:0] SHA1_ft_BCD;
	wire [31:0] next_Wt,next_A,next_C;
	wire [159:0] SHA1_result;
	
	assign SHA1_f1_BCD = (B & C) ^ (~B & D);
	assign SHA1_f2_BCD = B ^ C ^ D;
	assign SHA1_f3_BCD = (B & C) ^ (C & D) ^ (B & D);
	
	assign SHA1_ft_BCD = (round < 7'b0100101) ? SHA1_f1_BCD : (round < 7'b101001) ? SHA1_f2_BCD : (round < 7'b1111101) ? SHA1_f3_BCD : SHA1_f2_BCD;
	
	// Odin II doesn't support binary operations inside concatenations presently. 
	//assign SHA1_Wt_1 = {W13 ^ W8 ^ W2 ^ W0};
	assign SHA1_Wt_1 = W13 ^ W8 ^ W2 ^ W0;

	assign next_Wt = {SHA1_Wt_1[30:0],SHA1_Wt_1[31]};	// NSA fix added
	assign next_A = {A[26:0],A[31:27]} + SHA1_ft_BCD + E + Kt + Wt;
	assign next_C = {B[1:0],B[31:2]};
	
	assign SHA1_result   = {A,B,C,D,E};
	
	assign round_plus_1 = round + 1;
	
	//------------------------------------------------------------------	
	// SHA round
	//------------------------------------------------------------------
	always @(posedge clk_i)
	begin
		if (rst_i)
		begin
			round <= 7'b0000000;
			busy <= 1'b0;

			W0  <= 32'b00000000000000000000000000000000;
			W1  <= 32'b00000000000000000000000000000000;
			W2  <= 32'b00000000000000000000000000000000;
			W3  <= 32'b00000000000000000000000000000000;
			W4  <= 32'b00000000000000000000000000000000;
			W5  <= 32'b00000000000000000000000000000000;
			W6  <= 32'b00000000000000000000000000000000;
			W7  <= 32'b00000000000000000000000000000000;
			W8  <= 32'b00000000000000000000000000000000;
			W9  <= 32'b00000000000000000000000000000000;
			W10 <= 32'b00000000000000000000000000000000;
			W11 <= 32'b00000000000000000000000000000000;
			W12 <= 32'b00000000000000000000000000000000;
			W13 <= 32'b00000000000000000000000000000000;
			W14 <= 32'b00000000000000000000000000000000;
			Wt  <= 32'b00000000000000000000000000000000;
			
			A <= 32'b00000000000000000000000000000000;
			B <= 32'b00000000000000000000000000000000;
			C <= 32'b00000000000000000000000000000000;
			D <= 32'b00000000000000000000000000000000;
			E <= 32'b00000000000000000000000000000000;
			
			H0 <= 32'b00000000000000000000000000000000;
			H1 <= 32'b00000000000000000000000000000000;
			H2 <= 32'b00000000000000000000000000000000;
			H3 <= 32'b00000000000000000000000000000000;
			H4 <= 32'b00000000000000000000000000000000;

		end
		else
		begin
			case (round)
			
			7'b0000000:
				begin
					if (cmd[1])
					begin
						W0 <= text_i;
						Wt <= text_i;
						busy <= 1'b1;
						round <= round_plus_1;
                                               	
						case (cmd[2])
							1'b0:	// sha-1 first message
								begin
									A <= `SHA1_H0;
									B <= `SHA1_H1;
									C <= `SHA1_H2;
									D <= `SHA1_H3;
									E <= `SHA1_H4;
									
									H0 <= `SHA1_H0;
									H1 <= `SHA1_H1;
									H2 <= `SHA1_H2;
									H3 <= `SHA1_H3;
									H4 <= `SHA1_H4;
								end
							1'b1:	// sha-1 internal message
								begin
									H0 <= A;
									H1 <= B;
									H2 <= C;
									H3 <= D;
									H4 <= E;
								end
						endcase
					end
					else
					begin	// IDLE
						round <= 7'b0000000;
					end
				end
			7'b0000001:
				begin
					W1 <= text_i;
					Wt <= text_i;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0000010:
				begin
					W2 <= text_i;
					Wt <= text_i;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0000011:
				begin
					W3 <= text_i;
					Wt <= text_i;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0000100:
				begin
					W4 <= text_i;
					Wt <= text_i;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0000101:
				begin
					W5 <= text_i;
					Wt <= text_i;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0000110:
				begin
					W6 <= text_i;
					Wt <= text_i;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0000111:
				begin
					W7 <= text_i;
					Wt <= text_i;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0001000:
				begin
					W8 <= text_i;
					Wt <= text_i;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0001001:
				begin
					W9 <= text_i;
					Wt <= text_i;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0001010:
				begin
					W10 <= text_i;
					Wt <= text_i;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0001011:
				begin
					W11 <= text_i;
					Wt <= text_i;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0001100:
				begin
					W12 <= text_i;
					Wt <= text_i;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0001101:
				begin
					W13 <= text_i;
					Wt <= text_i;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0001110:
				begin
					W14 <= text_i;
					Wt <= text_i;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0001111:
				begin
					Wt <= text_i;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0010000:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0010001:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0010010:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0010011:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0010100:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0010101:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0010110:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0010111:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0011000:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0011001:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0011010:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0011011:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0011100:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0011101:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0011110:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0011111:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0100000:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0100001:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0100010:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0100011:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0100100:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0100101:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0100110:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0100111:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0101000:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0101001:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0101010:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0101011:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0101100:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0101101:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0101110:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0101111:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0110000:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0110001:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0110010:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0110011:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0110100:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0110101:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0110110:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0110111:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0111000:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0111001:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0111010:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0111011:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0111100:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0111101:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0111110:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b0111111:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b1000000:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b1000001:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b1000010:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b1000011:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b1000100:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b1000101:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b1000110:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b1000111:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b1001000:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b1001001:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b1001010:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b1001011:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b1001100:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b1001101:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b1001110:begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b1001111:
				begin
					W0  <= W1;
					W1  <= W2;
					W2  <= W3;
					W3  <= W4;
					W4  <= W5;
					W5  <= W6;
					W6  <= W7;
					W7  <= W8;
					W8  <= W9;
					W9  <= W10;
					W10 <= W11;
					W11 <= W12;
					W12 <= W13;
					W13 <= W14;
					W14 <= Wt;
					Wt  <= next_Wt;
					
					E <= D;
					D <= C;
					C <= next_C;
					B <= A;
					A <= next_A;
						
					round <= round_plus_1;
				end
			7'b1010000:
				begin
					A <= next_A + H0;
					B <= A + H1;
					C <= next_C + H2;
					D <= C + H3;
					E <= D + H4;
					round <= 7'b0000000;
					busy <= 1'b0;
				end
			default:
				begin
					round <= 7'b0000000;
					busy <= 1'b0;
				end
			endcase
		end	
	end 
	
	
	//------------------------------------------------------------------	
	// Kt generator
	//------------------------------------------------------------------	
	always @ (posedge clk_i)
	begin
		if (rst_i)
		begin
			Kt <= 32'b00000000000000000000000000000000;
		end
		else
		begin
			if (round < 7'b0100000)
				Kt <= `SHA1_K0;
			else
			if (round < 7'b1010000)
				Kt <= `SHA1_K1;
			else
			if (round < 7'b1111100)
				Kt <= `SHA1_K2;
			else
				Kt <= `SHA1_K3;
		end
	end

	//------------------------------------------------------------------	
	// read result 
	//------------------------------------------------------------------	
	always @ (posedge clk_i)
	begin
		if (rst_i)
		begin
			text_o <= 32'b00000000000000000000000000000000;
			read_counter <= 3'b000;
		end
		else
		begin
			if (cmd[0])
			begin
				read_counter <= 3'b100;	// sha-1 	160/32=5
			end
			else
			begin
			if (~busy)
			begin
				case (read_counter)
					3'b100:	text_o <= SHA1_result[5*32-1:4*32];
					3'b011:	text_o <= SHA1_result[4*32-1:3*32];
					3'b010:	text_o <= SHA1_result[3*32-1:2*32];
					3'b001:	text_o <= SHA1_result[2*32-1:1*32];
					3'b000:	text_o <= SHA1_result[1*32-1:0*32];
					default:text_o <= 3'b000;
				endcase
				if (|read_counter)
					read_counter <= read_counter - 7'b0000001;
			end
			else
			begin
				text_o <= 32'b00000000000000000000000000000000;
			end
			end
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