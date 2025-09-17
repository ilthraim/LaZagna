from __future__ import annotations
import keyword
import networkx as nx
from typing import TYPE_CHECKING, Optional, List, Literal
import xml.etree.ElementTree as ET
from .vtr_utils import _Node, _PinList, _Pins, _Pin

if TYPE_CHECKING:
    from .vtr_core import Model

#MARK: Mode
class Mode(_Node):
    def __init__(self,
                 name: str,
                 disable_packing: bool = False):
        self._root = ET.Element("mode", {"name": name, "disable_packing": str("true" if disable_packing else "false")})
        self._name = name
        self._contents: List[ComplexBlock | Primitive] = []
        self._interconnect = ET.SubElement(self._root, "interconnect")
        self._graph = nx.Graph()
        self.num_dc = 0
        self.num_cc = 0
        self.num_mux = 0

    #lz TODO error check inputs and outputs
    def add_direct_connection(self,
                              inputs: list[_PinList | _Pins], 
                              outputs: list[_PinList | _Pins],
                              name: Optional[str] = None):
        if name == None:
            name = "direct" + str(self.num_dc)
            self.num_dc += 1

        elems = {
            "name": name,
            "input": " ".join(str(x) for x in inputs),
            "output": " ".join(str(x) for x in outputs)
        }

        ET.SubElement(self._interconnect, "direct", elems)

        self._graph.add_edges_from((inp, out) for inp in inputs for out in outputs)


    #lz TODO need to graph this somehow (oh wait we use the individual get methods from pin)
    def add_complete_connection(self,
                                inputs: list[_PinList | _Pins],
                                outputs: list[_PinList | _Pins],
                                name: Optional[str] = None):
        
        if name == None:
            name = "complete" + str(self.num_cc)
            self.num_cc += 1
        
        elems = {
            "name": name,
            "input": " ".join(str(x) for x in inputs),
            "output": " ".join(str(x) for x in outputs)
        }
        ET.SubElement(self._interconnect, "complete", elems)

        self._graph.add_node(name)
        self._graph.add_edges_from((inp, name) for inp in inputs)
        self._graph.add_edges_from((name, out) for out in outputs)

    #lz TODO wait did we decide that mux output has to be width 1
    def add_mux_connection(self,
                           inputs: list[_PinList | _Pins],
                           output: _Pin | _Pins,
                           name: Optional[str] = None):
        if isinstance(output, _Pins):
            if len(output) != 1:
                raise ValueError("Mux output must be a single pin")

        if name == None:
            name = "mux" + str(self.num_mux)
            self.num_mux += 1

        elems = {
            "name": name,
            "input": " ".join(str(x) for x in inputs),
            "output": str(output)
        }
        ET.SubElement(self._interconnect, "mux", elems)

        self._graph.add_node(name)
        self._graph.add_edges_from((inp, name) for inp in inputs)
        self._graph.add_edge(name, output)

    def add_block(self, block: ComplexBlock | Primitive):
        if block in self._contents:
            raise ValueError("Block with name " + block._name + " already exists in this mode")
        self._contents.append(block)
        self._root.append(block.to_elem())
        nx.compose(self._graph, block._graph)

#MARK: Primitive

class _Primitive_Node():
    def __init__(self, parent: Primitive, index: int):
        self.parent = parent
        self.index = index
        self.nodeName = f"{self.parent._name}[{self.index}]"

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
        self._name = name
        self._primitive_nodes = [_Primitive_Node(self, i) for i in range(num_pb)]

        self._graph = nx.Graph()
        self._graph.add_nodes_from(self._primitive_nodes)

        self._type = type
        self._num_pb = num_pb
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
        if hasattr(self, name):
            raise ValueError("Pin with name " + name + " already exists in this primitive")

        for prim_node in self._primitive_nodes:
            prim_node._add_pins(name, _Pins(prim_node, name=name, type="input", num_pins=num_pins))
            self._graph.add_nodes_from(getattr(prim_node, name)._pins)
            self._graph.add_edges_from(zip([prim_node] * num_pins, getattr(prim_node, name)._pins))

        setattr(self, name, [getattr(prim_node, name) for prim_node in self._primitive_nodes])

        attrs = {"name": name, "num_pins": str(num_pins)}
        if port_class is not None:
            attrs["port_class"] = port_class
        ET.SubElement(self._root, "input", attrs)

    def _add_output(self, name: str, num_pins: int, port_class: Optional[str] = None):
        if hasattr(self, name):
            raise ValueError("Pin with name " + name + " already exists in this primitive")

        for prim_node in self._primitive_nodes:
            prim_node._add_pins(name, _Pins(prim_node, name=name, type="output", num_pins=num_pins))
            self._graph.add_nodes_from(getattr(prim_node, name)._pins)
            self._graph.add_edges_from(zip([prim_node] * num_pins, getattr(prim_node, name)._pins))

        setattr(self, name, [getattr(prim_node, name) for prim_node in self._primitive_nodes])

        attrs = {"name": name, "num_pins": str(num_pins)}
        if port_class is not None:
            attrs["port_class"] = port_class
        ET.SubElement(self._root, "output", attrs)

    def _add_clock(self, name: str, num_pins: int, port_class: Optional[str] = None):
        if hasattr(self, name):
            raise ValueError("Pin with name " + name + " already exists in this primitive")

        for prim_node in self._primitive_nodes:
            prim_node._add_pins(name, _Pins(prim_node, name=name, type="clock", num_pins=num_pins))
            self._graph.add_nodes_from(getattr(prim_node, name)._pins)
            self._graph.add_edges_from(zip([prim_node] * num_pins, getattr(prim_node, name)._pins))

        setattr(self, name, [getattr(prim_node, name) for prim_node in self._primitive_nodes])

        attrs = {"name": name, "num_pins": str(num_pins)}
        if port_class is not None:
            attrs["port_class"] = port_class
        ET.SubElement(self._root, "clock", attrs)

    def get_graph(self):
        return self._graph
       
#MARK: ComplexBlock
class _ComplexBlock_Node():
    def __init__(self, parent: ComplexBlock, index: int):
        self.parent = parent
        self.index = index
        self.nodeName = f"{self.parent._name}[{self.index}]"

    def _add_pins(self, name: str, pins: _Pins):
        setattr(self, name, pins)

class _ComplexBlock_Node_Helper(list):
    def __init__(self, parent: ComplexBlock, pinlist: list[_Pins], name: str):
        super().__init__(pinlist)
        self._parent = parent
        self._name = name

    def __getitem__(self, index):
        return_list = []
        if isinstance(index, slice):
            if index.start is None or index.stop is None:
                raise IndexError("Slice must have both start and stop defined")
            if index.start < 0 or index.stop < 0:
                raise IndexError("Negative indices are not supported")
            if index.step is not None:
                raise IndexError("Slice step is not supported")
            if index.start > index.stop:
                raise IndexError("Slice step is not supported")
            else:
                start = index.start
                stop = index.stop + 1
            for pb in self._parent._pb_nodes:
                return_list.append(getattr(pb, self._name)[start:stop]) # type: ignore
            return return_list

        for pb in self._parent._pb_nodes:
            return_list.append(getattr(pb, self._name)[index]) # type: ignore
        return return_list
    
class _ComplexBlock_Node_Slice_Helper():
    def __init__(self, parent: ComplexBlock, start: int, stop: int):
        self._parent = parent
        self._start = start
        self._stop = stop

    def __getattr__(self, name):
        return [getattr(pb, name) for pb in self._parent._pb_nodes[self._start:self._stop]]

class ComplexBlock(_Node):
    def __init__(self, name: str, num_pb:int = 1):
        self._name = name
        self._num_pb = num_pb
        self._root = ET.Element("pb_type", {"name": name, "num_pb": str(num_pb)})
        self._modes: List[Mode] = []
        self._contents: List[ComplexBlock | Primitive] = []
        self._interconnect = ET.SubElement(self._root, "interconnect")
        self._graph = nx.Graph()
        self.num_dc = 0
        self.num_cc = 0
        self.num_mux = 0

        self._pb_nodes = [_ComplexBlock_Node(self, i) for i in range(num_pb)]

    def add_block(self, block: ComplexBlock | Primitive):
        if len(self._modes) > 0:
            raise ValueError("Blocks can only be added to complex blocks with default mode")

        if block in self._contents:
            raise ValueError("Block with name " + block._name + " already exists in this mode")
        self._contents.append(block)
        self._root.append(block.to_elem())
        self._graph = nx.compose(self._graph, block._graph)

    def add_input(self, name:str, num_pins: int, equivalence: Literal["none", "full", "instance"] = "none", is_non_clock_global: bool = False):
        if keyword.iskeyword(name):
            raise ValueError("Pin name cannot be a reserved keyword: " + name)

        if hasattr(self, name):
            raise ValueError("Pin with name " + name + " already exists in this complex block")

        #setattr(self, name, _Pins(name=name, type="input", num_pins=num_pins, equivalence=equivalence, is_non_clock_global=is_non_clock_global))

        for pb in self._pb_nodes:
            pb._add_pins(name, _Pins(pb, name=name, type="input", num_pins=num_pins, equivalence=equivalence, is_non_clock_global=is_non_clock_global))
            self._graph.add_nodes_from(getattr(pb, name)._pins)

        setattr(self, name, _ComplexBlock_Node_Helper(self, [getattr(pb, name) for pb in self._pb_nodes], name))

        #lz TODO gotta make the parent tag optional
        self._root.append(_Pins(self._pb_nodes[0], name=name, type="input", num_pins=num_pins, equivalence=equivalence, is_non_clock_global=is_non_clock_global).get_xml_node())

    def add_output(self, name: str, num_pins: int):
        if keyword.iskeyword(name):
            raise ValueError("Pin name cannot be a reserved keyword: " + name)

        if hasattr(self, name):
            raise ValueError("Pin with name " + name + " already exists in this complex block")

        for pb in self._pb_nodes:
            pb._add_pins(name, _Pins(pb, name=name, type="output", num_pins=num_pins))
            self._graph.add_nodes_from(getattr(pb, name)._pins)

        setattr(self, name, [getattr(pb, name) for pb in self._pb_nodes])

        self._root.append(getattr(self, name).get_xml_node())

    def add_clock(self, name: str, num_pins: int):
        if keyword.iskeyword(name):
            raise ValueError("Pin name cannot be a reserved keyword: " + name)

        if hasattr(self, name):
            raise ValueError("Pin with name " + name + " already exists in this complex block")

        for pb in self._pb_nodes:
            pb._add_pins(name, _Pins(pb, name=name, type="clock", num_pins=num_pins))
            self._graph.add_nodes_from(getattr(pb, name)._pins)

        setattr(self, name, [getattr(pb, name) for pb in self._pb_nodes])

        self._root.append(getattr(self, name).get_xml_node())


#lz TODO add mode to graph
    def add_mode(self, mode: Mode):
        if len(self._contents) > 0:
            raise ValueError("Modes can only be added to complex blocks with no blocks")

        if mode in self._modes:
            raise ValueError("Mode with this name already exists")

        self._modes.append(mode)

        self._root.append(mode.to_elem())

        #self._graph.add_nodes_from(mode.get_graph().nodes)
        #self._graph.add_edges_from(mode.get_graph().edges)

    

    def add_direct_connection(self,
                            inputs: _PinList | _Pins | list[_Pins], 
                            outputs: _PinList | _Pins | list[_Pins],
                            name: Optional[str] = None):
        if len(self._modes) > 0:
            raise ValueError("Connections can only be added to complex blocks with no modes")

        if name == None:
            name = "direct" + str(self.num_dc)
            self.num_dc += 1
        
        full_inputs = []

        if not isinstance(inputs, (_PinList, _Pins)):
            for inp in inputs:
                full_inputs.extend(inp)
        else:
            full_inputs = inputs

        full_outputs = []

        if not isinstance(outputs, (_PinList, _Pins)):
            for out in outputs:
                full_outputs.extend(out)
        else:
            full_outputs = outputs

        self._graph.add_edges_from(zip(full_inputs, full_outputs))

        print(full_inputs, full_outputs)

        for ipin, opin in zip(full_inputs, full_outputs):
            elems = {
                "name": name,
                "input": ipin.nodeName,
                "output": opin.nodeName
            }
            ET.SubElement(self._interconnect, "direct", elems)
        #self._graph.add_edges_from((inp, out) for inp in inputs for out in outputs)

    #lz TODO need to graph this somehow (oh wait we use the individual get methods from pin)
    def add_complete_connection(self,
                                inputs: list[_PinList | _Pins],
                                outputs: list[_PinList | _Pins],
                                name: Optional[str] = None):
        
        if name == None:
            name = "complete" + str(self.num_cc)
            self.num_cc += 1
        
        elems = {
            "name": name,
            "input": " ".join(str(x) for x in inputs),
            "output": " ".join(str(x) for x in outputs)
        }
        ET.SubElement(self._interconnect, "complete", elems)

        self._graph.add_node(name)
        self._graph.add_edges_from((inp, name) for inp in inputs)
        self._graph.add_edges_from((name, out) for out in outputs)

    def add_mux_connection(self,
                           inputs: list[str],
                           output: str,
                           name: Optional[str] = None):
        if name == None:
            name = "mux" + str(self.num_mux)
            self.num_mux += 1

        elems = {
            "name": name,
            "input": " ".join(str(x) for x in inputs),
            "output": str(output)
        }
        ET.SubElement(self._interconnect, "mux", elems)
        
        self._graph.add_node(name)
        self._graph.add_edges_from((inp, name) for inp in inputs)
        self._graph.add_edge(name, output)

    def get_graph(self):
        return self._graph
    
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
                stop = index.stop - 1 if index.stop != 0 else self._num_pb
                step = -1
            else:
                start = index.start
                stop = index.stop + 1
                step = 1
            return _ComplexBlock_Node_Slice_Helper(self, start, stop)
        return self._pb_nodes[index]
