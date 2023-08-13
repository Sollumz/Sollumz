import bpy
from bpy.types import Context
from . import operators as ydr_ops
from .shader_materials import shadermats
from ..sollumz_ui import SOLLUMZ_PT_OBJECT_PANEL, SOLLUMZ_PT_MAT_PANEL
from ..sollumz_properties import SollumType, MaterialType, LightType, SOLLUMZ_UI_NAMES
from ..sollumz_ui import FlagsPanel, TimeFlagsPanel
from ..sollumz_helper import find_sollumz_parent


class SOLLUMZ_PT_DRAWABLE_PANEL(bpy.types.Panel):
    bl_label = "Drawable Properties"
    bl_idname = "SOLLUMZ_PT_DRAWABLE_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_options = {"HIDE_HEADER"}
    bl_parent_id = SOLLUMZ_PT_OBJECT_PANEL.bl_idname

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.sollum_type == SollumType.DRAWABLE

    def draw(self, context):
        layout = self.layout
        layout.use_property_decorate = False
        layout.use_property_split = True

        obj = context.active_object

        layout.prop(obj.drawable_properties, "lod_dist_high")
        layout.prop(obj.drawable_properties, "lod_dist_med")
        layout.prop(obj.drawable_properties, "lod_dist_low")
        layout.prop(obj.drawable_properties, "lod_dist_vlow")

        layout.separator()

        layout.operator("sollumz.order_shaders", icon="MATERIAL")


class SOLLUMZ_UL_SHADER_ORDER_LIST(bpy.types.UIList):
    bl_idname = "SOLLUMZ_UL_SHADER_ORDER_LIST"

    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        row = layout.row()
        col = row.column()
        col.label(text=f"{item.index}: {item.name}", icon="MATERIAL")

        col = row.column()
        col.enabled = False
        col.label(text=item.filename)

    def draw_filter(self, context, layout):
        ...

    def filter_items(self, context, data, propname):
        items = getattr(data, propname)

        ordered = [item.index for item in items]
        filtered = [self.bitflag_filter_item] * len(items)

        return filtered, ordered


class SOLLUMZ_PT_DRAWABLE_MODEL_PANEL(bpy.types.Panel):
    bl_label = "LOD Properties"
    bl_idname = "SOLLUMZ_PT_DRAWABLE_MODEL_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_OBJECT_PANEL.bl_idname

    @classmethod
    def poll(cls, context):
        obj = context.active_object

        if obj is None:
            return False

        active_lod = obj.sollumz_lods.active_lod
        sollumz_parent = find_sollumz_parent(
            obj, parent_type=SollumType.DRAWABLE)

        return active_lod is not None and obj.sollum_type == SollumType.DRAWABLE_MODEL and obj.type == "MESH" and sollumz_parent is not None

    def draw(self, context):
        layout = self.layout
        layout.use_property_decorate = False
        layout.use_property_split = True

        obj = context.active_object
        active_lod_level = obj.sollumz_lods.active_lod.level
        mesh = obj.data
        sollumz_parent = find_sollumz_parent(
            obj, parent_type=SollumType.DRAWABLE)

        model_props = mesh.drawable_model_properties

        col = layout.column()
        col.alignment = "RIGHT"
        col.enabled = False

        is_skinned_model = obj.vertex_groups and sollumz_parent is not None and not obj.sollumz_is_physics_child_mesh

        # All skinned objects (objects with vertex groups) go in the same drawable model
        if is_skinned_model:
            model_props = sollumz_parent.skinned_model_properties.get_lod(
                active_lod_level)

            col.label(
                text=f"Active LOD: {SOLLUMZ_UI_NAMES[active_lod_level]} (Skinned)")
        else:
            col.label(
                text=f"Active LOD: {SOLLUMZ_UI_NAMES[active_lod_level]}")

        col.separator()

        layout.prop(model_props, "render_mask")
        layout.prop(model_props, "unknown_1")
        layout.prop(model_props, "flags")


class SOLLUMZ_UL_SHADER_MATERIALS_LIST(bpy.types.UIList):
    bl_idname = "SOLLUMZ_UL_SHADER_MATERIALS_LIST"

    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        name = shadermats[item.index].ui_name
        # If the object is selected
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            row = layout.row()
            row.label(text=name, icon="SHADING_TEXTURE")
        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.prop(item, "name",
                        text=name, emboss=False, icon="SHADING_TEXTURE")


class SOLLUMZ_PT_LIGHT_PANEL(bpy.types.Panel):
    bl_label = "Sollumz"
    bl_idname = "SOLLUMZ_PT_LIGHT_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        return context.light and context.active_object.sollum_type == SollumType.LIGHT

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        light = context.light
        row = layout.row()
        row.enabled = light.sollum_type != LightType.NONE
        row.prop(light, "sollum_type")
        if light.sollum_type == LightType.NONE:
            return
        layout.separator()
        layout.prop(light.light_properties, "light_hash")
        layout.prop(light.light_properties, "group_id")
        layout.prop(light.light_properties, "projected_texture_hash")
        layout.separator()
        layout.prop(light.light_properties, "flashiness")
        if light.sollum_type == LightType.CAPSULE:
            layout.separator()
            layout.prop(light.light_properties, "extent")
        layout.separator()
        layout.prop(light.light_properties, "volume_size_scale")
        layout.prop(light.light_properties, "volume_outer_color")
        layout.prop(light.light_properties, "volume_outer_intensity")
        layout.prop(light.light_properties, "volume_outer_exponent")
        layout.separator()
        layout.prop(light.light_properties, "light_fade_distance")
        layout.prop(light.light_properties, "shadow_fade_distance")
        layout.prop(light.light_properties, "specular_fade_distance")
        layout.prop(light.light_properties, "volumetric_fade_distance")
        layout.separator()
        layout.prop(light.light_properties, "culling_plane_normal")
        layout.prop(light.light_properties, "culling_plane_offset")
        layout.separator()
        layout.prop(light.light_properties, "corona_size")
        layout.prop(light.light_properties, "corona_intensity")
        layout.prop(light.light_properties, "corona_z_bias")
        layout.separator()
        layout.prop(light.light_properties, "unknown_45")
        layout.prop(light.light_properties, "unknown_46")
        layout.separator()
        layout.prop(light.light_properties, "shadow_blur")


class SOLLUMZ_PT_LIGHT_TIME_FLAGS_PANEL(TimeFlagsPanel, bpy.types.Panel):
    bl_idname = "SOLLUMZ_PT_LIGHT_TIME_FLAGS_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"
    bl_parent_id = SOLLUMZ_PT_LIGHT_PANEL.bl_idname
    select_operator = "sollumz.light_time_flags_select_range"
    clear_operator = "sollumz.light_time_flags_clear"

    @classmethod
    def poll(self, context):
        return context.light is not None

    def get_flags(self, context):
        light = context.light
        return light.time_flags


class SOLLUMZ_PT_LIGHT_FLAGS_PANEL(FlagsPanel, bpy.types.Panel):
    bl_label = "Flags"
    bl_idname = "SOLLUMZ_PT_LIGHT_FLAGS_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"
    bl_parent_id = SOLLUMZ_PT_LIGHT_PANEL.bl_idname

    @classmethod
    def poll(self, context):
        return context.light is not None

    def get_flags(self, context):
        light = context.light
        return light.light_flags


class SOLLUMZ_PT_DRAWABLE_TOOL_PANEL(bpy.types.Panel):
    bl_label = "Drawables"
    bl_idname = "SOLLUMZ_PT_DRAWABLE_TOOL_PANEL"
    bl_category = "Sollumz Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 1

    def draw_header(self, context):
        # Example property to display a checkbox, can be anything
        self.layout.label(text="", icon="MESH_CUBE")

    def draw(self, context):
        pass


class SOLLUMZ_PT_SHADER_TOOLS_PANEL(bpy.types.Panel):
    bl_label = "Shader Tools"
    bl_idname = "SOLLUMZ_PT_SHADER_TOOLS_PANEL"
    bl_category = "Sollumz Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_DRAWABLE_TOOL_PANEL.bl_idname

    bl_order = 1

    def draw_header(self, context):
        self.layout.label(text="", icon="TOOL_SETTINGS")

    def draw(self, context):
        layout = self.layout
        layout.label(text="Create")
        layout.template_list(
            SOLLUMZ_UL_SHADER_MATERIALS_LIST.bl_idname, "", context.scene, "shader_materials", context.scene, "shader_material_index"
        )
        row = layout.row()
        row.operator(
            ydr_ops.SOLLUMZ_OT_create_shader_material.bl_idname, text="Create Shader Material")
        grid = layout.grid_flow(align=True)
        grid.operator(ydr_ops.SOLLUMZ_OT_convert_material_to_selected.bl_idname,
                      text="Convert Active Material", icon="FILE_REFRESH")
        grid.operator(
            ydr_ops.SOLLUMZ_OT_convert_allmaterials_to_selected.bl_idname, text="Convert All Materials")

        layout.separator()
        layout.label(text="Tools")

        row = layout.row()
        row.operator(
            ydr_ops.SOLLUMZ_OT_auto_convert_material.bl_idname, text="Auto Convert", icon="FILE_REFRESH")
        grid = layout.grid_flow(align=True)
        grid.operator(
            ydr_ops.SOLLUMZ_OT_set_all_textures_embedded.bl_idname, icon="TEXTURE")
        grid.operator(
            ydr_ops.SOLLUMZ_OT_remove_all_textures_embedded.bl_idname)
        grid = layout.grid_flow(align=True)
        grid.operator(
            ydr_ops.SOLLUMZ_OT_set_all_materials_embedded.bl_idname, icon="MATERIAL")
        grid.operator(
            ydr_ops.SOLLUMZ_OT_unset_all_materials_embedded.bl_idname)


class SOLLUMZ_PT_CREATE_DRAWABLE_PANEL(bpy.types.Panel):
    bl_label = "Create Drawable Objects"
    bl_idname = "SOLLUMZ_PT_CREATE_DRAWABLE_PANEL"
    bl_category = "Sollumz Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_DRAWABLE_TOOL_PANEL.bl_idname

    bl_order = 0

    def draw_header(self, context):
        self.layout.label(text="", icon="CUBE")

    def draw(self, context):
        layout = self.layout

        layout.label(text="Convert", icon="FILE_REFRESH")

        row = layout.row()
        row.operator(
            ydr_ops.SOLLUMZ_OT_convert_to_drawable_model.bl_idname, icon="MESH_DATA")

        row = layout.row()
        row.operator(
            ydr_ops.SOLLUMZ_OT_convert_to_drawable.bl_idname, icon="OUTLINER_OB_MESH")
        row = layout.row()
        row.prop(context.scene, "create_seperate_drawables")
        row.prop(context.scene, "auto_create_embedded_col")
        row.prop(context.scene, "center_drawable_to_selection")

        layout.separator(factor=2)

        layout.label(text="Create", icon="ADD")

        row = layout.row(align=True)
        row.operator(ydr_ops.SOLLUMZ_OT_create_drawable.bl_idname,
                     icon="OUTLINER_OB_MESH")
        row.operator(
            ydr_ops.SOLLUMZ_OT_create_drawable_dict.bl_idname, icon="TEXT")


class SOLLUMZ_PT_CREATE_LIGHT_PANEL(bpy.types.Panel):
    bl_label = "Create Lights"
    bl_idname = "SOLLUMZ_PT_CREATE_LIGHT_PANEL"
    bl_category = "Sollumz Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_DRAWABLE_TOOL_PANEL.bl_idname

    bl_order = 4

    def draw_header(self, context):
        self.layout.label(text="", icon="LIGHT")

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator(ydr_ops.SOLLUMZ_OT_create_light.bl_idname)
        row.prop(context.scene, "create_light_type", text="")


class SOLLUMZ_PT_BONE_TOOLS_PANEL(bpy.types.Panel):
    bl_label = "Bone Tools"
    bl_idname = "SOLLUMZ_PT_BONE_TOOLS_PANEL"
    bl_category = "Sollumz Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_DRAWABLE_TOOL_PANEL.bl_idname

    bl_order = 3

    def draw_header(self, context):
        self.layout.label(text="", icon="BONE_DATA")

    def draw(self, context):
        layout = self.layout

        layout.label(text="Rigging", icon="ARMATURE_DATA")
        layout.operator("sollumz.add_child_of_constraint",
                        icon="CONSTRAINT_BONE")
        layout.operator("sollumz.add_armature_modifier",
                        icon="MOD_ARMATURE")
        layout.separator()

        layout.label(text="Apply Bone Properties", icon="MODIFIER_ON")
        row = layout.row(align=True)
        row.operator(
            ydr_ops.SOLLUMZ_OT_apply_bone_properties_to_armature.bl_idname)
        row.operator(
            ydr_ops.SOLLUMZ_OT_apply_bone_properties_to_selected_bones.bl_idname)
        layout.separator()
        layout.label(text="Apply Bone Flags", icon="BOOKMARKS")
        row = layout.row(align=True)
        row.operator(ydr_ops.SOLLUMZ_OT_clear_bone_flags.bl_idname,
                     text="Clear All")
        row.operator(
            ydr_ops.SOLLUMZ_OT_rotation_bone_flags.bl_idname, text="Rotation")
        row.operator(
            ydr_ops.SOLLUMZ_OT_transform_bone_flags.bl_idname, text="Transform")
        row.operator(
            ydr_ops.SOLLUMZ_OT_scale_bone_flags.bl_idname, text="Scale")
        row.operator(
            ydr_ops.SOLLUMZ_OT_limit_bone_flags.bl_idname, text="Limit")


class SOLLUMZ_UL_BONE_FLAGS(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        custom_icon = "FILE"

        if self.layout_type in {"DEFAULT", "COMPACT"}:
            layout.prop(item, "name", text="", icon=custom_icon,
                        emboss=False, translate=False)
        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.prop(item, "name", text="", icon=custom_icon,
                        emboss=False, translate=False)


class SOLLUMZ_PT_BONE_PANEL(bpy.types.Panel):
    bl_label = "Sollumz"
    bl_idname = "SOLLUMZ_PT_BONE_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "bone"

    @classmethod
    def poll(cls, context):
        return context.mode != "EDIT_ARMATURE" and context.active_bone is not None

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        bone = context.active_bone

        layout.prop(bone.bone_properties, "tag")
        layout.separator()

        layout.label(text="Flags")
        row = layout.row()
        row.template_list("SOLLUMZ_UL_BONE_FLAGS", "Flags",
                          bone.bone_properties, "flags", bone.bone_properties, "ul_index")
        col = row.column(align=True)
        col.operator("sollumz.bone_flags_new_item", text="", icon="ADD")
        col.operator("sollumz.bone_flags_delete_item", text="", icon="REMOVE")


class SOLLUMZ_PT_SHADER_PANEL(bpy.types.Panel):
    bl_label = "Shader"
    bl_idname = "SOLLUMZ_PT_SHADER_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_options = {"HIDE_HEADER"}
    bl_parent_id = SOLLUMZ_PT_MAT_PANEL.bl_idname
    bl_order = 0

    @classmethod
    def poll(self, context):
        aobj = context.active_object

        if aobj is None:
            return False

        mat = aobj.active_material

        return mat is not None and mat.sollum_type == MaterialType.SHADER

    def draw(self, context):
        mat = context.active_object.active_material

        self.layout.label(text="Material Properties")

        row = self.layout.row()

        row.prop(mat.shader_properties, "renderbucket")
        row.prop(mat.shader_properties, "filename")
        row.prop(mat.shader_properties, "name")


class SOLLUMZ_PT_TXTPARAMS_PANEL(bpy.types.Panel):
    bl_label = "Texture Parameters"
    bl_idname = "SOLLUMZ_PT_TXTPARAMS_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_MAT_PANEL.bl_idname
    bl_order = 1

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.active_material is not None and context.active_object.active_material.sollum_type == MaterialType.SHADER

    def draw(self, context):
        layout = self.layout

        aobj = context.active_object
        if context.active_object is None:
            return

        mat = aobj.active_material
        if mat is None:
            return

        nodes = mat.node_tree.nodes
        for n in nodes:
            if isinstance(n, bpy.types.ShaderNodeTexImage) and n.is_sollumz:
                box = layout.box()
                row = box.row(align=True)
                row.label(text="Texture Type: " + n.name)
                row.label(text="Texture Name: " + n.sollumz_texture_name)

                if n.image:
                    row = box.row()
                    row.prop(n.image, "filepath", text="Texture Path")
                    row = box.row()
                    row.prop(n.texture_properties, "embedded")
                    row.enabled = n.image.filepath != ""
                else:
                    row = box.row()
                    row.label(
                        text="Image Texture has no linked image.", icon="ERROR")

                box.prop(n.texture_properties, "usage")


class SOLLUMZ_PT_VALUEPARAMS_PANEL(bpy.types.Panel):
    bl_label = "Value Parameters"
    bl_idname = "SOLLUMZ_PT_VALUEPARAMS_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_MAT_PANEL.bl_idname
    bl_order = 2

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.active_material is not None and context.active_object.active_material.sollum_type == MaterialType.SHADER

    def draw(self, context):
        layout = self.layout

        aobj = context.active_object
        if context.active_object is None:
            return

        mat = aobj.active_material
        if mat is None:
            return

        nodes = mat.node_tree.nodes
        for n in nodes:  # LOOP SERERATE SO TEXTURES SHOW ABOVE VALUE PARAMS
            if isinstance(n, bpy.types.ShaderNodeValue) and n.is_sollumz:
                if n.name[-1] == "x":
                    row = layout.row()
                    row.label(text=n.name[:-2])

                    x = n
                    y = mat.node_tree.nodes[n.name[:-1] + "y"]
                    z = mat.node_tree.nodes[n.name[:-1] + "z"]
                    w = mat.node_tree.nodes[n.name[:-1] + "w"]

                    row.prop(x.outputs[0], "default_value", text="X:")
                    row.prop(y.outputs[0], "default_value", text="Y:")
                    row.prop(z.outputs[0], "default_value", text="Z:")
                    row.prop(w.outputs[0], "default_value", text="W:")


class SOLLUMZ_PT_VALUEPARAMS_ARRAYS_PANEL(bpy.types.Panel):
    bl_label = "Array Parameters"
    bl_idname = "SOLLUMZ_PT_VALUEPARAMS_ARRAYS_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_MAT_PANEL.bl_idname
    bl_order = 3

    @classmethod
    def poll(cls, context):
        obj = context.active_object

        if not obj:
            return False

        mat = obj.active_material

        if mat is None or (mat is not None and mat.sollum_type != MaterialType.SHADER):
            return False

        for n in mat.node_tree.nodes:
            if isinstance(n, bpy.types.ShaderNodeGroup) and n.is_sollumz:
                return True

    def draw(self, context):
        layout = self.layout
        mat = context.active_object.active_material

        for n in mat.node_tree.nodes:
            if not isinstance(n, bpy.types.ShaderNodeGroup) or not n.is_sollumz:
                continue

            row = layout.row()
            row.label(text=n.name)

            x = n.inputs[0]
            y = n.inputs[1]
            z = n.inputs[2]
            w = n.inputs[3]

            row.prop(x, "default_value", text="X:")
            row.prop(y, "default_value", text="Y:")
            row.prop(z, "default_value", text="Z:")
            row.prop(w, "default_value", text="W:")


class SOLLUMZ_PT_CHILD_OF_SUBPANEL(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_label = "Sollumz"
    bl_parent_id = "OBJECT_PT_bChildOfConstraint"

    def draw(self, context):
        layout = self.layout
        con = self.custom_data
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.prop(con, "owner_space")
        layout.prop(con, "target_space")
        layout.separator()
        layout.operator("sollumz.set_correct_child_of_space")


class SOLLUMZ_PT_LOD_TOOLS_PANEL(bpy.types.Panel):
    bl_label = "LOD Tools"
    bl_idname = "SOLLUMZ_PT_LOD_TOOLS_PANEL"
    bl_category = "Sollumz Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_DRAWABLE_TOOL_PANEL.bl_idname

    bl_order = 2

    def draw_header(self, context):
        self.layout.label(text="", icon="MESH_DATA")

    def draw(self, context: Context):
        ...


class SOLLUMZ_PT_AUTO_LOD_PANEL(bpy.types.Panel):
    bl_label = "Auto LOD"
    bl_idname = "SOLLUMZ_PT_AUTO_LOD_PANEL"
    bl_category = "Sollumz Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"HIDE_HEADER"}
    bl_parent_id = SOLLUMZ_PT_LOD_TOOLS_PANEL.bl_idname

    bl_order = 0

    def draw(self, context: Context):
        layout = self.layout

        layout.label(text="Auto LOD")
        box = layout.box()

        box.prop(context.scene, "sollumz_auto_lod_levels")
        box.separator(factor=0.25)
        box.prop(context.scene, "sollumz_auto_lod_ref_mesh",
                 text="Reference Mesh")
        box.prop(context.scene, "sollumz_auto_lod_decimate_step")
        box.separator()
        box.operator("sollumz.auto_lod", icon="MOD_DECIM")


class SOLLUMZ_PT_EXTRACT_LODS_PANEL(bpy.types.Panel):
    bl_label = "Extract LODs"
    bl_idname = "SOLLUMZ_PT_EXTRACT_LODS_PANEL"
    bl_category = "Sollumz Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"HIDE_HEADER"}
    bl_parent_id = SOLLUMZ_PT_LOD_TOOLS_PANEL.bl_idname

    bl_order = 1

    def draw(self, context: Context):
        layout = self.layout

        layout.label(text="Extract LODs")
        box = layout.box()
        box.separator(factor=0.25)

        box.prop(context.scene, "sollumz_extract_lods_levels")
        box.prop(context.scene, "sollumz_extract_lods_parent_type")

        box.separator()

        box.operator("sollumz.extract_lods", icon="EXPORT")
