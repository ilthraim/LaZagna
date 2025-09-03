"""
VTR Architecture Python Builder
--------------------------------

A fluent, high-level Python API for generating Verilog-to-Routing (VTR/VPR)
architecture XML files.

Highlights
- Covers major sections: models, tiles, layout, device, switches, segments,
  complexblocklist (pb_types, modes, interconnect), pinlocations, fc, etc.
- Fluent chainable builders with sensible defaults.
- Outputs nicely formatted XML.

Usage (quick taste)
-------------------
from vtr_arch_builder import Arch

arch = (Arch()
  .models()
    .model("io")
      .input_port("outpad")
      .output_port("inpad").up()
    .done()
  .tiles()
    .tile("io", area=1)
      .sub_tile("io", capacity=8)
        .equivalent_site("io").up().up()
    .done()
  .layout().fixed("grid141", width=141, height=141)
    .perimeter(type="io", priority=100)
    .corners(type="EMPTY", priority=101)
    .fill(type="clb", priority=10)
    .done().done()
  .device()
    .sizing(R_minW_nmos=8926, R_minW_pmos=16067)
    .area(grid_logic_tile_area=0)
    .switch_block(type="wilton", fs=3)
    .connection_block(input_switch_name="ipin_cblock")
    .done()
  .switches()
    .switch(name="L4_driver", type="tristate", R=0.0, Cin=0.0, Cout=0.0, Tdel="185e-12")
    .done()
)

xml_text = arch.to_string()
arch.save("generated_arch.xml")
"""
from __future__ import annotations
import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import Optional, Iterable, Dict, Any, List

# ------------------------------ helpers ------------------------------

def _attrs(**kwargs) -> Dict[str, str]:
    return {k: str(v) for k, v in kwargs.items() if v is not None}

class _Node:
    def __init__(self, elem: ET.Element, parent: Optional["_Node"] = None):
        self.elem = elem
        self._parent = parent

    # Fluent traversal
    def up(self):
        """Return to parent builder in the chain."""
        return self._parent or self

    # Utilities
    def _add(self, tag: str, **attrs) -> "_Node":
        child = ET.SubElement(self.elem, tag, _attrs(**attrs))
        return _Node(child, self)

    def text(self, value: str) -> "_Node":
        self.elem.text = value
        return self

# ------------------------------ root ------------------------------

class Arch:
    def __init__(self):
        self.root = ET.Element("architecture")
        # top-level containers (order preserved):
        self._models = ET.SubElement(self.root, "models")
        self._tiles = ET.SubElement(self.root, "tiles")
        self._layout = ET.SubElement(self.root, "layout")
        self._device = ET.SubElement(self.root, "device")
        self._switchlist = ET.SubElement(self.root, "switchlist")
        self._segmentlist = ET.SubElement(self.root, "segmentlist")
        self._complexblocklist = ET.SubElement(self.root, "complexblocklist")

    # sections
    def models(self) -> "ModelsBuilder":
        return ModelsBuilder(_Node(self._models, None), self)

    def tiles(self) -> "TilesBuilder":
        return TilesBuilder(_Node(self._tiles, None), self)

    def layout(self) -> "LayoutBuilder":
        return LayoutBuilder(_Node(self._layout, None), self)

    def device(self) -> "DeviceBuilder":
        return DeviceBuilder(_Node(self._device, None), self)

    def switches(self) -> "SwitchListBuilder":
        return SwitchListBuilder(_Node(self._switchlist, None), self)

    def segments(self) -> "SegmentListBuilder":
        return SegmentListBuilder(_Node(self._segmentlist, None), self)

    def complexblocks(self) -> "ComplexBlockListBuilder":
        return ComplexBlockListBuilder(_Node(self._complexblocklist, None), self)

    # export
    def to_string(self, indent: str = "  ") -> str:
        rough = ET.tostring(self.root, encoding="utf-8")
        return minidom.parseString(rough).toprettyxml(indent=indent)

    def save(self, filename: str):
        with open(filename, "w", encoding="utf-8") as f:
            f.write(self.to_string())

# ------------------------------ models ------------------------------

class ModelsBuilder:
    def __init__(self, node: _Node, arch: Arch):
        self.n = node
        self._arch = arch

    def model(self, name: str) -> "ModelBuilder":
        return ModelBuilder(self.n._add("model", name=name), self)

    def done(self) -> Arch:
        return self._arch

class ModelBuilder:
    def __init__(self, node: _Node, parent: ModelsBuilder):
        self.n = node
        self._parent = parent
        self._inputs = ET.SubElement(self.n.elem, "input_ports")
        self._outputs = ET.SubElement(self.n.elem, "output_ports")

    def input_port(self, name: str, **attrs) -> "ModelBuilder":
        ET.SubElement(self._inputs, "port", _attrs(name=name, **attrs))
        return self

    def output_port(self, name: str, **attrs) -> "ModelBuilder":
        ET.SubElement(self._outputs, "port", _attrs(name=name, **attrs))
        return self

    def up(self) -> ModelsBuilder:
        return self._parent

# ------------------------------ tiles ------------------------------

class TilesBuilder:
    def __init__(self, node: _Node, arch: Arch):
        self.n = node
        self._arch = arch

    def tile(self, name: str, *, area: float = 0, height: Optional[int] = None, width: Optional[int] = None) -> "TileBuilder":
        return TileBuilder(self.n._add("tile", name=name, area=area, height=height, width=width), self)

    def done(self) -> Arch:
        return self._arch

class TileBuilder:
    def __init__(self, node: _Node, parent: TilesBuilder):
        self.n = node
        self._parent = parent

    # pin/clock declarations for tile (VPR 9+ style)
    def input(self, name: str, num_pins: int = 1) -> "TileBuilder":
        ET.SubElement(self.n.elem, "input", _attrs(name=name, num_pins=num_pins))
        return self

    def output(self, name: str, num_pins: int = 1) -> "TileBuilder":
        ET.SubElement(self.n.elem, "output", _attrs(name=name, num_pins=num_pins))
        return self

    def clock(self, name: str, num_pins: int = 1) -> "TileBuilder":
        ET.SubElement(self.n.elem, "clock", _attrs(name=name, num_pins=num_pins))
        return self

    def sub_tile(self, name: str, *, capacity: int = 1, height: Optional[int] = None) -> "SubTileBuilder":
        st = ET.SubElement(self.n.elem, "sub_tile", _attrs(name=name, capacity=capacity, height=height))
        return SubTileBuilder(_Node(st, self), self)

    def pinlocations(self, pattern: str, **attrs) -> "TileBuilder":
        pl = ET.SubElement(self.n.elem, "pinlocations", _attrs(pattern=pattern, **attrs))
        # The actual pin mapping text may be provided via .text() using the returned wrapper if needed
        return self

    def fc(self, default_in_type: str, default_in_val: str, default_out_type: str, default_out_val: str) -> "TileBuilder":
        ET.SubElement(self.n.elem, "fc", _attrs(
            in_type=default_in_type, in_val=default_in_val,
            out_type=default_out_type, out_val=default_out_val
        ))
        return self

    def fc_override(self, **attrs) -> "TileBuilder":
        ET.SubElement(self.n.elem, "fc_override", _attrs(**attrs))
        return self

    def up(self) -> TilesBuilder:
        return self._parent

class SubTileBuilder:
    def __init__(self, node: _Node, parent: TileBuilder):
        self.n = node
        self._parent = parent
        self._equiv = ET.SubElement(self.n.elem, "equivalent_sites")

    def equivalent_site(self, pb_type: str) -> "SubTileBuilder":
        ET.SubElement(self._equiv, "site", _attrs(pb_type=pb_type))
        return self

    def up(self) -> TileBuilder:
        return self._parent

# ------------------------------ layout ------------------------------

class LayoutBuilder:
    def __init__(self, node: _Node, arch: Arch):
        self.n = node
        self._arch = arch
        self._current = None  # type: Optional[_Node]

    def fixed(self, name: str, *, width: int, height: int) -> "FixedLayoutBuilder":
        return FixedLayoutBuilder(self.n._add("fixed_layout", name=name, width=width, height=height), self)

    def auto(self, name: str, *, aspect_ratio: float = 1.0, **attrs) -> "AutoLayoutBuilder":
        return AutoLayoutBuilder(self.n._add("auto_layout", name=name, aspect_ratio=aspect_ratio, **attrs), self)

    def done(self) -> Arch:
        return self._arch

class FixedLayoutBuilder:
    def __init__(self, node: _Node, parent: LayoutBuilder):
        self.n = node
        self._parent = parent

    def perimeter(self, **attrs) -> "FixedLayoutBuilder":
        ET.SubElement(self.n.elem, "perimeter", _attrs(**attrs))
        return self

    def corners(self, **attrs) -> "FixedLayoutBuilder":
        ET.SubElement(self.n.elem, "corners", _attrs(**attrs))
        return self

    def fill(self, **attrs) -> "FixedLayoutBuilder":
        ET.SubElement(self.n.elem, "fill", _attrs(**attrs))
        return self

    def col(self, **attrs) -> "FixedLayoutBuilder":
        ET.SubElement(self.n.elem, "col", _attrs(**attrs))
        return self

    def row(self, **attrs) -> "FixedLayoutBuilder":
        ET.SubElement(self.n.elem, "row", _attrs(**attrs))
        return self

    def done(self) -> LayoutBuilder:
        return self._parent

class AutoLayoutBuilder:
    def __init__(self, node: _Node, parent: LayoutBuilder):
        self.n = node
        self._parent = parent

    def region(self, **attrs) -> "AutoLayoutBuilder":
        ET.SubElement(self.n.elem, "region", _attrs(**attrs))
        return self

    def done(self) -> LayoutBuilder:
        return self._parent

# ------------------------------ device ------------------------------

class DeviceBuilder:
    def __init__(self, node: _Node, arch: Arch):
        self.n = node
        self._arch = arch


    def sizing(self, **attrs) -> "DeviceBuilder":
        ET.SubElement(self.n.elem, "sizing", _attrs(**attrs))
        return self


    def area(self, **attrs) -> "DeviceBuilder":
        ET.SubElement(self.n.elem, "area", _attrs(**attrs))
        return self


    def chan_width_distr(self,
                        x_distr: str, x_peak: float,
                        y_distr: str, y_peak: float,
                        x_width: Optional[float] = None,
                        x_xpeak: Optional[float] = None,
                        x_dc: Optional[float] = None,
                        y_width: Optional[float] = None,
                        y_xpeak: Optional[float] = None,
                        y_dc: Optional[float] = None
                        ) -> "DeviceBuilder":
        cwd = ET.SubElement(self.n.elem, "chan_width_distr")
        x_attrs = {"distr": x_distr, "peak": str(x_peak)}
        if x_distr in ("gaussian", "pulse", "delta"):
            if x_width is not None: x_attrs["width"] = str(x_width)
            if x_xpeak is not None: x_attrs["xpeak"] = str(x_xpeak)
            if x_dc is not None: x_attrs["dc"] = str(x_dc)
        ET.SubElement(cwd, "x", x_attrs)


        y_attrs = {"distr": y_distr, "peak": str(y_peak)}
        if y_distr in ("gaussian", "pulse", "delta"):
            if y_width is not None: y_attrs["width"] = str(y_width)
            if y_xpeak is not None: y_attrs["xpeak"] = str(y_xpeak)
            if y_dc is not None: y_attrs["dc"] = str(y_dc)
        ET.SubElement(cwd, "y", y_attrs)
        return self


    def switch_block(self, **attrs) -> "DeviceBuilder":
        ET.SubElement(self.n.elem, "switch_block", _attrs(**attrs))
        return self


    def connection_block(self, **attrs) -> "DeviceBuilder":
        ET.SubElement(self.n.elem, "connection_block", _attrs(**attrs))
        return self

    def default_fc(self, in_type: str, in_val: float, out_type: str, out_val: float) -> "DeviceBuilder":
        if ((in_type == "frac") | (in_type == "abs")):
            if ((out_type == "frac") | (out_type == "abs")):
                ET.SubElement(self.n.elem, "default_fc", {"in_type": in_type, "in_val": in_val, "out_type": out_type, "out_val": out_val})
        return self

    def done(self) -> Arch:
        return self._arch

# ------------------------------ switchlist ------------------------------

class SwitchListBuilder:
    def __init__(self, node: _Node, arch: Arch):
        self.n = node
        self._arch = arch

    def switch(self, *, name: str, type: str, R: float, Cin: float, Cout: float, Tdel: str, **extra) -> "SwitchListBuilder":
        ET.SubElement(self.n.elem, "switch", _attrs(name=name, type=type, R=R, Cin=Cin, Cout=Cout, Tdel=Tdel, **extra))
        return self

    def done(self) -> Arch:
        return self._arch

# ------------------------------ segmentlist ------------------------------

class SegmentListBuilder:
    def __init__(self, node: _Node, arch: Arch):
        self.n = node
        self._arch = arch

    def segment(self, name: str, *, freq: float, length: int, type: str, Rmetal: float, Cmetal: float,
                sb_pattern: str, cb_pattern: str, mux_name: Optional[str] = None, **attrs) -> "SegmentListBuilder":
        seg = ET.SubElement(self.n.elem, "segment", _attrs(name=name, freq=freq, length=length, type=type, Rmetal=Rmetal, Cmetal=Cmetal, **attrs))
        if mux_name:
            ET.SubElement(seg, "mux", _attrs(name=mux_name))
        sb = ET.SubElement(seg, "sb", _attrs(type="pattern"))
        sb.text = sb_pattern
        cb = ET.SubElement(seg, "cb", _attrs(type="pattern"))
        cb.text = cb_pattern
        return self

    def done(self) -> Arch:
        return self._arch

# ------------------------------ complexblocklist / pb_types ------------------------------

class ComplexBlockListBuilder:
    def __init__(self, node: _Node, arch: Arch):
        self.n = node
        self._arch = arch

    def pb_type(self, name: str, **attrs) -> "PbTypeBuilder":
        return PbTypeBuilder(self.n._add("pb_type", name=name, **attrs), self)

    def done(self) -> Arch:
        return self._arch

class PbTypeBuilder:
    def __init__(self, node: _Node, parent: ComplexBlockListBuilder | ModeBuilder | None):
        self.n = node
        self._parent = parent

    # ports
    def input(self, name: str, num_pins: int = 1, **attrs) -> "PbTypeBuilder":
        ET.SubElement(self.n.elem, "input", _attrs(name=name, num_pins=num_pins, **attrs))
        return self

    def output(self, name: str, num_pins: int = 1, **attrs) -> "PbTypeBuilder":
        ET.SubElement(self.n.elem, "output", _attrs(name=name, num_pins=num_pins, **attrs))
        return self

    def clock(self, name: str, num_pins: int = 1, **attrs) -> "PbTypeBuilder":
        ET.SubElement(self.n.elem, "clock", _attrs(name=name, num_pins=num_pins, **attrs))
        return self

    # timing annotations
    def T_setup(self, port: str, clock: str, value: str, **attrs) -> "PbTypeBuilder":
        ET.SubElement(self.n.elem, "T_setup", _attrs(port=port, clock=clock, value=value, **attrs))
        return self

    def T_hold(self, port: str, clock: str, value: str, **attrs) -> "PbTypeBuilder":
        ET.SubElement(self.n.elem, "T_hold", _attrs(port=port, clock=clock, value=value, **attrs))
        return self

    def T_clock_to_Q(self, port: str, clock: str, max: Optional[str] = None, min: Optional[str] = None, **attrs) -> "PbTypeBuilder":
        ET.SubElement(self.n.elem, "T_clock_to_Q", _attrs(port=port, clock=clock, max=max, min=min, **attrs))
        return self

    # modes and children
    def mode(self, name: str, **attrs) -> "ModeBuilder":
        return ModeBuilder(self.n._add("mode", name=name, **attrs), self)

    def pb_type(self, name: str,  num_pb: int = 1, **attrs) -> "PbTypeBuilder":
        # nested child pb_type
        return PbTypeBuilder(self.n._add("pb_type", name=name, num_pb=num_pb, **attrs), self)

    def interconnect(self) -> "InterconnectBuilder":
        return InterconnectBuilder(self.n._add("interconnect"), self)

    # pack patterns
    def pack_pattern(self, name: str) -> "PbTypeBuilder":
        ET.SubElement(self.n.elem, "pack_pattern", _attrs(name=name))
        return self

    # metadata / annotations convenience
    def annotation(self, key: str, value: str) -> "PbTypeBuilder":
        ann = ET.SubElement(self.n.elem, "annotation")
        ET.SubElement(ann, "metadata", _attrs(key=key, value=value))
        return self

    def up(self):
        return self._parent

class ModeBuilder:
    def __init__(self, node: _Node, parent: PbTypeBuilder):
        self.n = node
        self._parent = parent

    def pb_type(self, name: str, **attrs) -> PbTypeBuilder:
        return PbTypeBuilder(self.n._add("pb_type", name=name, **attrs), self)

    def interconnect(self) -> "InterconnectBuilder":
        return InterconnectBuilder(self.n._add("interconnect"), self)

    def up(self) -> PbTypeBuilder:
        return self._parent

class InterconnectBuilder:
    def __init__(self, node: _Node, parent: PbTypeBuilder | ModeBuilder):
        self.n = node
        self._parent = parent

    # connection types
    def direct(self, name: str, input: str, output: str, **attrs) -> "InterconnectBuilder":
        ET.SubElement(self.n.elem, "direct", _attrs(name=name, input=input, output=output, **attrs))
        return self

    def mux(self, name: str, input: str, output: str, **attrs) -> "InterconnectBuilder":
        ET.SubElement(self.n.elem, "mux", _attrs(name=name, input=input, output=output, **attrs))
        return self

    def complete(self, name: str, input: str, output: str, **attrs) -> "InterconnectBuilder":
        ET.SubElement(self.n.elem, "complete", _attrs(name=name, input=input, output=output, **attrs))
        return self

    # delay annotations
    def delay_constant(self, in_port: str, out_port: str, max: Optional[str] = None, min: Optional[str] = None) -> "InterconnectBuilder":
        ET.SubElement(self.n.elem, "delay_constant", _attrs(in_port=in_port, out_port=out_port, max=max, min=min))
        return self

    def C_constant(self, in_port: str, out_port: str, C: str) -> "InterconnectBuilder":
        ET.SubElement(self.n.elem, "C_constant", _attrs(in_port=in_port, out_port=out_port, C=C))
        return self

    def up(self):
        return self._parent

# ------------------------------ end of module ------------------------------
