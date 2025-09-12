from __future__ import annotations
import xml.etree.ElementTree as ET
import networkx as nx
import matplotlib.pyplot as plt
import re
from xml.dom import minidom
from typing import Optional, Iterable, Dict, Any, List, Literal

#MARK: Base Classes
class _Node:
    def __init__(self):
        self.root = ET.Element("")

    def to_elem(self) -> ET.Element:
        return self.root

class _GraphIO:
    def __init__(self, name: str, type: str, index: int, base_block: ComplexBlock | Primitive):
        self.name = name
        self.index = index
        self.type = type
        self.base_block = base_block

class _GraphBlock:
    def __init__(self, name: str, base_block: ComplexBlock | Primitive):
        self.name = name
        self.base_block = base_block

class _Pin():
    def __init__(self, 
                 parent_block: ComplexBlock | Primitive, 
                 name: str, 
                 type: Literal["input", "output", "clock"], 
                 num_pins: int = 1,
                 equivalence: Literal["none", "full", "instance"] = "none",
                 is_non_clock_global: bool = False):
        if equivalence == "instance" and type != "output":
            raise ValueError("Equivalence of instance is only valid for output pins")
        if is_non_clock_global and type != "input":
            raise ValueError("is_non_clock_global is only valid for input pins")

        self.parent_block = parent_block
        self.name = name
        self.type = type
        self.equivalence = equivalence
        self.num_pins = num_pins

        if is_non_clock_global:
            self.is_non_clock_global = is_non_clock_global

    def get_pin(self, index) -> list[str]:
        return [self.parent_block.name + "." + self.name + "[" + str(index) + "]"]

    def get_all_pins(self) -> list[str]:
        return_list = []

        for x in range(0, self.num_pins):
            return_list.append(self.parent_block.name + "." + self.name + "[" + str(x) + "]")

        return return_list
    
    def get_pins_range(self, start_index: int, end_index: int):
        return_list = []

        for x in range(start_index, end_index + 1):
            return_list.append(self.parent_block.name + "." + self.name + "[" + str(x) + "]")

        return return_list
    
    def get_xml_node(self) -> ET.Element:
        if self.type == "input":
            if hasattr(self, "is_non_clock_global"):
                if self.equivalence == "none":
                    return ET.Element("input", {"name": self.name, "num_pins": str(self.num_pins), "is_non_clock_global": "true"})
                else:
                    return ET.Element("input", {"name": self.name, "num_pins": str(self.num_pins), "equivalent": self.equivalence, "is_non_clock_global": "true"})
            else:
                if self.equivalence == "none":
                    return ET.Element("input", {"name": self.name, "num_pins": str(self.num_pins)})
                else:
                    return ET.Element("input", {"name": self.name, "num_pins": str(self.num_pins), "equivalent": self.equivalence})
        elif self.type == "output":
            if self.equivalence == "none":
                return ET.Element("output", {"name": self.name, "num_pins": str(self.num_pins)})
            else:
                return ET.Element("output", {"name": self.name, "num_pins": str(self.num_pins), "equivalent": self.equivalence})
        else: #clock
            if self.equivalence == "none":
                return ET.Element("clock", {"name": self.name, "num_pins": str(self.num_pins)})
            else:
                return ET.Element("clock", {"name": self.name, "num_pins": str(self.num_pins), "equivalent": self.equivalence})


#MARK: Arch
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
        self.root = ET.Element("model", {"name": name, "never_prune": prune})
        self.inputs: Dict[str, int] = {}
        self.outputs: Dict[str, int] = {}
        self.clocks: Dict[str, int] = {}
        self._inputs = ET.SubElement(self.root, "input_ports")
        self._outputs = ET.SubElement(self.root, "output_ports")

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
            self.root = ET.Element("tile", {"name": name, "width": width, "height": height, "area":area})
        else:
            self.root = ET.Element("tile", {"name": name, "width": width, "height": height})

    def add_sub_tile(self, subTile: SubTile):
        self.root.append(subTile.to_elem())

#MARK: SubTile
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

        self.root = ET.Element("switch", elems)

    def add_tdel(self, num_inputs: str, delay: str):
        ET.SubElement(self.root, "Tdel", {"num_inputs": num_inputs, "delay": delay})

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
        self.root = ET.Element("segment", elems)
        self.switch_mux: Switch
        self.switch_mux_inc: Switch
        self.switch_mux_dec: Switch
        self.switch_mux_inter_die: Switch
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

    def mux(self, switch: Switch):
        if self.type != "unidir":
            raise ValueError("Mux can only be defined for segments of type unidir")
        if switch.type != "mux":
            raise ValueError("Provided switch must be of type mux")
        if self.root.find("mux_inc") != None:
            raise ValueError("Mux cannot be defined alonside mux_inc/dec tag")

        self.switch_mux = switch
        ET.SubElement(self.root, "mux", {"name": switch.name})

    def mux_inc_dec(self, switch_inc: Switch, switch_dec: Switch):
        if self.type != "unidir":
            raise ValueError("Mux can only be defined for segments of type unidir")
        if switch_inc.type != "mux":
            raise ValueError("Provided switch must be of type mux")
        if switch_dec.type != "mux":
            raise ValueError("Provided switch must be of type mux")
        if self.root.find("mux") != None:
            raise ValueError("Inc/Dec mux cannot be defined alonside mux tag")
        
        self.switch_mux_inc = switch_inc
        self.switch_mux_dec = switch_dec
        ET.SubElement(self.root, "mux_inc", {"name": switch_inc.name})
        ET.SubElement(self.root, "mux_dec", {"name": switch_dec.name})

    def mux_inter_die(self, switch: Switch):
        if self.type != "unidir":
            raise ValueError("Mux can only be defined for segments of type unidir")
        if switch.type != "mux":
            raise ValueError("Provided switch must be of type mux")
        
        self.switch_mux_inter_die = switch
        ET.SubElement(self.root, "mux_inter_die", {"name": switch.name})

    def wire_switch(self, switch: Switch):
        if self.type != "bidir":
            raise ValueError("Wire_switch can only be defined for segments of type bidir")
        if not switch.type in ["tristate", "pass_gate"]:
            raise ValueError("Provided switch must be of type tristate or pass_gate")
        
        ET.SubElement(self.root, "wire_switch", {"name": switch.name})

    def opin_switch(self, switch: Switch):
        if self.type != "bidir":
            raise ValueError("Opin_switch can only be defined for segments of type bidir")
        if not switch.type in ["tristate", "pass_gate"]:
            raise ValueError("Provided switch must be of type tristate or pass_gate")
        
        ET.SubElement(self.root, "opin_switch", {"name": switch.name})

#MARK: Mode
class Mode(_Node):
    def __init__(self,
                 name: str,
                 disable_packing: bool = False):
        self.name = name
        self.contents: Dict[str, ComplexBlock | Primitive] = {}
        self.num_dc: int = 0
        self.num_cc: int = 0
        self.num_mux: int = 0
        self._graph: nx.Graph = nx.Graph()

        self.root = ET.Element("mode", {"name": name, "disable_packing": str("true" if disable_packing else "false")})
        self._interconnect = ET.SubElement(self.root, "interconnect")
        

    def get_graph(self, mode: Optional[str] = None) -> nx.Graph:
        return self._graph

    #lz TODO does contents really do anything for us?
    #lz TODO if we're adding another complex block then need to check its inputs/outputs for equivalence maybe
    def add_block(self, block: ComplexBlock | Primitive):

        if block.name in self.contents:
            raise ValueError("Block with this name already exists")

        self.contents[block.name] = block

        self._graph.add_nodes_from(block.get_graph().nodes)
        self._graph.add_edges_from(block.get_graph().edges)

        self.root.append(block.to_elem())

        #lz TODO do we need to add the block to the xml here?
    


    def add_direct_connection(self,
                              input_list: list[str], 
                              output_list: list[str],
                              name: Optional[str] = None):
        if name == None:
            name = "direct" + str(self.num_dc)
            self.num_dc += 1

        if len(input_list) != len(output_list):
            raise ValueError("Direct connections must map 1:1 between inputs and outputs")
        
        for input, output in zip(input_list, output_list):
            self._graph.add_edge(input, output)

        elems = {"name": name}

        if len(input_list) == 1:
            elems["input"] = input_list[0]
            elems["output"] = output_list[0]
        else:
            elems["input"] = input_list[0][:-1] + ":" + str(int(input_list[0][-2]) + len(input_list) - 1) + "]"
            elems["output"] = output_list[0][:-1] + ":" + str(int(output_list[0][-2]) + len(output_list) - 1) + "]"

        ET.SubElement(self._interconnect, "direct", elems)

    def add_complete_connection(self,
                                inputs: list[list[str]],
                                outputs: list[list[str]],
                                name: Optional[str] = None,
                                mode: Optional[str] = None):
        
        if name == None:
            name = "complete" + str(self.num_cc)
            self.num_cc += 1
        
        self._graph.add_node(name)
        input_string_list = []
        output_string_list = []

        for pin_list in inputs:
            if len(pin_list) == 1:
                input_string_list.append(pin_list[0])
            else:
                input_string_list.append(pin_list[0][:-1] + ":" + str(int(pin_list[0][-2]) + len(pin_list) - 1) + "]")

            for pin in pin_list:
                self._graph.add_edge(name, pin)

        for pin_list in outputs:
            if len(pin_list) == 1:
                output_string_list.append(pin_list[0])
            else:
                output_string_list.append(pin_list[0][:-1] + ":" + str(int(pin_list[0][-2]) + len(pin_list) - 1) + "]")

            for pin in pin_list:
                self._graph.add_edge(name, pin)

        ET.SubElement(self._interconnect, "complete", {"name": name, "input": " ".join(input_string_list), "output": " ".join(output_string_list)})

    def add_mux_connection(self,
                           input_list: list[str],
                           output: str,
                           name: Optional[str] = None):
        if name == None:
            name = "mux" + str(self.num_mux)
            self.num_mux += 1

        self._graph.add_node(name)
        self._graph.add_edge(name, output)

        for pin in input_list:
            self._graph.add_edge(name, pin)

        elems = {"name": name, "output": output}

        if len(input_list) == 1:
            elems["input"] = input_list[0]
        else:
            elems["input"] = input_list[0][:-1] + ":" + str(int(input_list[0][-2]) + len(input_list) - 1) + "]"

        ET.SubElement(self._interconnect, "mux", elems)

#MARK: Primitive
class Primitive(_Node):
    #options for primitive model are input, output, lut4-6, ff, memory, or custom
    def __init__(self,
                 name: str,
                 type: Literal["input", "output", "lut4", "lut5", "lut6", "ff", "memory", "custom"],
                 blif_model: Optional[Model] = None,
                 num_pb: int = 1,
                 ):

        self.elems = {}

        self.name = name
        self.elems["name"] = name
        self.num_pb = num_pb
        self.elems["num_pb"] = str(num_pb)
        self.type = type

        self._graph = nx.Graph()
        self._graph.add_node(self.name)

        #inputs, outputs, clocks are stored by name and number of pins
        self.pins: Dict[str, _Pin] = {}

        self.root = ET.Element("pb_type")

        match type:
            case "input":
                self._input()
            case "output":
                self._output()
            case "lut4":
                self._lut(4)
            case "lut5":
                self._lut(5)
            case "lut6":
                self._lut(6)
            case "ff":
                self._ff()
            case "memory":
                if (blif_model == None):
                    raise ValueError("If model is type memory, then blif_model parameter must be provided")
                self._memory(blif_model)
            case "custom":
                if (blif_model == None):
                    raise ValueError("If model is type custom, then blif_model parameter must be provided")
                self._custom(blif_model)

        self.root.attrib.update(self.elems)

    def get_graph(self) -> nx.Graph:
        return self._graph

    def _input(self):
        self.elems["blif_model"] = ".input"

        self._add_input("in", 1)

    def _output(self):
        self.elems["blif_model"] = ".output"

        self._add_output("out", 1)

    def _lut(self, num_pins: int):
        self.elems["blif_model"] = ".names"
        self.elems["class"] = "lut"

        self._add_input("in", num_pins, "lut_in")
        self._add_output("out", 1, "lut_out")

    def _ff(self):
        self.elems["blif_model"] = ".latch"
        self.elems["class"] = "flipflop"

        self._add_input("D", 1, "D")
        self._add_output("Q", 1, "Q")
        self._add_clock("clock", 1, "clock")

    #lz TODO memory
    def _memory(self, blif_model: Model):
        self.elems["blif_model"] = ".subckt " + blif_model.name
        self.elems["class"] = "memory"

    def _custom(self, blif_model: Model):
        self.elems["blif_model"] = ".subckt " + blif_model.name

        for port_name, value in blif_model.inputs.items():
            self._add_input(name=port_name, num_pins=value)
        for port_name, value in blif_model.outputs.items():
            self._add_output(name=port_name, num_pins=value)
        for port_name, value in blif_model.clocks.items():
            self._add_clock(name=port_name, num_pins=value)

    def _add_input(self, name: str, num_pins: int, port_class: Optional[str] = None):
        self.pins[name] = _Pin(self, name, "input", num_pins)

        for pin in self.pins[name].get_all_pins():
            self._graph.add_node(pin)
            self._graph.add_edge(self.name, pin)

        if port_class != None:
            ET.SubElement(self.root, "input", {"name": name, "num_pins": str(num_pins), "port_class": port_class})
        else:
            ET.SubElement(self.root, "input", {"name": name, "num_pins": str(num_pins)})

    def _add_output(self, name: str, num_pins: int, port_class: Optional[str] = None):
        self.pins[name] = _Pin(self, name, "output", num_pins)

        for pin in self.pins[name].get_all_pins():
            self._graph.add_node(pin)
            self._graph.add_edge(self.name, pin)

        if port_class != None:
            ET.SubElement(self.root, "output", {"name": name, "num_pins": str(num_pins), "port_class": port_class})
        else:
            ET.SubElement(self.root, "output", {"name": name, "num_pins": str(num_pins)})

    def _add_clock(self, name: str, num_pins: int, port_class: Optional[str] = None):
        self.pins[name] = _Pin(self, name, "clock", num_pins)

        for pin in self.pins[name].get_all_pins():
            self._graph.add_node(pin)
            self._graph.add_edge(self.name, pin)

        if port_class != None:
            ET.SubElement(self.root, "clock", {"name": name, "num_pins": str(num_pins), "port_class": port_class})
        else:
            ET.SubElement(self.root, "clock", {"name": name, "num_pins": str(num_pins)})
#MARK: ComplexBlock
class ComplexBlock(_Node):
    def __init__(self, name: str, num_pb:int = 1):
        self.name = name
        self.root = ET.Element("pb_type", {"name": name, "num_pb": str(num_pb)})
        self._graph = nx.Graph()
        self._modes: Dict[str, Mode] = {}
        self.pins: Dict[str, _Pin] = {}

    def add_block(self, block: ComplexBlock | Primitive):
        if len(self._modes) not in [0, 1] or (len(self._modes) == 1 and list(self._modes.values())[0].name != "default"):
            raise ValueError("Blocks can only be added to complex blocks with default mode")

        if len(self._modes) == 0:
            self._modes["default"] = Mode("default")
            self._modes["default"].add_block(block)
        else:
            self._modes["default"].add_block(block)

    def add_input(self, name:str, num_pins: int, equivalence: Literal["none", "full", "instance"] = "none", is_non_clock_global: bool = False):
        self.pins[name] = _Pin(self, name, "input", num_pins, equivalence, is_non_clock_global)

        self._graph.add_nodes_from(self.pins[name].get_all_pins())

        self.root.append(self.pins[name].get_xml_node())

    def add_output(self, name: str, num_pins: int):
        self.pins[name] = _Pin(self, name, "output", num_pins)

        self._graph.add_nodes_from(self.pins[name].get_all_pins())

        self.root.append(self.pins[name].get_xml_node())

    def add_clock(self, name: str, num_pins: int):
        self.pins[name] = _Pin(self, name, "clock", num_pins)

        self._graph.add_nodes_from(self.pins[name].get_all_pins())

        self.root.append(self.pins[name].get_xml_node())

    def add_mode(self, mode: Mode):
        if mode.name in self._modes:
            raise ValueError("Mode with this name already exists")
        if "default" in self._modes:
            raise ValueError("Cannot add modes to complex block with default mode")

        self._modes[mode.name] = mode

        self.root.append(mode.to_elem())

        self._graph.add_nodes_from(mode.get_graph().nodes)
        self._graph.add_edges_from(mode.get_graph().edges)

    def get_graph(self) -> nx.Graph:
        return self._graph


#MARK: Example Usage

############################################


arch = Arch()

############ MODELS ###################

io_model = Model("io")
io_model.add_input_ports(name="outpad")
io_model.add_output_ports(name="addr")

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

io = ComplexBlock(name="io")
io.add_input(name="outpad", num_pins=1)
io.add_output(name="inpad", num_pins=1)

iopad = Primitive(name="iopad", type="custom", blif_model=io_model)

physical = Mode(name="physical", disable_packing=True)
physical.add_block(iopad)

#lz TODO Should connections take place inside mode actually?
#lz TODO actually I was going to change the clb logic to be mode and the mode to be clb and that way everything works out and a clb cant have modes and blocks

nx.draw(cb1.get_graph(), with_labels=True)
plt.savefig("testgraph.png")

############ PRINT ###################

arch.save("my_arch.xml")
print(arch.to_string()[:4000]) 

        