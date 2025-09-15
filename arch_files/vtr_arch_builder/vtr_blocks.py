from __future__ import annotations
from dataclasses import dataclass
import networkx as nx
from typing import Optional, Dict, List, Literal
import xml.etree.ElementTree as ET
from .vtr_utils import _Node, _Pins
from .vtr_core import Model

#OKAY I THINK WE DIVORCE THE IDEA OF NUM_PB FROM THE BLOCK ITSELF AND INSTEAD THE PARENT KNOWS HOW MANY OF A BLOCK IT HAS

#MARK: Mode
class Mode(_Node):
    def __init__(self,
                 name: str,
                 disable_packing: bool = False):
        _BlockWithInterconnect.__init__(self, ET.Element("mode", {"name": name, "disable_packing": str("true" if disable_packing else "false")}))
        self._name = name
        self._contents: Dict[str, ComplexBlock | Primitive] = {}

        self._interconnect = ET.SubElement(self.root, "interconnect")

    def add_direct_connection(self,
                              input_list: list[str], 
                              output_list: list[str],
                              name: Optional[str] = None):
        if name == None:
            name = "direct" + str(self.num_dc)
            self.num_dc += 1

        # if len(input_list) != len(output_list):
        #     raise ValueError("Direct connections must map 1:1 between inputs and outputs")

        elems = {"name": name}

        if len(input_list) == 1:
            elems["input"] = input_list[0]
            elems["output"] = output_list[0]
        else:
            elems["input"] = " ".join(input_list)
            elems["output"] = " ".join(output_list)

        ET.SubElement(self._interconnect, "direct", elems)


    #lz TODO need to graph this somehow (oh wait we use the individual get methods from pin)
    def add_complete_connection(self,
                                inputs: list[str],
                                outputs: list[str],
                                name: Optional[str] = None):
        
        if name == None:
            name = "complete" + str(self.num_cc)
            self.num_cc += 1
        
        self._graph.add_node(name)
        input_string_list = []
        output_string_list = []

        ET.SubElement(self._interconnect, "complete", {"name": name, "input": " ".join(inputs), "output": " ".join(outputs)})

    def add_mux_connection(self,
                           input_list: list[str],
                           output: str,
                           name: Optional[str] = None):
        if name == None:
            name = "mux" + str(self.num_mux)
            self.num_mux += 1

        elems = {"name": name, "input": " ".join(input_list), "output": output}

        ET.SubElement(self._interconnect, "mux", elems)

#MARK: Primitive

class _Primitive_Node():
    def __init__(self, parent: Primitive, index: int):
        self.parent = parent
        self.index = index

    def _add_pins(self, name: str, pins: _Pins):
        setattr(self, name, pins)

class Primitive(_Node):
    #options for primitive model are input, output, lut4-6, ff, memory, or custom
    def __init__(self,
                 name: str,
                 type: Literal["input", "output", "lut4", "lut5", "lut6", "ff", "memory", "custom"],
                 blif_model: Optional[Model] = None,
                 num_pb: int = 1,
                 ):

        self._primitive_nodes = [_Primitive_Node(self, i) for i in range(num_pb)]

        self._graph = nx.Graph().add_nodes_from(self._primitive_nodes)

        self.root = ET.Element("pb_type")
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

        self.root.attrib.update(self._elems)

    def __getitem__(self, index):
        if isinstance(index, slice):
            if index.start is None or index.stop is None:
                raise IndexError("Slice must have both start and stop defined")
            if index.start < 0 or index.stop < 0:
                raise IndexError("Negative indices are not supported")
            if index.step is not None:
                raise IndexError("Slice step is not supported")
            if index.start > index.stop:
                start = index.start
                stop = index.stop - 1 if index.stop != 0 else None
                step = -1
            else:
                start = index.start
                stop = index.stop + 1
                step = 1
            return self._primitive_nodes[start:stop:step]
        return self._primitive_nodes[index]

    def _input(self, num_pb: int = 1):
        self._elems["blif_model"] = ".input"

        self._add_output("in", 1)

    def _output(self, num_pb: int = 1):
        self._elems["blif_model"] = ".output"

        self._add_input("out", 1)

    def _lut(self, num_pins: int, num_pb: int = 1):
        self._elems["blif_model"] = ".names"
        self._elems["class"] = "lut"

        self._add_input("in", num_pins, "lut_in")
        self._add_output("out", 1, "lut_out")

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
        if hasattr(self, name):
            raise ValueError("Pin with name " + name + " already exists in this primitive")
        
        setattr(self, name, _Pins(name=name, type="input", num_pins=num_pins))

        for prim_node in self._primitive_nodes:
            prim_node._add_pins(name, _Pins(name=name, type="input", num_pins=num_pins))

        if port_class != None:
            ET.SubElement(self.root, "input", {"name": name, "num_pins": str(num_pins), "port_class": port_class})
        else:
            ET.SubElement(self.root, "input", {"name": name, "num_pins": str(num_pins)})

    def _add_output(self, name: str, num_pins: int, port_class: Optional[str] = None):
        if hasattr(self, name):
            raise ValueError("Pin with name " + name + " already exists in this primitive")

        setattr(self, name, _Pins(name=name, type="output", num_pins=num_pins))

        for prim_node in self._primitive_nodes:
            prim_node._add_pins(name, _Pins(name=name, type="output", num_pins=num_pins))

        if port_class != None:
            ET.SubElement(self.root, "output", {"name": name, "num_pins": str(num_pins), "port_class": port_class})
        else:
            ET.SubElement(self.root, "output", {"name": name, "num_pins": str(num_pins)})

    def _add_clock(self, name: str, num_pins: int, port_class: Optional[str] = None):
        if hasattr(self, name):
            raise ValueError("Pin with name " + name + " already exists in this primitive")

        setattr(self, name, _Pins(name=name, type="input", num_pins=num_pins))

        for prim_node in self._primitive_nodes:
            prim_node._add_pins(name, _Pins(name=name, type="input", num_pins=num_pins))

        if port_class != None:
            ET.SubElement(self.root, "clock", {"name": name, "num_pins": str(num_pins), "port_class": port_class})
        else:
            ET.SubElement(self.root, "clock", {"name": name, "num_pins": str(num_pins)})
            
#MARK: ComplexBlock
class ComplexBlock(_Node, _BlockWithPins, _BlockWithInterconnect):
    def __init__(self, name: str, num_pb:int = 1):
        _BlockWithPins.__init__(self, name=name, num_pb=num_pb)
        _BlockWithInterconnect.__init__(self, ET.Element("pb_type", {"name": name, "num_pb": str(num_pb)}))
        self._modes: Dict[str, Mode] = {}
        self._pins: List[Dict[str, _Pin]] = [{} for _ in range(num_pb)]
        self._interconnect = ET.SubElement(self.root, "interconnect")

    def add_block(self, block: ComplexBlock | Primitive):
        if len(self._modes) not in [0, 1] or (len(self._modes) == 1 and list(self._modes.values())[0].name != "default"):
            raise ValueError("Blocks can only be added to complex blocks with default mode")

        _BlockWithInterconnect.add_block(self, block)

    def add_input(self, name:str, num_pins: int, equivalence: Literal["none", "full", "instance"] = "none", is_non_clock_global: bool = False):
        if self.num_pb == 1:
            self._pins[0][name] = _Pin(name= name, type="input", num_pins=num_pins, equivalence=equivalence, is_non_clock_global=is_non_clock_global)

            self._graph.add_node(self._pins[0][name].get_pins())
            self._graph.add_edge(self.name, self._pins[0][name].get_pins())
        else:
            for ii in range (0, self.num_pb):
                self._pins[ii][name] = _Pin(name=name, type="input", num_pins=num_pins, equivalence=equivalence, is_non_clock_global=is_non_clock_global)

                for pin in self._pins[ii][name]._get_pins_indiv((0, num_pins - 1)):
                    self._graph.add_node(pin)

        self.root.append(self._pins[0][name].get_xml_node())

    def add_output(self, name: str, num_pins: int):
        if self.num_pb == 1:
            self._pins[0][name] = _Pin(name= name, type="output", num_pins=num_pins)

            self._graph.add_node(self._pins[0][name].get_pins())
            self._graph.add_edge(self.name, self._pins[0][name].get_pins())
        else:
            for ii in range (0, self.num_pb):
                self._pins[ii][name] = _Pin(name=name, type="output", num_pins=num_pins)

                for pin in self._pins[ii][name]._get_pins_indiv((0, num_pins - 1)):
                    self._graph.add_node(pin)

        self.root.append(self._pins[0][name].get_xml_node())

    def add_clock(self, name: str, num_pins: int):
        if self.num_pb == 1:
            self._pins[0][name] = _Pin(name= name, type="clock", num_pins=num_pins)

            self._graph.add_node(self._pins[0][name].get_pins())
            self._graph.add_edge(self.name, self._pins[0][name].get_pins())
        else:
            for ii in range (0, self.num_pb):
                self._pins[ii][name] = _Pin(name=name, type="clock", num_pins=num_pins)

                for pin in self._pins[ii][name]._get_pins_indiv((0, num_pins - 1)):
                    self._graph.add_node(pin)

        self.root.append(self._pins[0][name].get_xml_node())

    def add_mode(self, mode: Mode):
        if mode.name in self._modes:
            raise ValueError("Mode with this name already exists")
        if "default" in self._modes:
            raise ValueError("Cannot add modes to complex block with default mode")

        self._modes[mode.name] = mode

        self.root.append(mode.to_elem())

        self._graph.add_nodes_from(mode.get_graph().nodes)
        self._graph.add_edges_from(mode.get_graph().edges)
    
    def add_direct_connection(self,
                            input_list: list[str], 
                            output_list: list[str],
                            name: Optional[str] = None):
        if name == None:
            name = "direct" + str(self.num_dc)
            self.num_dc += 1

        # if len(input_list) != len(output_list):
        #     raise ValueError("Direct connections must map 1:1 between inputs and outputs")

        elems = {"name": name}

        if len(input_list) == 1:
            elems["input"] = input_list[0]
            elems["output"] = output_list[0]
        else:
            elems["input"] = " ".join(input_list)
            elems["output"] = " ".join(output_list)

        ET.SubElement(self._interconnect, "direct", elems)


    #lz TODO need to graph this somehow (oh wait we use the individual get methods from pin)
    def add_complete_connection(self,
                                inputs: list[str],
                                outputs: list[str],
                                name: Optional[str] = None):
        
        if name == None:
            name = "complete" + str(self.num_cc)
            self.num_cc += 1
        
        self._graph.add_node(name)
        input_string_list = []
        output_string_list = []

        # for pin_list in inputs:
        #     if len(pin_list) == 1:
        #         input_string_list.append(pin_list[0])
        #     else:
        #         input_string_list.append(pin_list[0][:-1] + ":" + str(int(pin_list[0][-2]) + len(pin_list) - 1) + "]")

        #     for pin in pin_list:
        #         self._graph.add_edge(name, pin)

        # for pin_list in outputs:
        #     if len(pin_list) == 1:
        #         output_string_list.append(pin_list[0])
        #     else:
        #         output_string_list.append(pin_list[0][:-1] + ":" + str(int(pin_list[0][-2]) + len(pin_list) - 1) + "]")

        #     for pin in pin_list:
        #         self._graph.add_edge(name, pin)

        ET.SubElement(self._interconnect, "complete", {"name": name, "input": " ".join(inputs), "output": " ".join(outputs)})

    def add_mux_connection(self,
                           input_list: list[str],
                           output: str,
                           name: Optional[str] = None):
        if name == None:
            name = "mux" + str(self.num_mux)
            self.num_mux += 1

        # self._graph.add_node(name)
        # self._graph.add_edge(name, output)

        # for pin in input_list:
        #     self._graph.add_edge(name, pin)

        elems = {"name": name, "input": " ".join(input_list), "output": output}

        # if len(input_list) == 1:
        #     elems["input"] = input_list[0]
        # else:
        #     elems["input"] = input_list[0][:-1] + ":" + str(int(input_list[0][-2]) + len(input_list) - 1) + "]"

        ET.SubElement(self._interconnect, "mux", elems)
