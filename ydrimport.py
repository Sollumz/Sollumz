import bpy
import xml.etree.ElementTree as ET
import os

import sys
sys.path.append(os.path.dirname(__file__))

from bpy_extras.io_utils import ImportHelper
import sollumz_shaders
from .resources.drawable import Drawable, ShaderTextureParameter
from .resources.shader import ShaderManager
from mathutils import Vector

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

def geometry_to_blender(geometry):
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
    if(len(texcoords0) > 0):
        create_uv_layer(mesh, 0, texcoords0)
    if(len(texcoords1) > 0):
        create_uv_layer(mesh, 1, texcoords1)
    if(len(texcoords2) > 0):
        create_uv_layer(mesh, 2, texcoords2)
    if(len(texcoords3) > 0):
        create_uv_layer(mesh, 3, texcoords3)
    if(len(texcoords4) > 0):
        create_uv_layer(mesh, 4, texcoords4)
    if(len(texcoords5) > 0):
        create_uv_layer(mesh, 5, texcoords5)
    if(len(texcoords6) > 0):
        create_uv_layer(mesh, 6, texcoords6)
    if(len(texcoords7) > 0):
        create_uv_layer(mesh, 7, texcoords7)

    #set vertex colors
    if(len(colors0) > 0):
        create_vertexcolor_layer(mesh, 0, colors0)
    if(len(colors1) > 0):
        create_vertexcolor_layer(mesh, 1, colors1)
        
    return mesh

def drawable_to_blender(drawable, materials):
    drawable_obj = bpy.data.objects.new(drawable.name, None)

    drawable_obj.drawable_properties.lod_dist_high = drawable.lod_dist_high
    drawable_obj.drawable_properties.lod_dist_med = drawable.lod_dist_med
    drawable_obj.drawable_properties.lod_dist_low = drawable.lod_dist_low
    drawable_obj.drawable_properties.lod_dist_vlow = drawable.lod_dist_vlow
    drawable_obj.sollum_type = "sollumz_drawable"

    all_models = [*drawable.drawable_models_high, *drawable.drawable_models_med, *drawable.drawable_models_low,  *drawable.drawable_models_vlow]

    for model in all_models:
        for geo in model.geometries:
            mesh = geometry_to_blender(geo)
            geo_obj = bpy.data.objects.new(drawable.name + "_mesh", mesh)
            geo_obj.sollum_type = "sollumz_geometry"
            geo_obj.data.materials.append(materials[geo.shader_index])
################# FIGURE THIS OUT ################### maybe change the first loop to be a for i in range() and check i based on amount of high, med, low, and vlow models...
            geo_obj.geometry_properties.sollum_lod = "sollumz_high" 
########################################################
            geo_obj.parent = drawable_obj
            bpy.context.collection.objects.link(geo_obj)    

    bpy.context.collection.objects.link(drawable_obj)

def shader_group_to_blender(shadermanager, shadergroup, filepath):

    mats = []

    texture_folder = os.path.dirname(filepath) + "\\" + os.path.basename(filepath)[:-8]
    for shader in shadergroup.shaders:
        material = sollumz_shaders.create_shader(shader.name, shadermanager)

        for param in shader.parameters:
            for n in material.node_tree.nodes:
                if(isinstance(n, bpy.types.ShaderNodeTexImage)):
                    if(param.name == n.name):
                        texture_path = os.path.join(texture_folder, param.texture_name + ".dds")
                        
                        if(shadergroup.texture_dictionary != None):
                            for txt in shadergroup.texture_dictionary.textures:
                                if(txt.name == param.texture_name):
                                    print()
                                    
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
        sm = ShaderManager()
        d = Drawable()
        d.read_xml(ET.parse(self.filepath))
        
        mats = shader_group_to_blender(sm, d.shader_group, self.filepath)        
        drawable_to_blender(d, mats)

        return {'FINISHED'}

def menu_func_import(self, context):
    self.layout.operator(ImportYdrXml.bl_idname, text="Import .ydr.xml")

