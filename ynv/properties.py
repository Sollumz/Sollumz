import bpy
from bpy.types import (
    Object,
    Mesh,
    WindowManager,
    PropertyGroup,
    ShaderNode,
)
from bpy.props import (
    BoolProperty,
    BoolVectorProperty,
    IntProperty,
    FloatProperty,
    FloatVectorProperty,
    EnumProperty,
    PointerProperty,
)
import bmesh
from collections.abc import Iterator
from enum import IntEnum
from ..tools.blenderhelper import tag_redraw
from .navmesh_attributes import (
    mesh_get_navmesh_poly_attributes,
    mesh_set_navmesh_poly_attributes,
    NavPolyAttributes,
    mesh_get_navmesh_edge_attributes,
    mesh_set_navmesh_edge_attributes,
    NavEdgeAttributes,
)
from . import navmesh_material


class NavCoverType(IntEnum):
    LOW_WALL = 0
    LOW_WALL_TO_LEFT = 1
    LOW_WALL_TO_RIGHT = 2
    WALL_TO_LEFT = 3
    WALL_TO_RIGHT = 4
    WALL_TO_NEITHER = 5


NavCoverTypeEnumItems = tuple((enum.name, label, desc, enum.value) for enum, label, desc in (
    (NavCoverType.LOW_WALL, "Low Wall", "Behind low wall, can only shoot over the top"),
    (NavCoverType.LOW_WALL_TO_LEFT, "Low Wall To Left", "Behind low wall corner, can shoot over the top and to the right"),
    (NavCoverType.LOW_WALL_TO_RIGHT, "Low Wall To Right", "Behind low wall corner, can shoot over the top and to the left"),
    (NavCoverType.WALL_TO_LEFT, "Wall To Left", "Behind high wall corner, can only shoot to the right"),
    (NavCoverType.WALL_TO_RIGHT, "Wall To Right", "Behind high wall corner, can only shoot to the left"),
    (NavCoverType.WALL_TO_NEITHER, "Wall To Neither", "Behind thin high wall, can shoot to either the left or right sides"),
))


class NavCoverPointProps(PropertyGroup):
    cover_type: EnumProperty(name="Type", items=NavCoverTypeEnumItems, default=NavCoverType.LOW_WALL.name)
    disabled: BoolProperty(name="Disabled", default=False)

    def get_raw_int(self) -> int:
        cover_type_int = NavCoverType[self.cover_type].value
        disabled_int = 0x8 if self.disabled else 0
        return cover_type_int | disabled_int

    def set_raw_int(self, value):
        cover_type_int = value & 0x7
        if cover_type_int <= 5:
            self.cover_type = NavCoverType(cover_type_int).name
        else:
            # in case of corrupted out-of-range values, default to low-wall
            self.cover_type = NavCoverType.LOW_WALL.name
        self.disabled = (value & 0x8) != 0


class NavLinkType(IntEnum):
    CLIMB_LADDER = 1
    DESCEND_LADDER = 2
    CLIMB_OBJECT = 3


NavLinkTypeEnumItems = tuple((enum.name, label, desc, enum.value) for enum, label, desc in (
    (NavLinkType.CLIMB_LADDER, "Climb Ladder", "Link from the bottom of a ladder to the top"),
    (NavLinkType.DESCEND_LADDER, "Descend Ladder", "Link from the top of a ladder to the bottom"),
    (NavLinkType.CLIMB_OBJECT, "Climb Object", "Link for a climbable object"),
))


class NavLinkProps(PropertyGroup):
    link_type: EnumProperty(name="Type", items=NavLinkTypeEnumItems, default=NavLinkType.CLIMB_LADDER.name)
    heading: FloatProperty(name="Heading", subtype="ANGLE", unit="ROTATION")
    poly_from: IntProperty(name="Poly From")
    poly_to: IntProperty(name="Poly To")


def _edge_attr_getter(attr_name: str):
    def fn(self):
        return getattr(self.active_edge_attributes, attr_name)

    return fn


def _edge_attr_setter(attr_name: str):
    def fn(self, value):
        mesh = self.mesh
        for selected_edge in self.selected_edges:
            attrs = mesh_get_navmesh_edge_attributes(mesh, selected_edge)
            setattr(attrs, attr_name, value)
            mesh_set_navmesh_edge_attributes(mesh, selected_edge, attrs)

        active_edge = self.active_edge
        attrs = mesh_get_navmesh_edge_attributes(mesh, active_edge)
        setattr(attrs, attr_name, value)
        mesh_set_navmesh_edge_attributes(mesh, active_edge, attrs)

        mesh.update_tag()
        tag_redraw(bpy.context, space_type="VIEW_3D", region_type="WINDOW")

    return fn


def EdgeIntAttr(name: str, attr_name: str, min: int, max: int):
    return IntProperty(
        name=name,
        get=_edge_attr_getter(attr_name), set=_edge_attr_setter(attr_name),
        min=min, max=max,
    )


class NavMeshEdgeAccessor(PropertyGroup):
    """Property group to allow to access navmesh edge attributes from the UI."""

    @property
    def mesh(self) -> Mesh:
        assert self.id_data is not None and self.id_data.id_type == "MESH"
        return self.id_data

    @property
    def active_edge(self) -> int:
        mesh = self.mesh
        if mesh.is_editmode:
            bm = bmesh.from_edit_mesh(mesh)
            bm.edges.index_update()
            return bm.select_history.active.index if bm.select_mode == {"EDGE"} and bm.select_history.active else 0
        else:
            return 0

    @property
    def selected_edges(self) -> Iterator[int]:
        mesh = self.mesh
        active_edge = self.active_edge
        if mesh.is_editmode:
            bm = bmesh.from_edit_mesh(mesh)
            bm.edges.index_update()
            for edge in bm.edges:
                if edge.index != active_edge and edge.select:
                    yield edge.index
        else:
            # if not in edit mode, don't return anything
            pass

    @property
    def active_edge_attributes(self) -> NavEdgeAttributes:
        return mesh_get_navmesh_edge_attributes(self.mesh, self.active_edge)

    data00: EdgeIntAttr("Data 0-0", "data00", min=0, max=0xFFFF)
    data01: EdgeIntAttr("Data 0-1", "data01", min=0, max=0xFFFF)
    data10: EdgeIntAttr("Data 1-0", "data10", min=0, max=0xFFFF)
    data11: EdgeIntAttr("Data 1-1", "data11", min=0, max=0xFFFF)
    adjacent_poly_area: EdgeIntAttr("Adjacent Poly Area", "adjacent_poly_area", min=0, max=0xFFFF)
    adjacent_poly_index: EdgeIntAttr("Adjacent Poly Index", "adjacent_poly_index", min=0, max=0xFFFF)


# Helper functions for NavMeshPolyAccessor
def _attr_getter(attr_name: str):
    def fn(self):
        return getattr(self.active_poly_attributes, attr_name)

    return fn


def _attr_setter(attr_name: str):
    def fn(self, value):
        mesh = self.mesh
        for selected_poly in self.selected_polys:
            attrs = mesh_get_navmesh_poly_attributes(mesh, selected_poly)
            setattr(attrs, attr_name, value)
            mesh_set_navmesh_poly_attributes(mesh, selected_poly, attrs)

        active_poly = self.active_poly
        attrs = mesh_get_navmesh_poly_attributes(mesh, active_poly)
        setattr(attrs, attr_name, value)
        mesh_set_navmesh_poly_attributes(mesh, active_poly, attrs)

        mesh.update_tag()
        tag_redraw(bpy.context, space_type="VIEW_3D", region_type="WINDOW")

    return fn


def BoolAttr(name: str, attr_name: str):
    return BoolProperty(
        name=name,
        get=_attr_getter(attr_name), set=_attr_setter(attr_name),
    )


def IntAttr(name: str, attr_name: str, min: int, max: int):
    return IntProperty(
        name=name,
        get=_attr_getter(attr_name), set=_attr_setter(attr_name),
        min=min, max=max,
    )


def BoolVectorAttr(name: str, attr_name: str, size: int):
    return BoolVectorProperty(
        name=name,
        size=size,
        get=_attr_getter(attr_name), set=_attr_setter(attr_name),
    )


class NavMeshPolyAccessor(PropertyGroup):
    """Property group to allow to access navmesh polygon attributes from the UI."""

    @property
    def mesh(self) -> Mesh:
        assert self.id_data is not None and self.id_data.id_type == "MESH"
        return self.id_data

    @property
    def active_poly(self) -> int:
        mesh = self.mesh
        if mesh.is_editmode:
            bm = bmesh.from_edit_mesh(mesh)
            bm.faces.index_update()
            return bm.faces.active.index
        else:
            return mesh.polygons.active

    @property
    def selected_polys(self) -> Iterator[int]:
        mesh = self.mesh
        active_poly = self.active_poly
        if mesh.is_editmode:
            bm = bmesh.from_edit_mesh(mesh)
            bm.faces.index_update()
            for face in bm.faces:
                if face.index != active_poly and face.select:
                    yield face.index
        else:
            for poly in mesh.polygons:
                if poly.index != active_poly and poly.select:
                    yield poly.index

    @property
    def active_poly_attributes(self) -> NavPolyAttributes:
        return mesh_get_navmesh_poly_attributes(self.mesh, self.active_poly)

    is_small: BoolAttr("Small", "is_small")
    is_large: BoolAttr("Large", "is_large")
    is_pavement: BoolAttr("Pavement", "is_pavement")
    is_in_shelter: BoolAttr("In Shelter", "is_in_shelter")
    is_too_steep_to_walk_on: BoolAttr("Too Steep To Walk On", "is_too_steep_to_walk_on")
    is_water: BoolAttr("Water", "is_water")
    is_near_car_node: BoolAttr("Near Car Node", "is_near_car_node")
    is_interior: BoolAttr("Interior", "is_interior")
    is_isolated: BoolAttr("Isolated", "is_isolated")
    is_network_spawn_candidate: BoolAttr("Network Spawn Candidate", "is_network_spawn_candidate")
    is_road: BoolAttr("Road", "is_road")
    lies_along_edge: BoolAttr("Lies Along Edge", "lies_along_edge")
    is_train_track: BoolAttr("Train Track", "is_train_track")
    is_shallow_water: BoolAttr("Shallow Water", "is_shallow_water")
    cover_directions: BoolVectorAttr("Cover Directions", "cover_directions", size=8)
    audio_reverb_size: IntAttr("Audio Reverb Size", "audio_reverb_size", min=0, max=3)
    audio_reverb_wet: IntAttr("Audio Reverb Wet", "audio_reverb_wet", min=0, max=3)
    ped_density: IntAttr("Ped Density", "ped_density", min=0, max=7)
    is_dlc_stitch: BoolAttr("DLC Stitch", "is_dlc_stitch")


class NavMeshPolyRender(PropertyGroup):
    @property
    def mesh(self) -> Mesh:
        assert self.id_data is not None and self.id_data.id_type == "MESH"
        return self.id_data

    def get_node(self, name: str) -> ShaderNode:
        mesh = self.mesh
        node_tree = mesh.materials[0].node_tree
        return node_tree.nodes[name]


def _define_poly_render_flag_properties(flag: navmesh_material.FlagRenderInfo):
    def _toggle_getter(self: NavMeshPolyRender) -> bool:
        return self.get_node(flag.toggle_name).outputs[0].default_value != 0

    def _toggle_setter(self: NavMeshPolyRender, value: bool):
        self.get_node(flag.toggle_name).outputs[0].default_value = 1.0 if value else 0.0

    def _color_getter(self: NavMeshPolyRender) -> tuple[float, float, float]:
        node = self.get_node(flag.color_name)
        return tuple(node.inputs[i].default_value for i in range(3))

    def _color_setter(self: NavMeshPolyRender, value: tuple[float, float, float]):
        node = self.get_node(flag.color_name)
        for i in range(3):
            node.inputs[i].default_value = value[i]

    NavMeshPolyRender.__annotations__[flag.toggle_name] = BoolProperty(
        name=flag.toggle_name,
        get=_toggle_getter,
        set=_toggle_setter,
    )
    NavMeshPolyRender.__annotations__[flag.color_name] = FloatVectorProperty(
        name=flag.color_name, size=3, subtype="COLOR", min=0.0, max=1.0,
        get=_color_getter,
        set=_color_setter,
    )


def _define_poly_render_value_properties(val: navmesh_material.ValueRenderInfo):
    def _toggle_getter(self: NavMeshPolyRender) -> bool:
        return self.get_node(val.toggle_name).outputs[0].default_value != 0

    def _toggle_setter(self: NavMeshPolyRender, value: bool):
        self.get_node(val.toggle_name).outputs[0].default_value = 1.0 if value else 0.0

    def _color_min_getter(self: NavMeshPolyRender) -> tuple[float, float, float]:
        node = self.get_node(val.color_min_name)
        return tuple(node.inputs[i].default_value for i in range(3))

    def _color_min_setter(self: NavMeshPolyRender, value: tuple[float, float, float]):
        node = self.get_node(val.color_min_name)
        for i in range(3):
            node.inputs[i].default_value = value[i]

    def _color_max_getter(self: NavMeshPolyRender) -> tuple[float, float, float]:
        node = self.get_node(val.color_max_name)
        return tuple(node.inputs[i].default_value for i in range(3))

    def _color_max_setter(self: NavMeshPolyRender, value: tuple[float, float, float]):
        node = self.get_node(val.color_max_name)
        for i in range(3):
            node.inputs[i].default_value = value[i]

    NavMeshPolyRender.__annotations__[val.toggle_name] = BoolProperty(
        name=val.toggle_name,
        get=_toggle_getter,
        set=_toggle_setter,
    )
    NavMeshPolyRender.__annotations__[val.color_min_name] = FloatVectorProperty(
        name=val.color_min_name, size=3, subtype="COLOR", min=0.0, max=1.0,
        get=_color_min_getter,
        set=_color_min_setter,
    )
    NavMeshPolyRender.__annotations__[val.color_max_name] = FloatVectorProperty(
        name=val.color_max_name, size=3, subtype="COLOR", min=0.0, max=1.0,
        get=_color_max_getter,
        set=_color_max_setter,
    )


for flag in navmesh_material.ALL_FLAGS:
    _define_poly_render_flag_properties(flag)
for val in navmesh_material.ALL_VALUES:
    _define_poly_render_value_properties(val)


def register():
    Object.sz_nav_cover_point = PointerProperty(type=NavCoverPointProps)
    Object.sz_nav_link = PointerProperty(type=NavLinkProps)
    Mesh.sz_navmesh_poly_access = PointerProperty(type=NavMeshPolyAccessor)
    Mesh.sz_navmesh_edge_access = PointerProperty(type=NavMeshEdgeAccessor)
    Mesh.sz_navmesh_poly_render = PointerProperty(type=NavMeshPolyRender)

    WindowManager.sz_ui_nav_view_bounds = BoolProperty(
        name="Display Grid Bounds", description="Display the navigation mesh map grid bounds on the 3D Viewport",
        default=False
    )


def unregister():
    del Object.sz_nav_cover_point
    del Object.sz_nav_link
    del Mesh.sz_navmesh_poly_access
    del Mesh.sz_navmesh_edge_access
    del Mesh.sz_navmesh_poly_render
    del WindowManager.sz_ui_nav_view_bounds
