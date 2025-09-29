from vtr_arch_builder import Arch, Model, Switch, Segment, Tile, SubTile, Power_Estimate
from vtr_arch_builder import ComplexBlock, Primitive, Mode
import networkx as nx
import matplotlib.pyplot as plt


#MARK: Example Usage

############################################


arch = Arch()

############ MODELS ###################

io_model = Model("io")
io_model.add_input_ports(name="outpad")
io_model.add_output_ports(name="inpad")
arch.add_model(io_model)

sprams = []
for spram_name in ["spram512x40", "spram1024x20", "spram2048x10", "spram"]:
    spram = Model(spram_name)
    spram.add_input_ports(name="we", clock="clk", comb_ports=["dataout"])
    spram.add_input_ports(name="addr", clock="clk", comb_ports=["dataout"])
    spram.add_input_ports(name="datain", clock="clk", comb_ports=["dataout"])
    spram.add_input_ports(name="clk", is_clock=True)
    spram.add_output_ports(name="dataout", clock="clk")
    arch.add_model(spram)
    sprams.append(spram)

mults = []
for mult_name in ["two_mult_18x19", "one_mult_27x27"]:
    mult = Model(mult_name)
    mult.add_input_ports(name="A", comb_ports=["Y"])
    mult.add_input_ports(name="B", comb_ports=["Y"])
    mult.add_output_ports(name="Y")
    arch.add_model(mult)
    mults.append(mult)

dsp = Model("dsp")
dsp.add_input_ports(name="I")
dsp.add_output_ports(name="result")
arch.add_model(dsp)

############## DEVICE ##################

arch.sizing(nmos_w="8926", pmos_w="16067")
arch.tile_area("0")
arch.switch_block_type(type="custom", fs="")

arch.xchannel_dist("uniform", "1.000000")
arch.ychannel_dist("uniform", "1.000000")

########### SWITCH ##################

switch1 = Switch(type="mux", name="L4_driver", R="0.0", Cin="0.0", Cout="0.0", Tdel="185.8258e-12", mux_trans_size="6482996805637553", buf_size="744014602932605")
arch.add_switch(switch1)



############ SEGMENT #################

l4Segment = Segment(name="L4", freq="280", length="4", type="unidir", Rmetal="0.0", Cmetal="0.0")
l4Segment.switch_block_pattern([1, 1, 1, 1, 1])
l4Segment.connection_block_pattern([1, 1, 1, 1])
l4Segment.mux(switch1)

arch.add_segment(l4Segment)

########### PBs ##############

io_pb = ComplexBlock(name="io")
io_pb.add_input(name="outpad", num_pins=1)
io_pb.add_output(name="inpad", num_pins=1)
phys_mode = Mode(name="physical", parent=io_pb, disable_packing=True)
iopad_prim = Primitive(name="iopad", type="custom", blif_model=io_model, num_pb=1)
phys_mode.add_block(iopad_prim)
phys_mode.add_direct_connection(["io.outpad"], ["iopad.outpad"], delay_constant=("io.outpad", "iopad.outpad", [26.2256e-12]))
phys_mode.add_direct_connection(["iopad.inpad"], ["io.inpad"], delay_constant=("iopad.inpad", "io.inpad", [79.8279e-12]))
io_pb.add_mode(phys_mode)
in_mode = Mode(name="inpad", parent=io_pb)
inpad_prim = Primitive(name="inpad", type="input")
in_mode.add_block(inpad_prim)
in_mode.add_direct_connection(["inpad.input"], ["io.inpad"], delay_constant=("inpad.input", "io.inpad", [79.8279e-12]))
io_pb.add_mode(in_mode)
out_mode = Mode(name="outpad", parent=io_pb)
outpad_prim = Primitive(name="outpad", type="output")
out_mode.add_block(outpad_prim)
out_mode.add_direct_connection(["io.outpad"], ["outpad.output"], delay_constant=("io.outpad", "outpad.output", [26.2256e-12]))
io_pb.add_mode(out_mode)
io_pb.set_power_estimate(Power_Estimate("ignore"))
arch.add_pb(io_pb)


lut6 = Primitive(name="lut6", type="lut6", num_pb=1)
ff = Primitive(name="ff", type="ff", num_pb=1)

clb = ComplexBlock(name="clb")
clb.add_input(name="input", num_pins=40, equivalence="full")
clb.add_output(name="output", num_pins=10)
clb.add_clock(name="clock", num_pins=1)

fle = ComplexBlock(name="fle", num_pb=10)
fle.add_input(name="input", num_pins=6)
fle.add_output(name="output", num_pins=1)
fle.add_clock(name="clock", num_pins=1)

ble6 = ComplexBlock(name="ble6", num_pb=1)
ble6.add_input(name="input", num_pins=6)
ble6.add_output(name="output", num_pins=1)
ble6.add_clock(name="clock", num_pins=1)

ble6.add_block(lut6)
ble6.add_block(ff)
ble6.add_direct_connection(inputs=["ble6.input"], outputs=["lut6.input"])
ble6.add_direct_connection(inputs=["lut6.output"], outputs=["ff.D"])
ble6.add_direct_connection(inputs=["ble6.clock"], outputs=["ff.clock"])
ble6.add_mux_connection(inputs=["ff.Q", "lut6.output"], outputs="ble6.output")

n1_lut6 = Mode(name="n1_lut6", parent=fle)
n1_lut6.add_block(ble6)
n1_lut6.add_direct_connection(inputs=["fle.input"], outputs=["ble6.input"])
n1_lut6.add_direct_connection(inputs=["ble6.output"], outputs=["fle.output[0]"])
n1_lut6.add_direct_connection(inputs=["fle.clock"], outputs=["ble6.clock"])

fle.add_mode(n1_lut6)

clb.add_block(fle)
clb.add_complete_connection(inputs=["clb.input", "fle[9:0].output"], outputs=["fle[9:0].input"])
clb.add_complete_connection(inputs=["clb.clock"], outputs=["fle[9:0].clock"])
clb.add_direct_connection(inputs=["fle[9:0].output"], outputs=["clb.output"])

arch.add_pb(clb)

############# TILES ##############
io_tile = Tile(name="io", area=0)
io_subtile = SubTile(name="io", capacity=8)
io_subtile.add_site(io_pb)

############ PRINT ###################

arch.save("my_arch.xml")
print(arch.to_string()) 

nx.draw(ble6._graph, with_labels=True)
plt.savefig("graph.png")

        