from __future__ import annotations
import keyword
import networkx as nx
from typing import TYPE_CHECKING, Optional, List, Literal, Dict
import copy
import re
import xml.etree.ElementTree as ET
from .vtr_utils import _Node, _Pins

if TYPE_CHECKING:
    from .vtr_core import Model, Power_Estimate

#MARK: Mode
class Mode(_Node):
    def __init__(self,
                 name: str,
                 parent: ComplexBlock,
                 disable_packing: bool = False):
        self._root = ET.Element("mode", {"name": name, "disable_packing": str("true" if disable_packing else "false")})
        self._parent = parent
        self._name = name
        self._contents: Dict[str, ComplexBlock | Primitive] = {}
        self._interconnect = ET.SubElement(self._root, "interconnect")
        self._graph = nx.Graph()
        self.num_dc = 0
        self.num_cc = 0
        self.num_mux = 0

    #lz TODO error check inputs and outputs
    def add_direct_connection(self,
                              inputs: list[str], 
                              outputs: list[str],
                              delay_constant: Optional[tuple[str, str, list[float]]] = None):
        
        for input in inputs:
            ss = parse_property_string(input)
            if ss[0] != self._parent._name and ss[0] not in self._contents:
                raise ValueError("Block " + ss[0] + " not found in mode " + self._name)
            if ss[0] == self._parent._name and ss[1] not in self._parent._pins:
                raise ValueError("Pin " + ss[1] + " not found in complex block " + self._parent._name)
            if ss[0] != self._parent._name and ss[1] not in self._contents[ss[0]]._pins:
                raise ValueError("Pin " + ss[1] + " not found in block " + ss[0])
            
        for output in outputs:
            ss = parse_property_string(output)
            if ss[0] != self._parent._name and ss[0] not in self._contents:
                raise ValueError("Block " + ss[0] + " not found in mode " + self._name)
            if ss[0] == self._parent._name and ss[1] not in self._parent._pins:
                raise ValueError("Pin " + ss[1] + " not found in complex block " + self._parent._name)
            if ss[0] != self._parent._name and ss[1] not in self._contents[ss[0]]._pins:
                raise ValueError("Pin " + ss[1] + " not found in block " + ss[0])

        total_inputs = 0
        for input in inputs:
            split_string = parse_property_string(input)
            if split_string[0] == self._parent._name:
                if (split_string[2] != None or split_string[3] != None):
                    raise ValueError("Cannot index top level pb")
                total_inputs += abs((int(split_string[4]) if split_string[4] != None else 0) - (int(split_string[5]) if split_string[5] != None else int(self._parent._pins[split_string[1]]._num_pins) - 1)) + 1
            else:
                pins_per_block = abs((int(split_string[4]) if split_string[4] != None else 0) - (int(split_string[5]) if split_string[5] != None else int(self._contents[split_string[0]]._pins[split_string[1]]._num_pins) - 1)) + 1
                num_blocks = abs((int(split_string[2]) if split_string[2] != None else 0) - (int(split_string[3]) if split_string[3] != None else int(self._contents[split_string[0]]._num_pb) - 1)) + 1
                total_inputs += pins_per_block * num_blocks

        total_outputs = 0
        for output in outputs:
            split_string = parse_property_string(output)
            if split_string[0] == self._parent._name:
                if (split_string[2] != None or split_string[3] != None):
                    raise ValueError("Cannot index top level pb")
                total_outputs += abs((int(split_string[4]) if split_string[4] != None else 0) - (int(split_string[5]) if split_string[5] != None else int(self._parent._pins[split_string[1]]._num_pins) - 1)) + 1
            else:
                pins_per_block = abs((int(split_string[4]) if split_string[4] != None else 0) - (int(split_string[5]) if split_string[5] != None else int(self._contents[split_string[0]]._pins[split_string[1]]._num_pins) - 1)) + 1
                num_blocks = abs((int(split_string[2]) if split_string[2] != None else 0) - (int(split_string[3]) if split_string[3] != None else int(self._contents[split_string[0]]._num_pb) - 1)) + 1
                total_outputs += pins_per_block * num_blocks

        if total_inputs != total_outputs:
            raise ValueError("Number of input pins must match number of output pins for direct connection : " + str(total_inputs) + " != " + str(total_outputs))

        conn_node = ET.SubElement(self._interconnect, "direct", {
            "name": "direct" + str(self.num_dc),
            "input": " ".join(inputs),
            "output": " ".join(outputs)
        })
        self.num_dc += 1

        if delay_constant is not None:
            if delay_constant[0] not in inputs:
                raise ValueError("Delay constant in_port must be one of the inputs")
            if delay_constant[1] not in outputs:
                raise ValueError("Delay constant out_port must be one of the outputs")
            if len(delay_constant[2]) not in [1, 2]:
                raise ValueError("Delay constant list must specify min, max, or both")
            ET.SubElement(conn_node, "delay_constant", {
                "max": str(delay_constant[2][-1]),
                "min": str(delay_constant[2][0]),
                "in_port": delay_constant[0],
                "out_port": delay_constant[1]
            })

    #lz TODO need to graph this somehow (oh wait we use the individual get methods from pin)
    def add_complete_connection(self,
                                inputs: list[str],
                                outputs: list[str]):

        for input in inputs:
            ss = parse_property_string(input)
            if ss[0] != self._parent._name and ss[0] not in self._contents:
                raise ValueError("Block " + ss[0] + " not found in mode " + self._name)
            if ss[0] == self._parent._name and ss[1] not in self._parent._pins:
                raise ValueError("Pin " + ss[1] + " not found in complex block " + self._parent._name)
            if ss[0] != self._parent._name and ss[1] not in self._contents[ss[0]]._pins:
                raise ValueError("Pin " + ss[1] + " not found in block " + ss[0])
            
        for output in outputs:
            ss = parse_property_string(output)
            if ss[0] != self._parent._name and ss[0] not in self._contents:
                raise ValueError("Block " + ss[0] + " not found in mode " + self._name)
            if ss[0] == self._parent._name and ss[1] not in self._parent._pins:
                raise ValueError("Pin " + ss[1] + " not found in complex block " + self._parent._name)
            if ss[0] != self._parent._name and ss[1] not in self._contents[ss[0]]._pins:
                raise ValueError("Pin " + ss[1] + " not found in block " + ss[0])

        ET.SubElement(self._interconnect, "complete", {
            "name": "complete" + str(self.num_cc),
            "input": " ".join(inputs),
            "output": " ".join(outputs)
        })
        self.num_cc += 1

    #lz TODO wait did we decide that mux output has to be width 1
    def add_mux_connection(self,
                           inputs: list[str],
                           outputs: str,
                           name: Optional[str] = None):

        for input in inputs:
            ss = parse_property_string(input)
            if ss[0] != self._parent._name and ss[0] not in self._contents:
                raise ValueError("Block " + ss[0] + " not found in mode " + self._name)
            if ss[0] == self._parent._name and ss[1] not in self._parent._pins:
                raise ValueError("Pin " + ss[1] + " not found in complex block " + self._parent._name)
            if ss[0] != self._parent._name and ss[1] not in self._contents[ss[0]]._pins:
                raise ValueError("Pin " + ss[1] + " not found in block " + ss[0])
            
        ss = parse_property_string(outputs)
        if ss[0] != self._parent._name and ss[0] not in self._contents:
            raise ValueError("Block " + ss[0] + " not found in mode " + self._name)
        if ss[0] == self._parent._name and ss[1] not in self._parent._pins:
            raise ValueError("Pin " + ss[1] + " not found in complex block " + self._parent._name)
        if ss[0] != self._parent._name and ss[1] not in self._contents[ss[0]]._pins:
            raise ValueError("Pin " + ss[1] + " not found in block " + ss[0])

        if ss[4] != None and ss[5] != None and ss[4] != ss[5]:
            raise ValueError("Output of mux must be a single pin")
        if ss[0] == self._parent._name:
            if ss[4] == None and self._parent._pins[ss[1]]._num_pins != 1:
                raise ValueError("Output of mux must be a single pin")
        else:
            if ss[4] == None and self._contents[ss[0]]._pins[ss[1]]._num_pins != 1:
                raise ValueError("Output of mux must be a single pin")

    def add_block(self, block: ComplexBlock | Primitive):
        if block in self._contents:
            raise ValueError("Block with name " + block._name + " already exists in this mode")
        self._contents[block._name] = block
        self._root.append(block.to_elem())

#MARK: Primitive
class Primitive(_Node):
    #options for primitive model are input, output, lut4-6, ff, memory, or custom
    def __init__(self,
                 name: str,
                 type: Literal["input", "output", "lut4", "lut5", "lut6", "ff", "memory", "custom"],
                 blif_model: Optional[Model] = None,
                 num_pb: int = 1,
                 ):
        self._name = name
        self._num_pb = num_pb
        self._pins: Dict[str, _Pins] = {}

        self._graph = nx.Graph()
        self._graph.add_node(self)

        self._type = type
        self._root = ET.Element("pb_type")
        self._elems = {"name": name, "num_pb": str(num_pb)}
        self._type = type

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

        self._root.attrib.update(self._elems)
    
    def _input(self, num_pb: int = 1):
        self._elems["blif_model"] = ".input"

        self._add_output("input", 1)

    def _output(self, num_pb: int = 1):
        self._elems["blif_model"] = ".output"

        self._add_input("output", 1)

    def _lut(self, num_pins: int, num_pb: int = 1):
        self._elems["blif_model"] = ".names"
        self._elems["class"] = "lut"

        self._add_input("input", num_pins, "lut_in")
        self._add_output("output", 1, "lut_out")

    def _ff(self, num_pb: int = 1):
        self._elems["blif_model"] = ".latch"
        self._elems["class"] = "flipflop"

        self._add_input(name = "D",num_pins =  1, port_class= "D")
        self._add_output(name = "Q",num_pins= 1, port_class= "Q")
        self._add_clock(name="clock",num_pins= 1, port_class="clock")

    #lz TODO memory
    def _memory(self, blif_model: Model, num_pb: int = 1):
        self._elems["blif_model"] = ".subckt " + blif_model.name
        self._elems["class"] = "memory"

    def _custom(self, blif_model: Model):
        self._elems["blif_model"] = ".subckt " + blif_model.name

        for port_name, value in blif_model.inputs.items():
            self._add_input(name=port_name, num_pins=value)
        for port_name, value in blif_model.outputs.items():
            self._add_output(name=port_name, num_pins=value)
        for port_name, value in blif_model.clocks.items():
            self._add_clock(name=port_name, num_pins=value)

    def _add_input(self, name: str, num_pins: int, port_class: Optional[str] = None):
        if name in self._pins:
            raise ValueError("Pin with name " + name + " already exists in this primitive")

        self._pins[name] = _Pins(self, name=name, type="input", num_pins=num_pins)

        self._graph.add_nodes_from(self._pins[name]._pins)
        self._graph.add_edges_from(zip(self._pins[name]._pins, (self for _ in range(num_pins))))

        attrs = {"name": name, "num_pins": str(num_pins)}
        if port_class is not None:
            attrs["port_class"] = port_class
        ET.SubElement(self._root, "input", attrs)

    def _add_output(self, name: str, num_pins: int, port_class: Optional[str] = None):
        if name in self._pins:
            raise ValueError("Pin with name " + name + " already exists in this primitive")
        self._pins[name] = _Pins(self, name=name, type="output", num_pins=num_pins)

        self._graph.add_nodes_from(self._pins[name]._pins)
        self._graph.add_edges_from(zip(self._pins[name]._pins, (self for _ in range(num_pins))))


        attrs = {"name": name, "num_pins": str(num_pins)}
        if port_class is not None:
            attrs["port_class"] = port_class
        ET.SubElement(self._root, "output", attrs)

    def _add_clock(self, name: str, num_pins: int, port_class: Optional[str] = None):
        if name in self._pins:
            raise ValueError("Pin with name " + name + " already exists in this primitive")
        
        self._pins[name] = _Pins(self, name=name, type="clock", num_pins=num_pins)

        self._graph.add_nodes_from(self._pins[name]._pins)
        self._graph.add_edges_from(zip(self._pins[name]._pins, (self for _ in range(num_pins))))

        attrs = {"name": name, "num_pins": str(num_pins)}
        if port_class is not None:
            attrs["port_class"] = port_class
        ET.SubElement(self._root, "clock", attrs)

    def get_graph(self):
        return self._graph
       
#MARK: ComplexBlock

class ComplexBlock(_Node):
    def __init__(self, name: str, num_pb:int = 1):
        self._name = name
        self._num_pb = num_pb
        self._is_top = num_pb == 1 # initially assume top if num_pb is 1, if we add this block to a mode or another block we will reset it
        if self._is_top:
            self._root = ET.Element("pb_type", {"name": name})
        else:
            self._root = ET.Element("pb_type", {"name": name, "num_pb": str(num_pb)})
        self._modes: List[Mode] = []
        self._contents: Dict[str, ComplexBlock | Primitive] = {}
        self._interconnect = ET.SubElement(self._root, "interconnect")
        self._graph = nx.Graph()
        self.num_dc = 0
        self.num_cc = 0
        self.num_mux = 0
        self._dynamic_attrs = {}  # Store dynamically added attributes
        self._pins: Dict[str, _Pins] = {}

        self.node_name = self._name

    def add_block(self, block: ComplexBlock | Primitive):
        if len(self._modes) > 0:
            raise ValueError("Blocks can only be added to complex blocks with default mode")

        if isinstance(block, ComplexBlock) and block._is_top:
            block.set_n_top()

        if block._name in self._contents:
            raise ValueError("Block with name " + block._name + " already exists in this complex block")
        else:
            self._contents[block._name] = block
        self._root.append(block.to_elem())
        self._graph = nx.compose(self._graph, block._graph)

    def add_input(self, name:str, num_pins: int, equivalence: Literal["none", "full", "instance"] = "none", is_non_clock_global: bool = False):
        if name in self._pins:
            raise ValueError("Pin with name " + name + " already exists in this complex block")

        self._pins[name] = _Pins(self, name=name, type="input", num_pins=num_pins, equivalence=equivalence, is_non_clock_global=is_non_clock_global)

        self._root.append(self._pins[name].get_xml_node())

    def add_output(self, name: str, num_pins: int, equivalence: Literal["none", "full", "instance"] = "none"):
        if name in self._pins:
            raise ValueError("Pin with name " + name + " already exists in this complex block")

        self._pins[name] = _Pins(self, name=name, type="output", num_pins=num_pins, equivalence=equivalence)

        self._root.append(self._pins[name].get_xml_node())

    def add_clock(self, name: str, num_pins: int, equivalence: Literal["none", "full"] = "none"):
        if name in self._pins:
            raise ValueError("Pin with name " + name + " already exists in this complex block")

        self._pins[name] = _Pins(self, name=name, type="clock", num_pins=num_pins, equivalence=equivalence)

        self._root.append(self._pins[name].get_xml_node())

#lz TODO add mode to graph
    def add_mode(self, mode: Mode):
        if len(self._contents) > 0:
            raise ValueError("Modes can only be added to complex blocks with no blocks")

        if mode in self._modes:
            raise ValueError("Mode with this name already exists")

        self._modes.append(mode)

        self._root.append(mode.to_elem())

    def add_direct_connection(self,
                            inputs: list[str], 
                            outputs: list[str],
                            delay_constant: Optional[tuple[str, str, list[float]]] = None):
        if len(self._modes) > 0:
            raise ValueError("Connections can only be added to complex blocks with no modes")

        self._validate_io(inputs, outputs)

        total_inputs = 0
        for input in inputs:
            split_string = parse_property_string(input)
            if split_string[0] == self._name:
                if (split_string[2] != None or split_string[3] != None):
                    raise ValueError("Cannot index top level pb")
                total_inputs += abs((int(split_string[4]) if split_string[4] != None else 0) - (int(split_string[5]) if split_string[5] != None else int(self._pins[split_string[1]]._num_pins) - 1)) + 1
            else:
                pins_per_block = abs((int(split_string[4]) if split_string[4] != None else 0) - (int(split_string[5]) if split_string[5] != None else int(self._contents[split_string[0]]._pins[split_string[1]]._num_pins) - 1)) + 1
                num_blocks = abs((int(split_string[2]) if split_string[2] != None else 0) - (int(split_string[3]) if split_string[3] != None else int(self._contents[split_string[0]]._num_pb) - 1)) + 1
                total_inputs += pins_per_block * num_blocks

        total_outputs = 0
        for output in outputs:
            split_string = parse_property_string(output)
            if split_string[0] == self._name:
                if (split_string[2] != None or split_string[3] != None):
                    raise ValueError("Cannot index top level pb")
                total_outputs += abs((int(split_string[4]) if split_string[4] != None else 0) - (int(split_string[5]) if split_string[5] != None else int(self._pins[split_string[1]]._num_pins) - 1)) + 1
            else:
                pins_per_block = abs((int(split_string[4]) if split_string[4] != None else 0) - (int(split_string[5]) if split_string[5] != None else int(self._contents[split_string[0]]._pins[split_string[1]]._num_pins) - 1)) + 1
                num_blocks = abs((int(split_string[2]) if split_string[2] != None else 0) - (int(split_string[3]) if split_string[3] != None else int(self._contents[split_string[0]]._num_pb) - 1)) + 1
                total_outputs += pins_per_block * num_blocks

        if total_inputs != total_outputs:
            raise ValueError("Number of input pins must match number of output pins for direct connection : " + str(total_inputs) + " != " + str(total_outputs))

        conn_node = ET.SubElement(self._interconnect, "direct", {
            "name": "direct" + str(self.num_dc),
            "input": " ".join(inputs),
            "output": " ".join(outputs)
        })
        self.num_dc += 1

        if delay_constant is not None:
            if delay_constant[0] not in inputs:
                raise ValueError("Delay constant in_port must be one of the inputs")
            if delay_constant[1] not in outputs:
                raise ValueError("Delay constant out_port must be one of the outputs")
            if len(delay_constant[2]) not in [1, 2]:
                raise ValueError("Delay constant list must specify min, max, or both")
            ET.SubElement(conn_node, "delay_constant", {
                "max": str(delay_constant[2][-1]),
                "min": str(delay_constant[2][0]),
                "in_port": delay_constant[0],
                "out_port": delay_constant[1]
            })

    def add_complete_connection(self,
                                inputs: list[str], 
                                outputs: list[str]):
        if len(self._modes) > 0:
            raise ValueError("Connections can only be added to complex blocks with no modes")

        self._validate_io(inputs, outputs)

        ET.SubElement(self._interconnect, "complete", {
            "name": "complete" + str(self.num_cc),
            "input": " ".join(inputs),
            "output": " ".join(outputs)
        })
        self.num_cc += 1

    def add_mux_connection(self,
                           inputs: list[str], 
                           outputs: str):
        if len(self._modes) > 0:
            raise ValueError("Connections can only be added to complex blocks with no modes")

        self._validate_io(inputs, [outputs])

        ss = parse_property_string(outputs)

        if ss[4] != None and ss[5] != None and ss[4] != ss[5]:
            raise ValueError("Output of mux must be a single pin")
        if ss[0] == self._name:
            if ss[4] == None and self._pins[ss[1]]._num_pins != 1:
                raise ValueError("Output of mux must be a single pin")
        else:
            if ss[4] == None and self._contents[ss[0]]._pins[ss[1]]._num_pins != 1:
                raise ValueError("Output of mux must be a single pin")

        ET.SubElement(self._interconnect, "mux", {
            "name": "mux" + str(self.num_mux),
            "input": " ".join(inputs),
            "output": outputs
        })
        self.num_mux += 1

    def get_graph(self):
        return self._graph
    
    def set_n_top(self):
        self._is_top = False
        self._root.set("num_pb", str(self._num_pb))

    def set_power_estimate(self, power: Power_Estimate):
        for port in power._ports:
            if port not in self._pins:
                raise ValueError(f"Port {port} not found in block {self._name}")
            
        self._root.append(power.to_elem())

    def _validate_io(self, inputs: list[str], outputs: list[str]):
        for input in inputs:
            ss = parse_property_string(input)
            if ss[0] != self._name and ss[0] not in self._contents:
                raise ValueError("Block " + ss[0] + " not found in complex block " + self._name)
            if ss[0] == self._name and ss[1] not in self._pins:
                raise ValueError("Pin " + ss[1] + " not found in complex block " + self._name)
            if ss[0] != self._name and ss[1] not in self._contents[ss[0]]._pins:
                raise ValueError("Pin " + ss[1] + " not found in block " + ss[0])
            
        for output in outputs:
            ss = parse_property_string(output)
            if ss[0] != self._name and ss[0] not in self._contents:
                raise ValueError("Block " + ss[0] + " not found in complex block " + self._name)
            if ss[0] == self._name and ss[1] not in self._pins:
                raise ValueError("Pin " + ss[1] + " not found in complex block " + self._name)
            if ss[0] != self._name and ss[1] not in self._contents[ss[0]]._pins:
                raise ValueError("Pin " + ss[1] + " not found in block " + ss[0])

def parse_property_string(s: str):
    """
    Parse a string of the format 'string1[index1:index2].string2[index3:index4]'
    where indices are optional.
    
    Returns:
        (str1, str2, idx1, idx2, idx3, idx4)
        Integers or None if not present.
    """
    # Pattern: name + optional [x(:y)?]
    pattern = r"^([a-zA-Z_]\w*)(?:\[(\d+)(?::(\d+))?\])?\." \
            r"([a-zA-Z_]\w*)(?:\[(\d+)(?::(\d+))?\])?$"
    
    match = re.match(pattern, s)
    if not match:
        raise ValueError(f"Invalid format: {s}")
    
    str1, i1, i2, str2, i3, i4 = match.groups()
    
    # Convert numeric strings to int or None
    def to_int(x): return int(x) if x is not None else None
    
    return str1, str2, to_int(i1), to_int(i2), to_int(i3), to_int(i4)