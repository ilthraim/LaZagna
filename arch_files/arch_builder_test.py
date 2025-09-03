from vtr_arch_builder import Arch

arch = (
    Arch()
      # 1) Models
      .models()
        .model("io").input_port("outpad").output_port("inpad").up()
      .done()

      # 2) Tiles
      .tiles()
        .tile("io", area=1).sub_tile("io", capacity=8).equivalent_site("io").up().up()
        .tile("clb", area=1)
          .input("I", num_pins=10).output("O", num_pins=4).clock("clk", num_pins=1)
          .fc(default_in_type="fractional", default_in_val="0.15",
              default_out_type="fractional", default_out_val="0.10")
          .sub_tile("clb", capacity=4).equivalent_site("clb").up()
        .up()
      .done()

      # 3) Layout
      .layout().fixed("grid141", width=141, height=141)
        .perimeter(type="io", priority=100)
        .corners(type="EMPTY", priority=101)
        .fill(type="clb", priority=10)
        .done()
      .done()

      # 4) Device
      .device()
        .sizing(R_minW_nmos=8926, R_minW_pmos=16067)
        .area(grid_logic_tile_area=0)
        .chan_width_distr(
          x_distr="uniform", x_peak=1.0,
          y_distr="delta", y_peak=2.0, y_xpeak=0.5, y_dc=1.0
        )
        .switch_block(type="wilton", fs=3)
        .connection_block(input_switch_name="ipin_cblock")
        .default_fc(in_type="frac", in_val="0.1", out_type="frac", out_val="0.2")
        .done()

      # 5) Switches / Segments
      .switches().switch(name="L4_driver", type="tristate", R=0.0, Cin=0.0, Cout=0.0, Tdel="185e-12").done()
      .segments().segment(
          "L4", freq=1.0, length=4, type="unidir", Rmetal=100, Cmetal=2.5e-15,
          sb_pattern="1 1 1 1 1", cb_pattern="1 1 1 1", mux_name="L4_driver"
      ).done()

      # 6) Complex blocks: a tiny CLB with a LUT+FF mode and simple interconnect
      .complexblocks()
        .pb_type("clb")
          .input("I", 10).output("O", 4).clock("clk")
          .mode("normal")
            .pb_type("lut4", blif_model=".names", num_pb="1").input("in[0:3]").output("out[0:0]").up()
            .pb_type("ff", blif_model=".latch", num_pb="1").input("D").output("Q").clock("clk")
              .T_setup(port="D", clock="clk", value="50e-12")
              .T_hold(port="D", clock="clk", value="0")
              .T_clock_to_Q(port="Q", clock="clk", max="80e-12", min="50e-12").up()
            .interconnect()
              .complete("clb.I->lut.in",  input="clb.I",        output="lut4.in")
              .direct  ("lut.out->ff.D",  input="lut4.out",     output="ff.D")
              .direct  ("ff.Q->clb.O",    input="ff.Q",         output="clb.O")
              .delay_constant(in_port="lut4.out", out_port="ff.D", max="20e-12", min="10e-12")
              .up()
            .up()
          .up()
        .done()
)

# Write to disk
arch.save("my_arch.xml")
print(arch.to_string()[:4000])  # preview
