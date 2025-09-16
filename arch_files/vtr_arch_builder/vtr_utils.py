from __future__ import annotations
import xml.etree.ElementTree as ET
from typing import Literal
from dataclasses import dataclass
from .vtr_blocks import Primitive, ComplexBlock


#MARK: Base Classes
class _Node:
    def __init__(self):
        self.root = ET.Element("")

    def to_elem(self) -> ET.Element:
        return self.root

@dataclass(frozen=True)
class _Pin():
    pins: _Pins
    index: int

    def __str__(self) -> str:
        return f"{self.pins._name}[{self.index}]"
    
    def __repr__(self) -> str:
        return f"_Pin({self.pins._name}[{self.index}])"

class _PinList(list):
    def __init__(self, pins: list[_Pin]):
        super().__init__(pins)

    def __str__(self) -> str:
        return f"{self[0].pins._name}[{self[0].index}:{self[-1].index}]"

class _Pins():
    def __init__(self,
                 name: str,
                 type: Literal["input", "output", "clock"], 
                 num_pins: int = 1,
                 equivalence: Literal["none", "full", "instance"] = "none",
                 is_non_clock_global: bool = False):
        if equivalence == "instance" and type != "output":
            raise ValueError("Equivalence of instance is only valid for output pins")
        if is_non_clock_global and type != "input":
            raise ValueError("is_non_clock_global is only valid for input pins")
        self._name = name
        self._type = type
        self._equivalence = equivalence
        self._num_pins = num_pins
        self._pins = [_Pin(self, i) for i in range(num_pins)]

        if is_non_clock_global:
            self._is_non_clock_global = is_non_clock_global

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
            return _PinList(self._pins[start:stop:step])
        return self._pins[index]

    def __setitem__(self, index, value):
        pass

    def __len__(self):
        return self._num_pins

    def __iter__(self):
        return iter(self._pins)
    
    def get_xml_node(self) -> ET.Element:
        attrs = {"name": self._name, "num_pins": str(self._num_pins)}
        if self._equivalence != "none":
            attrs["equivalent"] = self._equivalence
        if self._type == "input" and hasattr(self, "_is_non_clock_global"):
            attrs["is_non_clock_global"] = "true"
        return ET.Element(self._type, attrs)
    
    def __str__(self) -> str:
        """Return VTR-style pin specification for all pins"""
        if self._num_pins == 1:
            return f"{self._name}[0]"
        else:
            return f"{self._name}[0:{self._num_pins-1}]"
    
    def __repr__(self) -> str:
        return f"_Pins(name='{self._name}', type='{self._type}', num_pins={self._num_pins})"