from vtr_arch_builder import Arch, Model, Switch, Segment, Tile, SubTile
from vtr_arch_builder import ComplexBlock, Primitive, Mode


#MARK: Example Usage

############################################


arch = Arch()

############ MODELS ###################

io_model = Model("io")
io_model.add_input_ports(name="outpad")
io_model.add_output_ports(name="inpad")

arch.add_model(io_model)

arch.add_model(Model("spram",  "true"))

############# TILES ##############

tile = Tile(name = "clb", area = "53894")
subTile = SubTile(name = "clb")
subTile.add_input(name = "I", num_pins="1")

tile.add_sub_tile(subTile)

arch.add_tile(tile)

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

########### GRAPH TEST ##############


clb = ComplexBlock(name="clb")
clb.add_input(name="I", num_pins=40,equivalence="full")
clb.add_output(name="O", num_pins=10)
clb.add_clock(name="clk", num_pins=1)

fle = ComplexBlock(name="fle", num_pb=10)
fle.add_input(name="in", num_pins=6)
fle.add_output(name="out", num_pins=1)
fle.add_clock(name="clk", num_pins=1)

n1_lut6 = Mode(name="n1_lut6")
ble6 = ComplexBlock(name="ble6", num_pb=1)
ble6.add_input(name="in", num_pins=6)
ble6.add_output(name="out", num_pins=1) 
ble6.add_clock(name="clk", num_pins=1)
lut6 = Primitive(name="lut6", type="lut6")
ff = Primitive(name="ff", type="ff")
ble6.add_block(lut6)
ble6.add_block(ff)

ble6.add_direct_connection([ble6.pins("in")], [lut6.pins("in")])
ble6.add_direct_connection([lut6.pins("out")], [ff.pins("D")])
ble6.add_direct_connection([ble6.pins("clk")], [ff.pins("clock")])
ble6.add_mux_connection([ff.pins("Q"), lut6.pins("out")], ble6.pins("out"))

n1_lut6.add_block(ble6)

fle.add_mode(n1_lut6)

n1_lut6.add_direct_connection([fle.pins("in")], [ble6.pins("in")])

clb.add_block(fle)

arch.add_pb(clb)

#lz TODO Should connections take place inside mode actually?
#lz TODO actually I was going to change the clb logic to be mode and the mode to be clb and that way everything works out and a clb cant have modes and blocks

# nx.draw(io.get_graph(), with_labels=True)
# plt.savefig("testgraph.png")

############ PRINT ###################

arch.save("my_arch.xml")
print(arch.to_string()[:4000]) 

        