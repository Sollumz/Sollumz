import os
import shutil
import bpy
from Sollumz.resources.drawable import *
from Sollumz.resources.shader import ShaderManager
from Sollumz.meshhelper import *
from Sollumz.tools.utils import StringHelper
from Sollumz.tools.blender_helper import BlenderHelper
from Sollumz.tools.blender_helper import *
from Sollumz.sollumz_properties import SOLLUMZ_UI_NAMES, DrawableType, MaterialType, BoundType, LODLevel
from Sollumz.ybn.ybnexport import composite_from_object


def get_used_materials(obj):

    materials = []

    for child in obj.children:
        for grandchild in child.children:
            if(grandchild.sollum_type == DrawableType.GEOMETRY):
                mats = grandchild.data.materials
                if(len(mats) < 0):
                    print(
                        f"Object: {grandchild.name} has no materials to export.")
                for mat in mats:
                    if(mat.sollum_type != MaterialType.SHADER):
                        print(
                            f"Object: {grandchild.name} has a material: {mat.name} that is not going to be exported because it is not a sollum material.")
                    materials.append(mat)

    return materials


def get_shader_index(obj, mat):
    mats = get_used_materials(obj.parent.parent)

    for i in range(len(mats)):
        if mats[i] == mat:
            return i


def get_shaders_from_blender(obj):
    shaders = []

    materials = get_used_materials(obj)
    for material in materials:
        shader = ShaderItem()
        # Maybe make this a property?
        shader.name = StringHelper.FixShaderName(material.name)
        shader.filename = material.shader_properties.filename
        shader.render_bucket = material.shader_properties.renderbucket

        for node in material.node_tree.nodes:
            if isinstance(node, bpy.types.ShaderNodeTexImage):
                param = TextureShaderParameter()
                param.name = node.name
                param.type = "Texture"
                param.texture_name = os.path.splitext(node.image.name)[0]
                shader.parameters.append(param)
            elif isinstance(node, bpy.types.ShaderNodeValue):
                if node.name[-1] == "x":
                    param = VectorShaderParameter()
                    param.name = node.name[:-2]
                    param.type = "Vector"

                    x = node
                    y = material.node_tree.nodes[node.name[:-1] + "y"]
                    z = material.node_tree.nodes[node.name[:-1] + "z"]
                    w = material.node_tree.nodes[node.name[:-1] + "w"]

                    param.x = x.outputs[0].default_value
                    param.y = y.outputs[0].default_value
                    param.z = z.outputs[0].default_value
                    param.w = w.outputs[0].default_value

                    shader.parameters.append(param)

        shaders.append(shader)

    return shaders


def texture_dictionary_from_materials(obj, materials, exportpath):
    texture_dictionary = []

    has_td = False

    t_names = []
    for mat in materials:
        nodes = mat.node_tree.nodes

        for n in nodes:
            if(isinstance(n, bpy.types.ShaderNodeTexImage)):
                if(n.texture_properties.embedded == True):
                    has_td = True
                    texture_item = TextureItem()
                    texture_name = os.path.splitext(n.image.name)[0]
                    if texture_name in t_names:
                        continue
                    else:
                        t_names.append(texture_name)
                    texture_item.name = texture_name
                    # texture_item.unk32 = 0
                    texture_item.usage = SOLLUMZ_UI_NAMES[n.texture_properties.usage]
                    for prop in dir(n.texture_flags):
                        value = getattr(n.texture_flags, prop)
                        if value == True:
                            texture_item.usage_flags.append(prop.upper())
                    texture_item.extra_flags = n.texture_properties.extra_flags
                    texture_item.width = n.image.size[0]
                    texture_item.height = n.image.size[1]
                    # ?????????????????????????????????????????????????????????????????????????????????????????????
                    texture_item.miplevels = 8
                    texture_item.format = SOLLUMZ_UI_NAMES[n.texture_properties.format]
                    texture_item.filename = n.image.name

                    texture_dictionary.append(texture_item)

                    # if(n.image != None):
                    foldername = obj.name
                    folderpath = os.path.join(exportpath, foldername)

                    if(os.path.isdir(folderpath) == False):
                        os.mkdir(folderpath)

                    txtpath = n.image.filepath
                    dstpath = folderpath + "\\" + \
                        os.path.basename(n.image.filepath)

                    # check if paths are the same because if they are no need to copy
                    if txtpath != dstpath:
                        shutil.copyfile(txtpath, dstpath)
                    # else:
                    #    print("Missing Embedded Texture, please supply texture! The texture will not be copied to the texture folder until entered!")

    if(has_td):
        return texture_dictionary
    else:
        return None


def get_blended_verts(mesh, vertex_groups, bones=None):
    bone_index_map = {}
    if(bones != None):
        for i in range(len(bones)):
            bone_index_map[bones[i].name] = i

    blend_weights = []
    blend_indices = []
    for v in mesh.vertices:
        if len(v.groups) > 0:
            bw = [0] * 4
            bi = [0] * 4
            valid_weights = 0
            total_weights = 0
            max_weights = 0
            max_weights_index = -1

            for element in v.groups:
                if element.group >= len(vertex_groups):
                    continue

                vertex_group = vertex_groups[element.group]
                bone_index = bone_index_map.get(vertex_group.name, -1)
                # 1/255 = 0.0039 the minimal weight for one vertex group
                weight = round(element.weight * 255)
                if (vertex_group.lock_weight == False and bone_index != -1 and weight > 0 and valid_weights < 4):
                    bw[valid_weights] = weight
                    bi[valid_weights] = bone_index
                    if (max_weights < weight):
                        max_weights_index = valid_weights
                        max_weights = weight
                    valid_weights += 1
                    total_weights += weight

            # weights normalization
            if valid_weights > 0 and max_weights_index != -1:
                bw[max_weights_index] = bw[max_weights_index] + \
                    (255 - total_weights)

            blend_weights.append(bw)
            blend_indices.append(bi)
        else:
            blend_weights.append([0, 0, 255, 0])
            blend_indices.append([0, 0, 0, 0])

    return blend_weights, blend_indices


def get_mesh_buffers(mesh, obj, vertex_type, bones=None):
    mesh = obj.data
    # thanks dexy
    if mesh.has_custom_normals:
        mesh.calc_normals_split()
    else:
        mesh.calc_normals()

    mesh.calc_tangents()
    mesh.calc_loop_triangles()

    blend_weights, blend_indices = get_blended_verts(
        mesh, obj.vertex_groups, bones)

    vertices = {}
    indices = []

    mesh_layer_idx = 0
    for tri in mesh.loop_triangles:
        for loop_idx in tri.loops:
            loop = mesh.loops[loop_idx]
            vert_idx = loop.vertex_index

            kwargs = {}

            if "position" in vertex_type._fields:
                kwargs['position'] = tuple(
                    obj.matrix_world @ mesh.vertices[vert_idx].co)
            if "normal" in vertex_type._fields:
                kwargs["normal"] = tuple(loop.normal)
            if "blendweights" in vertex_type._fields:
                kwargs['blendweights'] = tuple(blend_weights[vert_idx])
            if "blendindices" in vertex_type._fields:
                kwargs['blendindices'] = tuple(blend_indices[vert_idx])
            if "tangent" in vertex_type._fields:
                tangent = loop.tangent.to_4d()
                tangent[3] = loop.bitangent_sign
                kwargs["tangent"] = tuple(tangent)
            for i in range(6):
                if f"texcoord{i}" in vertex_type._fields:
                    key = f'texcoord{i}'
                    if mesh_layer_idx < len(mesh.uv_layers):
                        data = mesh.uv_layers[mesh_layer_idx].data
                        kwargs[key] = tuple(flip_uv(data[loop_idx].uv))
                        mesh_layer_idx += 1
                    else:
                        kwargs[key] = (0, 0)
            for i in range(2):
                if f"colour{i}" in vertex_type._fields:
                    key = f'colour{i}'
                    if i < len(mesh.vertex_colors):
                        data = mesh.vertex_colors[i].data
                        kwargs[key] = tuple(
                            round(val * 255) for val in data[loop_idx].color)
                    else:
                        kwargs[key] = (255, 255, 255, 255)

            vertex = vertex_type(**kwargs)

            if vertex in vertices:
                idx = vertices[vertex]
            else:
                idx = len(vertices)
                vertices[vertex] = idx

            indices.append(idx)

    return vertices.keys(), indices


def geometry_from_object(obj, bones=None):
    geometry = GeometryItem()

    depsgraph = bpy.context.evaluated_depsgraph_get()
    obj_eval = obj.evaluated_get(depsgraph)
    mesh = bpy.data.meshes.new_from_object(
        obj_eval, preserve_all_data_layers=True, depsgraph=depsgraph)

    geometry.shader_index = get_shader_index(obj, obj.active_material)

    bbmin, bbmax = get_bb_extents(obj_eval)
    geometry.bounding_box_min = bbmin
    geometry.bounding_box_max = bbmax

    materials = get_used_materials(obj.parent.parent)
    for i in range(len(materials)):
        if(materials[i] == obj_eval.active_material):
            geometry.shader_index = i

    shader_name = StringHelper.FixShaderName(obj_eval.active_material.name)
    layout = ShaderManager.shaders[shader_name].layouts[0]
    geometry.vertex_buffer.layout = layout.value

    vertex_buffer, index_buffer = get_mesh_buffers(
        mesh, obj, layout.vertex_type)

    geometry.vertex_buffer.data = vertex_buffer
    geometry.index_buffer.data = index_buffer

    return geometry


def drawable_model_from_object(obj, bones=None):
    drawable_model = DrawableModelItem()

    drawable_model.render_mask = obj.drawable_model_properties.render_mask
    drawable_model.flags = obj.drawable_model_properties.flags
    # drawable_model.hasskin = 0
    # rawable_model.bone_index = 0
    if bones is not None:
        drawable_model.unknown_1 = len(bones)

    for child in obj.children:
        if child.sollum_type == DrawableType.GEOMETRY:
            if len(child.data.materials) > 1:
                objs = BlenderHelper.split_object(child, obj)
                for obj in objs:
                    geometry = geometry_from_object(
                        obj, bones)  # MAYBE WRONG ASK LOYALIST
                    drawable_model.geometries.append(geometry)
                BlenderHelper.join_objects(objs)
            else:
                geometry = geometry_from_object(child, bones)
                drawable_model.geometries.append(geometry)

    return drawable_model


def bone_from_object(obj):

    bone = BoneItem()
    bone.name = obj.name
    bone.tag = obj.bone_properties.tag
    bone.index = obj["BONE_INDEX"]

    if obj.parent != None:
        bone.parent_index = obj.parent["BONE_INDEX"]
        children = obj.parent.children
        sibling = -1
        if len(children) > 1:
            for i, child in enumerate(children):
                if child["BONE_INDEX"] == obj["BONE_INDEX"] and i + 1 < len(children):
                    sibling = children[i + 1]["BONE_INDEX"]
                    break

        bone.sibling_index = sibling

    for flag in obj.bone_properties.flags:
        if len(flag.name) == 0:
            continue

        bone.flags.append(flag.name)

    if len(obj.children) > 0:
        bone.flags.append("Unk0")

    mat = obj.matrix_local
    if (obj.parent != None):
        mat = obj.parent.matrix_local.inverted() @ obj.matrix_local

    mat_decomposed = mat.decompose()

    bone.translation = mat_decomposed[0]
    bone.rotation = mat_decomposed[1]
    bone.scale = mat_decomposed[2]

    return bone


def skeleton_from_object(obj):

    skeleton = SkeletonProperty()
    if obj.type != 'ARMATURE' or len(obj.pose.bones) == 0:
        return None

    bones = obj.pose.bones

    ind = 0
    for pbone in bones:
        bone = pbone.bone
        bone["BONE_INDEX"] = ind
        ind = ind + 1

    for pbone in bones:
        bone = bone_from_object(pbone.bone)
        skeleton.bones.append(bone)

    return skeleton


def drawable_from_object(obj, exportpath, bones=None):
    drawable = Drawable()

    drawable.name = obj.name
    drawable.bounding_sphere_center = get_bound_center(obj)
    drawable.bounding_sphere_radius = get_obj_radius(obj)
    bbmin, bbmax = get_bb_extents(obj)
    drawable.bounding_box_min = bbmin
    drawable.bounding_box_max = bbmax

    drawable.lod_dist_high = obj.drawable_properties.lod_dist_high
    drawable.lod_dist_med = obj.drawable_properties.lod_dist_high
    drawable.lod_dist_low = obj.drawable_properties.lod_dist_high
    drawable.lod_dist_vlow = obj.drawable_properties.lod_dist_high

    shaders = get_shaders_from_blender(obj)
    for shader in shaders:
        drawable.shader_group.shaders.append(shader)

    drawable.shader_group.texture_dictionary = texture_dictionary_from_materials(
        obj, get_used_materials(obj), os.path.dirname(exportpath))

    if bones is None:
        if(obj.pose != None):
            bones = obj.pose.bones

    drawable.skeleton = skeleton_from_object(obj)

    highmodel_count = 0
    medmodel_count = 0
    lowhmodel_count = 0
    vlowmodel_count = 0

    for child in obj.children:
        if child.sollum_type == DrawableType.DRAWABLE_MODEL:
            drawable_model = drawable_model_from_object(child, bones)
            if child.drawable_model_properties.sollum_lod == LODLevel.HIGH:
                highmodel_count += 1
                drawable.drawable_models_high.append(drawable_model)
            elif child.drawable_model_properties.sollum_lod == LODLevel.MEDIUM:
                medmodel_count += 1
                drawable.drawable_models_med.append(drawable_model)
            elif child.drawable_model_properties.sollum_lod == LODLevel.LOW:
                lowhmodel_count += 1
                drawable.drawable_models_low.append(drawable_model)
            elif child.drawable_model_properties.sollum_lod == LODLevel.VERYLOW:
                vlowmodel_count += 1
                drawable.drawable_models_vlow.append(drawable_model)
        elif child.sollum_type == BoundType.COMPOSITE:
            drawable.bound = composite_from_object(child)

    if not len(drawable.bound.children) > 0:
        drawable.bound = None

    # flags = model count for each lod
    drawable.flags_high = highmodel_count
    drawable.flags_med = medmodel_count
    drawable.flags_low = lowhmodel_count
    drawable.flags_vlow = vlowmodel_count
    # drawable.unknown_9A = ?

    return drawable
