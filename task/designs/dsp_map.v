

//27x27 multiplier
module mult_27x27 (
  input [0:26] A,
  input [0:26] B,
  output [0:53] Y
);
  parameter A_SIGNED = 0;
  parameter B_SIGNED = 0;
  parameter A_WIDTH = 0;
  parameter B_WIDTH = 0;
  parameter Y_WIDTH = 0;

  one_mult_27x27 #() _TECHMAP_REPLACE_ (
    .A    (A),
    .B    (B),
    .Y    (Y));

endmodule

//18x19 multiplier
module mult_18x19 (
  input [0:17] A,
  input [0:18] B,
  output [0:36] Y
);
  parameter A_SIGNED = 0;
  parameter B_SIGNED = 0;
  parameter A_WIDTH = 0;
  parameter B_WIDTH = 0;
  parameter Y_WIDTH = 0;

  two_mult_18x19 #( ) _TECHMAP_REPLACE_ (
    .A    (A),
    .B    (B),
    .Y    (Y) );

endmodule

