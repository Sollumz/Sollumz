import bpy
from enum import Enum
from Sollumz.sollumz_properties import MaterialType

class ShaderMaterial(str, Enum):
    DEFAULT = "default"
    VEHICLE_MESH = "vehicle_mesh"
    NORMAL_SPEC = "normal_spec"
    TREES_LOD = "trees_lod"
    TREES_LOD2 = "trees_lod2"
    SPEC = "spec"
    DECAL = "decal"
    PED_DEFAULT = "ped_default"
    NORMAL = "normal"
    VEHICLE_TIRE = "vehicle_tire"
    VEHICLE_PAINT4 = "vehicle_paint4"
    NORMAL_SPEC_DETAIL = "normal_spec_detail"
    PED = "ped"
    VEHICLE_PAINT1 = "vehicle_paint1"
    NORMAL_SPEC_DECAL = "normal_spec_decal"
    VEHICLE_MESH2_ENVEFF = "vehicle_mesh2_enveff"
    NORMAL_DECAL = "normal_decal"
    DEFAULT_SPEC = "default_spec"
    EMISSIVE = "emissive"
    VEHICLE_INTERIOR2 = "vehicle_interior2"
    TERRAIN_CB_W_4LYR_2TEX_BLEND_PXM_SPM = "terrain_cb_w_4lyr_2tex_blend_pxm_spm"
    TERRAIN_CB_W_4LYR_2TEX_BLEND_LOD = "terrain_cb_w_4lyr_2tex_blend_lod"
    VEHICLE_DETAIL2 = "vehicle_detail2"
    VEHICLE_SHUTS = "vehicle_shuts"
    VEHICLE_PAINT3 = "vehicle_paint3"
    VEHICLE_BADGES = "vehicle_badges"
    DEFAULT_TNT = "default_tnt"
    VEHICLE_LIGHTSEMISSIVE = "vehicle_lightsemissive"
    CABLE = "cable"
    VEHICLE_VEHGLASS = "vehicle_vehglass"
    PED_HAIR_SPIKED = "ped_hair_spiked"
    NORMAL_SPEC_TNT = "normal_spec_tnt"
    NORMAL_DECAL_PXM = "normal_decal_pxm"
    TERRAIN_CB_W_4LYR_2TEX_BLEND = "terrain_cb_w_4lyr_2tex_blend"
    DEFAULT_TERRAIN_WET = "default_terrain_wet"
    VEHICLE_VEHGLASS_INNER = "vehicle_vehglass_inner"
    VEHICLE_LICENSEPLATE = "vehicle_licenseplate"
    GLASS_ENV = "glass_env"
    NORMAL_SPEC_DECAL_PXM = "normal_spec_decal_pxm"
    TERRAIN_CB_W_4LYR_LOD = "terrain_cb_w_4lyr_lod"
    NORMAL_DETAIL = "normal_detail"
    VEHICLE_DASH_EMISSIVE = "vehicle_dash_emissive"
    VEHICLE_EMISSIVE_OPAQUE = "vehicle_emissive_opaque"
    DECAL_TNT = "decal_tnt"
    EMISSIVENIGHT = "emissivenight"
    VEHICLE_DASH_EMISSIVE_OPAQUE = "vehicle_dash_emissive_opaque"
    VEHICLE_DECAL = "vehicle_decal"
    EMISSIVE_ADDITIVE_UV_ALPHA = "emissive_additive_uv_alpha"
    CLOTH_NORMAL_SPEC = "cloth_normal_spec"
    NORMAL_SPEC_REFLECT = "normal_spec_reflect"
    NORMAL_SPEC_PXM = "normal_spec_pxm"
    CLOTH_DEFAULT = "cloth_default"
    PED_ALPHA = "ped_alpha"
    TREES_NORMAL_SPEC = "trees_normal_spec"
    SPEC_TNT = "spec_tnt"
    EMISSIVE_SPECLUM = "emissive_speclum"
    VEHICLE_PAINT2 = "vehicle_paint2"
    NORMAL_SPEC_DETAIL_TNT = "normal_spec_detail_tnt"
    DEFAULT_DETAIL = "default_detail"
    VEHICLE_PAINT8 = "vehicle_paint8"
    TERRAIN_CB_W_4LYR_PXM = "terrain_cb_w_4lyr_pxm"
    DECAL_NORMAL_ONLY = "decal_normal_only"
    CUTOUT_FENCE = "cutout_fence"
    TERRAIN_CB_W_4LYR_PXM_SPM = "terrain_cb_w_4lyr_pxm_spm"
    GRASS_FUR_MASK = "grass_fur_mask"
    NORMAL_TNT = "normal_tnt"
    TERRAIN_CB_W_4LYR_SPEC_PXM = "terrain_cb_w_4lyr_spec_pxm"
    PTFX_MODEL = "ptfx_model"
    GRASS_FUR = "grass_fur"
    VEHICLE_INTERIOR = "vehicle_interior"
    SPEC_DECAL = "spec_decal"
    VEHICLE_PAINT6_ENVEFF = "vehicle_paint6_enveff"
    PED_HAIR_CUTOUT_ALPHA = "ped_hair_cutout_alpha"
    DECAL_DIRT = "decal_dirt"
    DECAL_EMISSIVE_ONLY = "decal_emissive_only"
    TERRAIN_CB_W_4LYR_2TEX_BLEND_PXM = "terrain_cb_w_4lyr_2tex_blend_pxm"
    WEAPON_NORMAL_SPEC_DETAIL_PALETTE = "weapon_normal_spec_detail_palette"
    CLOTH_SPEC_ALPHA = "cloth_spec_alpha"
    EMISSIVESTRONG = "emissivestrong"
    VEHICLE_TRACK2 = "vehicle_track2"
    PED_WRINKLE = "ped_wrinkle"
    VEHICLE_DETAIL = "vehicle_detail"
    SPEC_REFLECT = "spec_reflect"
    VEHICLE_CUTOUT = "vehicle_cutout"
    VEHICLE_PAINT4_ENVEFF = "vehicle_paint4_enveff"
    DECAL_GLUE = "decal_glue"
    NORMAL_SPEC_DECAL_TNT = "normal_spec_decal_tnt"
    EMISSIVE_TNT = "emissive_tnt"
    VEHICLE_PAINT9 = "vehicle_paint9"
    PED_NOPEDDAMAGEDECALS = "ped_nopeddamagedecals"
    TERRAIN_CB_W_4LYR = "terrain_cb_w_4lyr"
    GLASS_PV_ENV = "glass_pv_env"
    NORMAL_DECAL_TNT = "normal_decal_tnt"
    CPV_ONLY = "cpv_only"
    PED_DECAL = "ped_decal"
    EMISSIVE_CLIP = "emissive_clip"
    DEFAULT_UM = "default_um"
    MINIMAP = "minimap"
    GLASS_NORMAL_SPEC_REFLECT = "glass_normal_spec_reflect"
    DISTANCE_MAP = "distance_map"
    VEHICLE_BLURREDROTOR = "vehicle_blurredrotor"
    GLASS = "glass"
    CUTOUT_FENCE_NORMAL = "cutout_fence_normal"
    PED_EMISSIVE = "ped_emissive"
    NORMAL_TERRAIN_WET = "normal_terrain_wet"
    NORMAL_SPEC_DECAL_DETAIL = "normal_spec_decal_detail"
    VEHICLE_CLOTH = "vehicle_cloth"
    NORMAL_UM_TNT = "normal_um_tnt"
    VEHICLE_BASIC = "vehicle_basic"
    TREES = "trees"
    EMISSIVE_ADDITIVE_ALPHA = "emissive_additive_alpha"
    GLASS_BREAKABLE = "glass_breakable"
    TREES_NORMAL_DIFFSPEC = "trees_normal_diffspec"
    VEHICLE_TRACK = "vehicle_track"
    PED_ENVEFF = "ped_enveff"
    WATER_TERRAINFOAM = "water_terrainfoam"
    VEHICLE_GENERIC = "vehicle_generic"
    VEHICLE_TRACK_AMMO = "vehicle_track_ammo"
    PED_DEFAULT_MP = "ped_default_mp"
    GRASS = "grass"
    VEHICLE_TRACK_EMISSIVE = "vehicle_track_emissive"
    GLASS_SPEC = "glass_spec"
    VEHICLE_PAINT5_ENVEFF = "vehicle_paint5_enveff"
    PED_WRINKLE_ENVEFF = "ped_wrinkle_enveff"
    WEAPON_NORMAL_SPEC_DETAIL_TNT = "weapon_normal_spec_detail_tnt"
    GLASS_PV = "glass_pv"
    TERRAIN_CB_W_4LYR_SPEC_INT_PXM = "terrain_cb_w_4lyr_spec_int_pxm"
    GLASS_EMISSIVE = "glass_emissive"
    WEAPON_NORMAL_SPEC_ALPHA = "weapon_normal_spec_alpha"
    NORMAL_PXM = "normal_pxm"
    WATER_FOUNTAIN = "water_fountain"
    REFLECT = "reflect"
    NORMAL_REFLECT = "normal_reflect"
    TERRAIN_CB_W_4LYR_SPEC_INT = "terrain_cb_w_4lyr_spec_int"
    PED_WRINKLE_CS = "ped_wrinkle_cs"
    GRASS_BATCH = "grass_batch"
    EMISSIVENIGHT_GEOMNIGHTONLY = "emissivenight_geomnightonly"
    PED_DECAL_DECORATION = "ped_decal_decoration"
    VEHICLE_PAINT6 = "vehicle_paint6"
    WATER_RIVERLOD = "water_riverlod"
    NORMAL_UM = "normal_um"
    VEHICLE_DECAL2 = "vehicle_decal2"
    WEAPON_EMISSIVESTRONG_ALPHA = "weapon_emissivestrong_alpha"
    WATER_SHALLOW = "water_shallow"
    VEHICLE_PAINT1_ENVEFF = "vehicle_paint1_enveff"
    TERRAIN_CB_W_4LYR_2TEX = "terrain_cb_w_4lyr_2tex"
    TREES_SHADOW_PROXY = "trees_shadow_proxy"
    VEHICLE_MESH_ENVEFF = "vehicle_mesh_enveff"
    PED_DEFAULT_ENVEFF = "ped_default_enveff"
    WATER_RIVERFOAM = "water_riverfoam"
    ALBEDO_ALPHA = "albedo_alpha"
    DECAL_SHADOW_ONLY = "decal_shadow_only"
    RADAR = "radar"
    TREES_TNT = "trees_tnt"
    WEAPON_NORMAL_SPEC_PALETTE = "weapon_normal_spec_palette"
    TREES_NORMAL = "trees_normal"
    DECAL_SPEC_ONLY = "decal_spec_only"
    MIRROR_DEFAULT = "mirror_default"
    PED_PALETTE = "ped_palette"
    NORMAL_SPEC_DECAL_NOPUDDLE = "normal_spec_decal_nopuddle"
    NORMAL_SPEC_EMISSIVE = "normal_spec_emissive"
    NORMAL_SPEC_UM = "normal_spec_um"
    DECAL_EMISSIVENIGHT_ONLY = "decal_emissivenight_only"
    PED_DEFAULT_PALETTE = "ped_default_palette"
    WATER_RIVER = "water_river"
    WEAPON_NORMAL_SPEC_TNT = "weapon_normal_spec_tnt"
    CUTOUT_HARD = "cutout_hard"
    NORMAL_SPEC_PXM_TNT = "normal_spec_pxm_tnt"
    TERRAIN_CB_W_4LYR_CM_TNT = "terrain_cb_w_4lyr_cm_tnt"
    VEHICLE_EMISSIVE_ALPHA = "vehicle_emissive_alpha"
    MIRROR_DECAL = "mirror_decal"
    VEHICLE_TRACK2_EMISSIVE = "vehicle_track2_emissive"
    PED_CLOTH = "ped_cloth"
    NORMAL_CUBEMAP_REFLECT = "normal_cubemap_reflect"
    NORMAL_SPEC_CUBEMAP_REFLECT = "normal_spec_cubemap_reflect"
    GLASS_REFLECT = "glass_reflect"
    SPEC_TWIDDLE_TNT = "spec_twiddle_tnt"
    NORMAL_DIFFSPEC_DETAIL = "normal_diffspec_detail"
    WEAPON_NORMAL_SPEC_CUTOUT_PALETTE = "weapon_normal_spec_cutout_palette"
    TERRAIN_CB_W_4LYR_SPEC = "terrain_cb_w_4lyr_spec"
    PED_FUR = "ped_fur"
    CLOUDS_FAST = "clouds_fast"
    NORMAL_DIFFSPEC_DETAIL_DPM = "normal_diffspec_detail_dpm"
    VEHICLE_PAINT3_ENVEFF = "vehicle_paint3_enveff"
    TREES_NORMAL_SPEC_TNT = "trees_normal_spec_tnt"
    CLOUDS_ANIMSOFT = "clouds_animsoft"
    DECAL_AMB_ONLY = "decal_amb_only"
    NORMAL_DIFFSPEC_DETAIL_DPM_TNT = "normal_diffspec_detail_dpm_tnt"
    WATER_RIVEROCEAN = "water_riverocean"
    TERRAIN_CB_W_4LYR_CM_PXM = "terrain_cb_w_4lyr_cm_pxm"
    VEHICLE_PAINT2_ENVEFF = "vehicle_paint2_enveff"
    VEHICLE_BLURREDROTOR_EMISSIVE = "vehicle_blurredrotor_emissive"
    TERRAIN_CB_W_4LYR_CM_PXM_TNT = "terrain_cb_w_4lyr_cm_pxm_tnt"
    WATER_RIVERSHALLOW = "water_rivershallow"
    VEHICLE_PAINT7_ENVEFF = "vehicle_paint7_enveff"
    TERRAIN_CB_W_4LYR_2TEX_PXM = "terrain_cb_w_4lyr_2tex_pxm"
    PED_WRINKLE_CLOTH = "ped_wrinkle_cloth"
    NORMAL_SPEC_REFLECT_DECAL = "normal_spec_reflect_decal"
    PARALLAX_SPECMAP = "parallax_specmap"
    NORMAL_SPEC_DETAIL_DPM_TNT = "normal_spec_detail_dpm_tnt"
    PED_WRINKLE_CLOTH_ENVEFF = "ped_wrinkle_cloth_enveff"
    WATER_POOLENV = "water_poolenv"
    NORMAL_SPEC_REFLECT_EMISSIVENIGHT = "normal_spec_reflect_emissivenight"
    TREES_LOD_TNT = "trees_lod_tnt"
    DECAL_DIFF_ONLY_UM = "decal_diff_only_um"
    VEHICLE_PAINT7 = "vehicle_paint7"
    VEHICLE_PAINT4_EMISSIVE = "vehicle_paint4_emissive"
    NORMAL_PXM_TNT = "normal_pxm_tnt"
    BLEND_2LYR = "blend_2lyr"
    TREES_NORMAL_DIFFSPEC_TNT = "trees_normal_diffspec_tnt"
    PED_DEFAULT_CLOTH = "ped_default_cloth"
    MIRROR_CRACK = "mirror_crack"
    GLASS_DISPLACEMENT = "glass_displacement"
    NORMAL_SPEC_DETAIL_DPM_VERTDECAL_TNT = "normal_spec_detail_dpm_vertdecal_tnt"
    CLOTH_NORMAL_SPEC_TNT = "cloth_normal_spec_tnt"
    NORMAL_DIFFSPEC = "normal_diffspec"
    GLASS_EMISSIVENIGHT = "glass_emissivenight"
    NORMAL_DECAL_PXM_TNT = "normal_decal_pxm_tnt"
    NORMAL_SPEC_DPM = "normal_spec_dpm"
    WEAPON_EMISSIVE_TNT = "weapon_emissive_tnt"
    CLOUDS_ANIM = "clouds_anim"
    VEHICLE_PAINT3_LVR = "vehicle_paint3_lvr"
    NORMAL_SPEC_DETAIL_DPM = "normal_spec_detail_dpm"
    NORMAL_SPEC_BATCH = "normal_spec_batch"
    PED_DECAL_EXP = "ped_decal_exp"
    CLOUDS_ALTITUDE = "clouds_altitude"
    SPEC_REFLECT_DECAL = "spec_reflect_decal"
    TERRAIN_CB_W_4LYR_CM = "terrain_cb_w_4lyr_cm"
    PARALLAX = "parallax"
    NORMAL_DIFFSPEC_DETAIL_TNT = "normal_diffspec_detail_tnt"
    NORMAL_DETAIL_DPM = "normal_detail_dpm"
    VEHICLE_CLOTH2 = "vehicle_cloth2"
    NORMAL_DIFFSPEC_TNT = "normal_diffspec_tnt"
    REFLECT_DECAL = "reflect_decal"
    CLOUDS_SOFT = "clouds_soft"
    PED_DECAL_NODIFF = "ped_decal_nodiff"
    TERRAIN_CB_4LYR_2TEX = "terrain_cb_4lyr_2tex"
    NORMAL_SPEC_WRINKLE = "normal_spec_wrinkle"
    SKY_SYSTEM = "sky_system"
    CLOUDS_FOG = "clouds_fog"
    TERRAIN_CB_4LYR = "terrain_cb_4lyr"
    NORMAL_REFLECT_DECAL = "normal_reflect_decal"
    PED_CLOTH_ENVEFF = "ped_cloth_enveff"   

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