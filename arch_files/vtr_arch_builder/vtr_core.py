from __future__ import annotations
import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import TYPE_CHECKING, Optional, Dict, List, Literal
import networkx as nx

from .vtr_utils import _Node
if TYPE_CHECKING:
    from .vtr_blocks import ComplexBlock

#MARK: Arch
class Arch(_Node):
    def __init__(self):
        self._root = ET.Element("architecture")
        self._models = ET.SubElement(self._root, "models")
        self._tiles = ET.SubElement(self._root, "tiles")
        self._layout = ET.SubElement(self._root, "layout")
        self._device = ET.SubElement(self._root, "device")
        self._switchlist = ET.SubElement(self._root, "switchlist")
        self._segmentlist = ET.SubElement(self._root, "segmentlist")
        self._complexblocklist = ET.SubElement(self._root, "complexblocklist")

        self.switches: dict[str, Switch] = {}
        self.segments: dict[str, Segment] = {}

    def add_model(self, model: Model):
        #ET.append(self._models, model.to_elem())
        self._models.append(model.to_elem())

    def add_tile(self, tile: Tile):
        self._tiles.append(tile.to_elem())

    def add_switch(self, switch: Switch):
        self.switches[switch.name] = switch
        self._switchlist.append(switch.to_elem())

    #lz TODO do checking for bidirectional switches
    def add_segment(self, segment: Segment):
        if hasattr(segment, "switch_mux") and self.switches[segment.switch_mux.name] == None:
            raise ValueError("Mux used in segment must be present in switchlist")
        if hasattr(segment, "switch_mux_inc") and self.switches[segment.switch_mux_inc.name] == None:
            raise ValueError("Mux used in segment must be present in switchlist")
        if hasattr(segment, "switch_mux_dec") and self.switches[segment.switch_mux_dec.name] == None:
            raise ValueError("Mux used in segment must be present in switchlist")
        if hasattr(segment, "switch_mux_inter_die") and self.switches[segment.switch_mux_inter_die.name] == None:
            raise ValueError("Mux used in segment must be present in switchlist")

        self.segments[segment.name] = segment
        self._segmentlist.append(segment.to_elem())

    def add_pb(self, pb: ComplexBlock):
        self._complexblocklist.append(pb.to_elem())

    def to_string(self, indent: str = "  ") -> str:
        rough = ET.tostring(self._root, encoding="utf-8")
        return minidom.parseString(rough).toprettyxml(indent=indent)

    def save(self, filename: str):
        with open(filename, "w", encoding="utf-8") as f:
            f.write(self.to_string())

    def sizing(self, nmos_w: str, pmos_w: str):
        ET.SubElement(self._device, "sizing", {"R_minW_nmos": nmos_w, "R_minW_pmos": pmos_w})

    def tile_area(self, tile_area: str):
        ET.SubElement(self._device, "area", {"grid_logic_tile_area": tile_area})

    def switch_block_type(self, type: Literal["wilton", "subset", "univeral", "custom"], fs: str):
        
        if type == "custom":
            ET.SubElement(self._device, "switch_block", {"type": type})
        else:
            ET.SubElement(self._device, "switch_block", {"type": type, "fs": fs})

    def xchannel_dist(self, distr: str, peak: str, width: Optional[str] = None, xpeak: Optional[str] = None, dc: Optional[str] = None):
        if distr not in ["gaussian", "uniform", "pulse", "delta"]:
            raise ValueError("Channel distribution must be gaussian, uniform, pulse, or delta")

        if not hasattr(self, "_cwd"):
            self._cwd = ET.SubElement(self._root, "chan_width_distr")

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
            self._cwd = ET.SubElement(self._root, "chan_width_distr")

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

    #lz TODO verify there cannot be auto layout and fixed layout
    def auto_layout(self, aspect_ratio: Optional[str] = None):
        if self._layout.find("auto_layout") != None:
            raise ValueError("Cannot have multiple auto layouts defined")
        if self._layout.find("fixed_layout") != None:
            raise ValueError("Cannot have fixed and auto layouts")
        
        if(aspect_ratio != None):
            ET.SubElement(self._layout, "auto_layout", {"aspect_ratio": aspect_ratio})
        else:
            ET.SubElement(self._layout, "auto_layout")

    def fixed_layout(self, name: str, width: str, height: str):
        if self._layout.find("auto_layout") != None:
            raise ValueError("Cannot have auto and fixed layouts")
        
        ET.SubElement(self._layout, "fixed_layout", {"name": name, "width": width, "height": height})

#MARK: Model
class Model(_Node):
    def __init__(self, name: str, prune: str = "false"):
        self.name = name
        self._root = ET.Element("model", {"name": name, "never_prune": prune})
        self.inputs: Dict[str, int] = {}
        self.outputs: Dict[str, int] = {}
        self.clocks: Dict[str, int] = {}
        self._inputs = ET.SubElement(self._root, "input_ports")
        self._outputs = ET.SubElement(self._root, "output_ports")

    def add_input_ports(self, name: str, num_ports: int = 1, is_clock: bool = False, clock: Optional[str] = None, comb_ports: Optional[tuple] = None):
        elems = {"name": name, "is_clock": "1" if is_clock else "0"}
        if clock != None:
            elems["clock"] = clock
        if comb_ports != None:
            elems["combinational_sink_ports"] = " ".join(comb_ports)

        if is_clock:
            self.clocks[name] = num_ports
        else:
            self.inputs[name] = num_ports

        ET.SubElement(self._inputs, "port", elems)

    def add_output_ports(self, name: str, num_ports: int = 1, clock: Optional[str] = None):
        elems = {"name": name}
        if clock != None:
            elems["clock"] = clock

        self.outputs[name] = num_ports

        ET.SubElement(self._outputs, "port", elems)


#MARK: Tile    
class Tile(_Node):
    def __init__(self, name: str, width: str = "1", height: str = "1", area: Optional[str] = None):
        if area != None:
            self._root = ET.Element("tile", {"name": name, "width": width, "height": height, "area":area})
        else:
            self._root = ET.Element("tile", {"name": name, "width": width, "height": height})

    def add_sub_tile(self, subTile: SubTile):
        self._root.append(subTile.to_elem())

#MARK: SubTile
class SubTile(_Node):
    def __init__(self, name: str, capacity: str = "1"):
        self._root = ET.Element("sub_tile", {"name": name, "capacity": capacity})
        self._equivalent_sites = ET.SubElement(self._root, "equivalent_sites")
        self._pin_locations = ET.SubElement(self._root, "pin_locations")
        self._graph = nx.Graph()

    #lz TODO add inputs and outputs to the graph and connect them

    def add_input(self, name: str, num_pins: int, equivalent: str = "none", is_global: bool = False):
        ET.SubElement(self._root, "input", {"name": name, "num_pins": str(num_pins), "equivalent": equivalent, "is_non_clock_global": str(is_global)})

    def add_output(self, name: str, num_pins: int, equivalent: str = "none"):
        ET.SubElement(self._root, "output", {"name": name, "num_pins": str(num_pins), "equivalent": equivalent})

    def add_clock(self, name: str, num_pins: int, equivalent: str = "none"):
        ET.SubElement(self._root, "clock", {"name": name, "num_pins": str(num_pins), "equivalent": equivalent})

    #lz TODO add custom mapping
    # def add_site(self, cb: ComplexBlock, pin_mapping: Literal["direct", "custom"] = "direct"):
    #     if not cb._is_top:
    #         raise ValueError("Only top level complex blocks can be added as equivalent sites")
    #     ET.SubElement(self._equivalent_sites, "site", {"name": cb.name, "pin_mapping": pin_mapping})

    #     if pin_mapping == "direct":
    #         self._graph = nx.compose(self._graph, cb.get_graph())
    #         for name, elems in cb._inputs.items():
    #             self.add_input(name=name, num_pins=elems[0], equivalent=elems[1], is_global=elems[2])

    #         for name, elems in cb._outputs.items():
    #             self.add_output(name=name, num_pins=elems[0], equivalent=elems[1])

    #         for name, elems in cb._clocks.items():
    #             self.add_clock(name=name, num_pins=elems[0], equivalent=elems[1])

    # def add_direct_connection(self, inputs: _PinList, outputs: _PinList):
    #     if len(inputs) != len(outputs):
    #         raise ValueError("Number of input pins must match number of output pins for direct connection")
        
    #     for i in range(len(inputs)):
    #         # self._graph.add_edge(inputs[i].node_name, outputs[i].node_name)
    #         ET.SubElement(self._root, "direct_connection", {"input": inputs[i].node_name, "output": outputs[i].node_name})

    def set_fc(self, in_type: str, in_val: str, out_type: str, out_val: str):
        ET.SubElement(self._root, "fc", {"in_type": in_type, "in_val": in_val, "out_type": out_type, "out_val":out_val})

    def set_pin_locations(self, pattern: Literal["spread", "perimeter", "spread_inputs_perimeter_outputs", "custom"]):
        if pattern not in ["spread", "perimeter", "spread_inputs_perimeter_outputs", "custom"]:
            raise ValueError("Pattern must be spread, perimeter, spread_inputs_perimeter_outputs, or custom")
        self._pin_locations.set("pattern", pattern)

    #lz TODO add pin locations - come from block list too?

    #lz TODO - connection_block input switch is going to have to come from switchlist I fear

#MARK: Switch
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

        self._root = ET.Element("switch", elems)

    def add_tdel(self, num_inputs: str, delay: str):
        ET.SubElement(self._root, "Tdel", {"num_inputs": num_inputs, "delay": delay})

#MARK: Segment
class Segment(_Node):
    def __init__(self,
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

        self.name = name
        self.type = type
        self._root = ET.Element("segment", elems)
        self.switch_mux: Switch
        self.switch_mux_inc: Switch
        self.switch_mux_dec: Switch
        self.switch_mux_inter_die: Switch

    def switch_block_pattern(self, pattern: List[int]):
        if self.length == 0:
            raise ValueError("Cannot define switch block pattern with longline length")
        if len(pattern) != self.length + 1:
            raise ValueError("Switch block pattern must have length of segment + 1")
        if not all(x in (0, 1) for x in pattern):
            raise ValueError("Switch block pattern can only contain 1 and 0")
        
        ET.SubElement(self._root, "sb", {"type": "pattern"}).text = " ".join(str(x) for x in pattern)

    def connection_block_pattern(self, pattern: List[int]):
        if self.length == 0:
            raise ValueError("Cannot define connection block pattern with longline length")
        if len(pattern) != self.length:
            raise ValueError("Connection block pattern must have length of segment")
        if not all(x in (0, 1) for x in pattern):
            raise ValueError("Connection block pattern can only contain 1 and 0")

        ET.SubElement(self._root, "cb", {"type": "pattern"}).text = " ".join(str(x) for x in pattern)

    def mux(self, switch: Switch):
        if self.type != "unidir":
            raise ValueError("Mux can only be defined for segments of type unidir")
        if switch.type != "mux":
            raise ValueError("Provided switch must be of type mux")
        if self._root.find("mux_inc") != None:
            raise ValueError("Mux cannot be defined alonside mux_inc/dec tag")

        self.switch_mux = switch
        ET.SubElement(self._root, "mux", {"name": switch.name})

    def mux_inc_dec(self, switch_inc: Switch, switch_dec: Switch):
        if self.type != "unidir":
            raise ValueError("Mux can only be defined for segments of type unidir")
        if switch_inc.type != "mux":
            raise ValueError("Provided switch must be of type mux")
        if switch_dec.type != "mux":
            raise ValueError("Provided switch must be of type mux")
        if self._root.find("mux") != None:
            raise ValueError("Inc/Dec mux cannot be defined alonside mux tag")
        
        self.switch_mux_inc = switch_inc
        self.switch_mux_dec = switch_dec
        ET.SubElement(self._root, "mux_inc", {"name": switch_inc.name})
        ET.SubElement(self._root, "mux_dec", {"name": switch_dec.name})

    def mux_inter_die(self, switch: Switch):
        if self.type != "unidir":
            raise ValueError("Mux can only be defined for segments of type unidir")
        if switch.type != "mux":
            raise ValueError("Provided switch must be of type mux")
        
        self.switch_mux_inter_die = switch
        ET.SubElement(self._root, "mux_inter_die", {"name": switch.name})

    def wire_switch(self, switch: Switch):
        if self.type != "bidir":
            raise ValueError("Wire_switch can only be defined for segments of type bidir")
        if not switch.type in ["tristate", "pass_gate"]:
            raise ValueError("Provided switch must be of type tristate or pass_gate")

        ET.SubElement(self._root, "wire_switch", {"name": switch.name})

    def opin_switch(self, switch: Switch):
        if self.type != "bidir":
            raise ValueError("Opin_switch can only be defined for segments of type bidir")
        if not switch.type in ["tristate", "pass_gate"]:
            raise ValueError("Provided switch must be of type tristate or pass_gate")

        ET.SubElement(self._root, "opin_switch", {"name": switch.name})