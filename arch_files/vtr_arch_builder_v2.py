from __future__ import annotations
import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import Optional, Iterable, Dict, Any, List



class Arch:
    def __init__(self):
        self.root = ET.Element("architecture")
        self._models = ET.SubElement(self.root, "models")
        self._tiles = ET.SubElement(self.root, "tiles")
        self._layout = ET.SubElement(self.root, "layout")
        self._device = ET.SubElement(self.root, "device")
        self._switchlist = ET.SubElement(self.root, "switchlist")
        self._segmentlist = ET.SubElement(self.root, "segmentlist")
        self._complexblocklist = ET.SubElement(self.root, "complexblocklist")

    def addModel(self, model: Model):
        #ET.append(self._models, model.getElem())
        self._models.append(model.getElem())

    def addTile(self, tile: Tile):
        self._tiles.append(tile.getElem())

    def to_string(self, indent: str = "  ") -> str:
        rough = ET.tostring(self.root, encoding="utf-8")
        return minidom.parseString(rough).toprettyxml(indent=indent)

    def save(self, filename: str):
        with open(filename, "w", encoding="utf-8") as f:
            f.write(self.to_string())

class Model:
    def __init__(self, name: str, prune: str = "false"):
        self.root = ET.Element("model", {"name": name, "never_prune": prune})

    #THERE HAS TO BE A BETTER WAY

    def addInputPort(self, name: str, is_clock: str = "0", clock: Optional[str] = None, comb_ports: Optional[tuple] = None):
        if (clock != None):
            if (comb_ports != None):
                ET.SubElement(ET.SubElement(self.root, "input_ports"), "port", {"name": name, "is_clock": is_clock, "clock": clock, "combinational_sink_ports": ' '.join(comb_ports)})
            else:
                ET.SubElement(ET.SubElement(self.root, "input_ports"), "port", {"name": name, "is_clock": is_clock, "clock": clock})
        else:
            if (comb_ports != None):
                ET.SubElement(ET.SubElement(self.root, "input_ports"), "port", {"name": name, "is_clock": is_clock, "combinational_sink_ports": ' '.join(comb_ports)})
            else:
                ET.SubElement(ET.SubElement(self.root, "input_ports"), "port", {"name": name, "is_clock": is_clock})

    def addOutputPort(self, name: str, is_clock: str = "0", clock: Optional[str] = None, comb_ports: Optional[tuple] = None):
        if (clock != None):
            if (comb_ports != None):
                ET.SubElement(ET.SubElement(self.root, "output_ports"), "port", {"name": name, "is_clock": is_clock, "clock": clock, "combinational_sink_ports": ' '.join(comb_ports)})
            else:
                ET.SubElement(ET.SubElement(self.root, "output_ports"), "port", {"name": name, "is_clock": is_clock, "clock": clock})
        else:
            if (comb_ports != None):
                ET.SubElement(ET.SubElement(self.root, "output_ports"), "port", {"name": name, "is_clock": is_clock, "combinational_sink_ports": ' '.join(comb_ports)})
            else:
                ET.SubElement(ET.SubElement(self.root, "output_ports"), "port", {"name": name, "is_clock": is_clock})

    def getElem(self) -> ET.Element:
        return self.root
    
class Tile:
    def __init__(self, name: str, width: str = "1", height: str = "1", area: Optional[str] = None):
        if area != None:
            self.root = ET.Element("tile", {"name": name, "width": width, "height": height, "area":area})
        else:
            self.root = ET.Element("tile", {"name": name, "width": width, "height": height})

    def getElem(self) -> ET.Element:
        return self.root
    
class SubTile:
    def __init__(self, name: str, capacity: str = "1"):
        self.root = ET.Element("sub_tile", {"name": name, "capacity": capacity})

    def addInput(self, name: str, num_pins: str, equivalent: str = "none", is_global: Optional[str] = None):
        if is_global != None:
            ET.SubElement(self.root, "input", {"name": name, "num_pins": num_pins, "equivalent": equivalent, "is_non_clock_global": is_global})
        else:
            ET.SubElement(self.root, "input", {"name": name, "num_pins": num_pins, "equivalent": equivalent})

    def addOutput(self, name: str, num_pins: str, equivalent: str = "none"):
        ET.SubElement(self.root, "output", {"name": name, "num_pins": num_pins, "equivalent": equivalent})

    def addClock(self, name: str, num_pins: str, equivalent: str = "none"):
        ET.SubElement(self.root, "clock", {"name": name, "num_pins": num_pins, "equivalent": equivalent})

    #lz TODO add equivalent sites - should be able to snag em from the complex blocks list

    def addFc(self, in_type: str, in_val: str, out_type: str, out_val: str):
        ET.SubElement(self.root, "fc", {"in_type": in_type, "in_val": in_val, "out_type": out_type, "out_val":out_val})

    def getElem(self) -> ET.Element:
        return self.root

############################################


arch = Arch()

############ MODELS ###################

ioModel = Model("io")
ioModel.addInputPort(name="we", clock="0")
ioModel.addOutputPort(name="addr", is_clock="1", clock=None, comb_ports=("test", "test2"))

arch.addModel(ioModel)

arch.addModel(Model("spram",  "true"))

############# TILES ##############

tile = Tile("clb", area="53894")

arch.addTile(tile)

############ PRINT ###################

arch.save("my_arch2.xml")
print(arch.to_string()[:4000]) 

        