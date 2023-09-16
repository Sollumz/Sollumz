from typing import Optional, NamedTuple
import bpy
from ..cwxml.shader import ShaderManager, Shader
from ..sollumz_properties import MaterialType
from ..tools.blenderhelper import find_bsdf_and_material_output
from ..tools.animationhelper import add_global_anim_uv_nodes

class ShaderBuilder(NamedTuple):
    shader: Shader
    filename: str
    material: bpy.types.Material
    node_tree: bpy.types.ShaderNodeTree
    bsdf: bpy.types.ShaderNodeBsdfPrincipled
    material_output: bpy.types.ShaderNodeOutputMaterial

class ShaderMaterial(NamedTuple):
    name: str
    ui_name: str
    value: str

shadermats = []

for shader in ShaderManager._shaders.values():
    name = shader.filename.replace(".sps", "").upper()

    shadermats.append(ShaderMaterial(
        name, name.replace("_", " "), shader.filename))


def try_get_node(node_tree: bpy.types.NodeTree, name: str) -> Optional[bpy.types.Node]:
    """Gets a node by its name. Returns `None` if not found.
    Note, names are localized by Blender or can changed by the user, so
    this should only be used for names that Sollumz sets explicitly.
    """
    return node_tree.nodes.get(name, None)

def try_get_node_by_cls(node_tree: bpy.types.NodeTree, node_cls: type) -> Optional[bpy.types.Node]:
    """Gets a node by its type. Returns `None` if not found."""
    for node in node_tree.nodes:
        if isinstance(node, node_cls):
            return node

    return None

def get_child_nodes(node):
    child_nodes = []
    for input in node.inputs:
        for link in input.links:
            child = link.from_node
            if child in child_nodes:
                continue
            else:
                child_nodes.append(child)
    return child_nodes


def get_loose_nodes(node_tree):
    loose_nodes = []
    for node in node_tree.nodes:
        no = False
        ni = False
        for output in node.outputs:
            for link in output.links:
                if link.to_node is not None and link.from_node is not None:
                    no = True
                    break
        for input in node.inputs:
            for link in input.links:
                if link.to_node is not None and link.from_node is not None:
                    ni = True
                    break
        if no == False and ni == False:
            loose_nodes.append(node)
    return loose_nodes


def organize_node_tree(b: ShaderBuilder):
    mo = b.material_output
    mo.location.x = 0
    mo.location.y = 0
    organize_node(mo)
    organize_loose_nodes(b.node_tree, 1000, 0)


def organize_node(node):
    child_nodes = get_child_nodes(node)
    if len(child_nodes) < 0:
        return

    level = node.location.y
    for child in child_nodes:
        child.location.x = node.location.x - 300
        child.location.y = level
        level -= 300
        organize_node(child)


def organize_loose_nodes(node_tree, start_x, start_y):
    loose_nodes = get_loose_nodes(node_tree)
    if len(loose_nodes) == 0:
        return

    grid_x = start_x
    grid_y = start_y

    for i, node in enumerate(loose_nodes):
        if i % 4 == 0:
            grid_x = start_x
            grid_y -= 150

        node.location.x = grid_x
        node.location.y = grid_y

        grid_x -= node.width + 25


def get_tint_sampler_node(mat: bpy.types.Material) -> Optional[bpy.types.ShaderNodeTexImage]:
    nodes = mat.node_tree.nodes
    for node in nodes:
        if node.name in ("TintPaletteSampler", "TextureSamplerDiffPal") and isinstance(node, bpy.types.ShaderNodeTexImage):
            return node

    return None


def get_detail_extra_sampler(mat):  # move to blenderhelper.py?
    nodes = mat.node_tree.nodes
    for node in nodes:
        if node.name == "Extra":
            return node
    return None


def create_tinted_shader_graph(obj: bpy.types.Object):
    tint_mats = get_tinted_mats(obj)

    if not tint_mats:
        return

    if obj.data.color_attributes:
        input_color_attr_name = obj.data.color_attributes[0].name
    else:
        input_color_attr_name = None

    for mat in tint_mats:
        tint_sampler_node = get_tint_sampler_node(mat)
        palette_img = tint_sampler_node.image

        if tint_sampler_node is None:
            continue

        tint_color_attr_name = f"TintColor ({palette_img.name})" if palette_img else "TintColor"

        rename_tint_attr_node(mat.node_tree, name=tint_color_attr_name)

        tint_color_attr = obj.data.attributes.new(
            name=tint_color_attr_name, type="BYTE_COLOR", domain="CORNER")

        mod = create_tint_geom_modifier(
            obj, tint_color_attr.name, input_color_attr_name)

        if palette_img is not None:
            # create texture and get texture node
            txt_node = try_get_node_by_cls(mod.node_group, bpy.types.GeometryNodeImageTexture)
            assert txt_node is not None
            # apply texture
            txt_node.inputs[0].default_value = palette_img


def create_tint_geom_modifier(obj: bpy.types.Object, tint_color_attr_name: str, input_color_attr_name: Optional[str] = None):
    tnt_ng = create_tinted_geometry_graph()
    mod = obj.modifiers.new("GeometryNodes", "NODES")
    mod.node_group = tnt_ng

    # set input / output variables
    input_id = tnt_ng.inputs[1].identifier
    mod[input_id + "_attribute_name"] = input_color_attr_name if input_color_attr_name is not None else ""
    mod[input_id + "_use_attribute"] = True
    output_id = tnt_ng.outputs[1].identifier
    mod[output_id + "_attribute_name"] = tint_color_attr_name
    mod[output_id + "_use_attribute"] = True

    return mod


def rename_tint_attr_node(node_tree: bpy.types.NodeTree, name: str):
    for node in node_tree.nodes:
        if not isinstance(node, bpy.types.ShaderNodeAttribute) or node.attribute_name != "TintColor":
            continue

        node.attribute_name = name
        return


def get_tinted_mats(obj: bpy.types.Object) -> list[bpy.types.Material]:
    if obj.data is None or not obj.data.materials:
        return []

    return [mat for mat in obj.data.materials if is_tint_material(mat)]


def obj_has_tint_mats(obj: bpy.types.Object):
    if not obj.data.materials:
        return False

    mat = obj.data.materials[0]
    return is_tint_material(mat)


def is_tint_material(mat: bpy.types.Material):
    return mat.shader_properties.filename not in ShaderManager.tint_flag_2 and get_tint_sampler_node(mat) is not None


def link_geos(links, node1, node2):
    links.new(node1.inputs["Geometry"], node2.outputs["Geometry"])


def create_tinted_geometry_graph():  # move to blenderhelper.py?
    gnt = bpy.data.node_groups.new(
        name="TintGeometry", type="GeometryNodeTree")
    input = gnt.nodes.new("NodeGroupInput")
    output = gnt.nodes.new("NodeGroupOutput")

    # Create the necessary sockets for the node group
    gnt.inputs.new("NodeSocketGeometry", "Geometry")
    gnt.inputs.new("NodeSocketVector", "Vertex Colors")
    gnt.outputs.new("NodeSocketGeometry", "Geometry")
    gnt.outputs.new("NodeSocketColor", "Tint Color")

    # link input / output node to create geometry socket
    cptn = gnt.nodes.new("GeometryNodeCaptureAttribute")
    cptn.domain = "CORNER"
    cptn.data_type = "FLOAT_COLOR"
    gnt.links.new(input.outputs[0], cptn.inputs[0])
    gnt.links.new(cptn.outputs[0], output.inputs[0])

    # create and link texture node
    txtn = gnt.nodes.new("GeometryNodeImageTexture")
    txtn.interpolation = "Closest"
    gnt.links.new(cptn.outputs[3], txtn.inputs[1])
    gnt.links.new(txtn.outputs[0], output.inputs[1])

    # separate colour0
    sepn = gnt.nodes.new("ShaderNodeSeparateXYZ")
    gnt.links.new(input.outputs[1], sepn.inputs[0])

    # create math nodes
    mathns = []
    for i in range(9):
        mathns.append(gnt.nodes.new("ShaderNodeMath"))

    # c1
    mathns[0].operation = "LESS_THAN"
    gnt.links.new(sepn.outputs[2], mathns[0].inputs[0])
    mathns[0].inputs[1].default_value = 0.003
    mathns[1].operation = "SUBTRACT"
    gnt.links.new(mathns[0].outputs[0], mathns[1].inputs[1])
    mathns[1].inputs[0].default_value = 1.0

    # r1
    mathns[2].operation = "MULTIPLY"
    gnt.links.new(sepn.outputs[2], mathns[2].inputs[0])
    mathns[2].inputs[1].default_value = 12.920
    mathns[3].operation = "MULTIPLY"
    gnt.links.new(mathns[2].outputs[0], mathns[3].inputs[0])
    gnt.links.new(mathns[0].outputs[0], mathns[3].inputs[1])

    # r2
    mathns[4].operation = "POWER"
    gnt.links.new(sepn.outputs[2], mathns[4].inputs[0])
    mathns[4].inputs[1].default_value = 0.417
    mathns[5].operation = "MULTIPLY"
    gnt.links.new(mathns[4].outputs[0], mathns[5].inputs[0])
    mathns[5].inputs[1].default_value = 1.055
    mathns[6].operation = "SUBTRACT"
    gnt.links.new(mathns[5].outputs[0], mathns[6].inputs[0])
    mathns[6].inputs[1].default_value = 0.055
    mathns[7].operation = "MULTIPLY"
    gnt.links.new(mathns[6].outputs[0], mathns[7].inputs[0])
    gnt.links.new(mathns[1].outputs[0], mathns[7].inputs[1])

    # add r1 and r2
    mathns[8].operation = "ADD"
    gnt.links.new(mathns[3].outputs[0], mathns[8].inputs[0])
    gnt.links.new(mathns[7].outputs[0], mathns[8].inputs[1])

    # create and link vector
    comb = gnt.nodes.new("ShaderNodeCombineRGB")
    gnt.links.new(mathns[8].outputs[0], comb.inputs[0])
    gnt.links.new(comb.outputs[0], cptn.inputs[3])

    return gnt


def create_image_node(node_tree, param) -> bpy.types.ShaderNodeTexImage:
    imgnode = node_tree.nodes.new("ShaderNodeTexImage")
    imgnode.name = param.name
    imgnode.is_sollumz = True
    return imgnode


def create_vector_nodes(node_tree, param):
    for attr in vars(param).values():
        if attr.name != "name" and attr.name != "type":
            node = node_tree.nodes.new("ShaderNodeValue")
            node.name = f"{param.name}_{attr.name}"
            node.is_sollumz = True
            node.outputs[0].default_value = float(attr.value)


def create_array_item_node(group_name):
    array_item_group = bpy.data.node_groups.new(group_name, "ShaderNodeTree")
    array_item_group.nodes.new("NodeGroupInput")
    array_item_group.inputs.new("NodeSocketFloat", "X").default_value = 0
    array_item_group.inputs.new("NodeSocketFloat", "Y").default_value = 0
    array_item_group.inputs.new("NodeSocketFloat", "Z").default_value = 0
    array_item_group.inputs.new("NodeSocketFloat", "W").default_value = 0
    return array_item_group


def create_array_nodes(node_tree, param):
    array_item_group = None
    if "ArrayNode" not in bpy.data.node_groups:
        array_item_group = create_array_item_node("ArrayNode")
    else:
        array_item_group = bpy.data.node_groups["ArrayNode"]

    for i, value in enumerate(param.values):
        nodename = f"{param.name} {i + 1}"
        node = node_tree.nodes.new("ShaderNodeGroup")
        node.name = nodename
        node.label = nodename
        node.node_tree = array_item_group

        for index in range(0, len(node.inputs)):
            node.inputs[index].default_value = value[index]

        node.is_sollumz = True


def link_diffuse(b: ShaderBuilder, imgnode):
    node_tree = b.node_tree
    bsdf = b.bsdf
    links = node_tree.links
    links.new(imgnode.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(imgnode.outputs["Alpha"], bsdf.inputs["Alpha"])


def link_diffuses(b: ShaderBuilder, tex1, tex2):
    node_tree = b.node_tree
    bsdf = b.bsdf
    links = node_tree.links
    rgb = node_tree.nodes.new("ShaderNodeMixRGB")
    links.new(tex1.outputs["Color"], rgb.inputs["Color1"])
    links.new(tex2.outputs["Color"], rgb.inputs["Color2"])
    links.new(tex2.outputs["Alpha"], rgb.inputs["Fac"])
    links.new(rgb.outputs["Color"], bsdf.inputs["Base Color"])
    return rgb


def link_detailed_normal(b: ShaderBuilder, bumptex, dtltex, spectex):
    node_tree = b.node_tree
    bsdf = b.bsdf
    dtltex2 = node_tree.nodes.new("ShaderNodeTexImage")
    dtltex2.name = "Extra"
    dsz = node_tree.nodes["detailSettings_z"]
    dsw = node_tree.nodes["detailSettings_w"]
    dsy = node_tree.nodes["detailSettings_y"]
    links = node_tree.links
    attr = node_tree.nodes.new("ShaderNodeAttribute")
    comxyz = node_tree.nodes.new("ShaderNodeCombineXYZ")
    mathns = []
    for _ in range(9):
        math = node_tree.nodes.new("ShaderNodeVectorMath")
        mathns.append(math)
    nrm = node_tree.nodes.new("ShaderNodeNormalMap")

    attr.attribute_name = "UVMap 0"
    links.new(attr.outputs[1], mathns[0].inputs[0])

    links.new(dsz.outputs[0], comxyz.inputs[0])
    links.new(dsw.outputs[0], comxyz.inputs[1])

    mathns[0].operation = "MULTIPLY"
    links.new(comxyz.outputs[0], mathns[0].inputs[1])
    links.new(mathns[0].outputs[0], dtltex2.inputs[0])

    mathns[1].operation = "MULTIPLY"
    mathns[1].inputs[1].default_value[0] = 3.17
    mathns[1].inputs[1].default_value[1] = 3.17
    links.new(mathns[0].outputs[0], mathns[1].inputs[0])
    links.new(mathns[1].outputs[0], dtltex.inputs[0])

    mathns[2].operation = "SUBTRACT"
    mathns[2].inputs[1].default_value[0] = 0.5
    mathns[2].inputs[1].default_value[1] = 0.5
    links.new(dtltex.outputs[0], mathns[2].inputs[0])

    mathns[3].operation = "SUBTRACT"
    mathns[3].inputs[1].default_value[0] = 0.5
    mathns[3].inputs[1].default_value[1] = 0.5
    links.new(dtltex2.outputs[0], mathns[3].inputs[0])

    mathns[4].operation = "ADD"
    links.new(mathns[2].outputs[0], mathns[4].inputs[0])
    links.new(mathns[3].outputs[0], mathns[4].inputs[1])

    mathns[5].operation = "MULTIPLY"
    links.new(mathns[4].outputs[0], mathns[5].inputs[0])
    links.new(dsy.outputs[0], mathns[5].inputs[1])

    mathns[6].operation = "MULTIPLY"
    if spectex:
        links.new(spectex.outputs[1], mathns[6].inputs[0])
    links.new(mathns[5].outputs[0], mathns[6].inputs[1])

    mathns[7].operation = "MULTIPLY"
    mathns[7].inputs[1].default_value[0] = 1
    mathns[7].inputs[1].default_value[1] = 1
    links.new(mathns[6].outputs[0], mathns[7].inputs[0])

    mathns[8].operation = "ADD"
    links.new(mathns[7].outputs[0], mathns[8].inputs[0])
    links.new(bumptex.outputs[0], mathns[8].inputs[1])

    links.new(mathns[8].outputs[0], nrm.inputs[1])
    links.new(nrm.outputs[0], bsdf.inputs["Normal"])


def link_normal(b: ShaderBuilder, nrmtex):
    node_tree = b.node_tree
    bsdf = b.bsdf
    links = node_tree.links
    normalmap = node_tree.nodes.new("ShaderNodeNormalMap")

    rgb_curves = create_normal_invert_node(node_tree)

    links.new(nrmtex.outputs["Color"], rgb_curves.inputs["Color"])
    links.new(rgb_curves.outputs["Color"], normalmap.inputs["Color"])
    links.new(normalmap.outputs["Normal"], bsdf.inputs["Normal"])


def create_normal_invert_node(node_tree: bpy.types.NodeTree):
    """Create RGB curves node that inverts that green channel of normal maps"""
    rgb_curves: bpy.types.ShaderNodeRGBCurve = node_tree.nodes.new(
        "ShaderNodeRGBCurve")

    green_curves = rgb_curves.mapping.curves[1]
    green_curves.points[0].location = (0, 1)
    green_curves.points[1].location = (1, 0)

    return rgb_curves


def link_specular(b: ShaderBuilder, spctex):
    node_tree = b.node_tree
    bsdf = b.bsdf
    links = node_tree.links
    links.new(spctex.outputs["Color"], bsdf.inputs["Specular"])


def create_pixel_tint_nodes(b: ShaderBuilder, tex, tinttex, tintflags):
    tinttex.interpolation = "Closest"
    node_tree = b.node_tree
    bsdf = b.bsdf
    links = node_tree.links
    mathns = []
    locx = 0
    locy = 50
    for _ in range(6):
        math = node_tree.nodes.new("ShaderNodeMath")
        math.location.x = locx
        math.location.y = locy
        mathns.append(math)
        locx += 150
    comxyz = node_tree.nodes.new("ShaderNodeCombineXYZ")

    mathns[0].operation = "MULTIPLY"
    links.new(tex.outputs["Alpha"], mathns[0].inputs[0])
    mathns[0].inputs[1].default_value = 255.009995

    mathns[1].operation = "ROUND"
    links.new(mathns[0].outputs[0], mathns[1].inputs[0])

    mathns[2].operation = "SUBTRACT"
    links.new(mathns[1].outputs[0], mathns[2].inputs[0])
    mathns[2].inputs[1].default_value = 32.0

    mathns[3].operation = "MULTIPLY"
    links.new(mathns[2].outputs[0], mathns[3].inputs[0])
    mathns[3].inputs[1].default_value = 0.007813
    links.new(mathns[3].outputs[0], comxyz.inputs[0])

    mathns[4].operation = "MULTIPLY"
    mathns[4].inputs[0].default_value = 0.03125
    mathns[4].inputs[1].default_value = 0.5

    mathns[5].operation = "SUBTRACT"
    mathns[5].inputs[0].default_value = 1
    links.new(mathns[4].outputs[0], mathns[5].inputs[1])
    links.new(mathns[5].outputs[0], comxyz.inputs[1])

    links.new(comxyz.outputs[0], tinttex.inputs[0])
    links.new(tinttex.outputs[0], bsdf.inputs["Base Color"])


def create_tint_nodes(b: ShaderBuilder, tinttex, txt, tintflags):
    if tintflags == 2:
        create_pixel_tint_nodes(b, txt, tinttex, tintflags)
        return
    # create shader attribute node
    node_tree = b.node_tree
    bsdf = b.bsdf
    links = node_tree.links
    attr = node_tree.nodes.new("ShaderNodeAttribute")
    attr.attribute_name = "TintColor"
    mix = node_tree.nodes.new("ShaderNodeMixRGB")
    mix.inputs["Fac"].default_value = 0.95
    mix.blend_type = "MULTIPLY"
    links.new(attr.outputs["Color"], mix.inputs[2])
    links.new(txt.outputs[0], mix.inputs[1])
    links.new(mix.outputs[0], bsdf.inputs["Base Color"])


def create_decal_nodes(b: ShaderBuilder, texture, decalflag):
    node_tree = b.node_tree
    output = b.material_output
    bsdf = b.bsdf
    links = node_tree.links
    mix = node_tree.nodes.new("ShaderNodeMixShader")
    trans = node_tree.nodes.new("ShaderNodeBsdfTransparent")
    links.new(texture.outputs["Color"], bsdf.inputs["Base Color"])

    if decalflag == 0:
        links.new(texture.outputs["Alpha"], mix.inputs["Fac"])
    if decalflag == 1:
        vcs = node_tree.nodes.new("ShaderNodeVertexColor")
        vcs.layer_name = "Color 1"  # set in create shader???
        multi = node_tree.nodes.new("ShaderNodeMath")
        multi.operation = "MULTIPLY"
        links.new(vcs.outputs["Alpha"], multi.inputs[0])
        links.new(texture.outputs["Alpha"], multi.inputs[1])
        links.new(multi.outputs["Value"], mix.inputs["Fac"])

    links.new(trans.outputs["BSDF"], mix.inputs[1])
    links.remove(bsdf.outputs["BSDF"].links[0])
    links.new(bsdf.outputs["BSDF"], mix.inputs[2])
    links.new(mix.outputs["Shader"], output.inputs["Surface"])


def create_distance_map_nodes(b: ShaderBuilder, distance_map_texture: bpy.types.ShaderNodeTexImage):
    node_tree = b.node_tree
    output = b.material_output
    bsdf = b.bsdf
    links = node_tree.links
    mix = node_tree.nodes.new("ShaderNodeMixShader")
    trans = node_tree.nodes.new("ShaderNodeBsdfTransparent")
    multiply_color = node_tree.nodes.new("ShaderNodeVectorMath")
    multiply_color.operation = "MULTIPLY"
    multiply_alpha = node_tree.nodes.new("ShaderNodeMath")
    multiply_alpha.operation = "MULTIPLY"
    multiply_alpha.inputs[1].default_value = 1.0  # alpha value
    distance_greater_than = node_tree.nodes.new("ShaderNodeMath")
    distance_greater_than.operation = "GREATER_THAN"
    distance_greater_than.inputs[1].default_value = 0.5  # distance threshold
    distance_separate_x = node_tree.nodes.new("ShaderNodeSeparateXYZ")
    fill_color_combine = node_tree.nodes.new("ShaderNodeCombineXYZ")
    fill_color_r = node_tree.nodes["fillColor_x"]
    fill_color_g = node_tree.nodes["fillColor_y"]
    fill_color_b = node_tree.nodes["fillColor_z"]

    #distance_map_texture.image.colormapping_settings.name = "Non-Color"

    # combine fillColor into a vector
    links.new(fill_color_r.outputs["Value"], fill_color_combine.inputs["X"])
    links.new(fill_color_g.outputs["Value"], fill_color_combine.inputs["Y"])
    links.new(fill_color_b.outputs["Value"], fill_color_combine.inputs["Z"])

    # extract distance value from texture and check > 0.5
    links.new(distance_map_texture.outputs["Color"], distance_separate_x.inputs["Vector"])
    links.remove(distance_map_texture.outputs["Alpha"].links[0])
    links.new(distance_separate_x.outputs["X"], distance_greater_than.inputs["Value"])

    # multiply color and alpha by distance check result
    links.new(distance_greater_than.outputs["Value"], multiply_alpha.inputs[0])
    links.new(distance_greater_than.outputs["Value"], multiply_color.inputs[0])
    links.new(fill_color_combine.outputs["Vector"], multiply_color.inputs[1])

    # connect output color and alpha
    links.new(multiply_alpha.outputs["Value"], mix.inputs["Fac"])
    links.new(multiply_color.outputs["Vector"], bsdf.inputs["Base Color"])

    # connect BSDFs and material output
    links.new(trans.outputs["BSDF"], mix.inputs[1])
    links.remove(bsdf.outputs["BSDF"].links[0])
    links.new(bsdf.outputs["BSDF"], mix.inputs[2])
    links.new(mix.outputs["Shader"], output.inputs["Surface"])


def create_emissive_nodes(b: ShaderBuilder):
    node_tree = b.node_tree
    links = node_tree.links
    output = b.material_output
    tmpn = output.inputs[0].links[0].from_node
    mix = node_tree.nodes.new("ShaderNodeMixShader")    
    if tmpn == b.bsdf:
        em = node_tree.nodes.new("ShaderNodeEmission")
        diff = node_tree.nodes["DiffuseSampler"]
        links.new(diff.outputs[0], em.inputs[0])
        links.new(em.outputs[0], mix.inputs[1])
        links.new(tmpn.outputs[0], mix.inputs[2])
        links.new(mix.outputs[0], output.inputs[0])


def link_value_shader_parameters(b: ShaderBuilder):
    shader = b.shader
    node_tree = b.node_tree
    links = node_tree.links

    bsdf = b.bsdf
    bmp = None
    spec_im = None
    spec_fm = None
    em_m = None

    for param in shader.parameters:
        if param.name == "bumpiness":
            bmp = node_tree.nodes["bumpiness_x"]
        elif param.name == "specularIntensityMult":
            spec_im = node_tree.nodes["specularIntensityMult_x"]
        elif param.name == "specularFalloffMult":
            spec_fm = node_tree.nodes["specularFalloffMult_x"]
        elif param.name == "emissiveMultiplier":
            em_m = node_tree.nodes["emissiveMultiplier_x"]

    if bmp:
        nm = try_get_node_by_cls(node_tree, bpy.types.ShaderNodeNormalMap)
        if nm:
            links.new(bmp.outputs[0], nm.inputs[0])
    if spec_im:
        spec = try_get_node(node_tree, "SpecSampler")
        if spec:
            map = node_tree.nodes.new("ShaderNodeMapRange")
            map.inputs[2].default_value = 1
            map.inputs[4].default_value = 1
            map.clamp = True
            mult = node_tree.nodes.new("ShaderNodeMath")
            mult.operation = "MULTIPLY"
            links.new(spec.outputs[0], mult.inputs[0])
            links.new(map.outputs[0], mult.inputs[1])
            links.new(spec_im.outputs[0], map.inputs[0])
            links.new(mult.outputs[0], bsdf.inputs["Specular"])
    if spec_fm:
        map = node_tree.nodes.new("ShaderNodeMapRange")
        map.inputs[2].default_value = 512
        map.inputs[3].default_value = 1
        map.inputs[4].default_value = 0
        map.clamp = True
        links.new(spec_fm.outputs[0], map.inputs[0])
        links.new(map.outputs[0], bsdf.inputs["Roughness"])
    if em_m:
        em = try_get_node_by_cls(node_tree, bpy.types.ShaderNodeEmission)
        if em:
            links.new(em_m.outputs[0], em.inputs[1])


def create_water_nodes(b: ShaderBuilder):
    node_tree = b.node_tree
    links = node_tree.links
    bsdf = b.bsdf
    output = b.material_output
    mix_shader = node_tree.nodes.new("ShaderNodeMixShader")
    add_shader = node_tree.nodes.new("ShaderNodeAddShader")
    vol_absorb = node_tree.nodes.new("ShaderNodeVolumeAbsorption")
    vol_absorb.inputs[0].default_value = (0.772, 0.91, 0.882, 1.0)
    vol_absorb.inputs[1].default_value = 0.25  # Density
    bsdf.inputs[0].default_value = (0.588, 0.91, 0.851, 1.0)
    bsdf.inputs[19].default_value = (
        0.49102, 0.938685, 1.0, 1.0)  # Emission Colour
    bsdf.inputs['Emission Strength'].default_value = 0.1
    glass_shader = node_tree.nodes.new("ShaderNodeBsdfGlass")
    glass_shader.inputs['IOR'].default_value = 1.333
    trans_shader = node_tree.nodes.new("ShaderNodeBsdfTransparent")
    light_path = node_tree.nodes.new("ShaderNodeLightPath")
    bump = node_tree.nodes.new("ShaderNodeBump")
    bump.inputs['Strength'].default_value = 0.05
    noise_tex = node_tree.nodes.new("ShaderNodeTexNoise")
    noise_tex.inputs['Scale'].default_value = 12.0
    noise_tex.inputs['Detail'].default_value = 3.0
    noise_tex.inputs[4].default_value = 0.85  # Roughness

    links.new(glass_shader.outputs[0], mix_shader.inputs[1])
    links.new(trans_shader.outputs[0], mix_shader.inputs[2])
    links.new(bsdf.outputs[0], add_shader.inputs[0])
    links.new(vol_absorb.outputs[0], add_shader.inputs[1])
    links.new(add_shader.outputs[0], output.inputs['Volume'])
    links.new(mix_shader.outputs[0], output.inputs['Surface'])
    links.new(light_path.outputs['Is Shadow Ray'], mix_shader.inputs['Fac'])
    links.new(noise_tex.outputs['Fac'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], glass_shader.inputs['Normal'])


def create_basic_shader_nodes(b: ShaderBuilder):
    shader = b.shader
    filename = b.filename
    mat = b.material
    node_tree = b.node_tree
    bsdf = b.bsdf

    texture = None
    texture2 = None
    tintpal = None
    bumptex = None
    spectex = None
    detltex = None
    is_distance_map = False

    for param in shader.parameters:
        if param.type == "Texture":
            imgnode = create_image_node(node_tree, param)
            if param.name in ("DiffuseSampler", "PlateBgSampler"):
                texture = imgnode
            elif param.name in ("BumpSampler", "PlateBgBumpSampler"):
                bumptex = imgnode
            elif param.name == "SpecSampler":
                spectex = imgnode
            elif param.name == "DetailSampler":
                detltex = imgnode
            elif param.name in ("TintPaletteSampler", "TextureSamplerDiffPal"):
                tintpal = imgnode
            elif param.name == "distanceMapSampler":
                texture = imgnode
                is_distance_map = True
            elif param.name in ("DiffuseSampler2", "DiffuseExtraSampler"):
                texture2 = imgnode
            else:
                if not texture:
                    texture = imgnode

        elif param.type == "Vector":
            create_vector_nodes(node_tree, param)
        elif param.type == "Array":
            create_array_nodes(node_tree, param)
        else:
            raise Exception(
                f"Unknown shader parameter! {param.type} {param.name}")

    use_diff = True if texture else False
    use_diff2 = True if texture2 else False
    use_bump = True if bumptex else False
    use_spec = True if spectex else False
    use_detl = True if detltex else False
    use_tint = True if tintpal else False

    # get correct vertex color index to use
    tintflag = 0
    if use_tint:
        if filename in ShaderManager.tint_flag_1:
            tintflag = 1
        elif filename in ShaderManager.tint_flag_2:
            tintflag = 2

    use_decal = True if filename in ShaderManager.tinted_shaders() else False
    decalflag = 0
    blend_mode = "OPAQUE"
    if use_decal:
        # set blend mode
        if filename in ShaderManager.cutout_shaders():
            blend_mode = "CLIP"
        else:
            blend_mode = "BLEND"
            decalflag = 1
        # set flags
        if filename in [ShaderManager.decals[20]]:  # decal_dirt.sps
            # txt_alpha_mask = ?
            decalflag = 2
        # decal_normal_only.sps / mirror_decal.sps / reflect_decal.sps
        elif filename in [ShaderManager.decals[4], ShaderManager.decals[21], ShaderManager.decals[19]]:
            decalflag = 3
        # decal_spec_only.sps / spec_decal.sps
        elif filename in [ShaderManager.decals[3], ShaderManager.decals[17]]:
            decalflag = 4

    is_emissive = True if filename in ShaderManager.em_shaders else False

    if not use_decal:
        if use_diff:
            if use_diff2:
                link_diffuses(b, texture, texture2)
            else:
                link_diffuse(b, texture)
    else:
        create_decal_nodes(b, texture, decalflag)

    if use_bump:
        if use_detl:
            link_detailed_normal(b, bumptex, detltex, spectex)
        else:
            link_normal(b, bumptex)
    if use_spec:
        link_specular(b, spectex)
    else:
        bsdf.inputs["Specular"].default_value = 0
    if use_tint:
        create_tint_nodes(b, tintpal, texture, tintflag)

    if is_emissive:
        create_emissive_nodes(b)

    is_water = filename in ShaderManager.water_shaders
    if is_water:
        create_water_nodes(b)

    if is_distance_map:
        blend_mode = "BLEND"
        create_distance_map_nodes(b, texture)

    # link value parameters
    link_value_shader_parameters(b)

    mat.blend_method = blend_mode


def create_terrain_shader(b: ShaderBuilder):
    shader = b.shader
    filename = b.filename
    mat = b.material
    node_tree = b.node_tree
    bsdf = b.bsdf
    links = node_tree.links

    ts1 = None
    ts2 = None
    ts3 = None
    ts4 = None
    bs1 = None
    bs2 = None
    bs3 = None
    bs4 = None
    tm = None

    for param in shader.parameters:
        if param.type == "Texture":
            imgnode = create_image_node(node_tree, param)
            if param.name == "TextureSampler_layer0":
                ts1 = imgnode
            elif param.name == "TextureSampler_layer1":
                ts2 = imgnode
            elif param.name == "TextureSampler_layer2":
                ts3 = imgnode
            elif param.name == "TextureSampler_layer3":
                ts4 = imgnode
            elif param.name == "BumpSampler_layer0":
                bs1 = imgnode
            elif param.name == "BumpSampler_layer1":
                bs2 = imgnode
            elif param.name == "BumpSampler_layer2":
                bs3 = imgnode
            elif param.name == "BumpSampler_layer3":
                bs4 = imgnode
            elif param.name == "lookupSampler":
                tm = imgnode
        elif param.type == "Vector":
            create_vector_nodes(node_tree, param)
        elif param.type == "Array":
            create_array_nodes(node_tree, param)
        else:
            raise Exception(
                f"Unknown shader parameter! {param.type} {param.name}")

    mixns = []
    for _ in range(8 if tm else 7):
        mix = node_tree.nodes.new("ShaderNodeMixRGB")
        mixns.append(mix)

    seprgb = node_tree.nodes.new("ShaderNodeSeparateRGB")
    if filename in ShaderManager.mask_only_terrains:
        links.new(tm.outputs[0], seprgb.inputs[0])
    else:
        attr_c1 = node_tree.nodes.new("ShaderNodeAttribute")
        attr_c1.attribute_name = "Color 2"
        links.new(attr_c1.outputs[0], mixns[0].inputs[1])
        links.new(attr_c1.outputs[0], mixns[0].inputs[2])

        attr_c0 = node_tree.nodes.new("ShaderNodeAttribute")
        attr_c0.attribute_name = "Color 1"
        links.new(attr_c0.outputs[3], mixns[0].inputs[0])
        links.new(mixns[0].outputs[0], seprgb.inputs[0])

    # t1 / t2
    links.new(seprgb.outputs[2], mixns[1].inputs[0])
    links.new(ts1.outputs[0], mixns[1].inputs[1])
    links.new(ts2.outputs[0], mixns[1].inputs[2])

    # t3 / t4
    links.new(seprgb.outputs[2], mixns[2].inputs[0])
    links.new(ts3.outputs[0], mixns[2].inputs[1])
    links.new(ts4.outputs[0], mixns[2].inputs[2])

    links.new(seprgb.outputs[1], mixns[3].inputs[0])
    links.new(mixns[1].outputs[0], mixns[3].inputs[1])
    links.new(mixns[2].outputs[0], mixns[3].inputs[2])

    links.new(mixns[3].outputs[0], bsdf.inputs["Base Color"])

    if bs1:
        links.new(seprgb.outputs[2], mixns[4].inputs[0])
        links.new(bs1.outputs[0], mixns[4].inputs[1])
        links.new(bs2.outputs[0], mixns[4].inputs[2])

        links.new(seprgb.outputs[2], mixns[5].inputs[0])
        links.new(bs3.outputs[0], mixns[5].inputs[1])
        links.new(bs4.outputs[0], mixns[5].inputs[2])

        links.new(seprgb.outputs[1], mixns[6].inputs[0])
        links.new(mixns[4].outputs[0], mixns[6].inputs[1])
        links.new(mixns[5].outputs[0], mixns[6].inputs[2])

        nrm = node_tree.nodes.new("ShaderNodeNormalMap")
        links.new(mixns[6].outputs[0], nrm.inputs[1])
        links.new(nrm.outputs[0], bsdf.inputs["Normal"])

    # assign lookup sampler last so that it overwrites any socket connections
    if tm:
        attr_t1 = node_tree.nodes.new("ShaderNodeAttribute")
        attr_t1.attribute_name = "UVMap 1"
        links.new(attr_t1.outputs[1], tm.inputs[0])
        links.new(tm.outputs[0], mixns[0].inputs[1])

    # link value parameters
    bsdf.inputs["Specular"].default_value = 0
    link_value_shader_parameters(b)


def create_shader(filename: str):
    shader = ShaderManager.find_shader(filename)
    if shader is None:
        raise AttributeError(f"Shader '{filename}' does not exist!")

    filename = shader.filename  # in case `filename` was hashed initially
    base_name = ShaderManager.find_shader_base_name(filename)

    mat = bpy.data.materials.new(filename.replace(".sps", ""))
    mat.sollum_type = MaterialType.SHADER
    mat.use_nodes = True
    mat.shader_properties.name = base_name
    mat.shader_properties.filename = filename
    mat.shader_properties.renderbucket = shader.render_buckets[0]

    bsdf, material_output = find_bsdf_and_material_output(mat)
    assert material_output is not None, "ShaderNodeOutputMaterial not found in default node_tree!"
    assert bsdf is not None, "ShaderNodeBsdfPrincipled not found in default node_tree!"

    builder = ShaderBuilder(shader=shader,
                            filename=filename,
                            material=mat,
                            node_tree=mat.node_tree,
                            material_output=material_output,
                            bsdf=bsdf)

    if filename in ShaderManager.terrains:
        create_terrain_shader(builder)
    else:
        create_basic_shader_nodes(builder)

    if shader.is_uv_animation_supported:
        add_global_anim_uv_nodes(mat)

    organize_node_tree(builder)

    return mat
