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
from .render_bucket import RenderBucket
from ..shared.shader_expr.builtins import (
    vec,
    bsdf_principled,
    uv,
    tex,
    map_range,
    param,
    float_param,
    mix_color,
    emission,
    mix_shader,
    color_attribute,
    normal_map
)
from ..shared.shader_expr import expr, compile_to_material


class LegacyShaderConfig(NamedTuple):
    shader: ShaderDef
    is_distance_map: bool
    diffuse: str
    diffuse2: str
    tintpal: str
    diffpal: str
    bumptex: str
    spectex: str
    detltex: str
    decalflag: int
    blend_mode: str

    @property
    def use_uv_anim(self) -> bool:
        return self.shader.is_uv_animation_supported

    @property
    def use_diff(self) -> bool:
        return True if self.diffuse else False

    @property
    def use_diff2(self) -> bool:
        return True if self.diffuse2 else False

    @property
    def use_bump(self) -> bool:
        return True if self.bumptex else False

    @property
    def use_spec(self) -> bool:
        return True if self.spectex else False

    @property
    def use_detl(self) -> bool:
        return True if self.detltex else False

    @property
    def use_tint(self) -> bool:
        return True if self.tintpal else False

    @property
    def use_palette(self) -> bool:
        # Some shaders have TextureSamplerDiffPal but don't actually use it, so we only create palette
        # shader nodes on the specific shaders that use it
        return self.diffpal and self.shader.filename in ShaderManager.palette_shaders

    @property
    def use_decal(self) -> bool:
        return self.shader.filename in ShaderManager.tinted_shaders()

    @property
    def is_emissive(self) -> bool:
        return self.shader.filename in ShaderManager.em_shaders

    @property
    def is_veh_shader(self) -> bool:
        return self.shader.filename in ShaderManager.veh_paints


def get_shader_config(shader: ShaderDef) -> LegacyShaderConfig:
    # TODO: clean up this, some stuff can probably be moved to shaders.xml
    diffuse = None
    diffuse2 = None
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
            diffuse = p.name
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
            diffuse2 = p.name
        else:
            if not texture:
                texture = p.name

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

    if is_distance_map:
        blend_mode = "BLEND"

    return LegacyShaderConfig(
        shader=shader,
        is_distance_map=is_distance_map,
        diffuse=diffuse,
        diffuse2=diffuse2,
        tintpal=tintpal,
        diffpal=diffpal,
        bumptex=bumptex,
        spectex=spectex,
        detltex=detltex,
        blend_mode=blend_mode,
        decalflag=decalflag,
    )


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
    def _float_param_or_default(name: str, default_value: expr.Floaty) -> expr.Floaty:
        if name in shader.parameter_map:
            return float_param(name)
        else:
            return default_value

    cfg = get_shader_config(shader)

    base_color = vec(1.0, 1.0, 1.0)
    alpha = 1.0
    spec = 0.0
    roughness = 0.5
    normal = None
    metallic = None
    coat_weight = None

    if cfg.use_diff:
        diffuse_uv_map_index = shader.uv_maps.get(cfg.diffuse, 0)
        diffuse_uv = uv(diffuse_uv_map_index)
        if cfg.use_uv_anim:
            diffuse_uv = apply_global_anim_uv(diffuse_uv)
    else:
        diffuse_uv_map_index = None
        diffuse_uv = None

    if cfg.use_spec:
        spec_uv_map_index = shader.uv_maps.get(cfg.spectex, 0)
        spec_uv = diffuse_uv if diffuse_uv_map_index == spec_uv_map_index else uv(spec_uv_map_index)
        spec = tex(cfg.spectex, spec_uv).color
        spec = spec.x  # TODO: original takes the average of R,G,B channels, why?

    if "specularIntensityMult" in shader.parameter_map:
        specular_intensity_mult = float_param("specularIntensityMult")
        spec *= map_range(specular_intensity_mult, 0.0, 1.0, 0.0, 1.0, clamp=True)

    if "specularFalloffMult" in shader.parameter_map:
        specular_falloff_mult = float_param("specularFalloffMult")
        roughness = map_range(specular_falloff_mult, 0.0, 512.0, 1.0, 0.0, clamp=True)

    if cfg.use_bump:
        normal_uv_map_index = shader.uv_maps.get(cfg.spectex, 0)
        normal_uv = diffuse_uv if diffuse_uv_map_index == normal_uv_map_index else uv(normal_uv_map_index)
        normal = tex(cfg.bumptex, normal_uv).color

        # invert green channel of normal map
        normal = vec(normal.x, 1.0 - normal.y, normal.z)

        bumpiness = _float_param_or_default("bumpiness", 1.0)

        normal = normal_map(normal, bumpiness, normal_uv_map_index)

    if cfg.use_diff:
        diffuse = tex(cfg.diffuse, diffuse_uv)
        base_color = diffuse.color
        alpha = diffuse.alpha

    if cfg.use_diff2:
        diffuse2_uv_map_index = shader.uv_maps.get(cfg.diffuse2, 0)
        diffuse2_uv = diffuse_uv if diffuse_uv_map_index == diffuse2_uv_map_index else uv(diffuse2_uv_map_index)
        diffuse2 = tex(cfg.diffuse2, diffuse2_uv)

        base_color = mix_color(base_color, diffuse2.color, diffuse2.alpha)

    em_shader = None
    if cfg.is_emissive:
        em_strength = _float_param_or_default("emissiveMultiplier", 1.0)
        em_shader = emission(base_color, em_strength)

    if cfg.is_veh_shader:
        metallic = 1.0
        coat_weight = 1.0

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


def terrain_shader(shader: ShaderDef) -> expr.ShaderExpr:
    def _float_param_or_default(name: str, default_value: expr.Floaty) -> expr.Floaty:
        if name in shader.parameter_map:
            return float_param(name)
        else:
            return default_value

    tex_names = ("TextureSampler_layer0", "TextureSampler_layer1", "TextureSampler_layer2", "TextureSampler_layer3")
    bump_names = ("BumpSampler_layer0", "BumpSampler_layer1", "BumpSampler_layer2", "BumpSampler_layer3")
    lookup_name = "lookupSampler"

    tex_uvs = [uv(shader.uv_maps.get(n, 0)) for n in tex_names]
    bump_uvs = [uv(shader.uv_maps.get(n, 0)) for n in bump_names]
    tex0, tex1, tex2, tex3 = [tex(n, tex_uvs[i]) for i, n in enumerate(tex_names)]
    bump0, bump1, bump2, bump3 = [tex(n, bump_uvs[i]) for i, n in enumerate(bump_names)]

    lookup_uv = uv(shader.uv_maps.get(lookup_name, 0))
    lookup_tex = tex(lookup_name, lookup_uv)

    if shader.filename in ShaderManager.mask_only_terrains:
        lookup = lookup_tex.color
    else:
        attr_c0 = color_attribute("Color 1")
        attr_c1 = color_attribute("Color 2")

        if lookup_name in shader.parameter_map:
            lookup = mix_color(lookup_tex.color, attr_c1.color, attr_c0.alpha)
        else:
            lookup = attr_c1.color

    color01 = mix_color(tex0.color, tex1.color, lookup.b)
    color23 = mix_color(tex2.color, tex3.color, lookup.b)
    color = mix_color(color01, color23, lookup.g)

    normal = None
    if bump0.texture_name in shader.parameter_map:
        bumpiness = _float_param_or_default("bumpiness", 1.0)

        normal0 = normal_map(bump0.color, bumpiness, bump_uvs[0].uv_map_index)
        normal1 = normal_map(bump1.color, bumpiness, bump_uvs[1].uv_map_index)
        normal2 = normal_map(bump2.color, bumpiness, bump_uvs[2].uv_map_index)
        normal3 = normal_map(bump3.color, bumpiness, bump_uvs[3].uv_map_index)

        normal01 = mix_color(normal0, normal1, lookup.b)
        normal23 = mix_color(normal2, normal3, lookup.b)
        normal = mix_color(normal01, normal23, lookup.g)

        # TODO: original doesn't invert the normal in terrain shaders? why? bug?
        normal = vec(normal.x, 1.0 - normal.y, normal.z)  # invert green channel of normal map

    spec = 0.0
    if "specularIntensityMult" in shader.parameter_map:
        specular_intensity_mult = float_param("specularIntensityMult")
        specular_intensity_mult = map_range(specular_intensity_mult, 0.0, 1.0, 0.0, 1.0, clamp=True)
        spec = specular_intensity_mult * specular_intensity_mult

    roughness = None
    if "specularFalloffMult" in shader.parameter_map:
        specular_falloff_mult = float_param("specularFalloffMult")
        roughness = map_range(specular_falloff_mult, 0.0, 512.0, 1.0, 0.0, clamp=True)

    return bsdf_principled(
        base_color=color,
        normal=normal,
        specular_ior_level=spec,
        roughness=roughness,
    )


def get_shader_expr(shader: ShaderDef) -> expr.ShaderExpr:
    if shader.filename in ShaderManager.terrains:
        return terrain_shader(shader)
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
    mat.blend_method = get_shader_config(shader).blend_mode  # TODO: don't recompute ShaderConfig
    mat.sollum_type = MaterialType.SHADER
    mat.shader_properties.name = base_name
    mat.shader_properties.filename = filename
    mat.shader_properties.renderbucket = RenderBucket(shader.render_bucket).name

    organize_node_tree(mat.node_tree)

    return mat
