import bpy

from ..tools.version import USE_LEGACY
from ..resources.shader import ShaderManager
from ..sollumz_properties import MaterialType
from collections import namedtuple

ShaderMaterial = namedtuple("ShaderMaterial", "name, ui_name, value")

shadermats = []

for shader in ShaderManager.shaders.values():
    shadermats.append(ShaderMaterial(
        shader.name.upper(), shader.name.upper().replace('_', ' '), shader.name))


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
        no = False
        ni = False
        for output in node.outputs:
            for link in output.links:
                if link.to_node != None and link.from_node != None:
                    no = True
                    break
        for input in node.inputs:
            for link in input.links:
                if link.to_node != None and link.from_node != None:
                    ni = True
                    break
        if no == False and ni == False:
            loose_nodes.append(node)
    return loose_nodes


def organize_node_tree(node_tree):
    mo = try_get_node(node_tree, "Material Output")
    mo.location.x = 0
    mo.location.y = 0
    organize_node(mo)
    organize_loose_nodes(node_tree, 1000, 0)


def organize_node(node):
    child_nodes = get_child_nodes(node)
    if len(child_nodes) < 0:
        return

    level = node.location.y
    for child in child_nodes:
        child.location.x = node.location.x - 300  # (child.width + 25)
        child.location.y = level
        level -= 300  # child.height * 2 + 25
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


def get_tinted_sampler(mat):  # move to blenderhelper.py?
    nodes = mat.node_tree.nodes
    for node in nodes:
        if node.name in ("TintPaletteSampler", "TextureSamplerDiffPal"):
            if node.image:
                return node.image
            else:
                return None  # return none because that means it has the tinted sampler parameter but no image
    return None  # return none because that means it has no parameter which means it isnt a tinted shader


def get_detail_extra_sampler(mat):  # move to blenderhelper.py?
    nodes = mat.node_tree.nodes
    for node in nodes:
        if node.name == "Extra":
            return node
    return None


def create_tinted_texture_from_image(img):  # move to blenderhelper.py?
    bpy.ops.texture.new()
    txt = bpy.data.textures[len(bpy.data.textures) - 1]
    if img is not None:
        txt.image = img
    txt.use_interpolation = False
    txt.use_mipmap = False
    txt.use_alpha = False
    txt.name = img.name + "_texture" if img else "palette_texture"
    return txt


def create_tinted_shader_graph(obj):  # move to blenderhelper.py?
    mat = obj.data.materials[0]
    tint_img = get_tinted_sampler(mat)
    if mat.shader_properties.filename in ShaderManager.tint_flag_2 or tint_img == None:  # check here or?
        return

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.node.new_geometry_nodes_modifier()
    tnt_ng = create_tinted_geometry_graph()
    geom = obj.modifiers["GeometryNodes"]
    geom.node_group = tnt_ng
    txt = create_tinted_texture_from_image(tint_img)
    txt_node = geom.node_group.nodes["Attribute Sample Texture"]

    if USE_LEGACY:
        txt_node.texture = txt
    else:
        txt_node.inputs[1].default_value = txt

    obj.data.vertex_colors.new(name="TintColor")


def link_geos(links, node1, node2):
    links.new(node1.inputs["Geometry"], node2.outputs["Geometry"])


def create_tinted_geometry_graph():  # move to blenderhelper.py?
    gnt = bpy.data.node_groups.new(
        name="TintGeometry", type="GeometryNodeTree")
    input = gnt.nodes.new("NodeGroupInput")
    input.location.x = -150
    output = gnt.nodes.new("NodeGroupOutput")
    locx = 150

    if USE_LEGACY:
        sepxyz = gnt.nodes.new("GeometryNodeAttributeSeparateXYZ")
    else:
        sepxyz = gnt.nodes.new("GeometryNodeLegacyAttributeSeparateXYZ")
    gnt.links.new(input.outputs[0], sepxyz.inputs[0])

    mathns = []
    for i in range(9):
        if USE_LEGACY:
            math = gnt.nodes.new("GeometryNodeAttributeMath")
        else:
            math = gnt.nodes.new("GeometryNodeLegacyAttributeMath")

        math.location.x = locx
        if len(mathns) > 0:
            link_geos(gnt.links, math, mathns[i - 1])
        else:
            link_geos(gnt.links, math, sepxyz)
        mathns.append(math)
        locx += 150

    if USE_LEGACY:
        comxyz = gnt.nodes.new("GeometryNodeAttributeCombineXYZ")
    else:
        comxyz = gnt.nodes.new("GeometryNodeLegacyAttributeCombineXYZ")

    comxyz.location.x = locx
    locx += 150
    gnt.links.new(mathns[len(mathns) - 1].outputs["Geometry"],
                  comxyz.inputs["Geometry"])
    if USE_LEGACY:
        tsample = gnt.nodes.new("GeometryNodeAttributeSampleTexture")
    else:
        tsample = gnt.nodes.new("GeometryNodeLegacyAttributeSampleTexture")

    tsample.location.x = locx
    locx += 250
    gnt.links.new(comxyz.outputs["Geometry"], tsample.inputs["Geometry"])
    gnt.links.new(tsample.outputs[0], output.inputs[0])
    output.location.x = locx

    # assign attributes
    sepxyz.inputs[1].default_value = "colour0"
    sepxyz.inputs[5].default_value = "b"

    mathns[0].operation = "LESS_THAN"
    mathns[0].inputs[1].default_value = "b"
    mathns[0].input_type_b = "FLOAT"
    mathns[0].inputs[4].default_value = 0.003131
    mathns[0].inputs[7].default_value = "c1"

    mathns[1].operation = "SUBTRACT"
    mathns[1].input_type_a = "FLOAT"
    mathns[1].inputs[2].default_value = 1
    mathns[1].inputs[3].default_value = "c1"
    mathns[1].inputs[7].default_value = "c2"

    mathns[2].operation = "MULTIPLY"
    mathns[2].input_type_b = "FLOAT"
    mathns[2].inputs[1].default_value = "b"
    mathns[2].inputs[4].default_value = 12.92
    mathns[2].inputs[7].default_value = "r1"

    mathns[3].operation = "MULTIPLY"
    mathns[3].inputs[1].default_value = "r1"
    mathns[3].inputs[3].default_value = "c1"
    mathns[3].inputs[7].default_value = "r1"

    mathns[4].operation = "POWER"
    mathns[4].input_type_b = "FLOAT"
    mathns[4].inputs[1].default_value = "b"
    mathns[4].inputs[4].default_value = 0.416667
    mathns[4].inputs[7].default_value = "r2"

    mathns[5].operation = "MULTIPLY"
    mathns[5].input_type_b = "FLOAT"
    mathns[5].inputs[1].default_value = "r2"
    mathns[5].inputs[4].default_value = 1.055
    mathns[5].inputs[7].default_value = "r2"

    mathns[6].operation = "SUBTRACT"
    mathns[6].input_type_b = "FLOAT"
    mathns[6].inputs[1].default_value = "r2"
    mathns[6].inputs[4].default_value = 0.055
    mathns[6].inputs[7].default_value = "r2"

    mathns[7].operation = "MULTIPLY"
    mathns[7].inputs[1].default_value = "r2"
    mathns[7].inputs[3].default_value = "c2"
    mathns[7].inputs[7].default_value = "r2"

    mathns[8].operation = "ADD"
    mathns[8].inputs[1].default_value = "r1"
    mathns[8].inputs[3].default_value = "r2"
    mathns[8].inputs[7].default_value = "r3"

    comxyz.input_type_x = "ATTRIBUTE"
    comxyz.inputs[1].default_value = "r3"
    comxyz.inputs[7].default_value = "TintUV"

    if USE_LEGACY:
        tsample.inputs[1].default_value = "TintUV"
        tsample.inputs[2].default_value = "TintColor"
    else:
        tsample.inputs[2].default_value = "TintUV"
        tsample.inputs[3].default_value = "TintColor"

    return gnt


def create_image_node(node_tree, param):
    imgnode = node_tree.nodes.new("ShaderNodeTexImage")
    imgnode.name = param.name
    imgnode.is_sollumz = True
    return imgnode


def create_vector_nodes(node_tree, param):
    for attr in vars(param).values():
        if attr.name != 'name' and attr.name != 'type':
            node = node_tree.nodes.new("ShaderNodeValue")
            node.name = f"{param.name}_{attr.name}"
            node.is_sollumz = True
            node.outputs[0].default_value = float(attr.value)


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
    for i in range(9):
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


def link_specular(node_tree, spctex):
    bsdf = node_tree.nodes["Principled BSDF"]
    links = node_tree.links
    links.new(spctex.outputs["Color"], bsdf.inputs["Specular"])


def create_pixel_tint_nodes(node_tree, tex, tinttex, tintflags):
    tinttex.interpolation = "Closest"
    bsdf = node_tree.nodes["Principled BSDF"]
    links = node_tree.links
    mathns = []
    locx = 0
    locy = 50
    for i in range(6):
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


def create_tint_nodes(node_tree, tinttex, txt, tintflags):
    if tintflags == 2:
        create_pixel_tint_nodes(node_tree, txt, tinttex, tintflags)
        return
    # create shader attribute node and gamma node
    bsdf = node_tree.nodes["Principled BSDF"]
    links = node_tree.links
    attr = node_tree.nodes.new("ShaderNodeAttribute")
    attr.attribute_name = "TintColor"
    gamma = node_tree.nodes.new("ShaderNodeGamma")
    gamma.inputs["Gamma"].default_value = 2.2
    links.new(attr.outputs["Color"], gamma.inputs["Color"])
    mix = node_tree.nodes.new("ShaderNodeMixRGB")
    mix.inputs["Fac"].default_value = 0.95
    links.new(gamma.outputs["Color"], mix.inputs[2])
    links.new(txt.outputs[0], mix.inputs[1])
    links.new(mix.outputs[0], bsdf.inputs["Base Color"])


def create_decal_nodes(node_tree, texture, decalflag):
    output = node_tree.nodes["Material Output"]
    bsdf = node_tree.nodes["Principled BSDF"]
    links = node_tree.links
    mix = node_tree.nodes.new("ShaderNodeMixShader")
    trans = node_tree.nodes.new("ShaderNodeBsdfTransparent")
    links.new(texture.outputs["Color"], bsdf.inputs["Base Color"])

    if decalflag == 0:
        links.new(texture.outputs["Alpha"], mix.inputs["Fac"])
    if decalflag == 1:
        vcs = node_tree.nodes.new("ShaderNodeVertexColor")
        vcs.layer_name = "colour0"  # set in create shader???
        multi = node_tree.nodes.new("ShaderNodeMath")
        multi.operation = "MULTIPLY"
        links.new(vcs.outputs["Alpha"], multi.inputs[0])
        links.new(texture.outputs["Alpha"], multi.inputs[1])
        links.new(multi.outputs["Value"], mix.inputs["Fac"])

    links.new(trans.outputs["BSDF"], mix.inputs[1])
    links.remove(bsdf.outputs["BSDF"].links[0])
    links.new(bsdf.outputs["BSDF"], mix.inputs[2])
    links.new(mix.outputs["Shader"], output.inputs["Surface"])


def create_emissive_nodes(node_tree):
    links = node_tree.links
    output = node_tree.nodes["Material Output"]
    tmpn = output.inputs[0].links[0].from_node
    if tmpn.name == "Principled BSDF":
        em = node_tree.nodes.new("ShaderNodeEmission")
        diff = node_tree.nodes["DiffuseSampler"]
        links.new(diff.outputs[0], em.inputs[0])
        links.new(em.outputs[0], output.inputs[0])


def link_value_shader_parameters(shader, node_tree):
    links = node_tree.links

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
        nm = try_get_node(node_tree, "Normal Map")
        if nm:
            links.new(bmp.outputs[0], nm.inputs[0])
    if spec_im:
        spec = try_get_node(node_tree, "SpecSampler")
        bsdf = try_get_node(node_tree, "Principled BSDF")
        if spec and bsdf:
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
        bsdf = try_get_node(node_tree, "Principled BSDF")
        if bsdf:
            map = node_tree.nodes.new("ShaderNodeMapRange")
            map.inputs[2].default_value = 512
            map.inputs[3].default_value = 1
            map.inputs[4].default_value = 0
            map.clamp = True
            links.new(spec_fm.outputs[0], map.inputs[0])
            links.new(map.outputs[0], bsdf.inputs["Roughness"])
    if em_m:
        em = try_get_node(node_tree, "Emission")
        if em:
            links.new(em_m.outputs[0], em.inputs[1])


def create_basic_shader_nodes(mat, shader, filename):

    node_tree = mat.node_tree

    texture = None
    texture2 = None
    tintpal = None
    bumptex = None
    spectex = None
    detltex = None
    isdistmap = False

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
                isdistmap = True
            elif param.name in ("DiffuseSampler2", "DiffuseExtraSampler"):
                texture2 = imgnode
            # elif param.name == "heightSampler" or "EnvironmentSampler":
                # continue
            # elif param.name == "FlowSampler" or "FogSampler" or "FoamSampler":
                # if not texture: texture = imgnode
            else:
                if not texture:
                    texture = imgnode

        elif param.type == "Vector":
            create_vector_nodes(node_tree, param)
        elif param.type == "Array":
            # IMPLEMENT
            pass
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
                # texture = link_diffuses(node_tree, texture, texture2)
                link_diffuses(node_tree, texture, texture2)
            else:
                link_diffuse(node_tree, texture)
    else:
        create_decal_nodes(node_tree, texture, decalflag)

    if use_bump:
        if use_detl:
            link_detailed_normal(node_tree, bumptex, detltex, spectex)
        else:
            link_normal(node_tree, bumptex)
    if use_spec:
        link_specular(node_tree, spectex)
    else:
        node_tree.nodes["Principled BSDF"].inputs["Specular"].default_value = 0
    if use_tint:
        create_tint_nodes(node_tree, tintpal, texture, tintflag)

    if is_emissive:
        create_emissive_nodes(node_tree)

    # link value parameters
    link_value_shader_parameters(shader, node_tree)

    mat.blend_method = blend_mode


def create_terrain_shader(mat, shader, filename):
    node_tree = mat.node_tree
    bsdf = node_tree.nodes["Principled BSDF"]
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
            # IMPLEMENT
            pass
        else:
            raise Exception(
                f"Unknown shader parameter! {param.type} {param.name}")

    mixns = []
    for i in range(8 if tm else 7):
        mix = node_tree.nodes.new("ShaderNodeMixRGB")
        mixns.append(mix)

    # attr_t0 = node_tree.nodes.new("ShaderNodeAttribute")
    # attr_t0.attribute_name = "texcoord0"
    # links.new(attr_t0.outputs[1], ts1.inputs[0])
    # links.new(attr_t0.outputs[1], ts2.inputs[0])
    # links.new(attr_t0.outputs[1], ts3.inputs[0])
    # links.new(attr_t0.outputs[1], ts4.inputs[0])

    seprgb = node_tree.nodes.new("ShaderNodeSeparateRGB")
    if filename in ShaderManager.mask_only_terrains:
        links.new(tm.outputs[0], seprgb.inputs[0])
    else:
        attr_c1 = node_tree.nodes.new("ShaderNodeAttribute")
        attr_c1.attribute_name = "colour1"
        links.new(attr_c1.outputs[0], mixns[0].inputs[1])
        links.new(attr_c1.outputs[0], mixns[0].inputs[2])

        attr_c0 = node_tree.nodes.new("ShaderNodeAttribute")
        attr_c0.attribute_name = "colour0"
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

    # link normals
    # links.new(attr_t0.outputs[1], bs1.inputs[0])
    # links.new(attr_t0.outputs[1], bs1.inputs[0])
    # links.new(attr_t0.outputs[1], bs1.inputs[0])
    # links.new(attr_t0.outputs[1], bs1.inputs[0])

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
        attr_t1.attribute_name = "texcoord1"
        links.new(attr_t1.outputs[1], tm.inputs[0])
        links.new(tm.outputs[0], mixns[0].inputs[1])

    # link value parameters
    bsdf.inputs["Specular"].default_value = 0
    link_value_shader_parameters(shader, node_tree)


def create_shader(name, filename=None):
    if not name in ShaderManager.shaders:
        raise AttributeError(f"Shader '{name}' does not exist!")

    shader = ShaderManager.shaders[name]
    filename = filename if filename else shader.filenames[0].value

    mat = bpy.data.materials.new(name)
    mat.sollum_type = MaterialType.SHADER
    mat.use_nodes = True
    mat.shader_properties.name = shader.name
    mat.shader_properties.filename = filename
    mat.shader_properties.renderbucket = shader.render_buckets[0]

    if filename in ShaderManager.terrains:
        create_terrain_shader(mat, shader, filename)
    else:
        create_basic_shader_nodes(mat, shader, filename)

    organize_node_tree(mat.node_tree)

    return mat
