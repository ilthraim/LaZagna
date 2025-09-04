from __future__ import annotations
import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import Optional, Iterable, Dict, Any, List

class _Node:
    def __init__(self):
        self.root = ET.Element("")

    def to_elem(self) -> ET.Element:
        return self.root


class Arch(_Node):
    def __init__(self):
        self.root = ET.Element("architecture")
        self._models = ET.SubElement(self.root, "models")
        self._tiles = ET.SubElement(self.root, "tiles")
        self._layout = ET.SubElement(self.root, "layout")
        self._device = ET.SubElement(self.root, "device")
        self._switchlist = ET.SubElement(self.root, "switchlist")
        self._segmentlist = ET.SubElement(self.root, "segmentlist")
        self._complexblocklist = ET.SubElement(self.root, "complexblocklist")

        self.switches: dict[str, Switch] = {}

    def add_model(self, model: Model):
        #ET.append(self._models, model.to_elem())
        self._models.append(model.to_elem())

    def add_tile(self, tile: Tile):
        self._tiles.append(tile.to_elem())

    def add_switch(self, switch: Switch):
        self.switches[switch.name] = switch
        self._switchlist.append(switch.to_elem())

    def add_segment(self, segment: Segment):
        self._segmentlist.append(segment.to_elem())

    def to_string(self, indent: str = "  ") -> str:
        rough = ET.tostring(self.root, encoding="utf-8")
        return minidom.parseString(rough).toprettyxml(indent=indent)

    def save(self, filename: str):
        with open(filename, "w", encoding="utf-8") as f:
            f.write(self.to_string())

    def sizing(self, nmos_w: str, pmos_w: str):
        ET.SubElement(self._device, "sizing", {"R_minW_nmos": nmos_w, "R_minW_pmos": pmos_w})

    def tile_area(self, tile_area: str):
        ET.SubElement(self._device, "area", {"grid_logic_tile_area": tile_area})

    def switch_block_type(self, type: str, fs: str):
        if type not in ["wilton", "subset", "universal", "custom"]:
            raise ValueError("type must be wilton, subset, universal, or custom")
        
        if type == "custom":
            ET.SubElement(self._device, "switch_block", {"type": type})
        else:
            ET.SubElement(self._device, "switch_block", {"type": type, "fs": fs})

    def xchannel_dist(self, distr: str, peak: str, width: Optional[str] = None, xpeak: Optional[str] = None, dc: Optional[str] = None):
        if distr not in ["gaussian", "uniform", "pulse", "delta"]:
            raise ValueError("Channel distribution must be gaussian, uniform, pulse, or delta")

        if not hasattr(self, "_cwd"):
            self._cwd = ET.SubElement(self.root, "chan_width_distr")

        elems = {"distr": distr, "peak": peak}

        if distr in ["pulse", "gaussian"]:
            if width == None:
                raise ValueError("Width must be provided for pulse and gaussian distributions")
            else:
                elems["width"] = width

        if distr in ["pulse", "gaussian", "delta"]:
            if xpeak == None:
                raise ValueError("Xpeak must be provided for pulse, gaussian, and delta distributions")
            else:
                elems["xpeak"] = xpeak

            if dc == None:
                raise ValueError("Dc must be provided for pulse, gaussian, and delta distributions")
            else:
                elems["dc"] = dc
            
        ET.SubElement(self._cwd, "x", elems)

    def ychannel_dist(self, distr: str, peak: str, width: Optional[str] = None, xpeak: Optional[str] = None, dc: Optional[str] = None):
        if distr not in ["gaussian", "uniform", "pulse", "delta"]:
            raise ValueError("Channel distribution must be gaussian, uniform, pulse, or delta")

        if not hasattr(self, "_cwd"):
            self._cwd = ET.SubElement(self.root, "chan_width_distr")

        elems = {"distr": distr, "peak": peak}

        if distr in ["pulse", "gaussian"]:
            if width == None:
                raise ValueError("Width must be provided for pulse and gaussian distributions")
            else:
                elems["width"] = width

        if distr in ["pulse", "gaussian", "delta"]:
            if xpeak == None:
                raise ValueError("Xpeak must be provided for pulse, gaussian, and delta distributions")
            else:
                elems["xpeak"] = xpeak

            if dc == None:
                raise ValueError("Dc must be provided for pulse, gaussian, and delta distributions")
            else:
                elems["dc"] = dc
            
        ET.SubElement(self._cwd, "y", elems)

    def fc_type(self, in_type: str, in_val: str, out_type: str, out_val: str):
        if in_type not in ["frac", "abs"]:
            raise ValueError("in_type must be frac or abs")
        if out_type not in ["frac", "abs"]:
            raise ValueError("out_type must be frac or abs")
        ET.SubElement(self._device, "default_fc", {"in_type": in_type, "in_val": in_val, "out_type": out_type, "out_val": out_val})


class Model(_Node):
    def __init__(self, name: str, prune: str = "false"):
        self.root = ET.Element("model", {"name": name, "never_prune": prune})
        self._inputs = ET.SubElement(self.root, "input_ports")
        self._outputs = ET.SubElement(self.root, "output_ports")

    #THERE HAS TO BE A BETTER WAY

    def add_input_port(self, name: str, is_clock: str = "0", clock: Optional[str] = None, comb_ports: Optional[tuple] = None):
        elems = {"name": name, "is_clock": is_clock}
        if clock != None:
            elems["clock"] = clock
        if comb_ports != None:
            elems["combinational_sink_ports"] = " ".join(comb_ports)

        ET.SubElement(self._inputs, "port", elems)

    def add_output_port(self, name: str, is_clock: str = "0", clock: Optional[str] = None, comb_ports: Optional[tuple] = None):
        elems = {"name": name, "is_clock": is_clock}
        if clock != None:
            elems["clock"] = clock
        if comb_ports != None:
            elems["combinational_sink_ports"] = " ".join(comb_ports)

        ET.SubElement(self._outputs, "port", elems)
    
class Tile(_Node):
    def __init__(self, name: str, width: str = "1", height: str = "1", area: Optional[str] = None):
        if area != None:
            self.root = ET.Element("tile", {"name": name, "width": width, "height": height, "area":area})
        else:
            self.root = ET.Element("tile", {"name": name, "width": width, "height": height})

    def add_sub_tile(self, subTile: SubTile):
        self.root.append(subTile.to_elem())

    
class SubTile(_Node):
    def __init__(self, name: str, capacity: str = "1"):
        self.root = ET.Element("sub_tile", {"name": name, "capacity": capacity})

    #lz I bet we can get inputs and outputs from the equivalent sites

    def add_input(self, name: str, num_pins: str, equivalent: str = "none", is_global: Optional[str] = None):
        if is_global != None:
            ET.SubElement(self.root, "input", {"name": name, "num_pins": num_pins, "equivalent": equivalent, "is_non_clock_global": is_global})
        else:
            ET.SubElement(self.root, "input", {"name": name, "num_pins": num_pins, "equivalent": equivalent})

    def add_output(self, name: str, num_pins: str, equivalent: str = "none"):
        ET.SubElement(self.root, "output", {"name": name, "num_pins": num_pins, "equivalent": equivalent})

    def add_clock(self, name: str, num_pins: str, equivalent: str = "none"):
        ET.SubElement(self.root, "clock", {"name": name, "num_pins": num_pins, "equivalent": equivalent})

    #lz TODO add equivalent sites - should be able to snag em from the complex blocks list

    def set_fc(self, in_type: str, in_val: str, out_type: str, out_val: str):
        ET.SubElement(self.root, "fc", {"in_type": in_type, "in_val": in_val, "out_type": out_type, "out_val":out_val})

    #lz TODO add pin locations - come from block list too?

    #lz TODO - connection_block input switch is going to have to come from switchlist I fear

class Switch(_Node):

    def __init__(self, 
                    type: str,
                    name: str,
                    R: str,
                    Cin: str,
                    Cout: str,
                    Cinternal: Optional[str] = None,
                    Tdel: Optional[str] = None, #lz TODO this needs to be required if there is no overall Tdel tag
                    buf_size: Optional[str] = "auto",
                    mux_trans_size: Optional[str] = None,
                    power_buf_size: Optional[str] = None):
        
        if type not in ["mux", "tristate", "pass_gate", "short", "buffer"]:
            raise ValueError("type must be mux, tristate, pass_gate, short, or buffer")
        
        if (type in ["mux", "tristate", "buffer"]) and (buf_size == None):
            raise ValueError("buf_size must be defined for isolating switch types")
        
        if (type != "mux") and (mux_trans_size != None):
            raise ValueError("mux_trans_size is only valid for mux type switches")

        elems = {"type": type, "name": name, "R": R, "Cin": Cin, "Cout": Cout}
        self.name = name
        self.type = type

        if Cinternal != None:
            elems["Cinternal"] = Cinternal
        if Tdel != None:
            elems["Tdel"] = Tdel
        if buf_size != None:
            elems["buf_size"] = buf_size
        if mux_trans_size != None:
            elems["mux_trans_size"] = mux_trans_size
        if power_buf_size != None:
            elems["power_buf_size"] = power_buf_size

        self.root = ET.Element("switch", elems)

    def add_tdel(self, num_inputs: str, delay: str):
        ET.SubElement(self.root, "Tdel", {"num_inputs": num_inputs, "delay": delay})

class Segment(_Node):
    def __init__(self,
                 arch: Arch,
                 name: str,
                 length: str,
                 freq: str,
                 Rmetal: str,
                 Cmetal: str,
                 type: str,
                 axis: Optional[str] = None,
                 res_type: Optional[str] = None): #lz TODO link res_type to specific clock nets?
        if type not in ["bidir", "unidir"]:
            raise ValueError("Type must be either bidir or unidir")
        if length.isdigit():
            self.length = int(length)
        elif length == "longline":
            self.length = 0
            if (type != "bidir"):
                raise ValueError("longline is only supported for bidir routing")
        else:
            raise ValueError("length must either be an integer or the keyword longline")

        elems = {"name": name, "length": length, "freq": freq, "Rmetal": Rmetal, "Cmetal": Cmetal, "type": type}

        if axis != None:
            elems["axis"] = axis
        if res_type != None:
            elems["res_type"] = res_type

        self.root = ET.Element("segment", elems)
        self.arch = arch

    def switch_block_pattern(self, pattern: List[int]):
        if self.length == 0:
            raise ValueError("Cannot define switch block pattern with longline length")
        if len(pattern) != self.length + 1:
            raise ValueError("Switch block pattern must have length of segment + 1")
        if not all(x in (0, 1) for x in pattern):
            raise ValueError("Switch block pattern can only contain 1 and 0")
        
        ET.SubElement(self.root, "sb", {"type": "pattern"}).text = " ".join(str(x) for x in pattern)

    def connection_block_pattern(self, pattern: List[int]):
        if self.length == 0:
            raise ValueError("Cannot define connection block pattern with longline length")
        if len(pattern) != self.length:
            raise ValueError("Connection block pattern must have length of segment")
        if not all(x in (0, 1) for x in pattern):
            raise ValueError("Connection block pattern can only contain 1 and 0")
        
        ET.SubElement(self.root, "cb", {"type": "pattern"}).text = " ".join(str(x) for x in pattern)

    def mux(self, name: str):
        if (not name in arch.switches) or (arch.switches[name].type != "mux"):
            raise ValueError("Mux must be defined in the switchlist before use in segmentlist")
        
        ET.SubElement(self.root, "mux", {"name": name})


############################################


arch = Arch()

############ MODELS ###################

ioModel = Model("io")
ioModel.add_input_port(name="we", clock="0")
ioModel.add_output_port(name="addr", is_clock="1", clock=None, comb_ports=("test", "test2"))

arch.add_model(ioModel)

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

#lz TODO should creating segments be a function of the specific architecture?
#lz TODO could do mux checking in arch.add_segment()

l4Segment = Segment(arch=arch, name="L4", freq="280", length="4", type="unidir", Rmetal="0.0", Cmetal="0.0")
l4Segment.switch_block_pattern([1, 1, 1, 1, 1])
l4Segment.connection_block_pattern([1, 1, 1, 1])
l4Segment.mux(name="L4_driver")

arch.add_segment(l4Segment)

############ PRINT ###################

arch.save("my_arch2.xml")
print(arch.to_string()[:4000]) 

        