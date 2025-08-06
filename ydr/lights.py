import bpy
from math import radians, pi, degrees
from typing import Optional
from mathutils import Matrix, Vector
from .light_flashiness import Flashiness
from ..sollumz_properties import SOLLUMZ_UI_NAMES, SollumType, LightType
from ..tools.blenderhelper import create_empty_object, create_blender_object, add_child_of_bone_constraint
from ..cwxml.drawable import Light
from ..cwxml.ymap import LightInstance
from .properties import LightProperties
from .. import logger


def create_light_objs(lights: list[Light], armature_obj: Optional[bpy.types.Object] = None):
    lights_parent = create_empty_object(SollumType.NONE, "Lights")

    for light_xml in lights:
        lobj = create_light(light_xml, armature_obj)
        lobj.parent = lights_parent

    return lights_parent


def create_light_instance_objs(lights: list[LightInstance], armature_obj: Optional[bpy.types.Object] = None):
    lights = [convert_light_instance_to_light_xml(li) for li in lights]
    return create_light_objs(lights, armature_obj)


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

    set_light_properties(light_xml, light_data)

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

        add_child_of_bone_constraint(light_obj, armature_obj, bone.name)


def set_light_rotation(light_xml: Light, light_obj: bpy.types.Object):
    light_xml.direction.negate()
    bitangent = light_xml.direction.cross(light_xml.tangent).normalized()
    mat = Matrix().to_3x3()
    mat.col[0] = light_xml.tangent
    mat.col[1] = bitangent
    mat.col[2] = light_xml.direction
    light_obj.matrix_basis = mat.to_4x4()


def set_light_properties(light_xml: Light, light_data: bpy.types.Light):
    """Set the game properties of ``light_data`` based on ``light_xml``."""
    light_data.color = [channel / 255 for channel in light_xml.color]

    light_data.time_flags.total = str(light_xml.time_flags)
    light_data.light_flags.total = str(light_xml.flags)

    light_props: LightProperties = light_data.light_properties

    light_props.intensity = light_xml.intensity
    light_props.falloff = light_xml.falloff
    light_props.falloff_exponent = light_xml.falloff_exponent
    light_props.volume_intensity = light_xml.volume_intensity
    light_props.shadow_near_clip = light_xml.shadow_near_clip

    if light_data.sollum_type == LightType.SPOT:
        light_props.cone_inner_angle = radians(light_xml.cone_inner_angle)
        light_props.cone_outer_angle = radians(light_xml.cone_outer_angle)

    light_props.flashiness = Flashiness(light_xml.flashiness).name
    light_props.flags = light_xml.flags
    light_props.group_id = light_xml.group_id
    light_props.time_flags = light_xml.time_flags
    light_props.extent = light_xml.extent
    light_props.projected_texture_hash = light_xml.projected_texture_hash
    light_props.culling_plane_normal = light_xml.culling_plane_normal
    light_props.culling_plane_offset = light_xml.culling_plane_offset
    light_props.shadow_blur = light_xml.shadow_blur / 255
    light_props.volume_size_scale = light_xml.volume_size_scale
    light_props.volume_outer_color = [channel / 255 for channel in light_xml.volume_outer_color]
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


def create_xml_lights(parent_obj: bpy.types.Object) -> list[Light]:
    light_xmls: list[Light] = []

    for child in parent_obj.children_recursive:
        if child.type == "LIGHT" and child.data.sollum_type != LightType.NONE:
            light_xmls.append(create_light_xml(child, parent_obj))

    return light_xmls


def create_xml_light_instances(parent_obj: bpy.types.Object) -> list[LightInstance]:
    lights = create_xml_lights(parent_obj)
    return [convert_light_to_light_instance_xml(light) for light in lights]


def create_light_xml(light_obj: bpy.types.Object, parent_obj: bpy.types.Object):
    light_xml = Light()

    root_mat = parent_obj.matrix_world
    bone = set_light_xml_bone_id(light_xml, light_obj)
    if bone is not None:
        root_mat = root_mat @ bone.matrix_local

    mat = root_mat.inverted() @ light_obj.matrix_world
    light_xml.position = mat.to_translation()
    set_light_xml_direction(light_xml, mat)
    set_light_xml_tangent(light_xml, mat)

    set_light_xml_properties(light_xml, light_obj.data)

    return light_xml


def set_light_xml_direction(light_xml: Light, mat: Matrix):
    light_xml.direction = Vector(
        (mat[0][2], mat[1][2], mat[2][2])).normalized()
    light_xml.direction.negate()


def set_light_xml_tangent(light_xml: Light, mat: Matrix):
    light_xml.tangent = Vector((mat[0][0], mat[1][0], mat[2][0])).normalized()


def set_light_xml_bone_id(light_xml: Light, light_obj: bpy.types.Object):
    for constraint in light_obj.constraints:
        if not isinstance(constraint, bpy.types.CopyTransformsConstraint):
            continue

        if constraint.target is None or constraint.target.type != "ARMATURE":
            continue

        armature = constraint.target.data
        bone_name = constraint.subtarget
        bone = armature.bones[bone_name]
        light_xml.bone_id = bone.bone_properties.tag
        return bone

    return None


def set_light_xml_properties(light_xml: Light, light_data: bpy.types.Light):
    light_props: LightProperties = light_data.light_properties

    light_xml.type = SOLLUMZ_UI_NAMES[light_data.sollum_type]

    light_xml.time_flags = light_data.time_flags.total
    light_xml.flags = light_data.light_flags.total

    light_xml.color = light_data.color * 255
    light_xml.intensity = light_props.intensity

    light_xml.flashiness = Flashiness[light_props.flashiness].value
    light_xml.group_id = light_props.group_id
    light_xml.falloff = light_props.falloff
    light_xml.falloff_exponent = light_props.falloff_exponent
    light_xml.culling_plane_normal = Vector(light_props.culling_plane_normal)
    light_xml.culling_plane_offset = light_props.culling_plane_offset
    light_xml.volume_intensity = light_props.volume_intensity
    light_xml.shadow_blur = int(light_props.shadow_blur * 255)
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
    light_xml.shadow_near_clip = light_props.shadow_near_clip
    light_xml.corona_intensity = light_props.corona_intensity
    light_xml.corona_z_bias = light_props.corona_z_bias
    light_xml.extent = Vector(light_props.extent)
    light_xml.projected_texture_hash = light_props.projected_texture_hash

    if light_data.sollum_type == LightType.SPOT:
        light_xml.cone_inner_angle = degrees(light_props.cone_inner_angle)
        light_xml.cone_outer_angle = degrees(light_props.cone_outer_angle)


def duplicate_lights_for_light_effect(parent_obj: bpy.types.Object) -> bpy.types.Object:
    lights_parent = create_empty_object(SollumType.NONE, "Lights")

    for child in parent_obj.children_recursive:
        if child.type == "LIGHT" and child.data.sollum_type != LightType.NONE:
            light_copy = child.copy()
            light_copy.data = light_copy.data.copy()
            light_copy.parent = lights_parent
            bpy.context.collection.objects.link(light_copy)

    return lights_parent


def convert_light_instance_to_light_xml(li: LightInstance) -> Light:
    """Converts a ``LightInstance`` XML object (used in meta files, i.e. ymaps and ytyps, in light effect extensions) to a ``Light`` XML object (used in drawables)."""
    def _text_list_to_vec(tl):
        return Vector([float(v) for v in tl])

    def _text_list_to_color(tl):
        return [int(v) for v in tl]

    light = Light()
    light.position = _text_list_to_vec(li.position)
    light.color = _text_list_to_color(li.color)
    light.flashiness = li.flashiness
    light.intensity = li.intensity
    light.flags = li.flags
    light.bone_id = li.bone_id
    if li.light_type == 1:
        light.type = "Point"
    elif li.light_type == 2:
        light.type = "Spot"
    elif li.light_type == 4:
        light.type = "Capsule"
    light.group_id = li.group_id
    light.time_flags = li.time_flags
    light.falloff = li.falloff
    light.falloff_exponent = li.falloff_exponent
    light.culling_plane_normal = _text_list_to_vec(li.culling_plane[:3])
    light.culling_plane_offset = float(li.culling_plane[3])
    light.volume_intensity = li.volume_intensity
    light.volume_size_scale = li.volume_size_scale
    light.volume_outer_color = _text_list_to_color(li.volume_outer_color)
    light.volume_outer_intensity = li.volume_outer_intensity
    light.volume_outer_exponent = li.volume_outer_exponent
    light.light_hash = li.light_hash
    light.corona_size = li.corona_size
    light.corona_intensity = li.corona_intensity
    light.corona_z_bias = li.corona_z_bias
    light.light_fade_distance = li.light_fade_distance
    light.shadow_fade_distance = li.shadow_fade_distance
    light.specular_fade_distance = li.specular_fade_distance
    light.volumetric_fade_distance = li.volumetric_fade_distance
    light.shadow_near_clip = li.shadow_near_clip
    light.direction = _text_list_to_vec(li.direction)
    light.tangent = _text_list_to_vec(li.tangent)
    light.cone_inner_angle = li.cone_inner_angle
    light.cone_outer_angle = li.cone_outer_angle
    light.extent = _text_list_to_vec(li.extents)
    light.shadow_blur = li.shadow_blur
    light.projected_texture_hash = f"hash_{li.projected_texture_key:08X}" if li.projected_texture_key != 0 else ""
    return light


def convert_light_to_light_instance_xml(light: Light) -> LightInstance:
    """Converts a ``Light`` XML object (used in drawables) to a ``LightInstance`` XML object (used in meta files, i.e. ymaps and ytyps, in light effect extensions)."""
    def _vec_to_text_list(vec):
        return [str(v) for v in vec]

    def _color_to_text_list(color):
        return [str(int(v)) for v in color]

    li = LightInstance()
    li.position = _vec_to_text_list(light.position)
    li.color = _color_to_text_list(light.color)
    li.flashiness = light.flashiness
    li.intensity = light.intensity
    li.flags = light.flags
    li.bone_id = light.bone_id
    if light.type == "Point":
        li.light_type = 1
    elif light.type == "Spot":
        li.light_type = 2
    elif light.type == "Capsule":
        li.light_type = 4
    li.group_id = light.group_id
    li.time_flags = light.time_flags
    li.falloff = light.falloff
    li.falloff_exponent = light.falloff_exponent
    li.culling_plane = _vec_to_text_list(light.culling_plane_normal) + [str(light.culling_plane_offset)]
    li.volume_intensity = light.volume_intensity
    li.volume_size_scale = light.volume_size_scale
    li.volume_outer_color = _color_to_text_list(light.volume_outer_color)
    li.volume_outer_intensity = light.volume_outer_intensity
    li.volume_outer_exponent = light.volume_outer_exponent
    li.light_hash = light.light_hash
    li.corona_size = light.corona_size
    li.corona_intensity = light.corona_intensity
    li.corona_z_bias = light.corona_z_bias
    li.light_fade_distance = light.light_fade_distance
    li.shadow_fade_distance = light.shadow_fade_distance
    li.specular_fade_distance = light.specular_fade_distance
    li.volumetric_fade_distance = light.volumetric_fade_distance
    li.shadow_near_clip = light.shadow_near_clip
    li.direction = _vec_to_text_list(light.direction)
    li.tangent = _vec_to_text_list(light.tangent)
    li.cone_inner_angle = light.cone_inner_angle
    li.cone_outer_angle = light.cone_outer_angle
    li.extents = _vec_to_text_list(light.extent)
    li.shadow_blur = light.shadow_blur
    from ..tools.jenkhash import name_to_hash
    li.projected_texture_key = name_to_hash(light.projected_texture_hash)
    return li
