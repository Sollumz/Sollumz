import bpy
from bpy_extras.io_utils import ImportHelper
import os, traceback
from .sollumz_shaders import *
from .resources.shader import ShaderManager
from .resources.drawable import *

def shadergroup_to_materials(shadergroup, filepath):
    shadermanager = ShaderManager()

    materials = []

    texture_folder = os.path.dirname(filepath) + "\\" + os.path.basename(filepath)[:-8]
    for shader in shadergroup.shaders:
        
        material = create_shader(shader.name, shadermanager)

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
                            for txt in shadergroup.texture_dictionary:
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
                            n.outputs[0].default_value = param.quaternion_x
                        if(key == "y"):
                            n.outputs[0].default_value = param.quaternion_y
                        if(key == "z"):
                            n.outputs[0].default_value = param.quaternion_z
                        if(key == "w"):
                            n.outputs[0].default_value = param.quaternion_w

        #assign embedded texture dictionary properties
        if(shadergroup.texture_dictionary != None):
            idx = -1
            for node in material.node_tree.nodes:
                if(isinstance(node, bpy.types.ShaderNodeTexImage)):
                    if(node.image != None):
                        idx += 1
                        texturepath = node.image.filepath
                        texturename = os.path.basename(texturepath)
                        texture = shadergroup.texture_dictionary[idx]
                        node.texture_properties.embedded = True
                        format = "sollumz_" + texture.format[0].split("_")[1].lower()
                        node.texture_properties.format = format
                        usage = "sollumz_" + texture.usage[0].lower()
                        node.texture_properties.usage = usage
                        node.texture_properties.extra_flags = texture.extra_flags
                        
                        for prop in dir(node.texture_properties):
                            for uf in texture.usage_flags:
                                if(uf.lower() == prop):
                                    setattr(node.texture_properties, prop, True)     

        materials.append(material)

    return materials

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

def geometry_to_obj(geometry):

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
    blendindices = []

    data = geometry.vertex_buffer.data_to_vertices()
    for v in data:
        vertices.append(v.position)
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

        # if(v.blendweights != None):
        #     blendweights.append(v.blendweights)
        # if(v.blendindices != None):
        #     blendindices.append(v.blendindices)

    faces = geometry.index_buffer.data_to_indices()

    mesh = bpy.data.meshes.new("Geometry")
    mesh.from_pydata(vertices, [], faces)
    mesh.create_normals_split()
    mesh.validate(clean_customdata=False)
    polygon_count = len(mesh.polygons)
    mesh.polygons.foreach_set("use_smooth", [True] * polygon_count)
    # maybe normals_split_custom_set_from_vertices(self.normals) is better?
    if data[0].normal is not None:
        normals_fixed = []
        for l in mesh.loops:
            normals_fixed.append(data[l.vertex_index].normal)

        mesh.normals_split_custom_set(normals_fixed)

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

    #set tangents - .tangent is read only so can't set them
    #for poly in mesh.polygons:
        #for idx in poly.loop_indicies:
            #mesh.loops[i].tangent = tangents[i]    

    return mesh

'''
    #load weights
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
                    obj.vertex_groups[index].add([vertex_idx], weight, "ADD")

        Cats.remove_unused_vertex_groups_of_mesh(obj)
'''

def drawable_model_to_obj(model, materials, name, lodlevel):
    dobj = bpy.data.objects.new("Drawable Model", None)
    dobj.sollum_type = "sollumz_drawable_model"
    dobj.drawable_model_properties.sollum_lod = "sollumz_" + lodlevel
    dobj.drawable_model_properties.render_mask = model.render_mask
    dobj.drawable_model_properties.flags = model.flags

    for geo in model.geometries:
        mesh = geometry_to_obj(geo)
        geo_obj = bpy.data.objects.new(name + "_mesh", mesh)
        geo_obj.sollum_type = "sollumz_geometry"
        geo_obj.data.materials.append(materials[geo.shader_index])
        geo_obj.parent = dobj
        bpy.context.collection.objects.link(geo_obj)

    bpy.context.collection.objects.link(dobj)
    
    return dobj

def drawable_to_obj(drawable, filepath, name):

    materials = shadergroup_to_materials(drawable.shader_group, filepath)

    obj = bpy.data.objects.new(name, None)
    obj.sollum_type = "sollumz_drawable"
    obj.drawable_properties.lod_dist_high = drawable.lod_dist_high
    obj.drawable_properties.lod_dist_med = drawable.lod_dist_med
    obj.drawable_properties.lod_dist_low = drawable.lod_dist_low
    obj.drawable_properties.lod_dist_vlow = drawable.lod_dist_vlow

    for model in drawable.drawable_models_high:
        dobj = drawable_model_to_obj(model, materials, drawable.name, "high")
        dobj.parent = obj
        
    for model in drawable.drawable_models_med:
        dobj = drawable_model_to_obj(model, materials, drawable.name, "med")
        dobj.parent = obj

    for model in drawable.drawable_models_low:
        dobj = drawable_model_to_obj(model, materials, drawable.name, "low")
        dobj.parent = obj

    for model in drawable.drawable_models_vlow:
        dobj = drawable_model_to_obj(model, materials, drawable.name, "vlow")
        dobj.parent = obj

    return obj

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
        
        try:
            ydr_xml = YDR.from_xml_file(self.filepath)
            ydr_obj = drawable_to_obj(ydr_xml, self.filepath, os.path.basename(self.filepath))
            bpy.context.collection.objects.link(ydr_obj)
            self.report({'INFO'}, 'YBN Successfully imported.')
        except Exception as e:
            self.report({'ERROR'}, traceback.format_exc())

        return {'FINISHED'}

def ydr_menu_func_import(self, context):
    self.layout.operator(ImportYdrXml.bl_idname, text="Import .ydr.xml")
