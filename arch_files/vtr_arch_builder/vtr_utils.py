from __future__ import annotations
import xml.etree.ElementTree as ET
import networkx as nx
from typing import Optional, Dict, List, Literal
from xml.dom import minidom


#MARK: Base Classes
class _Node:
    def __init__(self):
        self.root = ET.Element("")

    def to_elem(self) -> ET.Element:
        return self.root
    
    
class _Pin():
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

        self.name = name
        self.type = type
        self.equivalence = equivalence
        self.num_pins = num_pins

        if is_non_clock_global:
            self.is_non_clock_global = is_non_clock_global
    
    def get_pins(self, index: int | tuple[int, int] = 0) -> str:
        if isinstance(index, int):
            if index < 0 or index >= self.num_pins:
                raise ValueError("Index out of range")
            return self.name + "[" + str(index) + "]"
        elif isinstance(index, tuple) and len(index) == 2:
            if index[0] < 0 or index[1] >= self.num_pins or index[1] < index[0]:
                raise ValueError("Index out of range")
            return self.name + "[" + str(index[0]) + ":" + str(index[1]) + "]"
        else:
            raise ValueError("Index must be an integer or a tuple of two integers")

    def _get_pins_indiv(self, index: int | tuple[int, int] = 0) -> list[str]:
        if isinstance(index, int):
            if index < 0 or index >= self.num_pins:
                raise ValueError("Index out of range")
            return [self.name + "[" + str(index) + "]"]
        elif isinstance(index, tuple) and len(index) == 2:
            if index[0] < 0 or index[1] >= self.num_pins or index[1] < index[0]:
                raise ValueError("Index out of range")
            return [self.name + "[" + str(i) + "]" for i in range(index[0], index[1] + 1)]
        else:
            raise ValueError("Index must be an integer or a tuple of two integers")
        
    
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