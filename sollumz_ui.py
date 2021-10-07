import bpy
from Sollumz.resources.bound import BoundType, PolygonType
from sollum_operators import *

SOLLUMZ_UI_NAMES = {
    BoundType.BOX: 'Bound Box',
    BoundType.SPHERE: 'Bound Sphere',
    BoundType.CAPSULE: 'Bound Capsule',
    BoundType.CYLINDER: 'Bound Cylinder',
    BoundType.DISC: 'Bound Disc',
    BoundType.CLOTH: 'Bound Cloth',
    BoundType.GEOMETRY: 'Bound Geometry',
    BoundType.GEOMETRYBVH: 'GeometryBVH',
    BoundType.COMPOSITE: 'Composite',

    PolygonType.BOX: 'Bound Poly Box',
    PolygonType.SPHERE: 'Bound Poly Sphere',
    PolygonType.CAPSULE: 'Bound Poly Capsule',
    PolygonType.CYLINDER: 'Bound Poly Cylinder',
    PolygonType.TRIANGLE: 'Bound Poly Mesh',
}

class SOLLUMZ_PT_MAT_PANEL(bpy.types.Panel):
    bl_label = "Material Properties"
    bl_idname = "SOLLUMZ_PT_MAT_PANEL"
    bl_category = "Sollumz"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    def draw_shader(self, layout, mat):
        
        layout.label(text = "Material Properties")
        box = layout.box()
        row = box.row()
        row.prop(mat.shader_properties, "renderbucket")
        row.prop(mat.shader_properties, "filename")

        layout.label(text = "Texture Parameters")
        nodes = mat.node_tree.nodes
        for n in nodes:   
            if(isinstance(n, bpy.types.ShaderNodeTexImage)):
                box = layout.box()
                row = box.row(align = True)
                row.label(text = "Texture Type: " + n.name)
                row.label(text = "Texture Name: " + n.image.name)
                row = box.row()
                row.prop(n.image, "filepath", text = "Texture Path")
                row = box.row(align = True)
                row.prop(n.texture_properties, "embedded")
                row.prop(n.texture_properties, "format")
                row.prop(n.texture_properties, "usage")
                #box = box.box()
                box.label(text = "Flags")
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
                row = box.row()
                row.prop(n.texture_properties, "unk24") 
                row.prop(n.texture_properties, "extra_flags")
        
        layout.label(text = "Shader Parameters")
        value_param_box = layout.box()

        for n in nodes:  # LOOP SERERATE SO TEXTURES SHOW ABOVE VALUE PARAMS
            if(isinstance(n, bpy.types.ShaderNodeValue)):
                if(n.name[-1] == "x"):
                    row = value_param_box.row()
                    row.label(text = n.name[:-2])    

                    x = n
                    y = mat.node_tree.nodes[n.name[:-1] + "y"]
                    z = mat.node_tree.nodes[n.name[:-1] + "z"]
                    w = mat.node_tree.nodes[n.name[:-1] + "w"]

                    row.prop(x.outputs[0], "default_value", text = "X:")
                    row.prop(y.outputs[0], "default_value", text = "Y:")
                    row.prop(z.outputs[0], "default_value", text = "Z:")
                    row.prop(w.outputs[0], "default_value", text = "W:")

    def draw_collision_material(self, layout, mat):
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

    def draw(self, context):
        layout = self.layout

        if(context.active_object == None):
            return

        mat = None
        mat = context.active_object.active_material

        if(mat == None):
            return 

        if(mat.sollum_type == "sollumz_gta_material"):
            self.draw_shader(layout, mat)
        elif(mat.sollum_type == "sollumz_gta_collision_material"):
            self.draw_collision_material(layout, mat)

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
        row.operator(SOLLUMZ_OT_create_collision_material.bl_idname).material_type = context.scene.create_collision_material_type
        row.prop(context.scene, "create_collision_material_type")
        box = layout.box()
        box.label(text = "Create Bound Objects")
        row = box.row()
        row.operator(SOLLUMZ_OT_create_bound_composite.bl_idname)
        row = box.row()
        row.operator(SOLLUMZ_OT_create_geometry_bound.bl_idname)
        row.operator(SOLLUMZ_OT_create_geometrybvh_bound.bl_idname)
        row = box.row()
        row.operator(SOLLUMZ_OT_create_box_bound.bl_idname)
        row.operator(SOLLUMZ_OT_create_sphere_bound.bl_idname)
        row = box.row()
        row.operator(SOLLUMZ_OT_create_capsule_bound.bl_idname)
        row.operator(SOLLUMZ_OT_create_cylinder_bound.bl_idname)
        row = box.row()
        row.operator(SOLLUMZ_OT_create_disc_bound.bl_idname)
        row.operator(SOLLUMZ_OT_create_cloth_bound.bl_idname)
        box = layout.box()
        box.label(text = "Create Polygon Bound Objects")
        row = box.row()
        row.operator(SOLLUMZ_OT_create_polygon_bound.bl_idname)
        row.prop(context.scene, "poly_bound_type")
        box = layout.box()
        box.label(text = "Quick Convert Tools")
        box.operator(SOLLUMZ_OT_quick_convert_mesh_to_collision.bl_idname)

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

class SOLLUMZ_UL_BONE_FLAGS(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index): 
        custom_icon = 'FILE'

        if self.layout_type in {'DEFAULT', 'COMPACT'}: 
            layout.prop(item, 'name', text='', icon = custom_icon, emboss=False, translate=False)
        elif self.layout_type in {'GRID'}: 
            layout.alignment = 'CENTER' 
            layout.prop(item, 'name', text='', icon = custom_icon, emboss=False, translate=False)

class SOLLUMZ_PT_BONE_PANEL(bpy.types.Panel):
    bl_label = "Bone Properties"
    bl_idname = "SOLLUMZ_PT_BONE_PANEL"
    bl_category = "Sollumz"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    #bl_context = "bone"
    
    def draw(self, context):
        layout = self.layout

        if (context.active_pose_bone == None):
            return

        bone = context.active_pose_bone.bone

        layout.prop(bone, "name", text = "Bone Name")
        layout.prop(bone.bone_properties, "tag", text = "BoneTag")

        layout.label(text="Flags")
        layout.template_list("SOLLUMZ_UL_BONE_FLAGS", "Flags", bone.bone_properties, "flags", bone.bone_properties, "ul_index")
        row = layout.row() 
        row.operator('sollumz.bone_flags_new_item', text='New')
        row.operator('sollumz.bone_flags_delete_item', text='Delete')

class SOLLUMZ_MT_sollumz(bpy.types.Menu):
    bl_label = "Sollumz"
    bl_idname = "SOLLUMZ_MT_sollumz"

    def draw(self, context):
        layout = self.layout

def SollumzContextMenu(self, context):
    self.layout.menu(SOLLUMZ_MT_sollumz.bl_idname)

class SOLLUMZ_MT_create(bpy.types.Menu):
    bl_label = "Create"
    bl_idname = "SOLLUMZ_MT_create"

    def draw(self, context):
        layout = self.layout

def SollumzCreateContextMenu(self, context):
    self.layout.menu(SOLLUMZ_MT_create.bl_idname)

class SOLLUMZ_MT_bound_objects_create(bpy.types.Menu):
    bl_label = "Bound Objects"
    bl_idname = "SOLLUMZ_MT_bound_objects_create"

    def draw(self, context):
        layout = self.layout
        layout.operator(SOLLUMZ_OT_create_bound_composite.bl_idname)
        layout.operator(SOLLUMZ_OT_create_geometry_bound.bl_idname)
        layout.operator(SOLLUMZ_OT_create_geometrybvh_bound.bl_idname)
        layout.operator(SOLLUMZ_OT_create_box_bound.bl_idname)
        layout.operator(SOLLUMZ_OT_create_sphere_bound.bl_idname)
        layout.operator(SOLLUMZ_OT_create_capsule_bound.bl_idname)
        layout.operator(SOLLUMZ_OT_create_cylinder_bound.bl_idname)
        layout.operator(SOLLUMZ_OT_create_disc_bound.bl_idname)
        layout.operator(SOLLUMZ_OT_create_cloth_bound.bl_idname)

def SollumzBoundContextMenu(self, context):
    self.layout.menu(SOLLUMZ_MT_bound_objects_create.bl_idname)

class SOLLUMZ_MT_polygon_bound_create(bpy.types.Menu):
    bl_label = "Polygon Bound Objects"
    bl_idname = "SOLLUMZ_MT_polygon_bound_create"

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene, "poly_bound_type")
        layout.operator(SOLLUMZ_OT_create_polygon_bound.bl_idname) 

def SollumzPolygonBoundContextMenu(self, context):
    self.layout.menu(SOLLUMZ_MT_polygon_bound_create.bl_idname)