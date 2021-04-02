import bpy
from bpy_extras.io_utils import ExportHelper
from bpy.types import Operator
from bpy.props import StringProperty
from xml.etree import ElementTree
from xml.etree.ElementTree import Element, SubElement, Comment, tostring
from xml.dom import minidom
from mathutils import Vector, Matrix
import os 
import sys 
import shutil
import ntpath
from datetime import datetime 
from . import shaderoperators as Shader

def prettify(elem):
    rough_string = tostring(elem, encoding='UTF-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent=" ")

def get_obj_children(obj):
    children = [] 
    objects = bpy.context.scene.objects
    for ob in obj.children: 
        if objects.get(ob.name):
            children.append(ob) 

    return children 

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
    
def process_uv(uv):
    u = uv[0]
    v = (uv[1] - 1.0) * -1

    return [u, v]

def get_vertex_string(obj, vlayout, bones, depsgraph):
    mesh = bpy.data.meshes.new_from_object(obj, preserve_all_data_layers=True, depsgraph=depsgraph)
    # mesh = obj.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
    # mesh = obj.data
    
    allstrings = []
    allstrings.append("\n") #makes xml a little prettier
    
    vertamount = len(mesh.vertices)
    vertices = [None] * vertamount
    normals = [None] * vertamount
    clr = [None] * vertamount
    clr1 = [None] * vertamount
    texcoords = {}
    tangents = [None] * vertamount
    blendw = [None] * vertamount
    blendi = [None] * vertamount

    for i in range(6):
        texcoords[i] = [None] * vertamount       
    
    if mesh.has_custom_normals:
        mesh.calc_normals_split()
    else:
        mesh.calc_normals()

    mesh.calc_tangents()

    vertex_groups = obj.vertex_groups

    bones_index_dict = {}
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
                blendw_list = []
                blendi_list = []
                valid_weights = 0
                total_weights = 0
                max_weights = 0
                max_weights_position = -1

                for element in vertex_group_elements:
                    if element.group >= len(vertex_groups):
                        continue

                    vertex_group = vertex_groups[element.group]
                    bone_index = bones_index_dict.get(vertex_group.name, -1)
                    # 1/255 = 0.0039 the minimal weight for one vertex group
                    weight = round(element.weight * 255)
                    if (vertex_group.lock_weight == False and bone_index != -1 and weight > 0 and valid_weights < 4):
                        blendw_list.append(weight)
                        blendi_list.append(bone_index)
                        if (max_weights < weight):
                            max_weights_position = valid_weights
                            max_weights = weight

                        valid_weights += 1
                        total_weights += weight

                #fill the positions where there are no weights
                if valid_weights < 4:
                    for i in range(4 - valid_weights):
                        blendw_list.append(0)
                        blendi_list.append(0)

                # weights verification stuff
                # wtf rockstar
                # why do you even use int for weights
                if valid_weights > 0 and max_weights_position != -1:
                    blendw_list[max_weights_position] = blendw_list[max_weights_position] + (255 - total_weights)

                blendw[vi] = ' '.join(str(i) for i in blendw_list)
                blendi[vi] = ' '.join(str(i) for i in blendi_list)
            else:
                blendw[vi] = "0 0 255 0"
                blendi[vi] = "0 0 0 0"
            
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
        tlist.append(blendw[i])
        tlist.append(blendi[i])
        
        layoutlist = order_vertex_list(tlist, vlayout)
        
        vstring = " " * 5
        for l in layoutlist:
            vstring += l 
            vstring += " " * 3
        vstring += "\n" 
        allstrings.append(vstring) 
            
    vertex_string = ""
    for s in allstrings:       
        vertex_string += s
    
    return vertex_string

def get_index_string(mesh):
    
    index_string = ""
    
    for poly in mesh.polygons:
        for loop_index in range(poly.loop_start, poly.loop_start + poly.loop_total):
            index_string += str(mesh.loops[loop_index].vertex_index) + " "
            
    return index_string

def fix_shader_name(name, no_extension = False): #because blender renames everything to .00X
    newname = ""
    n = name.split(".")
    if(len(n) == 3):
        newname += n[0]
        newname += "."  
        newname += n[1]
    else:
        newname = name
    if(no_extension):
        newname = newname[:-4]
    return newname

def get_vertex_layout(shader):
    shader = fix_shader_name(shader) 

    parameter_set = Shader.shaders.get(shader)
    if parameter_set is not None:
        for p in parameter_set:
            if p.Type == "Layout":
                return p.get_value()

    print('Unknown shader: ', shader)

def write_model_node(objs, materials, bones):
    
    m_node = Element("Item")
    rm_node = Element("RenderMask")
    rm_node.set("value", str(objs[0].mask))
    flags_node = Element("Flags")
    flags_node.set("value", "1")
    has_skin_node = Element("HasSkin")
    if len(objs[0].vertex_groups) > 0:
        has_skin_node.set("value", "1")
    else:
        has_skin_node.set("value", "0")

    bone_index_node = Element("BoneIndex")
    bone_index_node.set("value", "0")

    unk1_node = Element("Unknown1")
    if bones != None:
        unk1_node.set("value", str(len(bones)))
    else:
        unk1_node.set("value", "0")

    geo_node = Element("Geometries")

    # depsgraph stuff, for the purpose of auto-applying modifiers on exporting
    depsgraph = bpy.context.evaluated_depsgraph_get()
    for obj in objs:
        obj_eval = obj.evaluated_get(depsgraph)
        model = bpy.data.meshes.new_from_object(obj_eval, preserve_all_data_layers=True, depsgraph=depsgraph)
        #model = obj.data
        
        i_node = Element("Item")
        
        shader_index = 0
        shader = None
        for idx in range(len(materials)):
            if(model.materials[0] == materials[idx]):
                shader_index = idx
                shader = materials[idx] 
        shd_index = Element("ShaderIndex")
        shd_index.set("value", str(shader_index))
        
        bound_box_min = obj.bound_box[0] 
        bound_box_max = obj.bound_box[6]
        
        bbmin_node = Element("BoundingBoxMin")
        bbmin_node.set("x", str(bound_box_min[0]))
        bbmin_node.set("y", str(bound_box_min[1]))
        bbmin_node.set("z", str(bound_box_min[2]))
        bbmin_node.set("w", "0")
        bbmax_node = Element("BoundingBoxMax")
        bbmax_node.set("x", str(bound_box_max[0]))
        bbmax_node.set("y", str(bound_box_max[1]))  
        bbmax_node.set("z", str(bound_box_max[2]))
        bbmax_node.set("w", "0")

        boneids_node = Element("BoneIDs")
        if bones != None:
            boneids_node.text = ", ".join(str(i) for i in range(len(bones)))

        vb_node = Element("VertexBuffer")
        vbflags_node = Element("Flags")
        vbflags_node.set("value", "0")
        
        vblayout_node = Element("Layout")
        vblayout_node.set("type", "GTAV1")
        
        if(shader.sollumtype != "GTA"):
            print("Error Material Type Is Not GTA!!")
            return m_node
        
        print('Processing shader', shader_index, shader.name)
        vlayout = get_vertex_layout(shader.name)

        data2_node = Element("Data2")
        vertex_str = get_vertex_string(obj_eval, vlayout, bones, depsgraph)
        data2_node.text = vertex_str
        
        ib_node = Element("IndexBuffer")
        data_node = Element("Data")
        data_node.text = get_index_string(model)

        ib_node.append(data_node)
        
        for p in vlayout:
            p_node = Element(p)
            vblayout_node.append(p_node)
        
        vb_node.append(vbflags_node)
        vb_node.append(vblayout_node)
        vb_node.append(data2_node)
        
        i_node.append(shd_index)
        i_node.append(bbmin_node)
        i_node.append(bbmax_node)
        i_node.append(boneids_node)
        i_node.append(vb_node)
        i_node.append(ib_node)
        
        geo_node.append(i_node)
    
    m_node.append(rm_node)
    m_node.append(flags_node)
    m_node.append(has_skin_node)
    m_node.append(bone_index_node)
    m_node.append(unk1_node)
    m_node.append(geo_node)
    
    #print(prettify(m_node))
    
    return m_node
    
def write_drawablemodels_node(models, materials, bones):
    
    high_models = []
    med_models = []
    low_models = []
    
    for obj in models:
        if(obj.level_of_detail == "High"):
            high_models.append(obj)
        if(obj.level_of_detail == "Medium"):
            med_models.append(obj)
        if(obj.level_of_detail == "Low"):
            low_models.append(obj)
    
    drawablemodels_high_node = None
    drawablemodels_med_node = None 
    drawablemodels_low_node = None 
    
    if(len(high_models) != 0):
        drawablemodels_high_node = Element("DrawableModelsHigh")
        drawablemodels_high_node.append(write_model_node(high_models, materials, bones))
    if(len(med_models) != 0):
        drawablemodels_med_node = Element("DrawableModelsMedium")
        drawablemodels_med_node.append(write_model_node(med_models, materials, bones))
    if(len(low_models) != 0):
        drawablemodels_low_node = Element("DrawableModelsLow")
        drawablemodels_low_node.append(write_model_node(low_models, materials, bones))
    
    dm_nodes = []
    if(drawablemodels_high_node != None):
        dm_nodes.append(drawablemodels_high_node)
    if(drawablemodels_med_node != None):
        dm_nodes.append(drawablemodels_med_node)
    if(drawablemodels_low_node != None):
        dm_nodes.append(drawablemodels_low_node)
    
    return dm_nodes

def write_imageparam_node(node):
    
    paramname = node.name 
    
    #if the same parameter is imported multiple time naming gets prefixed with .00X 
    #if("." in paramname): 
    #    split = paramname.split(".")
       # paramname = split[0]
        
    iname = node.name 
    type = "Texture"
    tname = "None" #givemechecker? 
    
    #if(node.image != None):
        #tname = os.path.basename(node.image.filepath)
    tname = node.texture_name[:-4] #delete file extension
    
    i_node = Element("Item")
    i_node.set("name", iname)
    i_node.set("type", type)

    if (tname != None and len(tname) > 0):
        name_node = Element("Name")
        name_node.text = tname
    
        unk32_node = Element("Unk32")
        unk32_node.set("value", "128")
    
        i_node.append(name_node)
        i_node.append(unk32_node)
    
    return i_node 

#some parameters use y,z,w
def write_vectorparam_node(nodes):
    
    i_node = Element("Item")
    
    name = nodes[0].name[:-2] #remove _x
    type = "Vector"
    
    i_node.set("name", name)
    i_node.set("type", type)
    i_node.set("x", str(nodes[0].outputs[0].default_value))
    i_node.set("y", str(nodes[1].outputs[0].default_value))
    i_node.set("z", str(nodes[2].outputs[0].default_value))
    i_node.set("w", str(nodes[3].outputs[0].default_value))
    
    return i_node

def write_shader_node(mat):
    
    i_node = Element("Item")
    
    name_node = Element("Name")
    name_node.text = fix_shader_name(mat.name, True)
    
    filename_node = Element("FileName")
    filename_node.text = fix_shader_name(mat.name) 
    
    renderbucket_node = Element("RenderBucket")
    renderbucket_node.set("value", "0")
    parameter_set = Shader.shaders.get(fix_shader_name(mat.name))
    if parameter_set is not None:
        for p in parameter_set:
            if p.Type == "RenderBucket":
                renderbucket_node = p.write()
                break
    
    params_node = Element("Parameters")
    
    mat_nodes = mat.node_tree.nodes
    for node in mat_nodes:
        if(isinstance(node, bpy.types.ShaderNodeTexImage)):
            imgp_node = write_imageparam_node(node)
            params_node.append(imgp_node) 
        if(isinstance(node, bpy.types.ShaderNodeValue)):
            if(node.name[-1] == "x"):
                x = node
                y = mat_nodes[node.name[:-1] + "y"]
                z = mat_nodes[node.name[:-1] + "z"]
                w = mat_nodes[node.name[:-1] + "w"]
                vnode = write_vectorparam_node([x, y, z, w])
                params_node.append(vnode)
    
    i_node.append(name_node)
    i_node.append(filename_node)
    i_node.append(renderbucket_node)
    i_node.append(params_node)
    
    return i_node
    

def write_shaders_node(materials):
    
    shaders_node = Element("Shaders")

    for mat in materials:
        shader_node = write_shader_node(mat)
        shaders_node.append(shader_node)
        
    #print(prettify(shader_node))    
    
    return shaders_node

def write_tditem_node(exportpath, mat):
    
    i_nodes = []
    
    mat_nodes = mat.node_tree.nodes
    for node in mat_nodes:
        if(isinstance(node, bpy.types.ShaderNodeTexImage)):
            
            if(node.embedded == False):
                i_nodes.append(None)
            else:
                if(node.image != None):
                    
                
                    foldername = "\\" + os.path.splitext(os.path.splitext(os.path.basename(exportpath))[0])[0]
                    
                    if(os.path.isdir(os.path.dirname(exportpath) + foldername) == False):
                        os.mkdir(os.path.dirname(exportpath) + foldername)
                    
                    txtpath = node.image.filepath
                    dstpath = os.path.dirname(exportpath) + foldername + "\\" + os.path.basename(node.image.filepath)
                    
                    # SameFileError
                    if txtpath != dstpath:
                        shutil.copyfile(txtpath, dstpath)
                else:
                    print("Missing Embedded Texture, please supply texture! The texture will not be copied to the texture folder until entered!")

                #node.image.save_render(os.path.dirname(exportpath) + "\\untitled\\"+ os.path.basename(node.image.filepath), scene=None)
                
                i_node = Element("Item")
                
                name_node = Element("Name")
                name_node.text = os.path.splitext(node.texture_name)[0]
                i_node.append(name_node)
                
                unk32_node = Element("Unk32")
                unk32_node.set("value", "128")
                i_node.append(unk32_node)
                
                usage_node = Element("Usage")
                usage_node.text = node.usage
                i_node.append(usage_node)
                
                uflags_node = Element("UsageFlags")
                uflags_text = "" 
                 
                if(node.not_half == True):
                    uflags_text += "NOT_HALF, "
                if(node.hd_split == True):
                    uflags_text += "HD_SPLIT, "
                if(node.flag_full == True):
                    uflags_text += "FULL, "
                if(node.maps_half == True):
                    uflags_text += "MAPS_HALF, "
                if(node.x2 == True):
                    uflags_text += "X2, "
                if(node.x4 == True):
                    uflags_text += "X4, "
                if(node.y4 == True):
                    uflags_text += "Y4, "
                if(node.x8 == True):
                    uflags_text += "MAPS_HALF, "
                if(node.x16 == True):
                    uflags_text += "X16, "
                if(node.x32 == True):
                    uflags_text += "X32, "
                if(node.x64 == True):
                    uflags_text += "X64, "
                if(node.y64 == True):
                    uflags_text += "Y64, "
                if(node.x128 == True):
                    uflags_text += "X128, "
                if(node.x256 == True):
                    uflags_text += "X256, "
                if(node.x512 == True):
                    uflags_text += "X512, "
                if(node.y512 == True):
                    uflags_text += "Y512, "
                if(node.x1024 == True):
                    uflags_text += "X1024, "
                if(node.y1024 == True):
                    uflags_text += "Y1024, "
                if(node.x2048 == True):
                    uflags_text += "X2048, "
                if(node.y2048 == True):
                    uflags_text += "Y2048, "
                if(node.embeddedscriptrt == True):
                    uflags_text += "EMBEDDEDSCRIPTRT, "
                if(node.unk19 == True):
                    uflags_text += "UNK19, "
                if(node.unk20 == True):
                    uflags_text += "UNK20, "
                if(node.unk21 == True):
                    uflags_text += "UNK21, "
                if(node.unk24 == True):
                    uflags_text += "UNK24, "
                
                uflags_text = uflags_text[:-2] #remove , from str
                uflags_node.text = uflags_text
                
                i_node.append(uflags_node)

                eflags_node = Element("ExtraFlags")
                eflags_node.set("value", str(node.extra_flags))
                i_node.append(eflags_node)
                
                width_node = Element("Width")
                
                size = [0, 0]
                if(node.image != None):
                    size = node.image.size
                    
                width_node.set("value", str(size[0]))
                i_node.append(width_node)
                
                height_node = Element("Height")
                height_node.set("value", str(size[1]))
                i_node.append(height_node)
                
                miplevels_node = Element("MipLevels")
                miplevels_node.set("value", "8")
                i_node.append(miplevels_node)
                
                format_node = Element("Format")
                format_node.text = "D3DFMT_" + node.format_type
                i_node.append(format_node)
                
                filename_node = Element("FileName")
                filename_node.text = node.texture_name
                i_node.append(filename_node)
                
                i_nodes.append(i_node)
                    
    return i_nodes 

def write_texturedictionary_node(materials, exportpath):
    
    td_node = Element("TextureDictionary")
    
    all_nodes = []
    
    for mat in materials:
        i_nodes = write_tditem_node(exportpath, mat)
        
        for node in i_nodes:
            if(node != None):
                all_nodes.append(node)
    
    #removes duplicate embedded textures!
    for node in all_nodes: 
        t_name = node[0].text
        
        append = True 
        
        for t in td_node:
            if(t[0].text == t_name):
                append = False
                
        if(append == True):
            td_node.append(node)        
    
    return td_node

def write_shader_group_node(materials, filepath):
    
    shaderg_node = Element("ShaderGroup")
    unk30_node = Element("Unknown30")
    unk30_node.set("value", "0")
    
    td_node = write_texturedictionary_node(materials, filepath)
    
    shader_node = write_shaders_node(materials)
    
    shaderg_node.append(unk30_node)
    shaderg_node.append(td_node)
    shaderg_node.append(shader_node)
    
    return shaderg_node

def write_skeleton_node(obj):
    bones = obj.pose.bones
    if len(bones) == 0:
        return None

    skeleton_node = Element("Skeleton")

    #TODO: the current implementation works but IMHO there should be something more meaningful than "0"
    #as long as it doesn't break in game
    unk1c_node = Element("Unknown1C")
    unk1c_node.set("value", "16777216")

    unk50_node = Element("Unknown50")
    unk50_node.set("value", "0")

    unk54_node = Element("Unknown54")
    unk54_node.set("value", "0")

    unk58_node = Element("Unknown58")
    unk58_node.set("value", "0")

    bones_node = Element("Bones")

    skeleton_node.append(unk1c_node)
    skeleton_node.append(unk50_node)
    skeleton_node.append(unk54_node)
    skeleton_node.append(unk58_node)
    skeleton_node.append(bones_node)

    ind = 0
    for pbone in bones:
        bone = pbone.bone
        bone["BONE_INDEX"] = ind
        ind = ind + 1

    for pbone in bones:
        bone = pbone.bone

        bone_node = Element("Item")

        bone_node_name = Element("Name")
        bone_node_name.text = bone.name
        bone_node.append(bone_node_name)

        bone_node_tag = Element("Tag")

        bone_node_tag.set("value", str(bone.bone_properties.tag))

        bone_node.append(bone_node_tag)

        bone_node_tag = Element("Index")
        bone_node_tag.set("value", str(bone["BONE_INDEX"]))
        bone_node.append(bone_node_tag)

        bone_node_parent_index = Element("ParentIndex")
        bone_node_sibling_index = Element("SiblingIndex")

        if bone.parent != None:
            bone_node_parent_index.set("value", str(bone.parent["BONE_INDEX"]))
            children = bone.parent.children
            sibling = -1
            if len(children) > 1:
                for i, child in enumerate(children):
                    if child["BONE_INDEX"] == bone["BONE_INDEX"] and i + 1 < len(children):
                        sibling = children[i + 1]["BONE_INDEX"]
                        break

            bone_node_sibling_index.set("value", str(sibling))
        else:
            bone_node_parent_index.set("value", "-1")
            bone_node_sibling_index.set("value", "-1")

        bone_node.append(bone_node_parent_index)
        bone_node.append(bone_node_sibling_index)

        bone_node_flags = Element("Flags")
        flags = []
        for flag in bone.bone_properties.flags:
            flags.append(flag.name)

        if len(bone.children) > 0:
            flags.append("Unk0")

        bone_node_flags.text = ", ".join(flags)
        bone_node.append(bone_node_flags)

        mat = bone.matrix_local
        if (bone.parent != None):
            mat = bone.parent.matrix_local.inverted() @ bone.matrix_local

        mat_decomposed = mat.decompose()

        trans = mat_decomposed[0]
        bone_node_translation = Element("Translation")
        bone_node_translation.set("x", str(trans[0]))
        bone_node_translation.set("y", str(trans[1]))
        bone_node_translation.set("z", str(trans[2]))
        bone_node.append(bone_node_translation)

        #quat = bone.rotation_euler.to_quaternion()
        quat = mat_decomposed[1]
        bone_node_rotation = Element("Rotation")
        bone_node_rotation.set("x", str(quat[1]))
        bone_node_rotation.set("y", str(quat[2]))
        bone_node_rotation.set("z", str(quat[3]))
        bone_node_rotation.set("w", str(quat[0]))
        bone_node.append(bone_node_rotation)

        scale = mat_decomposed[2]
        bone_node_scale = Element("Scale")
        bone_node_scale.set("x", str(scale[0]))
        bone_node_scale.set("y", str(scale[1]))
        bone_node_scale.set("z", str(scale[2]))
        bone_node.append(bone_node_scale)

        bone_node_transform_unk = Element("TransformUnk")
        bone_node_transform_unk.set("x", "0")
        bone_node_transform_unk.set("y", "4")
        bone_node_transform_unk.set("z", "-3")
        bone_node_transform_unk.set("w", "0")
        bone_node.append(bone_node_transform_unk)

        bones_node.append(bone_node)

    return skeleton_node

def get_bbs(objs):
    bounding_boxs = []
    for obj in objs:
        bounding_boxs.append(obj.bound_box)
        
    bounding_boxmin = []
    bounding_boxmax = []

    for b in bounding_boxs:
        bounding_boxmin.append(b[0])
        bounding_boxmax.append(b[6])
    
    min_xs = []
    min_ys = []
    min_zs = []
    for v in bounding_boxmin:
        min_xs.append(v[0])
        min_ys.append(v[1])
        min_zs.append(v[2])
        
    max_xs = []
    max_ys = []
    max_zs = []
    for v in bounding_boxmax:
        max_xs.append(v[0])
        max_ys.append(v[1])
        max_zs.append(v[2])
    
    bounding_box_min = []    
    bounding_box_min.append(min(min_xs))
    bounding_box_min.append(min(min_ys))
    bounding_box_min.append(min(min_zs))
    
    bounding_box_max = []    
    bounding_box_max.append(max(max_xs))
    bounding_box_max.append(max(max_ys))
    bounding_box_max.append(max(max_zs))
    
    return [bounding_box_min, bounding_box_max]

def add_vector_list(list1, list2):
    x = list1[0] + list2[0]
    y = list1[1] + list2[1]
    z = list1[2] + list2[2]     
    return [x, y, z]

def subtract_vector_list(list1, list2):
    x = list1[0] - list2[0]
    y = list1[1] - list2[1]
    z = list1[2] - list2[2]     
    return [x, y, z]

def multiple_vector_list(list, num):
    x = list[0] * num
    y = list[1] * num
    z = list[2] * num
    return [x, y, z]

def get_vector_list_length(list):
    
    sx = list[0]**2  
    sy = list[1]**2
    sz = list[2]**2
    length = (sx + sy + sz) ** 0.5
    return length 
    
    
def get_sphere_bb(objs, bbminmax):
    
    allverts = []
    for obj in objs:
        mesh = obj.data
        for vert in mesh.vertices:
            allverts.append(vert)
    bscen = [0, 0, 0]
    bsrad = 0
    
    av = add_vector_list(bbminmax[0], bbminmax[1])
    bscen = multiple_vector_list(av, 0.5)

    for v in allverts:
        bsrad = max(bsrad, get_vector_list_length(subtract_vector_list(v.co, bscen)))

    return [bscen, bsrad]   

#still presents a problem where in a scenario you had other ydrs you didnt want to export in the scene it would pick up 
#them materials also 
def get_used_materials(drawable):
    
    materials = []
    
    children = drawable.children

    for obj in children:
        if(obj.sollumtype == "Geometry"):
            mat = obj.active_material
            if(mat != None):
                materials.append(mat)          

    return materials

def write_drawable(obj, filepath, root_name="Drawable", bones=None):
    
    children = get_obj_children(obj)
    bbminmax = get_bbs(children)
    bbsphere = get_sphere_bb(children, bbminmax)
    
    drawable_node = Element(root_name)
    name_node = Element("Name")
    name_node.text = obj.name.split(".")[0]
    
    bsc_node = Element("BoundingSphereCenter")
    bsc_node.set("x", str(bbsphere[0][0]))
    bsc_node.set("y", str(bbsphere[0][1]))
    bsc_node.set("z", str(bbsphere[0][2]))
    
    bsr_node = Element("BoundingSphereRadius")
    bsr_node.set("value", str(bbsphere[1]))
    
    bbmin_node = Element("BoundingBoxMin")
    bbmin_node.set("x", str(bbminmax[0][0]))
    bbmin_node.set("y", str(bbminmax[0][1]))
    bbmin_node.set("z", str(bbminmax[0][2]))
    
    bbmax_node = Element("BoundingBoxMax")
    bbmax_node.set("x", str(bbminmax[1][0]))
    bbmax_node.set("y", str(bbminmax[1][1]))
    bbmax_node.set("z", str(bbminmax[1][2]))
    
    ldh_node = Element("LodDistHigh")
    ldh_node.set("value", str(obj.drawble_distance_high))
    ldm_node = Element("LodDistMed")
    ldm_node.set("value", str(obj.drawble_distance_medium))
    ldl_node = Element("LodDistLow")
    ldl_node.set("value", str(obj.drawble_distance_low))
    ldvl_node = Element("LodDistVlow")
    ldvl_node.set("value", str(obj.drawble_distance_vlow)) 

    geometrys = []
    materials = get_used_materials(obj)
    bounds = []
    if bones == None:
        bones = obj.pose.bones

    flagshigh = 0
    flagsmed = 0
    flagslow = 0
    flagsvlow = 0
    
    for c in children:
        if(c.sollumtype == "Geometry"):
            geometrys.append(c)
            if(c.level_of_detail == "High"):
                flagshigh += 1
            if(c.level_of_detail == "Medium"):
                flagsmed += 1
            if(c.level_of_detail == "Low"):
                flagslow += 1
            if(c.level_of_detail == "Very Low"):
                flagsvlow += 1
            
    flagsh_node = Element("FlagsHigh")
    flagsh_node.set("value", str(flagshigh))
    flagsm_node = Element("FlagsMed")
    flagsm_node.set("value", str(flagsmed))
    flagsl_node = Element("FlagsLow")
    flagsl_node.set("value", str(flagslow))
    flagsvl_node = Element("FlagsVlow")
    flagsvl_node.set("value", str(flagsvlow))
    Unk9a_node = Element("Unknown9A")
    Unk9a_node.set("value", "0")

    shadergroup_node = write_shader_group_node(materials, filepath)
    skeleton_node = write_skeleton_node(obj)
    drawablemodels_node = write_drawablemodels_node(geometrys, materials, bones)
    bounds_node = None
    
    drawable_node.append(name_node)
    drawable_node.append(bsc_node)
    drawable_node.append(bsr_node)
    drawable_node.append(bbmin_node)
    drawable_node.append(bbmax_node)
    drawable_node.append(ldh_node)
    drawable_node.append(ldm_node)
    drawable_node.append(ldl_node)
    drawable_node.append(ldvl_node)
    drawable_node.append(flagsh_node)
    drawable_node.append(flagsm_node)
    drawable_node.append(flagsl_node)
    drawable_node.append(flagsvl_node)
    drawable_node.append(Unk9a_node)
    drawable_node.append(shadergroup_node)
    if skeleton_node != None:
        drawable_node.append(skeleton_node)

    for dm_node in drawablemodels_node:
        drawable_node.append(dm_node)
    if(bounds_node != None):
        drawable_node.append(bounds_node)
    
    #print(prettify(drawable_node))
    
    return drawable_node
    
def write_drawable_dictionary(obj, filepath):
    drawable_dictionary_node = Element("DrawableDictionary")
    children = get_obj_children(obj)

    bones = None
    for c in children:
        if c.sollumtype == "Drawable" and len(c.pose.bones) > 0:
            bones = c.pose.bones
            break

    for c in children:
        if c.sollumtype == "Drawable":
            drawable_node = write_drawable(c, filepath, "Item", bones)
            drawable_dictionary_node.append(drawable_node)

    return drawable_dictionary_node

def write_ydr_xml(context, filepath):
    
    root = None

    objects = bpy.context.scene.collection.objects

    if(len(objects) == 0):
        return "No objects in scene for Sollumz export"
    
    #select the object first?
    for obj in objects:
        if(obj.sollumtype == "Drawable"):
            root = write_drawable(obj, filepath)
            try: 
                print("*** Complete ***")
            except:
                print(str(Exception))
                return str(Exception)

    if(root == None):
        return "No Sollumz Drawable found to export"
    
    xmlstr = prettify(root)
    with open(filepath, "w") as f:
        f.write(xmlstr)
        return "Sollumz Drawable was succesfully exported to " + filepath

def write_ydd_xml(context, filepath):
    
    root = None

    objects = bpy.context.scene.collection.objects

    if(len(objects) == 0):
        return "No objects in scene for Sollumz export"
    
    #select the object first?
    for obj in objects:
        if(obj.sollumtype == "Drawable Dictionary"):
            root = write_drawable_dictionary(obj, filepath)
            try: 
                print("*** Complete ***")
            except:
                print(str(Exception))
                return str(Exception)

    if(root == None):
        return "No Sollumz Drawable found to export"
    
    xmlstr = prettify(root)
    with open(filepath, "w") as f:
        f.write(xmlstr)
        return "Sollumz Drawable was succesfully exported to " + filepath

class ExportYDR(Operator, ExportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "exportxml.ydr"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Export Ydr Xml (.ydr.xml)"

    # ExportHelper mixin class uses this
    filename_ext = ".ydr.xml"

    filter_glob: StringProperty(
        default="*.ydr.xml",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def execute(self, context):
        start = datetime.now()
        
        #try:
        result = write_ydr_xml(context, self.filepath)
        self.report({'INFO'}, result)
        
        #except Exception:
        #    self.report({"ERROR"}, str(Exception) )
            
        finished = datetime.now()
        difference = (finished - start).total_seconds()
        print("Exporting : " + self.filepath)
        print("Export Time:")
        print("start time: " + str(start))
        print("end time: " + str(finished))
        print("difference: " + str(difference) + " seconds")
        return {'FINISHED'}

class ExportYDD(Operator, ExportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "exportxml.ydd"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Export Ydd Xml (.ydd.xml)"

    # ExportHelper mixin class uses this
    filename_ext = ".ydd.xml"

    filter_glob: StringProperty(
        default="*.ydd.xml",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def execute(self, context):
        start = datetime.now()
        
        #try:
        result = write_ydd_xml(context, self.filepath)
        self.report({'INFO'}, result)
        
        #except Exception:
        #    self.report({"ERROR"}, str(Exception) )
            
        finished = datetime.now()
        difference = (finished - start).total_seconds()
        print("Exporting : " + self.filepath)
        print("Export Time:")
        print("start time: " + str(start))
        print("end time: " + str(finished))
        print("difference: " + str(difference) + " seconds")
        return {'FINISHED'}

# Only needed if you want to add into a dynamic menu
def menu_func_export(self, context):
    self.layout.operator(ExportYDR.bl_idname, text="Ydr Xml Export (.ydr.xml)")
    self.layout.operator(ExportYDD.bl_idname, text="Ydd Xml Export (.ydd.xml)")

def register():
    bpy.utils.register_class(ExportYDR)
    bpy.utils.register_class(ExportYDD)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_class(ExportYDR)
    bpy.utils.unregister_class(ExportYDD)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
