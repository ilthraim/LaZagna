from __future__ import annotations
import xml.etree.ElementTree as ET
from typing import Literal, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from .vtr_blocks import ComplexBlock, Primitive

#MARK: Base Classes
class _Node:
    def __init__(self):
        self._root = ET.Element("")

    def to_elem(self) -> ET.Element:
        return self._root
    
class _Pin():
    def __init__(self,
                 parent: _Pins,
                 index: int):
        self._parent = parent
        self._index = index

class _Pins():
    def __init__(self,
                 parent: ComplexBlock | Primitive,
                 name: str,
                 type: Literal["input", "output", "clock"], 
                 num_pins: int = 1,
                 equivalence: Literal["none", "full", "instance"] = "none",
                 is_non_clock_global: bool = False):
        if equivalence == "instance" and type != "output":
            raise ValueError("Equivalence of instance is only valid for output pins")
        if is_non_clock_global and type != "input":
            raise ValueError("is_non_clock_global is only valid for input pins")
        self._parent = parent
        self._name = name
        self._type = type
        self._equivalence = equivalence
        self._num_pins = num_pins
        self._pins = [_Pin(self, i) for i in range(num_pins)]

        if is_non_clock_global:
            self._is_non_clock_global = is_non_clock_global
    
    def get_xml_node(self) -> ET.Element:
        attrs = {"name": self._name, "num_pins": str(self._num_pins)}
        if self._equivalence != "none":
            attrs["equivalent"] = self._equivalence
        if self._type == "input" and hasattr(self, "_is_non_clock_global"):
            attrs["is_non_clock_global"] = "true"
        return ET.Element(self._type, attrs)
    