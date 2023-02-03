import os
import bpy
from typing import Optional
from mathutils import Matrix
from .shader_materials import create_shader, get_detail_extra_sampler
from ..ybn.ybnimport import create_bound_composite, create_bound_object
from ..sollumz_properties import TextureFormat, TextureUsage, SollumType, SollumzImportSettings
from ..cwxml.drawable import YDR, Shader, ShaderGroup, Drawable, Bone, Skeleton, RotationLimit
from ..cwxml.bound import BoundChild
from ..tools.blenderhelper import create_empty_object, create_blender_object, join_objects
from ..tools.utils import get_filename
from .create_drawable_models import create_drawable_models, create_drawable_models_split_by_group
from .lights import create_light_objs
from .. import logger


def import_ydr(filepath: str, import_settings: SollumzImportSettings):
    name = get_filename(filepath)
    ydr_xml = YDR.from_xml_file(filepath)

    if import_settings.import_as_asset:
        return create_drawable_as_asset(ydr_xml, name, filepath)

    return create_drawable_obj(ydr_xml, filepath, name)


def create_drawable_obj(drawable_xml: Drawable, filepath: str, name: Optional[str] = None, split_by_group: bool = False, external_armature: Optional[bpy.types.Object] = None, external_bones: Optional[list[Bone]] = None, materials: Optional[list[bpy.types.Material]] = None):
    """Create a drawable object. ``split_by_group`` will split each Drawable Model by vertex group. ``external_armature`` allows for bones to be rigged to an armature object that is not the parent drawable."""
    name = name or drawable_xml.name
    materials = materials or shadergroup_to_materials(
        drawable_xml.shader_group, filepath)

    has_skeleton = len(
        drawable_xml.skeleton.bones) > 0

    if external_bones:
        drawable_xml.skeleton.bones = external_bones

    if has_skeleton and external_armature is None:
        drawable_obj = create_drawable_armature(drawable_xml, name)
    else:
        drawable_obj = create_empty_object(SollumType.DRAWABLE, name)

    set_drawable_properties(drawable_obj, drawable_xml)

    if drawable_xml.bounds:
        create_embedded_collisions(drawable_xml.bounds, drawable_obj)

    if split_by_group and has_skeleton:
        model_objs = create_drawable_models_split_by_group(
            drawable_xml, materials, drawable_obj, external_armature)
    else:
        model_objs = create_drawable_models(
            drawable_xml, materials, drawable_obj, external_armature)

    parent_model_objs(model_objs, drawable_obj)

    if drawable_xml.lights:
        armature_obj = drawable_obj if has_skeleton else None
        lights = create_light_objs(drawable_xml.lights, armature_obj)
        lights.parent = drawable_obj

    return drawable_obj


def create_drawable_armature(drawable_xml: Drawable, name: str):
    armature = bpy.data.armatures.new(f"{name}.skel")
    drawable_obj = create_blender_object(
        SollumType.DRAWABLE, name, armature)

    create_drawable_skel(drawable_xml.skeleton, drawable_obj)

    if drawable_xml.joints.rotation_limits:
        apply_rotation_limits(
            drawable_xml.joints.rotation_limits, drawable_obj
        )

    return drawable_obj


def shadergroup_to_materials(shader_group: ShaderGroup, filepath: str):
    materials = []

    for shader in shader_group.shaders:
        material = shader_item_to_material(shader, shader_group, filepath)
        materials.append(material)

    return materials


def shader_item_to_material(shader: Shader, shader_group: ShaderGroup, filepath: str):
    texture_folder = os.path.dirname(
        filepath) + "\\" + os.path.basename(filepath)[:-8]

    filename = shader.filename

    if not filename:
        filename = f"{shader.name}.sps"

    material = create_shader(filename)

    material.shader_properties.renderbucket = shader.render_bucket
    material.shader_properties.filename = shader.filename

    for param in shader.parameters:
        for n in material.node_tree.nodes:
            if isinstance(n, bpy.types.ShaderNodeTexImage):
                if param.name == n.name:
                    texture_path = os.path.join(
                        texture_folder, param.texture_name + ".dds")
                    if os.path.isfile(texture_path):
                        img = bpy.data.images.load(
                            texture_path, check_existing=True)
                        n.image = img
                    if not n.image:
                        # for texture shader parameters with no name
                        if not param.texture_name:
                            continue
                        # Check for existing texture
                        existing_texture = None
                        for image in bpy.data.images:
                            if image.name == param.texture_name:
                                existing_texture = image
                        texture = bpy.data.images.new(
                            name=param.texture_name, width=512, height=512) if not existing_texture else existing_texture
                        n.image = texture

                    # assign non color to normal maps
                    if "Bump" in param.name:
                        n.image.colorspace_settings.name = "Non-Color"

                    if param.texture_name and param.name == "DiffuseSampler":
                        material.name = param.texture_name

                    # Assign embedded texture dictionary properties
                    if shader_group.texture_dictionary is not None:
                        for texture in shader_group.texture_dictionary:
                            if texture.name == param.texture_name:
                                n.texture_properties.embedded = True
                                try:
                                    format = TextureFormat[texture.format.replace(
                                        "D3DFMT_", "")]
                                    n.texture_properties.format = format
                                except AttributeError:
                                    print(
                                        f"Failed to set texture format: format '{texture.format}' unknown.")

                                try:
                                    usage = TextureUsage[texture.usage]
                                    n.texture_properties.usage = usage
                                except AttributeError:
                                    print(
                                        f"Failed to set texture usage: usage '{texture.usage}' unknown.")

                                n.texture_properties.extra_flags = texture.extra_flags

                                for prop in dir(n.texture_flags):
                                    for uf in texture.usage_flags:
                                        if uf.lower() == prop:
                                            setattr(
                                                n.texture_flags, prop, True)

                    if not n.texture_properties.embedded:
                        # Set external texture name for non-embedded textures
                        n.image.source = "FILE"
                        n.image.filepath = "//" + param.texture_name + ".dds"

                    if param.name == "BumpSampler" and hasattr(n.image, "colorspace_settings"):
                        n.image.colorspace_settings.name = "Non-Color"

            elif isinstance(n, bpy.types.ShaderNodeValue):
                if param.name == n.name[:-2]:
                    key = n.name[-1]
                    if key == "x":
                        n.outputs[0].default_value = param.x
                    if key == "y":
                        n.outputs[0].default_value = param.y
                    if key == "z":
                        n.outputs[0].default_value = param.z
                    if key == "w":
                        n.outputs[0].default_value = param.w

    # assign extra detail node image for viewing
    dtl_ext = get_detail_extra_sampler(material)
    if dtl_ext:
        dtl = material.node_tree.nodes["DetailSampler"]
        dtl_ext.image = dtl.image

    return material


def create_drawable_skel(skeleton_xml: Skeleton, armature_obj: bpy.types.Object):
    bpy.context.view_layer.objects.active = armature_obj
    bones = skeleton_xml.bones

    # Need to go into edit mode to modify edit bones
    bpy.ops.object.mode_set(mode="EDIT")

    for bone_xml in bones:
        create_bpy_bone(bone_xml, armature_obj.data)

    bpy.ops.object.mode_set(mode="OBJECT")

    for bone_xml in bones:
        set_bone_properties(bone_xml, armature_obj.data)

    return armature_obj


def create_bpy_bone(bone_xml: Bone, armature: bpy.types.Armature):
    # bpy.context.view_layer.objects.active = armature
    edit_bone = armature.edit_bones.new(bone_xml.name)
    if bone_xml.parent_index != -1:
        edit_bone.parent = armature.edit_bones[bone_xml.parent_index]

    # https://github.com/LendoK/Blender_GTA_V_model_importer/blob/master/importer.py
    mat_rot = bone_xml.rotation.to_matrix().to_4x4()
    mat_loc = Matrix.Translation(bone_xml.translation)
    mat_sca = Matrix.Scale(1, 4, bone_xml.scale)

    edit_bone.head = (0, 0, 0)
    edit_bone.tail = (0, 0.05, 0)
    edit_bone.matrix = mat_loc @ mat_rot @ mat_sca

    if edit_bone.parent is not None:
        edit_bone.matrix = edit_bone.parent.matrix @ edit_bone.matrix

    return bone_xml.name


def set_bone_properties(bone_xml: Bone, armature: bpy.types.Armature):
    bl_bone = armature.bones[bone_xml.name]
    bl_bone.bone_properties.tag = bone_xml.tag

    # LimitRotation and Unk0 have their special meanings, can be deduced if needed when exporting
    flags_restricted = set(["LimitRotation", "Unk0"])
    for _flag in bone_xml.flags:
        if _flag in flags_restricted:
            continue

        flag = bl_bone.bone_properties.flags.add()
        flag.name = _flag


def apply_rotation_limits(rotation_limits: list[RotationLimit], armature_obj: bpy.types.Object):
    bone_by_tag: dict[str, bpy.types.PoseBone] = get_bone_by_tag(armature_obj)

    for rot_limit in rotation_limits:
        if rot_limit.bone_id not in bone_by_tag:
            logger.warning(
                f"{armature_obj.name} contains a rotation limit with an invalid bone id '{rot_limit.bone_id}'! Skipping...")
            continue

        bone = bone_by_tag[rot_limit.bone_id]
        create_bone_constraint(rot_limit, bone)


def get_bone_by_tag(armature_obj: bpy.types.Object):
    bone_by_tag: dict[str, bpy.types.PoseBone] = {}

    for pose_bone in armature_obj.pose.bones:
        bone_tag = pose_bone.bone.bone_properties.tag
        bone_by_tag[bone_tag] = pose_bone

    return bone_by_tag


def create_bone_constraint(rot_limit: RotationLimit, pose_bone: bpy.types.PoseBone):
    constraint = pose_bone.constraints.new("LIMIT_ROTATION")
    constraint.owner_space = "LOCAL"
    constraint.use_limit_x = True
    constraint.use_limit_y = True
    constraint.use_limit_z = True
    constraint.max_x = rot_limit.max.x
    constraint.max_y = rot_limit.max.y
    constraint.max_z = rot_limit.max.z
    constraint.min_x = rot_limit.min.x
    constraint.min_y = rot_limit.min.y
    constraint.min_z = rot_limit.min.z


def create_embedded_collisions(bounds_xml: list[BoundChild], drawable_obj: bpy.types.Object):
    col_name = f"{drawable_obj.name}.col"
    bound_objs: list[bpy.types.Object] = []

    for bound_xml in bounds_xml:
        if bound_xml.type == "Composite":
            bound_obj = create_bound_composite(bound_xml)
        else:
            bound_obj = create_bound_object(bound_xml)

        bound_objs.append(bound_obj)

    # If there is only one bound object, parent directly to drawable
    if len(bound_objs) == 1:
        bound_obj = bound_objs[0]
        bound_obj.name = col_name
        bound_obj.parent = drawable_obj

        return bound_obj

    # Otherwise parent all embedded bounds to an empty for organization
    bounds_parent = create_empty_object(SollumType.NONE, col_name)

    for bound_obj in bound_objs:
        bound_obj.parent = bounds_parent

    return bounds_parent


def parent_model_objs(model_objs: list[bpy.types.Object], drawable_obj: bpy.types.Object):
    for obj in model_objs:
        obj.parent = drawable_obj


def set_drawable_properties(obj: bpy.types.Object, drawable_xml: Drawable):
    obj.drawable_properties.lod_dist_high = drawable_xml.lod_dist_high
    obj.drawable_properties.lod_dist_med = drawable_xml.lod_dist_med
    obj.drawable_properties.lod_dist_low = drawable_xml.lod_dist_low
    obj.drawable_properties.lod_dist_vlow = drawable_xml.lod_dist_vlow
    obj.drawable_properties.unknown_9A = drawable_xml.unknown_9A


def create_drawable_as_asset(drawable_xml: Drawable, name: str, filepath: str):
    """Create drawable as an asset with all the high LODs joined together."""
    drawable_xml.drawable_models_low = []
    drawable_xml.drawable_models_med = []
    drawable_xml.drawable_models_vlow = []

    drawable_obj = create_drawable_obj(drawable_xml, filepath)

    model_objs = []

    for child in drawable_obj.children:
        if child.sollum_type == SollumType.DRAWABLE_MODEL:
            model_objs.append(child)

    joined_obj = join_objects(model_objs)
    joined_obj.name = name

    joined_obj.asset_mark()
    joined_obj.asset_generate_preview()

    bpy.context.collection.objects.unlink(joined_obj)
    bpy.data.objects.remove(drawable_obj)

    return joined_obj
