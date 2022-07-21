import bpy
from ..sollumz_properties import SollumType
from ..tools.jenkhash import Generate


def animations_filter(self, object):
    if len(bpy.context.selected_objects) <= 0:
        return False

    active_object = bpy.context.selected_objects[0]

    if active_object.sollum_type != SollumType.CLIP:
        return False

    return object.sollum_type == SollumType.ANIMATION and active_object.parent.parent == object.parent.parent


def armature_obj_filter(self, object):
    return object.clip_dict_properties.uv_obj == None

def uv_object_filter(self, object):
    return object.sollum_type == SollumType.DRAWABLE_GEOMETRY

def uv_material_filter(self, material):
    return material.sollum_type != "sollumz_material_none"

def update_hashes(self, context):
    animation = context.object
    clip_dict = animation.parent.parent
    anim_drawable_mesh = clip_dict.clip_dict_properties.uv_obj
    anim_drawable_model = anim_drawable_mesh.parent.parent.name
    material_index = None
    for index, mat in enumerate(anim_drawable_mesh.data.materials):
        if mat == self.material:
            material_index = index
            break

    if material_index is None:
        raise Exception("Selected material does not exist with UV object")

    anim_hash = anim_drawable_model + "_uv_" + str(material_index)
    clip_hash = "hash_" + hex(Generate(anim_drawable_model) + (material_index + 1)).strip("0x").upper()
    clip_name = "pack:/" + anim_hash + ".clip"
    
    animation.animation_properties.hash = anim_hash

    for item in clip_dict.children:
        if item.sollum_type == "sollumz_clips":
            for clip in item.children:
                clip_linked_anims = clip.clip_properties.animations
                for anim in clip_linked_anims:
                    if anim.animation.name == animation.name:
                        clip.clip_properties.hash = clip_hash
                        clip.clip_properties.name = clip_name
                        break


class UVAnimMaterials(bpy.types.PropertyGroup):
    material: bpy.props.PointerProperty(
        name="Material", type=bpy.types.Material, poll=uv_material_filter, update=update_hashes)


class ClipDictionary(bpy.types.PropertyGroup):
    armature: bpy.props.PointerProperty(
        name="Armature", type=bpy.types.Armature)
    uv_obj: bpy.props.PointerProperty(
        name="UV Object", type=bpy.types.Object, poll=uv_object_filter)


class ClipAnimation(bpy.types.PropertyGroup):
    start_frame: bpy.props.IntProperty(
        name="Start Frame", default=0, min=0, description="First frame of the playback area")
    end_frame: bpy.props.IntProperty(
        name="End Frame", default=0, min=0, description="Last frame (inclusive) of the playback area")

    animation: bpy.props.PointerProperty(
        name="Animation", type=bpy.types.Object, poll=animations_filter)


class ClipProperties(bpy.types.PropertyGroup):
    hash: bpy.props.StringProperty(name="Hash", default="")
    name: bpy.props.StringProperty(name="Name", default="")

    duration: bpy.props.FloatProperty(
        name="Duration", default=0, min=0, description="Duration of the clip in seconds")

    start_frame: bpy.props.IntProperty(name="Start Frame", default=0, min=0)
    end_frame: bpy.props.IntProperty(name="End Frame", default=0, min=0)

    animations: bpy.props.CollectionProperty(
        name="Animations", type=ClipAnimation)


class AnimationProperties(bpy.types.PropertyGroup):
    hash: bpy.props.StringProperty(name="Hash", default="")
    frame_count: bpy.props.IntProperty(name="Frame Count", default=1, min=1)

    base_action: bpy.props.PointerProperty(name="Base", type=bpy.types.Action)
    root_motion_location_action: bpy.props.PointerProperty(
        name="Root Position", type=bpy.types.Action)
    root_motion_rotation_action: bpy.props.PointerProperty(
        name="Root Rotation", type=bpy.types.Action)


def register():
    bpy.types.Scene.create_animation_type = bpy.props.EnumProperty(
        items=[
            ("REGULAR",
             "Regular", "Create a general YCD for armature/bone animation"),
            ("UV",
             "UV", "Create a UV YCD.")
        ],
        name="Type",
        default="REGULAR"
    )
    bpy.types.Object.uv_anim_materials = bpy.props.PointerProperty(
        type=UVAnimMaterials)
    bpy.types.Object.clip_dict_properties = bpy.props.PointerProperty(
        type=ClipDictionary)
    bpy.types.Object.clip_properties = bpy.props.PointerProperty(
        type=ClipProperties)
    bpy.types.Object.animation_properties = bpy.props.PointerProperty(
        type=AnimationProperties)


def unregister():
    del bpy.types.Object.uv_anim_materials
    del bpy.types.Object.clip_dict_properties
    del bpy.types.Object.clip_properties
    del bpy.types.Object.animation_properties
