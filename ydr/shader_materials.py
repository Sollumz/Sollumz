import bpy
from Sollumz.sollumz_properties import MaterialType
from collections import namedtuple
import os

ShaderMaterial = namedtuple("ShaderMaterial", "name, ui_name, value")

shadermats = [
    ShaderMaterial("DEFAULT", "DEFAULT", "default"),
    ShaderMaterial("VEHICLE_MESH", "VEHICLE MESH", "vehicle_mesh"),
    ShaderMaterial("NORMAL_SPEC", "NORMAL SPEC", "normal_spec"),
    ShaderMaterial("TREES_LOD", "TREES LOD", "trees_lod"),
    ShaderMaterial("TREES_LOD2", "TREES LOD2", "trees_lod2"),
    ShaderMaterial("SPEC", "SPEC", "spec"),
    ShaderMaterial("DECAL", "DECAL", "decal"),
    ShaderMaterial("PED_DEFAULT", "PED DEFAULT", "ped_default"),
    ShaderMaterial("NORMAL", "NORMAL", "normal"),
    ShaderMaterial("VEHICLE_TIRE", "VEHICLE TIRE", "vehicle_tire"),
    ShaderMaterial("VEHICLE_PAINT4", "VEHICLE PAINT4", "vehicle_paint4"),
    ShaderMaterial("NORMAL_SPEC_DETAIL", "NORMAL SPEC DETAIL",
                   "normal_spec_detail"),
    ShaderMaterial("PED", "PED", "ped"),
    ShaderMaterial("VEHICLE_PAINT1", "VEHICLE PAINT1", "vehicle_paint1"),
    ShaderMaterial("NORMAL_SPEC_DECAL", "NORMAL SPEC DECAL",
                   "normal_spec_decal"),
    ShaderMaterial("VEHICLE_MESH2_ENVEFF",
                   "VEHICLE MESH2 ENVEFF", "vehicle_mesh2_enveff"),
    ShaderMaterial("NORMAL_DECAL", "NORMAL DECAL", "normal_decal"),
    ShaderMaterial("DEFAULT_SPEC", "DEFAULT SPEC", "default_spec"),
    ShaderMaterial("EMISSIVE", "EMISSIVE", "emissive"),
    ShaderMaterial("VEHICLE_INTERIOR2", "VEHICLE INTERIOR2",
                   "vehicle_interior2"),
    ShaderMaterial("TERRAIN_CB_W_4LYR_2TEX_BLEND_PXM_SPM",
                   "TERRAIN CB W 4LYR 2TEX BLEND PXM SPM", "terrain_cb_w_4lyr_2tex_blend_pxm_spm"),
    ShaderMaterial("TERRAIN_CB_W_4LYR_2TEX_BLEND_LOD",
                   "TERRAIN CB W 4LYR 2TEX BLEND LOD", "terrain_cb_w_4lyr_2tex_blend_lod"),
    ShaderMaterial("VEHICLE_DETAIL2", "VEHICLE DETAIL2", "vehicle_detail2"),
    ShaderMaterial("VEHICLE_SHUTS", "VEHICLE SHUTS", "vehicle_shuts"),
    ShaderMaterial("VEHICLE_PAINT3", "VEHICLE PAINT3", "vehicle_paint3"),
    ShaderMaterial("VEHICLE_BADGES", "VEHICLE BADGES", "vehicle_badges"),
    ShaderMaterial("DEFAULT_TNT", "DEFAULT TNT", "default_tnt"),
    ShaderMaterial("VEHICLE_LIGHTSEMISSIVE",
                   "VEHICLE LIGHTSEMISSIVE", "vehicle_lightsemissive"),
    ShaderMaterial("CABLE", "CABLE", "cable"),
    ShaderMaterial("VEHICLE_VEHGLASS", "VEHICLE VEHGLASS", "vehicle_vehglass"),
    ShaderMaterial("PED_HAIR_SPIKED", "PED HAIR SPIKED", "ped_hair_spiked"),
    ShaderMaterial("NORMAL_SPEC_TNT", "NORMAL SPEC TNT", "normal_spec_tnt"),
    ShaderMaterial("NORMAL_DECAL_PXM", "NORMAL DECAL PXM", "normal_decal_pxm"),
    ShaderMaterial("TERRAIN_CB_W_4LYR_2TEX_BLEND",
                   "TERRAIN CB W 4LYR 2TEX BLEND", "terrain_cb_w_4lyr_2tex_blend"),
    ShaderMaterial("DEFAULT_TERRAIN_WET", "DEFAULT TERRAIN WET",
                   "default_terrain_wet"),
    ShaderMaterial("VEHICLE_VEHGLASS_INNER",
                   "VEHICLE VEHGLASS INNER", "vehicle_vehglass_inner"),
    ShaderMaterial("VEHICLE_LICENSEPLATE",
                   "VEHICLE LICENSEPLATE", "vehicle_licenseplate"),
    ShaderMaterial("GLASS_ENV", "GLASS ENV", "glass_env"),
    ShaderMaterial("NORMAL_SPEC_DECAL_PXM",
                   "NORMAL SPEC DECAL PXM", "normal_spec_decal_pxm"),
    ShaderMaterial("TERRAIN_CB_W_4LYR_LOD",
                   "TERRAIN CB W 4LYR LOD", "terrain_cb_w_4lyr_lod"),
    ShaderMaterial("NORMAL_DETAIL", "NORMAL DETAIL", "normal_detail"),
    ShaderMaterial("VEHICLE_DASH_EMISSIVE",
                   "VEHICLE DASH EMISSIVE", "vehicle_dash_emissive"),
    ShaderMaterial("VEHICLE_EMISSIVE_OPAQUE",
                   "VEHICLE EMISSIVE OPAQUE", "vehicle_emissive_opaque"),
    ShaderMaterial("DECAL_TNT", "DECAL TNT", "decal_tnt"),
    ShaderMaterial("EMISSIVENIGHT", "EMISSIVENIGHT", "emissivenight"),
    ShaderMaterial("VEHICLE_DASH_EMISSIVE_OPAQUE",
                   "VEHICLE DASH EMISSIVE OPAQUE", "vehicle_dash_emissive_opaque"),
    ShaderMaterial("VEHICLE_DECAL", "VEHICLE DECAL", "vehicle_decal"),
    ShaderMaterial("EMISSIVE_ADDITIVE_UV_ALPHA",
                   "EMISSIVE ADDITIVE UV ALPHA", "emissive_additive_uv_alpha"),
    ShaderMaterial("CLOTH_NORMAL_SPEC", "CLOTH NORMAL SPEC",
                   "cloth_normal_spec"),
    ShaderMaterial("NORMAL_SPEC_REFLECT", "NORMAL SPEC REFLECT",
                   "normal_spec_reflect"),
    ShaderMaterial("NORMAL_SPEC_PXM", "NORMAL SPEC PXM", "normal_spec_pxm"),
    ShaderMaterial("CLOTH_DEFAULT", "CLOTH DEFAULT", "cloth_default"),
    ShaderMaterial("PED_ALPHA", "PED ALPHA", "ped_alpha"),
    ShaderMaterial("TREES_NORMAL_SPEC", "TREES NORMAL SPEC",
                   "trees_normal_spec"),
    ShaderMaterial("SPEC_TNT", "SPEC TNT", "spec_tnt"),
    ShaderMaterial("EMISSIVE_SPECLUM", "EMISSIVE SPECLUM", "emissive_speclum"),
    ShaderMaterial("VEHICLE_PAINT2", "VEHICLE PAINT2", "vehicle_paint2"),
    ShaderMaterial("NORMAL_SPEC_DETAIL_TNT",
                   "NORMAL SPEC DETAIL TNT", "normal_spec_detail_tnt"),
    ShaderMaterial("DEFAULT_DETAIL", "DEFAULT DETAIL", "default_detail"),
    ShaderMaterial("VEHICLE_PAINT8", "VEHICLE PAINT8", "vehicle_paint8"),
    ShaderMaterial("TERRAIN_CB_W_4LYR_PXM",
                   "TERRAIN CB W 4LYR PXM", "terrain_cb_w_4lyr_pxm"),
    ShaderMaterial("DECAL_NORMAL_ONLY", "DECAL NORMAL ONLY",
                   "decal_normal_only"),
    ShaderMaterial("CUTOUT_FENCE", "CUTOUT FENCE", "cutout_fence"),
    ShaderMaterial("TERRAIN_CB_W_4LYR_PXM_SPM",
                   "TERRAIN CB W 4LYR PXM SPM", "terrain_cb_w_4lyr_pxm_spm"),
    ShaderMaterial("GRASS_FUR_MASK", "GRASS FUR MASK", "grass_fur_mask"),
    ShaderMaterial("NORMAL_TNT", "NORMAL TNT", "normal_tnt"),
    ShaderMaterial("TERRAIN_CB_W_4LYR_SPEC_PXM",
                   "TERRAIN CB W 4LYR SPEC PXM", "terrain_cb_w_4lyr_spec_pxm"),
    ShaderMaterial("PTFX_MODEL", "PTFX MODEL", "ptfx_model"),
    ShaderMaterial("GRASS_FUR", "GRASS FUR", "grass_fur"),
    ShaderMaterial("VEHICLE_INTERIOR", "VEHICLE INTERIOR", "vehicle_interior"),
    ShaderMaterial("SPEC_DECAL", "SPEC DECAL", "spec_decal"),
    ShaderMaterial("VEHICLE_PAINT6_ENVEFF",
                   "VEHICLE PAINT6 ENVEFF", "vehicle_paint6_enveff"),
    ShaderMaterial("PED_HAIR_CUTOUT_ALPHA",
                   "PED HAIR CUTOUT ALPHA", "ped_hair_cutout_alpha"),
    ShaderMaterial("DECAL_DIRT", "DECAL DIRT", "decal_dirt"),
    ShaderMaterial("DECAL_EMISSIVE_ONLY", "DECAL EMISSIVE ONLY",
                   "decal_emissive_only"),
    ShaderMaterial("TERRAIN_CB_W_4LYR_2TEX_BLEND_PXM",
                   "TERRAIN CB W 4LYR 2TEX BLEND PXM", "terrain_cb_w_4lyr_2tex_blend_pxm"),
    ShaderMaterial("WEAPON_NORMAL_SPEC_DETAIL_PALETTE",
                   "WEAPON NORMAL SPEC DETAIL PALETTE", "weapon_normal_spec_detail_palette"),
    ShaderMaterial("CLOTH_SPEC_ALPHA", "CLOTH SPEC ALPHA", "cloth_spec_alpha"),
    ShaderMaterial("EMISSIVESTRONG", "EMISSIVESTRONG", "emissivestrong"),
    ShaderMaterial("VEHICLE_TRACK2", "VEHICLE TRACK2", "vehicle_track2"),
    ShaderMaterial("PED_WRINKLE", "PED WRINKLE", "ped_wrinkle"),
    ShaderMaterial("VEHICLE_DETAIL", "VEHICLE DETAIL", "vehicle_detail"),
    ShaderMaterial("SPEC_REFLECT", "SPEC REFLECT", "spec_reflect"),
    ShaderMaterial("VEHICLE_CUTOUT", "VEHICLE CUTOUT", "vehicle_cutout"),
    ShaderMaterial("VEHICLE_PAINT4_ENVEFF",
                   "VEHICLE PAINT4 ENVEFF", "vehicle_paint4_enveff"),
    ShaderMaterial("DECAL_GLUE", "DECAL GLUE", "decal_glue"),
    ShaderMaterial("NORMAL_SPEC_DECAL_TNT",
                   "NORMAL SPEC DECAL TNT", "normal_spec_decal_tnt"),
    ShaderMaterial("EMISSIVE_TNT", "EMISSIVE TNT", "emissive_tnt"),
    ShaderMaterial("VEHICLE_PAINT9", "VEHICLE PAINT9", "vehicle_paint9"),
    ShaderMaterial("PED_NOPEDDAMAGEDECALS",
                   "PED NOPEDDAMAGEDECALS", "ped_nopeddamagedecals"),
    ShaderMaterial("TERRAIN_CB_W_4LYR", "TERRAIN CB W 4LYR",
                   "terrain_cb_w_4lyr"),
    ShaderMaterial("GLASS_PV_ENV", "GLASS PV ENV", "glass_pv_env"),
    ShaderMaterial("NORMAL_DECAL_TNT", "NORMAL DECAL TNT", "normal_decal_tnt"),
    ShaderMaterial("CPV_ONLY", "CPV ONLY", "cpv_only"),
    ShaderMaterial("PED_DECAL", "PED DECAL", "ped_decal"),
    ShaderMaterial("EMISSIVE_CLIP", "EMISSIVE CLIP", "emissive_clip"),
    ShaderMaterial("DEFAULT_UM", "DEFAULT UM", "default_um"),
    ShaderMaterial("MINIMAP", "MINIMAP", "minimap"),
    ShaderMaterial("GLASS_NORMAL_SPEC_REFLECT",
                   "GLASS NORMAL SPEC REFLECT", "glass_normal_spec_reflect"),
    ShaderMaterial("DISTANCE_MAP", "DISTANCE MAP", "distance_map"),
    ShaderMaterial("VEHICLE_BLURREDROTOR",
                   "VEHICLE BLURREDROTOR", "vehicle_blurredrotor"),
    ShaderMaterial("GLASS", "GLASS", "glass"),
    ShaderMaterial("CUTOUT_FENCE_NORMAL", "CUTOUT FENCE NORMAL",
                   "cutout_fence_normal"),
    ShaderMaterial("PED_EMISSIVE", "PED EMISSIVE", "ped_emissive"),
    ShaderMaterial("NORMAL_TERRAIN_WET", "NORMAL TERRAIN WET",
                   "normal_terrain_wet"),
    ShaderMaterial("NORMAL_SPEC_DECAL_DETAIL",
                   "NORMAL SPEC DECAL DETAIL", "normal_spec_decal_detail"),
    ShaderMaterial("VEHICLE_CLOTH", "VEHICLE CLOTH", "vehicle_cloth"),
    ShaderMaterial("NORMAL_UM_TNT", "NORMAL UM TNT", "normal_um_tnt"),
    ShaderMaterial("VEHICLE_BASIC", "VEHICLE BASIC", "vehicle_basic"),
    ShaderMaterial("TREES", "TREES", "trees"),
    ShaderMaterial("EMISSIVE_ADDITIVE_ALPHA",
                   "EMISSIVE ADDITIVE ALPHA", "emissive_additive_alpha"),
    ShaderMaterial("GLASS_BREAKABLE", "GLASS BREAKABLE", "glass_breakable"),
    ShaderMaterial("TREES_NORMAL_DIFFSPEC",
                   "TREES NORMAL DIFFSPEC", "trees_normal_diffspec"),
    ShaderMaterial("VEHICLE_TRACK", "VEHICLE TRACK", "vehicle_track"),
    ShaderMaterial("PED_ENVEFF", "PED ENVEFF", "ped_enveff"),
    ShaderMaterial("WATER_TERRAINFOAM", "WATER TERRAINFOAM",
                   "water_terrainfoam"),
    ShaderMaterial("VEHICLE_GENERIC", "VEHICLE GENERIC", "vehicle_generic"),
    ShaderMaterial("VEHICLE_TRACK_AMMO", "VEHICLE TRACK AMMO",
                   "vehicle_track_ammo"),
    ShaderMaterial("PED_DEFAULT_MP", "PED DEFAULT MP", "ped_default_mp"),
    ShaderMaterial("GRASS", "GRASS", "grass"),
    ShaderMaterial("VEHICLE_TRACK_EMISSIVE",
                   "VEHICLE TRACK EMISSIVE", "vehicle_track_emissive"),
    ShaderMaterial("GLASS_SPEC", "GLASS SPEC", "glass_spec"),
    ShaderMaterial("VEHICLE_PAINT5_ENVEFF",
                   "VEHICLE PAINT5 ENVEFF", "vehicle_paint5_enveff"),
    ShaderMaterial("PED_WRINKLE_ENVEFF", "PED WRINKLE ENVEFF",
                   "ped_wrinkle_enveff"),
    ShaderMaterial("WEAPON_NORMAL_SPEC_DETAIL_TNT",
                   "WEAPON NORMAL SPEC DETAIL TNT", "weapon_normal_spec_detail_tnt"),
    ShaderMaterial("GLASS_PV", "GLASS PV", "glass_pv"),
    ShaderMaterial("TERRAIN_CB_W_4LYR_SPEC_INT_PXM",
                   "TERRAIN CB W 4LYR SPEC INT PXM", "terrain_cb_w_4lyr_spec_int_pxm"),
    ShaderMaterial("GLASS_EMISSIVE", "GLASS EMISSIVE", "glass_emissive"),
    ShaderMaterial("WEAPON_NORMAL_SPEC_ALPHA",
                   "WEAPON NORMAL SPEC ALPHA", "weapon_normal_spec_alpha"),
    ShaderMaterial("NORMAL_PXM", "NORMAL PXM", "normal_pxm"),
    ShaderMaterial("WATER_FOUNTAIN", "WATER FOUNTAIN", "water_fountain"),
    ShaderMaterial("REFLECT", "REFLECT", "reflect"),
    ShaderMaterial("NORMAL_REFLECT", "NORMAL REFLECT", "normal_reflect"),
    ShaderMaterial("TERRAIN_CB_W_4LYR_SPEC_INT",
                   "TERRAIN CB W 4LYR SPEC INT", "terrain_cb_w_4lyr_spec_int"),
    ShaderMaterial("PED_WRINKLE_CS", "PED WRINKLE CS", "ped_wrinkle_cs"),
    ShaderMaterial("GRASS_BATCH", "GRASS BATCH", "grass_batch"),
    ShaderMaterial("EMISSIVENIGHT_GEOMNIGHTONLY",
                   "EMISSIVENIGHT GEOMNIGHTONLY", "emissivenight_geomnightonly"),
    ShaderMaterial("PED_DECAL_DECORATION",
                   "PED DECAL DECORATION", "ped_decal_decoration"),
    ShaderMaterial("VEHICLE_PAINT6", "VEHICLE PAINT6", "vehicle_paint6"),
    ShaderMaterial("WATER_RIVERLOD", "WATER RIVERLOD", "water_riverlod"),
    ShaderMaterial("NORMAL_UM", "NORMAL UM", "normal_um"),
    ShaderMaterial("VEHICLE_DECAL2", "VEHICLE DECAL2", "vehicle_decal2"),
    ShaderMaterial("WEAPON_EMISSIVESTRONG_ALPHA",
                   "WEAPON EMISSIVESTRONG ALPHA", "weapon_emissivestrong_alpha"),
    ShaderMaterial("WATER_SHALLOW", "WATER SHALLOW", "water_shallow"),
    ShaderMaterial("VEHICLE_PAINT1_ENVEFF",
                   "VEHICLE PAINT1 ENVEFF", "vehicle_paint1_enveff"),
    ShaderMaterial("TERRAIN_CB_W_4LYR_2TEX",
                   "TERRAIN CB W 4LYR 2TEX", "terrain_cb_w_4lyr_2tex"),
    ShaderMaterial("TREES_SHADOW_PROXY", "TREES SHADOW PROXY",
                   "trees_shadow_proxy"),
    ShaderMaterial("VEHICLE_MESH_ENVEFF", "VEHICLE MESH ENVEFF",
                   "vehicle_mesh_enveff"),
    ShaderMaterial("PED_DEFAULT_ENVEFF", "PED DEFAULT ENVEFF",
                   "ped_default_enveff"),
    ShaderMaterial("WATER_RIVERFOAM", "WATER RIVERFOAM", "water_riverfoam"),
    ShaderMaterial("ALBEDO_ALPHA", "ALBEDO ALPHA", "albedo_alpha"),
    ShaderMaterial("DECAL_SHADOW_ONLY", "DECAL SHADOW ONLY",
                   "decal_shadow_only"),
    ShaderMaterial("RADAR", "RADAR", "radar"),
    ShaderMaterial("TREES_TNT", "TREES TNT", "trees_tnt"),
    ShaderMaterial("WEAPON_NORMAL_SPEC_PALETTE",
                   "WEAPON NORMAL SPEC PALETTE", "weapon_normal_spec_palette"),
    ShaderMaterial("TREES_NORMAL", "TREES NORMAL", "trees_normal"),
    ShaderMaterial("DECAL_SPEC_ONLY", "DECAL SPEC ONLY", "decal_spec_only"),
    ShaderMaterial("MIRROR_DEFAULT", "MIRROR DEFAULT", "mirror_default"),
    ShaderMaterial("PED_PALETTE", "PED PALETTE", "ped_palette"),
    ShaderMaterial("NORMAL_SPEC_DECAL_NOPUDDLE",
                   "NORMAL SPEC DECAL NOPUDDLE", "normal_spec_decal_nopuddle"),
    ShaderMaterial("NORMAL_SPEC_EMISSIVE",
                   "NORMAL SPEC EMISSIVE", "normal_spec_emissive"),
    ShaderMaterial("NORMAL_SPEC_UM", "NORMAL SPEC UM", "normal_spec_um"),
    ShaderMaterial("DECAL_EMISSIVENIGHT_ONLY",
                   "DECAL EMISSIVENIGHT ONLY", "decal_emissivenight_only"),
    ShaderMaterial("PED_DEFAULT_PALETTE", "PED DEFAULT PALETTE",
                   "ped_default_palette"),
    ShaderMaterial("WATER_RIVER", "WATER RIVER", "water_river"),
    ShaderMaterial("WEAPON_NORMAL_SPEC_TNT",
                   "WEAPON NORMAL SPEC TNT", "weapon_normal_spec_tnt"),
    ShaderMaterial("CUTOUT_HARD", "CUTOUT HARD", "cutout_hard"),
    ShaderMaterial("NORMAL_SPEC_PXM_TNT", "NORMAL SPEC PXM TNT",
                   "normal_spec_pxm_tnt"),
    ShaderMaterial("TERRAIN_CB_W_4LYR_CM_TNT",
                   "TERRAIN CB W 4LYR CM TNT", "terrain_cb_w_4lyr_cm_tnt"),
    ShaderMaterial("VEHICLE_EMISSIVE_ALPHA",
                   "VEHICLE EMISSIVE ALPHA", "vehicle_emissive_alpha"),
    ShaderMaterial("MIRROR_DECAL", "MIRROR DECAL", "mirror_decal"),
    ShaderMaterial("VEHICLE_TRACK2_EMISSIVE",
                   "VEHICLE TRACK2 EMISSIVE", "vehicle_track2_emissive"),
    ShaderMaterial("PED_CLOTH", "PED CLOTH", "ped_cloth"),
    ShaderMaterial("NORMAL_CUBEMAP_REFLECT",
                   "NORMAL CUBEMAP REFLECT", "normal_cubemap_reflect"),
    ShaderMaterial("NORMAL_SPEC_CUBEMAP_REFLECT",
                   "NORMAL SPEC CUBEMAP REFLECT", "normal_spec_cubemap_reflect"),
    ShaderMaterial("GLASS_REFLECT", "GLASS REFLECT", "glass_reflect"),
    ShaderMaterial("SPEC_TWIDDLE_TNT", "SPEC TWIDDLE TNT", "spec_twiddle_tnt"),
    ShaderMaterial("NORMAL_DIFFSPEC_DETAIL",
                   "NORMAL DIFFSPEC DETAIL", "normal_diffspec_detail"),
    ShaderMaterial("WEAPON_NORMAL_SPEC_CUTOUT_PALETTE",
                   "WEAPON NORMAL SPEC CUTOUT PALETTE", "weapon_normal_spec_cutout_palette"),
    ShaderMaterial("TERRAIN_CB_W_4LYR_SPEC",
                   "TERRAIN CB W 4LYR SPEC", "terrain_cb_w_4lyr_spec"),
    ShaderMaterial("PED_FUR", "PED FUR", "ped_fur"),
    ShaderMaterial("CLOUDS_FAST", "CLOUDS FAST", "clouds_fast"),
    ShaderMaterial("NORMAL_DIFFSPEC_DETAIL_DPM",
                   "NORMAL DIFFSPEC DETAIL DPM", "normal_diffspec_detail_dpm"),
    ShaderMaterial("VEHICLE_PAINT3_ENVEFF",
                   "VEHICLE PAINT3 ENVEFF", "vehicle_paint3_enveff"),
    ShaderMaterial("TREES_NORMAL_SPEC_TNT",
                   "TREES NORMAL SPEC TNT", "trees_normal_spec_tnt"),
    ShaderMaterial("CLOUDS_ANIMSOFT", "CLOUDS ANIMSOFT", "clouds_animsoft"),
    ShaderMaterial("DECAL_AMB_ONLY", "DECAL AMB ONLY", "decal_amb_only"),
    ShaderMaterial("NORMAL_DIFFSPEC_DETAIL_DPM_TNT",
                   "NORMAL DIFFSPEC DETAIL DPM TNT", "normal_diffspec_detail_dpm_tnt"),
    ShaderMaterial("WATER_RIVEROCEAN", "WATER RIVEROCEAN", "water_riverocean"),
    ShaderMaterial("TERRAIN_CB_W_4LYR_CM_PXM",
                   "TERRAIN CB W 4LYR CM PXM", "terrain_cb_w_4lyr_cm_pxm"),
    ShaderMaterial("VEHICLE_PAINT2_ENVEFF",
                   "VEHICLE PAINT2 ENVEFF", "vehicle_paint2_enveff"),
    ShaderMaterial("VEHICLE_BLURREDROTOR_EMISSIVE",
                   "VEHICLE BLURREDROTOR EMISSIVE", "vehicle_blurredrotor_emissive"),
    ShaderMaterial("TERRAIN_CB_W_4LYR_CM_PXM_TNT",
                   "TERRAIN CB W 4LYR CM PXM TNT", "terrain_cb_w_4lyr_cm_pxm_tnt"),
    ShaderMaterial("WATER_RIVERSHALLOW", "WATER RIVERSHALLOW",
                   "water_rivershallow"),
    ShaderMaterial("VEHICLE_PAINT7_ENVEFF",
                   "VEHICLE PAINT7 ENVEFF", "vehicle_paint7_enveff"),
    ShaderMaterial("TERRAIN_CB_W_4LYR_2TEX_PXM",
                   "TERRAIN CB W 4LYR 2TEX PXM", "terrain_cb_w_4lyr_2tex_pxm"),
    ShaderMaterial("PED_WRINKLE_CLOTH", "PED WRINKLE CLOTH",
                   "ped_wrinkle_cloth"),
    ShaderMaterial("NORMAL_SPEC_REFLECT_DECAL",
                   "NORMAL SPEC REFLECT DECAL", "normal_spec_reflect_decal"),
    ShaderMaterial("PARALLAX_SPECMAP", "PARALLAX SPECMAP", "parallax_specmap"),
    ShaderMaterial("NORMAL_SPEC_DETAIL_DPM_TNT",
                   "NORMAL SPEC DETAIL DPM TNT", "normal_spec_detail_dpm_tnt"),
    ShaderMaterial("PED_WRINKLE_CLOTH_ENVEFF",
                   "PED WRINKLE CLOTH ENVEFF", "ped_wrinkle_cloth_enveff"),
    ShaderMaterial("WATER_POOLENV", "WATER POOLENV", "water_poolenv"),
    ShaderMaterial("NORMAL_SPEC_REFLECT_EMISSIVENIGHT",
                   "NORMAL SPEC REFLECT EMISSIVENIGHT", "normal_spec_reflect_emissivenight"),
    ShaderMaterial("TREES_LOD_TNT", "TREES LOD TNT", "trees_lod_tnt"),
    ShaderMaterial("DECAL_DIFF_ONLY_UM", "DECAL DIFF ONLY UM",
                   "decal_diff_only_um"),
    ShaderMaterial("VEHICLE_PAINT7", "VEHICLE PAINT7", "vehicle_paint7"),
    ShaderMaterial("VEHICLE_PAINT4_EMISSIVE",
                   "VEHICLE PAINT4 EMISSIVE", "vehicle_paint4_emissive"),
    ShaderMaterial("NORMAL_PXM_TNT", "NORMAL PXM TNT", "normal_pxm_tnt"),
    ShaderMaterial("BLEND_2LYR", "BLEND 2LYR", "blend_2lyr"),
    ShaderMaterial("TREES_NORMAL_DIFFSPEC_TNT",
                   "TREES NORMAL DIFFSPEC TNT", "trees_normal_diffspec_tnt"),
    ShaderMaterial("PED_DEFAULT_CLOTH", "PED DEFAULT CLOTH",
                   "ped_default_cloth"),
    ShaderMaterial("MIRROR_CRACK", "MIRROR CRACK", "mirror_crack"),
    ShaderMaterial("GLASS_DISPLACEMENT", "GLASS DISPLACEMENT",
                   "glass_displacement"),
    ShaderMaterial("NORMAL_SPEC_DETAIL_DPM_VERTDECAL_TNT",
                   "NORMAL SPEC DETAIL DPM VERTDECAL TNT", "normal_spec_detail_dpm_vertdecal_tnt"),
    ShaderMaterial("CLOTH_NORMAL_SPEC_TNT",
                   "CLOTH NORMAL SPEC TNT", "cloth_normal_spec_tnt"),
    ShaderMaterial("NORMAL_DIFFSPEC", "NORMAL DIFFSPEC", "normal_diffspec"),
    ShaderMaterial("GLASS_EMISSIVENIGHT", "GLASS EMISSIVENIGHT",
                   "glass_emissivenight"),
    ShaderMaterial("NORMAL_DECAL_PXM_TNT",
                   "NORMAL DECAL PXM TNT", "normal_decal_pxm_tnt"),
    ShaderMaterial("NORMAL_SPEC_DPM", "NORMAL SPEC DPM", "normal_spec_dpm"),
    ShaderMaterial("WEAPON_EMISSIVE_TNT", "WEAPON EMISSIVE TNT",
                   "weapon_emissive_tnt"),
    ShaderMaterial("CLOUDS_ANIM", "CLOUDS ANIM", "clouds_anim"),
    ShaderMaterial("VEHICLE_PAINT3_LVR", "VEHICLE PAINT3 LVR",
                   "vehicle_paint3_lvr"),
    ShaderMaterial("NORMAL_SPEC_DETAIL_DPM",
                   "NORMAL SPEC DETAIL DPM", "normal_spec_detail_dpm"),
    ShaderMaterial("NORMAL_SPEC_BATCH", "NORMAL SPEC BATCH",
                   "normal_spec_batch"),
    ShaderMaterial("PED_DECAL_EXP", "PED DECAL EXP", "ped_decal_exp"),
    ShaderMaterial("CLOUDS_ALTITUDE", "CLOUDS ALTITUDE", "clouds_altitude"),
    ShaderMaterial("SPEC_REFLECT_DECAL", "SPEC REFLECT DECAL",
                   "spec_reflect_decal"),
    ShaderMaterial("TERRAIN_CB_W_4LYR_CM",
                   "TERRAIN CB W 4LYR CM", "terrain_cb_w_4lyr_cm"),
    ShaderMaterial("PARALLAX", "PARALLAX", "parallax"),
    ShaderMaterial("NORMAL_DIFFSPEC_DETAIL_TNT",
                   "NORMAL DIFFSPEC DETAIL TNT", "normal_diffspec_detail_tnt"),
    ShaderMaterial("NORMAL_DETAIL_DPM", "NORMAL DETAIL DPM",
                   "normal_detail_dpm"),
    ShaderMaterial("VEHICLE_CLOTH2", "VEHICLE CLOTH2", "vehicle_cloth2"),
    ShaderMaterial("NORMAL_DIFFSPEC_TNT", "NORMAL DIFFSPEC TNT",
                   "normal_diffspec_tnt"),
    ShaderMaterial("REFLECT_DECAL", "REFLECT DECAL", "reflect_decal"),
    ShaderMaterial("CLOUDS_SOFT", "CLOUDS SOFT", "clouds_soft"),
    ShaderMaterial("PED_DECAL_NODIFF", "PED DECAL NODIFF", "ped_decal_nodiff"),
    ShaderMaterial("TERRAIN_CB_4LYR_2TEX",
                   "TERRAIN CB 4LYR 2TEX", "terrain_cb_4lyr_2tex"),
    ShaderMaterial("NORMAL_SPEC_WRINKLE", "NORMAL SPEC WRINKLE",
                   "normal_spec_wrinkle"),
    ShaderMaterial("SKY_SYSTEM", "SKY SYSTEM", "sky_system"),
    ShaderMaterial("CLOUDS_FOG", "CLOUDS FOG", "clouds_fog"),
    ShaderMaterial("TERRAIN_CB_4LYR", "TERRAIN CB 4LYR", "terrain_cb_4lyr"),
    ShaderMaterial("NORMAL_REFLECT_DECAL",
                   "NORMAL REFLECT DECAL", "normal_reflect_decal"),
    ShaderMaterial("PED_CLOTH_ENVEFF", "PED CLOTH ENVEFF", "ped_cloth_enveff"),
]


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
    texture_path = os.path.dirname(
        __file__)[:-4] + "\\resources\\givemechecker.dds"
    gmc_texture = bpy.data.images.load(texture_path, check_existing=True)
    imgnode.image = gmc_texture

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
    mat.sollum_type = MaterialType.SHADER
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
