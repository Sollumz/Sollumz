import traceback
import os
import bpy
from mathutils import Matrix
from Sollumz.ydr.shader_materials import create_shader
from Sollumz.ybn.ybnimport import composite_to_obj
from Sollumz.sollumz_properties import SOLLUMZ_UI_NAMES, BoundType, DrawableType, LODLevel, TextureFormat, TextureUsage
from Sollumz.resources.drawable import *
from Sollumz.tools.meshhelper import flip_uv
from Sollumz.tools.utils import ListHelper
from Sollumz.tools.blenderhelper import BlenderHelper


def shadergroup_to_materials(shadergroup, filepath):
    materials = []

    texture_folder = os.path.dirname(
        filepath) + "\\" + os.path.basename(filepath)[:-8]
    for shader in shadergroup.shaders:

        material = create_shader(shader.name)

        material.shader_properties.renderbucket = shader.render_bucket
        material.shader_properties.filename = shader.filename

        for param in shader.parameters:
            for n in material.node_tree.nodes:
                if isinstance(n, bpy.types.ShaderNodeTexImage):
                    if param.name == n.name:
                        texture_path = os.path.join(
                            texture_folder, param.texture_name + ".dds")
                        shared_folder = bpy.context.preferences.addons[
                            "Sollumz"].preferences.shared_texture_folder
                        shared_texture_path = os.path.join(
                            shared_folder, param.texture_name + ".dds")
                        if(os.path.isfile(texture_path)):
                            img = bpy.data.images.load(
                                texture_path, check_existing=True)
                            n.image = img
                        # check shared texture folder
                        elif os.path.isfile(shared_texture_path):
                            img = bpy.data.images.load(
                                shared_texture_path, check_existing=True)
                            n.image = img
                        else:
                            n.image = bpy.data.images.new(
                                name=param.texture_name, width=512, height=512)

                        # Assign embedded texture dictionary properties
                        if shadergroup.texture_dictionary != None:
                            for texture in shadergroup.texture_dictionary:
                                if texture.name == param.texture_name:
                                    n.texture_properties.embedded = True
                                    try:
                                        format = TextureFormat[texture.format.replace(
                                            'D3DFMT_', '')]
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
                                            if(uf.lower() == prop):
                                                setattr(
                                                    n.texture_flags, prop, True)

                        if param.name == "BumpSampler" and hasattr(n.image, 'colorspace_settings'):
                            n.image.colorspace_settings.name = 'Non-Color'

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

        materials.append(material)

    return materials


def create_uv_layer(mesh, num, name, texcoords):
    mesh.uv_layers.new()
    uv_layer = mesh.uv_layers[num]
    uv_layer.name = name
    for i in range(len(uv_layer.data)):
        uv = flip_uv(texcoords[mesh.loops[i].vertex_index])
        uv_layer.data[i].uv = uv


def create_vertexcolor_layer(mesh, num, name, colors):
    mesh.vertex_colors.new(name="Vertex Colors " + str(num))
    color_layer = mesh.vertex_colors[num]
    color_layer.name = name
    for i in range(len(color_layer.data)):
        rgba = colors[mesh.loops[i].vertex_index]
        color_layer.data[i].color = ListHelper.divide_list(rgba, 255)


def geometry_to_obj(geometry, bones=None, name=None):

    vertices = []
    faces = []
    normals = []
    texcoords = {}
    colors = {}

    # gather data
    data = geometry.vertex_buffer.data
    for vertex in data:
        vertices.append(vertex.position)
        normals.append(vertex.normal)

        for key, value in vertex._asdict().items():
            if 'texcoord' in key:
                if not key in texcoords.keys():
                    texcoords[key] = []
                texcoords[key].append(value)
            if 'colour' in key:
                if not key in colors.keys():
                    colors[key] = []
                colors[key].append(value)

    indices = geometry.index_buffer.data
    # Split indices into groups of 3
    faces = [indices[i * 3:(i + 1) * 3]
             for i in range((len(indices) + 3 - 1) // 3)]

    # create mesh
    mesh = bpy.data.meshes.new(SOLLUMZ_UI_NAMES[DrawableType.GEOMETRY])
    mesh.from_pydata(vertices, [], faces)

    # set normals
    mesh.normals_split_custom_set_from_vertices(normals)
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
    mesh.use_auto_smooth = True

    # set uvs
    i = 0
    for layer_name, coords in texcoords.items():
        create_uv_layer(mesh, i, layer_name, coords)
        i += 1

    # set vertex colors
    i = 0
    for layer_name, color in colors.items():
        create_vertexcolor_layer(mesh, i, layer_name, color)
        i += 1

    obj = bpy.data.objects.new(name + "_mesh", mesh)

    # set weights
    if hasattr(data[0], "blendweights"):
        if (bones != None and len(bones) > 0 and data[0].blendweights is not None and len(data) > 0):
            num = max(256, len(bones))
            for i in range(num):
                if (i < len(bones)):
                    obj.vertex_groups.new(name=bones[i].name)
                else:
                    obj.vertex_groups.new(name="UNKNOWN_BONE." + str(i))

            for vertex_idx, vertex in enumerate(data):
                for i in range(0, 4):
                    weight = vertex.blendweights[i] / 255
                    index = vertex.blendindices[i]
                    if (weight > 0.0):
                        obj.vertex_groups[index].add(
                            [vertex_idx], weight, "ADD")

            BlenderHelper.remove_unused_vertex_groups_of_mesh(obj)

    return obj


def drawable_model_to_obj(model, materials, name, lod, bones=None):
    dobj = bpy.data.objects.new(
        SOLLUMZ_UI_NAMES[DrawableType.DRAWABLE_MODEL], None)
    dobj.sollum_type = DrawableType.DRAWABLE_MODEL
    dobj.empty_display_size = 0
    dobj.drawable_model_properties.sollum_lod = lod
    dobj.drawable_model_properties.render_mask = model.render_mask
    dobj.drawable_model_properties.flags = model.flags

    for child in model.geometries:
        child_obj = geometry_to_obj(child, bones=bones, name=name)
        child_obj.sollum_type = DrawableType.GEOMETRY
        child_obj.data.materials.append(materials[child.shader_index])
        child_obj.parent = dobj
        bpy.context.collection.objects.link(child_obj)

    bpy.context.collection.objects.link(dobj)

    return dobj


def bone_to_obj(bone, armature):

    if armature is None:
        return None

    # bpy.context.view_layer.objects.active = armature
    edit_bone = armature.data.edit_bones.new(bone.name)
    if bone.parent_index != -1:
        edit_bone.parent = armature.data.edit_bones[bone.parent_index]

    # https://github.com/LendoK/Blender_GTA_V_model_importer/blob/master/importer.py
    mat_rot = bone.rotation.to_matrix().to_4x4()
    mat_loc = Matrix.Translation(bone.translation)
    mat_sca = Matrix.Scale(1, 4, bone.scale)

    edit_bone.head = (0, 0, 0)
    edit_bone.tail = (0, 0.05, 0)
    edit_bone.matrix = mat_loc @ mat_rot @ mat_sca
    if edit_bone.parent != None:
        edit_bone.matrix = edit_bone.parent.matrix @ edit_bone.matrix

    return bone.name


def set_bone_properties(bone, armature):

    bl_bone = armature.pose.bones[bone.name].bone
    bl_bone.bone_properties.tag = bone.tag
    # LimitRotation and Unk0 have their special meanings, can be deduced if needed when exporting
    flags_restricted = set(["LimitRotation", "Unk0"])
    for _flag in bone.flags:
        if (_flag in flags_restricted):
            continue

        flag = bl_bone.bone_properties.flags.add()
        flag.name = _flag


def skeleton_to_obj(skeleton, armature):

    if skeleton is None:
        return None

    bpy.context.view_layer.objects.active = armature
    bones = skeleton.bones
    bpy.ops.object.mode_set(mode='EDIT')

    for bone in bones:
        bone_to_obj(bone, armature)

    bpy.ops.object.mode_set(mode='OBJECT')

    for bone in bones:
        set_bone_properties(bone, armature)

    return armature


def drawable_to_obj(drawable, filepath, name, bones_override=None, materials=None, return_mats=False):

    if not materials:
        materials = shadergroup_to_materials(drawable.shader_group, filepath)

    obj = None
    bones = None

    if len(drawable.skeleton.bones) > 0:
        skel = bpy.data.armatures.new(name + ".skel")
        obj = bpy.data.objects.new(name, skel)
    else:
        obj = bpy.data.objects.new(name, None)

    obj.sollum_type = DrawableType.DRAWABLE
    obj.empty_display_size = 0
    obj.drawable_properties.lod_dist_high = drawable.lod_dist_high
    obj.drawable_properties.lod_dist_med = drawable.lod_dist_med
    obj.drawable_properties.lod_dist_low = drawable.lod_dist_low
    obj.drawable_properties.lod_dist_vlow = drawable.lod_dist_vlow

    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj

    bones = None
    if len(drawable.skeleton.bones) > 0:
        bones = drawable.skeleton.bones
        skeleton_to_obj(drawable.skeleton, obj)

    if bones_override is not None:
        bones = bones_override

    if len(drawable.bound.children) > 0:
        bobj = composite_to_obj(
            drawable.bound, SOLLUMZ_UI_NAMES[BoundType.COMPOSITE], True)
        bobj.parent = obj

    for model in drawable.drawable_models_high:
        dobj = drawable_model_to_obj(
            model, materials, drawable.name, LODLevel.HIGH, bones=bones)
        dobj.parent = obj

    for model in drawable.drawable_models_med:
        dobj = drawable_model_to_obj(
            model, materials, drawable.name, LODLevel.MEDIUM, bones=bones)
        dobj.parent = obj

    for model in drawable.drawable_models_low:
        dobj = drawable_model_to_obj(
            model, materials, drawable.name, LODLevel.LOW, bones=bones)
        dobj.parent = obj

    for model in drawable.drawable_models_vlow:
        dobj = drawable_model_to_obj(
            model, materials, drawable.name, LODLevel.VERYLOW, bones=bones)
        dobj.parent = obj

    for model in obj.children:
        if model.sollum_type != DrawableType.DRAWABLE_MODEL:
            continue

        for child in model.children:
            if child.sollum_type != DrawableType.GEOMETRY:
                continue

            mod = child.modifiers.new("Armature", 'ARMATURE')
            mod.object = obj

    if return_mats:
        return obj, materials
    else:
        return obj


def import_ydr(filepath):
    try:
        ydr_xml = YDR.from_xml_file(filepath)
        drawable_to_obj(ydr_xml, filepath, os.path.basename(
            filepath.replace(YDR.file_extension, '')))
        return f"Succesfully imported : {filepath}"
    except:
        return f"Error importing : {filepath} \n {traceback.format_exc()}"
