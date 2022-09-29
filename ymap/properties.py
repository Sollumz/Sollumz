import bpy

from ..tools.utils import int_to_bool_list, flag_prop_to_list, flag_list_to_int
from bpy.props import (
    PointerProperty, 
    StringProperty, 
    IntProperty, 
    FloatVectorProperty,
    BoolProperty
)

def update_uint_prop(self, context, var_name):
    '''Work around for storing uint values as a Blender property (credits: CFox)'''
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

def safe_get_value(obj, prop):
    try:
        return obj[prop]
    except KeyError:
        return False

class FlagPropertyGroup:
    '''Credits: Sollumz'''
    def update_flags_total(self, context):
        flags = int_to_bool_list(int(self.flags), size=2)
        for index, flag_name in enumerate(MapFlags.__annotations__):
            self.flags_toggle[flag_name] = flags[index]

    def update_flag(self, context):
        flags = flag_prop_to_list(self.__class__, self)
        obj = context.active_object
        if obj:
            obj.ymap_properties.flags = flag_list_to_int(flags)

class ContentFlagPropertyGroup:
    '''Credits: Sollumz'''
    def update_flags_total(self, context):
        flags = int_to_bool_list(int(self.content_flags), size=11)
        for index, flag_name in enumerate(ContentFlags.__annotations__):
            self.content_flags_toggle[flag_name] = flags[index]

    def update_flag(self, context):
        flags = flag_prop_to_list(self.__class__, self)
        obj = context.active_object
        if obj:
            obj.ymap_properties.content_flags = flag_list_to_int(flags)

class MapFlags(bpy.types.PropertyGroup):
    script_loaded: bpy.props.BoolProperty(name="Script Loaded", update=FlagPropertyGroup.update_flag)
    has_lod: bpy.props.BoolProperty(name="LOD", update=FlagPropertyGroup.update_flag)

class ContentFlags(bpy.types.PropertyGroup):
    has_hd: BoolProperty(name="HD", update=ContentFlagPropertyGroup.update_flag)
    has_lod: BoolProperty(name="LOD", update=ContentFlagPropertyGroup.update_flag)
    has_slod2: BoolProperty(name="SLOD2", update=ContentFlagPropertyGroup.update_flag)
    has_int: BoolProperty(name="Interior", update=ContentFlagPropertyGroup.update_flag)
    has_slod: BoolProperty(name="SLOD", update=ContentFlagPropertyGroup.update_flag)
    has_occl: BoolProperty(name="Occlusion", update=ContentFlagPropertyGroup.update_flag)
    has_physics: BoolProperty(name="Physics", update=ContentFlagPropertyGroup.update_flag)
    has_lod_lights: BoolProperty(name="Lod Lights", update=ContentFlagPropertyGroup.update_flag)
    has_dis_lod_lights: BoolProperty(name="Distant Lod Lights", update=ContentFlagPropertyGroup.update_flag)
    has_critical: BoolProperty(name="Critical", update=ContentFlagPropertyGroup.update_flag)
    has_grass: BoolProperty(name="Grass", update=ContentFlagPropertyGroup.update_flag)

class YmapBlockProperties(bpy.types.PropertyGroup):
    version: StringProperty(name="Version", default='0', update=lambda self, context: update_uint_prop(self, context, 'version'))
    flags: StringProperty(name="Flags", default='0', update=lambda self, context: update_uint_prop(self, context, 'flags'))
    name: StringProperty(name="Name")
    exported_by: StringProperty(name="Exported By")
    owner: StringProperty(name="Owner")
    time: StringProperty(name="Time")

class YmapProperties(bpy.types.PropertyGroup):
    name: StringProperty(name="Name", default="untitled_ymap")
    parent: StringProperty(name="Parent", default="")
    flags: IntProperty(name="Flags", default=0, min=0, max=3, update=FlagPropertyGroup.update_flags_total)
    content_flags: IntProperty(name="Content Flags", default=0, min=0, max=(2**11)-1, update=ContentFlagPropertyGroup.update_flags_total)

    streaming_extents_min: FloatVectorProperty()
    streaming_extents_max: FloatVectorProperty()
    entities_extents_min: FloatVectorProperty()
    entities_extents_max: FloatVectorProperty()

    flags_toggle: PointerProperty(type=MapFlags)
    content_flags_toggle: PointerProperty(type=ContentFlags)

    block: PointerProperty(
        type=YmapBlockProperties)

def register():
    bpy.types.Object.ymap_properties = PointerProperty(
        type=YmapProperties)

def unregister():
    del bpy.types.Object.ymap_properties