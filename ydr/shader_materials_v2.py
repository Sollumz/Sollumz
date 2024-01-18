from typing import Optional, NamedTuple
import bpy
from ..cwxml.shader import (
    ShaderManager,
    ShaderDef,
    ShaderParameterType,
    ShaderParameterSubtype,
    ShaderParameterFloatDef,
    ShaderParameterFloat2Def,
    ShaderParameterFloat3Def,
    ShaderParameterFloat4Def,
    ShaderParameterFloat4x4Def,
)
from ..sollumz_properties import MaterialType
from ..tools.meshhelper import get_uv_map_name
from ..shared.shader_nodes import SzShaderNodeParameter, SzShaderNodeParameterDisplayType
from .render_bucket import RenderBucket
from ..shared.shader_expr.builtins import vec, bsdf_principled, uv, tex, map_range, param, float_param, mix_color, emission, mix_shader
from ..shared.shader_expr import expr, compile_to_material


def flip_v(v: expr.FloatExpr) -> expr.FloatExpr:
    return ((v - 1) * -1)


def apply_global_anim_uv(uv: expr.VectorExpr) -> expr.VectorExpr:
    globalAnimUV0 = vec(1.0, 0.0, 0.0)  # TODO: drivers for animation
    globalAnimUV1 = vec(0.0, 1.0, 0.0)

    uvw = vec(uv.x, flip_v(uv.y), 1)
    new_u = uvw.dot(globalAnimUV0)
    new_v = uvw.dot(globalAnimUV1)
    return vec(new_u, flip_v(new_v), 0)


def basic_shader(
    shader: ShaderDef,
) -> expr.ShaderExpr:

    ### BEGIN CONFIG DETECTION ###
    # TODO: clean up this, some stuff can probably be moved to shaders.xml
    use_uv_anim = shader.is_uv_animation_supported

    texture = None
    texture2 = None
    tintpal = None
    diffpal = None
    bumptex = None
    spectex = None
    detltex = None
    is_distance_map = False

    for p in shader.parameters:
        if p.type != ShaderParameterType.TEXTURE:
            continue

        if p.name in ("DiffuseSampler", "PlateBgSampler"):
            texture = p.name
        elif p.name in ("BumpSampler", "PlateBgBumpSampler"):
            bumptex = p.name
        elif p.name == "SpecSampler":
            spectex = p.name
        elif p.name == "DetailSampler":
            detltex = p.name
        elif p.name == "TintPaletteSampler":
            tintpal = p.name
        elif p.name == "TextureSamplerDiffPal":
            diffpal = p.name
        elif p.name == "distanceMapSampler":
            texture = p.name
            is_distance_map = True
        elif p.name in ("DiffuseSampler2", "DiffuseExtraSampler"):
            texture2 = p.name
        else:
            if not texture:
                texture = p.name

    use_diff = True if texture else False
    use_diff2 = True if texture2 else False
    use_bump = True if bumptex else False
    use_spec = True if spectex else False
    use_detl = True if detltex else False
    use_tint = True if tintpal else False

    # Some shaders have TextureSamplerDiffPal but don't actually use it, so we only create palette
    # shader nodes on the specific shaders that use it
    use_palette = diffpal is not None and shader.filename in ShaderManager.palette_shaders

    use_decal = True if shader.filename in ShaderManager.tinted_shaders() else False
    decalflag = 0
    blend_mode = "OPAQUE"
    if use_decal:
        # set blend mode
        if shader.filename in ShaderManager.cutout_shaders():
            blend_mode = "CLIP"
        else:
            blend_mode = "BLEND"
            decalflag = 1
        # set flags
        if shader.filename in [ShaderManager.decals[20]]:  # decal_dirt.sps
            # txt_alpha_mask = ?
            decalflag = 2
        # decal_normal_only.sps / mirror_decal.sps / reflect_decal.sps
        elif shader.filename in [ShaderManager.decals[4], ShaderManager.decals[21], ShaderManager.decals[19]]:
            decalflag = 3
        # decal_spec_only.sps / spec_decal.sps
        elif shader.filename in [ShaderManager.decals[3], ShaderManager.decals[17]]:
            decalflag = 4

    is_emissive = True if shader.filename in ShaderManager.em_shaders else False

    ### END CONFIG DETECTION ###

    ### BEGIN SHADER ###

    base_color = vec(1.0, 1.0, 1.0)
    alpha = 1.0
    spec = 0.0
    roughness = 0.5
    normal = None
    metallic = None
    coat_weight = None

    if use_diff:
        diffuse_uv_map_index = shader.uv_maps.get(texture, 0)
        diffuse_uv = uv(diffuse_uv_map_index)
        if use_uv_anim:
            diffuse_uv = apply_global_anim_uv(diffuse_uv)
    else:
        diffuse_uv_map_index = None
        diffuse_uv = None

    if use_spec:
        spec_uv_map_index = shader.uv_maps.get(spectex, 0)
        spec_uv = diffuse_uv if diffuse_uv_map_index == spec_uv_map_index else uv(spec_uv_map_index)
        spec = tex(spectex, spec_uv).color
        spec = spec.x  # TODO: original takes the average of R,G,B channels, why?

    if "specularIntensityMult" in shader.parameter_map:
        specular_intensity_mult = float_param("specularIntensityMult")
        spec *= map_range(specular_intensity_mult, 0.0, 1.0, 0.0, 1.0, clamp=True)

    if "specularFalloffMult" in shader.parameter_map:
        specular_falloff_mult = float_param("specularFalloffMult")
        roughness = map_range(specular_falloff_mult, 0.0, 512.0, 1.0, 0.0, clamp=True)

    if use_bump:
        normal_uv_map_index = shader.uv_maps.get(spectex, 0)
        normal_uv = diffuse_uv if diffuse_uv_map_index == normal_uv_map_index else uv(normal_uv_map_index)
        normal = tex(bumptex, normal_uv).color

        # invert green channel of normal map
        normal = vec(normal.x, 1.0 - normal.y, normal.z)

        bumpiness = 1.0
        if "bumpiness" in shader.parameter_map:
            bumpiness = float_param("bumpiness")

        # normal = normal_map(normal, bumpiness)  # TODO: ShaderNodeNormalMap, the UV map name should probably be included now too

    if use_diff:
        diffuse = tex(texture, diffuse_uv)
        base_color = diffuse.color
        alpha = diffuse.alpha

    if use_diff2:
        diffuse2_uv_map_index = shader.uv_maps.get(texture2, 0)
        diffuse2_uv = diffuse_uv if diffuse_uv_map_index == diffuse2_uv_map_index else uv(diffuse2_uv_map_index)
        diffuse2 = tex(texture2, diffuse2_uv)

        base_color = mix_color(base_color, diffuse2.color, diffuse2.alpha)

    em_shader = None
    if is_emissive:
        em_strength = 1.0
        if "emissiveMultiplier" in shader.parameter_map:
            em_strength = float_param("emissiveMultiplier")
        em_shader = emission(base_color, em_strength)

    is_veh_shader = shader.filename in ShaderManager.veh_paints
    if is_veh_shader:
        metallic = 1.0
        coat_weight = 1.0

    ### END SHADER ###
    main_shader = bsdf_principled(
        base_color,
        alpha=alpha,
        roughness=roughness,
        specular_ior_level=spec,
        normal=normal,
        metallic=metallic,
        coat_weight=coat_weight,
    )

    if em_shader is not None:
        main_shader = mix_shader(em_shader, main_shader, 0.5)

    return main_shader


def get_shader_expr(shader: ShaderDef) -> expr.ShaderExpr:

    if shader.filename in ShaderManager.terrains:
        raise NotImplementedError("terrain shaders not implemented")
    else:
        return basic_shader(shader)


def organize_node_tree(node_tree: bpy.types.ShaderNodeTree):
    from .shader_materials import organize_node, organize_loose_nodes, group_image_texture_nodes, try_get_node_by_cls

    mo = try_get_node_by_cls(node_tree, bpy.types.ShaderNodeOutputMaterial)
    mo.location.x = 0
    mo.location.y = 0
    organize_node(mo)
    organize_loose_nodes(node_tree, 1000, 0)
    group_image_texture_nodes(node_tree)


def create_shader(filename: str):
    shader = ShaderManager.find_shader(filename)
    if shader is None:
        raise AttributeError(f"Shader '{filename}' does not exist!")

    filename = shader.filename  # in case `filename` was hashed initially
    base_name = ShaderManager.find_shader_base_name(filename)

    shader_expr = get_shader_expr(shader)
    mat = compile_to_material(filename.replace(".sps", ""), shader_expr, shader_def=shader)
    # TODO: set mat.blend_method
    mat.sollum_type = MaterialType.SHADER
    mat.shader_properties.name = base_name
    mat.shader_properties.filename = filename
    mat.shader_properties.renderbucket = RenderBucket(shader.render_bucket).name

    organize_node_tree(mat.node_tree)

    return mat
