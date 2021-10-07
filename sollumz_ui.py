import bpy

class SOLLUMZ_PT_SHADER_PANEL(bpy.types.Panel):
    bl_label = "Sollumz Shader Panel"
    bl_idname = "SOLLUMZ_PT_SHADER_PANEL"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Item"

    def draw(self, context):
        layout = self.layout

        nodes = context.selected_nodes

        if(bpy.context.active_object != None):
            mat = bpy.context.active_object.data.materials[0]
        else:
            return

        for n in nodes:
            if(isinstance(n, bpy.types.ShaderNodeTexImage)):
                box = layout.box()
                box.prop(n, "image")
                row = box.row()
                row.prop(n.texture_properties, "embedded")
                row.prop(n.texture_properties, "format")
                row.prop(n.texture_properties, "extra_flags")
                row.prop(n.texture_properties, "usage")
                box = box.box()
                row = box.row()
                row.prop(n.texture_properties, "not_half")
                row.prop(n.texture_properties, "hd_split")
                row.prop(n.texture_properties, "flag_full")
                row.prop(n.texture_properties, "maps_half")
                row = box.row()
                row.prop(n.texture_properties, "x2")
                row.prop(n.texture_properties, "x4")
                row.prop(n.texture_properties, "y4")
                row.prop(n.texture_properties, "x8")
                row = box.row()
                row.prop(n.texture_properties, "x16")
                row.prop(n.texture_properties, "x32")
                row.prop(n.texture_properties, "x64")
                row.prop(n.texture_properties, "y64")
                row = box.row()
                row.prop(n.texture_properties, "x128")
                row.prop(n.texture_properties, "x256")
                row.prop(n.texture_properties, "x512")
                row.prop(n.texture_properties, "y512")
                row = box.row()
                row.prop(n.texture_properties, "x1024")
                row.prop(n.texture_properties, "y1024")
                row.prop(n.texture_properties, "x2048")
                row.prop(n.texture_properties, "y2048")
                row = box.row()
                row.prop(n.texture_properties, "embeddedscriptrt")
                row.prop(n.texture_properties, "unk19")
                row.prop(n.texture_properties, "unk20")
                row.prop(n.texture_properties, "unk21")
                row.prop(n.texture_properties, "unk24") 

            if(isinstance(n, bpy.types.ShaderNodeValue)):
                i = 0
                box = layout.box()
                for n in mat.node_tree.nodes:
                    if(isinstance(n, bpy.types.ShaderNodeValue)):
                        if(i == 4):
                            box = layout.box()
                            i = 0

                        #fix variable name for display
                        n_array = n.name.split('_')
                        name = n_array[0].capitalize()
                        letter = n_array[1].upper()
                        label = name + " " + letter
                        box.label(text = label)
                        
                        row = box.row()
                        row.prop(n.outputs[0], "default_value")
                        i += 1

class SOLLUMZ_PT_MAT_PANEL(bpy.types.Panel):
    bl_label = "Material Properties"
    bl_idname = "SOLLUMZ_PT_MAT_PANEL"
    bl_category = "Sollumz"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    def draw(self, context):
        layout = self.layout

        if(bpy.context.active_object == None):
            return

        mat = None
        mat = bpy.context.active_object.active_material

        if(mat == None):
            return 

        if(mat.sollum_type == "sollumz_gta_material"):
            box = layout.box()
            row = box.row()
            row.prop(mat.shader_properties, "renderbucket")
            row.prop(mat.shader_properties, "filename")
        elif(mat.sollum_type == "sollumz_gta_collision_material"):
            box = layout.box()
            row = box.row()
            #do this for material type? 
            #row.enabled = False
            row = box.row()
            row.prop(mat.collision_properties, "procedural_id")
            row.prop(mat.collision_properties, "room_id")
            row = box.row()
            row.prop(mat.collision_properties, "ped_density")
            row.prop(mat.collision_properties, "material_color_index")
            box = box.box()
            box.label(text = "Flags")            
            row = box.row()
            row.prop(mat.collision_flags, "stairs")
            row.prop(mat.collision_flags, "not_climbable")
            row.prop(mat.collision_flags, "see_through")
            row.prop(mat.collision_flags, "shoot_through")
            row = box.row()
            row.prop(mat.collision_flags, "not_cover")
            row.prop(mat.collision_flags, "walkable_path")
            row.prop(mat.collision_flags, "no_cam_collision")
            row.prop(mat.collision_flags, "shoot_through_fx")
            row = box.row()
            row.prop(mat.collision_flags, "no_decal")
            row.prop(mat.collision_flags, "no_navmesh")
            row.prop(mat.collision_flags, "no_ragdoll")
            row.prop(mat.collision_flags, "vehicle_wheel")
            row = box.row()
            row.prop(mat.collision_flags, "no_ptfx")
            row.prop(mat.collision_flags, "too_steep_for_player")
            row.prop(mat.collision_flags, "no_network_spawn")
            row.prop(mat.collision_flags, "no_cam_collision_allow_clipping")

class SOLLUMZ_PT_COLLISION_TOOL_PANEL(bpy.types.Panel):
    bl_label = "Ybn Tools"
    bl_idname = "SOLLUMZ_PT_COLLISION_TOOL_PANEL"
    bl_category = "Sollumz"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        box.label(text = "Create Material")
        row = box.row()
        row.operator("sollumz.createcollisionmaterial").material_type = context.scene.create_collision_material_type
        row.prop(context.scene, "create_collision_material_type")
        box = layout.box()
        box.label(text = "Create Collision Objects")
        row = box.row()
        row.operator("sollumz.createboundcomposite")
        row.operator("sollumz.creategeometrybound")
        row = box.row()
        row.operator("sollumz.creategeometryboundbvh")
        row.operator("sollumz.createboxbound")
        row = box.row()
        row.operator("sollumz.createspherebound")
        row.operator("sollumz.createcapsulebound")
        row = box.row()
        row.operator("sollumz.createcylinderbound")
        row.operator("sollumz.creatediscbound")
        row = box.row()
        row.operator("sollumz.createclothbound")
        row = box.row()
        row.operator("sollumz.createpolygonbound")
        row.prop(context.scene, "poly_bound_type")
        
class SOLLUMZ_PT_MAIN_PANEL(bpy.types.Panel):
    bl_label = "Object Properties"
    bl_idname = "SOLLUMZ_PT_MAIN_PANEL"
    bl_category = "Sollumz"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    def draw_drawable_properties(self, context, layout, obj):
        layout.prop(obj.drawable_properties, "lod_dist_high")
        layout.prop(obj.drawable_properties, "lod_dist_med")
        layout.prop(obj.drawable_properties, "lod_dist_low")
        layout.prop(obj.drawable_properties, "lod_dist_vlow")
    
    def draw_drawable_model_properties(self, context, layout, obj):
        layout.prop(obj.drawable_model_properties, "render_mask")
        layout.prop(obj.drawable_model_properties, "flags")
        layout.prop(obj.drawable_model_properties, "sollum_lod")

    def draw_bound_properties(self, context, layout, obj):
        if("poly" not in obj.sollum_type):
            row = layout.row()
            row.prop(obj.bound_properties, "procedural_id")
            row.prop(obj.bound_properties, "room_id")
            row = layout.row()
            row.prop(obj.bound_properties, "ped_density")
            row.prop(obj.bound_properties, "poly_flags")

        if("poly" not in obj.sollum_type and obj.sollum_type != "sollumz_bound_composite"):
            #flags1
            box = layout.box()
            box.label(text = "Composite Flags 1")
            row = box.row()
            row.prop(obj.composite_flags1, "unknown")
            row.prop(obj.composite_flags1, "map_weapon")
            row.prop(obj.composite_flags1, "map_dynamic")
            row.prop(obj.composite_flags1, "map_animal")
            row = box.row()
            row.prop(obj.composite_flags1, "map_cover")
            row.prop(obj.composite_flags1, "map_vehicle")
            row.prop(obj.composite_flags1, "vehicle_not_bvh")
            row.prop(obj.composite_flags1, "vehicle_bvh")
            row = box.row()
            row.prop(obj.composite_flags1, "ped")
            row.prop(obj.composite_flags1, "ragdoll")
            row.prop(obj.composite_flags1, "animal")
            row.prop(obj.composite_flags1, "animal_ragdoll")
            row = box.row()
            row.prop(obj.composite_flags1, "object")
            row.prop(obj.composite_flags1, "object_env_cloth")
            row.prop(obj.composite_flags1, "plant")
            row.prop(obj.composite_flags1, "projectile")
            row = box.row()
            row.prop(obj.composite_flags1, "explosion")
            row.prop(obj.composite_flags1, "pickup")
            row.prop(obj.composite_flags1, "foliage")
            row.prop(obj.composite_flags1, "forklift_forks")
            row = box.row()
            row.prop(obj.composite_flags1, "test_weapon")
            row.prop(obj.composite_flags1, "test_camera")
            row.prop(obj.composite_flags1, "test_ai")
            row.prop(obj.composite_flags1, "test_script")
            row = box.row()
            row.prop(obj.composite_flags1, "test_vehicle_wheel")
            row.prop(obj.composite_flags1, "glass")
            row.prop(obj.composite_flags1, "map_river")
            row.prop(obj.composite_flags1, "smoke")
            row = box.row()
            row.prop(obj.composite_flags1, "unsmashed")
            row.prop(obj.composite_flags1, "map_stairs")
            row.prop(obj.composite_flags1, "map_deep_surface")
            #flags2
            box = layout.box()
            box.label(text = "Composite Flags 2")
            row = box.row()
            row.prop(obj.composite_flags2, "unknown")
            row.prop(obj.composite_flags2, "map_weapon")
            row.prop(obj.composite_flags2, "map_dynamic")
            row.prop(obj.composite_flags2, "map_animal")
            row = box.row()
            row.prop(obj.composite_flags2, "map_cover")
            row.prop(obj.composite_flags2, "map_vehicle")
            row.prop(obj.composite_flags2, "vehicle_not_bvh")
            row.prop(obj.composite_flags2, "vehicle_bvh")
            row = box.row()
            row.prop(obj.composite_flags2, "ped")
            row.prop(obj.composite_flags2, "ragdoll")
            row.prop(obj.composite_flags2, "animal")
            row.prop(obj.composite_flags2, "animal_ragdoll")
            row = box.row()
            row.prop(obj.composite_flags2, "object")
            row.prop(obj.composite_flags2, "object_env_cloth")
            row.prop(obj.composite_flags2, "plant")
            row.prop(obj.composite_flags2, "projectile")
            row = box.row()
            row.prop(obj.composite_flags2, "explosion")
            row.prop(obj.composite_flags2, "pickup")
            row.prop(obj.composite_flags2, "foliage")
            row.prop(obj.composite_flags2, "forklift_forks")
            row = box.row()
            row.prop(obj.composite_flags2, "test_weapon")
            row.prop(obj.composite_flags2, "test_camera")
            row.prop(obj.composite_flags2, "test_ai")
            row.prop(obj.composite_flags2, "test_script")
            row = box.row()
            row.prop(obj.composite_flags2, "test_vehicle_wheel")
            row.prop(obj.composite_flags2, "glass")
            row.prop(obj.composite_flags2, "map_river")
            row.prop(obj.composite_flags2, "smoke")
            row = box.row()
            row.prop(obj.composite_flags2, "unsmashed")
            row.prop(obj.composite_flags2, "map_stairs")
            row.prop(obj.composite_flags2, "map_deep_surface")
    
    def draw(self, context):
        layout = self.layout

        obj = bpy.context.active_object

        if(obj == None):
            return

        box = layout.box()
        row = box.row()
        row.enabled = False
        row.prop(obj, "sollum_type")

        if(obj.sollum_type == "sollumz_drawable"):
            self.draw_drawable_properties(context, box, obj)
        elif(obj.sollum_type == "sollumz_drawable_model"):
            self.draw_drawable_model_properties(context, box, obj)
        elif("bound" in obj.sollum_type):
            self.draw_bound_properties(context, box, obj)