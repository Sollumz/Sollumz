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

def get_vertex_string(obj, layout):

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

def geometry_from_object(obj):
    geometry = GeometryItem()

    bbmin, bbmax = get_bb_extents(obj)
    geometry.bounding_box_min = bbmin
    geometry.bounding_box_max = bbmax
    
    materials = get_used_materials(obj.parent.parent)
    for i in range(len(materials)):
        if(materials[i] == obj.active_material):
            geometry.shader_index = i

    sm = ShaderManager()
    layout = sm.shaders[FixShaderName(obj.active_material.name)].layouts["0x0"]
    for l in layout:
        geometry.vertex_buffer.layout.append(VertexLayoutItem(l))
    geometry.vertex_buffer.data = get_vertex_string(obj, layout)
    geometry.index_buffer.data = get_index_string(obj.data)
    
    return geometry

def drawable_model_from_object(obj):
    drawable_model = DrawableModelItem()

    drawable_model.render_mask = obj.drawable_model_properties.render_mask
    drawable_model.flags = obj.drawable_model_properties.flags
    #drawable_model.hasskin = 0
    #rawable_model.bone_index = 0
    #drawable_model.unknown_1 = ?

    for child in obj.children:
        if(child.sollum_type == "sollumz_geometry"):
            geometry = geometry_from_object(child)
            drawable_model.geometries.append(geometry)

    return drawable_model

def drawable_from_object(obj):
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

    highmodel_count = 0
    medmodel_count = 0
    lowhmodel_count = 0
    vlowmodel_count = 0

    for child in obj.children:
        if(child.sollum_type == "sollumz_drawable_model"):
            drawable_model = drawable_model_from_object(child)
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
    
class ExportYdrXml(bpy.types.Operator, ExportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "exportxml.ydr"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Export Ydr Xml (.ydr.xml)"

    filename_ext = ".ydr.xml"

    def execute(self, context):

        objects = bpy.context.collection.objects

        found = False
        if len(objects) > 0:
            for obj in objects:
                if obj.sollum_type == "sollumz_drawable":
                    found = True
                    try:
                        drawable_from_object(obj).write_xml(self.filepath)
                        self.report({'INFO'}, 'Ydr Successfully exported.')
                    except Exception as e:
                        #self.report({'ERROR'}, f"Composite {obj.name} failed to export: {e}")
                        self.report({'ERROR'}, traceback.format_exc())
        
        if not found:
            self.report({'INFO'}, "No bound object types in scene for Sollumz export")

        return {'FINISHED'}

def ydr_menu_func_export(self, context):
    self.layout.operator(ExportYdrXml.bl_idname, text="Export .ydr.xml")

def register():
    bpy.types.TOPBAR_MT_file_export.append(ydr_menu_func_export)

def unregister():
    bpy.types.TOPBAR_MT_file_export.remove(ydr_menu_func_export)