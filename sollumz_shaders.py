import bpy
from Sollumz.sollumz_properties import MaterialType


def get_child_node(node):

    if node == None:
        return None

    for output in node.outputs:
        if len(output.links) == 1:
            return output.links[0].to_node


def get_list_of_child_nodes(node):

    all_nodes = []
    all_nodes.append(node)

    searching = True
    child = get_child_node(node)

    while searching:

        if isinstance(child, bpy.types.ShaderNodeBsdfPrincipled):
            pass
        elif isinstance(child, bpy.types.ShaderNodeOutputMaterial):
            pass
        else:
            all_nodes.append(child)

        child = get_child_node(child)

        if child == None:
            searching = False

    return all_nodes


def check_if_node_has_child(node):

    haschild = False
    for output in node.outputs:
        if len(output.links) > 0:
            haschild = True
    return haschild


def organize_node_tree(node_tree):

    level = 0
    singles_x = 0

    grid_x = 600
    grid_y = -300
    row_count = 0

    for n in node_tree.nodes:

        if isinstance(n, bpy.types.ShaderNodeValue):
            n.location.x = grid_x
            n.location.y = grid_y
            grid_x += 150
            row_count += 1
            if row_count == 4:
                grid_y -= 100
                row_count = 0
                grid_x = 600

        if isinstance(n, bpy.types.ShaderNodeBsdfPrincipled):
            n.location.x = 0
            n.location.y = -300
        if isinstance(n, bpy.types.ShaderNodeOutputMaterial):
            n.location.y = -300
            n.location.x = 300

        if isinstance(n, bpy.types.ShaderNodeTexImage):

            haschild = check_if_node_has_child(n)
            if haschild:
                level -= 250
                all_nodes = get_list_of_child_nodes(n)

                idx = 0
                for n in all_nodes:
                    try:
                        x = -300 * (len(all_nodes) - idx)

                        n.location.x = x
                        n.location.y = level

                        idx += 1
                    except:
                        print("error")
            else:
                n.location.x = singles_x
                n.location.y = 100
                singles_x += 300


def create_image_node(node_tree, param):

    imgnode = node_tree.nodes.new("ShaderNodeTexImage")
    imgnode.name = param.name
    # imgnode.img = param.DefaultValue
    bsdf = node_tree.nodes["Principled BSDF"]
    links = node_tree.links

    if "Diffuse" in param.name:
        links.new(imgnode.outputs["Color"], bsdf.inputs["Base Color"])
        links.new(imgnode.outputs["Alpha"], bsdf.inputs["Alpha"])
    elif "Bump" in param.name:
        normalmap = node_tree.nodes.new("ShaderNodeNormalMap")
        links.new(imgnode.outputs["Color"], normalmap.inputs["Color"])
        links.new(normalmap.outputs["Normal"], bsdf.inputs["Normal"])
    elif "Spec" in param.name:
        links.new(imgnode.outputs["Color"], bsdf.inputs["Specular"])


def create_vector_nodes(node_tree, param):

    vnodex = node_tree.nodes.new("ShaderNodeValue")
    vnodex.name = param.name + "_x"
    vnodex.outputs[0].default_value = param.value[0]

    vnodey = node_tree.nodes.new("ShaderNodeValue")
    vnodey.name = param.name + "_y"
    vnodey.outputs[0].default_value = param.value[1]

    vnodez = node_tree.nodes.new("ShaderNodeValue")
    vnodez.name = param.name + "_z"
    vnodez.outputs[0].default_value = param.value[2]

    vnodew = node_tree.nodes.new("ShaderNodeValue")
    vnodew.name = param.name + "_w"
    vnodew.outputs[0].default_value = param.value[3]


def create_shader(shadername, shadermanager):

    mat = bpy.data.materials.new(shadername)
    mat.sollum_type = MaterialType.MATERIAL
    mat.use_nodes = True

    parameters = shadermanager.shaders[shadername].parameters
    node_tree = mat.node_tree

    for param in parameters:
        if param.type == "Texture":
            create_image_node(node_tree, param)
        elif param.type == "Vector":
            create_vector_nodes(node_tree, param)

    organize_node_tree(node_tree)

    return mat
