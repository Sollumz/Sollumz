import bpy
from ..tools.utils import int_to_bool_list, flag_prop_to_list, flag_list_to_int
from ..sollumz_properties import items_from_enums, YmapElementType
from bpy.props import (EnumProperty, FloatProperty, PointerProperty, CollectionProperty,
                       StringProperty, IntProperty, FloatVectorProperty, BoolProperty)
from ..tools.utils import get_list_item
from enum import Enum


def update_uint_prop(self, context, var_name):
    """Work around for storing uint values as a Blender property (credits: CFox)"""
    try:
        int(getattr(self, var_name))
    except ValueError:
        setattr(self, var_name, '0')

    value = int(getattr(self, var_name))
    max_val = (2**32) - 1

    if value < 0:
        setattr(self, var_name, '0')
    elif value > max_val:
        setattr(self, var_name, str(max_val))


# TODO: why is FlagPropertyGroup duplicated here?
class FlagPropertyGroup:
    """Credits: Sollumz"""

    def update_flags_total(self, context):
        flags = int_to_bool_list(int(self.flags), size=2)
        for index, flag_name in enumerate(MapFlags.__annotations__):
            self.flags_toggle[flag_name] = flags[index]

    def update_flag(self, context):
        flags = flag_prop_to_list(self.__class__.__annotations__, self)
        obj = context.active_object
        if obj:
            obj.ymap_properties.flags = flag_list_to_int(flags)


class YmapModelOccluderProperties(bpy.types.PropertyGroup):
    name: StringProperty(name="Name", default="")
    flags: IntProperty(name="Flags", default=0)

class YmapBoxOcclProperties(bpy.types.PropertyGroup):
    name: StringProperty(name="Name", default="")


class YmapCarGeneratorProperties(bpy.types.PropertyGroup):
    car_model: StringProperty(name="CarModel", default="panto")
    flags: IntProperty(name="Flags", default=0)
    pop_group: StringProperty(name="PopGroup", default="")
    perpendicular_length: FloatProperty(
        name="PerpendicularLength", default=2.3)
    body_color_remap_1: IntProperty(name="BodyColorRemap1", default=-1)
    body_color_remap_2: IntProperty(name="BodyColorRemap2", default=-1)
    body_color_remap_3: IntProperty(name="BodyColorRemap3", default=-1)
    body_color_remap_4: IntProperty(name="BodyColorRemap4", default=-1)
    livery: IntProperty(name="Livery", default=-1)


class ContentFlagPropertyGroup:
    """Credits: Sollumz"""

    def update_flags_total(self, context):
        flags = int_to_bool_list(int(self.content_flags), size=11)
        for index, flag_name in enumerate(ContentFlags.__annotations__):
            self.content_flags_toggle[flag_name] = flags[index]

    def update_flag(self, context):
        flags = flag_prop_to_list(self.__class__.__annotations__, self)
        obj = context.active_object
        if obj:
            obj.ymap_properties.content_flags = flag_list_to_int(flags)


class MapFlags(bpy.types.PropertyGroup):
    script_loaded: bpy.props.BoolProperty(
        name="Script Loaded", update=FlagPropertyGroup.update_flag)
    has_lod: bpy.props.BoolProperty(
        name="LOD", update=FlagPropertyGroup.update_flag)


class ContentFlags(bpy.types.PropertyGroup):
    has_hd: BoolProperty(
        name="HD", update=ContentFlagPropertyGroup.update_flag)
    has_lod: BoolProperty(
        name="LOD", update=ContentFlagPropertyGroup.update_flag)
    has_slod2: BoolProperty(
        name="SLOD2", update=ContentFlagPropertyGroup.update_flag)
    has_int: BoolProperty(
        name="Interior", update=ContentFlagPropertyGroup.update_flag)
    has_slod: BoolProperty(
        name="SLOD", update=ContentFlagPropertyGroup.update_flag)
    has_occl: BoolProperty(
        name="Occlusion", update=ContentFlagPropertyGroup.update_flag)
    has_physics: BoolProperty(
        name="Physics", update=ContentFlagPropertyGroup.update_flag)
    has_lod_lights: BoolProperty(
        name="Lod Lights", update=ContentFlagPropertyGroup.update_flag)
    has_dis_lod_lights: BoolProperty(
        name="Distant Lod Lights", update=ContentFlagPropertyGroup.update_flag)
    has_critical: BoolProperty(
        name="Critical", update=ContentFlagPropertyGroup.update_flag)
    has_grass: BoolProperty(
        name="Grass", update=ContentFlagPropertyGroup.update_flag)


class YmapBlockProperties(bpy.types.PropertyGroup):
    version: StringProperty(name="Version", default='0', update=lambda self,
                            context: update_uint_prop(self, context, 'version'))
    flags: StringProperty(name="Flags", default='0', update=lambda self,
                          context: update_uint_prop(self, context, 'flags'))
    # TODO: Sync the name input with the object name?
    name: StringProperty(name="Name")
    exported_by: StringProperty(name="Exported By", default="Sollumz")
    owner: StringProperty(name="Owner")
    time: StringProperty(name="Time")


class EntityFlags(FlagPropertyGroup, bpy.types.PropertyGroup):
    size = 32
    flag1: bpy.props.BoolProperty(
        name="Allow full rotation", update=FlagPropertyGroup.update_flag)
    flag2: bpy.props.BoolProperty(
        name="Stream Low Priority", update=FlagPropertyGroup.update_flag)
    flag3: bpy.props.BoolProperty(
        name="Disable embedded collisions", update=FlagPropertyGroup.update_flag)
    flag4: bpy.props.BoolProperty(
        name="LOD in Parented YMAP", update=FlagPropertyGroup.update_flag)
    flag5: bpy.props.BoolProperty(
        name="LOD Adopt Me", update=FlagPropertyGroup.update_flag)
    flag6: bpy.props.BoolProperty(
        name="Static entity", update=FlagPropertyGroup.update_flag)
    flag7: bpy.props.BoolProperty(
        name="Interior LOD", update=FlagPropertyGroup.update_flag)
    flag8: bpy.props.BoolProperty(
        name="Unknown 8", update=FlagPropertyGroup.update_flag)
    flag9: bpy.props.BoolProperty(
        name="Unknown 9", update=FlagPropertyGroup.update_flag)
    flag10: bpy.props.BoolProperty(
        name="Unknown 10", update=FlagPropertyGroup.update_flag)
    flag11: bpy.props.BoolProperty(
        name="Unknown 11", update=FlagPropertyGroup.update_flag)
    flag12: bpy.props.BoolProperty(
        name="Unknown 12", update=FlagPropertyGroup.update_flag)
    flag13: bpy.props.BoolProperty(
        name="Unknown 13", update=FlagPropertyGroup.update_flag)
    flag14: bpy.props.BoolProperty(
        name="Unknown 14", update=FlagPropertyGroup.update_flag)
    flag15: bpy.props.BoolProperty(
        name="Unknown 15", update=FlagPropertyGroup.update_flag)
    flag16: bpy.props.BoolProperty(
        name="LOD Use Alt Fade", update=FlagPropertyGroup.update_flag)
    flag17: bpy.props.BoolProperty(
        name="Unused", update=FlagPropertyGroup.update_flag)
    flag18: bpy.props.BoolProperty(
        name="Does Not Touch Water", update=FlagPropertyGroup.update_flag)
    flag19: bpy.props.BoolProperty(name="Does Not Spawn Peds",
                                   update=FlagPropertyGroup.update_flag)
    flag20: bpy.props.BoolProperty(
        name="Cast Static Shadows", update=FlagPropertyGroup.update_flag)
    flag21: bpy.props.BoolProperty(
        name="Cast Dynamic Shadows", update=FlagPropertyGroup.update_flag)
    flag22: bpy.props.BoolProperty(
        name="Ignore Day Night Settings", update=FlagPropertyGroup.update_flag)
    flag23: bpy.props.BoolProperty(
        name="Disable shadow for entity", update=FlagPropertyGroup.update_flag)
    flag24: bpy.props.BoolProperty(
        name="Disable entity, shadow casted", update=FlagPropertyGroup.update_flag)
    flag25: bpy.props.BoolProperty(
        name="Dont Render In Reflections", update=FlagPropertyGroup.update_flag)
    flag26: bpy.props.BoolProperty(
        name="Only Render In Reflections", update=FlagPropertyGroup.update_flag)
    flag27: bpy.props.BoolProperty(
        name="Dont Render In Water Reflections", update=FlagPropertyGroup.update_flag)
    flag28: bpy.props.BoolProperty(
        name="Only Render In Water Reflections", update=FlagPropertyGroup.update_flag)
    flag29: bpy.props.BoolProperty(
        name="Dont Render In Mirror Reflections", update=FlagPropertyGroup.update_flag)
    flag30: bpy.props.BoolProperty(
        name="Only Render In Mirror Reflections", update=FlagPropertyGroup.update_flag)
    flag31: bpy.props.BoolProperty(
        name="Unknown 31", update=FlagPropertyGroup.update_flag)
    flag32: bpy.props.BoolProperty(
        name="Unknown 32", update=FlagPropertyGroup.update_flag)

#TODO: FIX DUPLICATED CODE
class EntityLodLevel(str, Enum):
    LODTYPES_DEPTH_HD = "sollumz_lodtypes_depth_hd"
    LODTYPES_DEPTH_LOD = "sollumz_lodtypes_depth_lod"
    LODTYPES_DEPTH_SLOD1 = "sollumz_lodtypes_depth_slod1"
    LODTYPES_DEPTH_SLOD2 = "sollumz_lodtypes_depth_slod2"
    LODTYPES_DEPTH_SLOD3 = "sollumz_lodtypes_depth_slod3"
    LODTYPES_DEPTH_SLOD4 = "sollumz_lodtypes_depth_slod4"
    LODTYPES_DEPTH_ORPHANHD = "sollumz_lodtypes_depth_orphanhd"


class EntityPriorityLevel(str, Enum):
    PRI_REQUIRED = "sollumz_pri_required"
    PRI_OPTIONAL_HIGH = "sollumz_pri_optional_high"
    PRI_OPTIONAL_MEDIUM = "sollumz_pri_optional_medium"
    PRI_OPTIONAL_LOW = "sollumz_pri_optional_low"


class EntityProperties(bpy.types.PropertyGroup):
    archetype_name: bpy.props.StringProperty(name="Archetype Name")
    flags: bpy.props.PointerProperty(type=EntityFlags, name="Flags")
    guid: bpy.props.FloatProperty(name="GUID")
    parent_index: bpy.props.IntProperty(name="Parent Index", default=-1)
    lod_dist: bpy.props.FloatProperty(name="Lod Distance", default=200)
    child_lod_dist: bpy.props.FloatProperty(name="Child Lod Distance")
    lod_level: bpy.props.EnumProperty(
        items=items_from_enums(EntityLodLevel),
        name="LOD Level",
        default=EntityLodLevel.LODTYPES_DEPTH_ORPHANHD,
        options={"HIDDEN"}
    )
    num_children: bpy.props.IntProperty(name="Number of Children")
    priority_level: bpy.props.EnumProperty(
        items=items_from_enums(EntityPriorityLevel),
        name="Priority Level",
        default=EntityPriorityLevel.PRI_REQUIRED,
        options={"HIDDEN"}
    )
    ambient_occlusion_multiplier: bpy.props.FloatProperty(
        name="Ambient Occlusion Multiplier", default=255)
    artificial_ambient_occlusion: bpy.props.FloatProperty(
        name="Artificial Ambient Occlusion", default=255)
    tint_value: bpy.props.FloatProperty(name="Tint Value")


class CMapDataProperties(bpy.types.PropertyGroup):
    parent: StringProperty(name="Parent", default="")
    flags: bpy.props.PointerProperty(type=MapFlags, name="Flags")
    content_flags: IntProperty(name="Content Flags", default=0, min=0, max=(
        2**11)-1, update=ContentFlagPropertyGroup.update_flags_total)

    streaming_extents_min: FloatVectorProperty(name="Streaming Extents Min", default=(0, 0, 0), size=3, subtype='XYZ')
    streaming_extents_max: FloatVectorProperty(name="Streaming Extents Max", default=(0, 0, 0), size=3, subtype='XYZ')
    entities_extents_min: FloatVectorProperty(name="Entities Extents Min", default=(0, 0, 0), size=3, subtype='XYZ')
    entities_extents_max: FloatVectorProperty(name="Entities Extents Max", default=(0, 0, 0), size=3, subtype='XYZ')

    flags_toggle: PointerProperty(type=MapFlags)
    content_flags_toggle: PointerProperty(type=ContentFlags)

    block: PointerProperty(
        type=YmapBlockProperties)
    
    # Collections
    entities: CollectionProperty(type=EntityProperties)
    entity_index: IntProperty()

    cargens: CollectionProperty(type=YmapCarGeneratorProperties)
    cargen_index: IntProperty()

    modeloccluders: CollectionProperty(type=YmapModelOccluderProperties)
    modeloccluder_index: IntProperty()

    boxoccluders: CollectionProperty(type=YmapBoxOcclProperties)
    boxoccluder_index: IntProperty()


def register():
    bpy.types.Scene.selected_ymap_element = bpy.props.EnumProperty(
        items=items_from_enums(YmapElementType), name="Elements")
    bpy.types.Scene.ymaps = bpy.props.CollectionProperty(
        type=CMapDataProperties, name="YMAPs")
    bpy.types.Scene.ymap_index = bpy.props.IntProperty(name="YMAP")
    bpy.types.Scene.ymap_model_occl_properties = PointerProperty(
        type=YmapModelOccluderProperties)
    bpy.types.Scene.ymap_cargen_properties = PointerProperty(
        type=YmapCarGeneratorProperties)


def unregister():
    del bpy.types.Scene.ymaps
    del bpy.types.Scene.ymap_index
    del bpy.types.Scene.ymap_properties
    del bpy.types.Scene.ymap_model_occl_properties
    del bpy.types.Scene.ymap_cargen_properties
