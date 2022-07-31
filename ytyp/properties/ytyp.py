import bpy
from ...tools.blenderhelper import get_children_recursive
from ...sollumz_properties import SollumType, items_from_enums, ArchetypeType, AssetType, TimeFlags
from ...tools.utils import get_list_item
from ..utils import get_selected_archetype
from .mlo import RoomProperties, PortalProperties, UnlinkedEntityProperties, TimecycleModifierProperties
from .flags import ArchetypeFlags, UnknownFlags


class ArchetypeProperties(bpy.types.PropertyGroup):
    def update_asset(self, context):
        if self.asset:
            self.asset_name = self.asset.name
            # Automatically determine asset type
            if self.asset.sollum_type == SollumType.BOUND_COMPOSITE:
                self.asset_type = AssetType.ASSETLESS
                self.drawable_dictionary = ""
                self.physics_dictionary = ""
                self.texture_dictionary = ""
            elif self.asset.sollum_type == SollumType.DRAWABLE:
                self.asset_type = AssetType.DRAWABLE
                # Check if in a drawable dictionary
                if self.asset.parent and hasattr(self.asset.parent, "sollum_type") and self.asset.parent.sollum_type == SollumType.DRAWABLE_DICTIONARY:
                    self.drawable_dictionary = self.asset.parent.name
            elif self.asset.sollum_type == SollumType.DRAWABLE_DICTIONARY:
                self.asset_type = AssetType.DRAWABLE_DICTIONARY
            elif self.asset.sollum_type == AssetType.FRAGMENT:
                self.asset_type = AssetType.FRAGMENT
            # Check for embedded collisions
            if self.asset_type in [AssetType.DRAWABLE, AssetType.FRAGMENT]:
                for child in get_children_recursive(self.asset):
                    if child.sollum_type == SollumType.BOUND_COMPOSITE:
                        self.physics_dictionary = self.asset_name
                    # Check for embedded textures
                    if child.sollum_type == SollumType.DRAWABLE_GEOMETRY:
                        for mat in child.data.materials:
                            if not mat.use_nodes:
                                continue
                            for node in mat.node_tree.nodes:
                                if isinstance(node, bpy.types.ShaderNodeTexImage):
                                    if node.texture_properties.embedded == True:
                                        self.texture_dictionary = self.asset_name
                                        break

    def new_portal(self):
        item = self.portals.add()
        self.portal_index = len(self.portals) - 1
        item.id = self.last_portal_id + 1
        self.last_portal_id = item.id
        selected_archetype = get_selected_archetype(bpy.context)
        if len(selected_archetype.rooms) > 0:
            room_id = selected_archetype.rooms[0].id
            item.room_to_id = room_id
            item.room_from_id = room_id
        return item

    def new_room(self):
        item = self.rooms.add()
        self.room_index = len(self.rooms) - 1
        item.name = f"Room.{self.room_index}"
        item.id = self.last_room_id + 1
        self.last_room_id = item.id
        return item

    bb_min: bpy.props.FloatVectorProperty(name="Bound Min")
    bb_max: bpy.props.FloatVectorProperty(name="Bound Max")
    bs_center: bpy.props.FloatVectorProperty(name="Bound Center")
    bs_radius: bpy.props.FloatProperty(name="Bound Radius")
    type: bpy.props.EnumProperty(
        items=items_from_enums(ArchetypeType), name="Type")
    lod_dist: bpy.props.FloatProperty(name="Lod Distance", default=100)
    flags: bpy.props.PointerProperty(
        type=ArchetypeFlags, name="Flags")
    special_attribute: bpy.props.IntProperty(name="Special Attribute")
    hd_texture_dist: bpy.props.FloatProperty(
        name="HD Texture Distance", default=100)
    name: bpy.props.StringProperty(name="Name")
    texture_dictionary: bpy.props.StringProperty(name="Texture Dictionary")
    clip_dictionary: bpy.props.StringProperty(name="Clip Dictionary")
    drawable_dictionary: bpy.props.StringProperty(name="Drawable Dictionary")
    physics_dictionary: bpy.props.StringProperty(
        name="Physics Dictionary")
    asset_type: bpy.props.EnumProperty(
        items=items_from_enums(AssetType), name="Asset Type")
    asset: bpy.props.PointerProperty(
        name="Asset", type=bpy.types.Object, update=update_asset)
    asset_name: bpy.props.StringProperty(
        name="Asset Name")
    # Time archetype
    time_flags: bpy.props.PointerProperty(type=TimeFlags, name="Time Flags")
    # Mlo archetype
    mlo_flags: bpy.props.PointerProperty(type=UnknownFlags, name="MLO Flags")
    rooms: bpy.props.CollectionProperty(type=RoomProperties, name="Rooms")
    portals: bpy.props.CollectionProperty(
        type=PortalProperties, name="Portals")
    entities: bpy.props.CollectionProperty(
        type=UnlinkedEntityProperties, name="Entities")
    timecycle_modifiers: bpy.props.CollectionProperty(
        type=TimecycleModifierProperties, name="Timecycle Modifiers")
    # Selected room index
    room_index: bpy.props.IntProperty(name="Room Index")
    # Selected portal index
    portal_index: bpy.props.IntProperty(name="Portal Index")
    # Unique portal id
    last_portal_id: bpy.props.IntProperty(name="")
    # Selected entity index
    entity_index: bpy.props.IntProperty(name="Entity Index")
    # Unique room id
    last_room_id: bpy.props.IntProperty(name="")
    # Selected timecycle modifier index
    tcm_index: bpy.props.IntProperty(
        name="Timecycle Modifier Index")

    @property
    def selected_room(self):
        return get_list_item(self.rooms, self.room_index)

    @property
    def selected_portal(self):
        return get_list_item(self.portals, self.portal_index)

    @property
    def selected_entity(self):
        return get_list_item(self.entities, self.entity_index)

    @property
    def selected_tcm(self):
        return get_list_item(self.timecycle_modifiers, self.tcm_index)


class CMapTypesProperties(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name")
    # extensions
    archetypes: bpy.props.CollectionProperty(
        type=ArchetypeProperties, name="Archetypes")
    # Selected archetype index
    archetype_index: bpy.props.IntProperty(
        name="Archetype Index")

    @property
    def selected_archetype(self):
        return get_list_item(self.archetypes, self.archetype_index)


def register():
    bpy.types.Scene.ytyps = bpy.props.CollectionProperty(
        type=CMapTypesProperties, name="YTYPs")
    bpy.types.Scene.ytyp_index = bpy.props.IntProperty(name="YTYP Index")
    bpy.types.Scene.show_room_gizmo = bpy.props.BoolProperty(
        name="Show Room Gizmo", default=True)
    bpy.types.Scene.show_portal_gizmo = bpy.props.BoolProperty(
        name="Show Portal Gizmo", default=True)

    bpy.types.Scene.create_archetype_type = bpy.props.EnumProperty(
        items=items_from_enums(ArchetypeType), name="Type")


def unregister():
    del bpy.types.Scene.ytyps
    del bpy.types.Scene.ytyp_index
    del bpy.types.Scene.show_room_gizmo
    del bpy.types.Scene.show_portal_gizmo
    del bpy.types.Scene.create_archetype_type
