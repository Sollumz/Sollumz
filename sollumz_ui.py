import bpy

class SollumzMainPanel(bpy.types.Panel):
    bl_label = "Sollumz"
    bl_idname = "SOLLUMZ_PT_MAIN_PANEL"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout

        object = context.active_object
                
        if(object == None):
            layout.label(text = "No objects in scene")            
        else:
            mainbox = layout.box()
            
            textbox = mainbox.box()
            textbox.prop(object, "name", text = "Object Name")
            
            subbox = mainbox.box() 
            subbox.props_enum(object, "sollumtype")
            
            if(object.sollumtype == "Drawable"):
                box = mainbox.box()
                row = box.row()
                box.prop(object, "drawble_distance_high")
                box.prop(object, "drawble_distance_medium")
                row = box.row()
                box.prop(object, "drawble_distance_low")
                box.prop(object, "drawble_distance_vlow")
            if(object.sollumtype == "Geometry"):
                box = mainbox.box()
                box.prop(object, "level_of_detail")
                box.prop(object, "mask")   
        
        box = layout.box()
        box.label(text = "Tools") 
        
def param_name_to_title(pname):
    
    title = ""
    
    a = pname.split("_")
    b = a[0]
    glue = ' '
    c = ''.join(glue + x if x.isupper() else x for x in b).strip(glue).split(glue)
    d = ""
    for word in c:
        d += word
        d += " "
    title = d.title() #+ a[1].upper() dont add back the X, Y, Z, W
    
    return title

class SollumzMaterialPanel(bpy.types.Panel):
    bl_label = "Sollumz Material Panel"
    bl_idname = "Sollumz_PT_MAT_PANEL"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "material"
    
    shadername : bpy.props.StringProperty(default = "default.sps")
    
    def draw(self, context):
        layout = self.layout

        object = context.active_object        
        if(object == None):
            return
        mat = object.active_material  
        
        tbox = layout.box()
        tbox.label(text = "Tools")
        box = tbox.box()
        box.label(text = "Create Shader")
        row = box.row()  
        row.label(text = "Shader Type:")
        row.prop_menu_enum(object, "shadertype", text = object.shadertype)
        box.operator("sollum.createvshader").shadername = object.shadertype
        
        if(mat == None):
            return
        
        if(mat.sollumtype == "Blender"):
            box = tbox.box()
            row = box.row()
            row.label(text = "Convert To Shader")
            row.operator("sollum.converttov") 
        
        
        if(mat.sollumtype == "GTA"):
            
            box = layout.box()
            box.prop(mat, "name", text = "Shader")
            
            #layout.label(text = "Parameters")
            
            #box = layout.box()
            #box.label(text = "Parameters")
            
            mat_nodes = mat.node_tree.nodes
            
            image_nodes = []
            value_nodes = []
            
            for n in mat_nodes:
                if(isinstance(n, bpy.types.ShaderNodeTexImage)):
                    image_nodes.append(n)
                elif(isinstance(n, bpy.types.ShaderNodeValue)):
                    value_nodes.append(n)
                #else:
            
            for n in image_nodes:
                box = box.box()
                box.label(text = n.name + " Texture")
                
                row = box.row()
                if(n.image != None):
                    row.prop(n.image, "filepath")
                row.prop(n, "embedded")
                
                row = box.row()
                #row.prop(specnode, "type") #gims fault
                row.prop(n, "format_type")
                
                #row = box.row() #gims fault
                row.prop(n, "usage")
                
                uf_box = box.box()
                uf_box.label(text = "Usage Flags:")
                uf_row = uf_box.row()
                uf_row.prop(n, "not_half")
                uf_row.prop(n, "hd_split")
                uf_row.prop(n, "full")
                uf_row.prop(n, "maps_half")
                uf_box.prop(n, "extra_flags")
                
            prevname = ""
            #value_nodes.insert(1, value_nodes.pop(len(value_nodes) - 1)) #shift last item to second because params are messed up for some reason ? (fixed?)
            for n in value_nodes:
                if(n.name[:-2] not in prevname):
                    #new parameter
                    parambox = box.box()
                    parambox.label(text = param_name_to_title(n.name)) 
                      
                parambox.prop(n.outputs[0], "default_value", text = n.name[-1].upper())
                
                prevname = n.name 
            
        
        
        
            
#sollum properties
bpy.types.Object.sollumtype = bpy.props.EnumProperty(
                                                        name = "Vtype", 
                                                        default = "None",
                                                        items = [
                                                                    ("None", "None", "None"),
                                                                    ("Drawable", "Drawable", "Drawable"), 
                                                                    ("Geometry", "Geometry", "Geometry"),
                                                                    ("Bound Composite", "Bound Composite", "Bound Composite"),
                                                                    ("Bound Box", "Bound Box", "Bound Box"),
                                                                    ("Bound Triangle", "Bound Triangle", "Bound Triangle"), 
                                                                    ("Bound Sphere", "Bound Sphere", "Bound Sphere"),
                                                                    ("Bound Capsule", "Bound Capsule", "Bound Capsule"),
                                                                    ("Bound Disc", "Bound Disc", "Bound Disc")])
                                                                    
bpy.types.Object.level_of_detail = bpy.props.EnumProperty(name = "Level Of Detail", items = [("High", "High", "High"), ("Medium", "Medium", "Medium"), ("Low", "Low", "Low"), ("Very Low", "Very Low", "Very Low")])
bpy.types.Object.mask = bpy.props.IntProperty(name = "Mask", default = 255)
bpy.types.Object.drawble_distance_high = bpy.props.FloatProperty(name = "Lod Distance High", default = 9998.0, min = 0, max = 100000)
bpy.types.Object.drawble_distance_medium = bpy.props.FloatProperty(name = "Lod Distance Medium", default = 9998.0, min = 0, max = 100000)
bpy.types.Object.drawble_distance_low = bpy.props.FloatProperty(name = "Lod Distance Low", default = 9998.0, min = 0, max = 100000)
bpy.types.Object.drawble_distance_vlow = bpy.props.FloatProperty(name = "Lod Distance vlow", default = 9998.0, min = 0, max = 100000)
bpy.types.Object.shadertype = bpy.props.EnumProperty(
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
#bpy.types.ShaderNodeTexImage.type = bpy.props.EnumProperty(name = "Type", items = [("Regular", "Regular", "Regular"), ("Cube", "Cube", "Cube"), ("Volume", "Volume", "Volume")])
bpy.types.ShaderNodeTexImage.format_type = bpy.props.EnumProperty(name = "Pixel Format", items = [("DXT1", "DXT1", "DXT1"), ("DXT3", "DXT3", "DXT3"), ("DXT5", "DXT5", "DXT5"), ("ATI1", "ATI1", "ATI1"), ("ATI2", "ATI2", "ATI2"), ("BC7", "BC7", "BC7"), ("A1R5G5B5", "A1R5G5B5", "A1R5G5B5"), ("A1R8G8B8", "A1R8G8B8", "A8R8G8B8"), ("A8R8G8B8", "A1R8G8B8", "A8R8G8B8"), ("A8", "A8", "A8"), ("L8", "L8", "L8")])
bpy.types.ShaderNodeTexImage.usage = bpy.props.EnumProperty(name = "Usage", items = [("TINTPALETTE", "TINTPALETTE", "TINTPALETTE"), ("UNKNOWN", "UNKNOWN", "UNKNOWN"), ("DEFAULT", "DEFAULT", "DEFAULT"), ("TERRAIN", "TERRAIN", "TERRAIN"), ("CLOUDDENSITY", "CLOUDDENSITY", "CLOUDDENSITY"), ("CLOUDNORMAL", "CLOUDNORMAL", "CLOUDNORMAL"), ("CABLE", "CABLE", "CABLE"), ("FENCE", "FENCE", "FENCE"), ("ENV.EFFECT", "ENV.EFFECT", "ENV.EFFECT"), ("SCRIPT", "SCRIPT", "SCRIPT"), ("WATERFLOW", "WATERFLOW", "WATERFLOW"), ("WATERFOAM", "WATERFOAM", "WATERFOAM"), ("WATERFOG", "WATERFOG", "WATERFOG"), ("WATEROCEAN", "WATEROCEAN", "WATEROCEAN"), ("WATER", "WATER", "WATER"), ("FOAMOPACITY", "FOAMOPACITY", "FOAMOPACITY"), ("FOAM", "FOAM", "FOAM"), ("DIFFUSEDETAIL", "DIFFUSEDETAIL", "DIFFUSEDETAIL"), ("DIFFUSEDARK", "DIFFUSEDARK", "DIFFUSEDARK"), ("DIFFUSEALPHAOPAQUE", "DIFFUSEALPHAOPAQUE", "DIFFUSEALPHAOPAQUE"), ("DIFFUSE", "DIFFUSE", "DIFFUSE"), ("DETAIL", "DETAIL", "DETAIL"), ("NORMAL", "NORMAL", "NORMAL"), ("SPECULAR", "SPECULAR", "SPECULAR"), ("EMMISIVE", "EMMISIVE", "EMMISIVE"), ("TINTPALLETE", "TINTPALLETE", "TINTPALLETE"), ("SKIPPROCCESING", "SKIPPROCCESING", "SKIPPROCCESING"), ("DONTOPTIMIZE", "DONTOPTIMIZE", "DONTOPTIMIZE"), ("TEST", "TEST", "TEST"), ("COUNT", "COUNT", "COUNT")])
bpy.types.ShaderNodeTexImage.extra_flags = bpy.props.IntProperty(name = "Extra Flags", default = 0)
bpy.types.ShaderNodeTexImage.embedded = bpy.props.BoolProperty(name = "Embedded", default = False)
#usage flags whatever this is 
bpy.types.ShaderNodeTexImage.not_half    = bpy.props.BoolProperty(name = "Not Half", default = False)
bpy.types.ShaderNodeTexImage.hd_split = bpy.props.BoolProperty(name = "HD Split", default = False)
bpy.types.ShaderNodeTexImage.full = bpy.props.BoolProperty(name = "Full", default = False)
bpy.types.ShaderNodeTexImage.maps_half = bpy.props.BoolProperty(name = "Maps Half", default = False)

bpy.types.Material.sollumtype = bpy.props.EnumProperty(name = "Sollum Type", items = [("Blender", "Blender", "Blender"), ("GTA", "GTA", "GTA")], default = "Blender")

def register():
    bpy.utils.register_class(SollumzMaterialPanel)
    bpy.utils.register_class(SollumzMainPanel)
def unregister():
    bpy.utils.unregister_class(SollumzMaterialPanel)
    bpy.utils.unregister_class(SollumzMainPanel)
