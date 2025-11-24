import bpy
from bpy.types import (
    Object
)
from math import radians, degrees
from typing import Optional
from mathutils import Matrix, Vector
from .light_flashiness import LightFlashiness
from ..sollumz_properties import SOLLUMZ_UI_NAMES, SollumType, LightType
from ..tools.blenderhelper import create_empty_object, create_blender_object, add_child_of_bone_constraint, get_child_of_bone
from szio.gta5 import (
    Light,
    LightType as IOLightType,
)
from .properties import LightProperties
from .. import logger

INTENSITY_SCALE_FACTOR = 500


def create_light_objs(lights: list[Light], armature_obj: Optional[Object] = None, name: Optional[str] = None) -> Object:
    lights_parent = create_empty_object(SollumType.NONE, name if name else "Lights")

    for light in lights:
        lobj = create_light(light, armature_obj)
        lobj.parent = lights_parent

    return lights_parent


def create_light(light: Light, armature_obj: Optional[Object] = None) -> Object:
    light_type = convert_light_type(light)

    name = SOLLUMZ_UI_NAMES[light_type]

    light_data = create_light_data(light_type, name)
    light_obj = create_blender_object(SollumType.LIGHT, name, light_data)

    if armature_obj is not None:
        create_light_bone_constraint(light, light_obj, armature_obj)

    set_light_rotation(light, light_obj)

    light_obj.data.sollum_type = light_type
    light_obj.name = name
    light_data.name = name
    light_obj.location = light.position

    set_light_properties(light, light_data)

    return light_obj


def convert_light_type(light: Light) -> LightType:
    match light.light_type:
        case IOLightType.POINT:
            return LightType.POINT
        case IOLightType.SPOT:
            return LightType.SPOT
        case IOLightType.CAPSULE:
            return LightType.CAPSULE
        case _:
            logger.warning(
                f"Encountered an unknown light type '{light.light_type}'! Making a point light..."
            )
            return LightType.POINT


def create_light_data(light_type: LightType, name: str):
    if light_type in [LightType.SPOT, LightType.CAPSULE]:
        bpy_light_type = "SPOT"
    else:
        bpy_light_type = "POINT"

    return bpy.data.lights.new(name=name, type=bpy_light_type)


def create_light_bone_constraint(light: Light, light_obj: Object, armature_obj: Object):
    armature = armature_obj.data

    for bone in armature.bones:
        if bone.bone_properties.tag != light.bone_id:
            continue

        add_child_of_bone_constraint(light_obj, armature_obj, bone.name)
        break


def set_light_rotation(light: Light, light_obj: bpy.types.Object):
    light.direction.negate()
    bitangent = light.direction.cross(light.tangent).normalized()
    mat = Matrix().to_3x3()
    mat.col[0] = light.tangent
    mat.col[1] = bitangent
    mat.col[2] = light.direction
    light_obj.matrix_basis = mat.to_4x4()


def set_light_properties(light: Light, light_data: bpy.types.Light):
    """Set the game properties of ``light_data`` based on ``light``."""
    light_data.color = [channel / 255 for channel in light.color]

    light_data.time_flags.total = str(light.time_flags)
    light_data.light_flags.total = str(light.flags)

    light_props: LightProperties = light_data.light_properties

    light_props.intensity = light.intensity
    light_props.falloff = light.falloff
    light_props.falloff_exponent = light.falloff_exponent
    light_props.volume_intensity = light.volume_intensity
    light_props.shadow_near_clip = light.shadow_near_clip

    if light_data.sollum_type == LightType.SPOT:
        light_props.cone_inner_angle = radians(light.cone_inner_angle)
        light_props.cone_outer_angle = radians(light.cone_outer_angle)

    light_props.flashiness = light.flashiness.name
    light_props.group_id = light.group_id
    light_props.time_flags = light.time_flags
    light_props.extent = light.extent
    light_props.projected_texture_hash = light.projected_texture_hash
    light_props.culling_plane_normal = light.culling_plane_normal
    light_props.culling_plane_offset = light.culling_plane_offset
    light_props.shadow_blur = light.shadow_blur / 255
    light_props.volume_size_scale = light.volume_size_scale
    light_props.volume_outer_color = [channel / 255 for channel in light.volume_outer_color]
    light_props.light_hash = light.light_hash
    light_props.volume_outer_intensity = light.volume_outer_intensity
    light_props.corona_size = light.corona_size
    light_props.volume_outer_exponent = light.volume_outer_exponent
    light_props.light_fade_distance = light.light_fade_distance
    light_props.shadow_fade_distance = light.shadow_fade_distance
    light_props.specular_fade_distance = light.specular_fade_distance
    light_props.volumetric_fade_distance = light.volumetric_fade_distance
    light_props.corona_intensity = light.corona_intensity
    light_props.corona_z_bias = light.corona_z_bias


def export_lights(parent_obj: Object) -> list[Light]:
    lights = []

    for child in parent_obj.children_recursive:
        if child.type == "LIGHT" and child.data.sollum_type != LightType.NONE:
            lights.append(export_light(child, parent_obj))

    return lights


def export_light(light_obj: Object, parent_obj: Object) -> Light:
    root_mat = parent_obj.matrix_world
    bone_id = 0
    bone = get_child_of_bone(light_obj)
    if bone is not None:
        root_mat = root_mat @ bone.matrix_local
        bone_id = bone.bone_properties.tag

    mat = root_mat.inverted() @ light_obj.matrix_world
    position = mat.to_translation()
    direction = Vector((mat[0][2], mat[1][2], mat[2][2])).normalized()
    direction.negate()
    tangent = Vector((mat[0][0], mat[1][0], mat[2][0])).normalized()

    light_data = light_obj.data
    light_props: LightProperties = light_data.light_properties

    light_type = LightType(light_data.sollum_type)
    is_spot = light_type == LightType.SPOT

    return Light(
        light_type=light_type.to_io(),
        position=position,
        direction=direction,
        tangent=tangent,
        extent=Vector(light_props.extent),
        color=tuple(map(int, light_data.color * 255)),
        flashiness=LightFlashiness[light_props.flashiness],
        intensity=light_props.intensity,
        flags=int(light_data.light_flags.total),
        time_flags=int(light_data.time_flags.total),
        bone_id=bone_id,
        group_id=light_props.group_id,
        light_hash=light_props.light_hash,
        falloff=light_props.falloff,
        falloff_exponent=light_props.falloff_exponent,
        culling_plane_normal=Vector(light_props.culling_plane_normal),
        culling_plane_offset=light_props.culling_plane_offset,
        volume_intensity=light_props.volume_intensity,
        volume_size_scale=light_props.volume_size_scale,
        volume_outer_color=tuple(map(int, light_props.volume_outer_color * 255)),
        volume_outer_intensity=light_props.volume_outer_intensity,
        volume_outer_exponent=light_props.volume_outer_exponent,
        corona_size=light_props.corona_size,
        corona_intensity=light_props.corona_intensity,
        corona_z_bias=light_props.corona_z_bias,
        projected_texture_hash=light_props.projected_texture_hash,
        light_fade_distance=int(light_props.light_fade_distance),
        shadow_fade_distance=int(light_props.shadow_fade_distance),
        specular_fade_distance=int(light_props.specular_fade_distance),
        volumetric_fade_distance=int(light_props.volumetric_fade_distance),
        shadow_near_clip=light_props.shadow_near_clip,
        shadow_blur=int(light_props.shadow_blur * 255),
        cone_inner_angle=degrees(light_props.cone_inner_angle) if is_spot else 0.0,
        cone_outer_angle=degrees(light_props.cone_outer_angle) if is_spot else 0.0,
    )

