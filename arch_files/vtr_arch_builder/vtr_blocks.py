import networkx as nx
from typing import Optional, Dict, List, Literal
import xml.etree.ElementTree as ET
from .vtr_utils import _Node, _Pin
from .vtr_core import Model


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

        self.root.append(block.to_elem())

        #lz TODO do we need to add the block to the xml here?
    


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
        for prim in range(0, num_pb):
            self._graph.add_node(self.name + "[" + str(prim) + "]")

        #inputs, outputs, clocks are stored by name and number of pins
        self._pins: List[Dict[str, _Pin]] = [{} for _ in range(num_pb)]

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

    #lz TODO need to change pins function to not add the name of the block to the return because its stored in the pin object
    #lz TODO need to figure out how this interacts with adding connections (do I return a list of strings or a single string?)

    def pins(self, name:str, index: Optional[int | tuple[int, int]] = None, block_index: Optional[int | tuple[int, int]] = None) -> str:
        if index == None:
            if block_index == None:
                return self.name + "." + name
            elif isinstance(block_index, int):
                if block_index < 0 or block_index >= self.num_pb:
                    raise ValueError("Block index out of range")
                return self.name + "[" + str(block_index) + "]." + name
            elif isinstance(block_index, tuple) and len(block_index) == 2:
                if block_index[0] < 0 or block_index[1] >= self.num_pb or block_index[1] < block_index[0]:
                    raise ValueError("Block index out of range")
                return self.name + "[" + str(block_index[0]) + ":" + str(block_index[1]) + "]." + name
            else:
                raise ValueError("Block index must be an integer or a tuple of two integers")
        elif isinstance(index, int):
            if block_index == None:
                return self.name + "." + name + "[" + str(index) + "]"
            elif isinstance(block_index, int):
                if block_index < 0 or block_index >= self.num_pb:
                    raise ValueError("Block index out of range")
                return self.name + "[" + str(block_index) + "]." + name + "[" + str(index) + "]"
            elif isinstance(block_index, tuple) and len(block_index) == 2:
                if block_index[0] < 0 or block_index[1] >= self.num_pb or block_index[1] < block_index[0]:
                    raise ValueError("Block index out of range")
                return self.name + "[" + str(block_index[0]) + ":" + str(block_index[1]) + "]." + name + "[" + str(index) + "]"
            else:
                raise ValueError("Block index must be an integer or a tuple of two integers")
        elif isinstance(index, tuple) and len(index) == 2:
            if block_index == None:
                return self.name + "." + name + "[" + str(index[0]) + ":" + str(index[1]) + "]"
            elif isinstance(block_index, int):
                if block_index < 0 or block_index >= self.num_pb:
                    raise ValueError("Block index out of range")
                return self.name + "[" + str(block_index) + "]." + name + "[" + str(index[0]) + ":" + str(index[1]) + "]"
            elif isinstance(block_index, tuple) and len(block_index) == 2:
                if block_index[0] < 0 or block_index[1] >= self.num_pb or block_index[1] < block_index[0]:
                    raise ValueError("Block index out of range")
                return self.name + "[" + str(block_index[0]) + ":" + str(block_index[1]) + "]." + name + "[" + str(index[0]) + ":" + str(index[1]) + "]"
            else:
                raise ValueError("Block index must be an integer or a tuple of two integers")
        else:
            raise ValueError("Index must be an integer or a tuple of two integers")

    def get_graph(self) -> nx.Graph:
        return self._graph

    def _input(self, num_pb: int = 1):
        self.elems["blif_model"] = ".input"

        self._add_output("in", 1, num_pb)

    def _output(self, num_pb: int = 1):
        self.elems["blif_model"] = ".output"

        self._add_input("out", 1, num_pb)

    def _lut(self, num_pins: int, num_pb: int = 1):
        self.elems["blif_model"] = ".names"
        self.elems["class"] = "lut"

        self._add_input("in", num_pins, num_pb, "lut_in")
        self._add_output("out", 1, num_pb, "lut_out")

    def _ff(self, num_pb: int = 1):
        self.elems["blif_model"] = ".latch"
        self.elems["class"] = "flipflop"

        self._add_input(name = "D",num_pins =  1,num_pb=num_pb, port_class= "D")
        self._add_output(name = "Q",num_pins= 1, num_pb=num_pb, port_class= "Q")
        self._add_clock(name="clock",num_pins= 1, num_pb=num_pb, port_class="clock")

    #lz TODO memory
    def _memory(self, blif_model: Model, num_pb: int = 1):
        self.elems["blif_model"] = ".subckt " + blif_model.name
        self.elems["class"] = "memory"

    def _custom(self, blif_model: Model, num_pb: int = 1):
        self.elems["blif_model"] = ".subckt " + blif_model.name

        for port_name, value in blif_model.inputs.items():
            self._add_input(name=port_name, num_pins=value, num_pb=num_pb)
        for port_name, value in blif_model.outputs.items():
            self._add_output(name=port_name, num_pins=value, num_pb=num_pb)
        for port_name, value in blif_model.clocks.items():
            self._add_clock(name=port_name, num_pins=value, num_pb=num_pb)

    def _add_input(self, name: str, num_pins: int, num_pb: int, port_class: Optional[str] = None):
        if num_pb == 1:
            self._pins[0][name] = _Pin(name=name, type="input", num_pins=num_pins)

            self._graph.add_node(self._pins[0][name].get_pins())
            self._graph.add_edge(self.name, self._pins[0][name].get_pins())
        else:
            for ii in range (0, num_pb):
                self._pins[ii][name] = _Pin(name=name, type="input", num_pins=num_pins)

                for pin in self._pins[ii][name]._get_pins_indiv((0, num_pins)):
                    self._graph.add_node(pin)
                    self._graph.add_edge(self.name, pin)

        if port_class != None:
            ET.SubElement(self.root, "input", {"name": name, "num_pins": str(num_pins), "port_class": port_class})
        else:
            ET.SubElement(self.root, "input", {"name": name, "num_pins": str(num_pins)})

    def _add_output(self, name: str, num_pins: int, num_pb:int, port_class: Optional[str] = None):
        if num_pb == 1:
            self._pins[0][name] = _Pin(name=name, type="output", num_pins=num_pins)

            self._graph.add_node(self._pins[0][name].get_pins())
            self._graph.add_edge(self.name, self._pins[0][name].get_pins())
        else:
            for ii in range (0, num_pb):
                self._pins[ii][name] = _Pin(name=name, type="output", num_pins=num_pins)

                for pin in self._pins[ii][name]._get_pins_indiv((0, num_pins)):
                    self._graph.add_node(pin)
                    self._graph.add_edge(self.name, pin)

        if port_class != None:
            ET.SubElement(self.root, "output", {"name": name, "num_pins": str(num_pins), "port_class": port_class})
        else:
            ET.SubElement(self.root, "output", {"name": name, "num_pins": str(num_pins)})

    def _add_clock(self, name: str, num_pins: int, num_pb:int, port_class: Optional[str] = None):
        if num_pb == 1:
            self._pins[0][name] = _Pin(name=name, type="clock", num_pins=num_pins)

            self._graph.add_node(self._pins[0][name].get_pins())
            self._graph.add_edge(self.name, self._pins[0][name].get_pins())
        else:
            for ii in range (0, num_pb):
                self._pins[ii][name] = _Pin(name=name, type="clock", num_pins=num_pins)

                for pin in self._pins[ii][name]._get_pins_indiv((0, num_pins)):
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
        self._pins: List[Dict[str, _Pin]] = [{} for _ in range(num_pb)]
        self.num_pb = num_pb
        self._interconnect = ET.SubElement(self.root, "interconnect")
        self.num_dc: int = 0
        self.num_cc: int = 0
        self.num_mux: int = 0

    def add_block(self, block: ComplexBlock | Primitive):
        if len(self._modes) not in [0, 1] or (len(self._modes) == 1 and list(self._modes.values())[0].name != "default"):
            raise ValueError("Blocks can only be added to complex blocks with default mode")

        if len(self._modes) == 0:
            self._modes["default"] = Mode("default")
            self._modes["default"].add_block(block)
            self.root.append(block.to_elem())
        else:
            self._modes["default"].add_block(block)
            self.root.append(block.to_elem())

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

    def pins(self, name:str, index: Optional[int | tuple[int, int]] = None, block_index: Optional[int | tuple[int, int]] = None) -> str:
        if index == None:
            if block_index == None:
                return self.name + "." + name
            elif isinstance(block_index, int):
                if block_index < 0 or block_index >= self.num_pb:
                    raise ValueError("Block index out of range")
                return self.name + "[" + str(block_index) + "]." + name
            elif isinstance(block_index, tuple) and len(block_index) == 2:
                if block_index[0] < 0 or block_index[1] >= self.num_pb or block_index[1] < block_index[0]:
                    raise ValueError("Block index out of range")
                return self.name + "[" + str(block_index[0]) + ":" + str(block_index[1]) + "]." + name
            else:
                raise ValueError("Block index must be an integer or a tuple of two integers")
        elif isinstance(index, int):
            if block_index == None:
                return self.name + "." + name + "[" + str(index) + "]"
            elif isinstance(block_index, int):
                if block_index < 0 or block_index >= self.num_pb:
                    raise ValueError("Block index out of range")
                return self.name + "[" + str(block_index) + "]." + name + "[" + str(index) + "]"
            elif isinstance(block_index, tuple) and len(block_index) == 2:
                if block_index[0] < 0 or block_index[1] >= self.num_pb or block_index[1] < block_index[0]:
                    raise ValueError("Block index out of range")
                return self.name + "[" + str(block_index[0]) + ":" + str(block_index[1]) + "]." + name + "[" + str(index) + "]"
            else:
                raise ValueError("Block index must be an integer or a tuple of two integers")
        elif isinstance(index, tuple) and len(index) == 2:
            if block_index == None:
                return self.name + "." + name + "[" + str(index[0]) + ":" + str(index[1]) + "]"
            elif isinstance(block_index, int):
                if block_index < 0 or block_index >= self.num_pb:
                    raise ValueError("Block index out of range")
                return self.name + "[" + str(block_index) + "]." + name + "[" + str(index[0]) + ":" + str(index[1]) + "]"
            elif isinstance(block_index, tuple) and len(block_index) == 2:
                if block_index[0] < 0 or block_index[1] >= self.num_pb or block_index[1] < block_index[0]:
                    raise ValueError("Block index out of range")
                return self.name + "[" + str(block_index[0]) + ":" + str(block_index[1]) + "]." + name + "[" + str(index[0]) + ":" + str(index[1]) + "]"
            else:
                raise ValueError("Block index must be an integer or a tuple of two integers")
        else:
            raise ValueError("Index must be an integer or a tuple of two integers")

    def get_graph(self) -> nx.Graph:
        return self._graph
    
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
