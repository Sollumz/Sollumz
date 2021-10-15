import bpy
from bpy_extras.io_utils import ExportHelper
from Sollumz.resources.drawable import *
from Sollumz.resources.shader import ShaderManager
import os, sys, traceback
from Sollumz.meshhelper import *
from Sollumz.tools.utils import *

sys.path.append(os.path.dirname(__file__))

def get_used_materials(obj):
    
    materials = []
    
    for child in obj.children:
        for grandchild in child.children:
            if(grandchild.sollum_type == "sollumz_geometry"):
                mat = grandchild.active_material
                if(mat != None):
                    materials.append(mat)          

    return materials

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
                if(node.image != None):
                    param.texture_name = os.path.splitext(node.image.name)[0]
                else:
                    param.texture_name = "givemechecker"
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

def get_index_string(mesh):
    
    index_string = ""
    
    i = 0
    for poly in mesh.polygons:
        for loop_index in range(poly.loop_start, poly.loop_start + poly.loop_total):
            index_string += str(mesh.loops[loop_index].vertex_index) + " "
            i += 1
            if(i == 24): # MATCHES CW's FORMAT
                index_string += "\n"
                i = 0

    return index_string

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

def meshloopcolor_tostring(color):
    try:
        string = ""
        string += str(round(color[0] * 255)) + " "
        string += str(round(color[1] * 255)) + " "
        string += str(round(color[2] * 255)) + " "
        string += str(round(color[3] * 255))
        return string 
    except:
        return None

def order_vertex_list(list, vlayout):

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

    newlist = []

    for i in range(len(vlayout)):
        layout_key = layout_map[vlayout[i]]
        if layout_key != None:
            if list[layout_key] == None:
                raise TypeError("Missing layout item " + vlayout[i])

            newlist.append(list[layout_key])
        else:
            print('Incorrect layout element', vlayout[i])

    if (len(newlist) != len(vlayout)):
        print('Incorrect layout parse')

    return newlist

def get_vertex_string(obj, mesh, layout, bones=None):

    mesh = obj.data

    allstrings = []
    allstrings.append("\n") #makes xml a little prettier
    
    vertamount = len(mesh.vertices)
    vertices = [None] * vertamount
    normals = [None] * vertamount
    clr = [None] * vertamount
    clr1 = [None] * vertamount
    texcoords = {}
    tangents = [None] * vertamount
    blendw = [[]] * vertamount
    blendi = [[]] * vertamount

    for i in range(6):
        texcoords[i] = [None] * vertamount       
    
    if mesh.has_custom_normals:
        mesh.calc_normals_split()
    else:
        mesh.calc_normals()

    mesh.calc_tangents()

    vertex_groups = obj.vertex_groups

    bones_index_dict = {}
    if(bones != None):
        for i in range(len(bones)):
            bones_index_dict[bones[i].name] = i

    clr0_layer = None 
    clr1_layer = None
    if(mesh.vertex_colors == None):
        clr0_layer = mesh.vertex_colors.new()
        clr1_layer = mesh.vertex_colors.new()
    else:
        clr0_layer = mesh.vertex_colors[0]
        if len(mesh.vertex_colors) >= 2:
            clr1_layer = mesh.vertex_colors[1]
        else:
            clr1_layer = mesh.vertex_colors.new()

    for uv_layer_id in range(len(mesh.uv_layers)):
        uv_layer = mesh.uv_layers[uv_layer_id].data
        for poly in mesh.polygons:
            for loop_index in range(poly.loop_start, poly.loop_start + poly.loop_total):
                vi = mesh.loops[loop_index].vertex_index
                uv = process_uv(uv_layer[loop_index].uv)
                u = uv[0]
                v = uv[1]
                fixed_uv = Vector((u, v))
                texcoords[uv_layer_id][vi] = fixed_uv

    for poly in mesh.polygons:
        for loop_index in range(poly.loop_start, poly.loop_start + poly.loop_total):
            vi = mesh.loops[loop_index].vertex_index
            vertices[vi] = mesh.vertices[vi].co
            # normals[vi] = mesh.vertices[vi].normal
            normals[vi] = mesh.loops[loop_index].normal
            clr[vi] = clr0_layer.data[loop_index].color
            clr1[vi] = clr1_layer.data[loop_index].color
            tangents[vi] = mesh.loops[loop_index].tangent.to_4d()
            # https://github.com/labnation/MonoGame/blob/master/MonoGame.Framework.Content.Pipeline/Graphics/MeshHelper.cs#L298
            # bitangent = bitangent_sign * cross(normal, tangent)
            tangents[vi].w = mesh.loops[loop_index].bitangent_sign
            #FIXME: one vert can only be influenced by 4 weights at most
            vertex_group_elements = mesh.vertices[vi].groups

            if len(vertex_group_elements) > 0:
                blendw[vi] = [0] * 4
                blendi[vi] = [0] * 4
                valid_weights = 0
                total_weights = 0
                max_weights = 0
                max_weights_index = -1

                for element in vertex_group_elements:
                    if element.group >= len(vertex_groups):
                        continue

                    vertex_group = vertex_groups[element.group]
                    bone_index = bones_index_dict.get(vertex_group.name, -1)
                    # 1/255 = 0.0039 the minimal weight for one vertex group
                    weight = round(element.weight * 255)
                    if (vertex_group.lock_weight == False and bone_index != -1 and weight > 0 and valid_weights < 4):
                        blendw[vi][valid_weights] = weight
                        blendi[vi][valid_weights] = bone_index
                        if (max_weights < weight):
                            max_weights_index = valid_weights
                            max_weights = weight

                        valid_weights += 1
                        total_weights += weight

                # weights verification stuff
                # wtf rockstar
                # why do you even use int for weights
                if valid_weights > 0 and max_weights_index != -1:
                    blendw[vi][max_weights_index] = blendw[vi][max_weights_index] + (255 - total_weights)
            else:
                blendw[vi] = [0, 0, 255, 0]
                blendi[vi] = [0] * 4

    for i in range(len(vertices)):
        vstring = ""
        tlist = []
        tlist.append(vector_tostring(vertices[i])) 
        tlist.append(vector_tostring(normals[i])) 
        tlist.append(meshloopcolor_tostring(clr[i])) 
        tlist.append(meshloopcolor_tostring(clr1[i]))
        tlist.append(vector_tostring(texcoords[0][i])) 
        tlist.append(vector_tostring(texcoords[1][i]))
        tlist.append(vector_tostring(texcoords[2][i]))
        tlist.append(vector_tostring(texcoords[3][i]))
        tlist.append(vector_tostring(texcoords[4][i]))
        tlist.append(vector_tostring(texcoords[5][i]))
        tlist.append(vector_tostring(tangents[i]))
        tlist.append(' '.join(str(j) for j in blendw[i]))
        tlist.append(' '.join(str(j) for j in blendi[i]))
        
        layoutlist = order_vertex_list(tlist, layout)
        
        for l in layoutlist:
            vstring += l 
            vstring += " " * 3
        vstring += "\n" 
        allstrings.append(vstring) 
            
    vertex_string = ""
    for s in allstrings:       
        vertex_string += s
    
    return vertex_string

def geometry_from_object(obj, bones=None):
    geometry = GeometryItem()

    depsgraph = bpy.context.evaluated_depsgraph_get()
    obj_eval = obj.evaluated_get(depsgraph)
    mesh = bpy.data.meshes.new_from_object(obj, preserve_all_data_layers=True, depsgraph=depsgraph)

    bbmin, bbmax = get_bb_extents(obj_eval)
    geometry.bounding_box_min = bbmin
    geometry.bounding_box_max = bbmax
    
    materials = get_used_materials(obj_eval.parent.parent)
    for i in range(len(materials)):
        if(materials[i] == obj_eval.active_material):
            geometry.shader_index = i

    sm = ShaderManager()
    layout = sm.shaders[FixShaderName(obj_eval.active_material.name)].layouts["0x0"]
    for l in layout:
        geometry.vertex_buffer.layout.append(VertexLayoutItem(l))
    geometry.vertex_buffer.data = get_vertex_string(obj_eval, mesh, layout, bones)
    geometry.index_buffer.data = get_index_string(mesh)
    
    return geometry

def drawable_model_from_object(obj, bones=None):
    drawable_model = DrawableModelItem()

    drawable_model.render_mask = obj.drawable_model_properties.render_mask
    drawable_model.flags = obj.drawable_model_properties.flags
    #drawable_model.hasskin = 0
    #rawable_model.bone_index = 0
    if bones is not None:
        drawable_model.unknown_1 = len(bones)

    for child in obj.children:
        if(child.sollum_type == "sollumz_geometry"):
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
        return skeleton

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

def drawable_from_object(obj, bones=None):
    drawable = Drawable()

    drawable.name = obj.name
    drawable.bounding_sphere_center = get_bound_center(obj)
    drawable.bounding_sphere_radius  = get_obj_radius(obj)
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

    #drawable.shader_group.texture_dictionary = None #NOT IMPLEMENTED

    if bones is None:
        if(obj.pose != None):
            bones = obj.pose.bones

    drawable.skeleton = skeleton_from_object(obj)

    highmodel_count = 0
    medmodel_count = 0
    lowhmodel_count = 0
    vlowmodel_count = 0

    for child in obj.children:
        if(child.sollum_type == "sollumz_drawable_model"):
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

    #flags = model count for each lod 
    drawable.flags_high = highmodel_count
    drawable.flags_med = medmodel_count
    drawable.flags_low = lowhmodel_count
    drawable.flags_vlow = vlowmodel_count
    #drawable.unknown_9A = ?

    return drawable
    
