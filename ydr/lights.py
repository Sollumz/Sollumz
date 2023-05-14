import bpy
from math import radians, pi, degrees
from typing import Optional
from mathutils import Matrix, Vector
from ..sollumz_properties import SOLLUMZ_UI_NAMES, SollumType, LightType
from ..tools.blenderhelper import create_empty_object, create_blender_object
from ..sollumz_preferences import get_addon_preferences
from ..cwxml.drawable import Light
from .properties import LightProperties
from .. import logger


def create_light_objs(lights: list[Light], armature_obj: Optional[bpy.types.Object] = None):
    lights_parent = create_empty_object(SollumType.NONE, "Lights")

    for light_xml in lights:
        lobj = create_light(light_xml, armature_obj)
        lobj.parent = lights_parent

    return lights_parent


def create_light(light_xml: Light, armature_obj: Optional[bpy.types.Object] = None):
    light_type = get_light_type(light_xml)

    if light_type is None:
        logger.warning(
            f"Encountered an unknown light type '{light_xml.type}'! Making a point light...")
        light_type = LightType.POINT

    name = SOLLUMZ_UI_NAMES[light_type]

    light_data = create_light_data(light_type, name)
    light_obj = create_blender_object(SollumType.LIGHT, name, light_data)

    if armature_obj is not None:
        create_light_bone_constraint(light_xml, light_obj, armature_obj)

    set_light_rotation(light_xml, light_obj)

    light_obj.data.sollum_type = light_type
    light_obj.name = name
    light_data.name = name
    light_obj.location = light_xml.position

    set_light_bpy_properties(light_xml, light_data)
    set_light_rage_properties(light_xml, light_data)

    return light_obj


def get_light_type(light_xml: Light):
    if light_xml.type == "Point":
        return LightType.POINT
    if light_xml.type == "Spot":
        return LightType.SPOT
    if light_xml.type == "Capsule":
        return LightType.CAPSULE


def create_light_data(light_type: LightType, name: str):
    if light_type in [LightType.SPOT, LightType.CAPSULE]:
        bpy_light_type = "SPOT"
    else:
        bpy_light_type = "POINT"

    return bpy.data.lights.new(name=name, type=bpy_light_type)


def create_light_bone_constraint(light_xml: Light, light_obj: bpy.types.Object, armature_obj: bpy.types.Object):
    armature = armature_obj.data

    for bone in armature.bones:
        if bone.bone_properties.tag != light_xml.bone_id:
            continue

        constraint = light_obj.constraints.new("COPY_TRANSFORMS")
        constraint.target = armature_obj
        constraint.subtarget = bone.name
        constraint.mix_mode = "BEFORE_FULL"
        constraint.target_space = "POSE"
        constraint.owner_space = "LOCAL"


def set_light_rotation(light_xml: Light, light_obj: bpy.types.Object):
    light_xml.direction.negate()
    bitangent = light_xml.direction.cross(light_xml.tangent).normalized()
    mat = Matrix().to_3x3()
    mat.col[0] = light_xml.tangent
    mat.col[1] = bitangent
    mat.col[2] = light_xml.direction
    light_obj.matrix_basis = mat.to_4x4()


def set_light_bpy_properties(light_xml: Light, light_data: bpy.types.Light):
    """Set Blender light properties of ``light_data`` based on ``light_xml``."""
    preferences = get_addon_preferences(bpy.context)
    intensity_factor = 500 if preferences.scale_light_intensity else 1

    light_data.color = [channel / 255 for channel in light_xml.color]
    light_data.energy = light_xml.intensity * intensity_factor
    light_data.use_custom_distance = True
    light_data.cutoff_distance = light_xml.falloff
    light_data.shadow_soft_size = light_xml.falloff_exponent / 5
    light_data.volume_factor = light_xml.volume_intensity

    light_data.shadow_buffer_clip_start = light_xml.shadow_near_clip

    if light_data.sollum_type == LightType.SPOT:
        light_data.spot_blend = abs(
            (radians(light_xml.cone_inner_angle) / pi) - 1)
        light_data.spot_size = radians(light_xml.cone_outer_angle) * 2


def set_light_rage_properties(light_xml: Light, light_data: bpy.types.Light):
    """Set the game properties of ``light_data`` based on ``light_xml``. These properties do not affect how the light appears in the scene."""
    light_data.time_flags.total = str(light_xml.time_flags)
    light_data.light_flags.total = str(light_xml.flags)

    light_props: LightProperties = light_data.light_properties

    light_props.flashiness = light_xml.flashiness
    light_props.flags = light_xml.flags
    light_props.group_id = light_xml.group_id
    light_props.time_flags = light_xml.time_flags
    light_props.extent = light_xml.extent
    light_props.projected_texture_hash = light_xml.projected_texture_hash
    light_props.culling_plane_normal = light_xml.culling_plane_normal
    light_props.culling_plane_offset = light_xml.culling_plane_offset
    light_props.unknown_45 = light_xml.unknown_45
    light_props.unknown_46 = light_xml.unknown_46
    light_props.shadow_blur = light_xml.shadow_blur
    light_props.volume_size_scale = light_xml.volume_size_scale
    light_props.volume_outer_color = [
        channel / 255 for channel in light_xml.volume_outer_color]
    light_props.light_hash = light_xml.light_hash
    light_props.volume_outer_intensity = light_xml.volume_outer_intensity
    light_props.corona_size = light_xml.corona_size
    light_props.volume_outer_exponent = light_xml.volume_outer_exponent
    light_props.light_fade_distance = light_xml.light_fade_distance
    light_props.shadow_fade_distance = light_xml.shadow_fade_distance
    light_props.specular_fade_distance = light_xml.specular_fade_distance
    light_props.volumetric_fade_distance = light_xml.volumetric_fade_distance
    light_props.corona_intensity = light_xml.corona_intensity
    light_props.corona_z_bias = light_xml.corona_z_bias


def create_xml_lights(parent_obj: bpy.types.Object, armature_obj: Optional[bpy.types.Object] = None):
    light_xmls: list[Light] = []

    for child in parent_obj.children_recursive:
        if child.type == "LIGHT" and child.data.sollum_type != LightType.NONE:
            light_xmls.append(create_light_xml(child, armature_obj))

    return light_xmls


def create_light_xml(light_obj: bpy.types.Object, armature_obj: Optional[bpy.types.Object] = None):
    light_xml = Light()
    light_xml.position = light_obj.location
    mat = light_obj.matrix_basis
    set_light_xml_direction(light_xml, mat)
    set_light_xml_tangent(light_xml, mat)

    if armature_obj is not None:
        set_light_xml_bone_id(light_xml, armature_obj.data, light_obj)

    set_light_xml_properties(light_xml, light_obj.data)

    return light_xml


def set_light_xml_direction(light_xml: Light, mat: Matrix):
    light_xml.direction = Vector(
        (mat[0][2], mat[1][2], mat[2][2])).normalized()
    light_xml.direction.negate()


def set_light_xml_tangent(light_xml: Light, mat: Matrix):
    light_xml.tangent = Vector((mat[0][0], mat[1][0], mat[2][0])).normalized()


def set_light_xml_bone_id(light_xml: Light, armature: bpy.types.Armature, light_obj: bpy.types.Object):
    for constraint in light_obj.constraints:
        if not isinstance(constraint, bpy.types.CopyTransformsConstraint):
            continue

        bone = constraint.subtarget
        light_xml.bone_id = armature.bones[bone].bone_properties.tag


def set_light_xml_properties(light_xml: Light, light_data: bpy.types.Light):
    light_props: LightProperties = light_data.light_properties

    light_xml.type = SOLLUMZ_UI_NAMES[light_data.sollum_type]

    light_xml.time_flags = light_data.time_flags.total
    light_xml.flags = light_data.light_flags.total

    light_xml.color = light_data.color * 255
    light_xml.intensity = light_data.energy / 500

    light_xml.flashiness = light_props.flashiness
    light_xml.group_id = light_props.group_id
    light_xml.falloff = light_data.cutoff_distance
    light_xml.falloff_exponent = light_data.shadow_soft_size * 5
    light_xml.culling_plane_normal = Vector(light_props.culling_plane_normal)
    light_xml.culling_plane_offset = light_props.culling_plane_offset
    light_xml.unknown_45 = light_props.unknown_45
    light_xml.unknown_46 = light_props.unknown_46
    light_xml.volume_intensity = light_data.volume_factor
    light_xml.shadow_blur = light_props.shadow_blur
    light_xml.volume_size_scale = light_props.volume_size_scale
    light_xml.volume_outer_color = light_props.volume_outer_color * 255
    light_xml.light_hash = light_props.light_hash
    light_xml.volume_outer_intensity = light_props.volume_outer_intensity
    light_xml.corona_size = light_props.corona_size
    light_xml.volume_outer_exponent = light_props.volume_outer_exponent
    light_xml.light_fade_distance = light_props.light_fade_distance
    light_xml.shadow_fade_distance = light_props.shadow_fade_distance
    light_xml.specular_fade_distance = light_props.specular_fade_distance
    light_xml.volumetric_fade_distance = light_props.volumetric_fade_distance
    light_xml.shadow_near_clip = light_data.shadow_buffer_clip_start
    light_xml.corona_intensity = light_props.corona_intensity
    light_xml.corona_z_bias = light_props.corona_z_bias
    light_xml.extent = Vector(light_props.extent)
    light_xml.projected_texture_hash = light_props.projected_texture_hash

    if light_data.sollum_type == LightType.SPOT:
        light_xml.cone_inner_angle = degrees(
            abs((light_data.spot_blend * pi) - pi))
        light_xml.cone_outer_angle = degrees(light_data.spot_size) / 2
