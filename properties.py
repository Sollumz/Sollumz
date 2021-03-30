import bpy
from bpy.types import PropertyGroup
from bpy.props import CollectionProperty, PointerProperty, StringProperty, IntProperty, BoolProperty, FloatProperty, EnumProperty
from .sollumz_ui import bounds_update, scene_lod_update, scene_hide_collision


#sollum properties
bpy.types.Scene.last_created_material = PointerProperty(type=bpy.types.Material)
bpy.types.Scene.level_of_detail = bpy.props.EnumProperty(
    name = "Level Of Detail",
    items = [
        ("All", "All", "All"),
        ("High", "High", "High"),
        ("Medium", "Medium", "Medium"),
        ("Low", "Low", "Low"),
        ("Very Low", "Very Low", "Very Low")
    ],
    update = scene_lod_update,
)

bpy.types.Scene.hide_collision = bpy.props.BoolProperty(name = "Hide Collision", update = scene_hide_collision)

bpy.types.Object.sollumtype = bpy.props.EnumProperty(
                                                        name = "Vtype", 
                                                        default = "None",
                                                        items = [
                                                                    ("None", "None", "None"),
                                                                    ("Fragment", "Fragment", "Fragment"),
                                                                    ("Drawable Dictionary", "Drawable Dictionary", "Drawable Dictionary"),
                                                                    ("Drawable", "Drawable", "Drawable"), 
                                                                    ("Geometry", "Geometry", "Geometry"),
                                                                    ("Bound Composite", "Bound Composite", "Bound Composite"),
                                                                    ("Bound Geometry", "Bound Geometry", "Bound Geometry"),
                                                                    ("Bound Box", "Bound Box", "Bound Box"),
                                                                    ("Bound Triangle", "Bound Triangle", "Bound Triangle"), 
                                                                    ("Bound Sphere", "Bound Sphere", "Bound Sphere"),
                                                                    ("Bound Capsule", "Bound Capsule", "Bound Capsule"),
                                                                    ("Bound Disc", "Bound Disc", "Bound Disc"),
                                                                    ("Bound Cylinder", "Bound Cylinder", "Bound Cylinder")])
                                                                    
bpy.types.Object.level_of_detail = EnumProperty(name = "Level Of Detail", items = [("High", "High", "High"), ("Medium", "Medium", "Medium"), ("Low", "Low", "Low"), ("Very Low", "Very Low", "Very Low")])
bpy.types.Object.mask = IntProperty(name = "Mask", default = 255)
bpy.types.Object.drawble_distance_high = FloatProperty(name = "Lod Distance High", default = 9998.0, min = 0, max = 100000)
bpy.types.Object.drawble_distance_medium = FloatProperty(name = "Lod Distance Medium", default = 9998.0, min = 0, max = 100000)
bpy.types.Object.drawble_distance_low = FloatProperty(name = "Lod Distance Low", default = 9998.0, min = 0, max = 100000)
bpy.types.Object.drawble_distance_vlow = FloatProperty(name = "Lod Distance vlow", default = 9998.0, min = 0, max = 100000)

bpy.types.Object.bounds_length = FloatProperty(name="Length", default=1, min=0, max=100, update=bounds_update)
bpy.types.Object.bounds_radius = FloatProperty(name="Radius", default=1, min=0, max=100, update=bounds_update)
bpy.types.Object.bounds_rings = IntProperty(name="Rings", default=6, min=1, max=100, update=bounds_update)
bpy.types.Object.bounds_segments = IntProperty(name="Segments", default=12, min=3, max=100, update=bounds_update)
bpy.types.Object.bounds_bvh = BoolProperty(name="BVH (Bounding volume hierarchy)", default=False, update=bounds_update)

bpy.types.Object.shadertype = EnumProperty(
                                                        name = "Shader Type", 
                                                        default = "default.sps",
                                                        items = [
                                                                    ("blend_2lyr.sps", "blend_2lyr.sps", "blend_2lyr.sps"), 
                                                                    ("cable.sps", "cable.sps", "cable.sps"), 
                                                                    ("cloth_default.sps", "cloth_default.sps", "cloth_default.sps"), 
                                                                    ("cloth_normal_spec.sps", "cloth_normal_spec.sps", "cloth_normal_spec.sps"), 
                                                                    ("cloth_normal_spec_alpha.sps", "cloth_normal_spec_alpha.sps", "cloth_normal_spec_alpha.sps"), 
                                                                    ("cloth_normal_spec_cutout.sps", "cloth_normal_spec_cutout.sps", "cloth_normal_spec_cutout.sps"), 
                                                                    ("cloth_normal_spec_tnt.sps", "cloth_normal_spec_tnt.sps", "cloth_normal_spec_tnt.sps"), 
                                                                    ("cloth_spec_alpha.sps", "cloth_spec_alpha.sps", "cloth_spec_alpha.sps"), 
                                                                    ("cloth_spec_cutout.sps", "cloth_spec_cutout.sps", "cloth_spec_cutout.sps"), 
                                                                    ("clouds_altitude.sps", "clouds_altitude.sps", "clouds_altitude.sps"), 
                                                                    ("clouds_anim.sps", "clouds_anim.sps", "clouds_anim.sps"), 
                                                                    ("clouds_animsoft.sps", "clouds_animsoft.sps", "clouds_animsoft.sps"), 
                                                                    ("clouds_fast.sps", "clouds_fast.sps", "clouds_fast.sps"), 
                                                                    ("clouds_fog.sps", "clouds_fog.sps", "clouds_fog.sps"), 
                                                                    ("clouds_soft.sps", "clouds_soft.sps", "clouds_soft.sps"), 
                                                                    ("cpv_only.sps", "cpv_only.sps", "cpv_only.sps"), 
                                                                    ("cutout_fence.sps", "cutout_fence.sps", "cutout_fence.sps"), 
                                                                    ("cutout_fence_normal.sps", "cutout_fence_normal.sps", "cutout_fence_normal.sps"), 
                                                                    ("cutout_hard.sps", "cutout_hard.sps", "cutout_hard.sps"), 
                                                                    ("decal.sps", "decal.sps", "decal.sps"), 
                                                                    ("decal_amb_only.sps", "decal_amb_only.sps", "decal_amb_only.sps"), 
                                                                    ("decal_diff_only_um.sps", "decal_diff_only_um.sps", "decal_diff_only_um.sps"), 
                                                                    ("decal_dirt.sps", "decal_dirt.sps", "decal_dirt.sps"), 
                                                                    ("decal_emissivenight_only.sps", "decal_emissivenight_only.sps", "decal_emissivenight_only.sps"), 
                                                                    ("decal_emissive_only.sps", "decal_emissive_only.sps", "decal_emissive_only.sps"), 
                                                                    ("decal_glue.sps", "decal_glue.sps", "decal_glue.sps"), 
                                                                    ("decal_normal_only.sps", "decal_normal_only.sps", "decal_normal_only.sps"), 
                                                                    ("decal_shadow_only.sps", "decal_shadow_only.sps", "decal_shadow_only.sps"), 
                                                                    ("decal_spec_only.sps", "decal_spec_only.sps", "decal_spec_only.sps"), 
                                                                    ("decal_tnt.sps", "decal_tnt.sps", "decal_tnt.sps"), 
                                                                    ("custom_default.sps", "custom_default.sps", "custom_default.sps"), 
                                                                    ("default.sps", "default.sps", "default.sps"), 
                                                                    ("default_noedge.sps", "default_noedge.sps", "default_noedge.sps"), 
                                                                    ("gta_default.sps", "gta_default.sps", "gta_default.sps"), 
                                                                    ("alpha.sps", "alpha.sps", "alpha.sps"), 
                                                                    ("cutout.sps", "cutout.sps", "cutout.sps"), 
                                                                    ("default_detail.sps", "default_detail.sps", "default_detail.sps"), 
                                                                    ("default_spec.sps", "default_spec.sps", "default_spec.sps"), 
                                                                    ("spec_const.sps", "spec_const.sps", "spec_const.sps"), 
                                                                    ("default_terrain_wet.sps", "default_terrain_wet.sps", "default_terrain_wet.sps"), 
                                                                    ("default_tnt.sps", "default_tnt.sps", "default_tnt.sps"), 
                                                                    ("cutout_tnt.sps", "cutout_tnt.sps", "cutout_tnt.sps"), 
                                                                    ("default_um.sps", "default_um.sps", "default_um.sps"), 
                                                                    ("cutout_um.sps", "cutout_um.sps", "cutout_um.sps"), 
                                                                    ("distance_map.sps", "distance_map.sps", "distance_map.sps"), 
                                                                    ("emissive.sps", "emissive.sps", "emissive.sps"), 
                                                                    ("emissive_alpha.sps", "emissive_alpha.sps", "emissive_alpha.sps"), 
                                                                    ("emissivenight.sps", "emissivenight.sps", "emissivenight.sps"), 
                                                                    ("emissivenight_alpha.sps", "emissivenight_alpha.sps", "emissivenight_alpha.sps"), 
                                                                    ("emissivenight_geomnightonly.sps", "emissivenight_geomnightonly.sps", "emissivenight_geomnightonly.sps"), 
                                                                    ("emissivestrong.sps", "emissivestrong.sps", "emissivestrong.sps"), 
                                                                    ("emissivestrong_alpha.sps", "emissivestrong_alpha.sps", "emissivestrong_alpha.sps"), 
                                                                    ("emissive_additive_alpha.sps", "emissive_additive_alpha.sps", "emissive_additive_alpha.sps"), 
                                                                    ("emissive_additive_uv_alpha.sps", "emissive_additive_uv_alpha.sps", "emissive_additive_uv_alpha.sps"), 
                                                                    ("emissive_clip.sps", "emissive_clip.sps", "emissive_clip.sps"), 
                                                                    ("emissive_speclum.sps", "emissive_speclum.sps", "emissive_speclum.sps"), 
                                                                    ("emissive_tnt.sps", "emissive_tnt.sps", "emissive_tnt.sps"), 
                                                                    ("emissive_alpha_tnt.sps", "emissive_alpha_tnt.sps", "emissive_alpha_tnt.sps"), 
                                                                    ("glass.sps", "glass.sps", "glass.sps"), 
                                                                    ("glass_breakable.sps", "glass_breakable.sps", "glass_breakable.sps"), 
                                                                    ("glass_breakable_screendooralpha.sps", "glass_breakable_screendooralpha.sps", "glass_breakable_screendooralpha.sps"), 
                                                                    ("glass_displacement.sps", "glass_displacement.sps", "glass_displacement.sps"), 
                                                                    ("glass_emissive.sps", "glass_emissive.sps", "glass_emissive.sps"), 
                                                                    ("glass_emissive_alpha.sps", "glass_emissive_alpha.sps", "glass_emissive_alpha.sps"), 
                                                                    ("glass_emissivenight.sps", "glass_emissivenight.sps", "glass_emissivenight.sps"), 
                                                                    ("glass_emissivenight_alpha.sps", "glass_emissivenight_alpha.sps", "glass_emissivenight_alpha.sps"), 
                                                                    ("glass_env.sps", "glass_env.sps", "glass_env.sps"), 
                                                                    ("glass_normal_spec_reflect.sps", "glass_normal_spec_reflect.sps", "glass_normal_spec_reflect.sps"), 
                                                                    ("glass_pv.sps", "glass_pv.sps", "glass_pv.sps"), 
                                                                    ("glass_pv_env.sps", "glass_pv_env.sps", "glass_pv_env.sps"), 
                                                                    ("glass_reflect.sps", "glass_reflect.sps", "glass_reflect.sps"), 
                                                                    ("glass_spec.sps", "glass_spec.sps", "glass_spec.sps"), 
                                                                    ("grass.sps", "grass.sps", "grass.sps"), 
                                                                    ("grass_batch.sps", "grass_batch.sps", "grass_batch.sps"), 
                                                                    ("grass_fur.sps", "grass_fur.sps", "grass_fur.sps"), 
                                                                    ("grass_fur_mask.sps", "grass_fur_mask.sps", "grass_fur_mask.sps"), 
                                                                    ("minimap.sps", "minimap.sps", "minimap.sps"), 
                                                                    ("mirror_crack.sps", "mirror_crack.sps", "mirror_crack.sps"), 
                                                                    ("mirror_decal.sps", "mirror_decal.sps", "mirror_decal.sps"), 
                                                                    ("mirror_default.sps", "mirror_default.sps", "mirror_default.sps"), 
                                                                    ("gta_normal.sps", "gta_normal.sps", "gta_normal.sps"), 
                                                                    ("normal.sps", "normal.sps", "normal.sps"), 
                                                                    ("normal_alpha.sps", "normal_alpha.sps", "normal_alpha.sps"), 
                                                                    ("water_decal.sps", "water_decal.sps", "water_decal.sps"), 
                                                                    ("normal_cutout.sps", "normal_cutout.sps", "normal_cutout.sps"), 
                                                                    ("normal_screendooralpha.sps", "normal_screendooralpha.sps", "normal_screendooralpha.sps"), 
                                                                    ("normal_cubemap_reflect.sps", "normal_cubemap_reflect.sps", "normal_cubemap_reflect.sps"), 
                                                                    ("normal_decal.sps", "normal_decal.sps", "normal_decal.sps"), 
                                                                    ("normal_decal_pxm.sps", "normal_decal_pxm.sps", "normal_decal_pxm.sps"), 
                                                                    ("normal_decal_pxm_tnt.sps", "normal_decal_pxm_tnt.sps", "normal_decal_pxm_tnt.sps"), 
                                                                    ("normal_decal_tnt.sps", "normal_decal_tnt.sps", "normal_decal_tnt.sps"), 
                                                                    ("normal_detail.sps", "normal_detail.sps", "normal_detail.sps"), 
                                                                    ("normal_detail_dpm.sps", "normal_detail_dpm.sps", "normal_detail_dpm.sps"), 
                                                                    ("normal_diffspec.sps", "normal_diffspec.sps", "normal_diffspec.sps"), 
                                                                    ("normal_diffspec_detail.sps", "normal_diffspec_detail.sps", "normal_diffspec_detail.sps"), 
                                                                    ("normal_diffspec_detail_dpm.sps", "normal_diffspec_detail_dpm.sps", "normal_diffspec_detail_dpm.sps"), 
                                                                    ("normal_diffspec_detail_dpm_tnt.sps", "normal_diffspec_detail_dpm_tnt.sps", "normal_diffspec_detail_dpm_tnt.sps"), 
                                                                    ("normal_diffspec_detail_tnt.sps", "normal_diffspec_detail_tnt.sps", "normal_diffspec_detail_tnt.sps"), 
                                                                    ("normal_diffspec_tnt.sps", "normal_diffspec_tnt.sps", "normal_diffspec_tnt.sps"), 
                                                                    ("normal_pxm.sps", "normal_pxm.sps", "normal_pxm.sps"), 
                                                                    ("normal_pxm_tnt.sps", "normal_pxm_tnt.sps", "normal_pxm_tnt.sps"), 
                                                                    ("normal_tnt_pxm.sps", "normal_tnt_pxm.sps", "normal_tnt_pxm.sps"), 
                                                                    ("normal_reflect.sps", "normal_reflect.sps", "normal_reflect.sps"), 
                                                                    ("normal_reflect_alpha.sps", "normal_reflect_alpha.sps", "normal_reflect_alpha.sps"), 
                                                                    ("normal_reflect_screendooralpha.sps", "normal_reflect_screendooralpha.sps", "normal_reflect_screendooralpha.sps"), 
                                                                    ("normal_reflect_decal.sps", "normal_reflect_decal.sps", "normal_reflect_decal.sps"), 
                                                                    ("normal_spec.sps", "normal_spec.sps", "normal_spec.sps"), 
                                                                    ("normal_spec_alpha.sps", "normal_spec_alpha.sps", "normal_spec_alpha.sps"), 
                                                                    ("normal_spec_cutout.sps", "normal_spec_cutout.sps", "normal_spec_cutout.sps"), 
                                                                    ("normal_spec_screendooralpha.sps", "normal_spec_screendooralpha.sps", "normal_spec_screendooralpha.sps"), 
                                                                    ("normal_spec_batch.sps", "normal_spec_batch.sps", "normal_spec_batch.sps"), 
                                                                    ("normal_spec_cubemap_reflect.sps", "normal_spec_cubemap_reflect.sps", "normal_spec_cubemap_reflect.sps"), 
                                                                    ("normal_spec_decal.sps", "normal_spec_decal.sps", "normal_spec_decal.sps"), 
                                                                    ("normal_spec_decal_detail.sps", "normal_spec_decal_detail.sps", "normal_spec_decal_detail.sps"), 
                                                                    ("normal_spec_decal_nopuddle.sps", "normal_spec_decal_nopuddle.sps", "normal_spec_decal_nopuddle.sps"), 
                                                                    ("normal_spec_decal_pxm.sps", "normal_spec_decal_pxm.sps", "normal_spec_decal_pxm.sps"), 
                                                                    ("normal_spec_decal_tnt.sps", "normal_spec_decal_tnt.sps", "normal_spec_decal_tnt.sps"), 
                                                                    ("normal_spec_detail.sps", "normal_spec_detail.sps", "normal_spec_detail.sps"), 
                                                                    ("normal_spec_detail_dpm.sps", "normal_spec_detail_dpm.sps", "normal_spec_detail_dpm.sps"), 
                                                                    ("normal_spec_detail_dpm_tnt.sps", "normal_spec_detail_dpm_tnt.sps", "normal_spec_detail_dpm_tnt.sps"), 
                                                                    ("normal_spec_detail_dpm_vertdecal_tnt.sps", "normal_spec_detail_dpm_vertdecal_tnt.sps", "normal_spec_detail_dpm_vertdecal_tnt.sps"), 
                                                                    ("normal_spec_detail_tnt.sps", "normal_spec_detail_tnt.sps", "normal_spec_detail_tnt.sps"), 
                                                                    ("normal_spec_dpm.sps", "normal_spec_dpm.sps", "normal_spec_dpm.sps"), 
                                                                    ("normal_spec_emissive.sps", "normal_spec_emissive.sps", "normal_spec_emissive.sps"), 
                                                                    ("normal_spec_pxm.sps", "normal_spec_pxm.sps", "normal_spec_pxm.sps"), 
                                                                    ("normal_spec_pxm_tnt.sps", "normal_spec_pxm_tnt.sps", "normal_spec_pxm_tnt.sps"), 
                                                                    ("normal_spec_tnt_pxm.sps", "normal_spec_tnt_pxm.sps", "normal_spec_tnt_pxm.sps"), 
                                                                    ("normal_spec_reflect.sps", "normal_spec_reflect.sps", "normal_spec_reflect.sps"), 
                                                                    ("normal_spec_reflect_alpha.sps", "normal_spec_reflect_alpha.sps", "normal_spec_reflect_alpha.sps"), 
                                                                    ("normal_spec_reflect_decal.sps", "normal_spec_reflect_decal.sps", "normal_spec_reflect_decal.sps"), 
                                                                    ("normal_spec_reflect_emissivenight.sps", "normal_spec_reflect_emissivenight.sps", "normal_spec_reflect_emissivenight.sps"), 
                                                                    ("normal_spec_reflect_emissivenight_alpha.sps", "normal_spec_reflect_emissivenight_alpha.sps", "normal_spec_reflect_emissivenight_alpha.sps"), 
                                                                    ("normal_spec_tnt.sps", "normal_spec_tnt.sps", "normal_spec_tnt.sps"), 
                                                                    ("normal_spec_cutout_tnt.sps", "normal_spec_cutout_tnt.sps", "normal_spec_cutout_tnt.sps"), 
                                                                    ("normal_spec_um.sps", "normal_spec_um.sps", "normal_spec_um.sps"), 
                                                                    ("normal_spec_wrinkle.sps", "normal_spec_wrinkle.sps", "normal_spec_wrinkle.sps"), 
                                                                    ("normal_terrain_wet.sps", "normal_terrain_wet.sps", "normal_terrain_wet.sps"), 
                                                                    ("normal_tnt.sps", "normal_tnt.sps", "normal_tnt.sps"), 
                                                                    ("normal_tnt_alpha.sps", "normal_tnt_alpha.sps", "normal_tnt_alpha.sps"), 
                                                                    ("normal_cutout_tnt.sps", "normal_cutout_tnt.sps", "normal_cutout_tnt.sps"), 
                                                                    ("normal_um.sps", "normal_um.sps", "normal_um.sps"), 
                                                                    ("normal_cutout_um.sps", "normal_cutout_um.sps", "normal_cutout_um.sps"), 
                                                                    ("normal_um_tnt.sps", "normal_um_tnt.sps", "normal_um_tnt.sps"), 
                                                                    ("parallax.sps", "parallax.sps", "parallax.sps"), 
                                                                    ("parallax_specmap.sps", "parallax_specmap.sps", "parallax_specmap.sps"), 
                                                                    ("ped.sps", "ped.sps", "ped.sps"), 
                                                                    ("ped_alpha.sps", "ped_alpha.sps", "ped_alpha.sps"), 
                                                                    ("ped_cloth.sps", "ped_cloth.sps", "ped_cloth.sps"), 
                                                                    ("ped_cloth_enveff.sps", "ped_cloth_enveff.sps", "ped_cloth_enveff.sps"), 
                                                                    ("ped_decal.sps", "ped_decal.sps", "ped_decal.sps"), 
                                                                    ("ped_decal_decoration.sps", "ped_decal_decoration.sps", "ped_decal_decoration.sps"), 
                                                                    ("ped_decal_expensive.sps", "ped_decal_expensive.sps", "ped_decal_expensive.sps"), 
                                                                    ("ped_decal_nodiff.sps", "ped_decal_nodiff.sps", "ped_decal_nodiff.sps"), 
                                                                    ("ped_default.sps", "ped_default.sps", "ped_default.sps"), 
                                                                    ("ped_default_cutout.sps", "ped_default_cutout.sps", "ped_default_cutout.sps"), 
                                                                    ("ped_default_cloth.sps", "ped_default_cloth.sps", "ped_default_cloth.sps"), 
                                                                    ("ped_default_enveff.sps", "ped_default_enveff.sps", "ped_default_enveff.sps"), 
                                                                    ("ped_default_mp.sps", "ped_default_mp.sps", "ped_default_mp.sps"), 
                                                                    ("ped_default_palette.sps", "ped_default_palette.sps", "ped_default_palette.sps"), 
                                                                    ("ped_emissive.sps", "ped_emissive.sps", "ped_emissive.sps"), 
                                                                    ("ped_enveff.sps", "ped_enveff.sps", "ped_enveff.sps"), 
                                                                    ("ped_fur.sps", "ped_fur.sps", "ped_fur.sps"), 
                                                                    ("ped_hair_cutout_alpha.sps", "ped_hair_cutout_alpha.sps", "ped_hair_cutout_alpha.sps"), 
                                                                    ("ped_hair_spiked.sps", "ped_hair_spiked.sps", "ped_hair_spiked.sps"), 
                                                                    ("ped_nopeddamagedecals.sps", "ped_nopeddamagedecals.sps", "ped_nopeddamagedecals.sps"), 
                                                                    ("ped_palette.sps", "ped_palette.sps", "ped_palette.sps"), 
                                                                    ("ped_wrinkle.sps", "ped_wrinkle.sps", "ped_wrinkle.sps"), 
                                                                    ("ped_wrinkle_cloth.sps", "ped_wrinkle_cloth.sps", "ped_wrinkle_cloth.sps"), 
                                                                    ("ped_wrinkle_cloth_enveff.sps", "ped_wrinkle_cloth_enveff.sps", "ped_wrinkle_cloth_enveff.sps"), 
                                                                    ("ped_wrinkle_cs.sps", "ped_wrinkle_cs.sps", "ped_wrinkle_cs.sps"), 
                                                                    ("ped_wrinkle_enveff.sps", "ped_wrinkle_enveff.sps", "ped_wrinkle_enveff.sps"), 
                                                                    ("ptfx_model.sps", "ptfx_model.sps", "ptfx_model.sps"), 
                                                                    ("gta_radar.sps", "gta_radar.sps", "gta_radar.sps"), 
                                                                    ("radar.sps", "radar.sps", "radar.sps"), 
                                                                    ("reflect.sps", "reflect.sps", "reflect.sps"), 
                                                                    ("gta_reflect_alpha.sps", "gta_reflect_alpha.sps", "gta_reflect_alpha.sps"), 
                                                                    ("reflect_alpha.sps", "reflect_alpha.sps", "reflect_alpha.sps"), 
                                                                    ("reflect_decal.sps", "reflect_decal.sps", "reflect_decal.sps"), 
                                                                    ("sky_system.sps", "sky_system.sps", "sky_system.sps"), 
                                                                    ("gta_spec.sps", "gta_spec.sps", "gta_spec.sps"), 
                                                                    ("spec.sps", "spec.sps", "spec.sps"), 
                                                                    ("spec_alpha.sps", "spec_alpha.sps", "spec_alpha.sps"), 
                                                                    ("spec_screendooralpha.sps", "spec_screendooralpha.sps", "spec_screendooralpha.sps"), 
                                                                    ("spec_decal.sps", "spec_decal.sps", "spec_decal.sps"), 
                                                                    ("spec_reflect.sps", "spec_reflect.sps", "spec_reflect.sps"), 
                                                                    ("spec_reflect_alpha.sps", "spec_reflect_alpha.sps", "spec_reflect_alpha.sps"), 
                                                                    ("spec_reflect_decal.sps", "spec_reflect_decal.sps", "spec_reflect_decal.sps"), 
                                                                    ("spec_tnt.sps", "spec_tnt.sps", "spec_tnt.sps"), 
                                                                    ("cutout_spec_tnt.sps", "cutout_spec_tnt.sps", "cutout_spec_tnt.sps"), 
                                                                    ("spec_twiddle_tnt.sps", "spec_twiddle_tnt.sps", "spec_twiddle_tnt.sps"), 
                                                                    ("terrain_cb_4lyr.sps", "terrain_cb_4lyr.sps", "terrain_cb_4lyr.sps"), 
                                                                    ("terrain_cb_4lyr_2tex.sps", "terrain_cb_4lyr_2tex.sps", "terrain_cb_4lyr_2tex.sps"), 
                                                                    ("terrain_cb_w_4lyr.sps", "terrain_cb_w_4lyr.sps", "terrain_cb_w_4lyr.sps"), 
                                                                    ("terrain_cb_w_4lyr_2tex.sps", "terrain_cb_w_4lyr_2tex.sps", "terrain_cb_w_4lyr_2tex.sps"), 
                                                                    ("terrain_cb_w_4lyr_2tex_blend.sps", "terrain_cb_w_4lyr_2tex_blend.sps", "terrain_cb_w_4lyr_2tex_blend.sps"), 
                                                                    ("terrain_cb_w_4lyr_2tex_blend_lod.sps", "terrain_cb_w_4lyr_2tex_blend_lod.sps", "terrain_cb_w_4lyr_2tex_blend_lod.sps"), 
                                                                    ("terrain_cb_w_4lyr_2tex_blend_pxm.sps", "terrain_cb_w_4lyr_2tex_blend_pxm.sps", "terrain_cb_w_4lyr_2tex_blend_pxm.sps"), 
                                                                    ("terrain_cb_w_4lyr_2tex_blend_pxm_spm.sps", "terrain_cb_w_4lyr_2tex_blend_pxm_spm.sps", "terrain_cb_w_4lyr_2tex_blend_pxm_spm.sps"), 
                                                                    ("terrain_cb_w_4lyr_2tex_pxm.sps", "terrain_cb_w_4lyr_2tex_pxm.sps", "terrain_cb_w_4lyr_2tex_pxm.sps"), 
                                                                    ("terrain_cb_w_4lyr_cm.sps", "terrain_cb_w_4lyr_cm.sps", "terrain_cb_w_4lyr_cm.sps"), 
                                                                    ("terrain_cb_w_4lyr_cm_pxm.sps", "terrain_cb_w_4lyr_cm_pxm.sps", "terrain_cb_w_4lyr_cm_pxm.sps"), 
                                                                    ("terrain_cb_w_4lyr_cm_pxm_tnt.sps", "terrain_cb_w_4lyr_cm_pxm_tnt.sps", "terrain_cb_w_4lyr_cm_pxm_tnt.sps"), 
                                                                    ("terrain_cb_w_4lyr_cm_tnt.sps", "terrain_cb_w_4lyr_cm_tnt.sps", "terrain_cb_w_4lyr_cm_tnt.sps"), 
                                                                    ("terrain_cb_w_4lyr_lod.sps", "terrain_cb_w_4lyr_lod.sps", "terrain_cb_w_4lyr_lod.sps"), 
                                                                    ("terrain_cb_w_4lyr_pxm.sps", "terrain_cb_w_4lyr_pxm.sps", "terrain_cb_w_4lyr_pxm.sps"), 
                                                                    ("terrain_cb_w_4lyr_pxm_spm.sps", "terrain_cb_w_4lyr_pxm_spm.sps", "terrain_cb_w_4lyr_pxm_spm.sps"), 
                                                                    ("terrain_cb_w_4lyr_spec.sps", "terrain_cb_w_4lyr_spec.sps", "terrain_cb_w_4lyr_spec.sps"), 
                                                                    ("terrain_cb_w_4lyr_spec_int.sps", "terrain_cb_w_4lyr_spec_int.sps", "terrain_cb_w_4lyr_spec_int.sps"), 
                                                                    ("terrain_cb_w_4lyr_spec_int_pxm.sps", "terrain_cb_w_4lyr_spec_int_pxm.sps", "terrain_cb_w_4lyr_spec_int_pxm.sps"), 
                                                                    ("terrain_cb_w_4lyr_spec_pxm.sps", "terrain_cb_w_4lyr_spec_pxm.sps", "terrain_cb_w_4lyr_spec_pxm.sps"), 
                                                                    ("trees.sps", "trees.sps", "trees.sps"), 
                                                                    ("trees_lod.sps", "trees_lod.sps", "trees_lod.sps"), 
                                                                    ("trees_lod2.sps", "trees_lod2.sps", "trees_lod2.sps"), 
                                                                    ("trees_lod_tnt.sps", "trees_lod_tnt.sps", "trees_lod_tnt.sps"), 
                                                                    ("trees_normal.sps", "trees_normal.sps", "trees_normal.sps"), 
                                                                    ("trees_normal_diffspec.sps", "trees_normal_diffspec.sps", "trees_normal_diffspec.sps"), 
                                                                    ("trees_normal_diffspec_tnt.sps", "trees_normal_diffspec_tnt.sps", "trees_normal_diffspec_tnt.sps"), 
                                                                    ("trees_normal_spec.sps", "trees_normal_spec.sps", "trees_normal_spec.sps"), 
                                                                    ("trees_normal_spec_tnt.sps", "trees_normal_spec_tnt.sps", "trees_normal_spec_tnt.sps"), 
                                                                    ("trees_shadow_proxy.sps", "trees_shadow_proxy.sps", "trees_shadow_proxy.sps"), 
                                                                    ("trees_tnt.sps", "trees_tnt.sps", "trees_tnt.sps"), 
                                                                    ("vehicle_badges.sps", "vehicle_badges.sps", "vehicle_badges.sps"), 
                                                                    ("vehicle_basic.sps", "vehicle_basic.sps", "vehicle_basic.sps"), 
                                                                    ("vehicle_blurredrotor.sps", "vehicle_blurredrotor.sps", "vehicle_blurredrotor.sps"), 
                                                                    ("vehicle_blurredrotor_emissive.sps", "vehicle_blurredrotor_emissive.sps", "vehicle_blurredrotor_emissive.sps"), 
                                                                    ("vehicle_cloth.sps", "vehicle_cloth.sps", "vehicle_cloth.sps"), 
                                                                    ("vehicle_cloth2.sps", "vehicle_cloth2.sps", "vehicle_cloth2.sps"), 
                                                                    ("vehicle_cutout.sps", "vehicle_cutout.sps", "vehicle_cutout.sps"), 
                                                                    ("vehicle_dash_emissive.sps", "vehicle_dash_emissive.sps", "vehicle_dash_emissive.sps"), 
                                                                    ("vehicle_dash_emissive_opaque.sps", "vehicle_dash_emissive_opaque.sps", "vehicle_dash_emissive_opaque.sps"), 
                                                                    ("vehicle_decal.sps", "vehicle_decal.sps", "vehicle_decal.sps"), 
                                                                    ("vehicle_decal2.sps", "vehicle_decal2.sps", "vehicle_decal2.sps"), 
                                                                    ("vehicle_detail.sps", "vehicle_detail.sps", "vehicle_detail.sps"), 
                                                                    ("vehicle_detail2.sps", "vehicle_detail2.sps", "vehicle_detail2.sps"), 
                                                                    ("vehicle_emissive_alpha.sps", "vehicle_emissive_alpha.sps", "vehicle_emissive_alpha.sps"), 
                                                                    ("vehicle_emissive_opaque.sps", "vehicle_emissive_opaque.sps", "vehicle_emissive_opaque.sps"), 
                                                                    ("vehicle_generic.sps", "vehicle_generic.sps", "vehicle_generic.sps"), 
                                                                    ("vehicle_interior.sps", "vehicle_interior.sps", "vehicle_interior.sps"), 
                                                                    ("vehicle_interior2.sps", "vehicle_interior2.sps", "vehicle_interior2.sps"), 
                                                                    ("vehicle_licenseplate.sps", "vehicle_licenseplate.sps", "vehicle_licenseplate.sps"), 
                                                                    ("vehicle_lightsemissive.sps", "vehicle_lightsemissive.sps", "vehicle_lightsemissive.sps"), 
                                                                    ("vehicle_mesh.sps", "vehicle_mesh.sps", "vehicle_mesh.sps"), 
                                                                    ("vehicle_mesh2_enveff.sps", "vehicle_mesh2_enveff.sps", "vehicle_mesh2_enveff.sps"), 
                                                                    ("vehicle_mesh_enveff.sps", "vehicle_mesh_enveff.sps", "vehicle_mesh_enveff.sps"), 
                                                                    ("vehicle_paint1.sps", "vehicle_paint1.sps", "vehicle_paint1.sps"), 
                                                                    ("vehicle_nosplash.sps", "vehicle_nosplash.sps", "vehicle_nosplash.sps"), 
                                                                    ("vehicle_nowater.sps", "vehicle_nowater.sps", "vehicle_nowater.sps"), 
                                                                    ("vehicle_paint1_enveff.sps", "vehicle_paint1_enveff.sps", "vehicle_paint1_enveff.sps"), 
                                                                    ("vehicle_paint2.sps", "vehicle_paint2.sps", "vehicle_paint2.sps"), 
                                                                    ("vehicle_paint2_enveff.sps", "vehicle_paint2_enveff.sps", "vehicle_paint2_enveff.sps"), 
                                                                    ("vehicle_paint3.sps", "vehicle_paint3.sps", "vehicle_paint3.sps"), 
                                                                    ("vehicle_paint3_enveff.sps", "vehicle_paint3_enveff.sps", "vehicle_paint3_enveff.sps"), 
                                                                    ("vehicle_paint3_lvr.sps", "vehicle_paint3_lvr.sps", "vehicle_paint3_lvr.sps"), 
                                                                    ("vehicle_paint4.sps", "vehicle_paint4.sps", "vehicle_paint4.sps"), 
                                                                    ("vehicle_paint4_emissive.sps", "vehicle_paint4_emissive.sps", "vehicle_paint4_emissive.sps"), 
                                                                    ("vehicle_paint4_enveff.sps", "vehicle_paint4_enveff.sps", "vehicle_paint4_enveff.sps"), 
                                                                    ("vehicle_paint5_enveff.sps", "vehicle_paint5_enveff.sps", "vehicle_paint5_enveff.sps"), 
                                                                    ("vehicle_paint6.sps", "vehicle_paint6.sps", "vehicle_paint6.sps"), 
                                                                    ("vehicle_paint6_enveff.sps", "vehicle_paint6_enveff.sps", "vehicle_paint6_enveff.sps"), 
                                                                    ("vehicle_paint7.sps", "vehicle_paint7.sps", "vehicle_paint7.sps"), 
                                                                    ("vehicle_paint7_enveff.sps", "vehicle_paint7_enveff.sps", "vehicle_paint7_enveff.sps"), 
                                                                    ("vehicle_paint8.sps", "vehicle_paint8.sps", "vehicle_paint8.sps"), 
                                                                    ("vehicle_paint9.sps", "vehicle_paint9.sps", "vehicle_paint9.sps"), 
                                                                    ("vehicle_shuts.sps", "vehicle_shuts.sps", "vehicle_shuts.sps"), 
                                                                    ("vehicle_tire.sps", "vehicle_tire.sps", "vehicle_tire.sps"), 
                                                                    ("vehicle_tire_emissive.sps", "vehicle_tire_emissive.sps", "vehicle_tire_emissive.sps"), 
                                                                    ("vehicle_track.sps", "vehicle_track.sps", "vehicle_track.sps"), 
                                                                    ("vehicle_track2.sps", "vehicle_track2.sps", "vehicle_track2.sps"), 
                                                                    ("vehicle_track2_emissive.sps", "vehicle_track2_emissive.sps", "vehicle_track2_emissive.sps"), 
                                                                    ("vehicle_track_ammo.sps", "vehicle_track_ammo.sps", "vehicle_track_ammo.sps"), 
                                                                    ("vehicle_track_emissive.sps", "vehicle_track_emissive.sps", "vehicle_track_emissive.sps"), 
                                                                    ("vehicle_lights.sps", "vehicle_lights.sps", "vehicle_lights.sps"), 
                                                                    ("vehicle_vehglass.sps", "vehicle_vehglass.sps", "vehicle_vehglass.sps"), 
                                                                    ("vehicle_vehglass_inner.sps", "vehicle_vehglass_inner.sps", "vehicle_vehglass_inner.sps"), 
                                                                    ("water_fountain.sps", "water_fountain.sps", "water_fountain.sps"), 
                                                                    ("water_poolenv.sps", "water_poolenv.sps", "water_poolenv.sps"), 
                                                                    ("water_river.sps", "water_river.sps", "water_river.sps"), 
                                                                    ("water_riverfoam.sps", "water_riverfoam.sps", "water_riverfoam.sps"), 
                                                                    ("water_riverlod.sps", "water_riverlod.sps", "water_riverlod.sps"), 
                                                                    ("water_riverocean.sps", "water_riverocean.sps", "water_riverocean.sps"), 
                                                                    ("water_rivershallow.sps", "water_rivershallow.sps", "water_rivershallow.sps"), 
                                                                    ("water_shallow.sps", "water_shallow.sps", "water_shallow.sps"), 
                                                                    ("water_terrainfoam.sps", "water_terrainfoam.sps", "water_terrainfoam.sps"), 
                                                                    ("weapon_emissivestrong_alpha.sps", "weapon_emissivestrong_alpha.sps", "weapon_emissivestrong_alpha.sps"), 
                                                                    ("weapon_emissive_tnt.sps", "weapon_emissive_tnt.sps", "weapon_emissive_tnt.sps"), 
                                                                    ("weapon_normal_spec_alpha.sps", "weapon_normal_spec_alpha.sps", "weapon_normal_spec_alpha.sps"), 
                                                                    ("weapon_normal_spec_cutout_palette.sps", "weapon_normal_spec_cutout_palette.sps", "weapon_normal_spec_cutout_palette.sps"), 
                                                                    ("weapon_normal_spec_detail_palette.sps", "weapon_normal_spec_detail_palette.sps", "weapon_normal_spec_detail_palette.sps"), 
                                                                    ("weapon_normal_spec_detail_tnt.sps", "weapon_normal_spec_detail_tnt.sps", "weapon_normal_spec_detail_tnt.sps"), 
                                                                    ("weapon_normal_spec_palette.sps", "weapon_normal_spec_palette.sps", "weapon_normal_spec_palette.sps"), 
                                                                    ("weapon_normal_spec_tnt.sps", "weapon_normal_spec_tnt.sps", "weapon_normal_spec_tnt.sps")])

#GIMS ONLY PROPERTY?
#bpy.types.ShaderNodeTexImage.type = EnumProperty(name = "Type", items = [("Regular", "Regular", "Regular"), ("Cube", "Cube", "Cube"), ("Volume", "Volume", "Volume")])
bpy.types.ShaderNodeTexImage.texture_name = StringProperty(name="Texture Name", default = "None")
bpy.types.ShaderNodeTexImage.format_type = EnumProperty(name = "Pixel Format", items = [("DXT1", "DXT1", "DXT1"), ("DXT3", "DXT3", "DXT3"), ("DXT5", "DXT5", "DXT5"), ("ATI1", "ATI1", "ATI1"), ("ATI2", "ATI2", "ATI2"), ("BC7", "BC7", "BC7"), ("A1R5G5B5", "A1R5G5B5", "A1R5G5B5"), ("A1R8G8B8", "A1R8G8B8", "A8R8G8B8"), ("A8R8G8B8", "A1R8G8B8", "A8R8G8B8"), ("A8", "A8", "A8"), ("L8", "L8", "L8")])
bpy.types.ShaderNodeTexImage.usage = EnumProperty(name = "Usage", items = [("TINTPALETTE", "TINTPALETTE", "TINTPALETTE"), ("UNKNOWN", "UNKNOWN", "UNKNOWN"), ("DEFAULT", "DEFAULT", "DEFAULT"), ("TERRAIN", "TERRAIN", "TERRAIN"), ("CLOUDDENSITY", "CLOUDDENSITY", "CLOUDDENSITY"), ("CLOUDNORMAL", "CLOUDNORMAL", "CLOUDNORMAL"), ("CABLE", "CABLE", "CABLE"), ("FENCE", "FENCE", "FENCE"), ("ENV.EFFECT", "ENV.EFFECT", "ENV.EFFECT"), ("SCRIPT", "SCRIPT", "SCRIPT"), ("WATERFLOW", "WATERFLOW", "WATERFLOW"), ("WATERFOAM", "WATERFOAM", "WATERFOAM"), ("WATERFOG", "WATERFOG", "WATERFOG"), ("WATEROCEAN", "WATEROCEAN", "WATEROCEAN"), ("WATER", "WATER", "WATER"), ("FOAMOPACITY", "FOAMOPACITY", "FOAMOPACITY"), ("FOAM", "FOAM", "FOAM"), ("DIFFUSEDETAIL", "DIFFUSEDETAIL", "DIFFUSEDETAIL"), ("DIFFUSEDARK", "DIFFUSEDARK", "DIFFUSEDARK"), ("DIFFUSEALPHAOPAQUE", "DIFFUSEALPHAOPAQUE", "DIFFUSEALPHAOPAQUE"), ("DIFFUSE", "DIFFUSE", "DIFFUSE"), ("DETAIL", "DETAIL", "DETAIL"), ("NORMAL", "NORMAL", "NORMAL"), ("SPECULAR", "SPECULAR", "SPECULAR"), ("EMMISIVE", "EMMISIVE", "EMMISIVE"), ("TINTPALLETE", "TINTPALLETE", "TINTPALLETE"), ("SKIPPROCCESING", "SKIPPROCCESING", "SKIPPROCCESING"), ("DONTOPTIMIZE", "DONTOPTIMIZE", "DONTOPTIMIZE"), ("TEST", "TEST", "TEST"), ("COUNT", "COUNT", "COUNT")])
bpy.types.ShaderNodeTexImage.extra_flags = IntProperty(name = "Extra Flags", default = 0)
bpy.types.ShaderNodeTexImage.embedded = BoolProperty(name = "Embedded", default = False)
#usage flags whatever this is 
bpy.types.ShaderNodeTexImage.not_half = BoolProperty(name = "NOT_HALF", default = False)
bpy.types.ShaderNodeTexImage.hd_split = BoolProperty(name = "HD_SPLIT", default = False)
bpy.types.ShaderNodeTexImage.x2 = BoolProperty(name = "X2", default = False)
bpy.types.ShaderNodeTexImage.x4 = BoolProperty(name = "X4", default = False)
bpy.types.ShaderNodeTexImage.y4 = BoolProperty(name = "Y4", default = False)
bpy.types.ShaderNodeTexImage.x8 = BoolProperty(name = "X8", default = False)
bpy.types.ShaderNodeTexImage.x16 = BoolProperty(name = "X16", default = False)
bpy.types.ShaderNodeTexImage.x32 = BoolProperty(name = "X32", default = False)
bpy.types.ShaderNodeTexImage.x64 = BoolProperty(name = "X64", default = False)
bpy.types.ShaderNodeTexImage.y64 = BoolProperty(name = "Y64", default = False)
bpy.types.ShaderNodeTexImage.x128 = BoolProperty(name = "X128", default = False)
bpy.types.ShaderNodeTexImage.x256 = BoolProperty(name = "X256", default = False)
bpy.types.ShaderNodeTexImage.x512 = BoolProperty(name = "X512", default = False)
bpy.types.ShaderNodeTexImage.y512 = BoolProperty(name = "Y512", default = False)
bpy.types.ShaderNodeTexImage.x1024 = BoolProperty(name = "X1024", default = False)
bpy.types.ShaderNodeTexImage.y1024 = BoolProperty(name = "Y1024", default = False)
bpy.types.ShaderNodeTexImage.x2048 = BoolProperty(name = "X2048", default = False)
bpy.types.ShaderNodeTexImage.y2048 = BoolProperty(name = "Y2048", default = False)
bpy.types.ShaderNodeTexImage.embeddedscriptrt = BoolProperty(name = "EMBEDDEDSCRIPTRT", default = False)
bpy.types.ShaderNodeTexImage.unk19 = BoolProperty(name = "UNK19", default = False)
bpy.types.ShaderNodeTexImage.unk20 = BoolProperty(name = "UNK20", default = False)
bpy.types.ShaderNodeTexImage.unk21 = BoolProperty(name = "UNK21", default = False)
bpy.types.ShaderNodeTexImage.flag_full = BoolProperty(name = "FLAG_FULL", default = False)
bpy.types.ShaderNodeTexImage.maps_half = BoolProperty(name = "MAPS_HALF", default = False)
bpy.types.ShaderNodeTexImage.unk24 = BoolProperty(name = "UNK24", default = False)

bpy.types.Material.sollumtype = EnumProperty(name = "Sollum Type", items = [("Blender", "Blender", "Blender"), ("GTA", "GTA", "GTA")], default = "Blender")

bpy.types.Object.bounds_length = bpy.props.FloatProperty(name="Length", default=1, min=0, max=100, update=bounds_update)
bpy.types.Object.bounds_radius = bpy.props.FloatProperty(name="Radius", default=1, min=0, max=100, update=bounds_update)
bpy.types.Object.bounds_rings = bpy.props.IntProperty(name="Rings", default=6, min=1, max=100, update=bounds_update)
bpy.types.Object.bounds_segments = bpy.props.IntProperty(name="Segments", default=12, min=3, max=100, update=bounds_update)
bpy.types.Object.bounds_bvh = bpy.props.BoolProperty(name="BVH (Bounding volume hierarchy)", default=False, update=bounds_update)



class SollumzBoneFlag(PropertyGroup):
    name: StringProperty(default="Unk0")

class SollumzBoneProperties(PropertyGroup):
    tag: IntProperty(name = "BoneTag", default = 0, min = 0)
    flags: CollectionProperty(type = SollumzBoneFlag)
    ul_flags_index: IntProperty(name = "UIListIndex", default = 0)

class SollumzDrawableDictExportables(PropertyGroup):
    drawable: PointerProperty(type = bpy.types.Object)

class SollumzDrawableDictProperties(PropertyGroup):
    exportables: CollectionProperty(type = SollumzDrawableDictExportables)
    ul_exportablesorder_index: IntProperty(name = "UIListIndex", default = 0)

classes = (
    SollumzBoneFlag,
    SollumzBoneProperties,
    SollumzDrawableDictExportables,
    SollumzDrawableDictProperties,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Bone.bone_properties = PointerProperty(type = SollumzBoneProperties)
    bpy.types.Object.drawable_dict_properties = PointerProperty(type = SollumzDrawableDictProperties)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    
    del bpy.types.Bone.bone_properties
    del bpy.types.Object.drawable_dict_properties