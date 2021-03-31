import bpy
import os
import xml.etree.ElementTree as ET
from mathutils import Vector, Quaternion, Matrix
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator
import time
import random 
from .tools import cats as Cats
from .ybnimport import read_ybn_xml 

class v_vertex:

    def __init__(self, p, tc, tc1, tc2, tc3, tc4, tc5, c, c1, n, t, bw, bi):
        self.Position = p
        self.TexCoord = tc
        self.TexCoord1 = tc1
        self.TexCoord2 = tc2
        self.TexCoord3 = tc3
        self.TexCoord4 = tc4
        self.TexCoord5 = tc5
        self.Color = c
        self.Color1 = c1
        self.Normal = n
        self.Tangent = t
        self.BlendWeights = bw
        self.BlendIndices = bi

class Drawable:
    root = None
    name = "Drawable"
    lods = None
    shaders = None
    bones = None
    objects = None

    def __init__(self, root, name, lods, shaders, bones, objects):
        self.root = root
        self.name = name
        self.lods = lods
        self.shaders = shaders
        self.bones = bones
        self.objects = objects

def get_related_texture(texture_dictionary, img_name):

    props = None 
    format = None
    usage = None 
    not_half = False
    hd_split = False
    full = False
    maps_half = False
    
    for t in texture_dictionary:
        tname = t.find("FileName").text 
        if(tname == img_name):
            
            format = t.find("Format").text.split("_")[1] 
            usage = t.find("Usage").text
            uf = t.find("UsageFlags").text
            
            not_half = False
            hd_split = False    
            full = False
            maps_half = False
            x2 = False
            x4 = False
            y4 = False
            x8 = False
            x16 = False 
            x32 = False
            x64 = False
            y64 = False
            x128 = False
            x256 = False
            x512 = False
            y512 = False
            x1024 = False
            y1024 = False
            x2048 = False
            y2048 = False
            embeddedscriptrt = False
            unk19 = False
            unk20 = False
            unk21 = False
            unk24 = False
            
            if("NOT_HALF" in uf):
                not_half = True
            if("HD_SPLIT" in uf):
                hd_split = True
            if("FLAG_FULL" in uf):
                full = True
            if("MAPS_HALF" in uf):
                maps_half = True
            if("X2" in uf):
                x2 = True
            if("X4" in uf):
                x4 = True
            if("Y4" in uf):
                y4 = True
            if("X8" in uf):
                x8 = True
            if("X16" in uf):
                x16 = True
            if("X32" in uf):
                x32 = True
            if("X64" in uf):
                x64 = True
            if("Y64" in uf):
                y64 = True
            if("X128" in uf):
                x128 = True
            if("X256" in uf):
                x256 = True
            if("X512" in uf):
                x512 = True
            if("Y512" in uf):
                y512 = True
            if("X1024" in uf):
                x1024 = True
            if("Y1024" in uf):
                y1024 = True
            if("X2048" in uf):
                x2048 = True
            if("Y2048" in uf):
                y2048 = True
            if("EMBEDDEDSCRIPTRT" in uf):
                embeddedscriptrt = True
            if("UNK19" in uf):
                unk19 = True
            if("UNK20" in uf):
                unk20 = True
            if("UNK21" in uf):
                unk21 = True
            if("UNK24" in uf):
                unk24 = True
            
            
            extra_flags = int(t.find("ExtraFlags").attrib["value"])
            
            props = []
            props.append(format)
            props.append(usage)
            props.append(not_half) 
            props.append(hd_split) 
            props.append(full) 
            props.append(maps_half) 
            props.append(extra_flags)
            props.append(x2)
            props.append(x4)
            props.append(y4)
            props.append(x8)
            props.append(x16)
            props.append(x32)
            props.append(x64)
            props.append(y64)
            props.append(x128)
            props.append(x256)
            props.append(x512)
            props.append(y512)
            props.append(x1024)
            props.append(y1024)
            props.append(x2048)
            props.append(y2048)
            props.append(embeddedscriptrt)
            props.append(unk19)
            props.append(unk20)
            props.append(unk21)
            props.append(unk24)
        
    return props 

def create_material(filepath, td_node, shader):
    
    params = shader.find("Parameters")
    
    filename = os.path.basename(filepath)[:-8]
    texture_dir = os.path.dirname(os.path.abspath(filepath)) + "\\" + filename + "\\"
    
    texture_dictionary = None
    if(td_node != None):
        texture_dictionary = []
        for i in td_node:
            texture_dictionary.append(i)
    
    shadern_node = shader.find("FileName")
    if shadern_node is not None:
        shadern = shadern_node.text
    else:
        shadern = "default.sps"

    bpy.ops.sollum.createvshader(shadername = shadern)
    mat = bpy.context.scene.last_created_material
    
    nodes = mat.node_tree.nodes 
    for p in params:
        for n in nodes: 
            if(isinstance(n, bpy.types.ShaderNodeTexImage)):
                if(p.attrib["name"] == n.name):
                    texture_pos = p.find("Name")
                    if(hasattr(texture_pos, 'text')):
                        texture_name = texture_pos.text + ".dds" 
                        texture_path = texture_dir + texture_name
                        n.texture_name = texture_name
                        if(os.path.isfile(texture_dir + texture_name)):
                            img = bpy.data.images.load(texture_path, check_existing=True)
                            n.image = img 

                        #deal with special situations
                        if(p.attrib["name"] == "BumpSampler" and hasattr(n.image, 'colorspace_settings')):
                            n.image.colorspace_settings.name = 'Non-Color'

            elif(isinstance(n, bpy.types.ShaderNodeValue)):
                if(p.attrib["name"].lower() == n.name[:-2].lower()): #remove _X
                    value_key = n.name[-1] #X,Y,Z,W
                    if p.attrib["type"] == "Array":
                        value = p.find("Value").attrib[value_key]
                    else:
                        value = p.attrib[value_key]

                    n.outputs[0].default_value = float(value)      
        
    #assign all embedded texture properties
    #### FIND A BETTER WAY TO DO THIS ####
    if(texture_dictionary != None):
        for node in nodes:
            if(isinstance(node, bpy.types.ShaderNodeTexImage)):
                if(node.image != None):
                    texturepath = node.image.filepath
                    texturename = os.path.basename(texturepath)
                    texture_properties = get_related_texture(texture_dictionary, texturename)
                    if(texture_properties != None):
                        node.embedded = True
                        node.format_type = texture_properties[0] 
                        node.usage = texture_properties[1]
                        node.not_half = texture_properties[2] 
                        node.hd_split = texture_properties[3] 
                        node.flag_full = texture_properties[4] 
                        node.maps_half = texture_properties[5]  
                        node.extra_flags = texture_properties[6] 
                        node.x2 = texture_properties[7] 
                        node.x4 = texture_properties[8] 
                        node.y4 = texture_properties[9] 
                        node.x8 = texture_properties[10] 
                        node.x16 = texture_properties[11] 
                        node.x32 = texture_properties[12] 
                        node.x64 = texture_properties[13] 
                        node.y64 = texture_properties[14] 
                        node.x128 = texture_properties[15] 
                        node.x256 = texture_properties[16] 
                        node.x512 = texture_properties[17] 
                        node.y512 = texture_properties[18] 
                        node.x1024 = texture_properties[19] 
                        node.y1024 = texture_properties[20] 
                        node.x2048 = texture_properties[21] 
                        node.y2048 = texture_properties[22] 
                        node.embeddedscriptrt = texture_properties[23] 
                        node.unk19 = texture_properties[24] 
                        node.unk20 = texture_properties[25]
                        node.unk21 = texture_properties[26]
                        node.unk24 = texture_properties[27]
    
    mat.sollumtype = "GTA" 
    
    return mat

def process_uv(uv):
    u = uv[0]
    v = (uv[1] * -1) + 1.0

    return [u, v]

def create_model(self, context, index_buffer, vertices, filepath, name, bones):

    verts = []
    faces = index_buffer
    normals = []
    texcoords = []
    texcoords1 = []
    texcoords2 = []
    texcoords3 = []
    texcoords4 = []
    texcoords5 = []
    tangents = []
    vcolors = [] 
    vcolors1 = [] 
    blendweights = [] 
    blendindices = [] 

    for v in vertices:
        if(v.Position != None):
            verts.append(Vector((v.Position[0], v.Position[1], v.Position[2])))
        else:
            return None #SHOULD NEVER HAPPEN
        if(v.Normal != None):
            normals.append(v.Normal)
        if(v.TexCoord != None):
            texcoords.append(v.TexCoord)
        if(v.TexCoord1 != None):
            texcoords1.append(v.TexCoord1)
        if(v.TexCoord2 != None):
            texcoords2.append(v.TexCoord2)
        if(v.TexCoord3 != None):
            texcoords3.append(v.TexCoord3)
        if(v.TexCoord4 != None):
            texcoords4.append(v.TexCoord4)
        if(v.TexCoord5 != None):
            texcoords5.append(v.TexCoord5)
        if(v.Tangent != None):
            tangents.append(Vector((v.Tangent[0], v.Tangent[1], v.Tangent[2])))
        if(v.Color != None):
            vcolors.append(v.Color)
        if(v.Color1 != None):
            vcolors1.append(v.Color1)
        if(v.BlendWeights != None):
            blendweights.append(v.BlendWeights)
        if(v.BlendIndices != None):
            blendindices.append(v.BlendIndices)
        
    #create mesh
    mesh = bpy.data.meshes.new("Geometry")
    mesh.from_pydata(verts, [], faces)
    verts_num = mesh.vertices
    mesh.create_normals_split()
    mesh.validate(clean_customdata=False)
    normals_fixed = []
    for l in mesh.loops:
        normals_fixed.append(normals[l.vertex_index])
    
    polygon_count = len(mesh.polygons)
    mesh.polygons.foreach_set("use_smooth", [True] * polygon_count)

    mesh.normals_split_custom_set(normals_fixed)
    mesh.use_auto_smooth = True

    # set uv 
    if(texcoords):
        uv0 = mesh.uv_layers.new()
        uv_layer0 = mesh.uv_layers[0]
        for i in range(len(uv_layer0.data)):
            uv = process_uv(texcoords[mesh.loops[i].vertex_index])
            uv_layer0.data[i].uv = uv 
    if(texcoords1):
        uv1 = mesh.uv_layers.new()
        uv_layer1 = mesh.uv_layers[1]
        for i in range(len(uv_layer1.data)):
            uv = process_uv(texcoords1[mesh.loops[i].vertex_index])
            uv_layer1.data[i].uv = uv 
    if(texcoords2):
        uv2 = mesh.uv_layers.new()
        uv_layer2 = mesh.uv_layers[2]
        for i in range(len(uv_layer2.data)):
            uv = process_uv(texcoords2[mesh.loops[i].vertex_index])
            uv_layer2.data[i].uv = uv 
    if(texcoords3):
        uv3 = mesh.uv_layers.new()
        uv_layer3 = mesh.uv_layers[3]
        for i in range(len(uv_layer3.data)):
            uv = process_uv(texcoords3[mesh.loops[i].vertex_index])
            uv_layer3.data[i].uv = uv 
    if(texcoords4):
        uv4 = mesh.uv_layers.new()
        uv_layer4 = mesh.uv_layers[4]
        for i in range(len(uv_layer4.data)):
            uv = process_uv(texcoords4[mesh.loops[i].vertex_index])
            uv_layer4.data[i].uv = uv 
    if(texcoords5):
        uv5 = mesh.uv_layers.new()
        uv_layer5 = mesh.uv_layers[5]
        for i in range(len(uv_layer5.data)):
            uv = process_uv(texcoords5[mesh.loops[i].vertex_index])
            uv_layer5.data[i].uv = uv 
    
    #set vertex colors 
    if(vcolors):
        clr0 = mesh.vertex_colors.new(name = "Vertex Colors") 
        color_layer = mesh.vertex_colors[0]
        for i in range(len(color_layer.data)):
            rgba = vcolors[mesh.loops[i].vertex_index]
            color_layer.data[i].color = rgba
    if(vcolors1):
        clr1 = mesh.vertex_colors.new(name = "Vertex illumiation") 
        color_layer1 = mesh.vertex_colors[1]
        for i in range(len(color_layer.data)):
            rgba = vcolors1[mesh.loops[i].vertex_index]
            color_layer1.data[i].color = rgba
    
    #set tangents - .tangent is read only so can't set them
    #for poly in mesh.polygons:
        #for idx in poly.loop_indicies:
            #mesh.loops[i].tangent = tangents[i]    

    obj = bpy.data.objects.new(name.replace(".#dr", "") + "_mesh", mesh)
    
    #load weights
    # 256 - possibly the maximum of bones?
    if (bones != None and len(bones) > 0 and len(blendweights) > 0 and len(verts_num) > 0):
        for i in range(256):
            if (i < len(bones)):
                obj.vertex_groups.new(name=bones[i])
            else:
                obj.vertex_groups.new(name="UNKNOWN_BONE." + str(i))

        for vertex_idx in range(len(verts_num)):
            for i in range(0, 4):
                if (blendweights[vertex_idx][i] > 0.0):
                    obj.vertex_groups[blendindices[vertex_idx][i]].add([vertex_idx], blendweights[vertex_idx][i], "ADD")

        Cats.remove_unused_vertex_groups_of_mesh(obj)

    return obj
    #context.collection.objects.link(obj)

def get_vertices_from_data(layout, v_buffer):
    #find the position of the variable in the vertex layout
    layers = []
    for idx in range(len(layout)):
        layers.append(layout[idx].tag)
        
    vertices = []
    for v in v_buffer:
        position = None
        texcoords = None
        texcoords1 = None
        texcoords2 = None
        texcoords3 = None
        texcoords4 = None
        texcoords5 = None
        color = None
        color1 = None
        normal = None
        tangents = None
        blendw = None
        blendi = None

        tokens = v.split(" " * 3) #each vert value is split by 3 spaces

        if len(tokens) != len(layers):
            print("Incorrect layout data!")

        for i in range(len(tokens)):
            layer = layers[i]
            token = tokens[i]

            if layer == "Position":
                position = list(map(lambda x: float(x), token.split()))
            elif layer == "Normal":
                normal = list(map(lambda x: float(x), token.split()))
            elif layer == "Colour0":
                color = list(map(lambda x: float(x) / 255, token.split()))
            elif layer == "Colour1":
                color1 = list(map(lambda x: float(x) / 255, token.split()))
            elif layer == "TexCoord0":
                texcoords = list(map(lambda x: float(x), token.split()))
            elif layer == "TexCoord1":
                texcoords1 = list(map(lambda x: float(x), token.split()))
            elif layer == "TexCoord2":
                texcoords2 = list(map(lambda x: float(x), token.split()))
            elif layer == "TexCoord3":
                texcoords3 = list(map(lambda x: float(x), token.split()))
            elif layer == "TexCoord4":
                texcoords4 = list(map(lambda x: float(x), token.split()))
            elif layer == "TexCoord5":
                texcoords5 = list(map(lambda x: float(x), token.split()))
            elif layer == "Tangent":
                tangents = list(map(lambda x: float(x), token.split()))
            elif layer == "BlendWeights":
                blendw = list(map(lambda x: float(x) / 255, token.split()))
            elif layer == "BlendIndices":
                blendi = list(map(lambda x: int(x), token.split()))

        vertices.append(v_vertex(position, texcoords, texcoords1, texcoords2, texcoords3, texcoords4, texcoords5, color, color1, normal, tangents, blendw, blendi))

    return vertices

def read_model_info(self, context, filepath, model, shaders, name, bones):
    
    v_buffer = []
    i_buffer = []
    shader_index = 0

    shader_index = int(model.find("ShaderIndex").attrib["value"])
    vb = model.find("VertexBuffer")
    v_buffer = map(lambda line : line.strip(), vb[2].text.strip().split("\n"))

    ib = model.find("IndexBuffer")
    i_buffer = ib[0].text.strip().replace("\n", "").split()

    vertices = get_vertices_from_data(vb.find("Layout"), v_buffer)

    i_buf = []
    for num in i_buffer:
        i_buf.append(int(num))

    index_buffer = [i_buf[i * 3:(i + 1) * 3] for i in range((len(i_buf) + 3 - 1) // 3 )] #split index buffer into 3s for each triangle

    # this is for the rare cases that model with no bone but have weights
    if (bones == None):
        boneids = model.find("BoneIDs")
        if (boneids != None):
            boneids = boneids.text.split(", ")
            bones = []
            for id in boneids:
                bones.append("UNKNOWN_BONE." + id)

    obj = create_model(self, context, index_buffer, vertices, filepath, name, bones) #supply shaderindex into texturepaths because the shaders are always in order
    
    obj.data.materials.append(shaders[shader_index])
    return obj

def read_shader_info(self, context, filepath, shd_node, td_node):
    
    shaders = []
    
    for shader in shd_node:
        mat = create_material(filepath, td_node, shader)
        shaders.append(mat)
        
    return shaders

def read_drawable_models(self, context, filepath, root, name, shaders, key, bones):

    dm_node = root.find("DrawableModels" + key)
    drawable_models = []
    rm_nodes = []
    drawable_objects = []

    for dm in dm_node:
        drawable_models.append(dm)
        render_mask = int(dm.find("RenderMask").attrib["value"])
        
        g_node = []
        for geo_node in dm.iter('Geometries'):
            g_node = geo_node
            
        models = []
        for model in g_node:
            models.append(model)
        
        idx = 0
        for model in models:
            d_obj = read_model_info(self, context, filepath, model, shaders, name, bones)
            
            #set sollum properties 
            d_obj.sollumtype = "Geometry"
            d_obj.level_of_detail = key
            d_obj.mask = render_mask
            
            drawable_objects.append(d_obj)
            idx += 1
        
    return drawable_objects

def build_bones_dict(armature):
    if (armature == None):
        return None

    bones_dict = {}
    for pose_bone in armature.pose.bones:
        bones_dict[pose_bone.bone.bone_properties.tag] = pose_bone.name

    return bones_dict

def read_joints(self, context, filepath, root, bones_dict=None):

    joints_node = root.find("Joints")
    if (joints_node == None):
        return None

    rotationlimits_node = joints_node.find("RotationLimits")
    if (rotationlimits_node == None):
        return None

    armature = context.object
    if (bones_dict == None):
        bones_dict = build_bones_dict(armature)

    rotationlimits = []
    for rotationlimits_item in rotationlimits_node:
        rotationlimits_bone_id = rotationlimits_item.find("BoneId")
        rotationlimits_min = rotationlimits_item.find("Min")
        rotationlimits_max = rotationlimits_item.find("Max")
        bone = armature.pose.bones.get(bones_dict[int(rotationlimits_bone_id.attrib["value"])])
        constraint = bone.constraints.new('LIMIT_ROTATION')
        constraint.owner_space = 'LOCAL'
        constraint.use_limit_x = True
        constraint.use_limit_y = True
        constraint.use_limit_z = True
        constraint.max_x = float(rotationlimits_max.attrib["x"])
        constraint.max_y = float(rotationlimits_max.attrib["y"])
        constraint.max_z = float(rotationlimits_max.attrib["z"])
        constraint.min_x = float(rotationlimits_min.attrib["x"])
        constraint.min_y = float(rotationlimits_min.attrib["y"])
        constraint.min_z = float(rotationlimits_min.attrib["z"])
        rotationlimits.append(bone.name)

    return rotationlimits

def read_bones(self, context, filepath, root):

    skeleton_node = root.find("Skeleton")
    if (skeleton_node == None):
        return None, None

    bones = []
    bones_tag = []
    flags_list = []
    # LimitRotation and Unk0 have their special meanings, can be deduced if needed when exporting
    flags_restricted = set(["LimitRotation", "Unk0"])
    drawable_name = root.find("Name").text.split(".")[0]
    bones_node = skeleton_node.find("Bones")
    armature = context.object
    bpy.ops.object.mode_set(mode='EDIT')

    for bones_item in bones_node:
        name_item = bones_item.find("Name")
        tag_item = bones_item.find("Tag")
        parentindex_item = bones_item.find("ParentIndex")
        flags_item = bones_item.find("Flags")
        translation_item = bones_item.find("Translation")
        rotation_item = bones_item.find("Rotation")
        scale_item = bones_item.find("Scale")

        quaternion = Quaternion()
        quaternion.w = float(rotation_item.attrib["w"])
        quaternion.x = float(rotation_item.attrib["x"])
        quaternion.y = float(rotation_item.attrib["y"])
        quaternion.z = float(rotation_item.attrib["z"])
        mat_rot = quaternion.to_matrix().to_4x4()

        trans = Vector()
        trans.x = float(translation_item.attrib["x"])
        trans.y = float(translation_item.attrib["y"])
        trans.z = float(translation_item.attrib["z"])
        mat_loc = Matrix.Translation(trans)

        scale = Vector()
        scale.x = float(scale_item.attrib["x"])
        scale.y = float(scale_item.attrib["y"])
        scale.z = float(scale_item.attrib["z"])
        mat_sca = Matrix.Scale(1, 4, scale)

        edit_bone = armature.data.edit_bones.new(name_item.text)
        # edit_bone.bone_id = int(bone_tag.attrib["value"])
        if parentindex_item.attrib["value"] != "-1":
            edit_bone.parent = armature.data.edit_bones[int(parentindex_item.attrib["value"])]

        # https://github.com/LendoK/Blender_GTA_V_model_importer/blob/master/importer.py
        edit_bone.head = (0,0,0)
        edit_bone.tail = (0,0.05,0)
        edit_bone.matrix = mat_loc @ mat_rot @ mat_sca
        if edit_bone.parent != None:
            edit_bone.matrix = edit_bone.parent.matrix @ edit_bone.matrix

        if (flags_item != None and flags_item.text != None):
            flags = flags_item.text.strip().split(", ")
            
        flags_list.append(flags)

        # build a bones lookup table
        bones.append(name_item.text)
        bones_tag.append(int(tag_item.get('value')))

    bpy.ops.object.mode_set(mode='POSE')

    for i in range(len(bones)):
        armature.pose.bones[i].bone.bone_properties.tag = bones_tag[i]
        for _flag in flags_list[i]:
            if (_flag in flags_restricted):
                continue

            flag = armature.pose.bones[i].bone.bone_properties.flags.add()
            flag.name = _flag

    bpy.ops.object.mode_set(mode='OBJECT')
    return bones, drawable_name

def read_ydr_shaders(self, context, filepath, root):
    shd_group = root.find("ShaderGroup")

    if not shd_group:
        return None

    shd_node = shd_group.find("Shaders")
    td_node = shd_group.find("TextureDictionary")  

    shaders = read_shader_info(self, context, filepath, shd_node, td_node)
    return shaders

def read_ydr_xml(self, context, filepath, root, shaders, bones=None):

    fname = os.path.basename(filepath)
    name = fname[:-8] #removes file extension

    model_name = root.find("Name").text

    if model_name == None:
        model_name = name

    # ydd specific, if bones are found then don't do that all over again
    if (bones == None):
        bones = read_bones(self, context, filepath, root)[0]

    if (bones != None):
        joints = read_joints(self, context, filepath, root)

    #get objects from drawable info
    high_objects = []
    med_objects = []
    low_objects = []
    
    if(root.find("DrawableModelsHigh") != None):
        high_objects = read_drawable_models(self, context, filepath, root, model_name, shaders, "High", bones)
    if(root.find("DrawableModelsMedium") != None):
        med_objects = read_drawable_models(self, context, filepath, root, model_name, shaders, "Medium", bones)
    if(root.find("DrawableModelsLow") != None):
        low_objects = read_drawable_models(self, context, filepath, root, model_name, shaders, "Low", bones)

    all_objects = []
    for o in high_objects:
        all_objects.append(o)
    for o in med_objects:
        all_objects.append(o)
    for o in low_objects:
        all_objects.append(o)

    #set sollum properties 
    dd_high = float(root.find("LodDistHigh").attrib["value"])
    dd_med = float(root.find("LodDistMed").attrib["value"])
    dd_low = float(root.find("LodDistLow").attrib["value"])
    dd_vlow = float(root.find("LodDistVlow").attrib["value"])

    return Drawable(root, model_name, [dd_high, dd_med, dd_low, dd_vlow], shaders, bones, all_objects)

def read_ydd_xml(self, context, filepath, root):

    drawables = []
    bones = None
    drawable_with_bones_name = None
    # we need to get the name of that particular drawable and its bones before loading other data
    for ydr in root:
        bones, drawable_with_bones_name = read_bones(self, context, filepath, ydr)
        if (drawable_with_bones_name != None):
            break

    for ydr in root:
        shaders = read_ydr_shaders(self, context, filepath, ydr)
        drawable = read_ydr_xml(self, context, filepath, ydr, shaders, bones)
        drawables.append(drawable)

    return drawables, drawable_with_bones_name

class ImportYDR(Operator, ImportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "importxml.ydr"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Import Ydr"

    # ImportHelper mixin class uses this
    filename_ext = ".ydr.xml"

    filter_glob: StringProperty(
        default="*.ydr.xml",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def execute(self, context):
        start = time.time()
        
        tree = ET.parse(self.filepath)
        root = tree.getroot()

        name = os.path.basename(self.filepath)[:-8]
        armature = bpy.data.armatures.new(name + ".skel")
        vmodel_obj = bpy.data.objects.new(name, armature)
        context.scene.collection.objects.link(vmodel_obj)
        context.view_layer.objects.active = vmodel_obj

        shaders = read_ydr_shaders(self, context, self.filepath, root)
        drawable = read_ydr_xml(self, context, self.filepath, root, shaders)

        if drawable.objects is not None:
            for obj in drawable.objects:
                context.scene.collection.objects.link(obj)
                obj.parent = vmodel_obj
                mod = obj.modifiers.new("Armature", 'ARMATURE')
                mod.object = vmodel_obj
        
        bound_obj = read_ybn_xml(context, self.filepath, root)
        
        if bound_obj is not None:
            bound_obj.parent = vmodel_obj
            context.scene.collection.objects.link(bound_obj)
        
        #set sollum properties 
        dd_high = float(root.find("LodDistHigh").attrib["value"])
        dd_med = float(root.find("LodDistMed").attrib["value"])
        dd_low = float(root.find("LodDistLow").attrib["value"])
        dd_vlow = float(root.find("LodDistVlow").attrib["value"])
        
        vmodel_obj.sollumtype = "Drawable"
        vmodel_obj.drawble_distance_high = drawable.lods[0]
        vmodel_obj.drawble_distance_medium = drawable.lods[1]
        vmodel_obj.drawble_distance_low = drawable.lods[2]
        vmodel_obj.drawble_distance_vlow = drawable.lods[3]

        finished = time.time()
        
        difference = finished - start
        
        print("start time: " + str(start))
        print("end time: " + str(finished))
        print("difference in seconds: " + str(difference))
        print("difference in milliseconds: " + str(difference * 1000))
                
        return {'FINISHED'}

class ImportYDD(Operator, ImportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "importxml.ydd"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Import Ydd"

    # ImportHelper mixin class uses this
    filename_ext = ".ydd.xml"

    filter_glob: StringProperty(
        default="*.ydd.xml",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def execute(self, context):
        start = time.time()

        tree = ET.parse(self.filepath)
        root = tree.getroot()

        name = os.path.basename(self.filepath)[:-8]
        vmodels = []
        # bones are shared in single ydd however they still have to be placed under a paticular drawable
        # temp armature, to be merged
        armature_temp = bpy.data.armatures.new("ARMATURE_TEMP")
        armature_temp_obj = bpy.data.objects.new("ARMATURE_TEMP", armature_temp)
        context.scene.collection.objects.link(armature_temp_obj)
        context.view_layer.objects.active = armature_temp_obj

        drawable_with_bones_name = None
        armature_with_bones_obj = None

        mod_objs = []
        drawable_dict, drawable_with_bones_name = read_ydd_xml(self, context, self.filepath, root)
        for drawable in drawable_dict:
            armature = bpy.data.armatures.new(drawable.name + ".skel")
            # mesh has "_mesh" at the end of its name, so remove that for the parented armature
            vmodel_obj = bpy.data.objects.new(drawable.name, armature)
            context.scene.collection.objects.link(vmodel_obj)
            if (armature_with_bones_obj == None and drawable_with_bones_name != None and drawable.name == drawable_with_bones_name):
                armature_with_bones_obj = vmodel_obj

            if drawable.objects is not None:
                for obj in drawable.objects:
                    context.scene.collection.objects.link(obj)
                    obj.parent = vmodel_obj
                    mod_objs.append(obj)
        
            for ydr in root:
                bound_obj = read_ybn_xml(context, self.filepath, ydr)
                if(bound_obj != None):
                    bound_obj.parent = vmodel_obj
                    context.scene.collection.link(bound_obj)
                    
            vmodel_obj.sollumtype = "Drawable"
            vmodel_obj.drawble_distance_high = drawable.lods[0]
            vmodel_obj.drawble_distance_medium = drawable.lods[1]
            vmodel_obj.drawble_distance_low = drawable.lods[2]
            vmodel_obj.drawble_distance_vlow = drawable.lods[3]
            vmodels.append(vmodel_obj)
        
        vmodel_dict_obj = bpy.data.objects.new(name, None)
        vmodel_dict_obj.sollumtype = "Drawable Dictionary"

        for vmodel in vmodels:
            vmodel.parent = vmodel_dict_obj
            exportable = vmodel_dict_obj.drawable_dict_properties.exportables.add()
            exportable.drawable = vmodel
        
        context.scene.collection.objects.link(vmodel_dict_obj)

        if (armature_with_bones_obj != None):
            for obj in mod_objs:
                mod = obj.modifiers.new("Armature", 'ARMATURE')
                mod.object = armature_with_bones_obj

            bpy.ops.object.select_all(action='DESELECT')
            armature_temp_obj.select_set(True)
            armature_with_bones_obj.select_set(True)
            context.view_layer.objects.active = armature_with_bones_obj
            bpy.ops.object.join()
        else:
            bpy.data.objects.remove(armature_temp_obj, do_unlink=True)

        finished = time.time()
        
        difference = finished - start
        
        print("start time: " + str(start))
        print("end time: " + str(finished))
        print("difference in seconds: " + str(difference))
        print("difference in milliseconds: " + str(difference * 1000))

        return {'FINISHED'}


# Only needed if you want to add into a dynamic menu
def menu_func_import_ydr(self, context):
    self.layout.operator(ImportYDR.bl_idname, text="Ydr (.ydr.xml)")
# Only needed if you want to add into a dynamic menu
def menu_func_import_ydd(self, context):
    self.layout.operator(ImportYDD.bl_idname, text="Ydd (.ydd.xml)")

def register():
    bpy.utils.register_class(ImportYDR)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import_ydr)
    bpy.utils.register_class(ImportYDD)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import_ydd)

def unregister():
    bpy.utils.unregister_class(ImportYDR)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import_ydr)
    bpy.utils.unregister_class(ImportYDD)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import_ydd)
