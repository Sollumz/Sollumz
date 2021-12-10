import bpy
from ..ydr.shader_materials import create_shader
from ..sollumz_properties import SollumType, SOLLUMZ_UI_NAMES, MaterialType
from ..tools.meshhelper import get_children_recursive
from ..tools.blenderhelper import join_objects


def create_drawable(sollum_type=SollumType.DRAWABLE):
    empty = bpy.data.objects.new(SOLLUMZ_UI_NAMES[sollum_type], None)
    empty.empty_display_size = 0
    empty.sollum_type = sollum_type
    bpy.context.collection.objects.link(empty)
    bpy.context.view_layer.objects.active = bpy.data.objects[empty.name]

    return empty


def convert_selected_to_drawable(objs, use_names=False, multiple=False):
    parent = None

    if not multiple:
        dobj = create_drawable()
        dmobj = create_drawable(SollumType.DRAWABLE_MODEL)
        dmobj.parent = dobj

    for obj in objs:

        if obj.type != "MESH":
            raise Exception(
                f"{obj.name} cannot be converted because it has no mesh data.")

        if multiple:
            dobj = parent or create_drawable()
            dmobj = create_drawable(SollumType.DRAWABLE_MODEL)
            dmobj.parent = dobj

        # create material
        i = 0
        if(len(obj.data.materials) > 0):
            mat = obj.data.materials[0]
            if(mat.sollum_type != MaterialType.SHADER):
                # remove old materials
                try:
                    new_mat = convert_material(mat)
                    if new_mat != None:
                        obj.material_slots[i].material = new_mat
                    else:
                        raise Exception  # continute to creating a default shader
                except:
                    new_mat = create_shader("default")
                    obj.material_slots[i].material = new_mat
            i += 1

        obj.parent = dmobj

        name = obj.name
        obj.name = name + "_geom"

        if use_names:
            dobj.name = name

        # set properties
        obj.sollum_type = SollumType.DRAWABLE_GEOMETRY

        new_obj = obj.copy()
        # add color layer
        if len(new_obj.data.vertex_colors) == 0:
            new_obj.data.vertex_colors.new()
        # add object to collection
        bpy.data.objects.remove(obj, do_unlink=True)
        bpy.context.collection.objects.link(new_obj)


def join_drawable_geometries(drawable):
    cobjs = []
    children = get_children_recursive(drawable)
    for obj in children:
        if obj.sollum_type == SollumType.DRAWABLE_GEOMETRY:
            cobjs.append(obj)
    join_objects(cobjs)


def convert_material(material):
    bsdf = material.node_tree.nodes["Principled BSDF"]

    # if(bsdf == None):
    # self.messages.append(
    # f"{material.name} Material must have a Principled BSDF node.")
    # return None

    diffuse_node = None
    diffuse_input = bsdf.inputs["Base Color"]
    if diffuse_input.is_linked:
        diffuse_node = diffuse_input.links[0].from_node

    # if not isinstance(diffuse_node, bpy.types.ShaderNodeTexImage):
        # self.messages.append(
        # f"{material.name} Material has no diffuse image.")
        # return None

    specular_node = None
    specular_input = bsdf.inputs["Specular"]
    if specular_input.is_linked:
        specular_node = specular_input.links[0].from_node

    if not isinstance(diffuse_node, bpy.types.ShaderNodeTexImage):
        specular_node = None

    normal_node = None
    normal_input = bsdf.inputs["Normal"]
    if len(normal_input.links) > 0:
        normal_map_node = normal_input.links[0].from_node
        normal_map_input = normal_map_node.inputs["Color"]
        if len(normal_map_input.links) > 0:
            normal_node = normal_map_input.links[0].from_node

    if not isinstance(normal_node, bpy.types.ShaderNodeTexImage):
        normal_node = None

    shader_name = "default"

    if normal_node != None and specular_node != None:
        shader_name = "normal_spec"
    elif normal_node != None and specular_node == None:
        shader_name = "normal"
    elif normal_node == None and specular_node != None:
        shader_name = "spec"

    new_material = create_shader(shader_name)
    # new_mat.name = mat.name

    bsdf = new_material.node_tree.nodes["Principled BSDF"]

    new_diffuse_node = None
    diffuse_input = bsdf.inputs["Base Color"]
    if diffuse_input.is_linked:
        new_diffuse_node = diffuse_input.links[0].from_node

    if(diffuse_node != None):
        new_diffuse_node.image = diffuse_node.image

    new_specular_node = None
    specular_input = bsdf.inputs["Specular"]
    if specular_input.is_linked:
        new_specular_node = specular_input.links[0].from_node

    if(specular_node != None):
        new_specular_node.image = specular_node.image

    new_normal_node = None
    normal_input = bsdf.inputs["Normal"]
    if len(normal_input.links) > 0:
        normal_map_node = normal_input.links[0].from_node
        normal_map_input = normal_map_node.inputs["Color"]
        if len(normal_map_input.links) > 0:
            new_normal_node = normal_map_input.links[0].from_node

    if(normal_node != None):
        new_normal_node.image = normal_node.image

    # self.messages.append(
        # f"{material.name} was successfully converted to a sollumz material.")

    return new_material
