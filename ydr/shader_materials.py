import bpy
from ..tools.version import USE_LEGACY
from ..cwxml.shader import ShaderManager
from ..sollumz_properties import MaterialType
from collections import namedtuple

ShaderMaterial = namedtuple("ShaderMaterial", "name, ui_name, value")

shadermats = []

for shader in ShaderManager.shaders.values():
    name = shader.filename.replace(".sps", "").upper()

    shadermats.append(ShaderMaterial(
        name, name.replace("_", " "), shader.filename))


def try_get_node(node_tree, name):
    try:
        return node_tree.nodes[name]
    except:
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
        node_output = False
        node_input = False
        for output in node.outputs:
            for link in output.links:
                if link.to_node is not None and link.from_node is not None:
                    node_output = True
                    break
        for input in node.inputs:
            for link in input.links:
                if link.to_node is not None and link.from_node is not None:
                    node_input = True
                    break
        if node_output == False and node_input == False:
            loose_nodes.append(node)
    return loose_nodes


def organize_node_tree(node_tree):
    mat_output = try_get_node(node_tree, "Material Output")
    mat_output.location.x = 0
    mat_output.location.y = 0
    organize_node(mat_output)
    organize_loose_nodes(node_tree, 1000, 0)


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


def get_tinted_sampler(mat):
    nodes = mat.node_tree.nodes
    for node in nodes:
        if node.name in ("TintPaletteSampler", "TextureSamplerDiffPal"):
            if node.image:
                return node.image
            else:
                return None  # return none because that means it has the tinted sampler parameter but no image
    return None  # return none because that means it has no parameter which means it isnt a tinted shader


def get_detail_extra_sampler(mat):
    nodes = mat.node_tree.nodes
    for node in nodes:
        if node.name == "Extra":
            return node
    return None


def create_tinted_texture_from_image(img):
    bpy.ops.texture.new()
    texture = bpy.data.textures[len(bpy.data.textures) - 1]
    if img is not None:
        texture.image = img
    texture.use_interpolation = False
    texture.use_mipmap = False
    texture.use_alpha = False
    texture.name = img.name + "_texture" if img else "palette_texture"
    return texture


def create_tinted_shader_graph(obj):
    mat = obj.data.materials[0]
    tint_img = get_tinted_sampler(mat)
    if mat.shader_properties.filename in ShaderManager.tint_flag_2 or tint_img is None:
        return

    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.node.new_geometry_nodes_modifier()
    tint_node_graph = create_tinted_geometry_graph()
    geom = obj.modifiers["GeometryNodes"]
    geom.node_group = tint_node_graph

    # set input / output variables
    input_id = geom.node_group.inputs[1].identifier
    geom[input_id + "_attribute_name"] = "colour0"
    geom[input_id + "_use_attribute"] = True
    output_id = geom.node_group.outputs[1].identifier
    geom[output_id + "_attribute_name"] = "TintColor"
    geom[output_id + "_use_attribute"] = True

    # create texture and get texture node
    tint_txt = create_tinted_texture_from_image(tint_img)
    txt_node = geom.node_group.nodes["Image Texture"]
    txt_node.inputs[0].default_value = tint_txt.image

    obj.data.vertex_colors.new(name="TintColor")


def link_geos(links, node1, node2):
    links.new(node1.inputs["Geometry"], node2.outputs["Geometry"])


def create_tinted_geometry_graph():
    geo_node_tree = bpy.data.node_groups.new(
        name="TintGeometry", type="GeometryNodeTree")
    input = geo_node_tree.nodes.new("NodeGroupInput")
    output = geo_node_tree.nodes.new("NodeGroupOutput")

    # Create the necessary sockets for the node group
    geo_node_tree.inputs.new("NodeSocketGeometry", "Geometry")
    geo_node_tree.inputs.new("NodeSocketVector", "Vector")
    geo_node_tree.outputs.new("NodeSocketGeometry", "Geometry")
    geo_node_tree.outputs.new("NodeSocketColor", "Color")

    # link input / output node to create geometry socket
    capture_attribute = geo_node_tree.nodes.new("GeometryNodeCaptureAttribute")
    capture_attribute.domain = "CORNER"
    capture_attribute.data_type = "FLOAT_COLOR"
    geo_node_tree.links.new(input.outputs[0], capture_attribute.inputs[0])
    geo_node_tree.links.new(capture_attribute.outputs[0], output.inputs[0])

    # create and link texture node
    texture_node = geo_node_tree.nodes.new("GeometryNodeImageTexture")
    texture_node.interpolation = "Closest"
    geo_node_tree.links.new(
        capture_attribute.outputs[3], texture_node.inputs[1])
    geo_node_tree.links.new(texture_node.outputs[0], output.inputs[1])

    # separate colour0
    separate_node = geo_node_tree.nodes.new("ShaderNodeSeparateXYZ")
    geo_node_tree.links.new(input.outputs[1], separate_node.inputs[0])

    # math node 0
    less_than_node = geo_node_tree.nodes.new("ShaderNodeMath")
    less_than_node.operation = "LESS_THAN"
    geo_node_tree.links.new(separate_node.outputs[2], less_than_node.inputs[0])
    less_than_node.inputs[1].default_value = 0.003

    # math node 1
    subtract_node = geo_node_tree.nodes.new("ShaderNodeMath")
    subtract_node.operation = "SUBTRACT"
    geo_node_tree.links.new(less_than_node.outputs[0], subtract_node.inputs[1])
    subtract_node.inputs[0].default_value = 1.0

    # math node 2
    multiply_node = geo_node_tree.nodes.new("ShaderNodeMath")
    multiply_node.operation = "MULTIPLY"
    geo_node_tree.links.new(separate_node.outputs[2], multiply_node.inputs[0])
    multiply_node.inputs[1].default_value = 12.920

    # math node 3
    multiply_node2 = geo_node_tree.nodes.new("ShaderNodeMath")
    multiply_node2.operation = "MULTIPLY"
    geo_node_tree.links.new(multiply_node.outputs[0], multiply_node2.inputs[0])
    geo_node_tree.links.new(
        less_than_node.outputs[0], multiply_node2.inputs[1])

    # math node 4
    power_node = geo_node_tree.nodes.new("ShaderNodeMath")
    power_node.operation = "POWER"
    geo_node_tree.links.new(separate_node.outputs[2], power_node.inputs[0])
    power_node.inputs[1].default_value = 0.417

    # math node 5
    multiply_node3 = geo_node_tree.nodes.new("ShaderNodeMath")
    multiply_node3.operation = "MULTIPLY"
    geo_node_tree.links.new(power_node.outputs[0], multiply_node3.inputs[0])
    multiply_node3.inputs[1].default_value = 1.055

    # math node 6
    subtract_node2 = geo_node_tree.nodes.new("ShaderNodeMath")
    subtract_node2.operation = "SUBTRACT"
    geo_node_tree.links.new(
        multiply_node3.outputs[0], subtract_node2.inputs[0])
    subtract_node2.inputs[1].default_value = 0.055

    # math node 7
    multiply_node4 = geo_node_tree.nodes.new("ShaderNodeMath")
    multiply_node4.operation = "MULTIPLY"
    geo_node_tree.links.new(
        subtract_node2.outputs[0], multiply_node4.inputs[0])
    geo_node_tree.links.new(subtract_node.outputs[0], multiply_node4.inputs[1])

    # math node 8
    add_node = geo_node_tree.nodes.new("ShaderNodeMath")
    add_node.operation = "ADD"
    geo_node_tree.links.new(multiply_node2.outputs[0], add_node.inputs[0])
    geo_node_tree.links.new(multiply_node4.outputs[0], add_node.inputs[1])

    # create and link vector
    combine_rgb_node = geo_node_tree.nodes.new("ShaderNodeCombineRGB")
    geo_node_tree.links.new(add_node.outputs[0], combine_rgb_node.inputs[0])
    geo_node_tree.links.new(
        combine_rgb_node.outputs[0], capture_attribute.inputs[3])

    return geo_node_tree


def create_image_node(node_tree, param):
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


def link_diffuse(node_tree, imgnode):
    bsdf = node_tree.nodes["Principled BSDF"]
    links = node_tree.links
    links.new(imgnode.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(imgnode.outputs["Alpha"], bsdf.inputs["Alpha"])


def link_diffuses(node_tree, tex1, tex2):
    bsdf = node_tree.nodes["Principled BSDF"]
    links = node_tree.links
    rgb = node_tree.nodes.new("ShaderNodeMixRGB")
    links.new(tex1.outputs["Color"], rgb.inputs["Color1"])
    links.new(tex2.outputs["Color"], rgb.inputs["Color2"])
    links.new(tex2.outputs["Alpha"], rgb.inputs["Fac"])
    links.new(rgb.outputs["Color"], bsdf.inputs["Base Color"])
    return rgb


def link_detailed_normal(node_tree, bumptex, dtltex, spectex):
    dtltex2 = node_tree.nodes.new("ShaderNodeTexImage")
    dtltex2.name = "Extra"
    bsdf = node_tree.nodes["Principled BSDF"]
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

    attr.attribute_name = "texcoord0"
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


def link_normal(node_tree, nrmtex):
    bsdf = node_tree.nodes["Principled BSDF"]
    links = node_tree.links
    normalmap = node_tree.nodes.new("ShaderNodeNormalMap")
    links.new(nrmtex.outputs["Color"], normalmap.inputs["Color"])
    links.new(normalmap.outputs["Normal"], bsdf.inputs["Normal"])


def link_normal(node_tree, nrmtex):
    bsdf = node_tree.nodes["Principled BSDF"]
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


def link_specular(node_tree, spctex):
    bsdf = node_tree.nodes["Principled BSDF"]
    links = node_tree.links
    links.new(spctex.outputs["Color"], bsdf.inputs["Specular"])


def create_pixel_tint_nodes(node_tree, tex, tinttex):
    tinttex.interpolation = "Closest"
    bsdf = node_tree.nodes["Principled BSDF"]
    links = node_tree.links

    math_nodes = []
    locx = 0
    locy = 50
    for _ in range(6):
        math = node_tree.nodes.new("ShaderNodeMath")
        math.location.x = locx
        math.location.y = locy
        math_nodes.append(math)
        locx += 150
    # positions each math node instead of manually defining each location
    combine_xyz_node = node_tree.nodes.new("ShaderNodeCombineXYZ")

    # math node 0
    math_nodes[0].operation = "MULTIPLY"
    links.new(tex.outputs["Alpha"], math_nodes[0].inputs[0])
    math_nodes[0].inputs[1].default_value = 255.009995

    # math node 1
    math_nodes[1].operation = "ROUND"
    links.new(math_nodes[0].outputs[0], math_nodes[1].inputs[0])

    # math node 2
    math_nodes[2].operation = "SUBTRACT"
    links.new(math_nodes[1].outputs[0], math_nodes[2].inputs[0])
    math_nodes[2].inputs[1].default_value = 32.0

    # math node 3
    math_nodes[3].operation = "MULTIPLY"
    links.new(math_nodes[2].outputs[0], math_nodes[3].inputs[0])
    math_nodes[3].inputs[1].default_value = 0.007813
    links.new(math_nodes[3].outputs[0], combine_xyz_node.inputs[0])

    # math node 4
    math_nodes[4].operation = "MULTIPLY"
    math_nodes[4].inputs[0].default_value = 0.03125
    math_nodes[4].inputs[1].default_value = 0.5

    # math node 5
    math_nodes[5].operation = "SUBTRACT"
    math_nodes[5].inputs[0].default_value = 1
    links.new(math_nodes[4].outputs[0], math_nodes[5].inputs[1])
    links.new(math_nodes[5].outputs[0], combine_xyz_node.inputs[1])

    # link combine xyz node to tint texture and tint texture to BSDF base color
    links.new(combine_xyz_node.outputs[0], tinttex.inputs[0])
    links.new(tinttex.outputs[0], bsdf.inputs["Base Color"])


def create_tint_nodes(node_tree, tinttex, txt, tintflags):
    if tintflags == 2:
        create_pixel_tint_nodes(node_tree, txt, tinttex, tintflags)
        return
    # create shader attribute node
    bsdf = node_tree.nodes["Principled BSDF"]
    links = node_tree.links
    attr = node_tree.nodes.new("ShaderNodeAttribute")
    attr.attribute_name = "TintColor"
    mix = node_tree.nodes.new("ShaderNodeMixRGB")
    mix.inputs["Fac"].default_value = 0.95
    mix.blend_type = "MULTIPLY"
    links.new(attr.outputs["Color"], mix.inputs[2])
    links.new(txt.outputs[0], mix.inputs[1])
    links.new(mix.outputs[0], bsdf.inputs["Base Color"])


def create_decal_nodes(node_tree, texture, decalflag):
    output = node_tree.nodes["Material Output"]
    bsdf = node_tree.nodes["Principled BSDF"]
    links = node_tree.links
    mix_shader = node_tree.nodes.new("ShaderNodeMixShader")
    transparent_bsdf = node_tree.nodes.new("ShaderNodeBsdfTransparent")
    links.new(texture.outputs["Color"], bsdf.inputs["Base Color"])

    if decalflag == 0:
        links.new(texture.outputs["Alpha"], mix_shader.inputs["Fac"])
    if decalflag == 1:
        vcs = node_tree.nodes.new("ShaderNodeVertexColor")
        vcs.layer_name = "colour0"
        multiply_node = node_tree.nodes.new("ShaderNodeMath")
        multiply_node.operation = "MULTIPLY"
        links.new(vcs.outputs["Alpha"], multiply_node.inputs[0])
        links.new(texture.outputs["Alpha"], multiply_node.inputs[1])
        links.new(multiply_node.outputs["Value"], mix_shader.inputs["Fac"])

    # shader mixing / linking
    links.new(transparent_bsdf.outputs["BSDF"], mix_shader.inputs[1])
    links.remove(bsdf.outputs["BSDF"].links[0])
    links.new(bsdf.outputs["BSDF"], mix_shader.inputs[2])
    links.new(mix_shader.outputs["Shader"], output.inputs["Surface"])


def create_emissive_nodes(node_tree):
    links = node_tree.links
    output = node_tree.nodes["Material Output"]
    temp_node = output.inputs[0].links[0].from_node
    if temp_node.name == "Principled BSDF":
        emission_shader = node_tree.nodes.new("ShaderNodeEmission")
        diffuse = node_tree.nodes["DiffuseSampler"]
        links.new(diffuse.outputs[0], emission_shader.inputs[0])
        links.new(emission_shader.outputs[0], output.inputs[0])


def link_value_shader_parameters(shader, node_tree):
    links = node_tree.links

    bump = None
    spec_im = None
    spec_fm = None
    emissive_m = None

    for param in shader.parameters:
        if param.name == "bumpiness":
            bump = node_tree.nodes["bumpiness_x"]
        elif param.name == "specularIntensityMult":
            spec_im = node_tree.nodes["specularIntensityMult_x"]
        elif param.name == "specularFalloffMult":
            spec_fm = node_tree.nodes["specularFalloffMult_x"]
        elif param.name == "emissiveMultiplier":
            emissive_m = node_tree.nodes["emissiveMultiplier_x"]

    if bump:
        normal_map = try_get_node(node_tree, "Normal Map")
        if normal_map:
            links.new(bump.outputs[0], normal_map.inputs[0])
    if spec_im:
        specular = try_get_node(node_tree, "SpecSampler")
        bsdf = try_get_node(node_tree, "Principled BSDF")
        if specular and bsdf:
            map_range = node_tree.nodes.new("ShaderNodeMapRange")
            map_range.inputs[2].default_value = 1
            map_range.inputs[4].default_value = 1
            map_range.clamp = True
            multiply_node = node_tree.nodes.new("ShaderNodeMath")
            multiply_node.operation = "MULTIPLY"
            links.new(specular.outputs[0], multiply_node.inputs[0])
            links.new(map_range.outputs[0], multiply_node.inputs[1])
            links.new(spec_im.outputs[0], map_range.inputs[0])
            links.new(multiply_node.outputs[0], bsdf.inputs["Specular"])
    if spec_fm:
        bsdf = try_get_node(node_tree, "Principled BSDF")
        if bsdf:
            map_range = node_tree.nodes.new("ShaderNodeMapRange")
            map_range.inputs[2].default_value = 512
            map_range.inputs[3].default_value = 1
            map_range.inputs[4].default_value = 0
            map_range.clamp = True
            links.new(spec_fm.outputs[0], map_range.inputs[0])
            links.new(map_range.outputs[0], bsdf.inputs["Roughness"])
    if emissive_m:
        emissive = try_get_node(node_tree, "Emission")
        if emissive:
            links.new(emissive_m.outputs[0], emissive.inputs[1])


def create_water_nodes(node_tree):
    vol_absorb_density = 0.25
    vol_absorb_color = (0.772, 0.91, 0.882, 1.0)
    bsdf_base_color = (0.588, 0.91, 0.851, 1.0)
    bsdf_emission_color = (0.49102, 0.938685, 1.0, 1.0)
    bsdf_emission = 0.1
    glass_shader_ior = 1.333
    bump_strength = 0.05
    noise_roughness = 0.85
    noise_detail = 3.0
    noise_scale = 12.0
    # Material output
    mat_output = node_tree.nodes["Material Output"]
    mat_output_volume = mat_output.inputs['Volume']
    mat_output_surface = mat_output.inputs['Surface']
    # Mix Shader
    mix_shader = node_tree.nodes.new("ShaderNodeMixShader")
    mix_shader_factor = mix_shader.inputs[0]
    mix_shader_shader1 = mix_shader.inputs[1]
    mix_shader_shader2 = mix_shader.inputs[2]
    mix_shader_out = mix_shader.outputs[0]
    # Add Shader
    add_shader = node_tree.nodes.new("ShaderNodeAddShader")
    add_shader_shader1 = add_shader.inputs[0]
    add_shader_shader2 = add_shader.inputs[1]
    add_shader_out = add_shader.outputs[0]
    # Volume Absorbtion
    vol_absorb = node_tree.nodes.new("ShaderNodeVolumeAbsorption")
    vol_absorb_out = vol_absorb.outputs[0]
    vol_absorb.inputs[0].default_value = vol_absorb_color
    vol_absorb.inputs[1].default_value = vol_absorb_density
    # Principled BSDF
    bsdf = node_tree.nodes["Principled BSDF"]
    bsdf_out = bsdf.outputs[0]
    bsdf.inputs[0].default_value = bsdf_base_color
    bsdf.inputs[19].default_value = bsdf_emission_color
    bsdf.inputs['Emission Strength'].default_value = bsdf_emission
    # Glass Shader
    glass_shader = node_tree.nodes.new("ShaderNodeBsdfGlass")
    glass_shader.inputs['IOR'].default_value = glass_shader_ior
    glass_shader_normal = glass_shader.inputs['Normal']
    glass_shader_out = glass_shader.outputs[0]
    # Transparent Shader
    trans_shader = node_tree.nodes.new("ShaderNodeBsdfTransparent")
    trans_shader_out = trans_shader.outputs[0]
    # Light Path
    light_path = node_tree.nodes.new("ShaderNodeLightPath")
    light_path_out_shadow_ray = light_path.outputs['Is Shadow Ray']
    # Bump Node
    bump = node_tree.nodes.new("ShaderNodeBump")
    bump_height = bump.inputs['Height']
    bump_output = bump.outputs['Normal']
    bump.inputs['Strength'].default_value = bump_strength
    # Noise Texture
    noise_tex = node_tree.nodes.new("ShaderNodeTexNoise")
    noise_tex_factor = noise_tex.outputs['Fac']
    noise_tex.inputs['Scale'].default_value = noise_scale
    noise_tex.inputs['Detail'].default_value = noise_detail
    noise_tex.inputs[4].default_value = noise_roughness

    # Link nodes
    links = node_tree.links
    links.new(glass_shader_out, mix_shader_shader1)
    links.new(trans_shader_out, mix_shader_shader2)
    links.new(bsdf_out, add_shader_shader1)
    links.new(vol_absorb_out, add_shader_shader2)
    links.new(add_shader_out, mat_output_volume)
    links.new(mix_shader_out, mat_output_surface)
    links.new(light_path_out_shadow_ray, mix_shader_factor)
    links.new(noise_tex_factor, bump_height)
    links.new(bump_output, glass_shader_normal)


def create_basic_shader_nodes(mat, shader, filename):

    node_tree = mat.node_tree

    texture = None
    texture2 = None
    tint_pal = None
    bump_tex = None
    spec_tex = None
    detail_tex = None
    isdistmap = False

    for param in shader.parameters:
        if param.type == "Texture":
            imgnode = create_image_node(node_tree, param)
            if param.name in ("DiffuseSampler", "PlateBgSampler"):
                texture = imgnode
            elif param.name in ("BumpSampler", "PlateBgBumpSampler"):
                bump_tex = imgnode
            elif param.name == "SpecSampler":
                spec_tex = imgnode
            elif param.name == "DetailSampler":
                detail_tex = imgnode
            elif param.name in ("TintPaletteSampler", "TextureSamplerDiffPal"):
                tint_pal = imgnode
            elif param.name == "distanceMapSampler":
                texture = imgnode
                isdistmap = True
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

    use_diffuse = True if texture else False
    use_diffuse2 = True if texture2 else False
    use_bump = True if bump_tex else False
    use_spec = True if spec_tex else False
    use_detail = True if detail_tex else False
    use_tint = True if tint_pal else False

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
        if use_diffuse:
            if use_diffuse2:
                link_diffuses(node_tree, texture, texture2)
            else:
                link_diffuse(node_tree, texture)
    else:
        create_decal_nodes(node_tree, texture, decalflag)

    if use_bump:
        if use_detail:
            link_detailed_normal(node_tree, bump_tex, detail_tex, spec_tex)
        else:
            link_normal(node_tree, bump_tex)
    if use_spec:
        link_specular(node_tree, spec_tex)
    else:
        node_tree.nodes["Principled BSDF"].inputs["Specular"].default_value = 0
    if use_tint:
        create_tint_nodes(node_tree, tint_pal, texture, tintflag)

    if is_emissive:
        create_emissive_nodes(node_tree)

    is_water = filename in ShaderManager.water_shaders
    if is_water:
        create_water_nodes(node_tree)

    # link value parameters
    link_value_shader_parameters(shader, node_tree)

    mat.blend_method = blend_mode


def create_terrain_shader(mat, shader, filename):
    node_tree = mat.node_tree
    bsdf = node_tree.nodes["Principled BSDF"]
    links = node_tree.links

    tex_sampler1 = None
    tex_sampler2 = None
    tex_sampler3 = None
    tex_sampler4 = None
    bump_sampler1 = None
    bump_sampler2 = None
    bump_sampler3 = None
    bump_sampler4 = None
    lookup_sampler = None

    for param in shader.parameters:
        if param.type == "Texture":
            imgnode = create_image_node(node_tree, param)
            if param.name == "TextureSampler_layer0":
                tex_sampler1 = imgnode
            elif param.name == "TextureSampler_layer1":
                tex_sampler2 = imgnode
            elif param.name == "TextureSampler_layer2":
                tex_sampler3 = imgnode
            elif param.name == "TextureSampler_layer3":
                tex_sampler4 = imgnode
            elif param.name == "BumpSampler_layer0":
                bump_sampler1 = imgnode
            elif param.name == "BumpSampler_layer1":
                bump_sampler2 = imgnode
            elif param.name == "BumpSampler_layer2":
                bump_sampler3 = imgnode
            elif param.name == "BumpSampler_layer3":
                bump_sampler4 = imgnode
            elif param.name == "lookupSampler":
                lookup_sampler = imgnode
        elif param.type == "Vector":
            create_vector_nodes(node_tree, param)
        elif param.type == "Array":
            create_array_nodes(node_tree, param)
        else:
            raise Exception(
                f"Unknown shader parameter! {param.type} {param.name}")

    mix_nodes = []
    for _ in range(8 if lookup_sampler else 7):
        mix = node_tree.nodes.new("ShaderNodeMixRGB")
        mix_nodes.append(mix)

    separate_rgb = node_tree.nodes.new("ShaderNodeSeparateRGB")
    if filename in ShaderManager.mask_only_terrains:
        links.new(lookup_sampler.outputs[0], separate_rgb.inputs[0])
    else:
        attr_colour1 = node_tree.nodes.new("ShaderNodeAttribute")
        attr_colour1.attribute_name = "colour1"
        links.new(attr_colour1.outputs[0], mix_nodes[0].inputs[1])
        links.new(attr_colour1.outputs[0], mix_nodes[0].inputs[2])

        attr_colour0 = node_tree.nodes.new("ShaderNodeAttribute")
        attr_colour0.attribute_name = "colour0"
        links.new(attr_colour0.outputs[3], mix_nodes[0].inputs[0])
        links.new(mix_nodes[0].outputs[0], separate_rgb.inputs[0])

    # texture1 / texture2
    links.new(separate_rgb.outputs[2], mix_nodes[1].inputs[0])
    links.new(tex_sampler1.outputs[0], mix_nodes[1].inputs[1])
    links.new(tex_sampler2.outputs[0], mix_nodes[1].inputs[2])

    # texture3 / texture4
    links.new(separate_rgb.outputs[2], mix_nodes[2].inputs[0])
    links.new(tex_sampler3.outputs[0], mix_nodes[2].inputs[1])
    links.new(tex_sampler4.outputs[0], mix_nodes[2].inputs[2])

    links.new(separate_rgb.outputs[1], mix_nodes[3].inputs[0])
    links.new(mix_nodes[1].outputs[0], mix_nodes[3].inputs[1])
    links.new(mix_nodes[2].outputs[0], mix_nodes[3].inputs[2])

    links.new(mix_nodes[3].outputs[0], bsdf.inputs["Base Color"])

    if bump_sampler1:
        links.new(separate_rgb.outputs[2], mix_nodes[4].inputs[0])
        links.new(bump_sampler1.outputs[0], mix_nodes[4].inputs[1])
        links.new(bump_sampler2.outputs[0], mix_nodes[4].inputs[2])

        links.new(separate_rgb.outputs[2], mix_nodes[5].inputs[0])
        links.new(bump_sampler3.outputs[0], mix_nodes[5].inputs[1])
        links.new(bump_sampler4.outputs[0], mix_nodes[5].inputs[2])

        links.new(separate_rgb.outputs[1], mix_nodes[6].inputs[0])
        links.new(mix_nodes[4].outputs[0], mix_nodes[6].inputs[1])
        links.new(mix_nodes[5].outputs[0], mix_nodes[6].inputs[2])

        nrm = node_tree.nodes.new("ShaderNodeNormalMap")
        links.new(mix_nodes[6].outputs[0], nrm.inputs[1])
        links.new(nrm.outputs[0], bsdf.inputs["Normal"])

    # assign lookup sampler last so that it overwrites any socket connections
    if lookup_sampler:
        attr_t1 = node_tree.nodes.new("ShaderNodeAttribute")
        attr_t1.attribute_name = "texcoord1"
        links.new(attr_t1.outputs[1], lookup_sampler.inputs[0])
        links.new(lookup_sampler.outputs[0], mix_nodes[0].inputs[1])

    # link value parameters
    bsdf.inputs["Specular"].default_value = 0
    link_value_shader_parameters(shader, node_tree)


def create_shader(filename: str):
    if filename not in ShaderManager.shaders:
        raise AttributeError(f"Shader '{filename}' does not exist!")

    shader = ShaderManager.shaders[filename]
    base_name = ShaderManager.base_shaders[filename]

    mat = bpy.data.materials.new(filename.replace(".sps", ""))
    mat.sollum_type = MaterialType.SHADER
    mat.use_nodes = True
    mat.shader_properties.name = base_name
    mat.shader_properties.filename = filename
    mat.shader_properties.renderbucket = shader.render_buckets[0]

    if filename in ShaderManager.terrains:
        create_terrain_shader(mat, shader, filename)
    else:
        create_basic_shader_nodes(mat, shader, filename)

    organize_node_tree(mat.node_tree)

    return mat
