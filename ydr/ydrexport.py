import bpy
from Sollumz.resources.drawable import *
from Sollumz.resources.shader import ShaderManager
import os
import sys
import shutil
from Sollumz.meshhelper import *
from Sollumz.tools.utils import *
from Sollumz.tools.blender_helper import *
from Sollumz.sollumz_properties import SOLLUMZ_UI_NAMES, DrawableType, MaterialType, BoundType
from Sollumz.ybn.ybnexport import composite_from_object

sys.path.append(os.path.dirname(__file__))


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
                    if(mat.sollum_type != MaterialType.MATERIAL):
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
        shader.name = FixShaderName(material.name)
        shader.filename = material.shader_properties.filename
        shader.render_bucket = material.shader_properties.renderbucket

        for node in material.node_tree.nodes:
            if(isinstance(node, bpy.types.ShaderNodeTexImage)):
                param = TextureParameterItem()
                param.name = node.name
                param.type = "Texture"
                param.texture_name = os.path.splitext(node.image.name)[0]
                shader.parameters.append(param)
            elif(isinstance(node, bpy.types.ShaderNodeValue)):
                if(node.name[-1] == "x"):
                    param = ValueParameterItem()
                    param.name = node.name[:-2]
                    param.type = "Vector"

                    x = node
                    y = material.node_tree.nodes[node.name[:-1] + "y"]
                    z = material.node_tree.nodes[node.name[:-1] + "z"]
                    w = material.node_tree.nodes[node.name[:-1] + "w"]

                    param.quaternion_x = x.outputs[0].default_value
                    param.quaternion_y = y.outputs[0].default_value
                    param.quaternion_z = z.outputs[0].default_value
                    param.quaternion_w = w.outputs[0].default_value

                    shader.parameters.append(param)

        shaders.append(shader)

    return shaders


def texture_dictionary_from_materials(obj, materials, exportpath):
    texture_dictionary = []

    has_td = False

    for mat in materials:
        nodes = mat.node_tree.nodes

        for n in nodes:
            if(isinstance(n, bpy.types.ShaderNodeTexImage)):
                if(n.texture_properties.embedded == True):
                    has_td = True
                    texture_item = TextureItem()
                    texture_item.name = os.path.splitext(n.image.name)[0]
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
                    folderpath = exportpath + foldername

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


def process_uv(uv):
    u = uv[0]
    v = (uv[1] - 1.0) * -1

    return [u, v]


def vector_tostring(vector):
    try:
        string = [str(vector.x), str(vector.y)]
        if(hasattr(vector, "z")):
            string.append(str(vector.z))

        if(hasattr(vector, "w")):
            string.append(str(vector.w))

        return " ".join(string)
    except:
        return None


def list_tostring(list):
    try:
        string = ""
        string += str(round(list[0])) + " "
        string += str(round(list[1])) + " "
        string += str(round(list[2])) + " "
        string += str(round(list[3]))
        return string
    except:
        return None


def order_vertex_list(vertex, layout):

    layout_map = {
        "Position": 0,
        "Normal": 1,
        "Colour0": 2,
        "Colour1": 3,
        "TexCoord0": 4,
        "TexCoord1": 5,
        "TexCoord2": 6,
        "TexCoord3": 7,
        "TexCoord4": 8,
        "TexCoord5": 9,
        "Tangent": 10,
        "BlendWeights": 11,
        "BlendIndices": 12,
    }

    ordered = []

    for i in range(len(layout)):
        layout_key = layout_map[layout[i]]
        if layout_key != None:
            if vertex[layout_key] == None:
                raise TypeError("Missing layout item " + layout[i])

            ordered.append(vertex[layout_key])
        else:
            print('Incorrect layout element', layout[i])

    if (len(ordered) != len(layout)):
        print('Incorrect layout parse')

    result = ""

    for data in ordered:
        # vector
        if hasattr(data, "x"):
            result += vector_tostring(data) + " "
        # color
        elif(isinstance(data, list)):
            result += list_tostring(data) + " "
        # floats
        else:
            result.join(' '.join(str(j) for j in data[i]))

    return result


def mesh_to_buffers(obj, mesh, layout, bones=None):
    # thanks dexy
    if mesh.has_custom_normals:
        mesh.calc_normals_split()
    else:
        mesh.calc_normals()

    mesh.calc_tangents()
    mesh.calc_loop_triangles()

    bones_index_dict = {}
    if(bones != None):
        for i in range(len(bones)):
            bones_index_dict[bones[i].name] = i
    vertex_groups = obj.vertex_groups

    vertex_strings = {}
    index_strings = []
    for tri in mesh.loop_triangles:
        for loop_idx in tri.loops:
            loop = mesh.loops[loop_idx]
            vert_idx = loop.vertex_index
            position = (obj.matrix_world @ mesh.vertices[vert_idx].co)
            normal = loop.normal
            texcoord = {}
            for i in range(6):
                texcoord[i] = [None] * 2
            for i in range(len(mesh.uv_layers)):
                data = mesh.uv_layers[i].data
                texcoord[i] = data[loop_idx].uv
            color = {}
            for i in range(2):
                color[i] = [None] * 4
            if len(mesh.vertex_colors) > 0:
                for i in range(len(mesh.vertex_colors)):
                    data = mesh.vertex_colors[i].data
                    clr = data[loop_idx].color
                    color[i] = [clr[0] * 255, clr[1] *
                                255, clr[2] * 255, clr[3] * 255]
            else:
                for i in range(len(color)):
                    color[i] = [255, 255, 255, 255]

            tangent = loop.tangent.to_4d()
            tangent[3] = loop.bitangent_sign

            string = order_vertex_list([position, normal, color[0], color[1], texcoord[0],
                                        texcoord[1], texcoord[2], texcoord[3], texcoord[4], texcoord[5], tangent], layout)

            if string in vertex_strings:
                idx = vertex_strings[string]
            else:
                idx = len(vertex_strings)
                vertex_strings[string] = idx

            index_strings.append(str(idx))
            if len(index_strings) % 24 == 0:  # dexys "hack"
                index_strings.append("\n")

    vertex_buffer = '\n'.join(vertex_strings)
    index_buffer = ' '.join(index_strings)

    return vertex_buffer, index_buffer


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

    sm = ShaderManager()
    layout = sm.shaders[FixShaderName(
        obj_eval.active_material.name)].layouts["0x0"]
    for l in layout:
        geometry.vertex_buffer.layout.append(VertexLayoutItem(l))

    vertex_buffer, index_buffer = mesh_to_buffers(obj_eval, mesh, layout)

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
        if(child.sollum_type == DrawableType.GEOMETRY):
            if(len(child.data.materials) > 1):
                objs = split_object(child, obj)
                for obj in objs:
                    geometry = geometry_from_object(
                        obj, bones)  # MAYBE WRONG ASK LOYALIST
                    drawable_model.geometries.append(geometry)
                join_objects(objs)
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


def drawable_from_object(obj, bones=None, exportpath=""):
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
        obj, get_used_materials(obj), exportpath)

    if bones is None:
        if(obj.pose != None):
            bones = obj.pose.bones

    drawable.skeleton = skeleton_from_object(obj)

    highmodel_count = 0
    medmodel_count = 0
    lowhmodel_count = 0
    vlowmodel_count = 0

    for child in obj.children:
        if(child.sollum_type == DrawableType.DRAWABLE_MODEL):
            drawable_model = drawable_model_from_object(child, bones)
            if("high" in child.drawable_model_properties.sollum_lod):
                highmodel_count += 1
                drawable.drawable_models_high.append(drawable_model)
            elif("med" in child.drawable_model_properties.sollum_lod):
                medmodel_count += 1
                drawable.drawable_models_med.append(drawable_model)
            elif("low" in child.drawable_model_properties.sollum_lod):
                lowhmodel_count += 1
                drawable.drawable_models_low.append(drawable_model)
            elif("vlow" in child.drawable_model_properties.sollum_lod):
                vlowmodel_count += 1
                drawable.drawable_models_vlow.append(drawable_model)
        elif(child.sollum_type == BoundType.COMPOSITE):
            drawable.bound = composite_from_object(child)

    # flags = model count for each lod
    drawable.flags_high = highmodel_count
    drawable.flags_med = medmodel_count
    drawable.flags_low = lowhmodel_count
    drawable.flags_vlow = vlowmodel_count
    # drawable.unknown_9A = ?

    return drawable
