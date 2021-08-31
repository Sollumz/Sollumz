import bpy
import xml.etree.ElementTree as ET
import os
import time
import sys
sys.path.append(os.path.dirname(__file__))

from bpy_extras.io_utils import ImportHelper
import sollumz_shaders
from .resources.drawable import Drawable, ShaderTextureParameter
from .resources.shader import ShaderManager
from mathutils import Vector, Quaternion, Matrix
from .ybnimport import bound_composite_to_blender

def process_uv(uv):
    u = uv[0]
    v = (uv[1] * -1) + 1.0
    return [u, v]

def create_uv_layer(mesh, num, texcoords):
    mesh.uv_layers.new()
    uv_layer = mesh.uv_layers[num]
    for i in range(len(uv_layer.data)):
        uv = process_uv(texcoords[mesh.loops[i].vertex_index])
        uv_layer.data[i].uv = uv 

def create_vertexcolor_layer(mesh, num, colors):
    mesh.vertex_colors.new(name = "Vertex Colors " + str(num)) 
    color_layer = mesh.vertex_colors[num]
    for i in range(len(color_layer.data)):
        rgba = colors[mesh.loops[i].vertex_index]
        color_layer.data[i].color = rgba

def geometry_to_blender(geometry, skeleton):
    vertices = []
    faces = []
    normals = []
    texcoords0 = []
    texcoords1 = []
    texcoords2 = []
    texcoords3 = []
    texcoords4 = []
    texcoords5 = []
    texcoords6 = []
    texcoords7 = []
    colors0 = []
    colors1 = []
    blendweights = []
    blendindicies = []

    for v in geometry.vertex_buffer.vertices:
        vertices.append(Vector((v.position[0], v.position[1], v.position[2])))
        normals.append(v.normal)

        if(v.texcoord0 != None):
            texcoords0.append(v.texcoord0)
        if(v.texcoord1 != None):
            texcoords1.append(v.texcoord1)
        if(v.texcoord2 != None):
            texcoords2.append(v.texcoord2)
        if(v.texcoord3 != None):
            texcoords3.append(v.texcoord3)
        if(v.texcoord4 != None):
            texcoords4.append(v.texcoord4)
        if(v.texcoord5 != None):
            texcoords5.append(v.texcoord5)
        if(v.texcoord6 != None):
            texcoords6.append(v.texcoord6)
        if(v.texcoord7 != None):
            texcoords7.append(v.texcoord7)

        if(v.colors0 != None):
            colors0.append(v.colors0)
        if(v.colors1 != None):
            colors1.append(v.colors1)

        if(v.blendweights != None):
            blendweights.append(v.blendweights)
        if(v.blendindicies != None):
            blendindicies.append(v.blendindicies)

    for i in geometry.index_buffer:
        faces.append(i)

    #create mesh
    mesh = bpy.data.meshes.new('geometry')
    mesh.from_pydata(vertices, [], faces)

    #set normals
    mesh.create_normals_split()
    if(len(normals) > 0):
        normals_fixed = []
        for l in mesh.loops:
            normals_fixed.append(normals[l.vertex_index])
        mesh.normals_split_custom_set(normals_fixed)

    #set autosmooth
    polygon_count = len(mesh.polygons)
    mesh.polygons.foreach_set("use_smooth", [True] * polygon_count)
    mesh.use_auto_smooth = True
    
    # set uvs
    uv_layer_count = 0
    if(len(texcoords0) > 0):
        create_uv_layer(mesh, uv_layer_count, texcoords0)
        uv_layer_count += 1
    if(len(texcoords1) > 0):
        create_uv_layer(mesh, uv_layer_count, texcoords1)
        uv_layer_count += 1
    if(len(texcoords2) > 0):
        create_uv_layer(mesh, uv_layer_count, texcoords2)
        uv_layer_count += 1
    if(len(texcoords3) > 0):
        create_uv_layer(mesh, uv_layer_count, texcoords3)
        uv_layer_count += 1
    if(len(texcoords4) > 0):
        create_uv_layer(mesh, uv_layer_count, texcoords4)
        uv_layer_count += 1
    if(len(texcoords5) > 0):
        create_uv_layer(mesh, uv_layer_count, texcoords5)
        uv_layer_count += 1
    if(len(texcoords6) > 0):
        create_uv_layer(mesh, uv_layer_count, texcoords6)
        uv_layer_count += 1
    if(len(texcoords7) > 0):
        create_uv_layer(mesh, uv_layer_count, texcoords7)
        uv_layer_count += 1

    #set vertex colors
    if(len(colors0) > 0):
        create_vertexcolor_layer(mesh, 0, colors0)
    if(len(colors1) > 0):
        create_vertexcolor_layer(mesh, 1, colors1)
    
    #set weights 
    if(skeleton != None and len(skeleton.bones) > 0 and len(blendweights) > 0):
        for i in range(256):
            if(i < len(skeleton.bones)):
                print("add vertex group")
                #obj.vertex_groups.new(name=bones[i])
            else:
                print("add vertex group unk")
                #obj.vertex_groups.new(name="UNKNOWN_BONE." + str(i))
        
        for vertex_idx in range(len(mesh.vertices)):
            for i in range(0, 4):
                if (blendweights[vertex_idx][i] > 0.0):
                    #obj.vertex_groups[blendindices[vertex_idx][i]].add([vertex_idx], blendweights[vertex_idx][i], "ADD")
                    print("add weight")

    return mesh

def skeleton_to_blender(drawable_obj, skeleton):
    armature = bpy.data.armatures.new("skeleton")
    skeleton_obj = bpy.data.objects.new(drawable_obj.name + "_skeleton", armature)
    bpy.context.collection.objects.link(skeleton_obj)
    skeleton_obj.parent = drawable_obj
    bpy.context.view_layer.objects.active = skeleton_obj

    bpy.ops.object.mode_set(mode='EDIT')

    for bone in skeleton.bones:
        edit_bone = skeleton_obj.data.edit_bones.new(bone.name)
        
        if(bone.parent_index != -1):
            edit_bone.parent = skeleton_obj.data.edit_bones[bone.parent_index]

        matrix_location = Matrix.Translation(Vector((bone.translation[0], bone.translation[1], bone.translation[2])))
        matrix_rotation = Quaternion((bone.rotation[0], bone.rotation[1], bone.rotation[2], bone.rotation[3])).to_matrix().to_4x4()
        matrix_scale = Matrix.Scale(1, 4, Vector((bone.scale[0], bone.scale[1], bone.scale[2])))

        edit_bone.head = (0,0,0)
        edit_bone.tail = (0,0.05,0)
        edit_bone.matrix = matrix_location @ matrix_rotation @ matrix_scale
        if edit_bone.parent != None:
            edit_bone.matrix = edit_bone.parent.matrix @ edit_bone.matrix
            
    bpy.ops.object.mode_set(mode='OBJECT')

    return skeleton_obj

def drawable_to_blender(drawable, materials):

    drawable_obj = bpy.data.objects.new(drawable.name, None)
    drawable_obj.drawable_properties.lod_dist_high = drawable.lod_dist_high
    drawable_obj.drawable_properties.lod_dist_med = drawable.lod_dist_med
    drawable_obj.drawable_properties.lod_dist_low = drawable.lod_dist_low
    drawable_obj.drawable_properties.lod_dist_vlow = drawable.lod_dist_vlow
    drawable_obj.sollum_type = "sollumz_drawable"

    skeleton_obj = None
    skeleton = drawable.skeleton
    if(skeleton != None):
        skeleton_obj = skeleton_to_blender(drawable_obj, drawable.skeleton)
        skeleton_obj.sollum_type = "sollumz_skeleton"
    
    bound_obj = None
    bound = drawable.bound
    if(bound != None):
        bound_obj = bound_composite_to_blender(bound, drawable.name + "_bound")
        bound_obj.parent = drawable_obj

    all_models = [*drawable.drawable_models_high, *drawable.drawable_models_med, *drawable.drawable_models_low,  *drawable.drawable_models_vlow]
    
    i = 0
    for model in all_models:
        for geo in model.geometries:
            mesh = geometry_to_blender(geo, skeleton)
            geo_obj = bpy.data.objects.new(drawable.name + "_mesh", mesh)
            geo_obj.sollum_type = "sollumz_geometry"
            geo_obj.data.materials.append(materials[geo.shader_index])

            lod = ""
            if(model in drawable.drawable_models_high):
                lod = "sollumz_high"
            elif(model in drawable.drawable_models_med):
                lod = "sollumz_med"
            elif(model in drawable.drawable_models_low):
                lod = "sollumz_low"
            else:
                lod = "sollumz_vlow"

            geo_obj.geometry_properties.sollum_lod = lod

            geo_obj.parent = drawable_obj
            bpy.context.collection.objects.link(geo_obj)    
        i += 1

    bpy.context.collection.objects.link(drawable_obj)

    return drawable_obj

def shader_group_to_blender(shadermanager, shadergroup, filepath):

    mats = []

    texture_folder = os.path.dirname(filepath) + "\\" + os.path.basename(filepath)[:-8]
    for shader in shadergroup.shaders:
        material = sollumz_shaders.create_shader(shader.name, shadermanager)

        #################### GETTING ERROR FOR NO REASON #########################
        #material.shader_properties.renderbucket = shader.renderbucket[0] 
        ##########################################################################
        material.shader_properties.filename = shader.filename

        for param in shader.parameters:
            for n in material.node_tree.nodes:
                if(isinstance(n, bpy.types.ShaderNodeTexImage)):
                    if(param.name == n.name):
                        texture_path = os.path.join(texture_folder, param.texture_name + ".dds")
                        
                        if(shadergroup.texture_dictionary != None):
                            for txt in shadergroup.texture_dictionary.textures:
                                if(txt.name == param.texture_name):
                                    continue
                                    
                        if(os.path.isfile(texture_path)):
                            img = bpy.data.images.load(texture_path, check_existing=True)
                            n.image = img 

                        if(param.name == "BumpSampler" and hasattr(n.image, 'colorspace_settings')):
                            n.image.colorspace_settings.name = 'Non-Color'
                            
                elif(isinstance(n, bpy.types.ShaderNodeValue)):
                    if(param.name == n.name[:-2]):
                        key = n.name[-1]
                        if(key == "x"):
                            n.outputs[0].default_value = param.quaternion[0]
                        if(key == "y"):
                            n.outputs[0].default_value = param.quaternion[1]
                        if(key == "z"):
                            n.outputs[0].default_value = param.quaternion[2]
                        if(key == "w"):
                            n.outputs[0].default_value = param.quaternion[3]

        #assign embedded texture dictionary properties
        if(shadergroup.texture_dictionary != None):
            idx = -1
            for node in material.node_tree.nodes:
                if(isinstance(node, bpy.types.ShaderNodeTexImage)):
                    if(node.image != None):
                        idx += 1
                        texturepath = node.image.filepath
                        texturename = os.path.basename(texturepath)
                        texture = shadergroup.texture_dictionary.textures[idx]
                        node.texture_properties.embedded = True
                        node.texture_properties.format = "sollumz_" + texture.format.split('_')[1].lower()
                        node.texture_properties.usage = "sollumz_" + texture.usage.lower()
                        node.texture_properties.extra_flags = texture.extra_flags
                        
                        for prop in dir(node.texture_properties):
                            for uf in texture.usage_flags:
                                if(uf.lower() == prop):
                                    setattr(node.texture_properties, prop, True)                      
                                    
        mats.append(material)
        
    return mats

class ImportYdrXml(bpy.types.Operator, ImportHelper):
    """Imports .ydr.xml file exported from codewalker."""
    bl_idname = "sollumz.importydr" 
    bl_label = "Import ydr.xml"
    filename_ext = ".ydr.xml"

    filter_glob: bpy.props.StringProperty(
        default="*.ydr.xml",
        options={'HIDDEN'},
        maxlen=255,  
    )

    def execute(self, context):
        
        count = 0 
        size = 0

        sm = ShaderManager()
        d = Drawable()

        parse_time_start = time.time()
        root = ET.parse(self.filepath)
        parse_time_end = time.time()

        read_time_start = time.time()
        d.read_xml(root)
        read_time_end = time.time()
        
        count += 1
        size += os.path.getsize(self.filepath)

        import_time_start = time.time()
        mats = shader_group_to_blender(sm, d.shader_group, self.filepath)        
        drawable_to_blender(d, mats)
        import_time_end = time.time()

        """ #dev - import folder of ydrs
        directory = os.path.dirname(self.filepath)
        for file in os.listdir(directory):
            if(file.endswith(".ydr.xml")):
                try:
                    count += 1
                    filepath = os.path.join(directory, file)
                    size += os.path.getsize(filepath)
                    d = Drawable()
                    d.read_xml(ET.parse(filepath))

                    sm = ShaderManager()
                    mats = shader_group_to_blender(sm, d.shader_group, self.filepath)        
                    drawable_to_blender(d, mats)
                except:
                    print("failed importing: " + file)

        """
        parsing_time = parse_time_end - parse_time_start
        reading_time = read_time_end - read_time_start
        importing_time = import_time_end - import_time_start
        total_time = parsing_time + reading_time + importing_time 
        print(str(parsing_time) + " seconds to parse xml " + str(reading_time) + " seconds to convert xml to classes and " + str(importing_time) + " second to import, with a total import time being " + str(total_time) + " seconds")

        return {'FINISHED'}

def ydr_menu_func_import(self, context):
    self.layout.operator(ImportYdrXml.bl_idname, text="Import .ydr.xml")

