import bpy
from bpy.types import Context
from . import operators as ydr_ops
from .shader_materials import shadermats
from ..sollumz_ui import SOLLUMZ_PT_OBJECT_PANEL, SOLLUMZ_PT_MAT_PANEL
from ..sollumz_properties import SollumType, MaterialType, LightType, SOLLUMZ_UI_NAMES
from ..sollumz_ui import FlagsPanel, TimeFlagsPanel
from ..sollumz_helper import find_sollumz_parent
from ..icons import icon_manager
from ..shared.shader_nodes import SzShaderNodeParameter


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
        obj = context.active_object
        drawable_props = obj.drawable_properties

        col = layout.column(align=True)
        col.use_property_decorate = False
        col.use_property_split = True

        col.prop(drawable_props, "lod_dist_high", text="Lod Distance High")
        col.prop(drawable_props, "lod_dist_med", text="Med")
        col.prop(drawable_props, "lod_dist_low", text="Low")
        col.prop(drawable_props, "lod_dist_vlow", text="Vlow")

        col.separator()

        col.operator("sollumz.order_shaders", icon="MATERIAL")


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
        layout.prop(model_props, "matrix_count")
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
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        return context.light and context.active_object is not None

    def draw_header(self, context):
        icon_manager.icon_label("sollumz_icon", self)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        aobj = context.active_object

        if aobj.sollum_type != SollumType.LIGHT:
            row = layout.row()
            row.prop(aobj, "sollum_type")
            layout.label(text="No Sollumz light in the scene selected.", icon="ERROR")
            return

        light = context.light

        row = layout.row()
        row.enabled = light.sollum_type != LightType.NONE
        row.prop(light, "sollum_type")

        if light.sollum_type != LightType.NONE:
            layout.separator()

            box = layout.box()
            box.label(text="General Properties")
            box.prop(light, "color")
            box.prop(light, "energy", text="Intensity")
            box.prop(light, "cutoff_distance", text="Falloff")
            box.prop(light, "shadow_soft_size", text="Falloff Exponent")
            box.prop(light, "shadow_buffer_clip_start", text="Shadow Near Clip")

            # Extra Properties
            match light.sollum_type:
                case LightType.SPOT:
                    box = layout.box()
                    box.label(text="Spot Properties")
                    box.prop(light, "spot_size", text="Cone Outer Angle")
                    box.prop(light, "spot_blend",text="Cone Inner Angle")
                case LightType.CAPSULE:
                    box = layout.box()
                    box.label(text="Capsule Properties")
                    box.prop(light.light_properties, "extent", index=0)

            # Misc Properties
            box = layout.box()
            box.label(text="Misc Properties")
            box.prop(light.light_properties, "light_hash")
            box.prop(light.light_properties, "group_id")
            box.prop(light.light_properties, "projected_texture_hash")
            box.prop(light.light_properties, "flashiness")


            # Volume properties
            box = layout.box()
            box.label(text="Volume Properties", icon="MOD_EXPLODE")
            box.prop(light, "volume_factor", text="Volume Intensity")
            box.prop(light.light_properties, "volume_size_scale")
            box.prop(light.light_properties, "volume_outer_color")
            box.prop(light.light_properties, "volume_outer_intensity")
            box.prop(light.light_properties, "volume_outer_exponent")

            # Distance properties
            box = layout.box()
            box.label(text="Distance Properties", icon="DRIVER_DISTANCE")
            box.prop(light.light_properties, "light_fade_distance")
            box.prop(light.light_properties, "shadow_fade_distance")
            box.prop(light.light_properties, "specular_fade_distance")
            box.prop(light.light_properties, "volumetric_fade_distance")

            # Culling Plane
            box = layout.box()
            box.label(text="Culling Plane", icon="MESH_PLANE")
            box.prop(light.light_properties, "culling_plane_normal")
            box.prop(light.light_properties, "culling_plane_offset")

            # Corona Properties
            box = layout.box()
            box.label(text="Corona Properties", icon="LIGHT_SUN")
            box.prop(light.light_properties, "corona_size")
            box.prop(light.light_properties, "corona_intensity")
            box.prop(light.light_properties, "corona_z_bias")

            # Advanced Properties
            box = layout.box()
            box.label(text="Advanced Properties", icon="TOOL_SETTINGS")
            box.prop(light.light_properties, "shadow_blur")


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
        obj = context.active_object
        return obj is not None and obj.type == "LIGHT" and obj.sollum_type == SollumType.LIGHT

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
        obj = context.active_object
        return obj is not None and obj.type == "LIGHT" and obj.sollum_type == SollumType.LIGHT

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
    bl_label = "Light Tools"
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
        row.template_list(SOLLUMZ_UL_LIGHT_PRESET_LIST.bl_idname, "light_presets",
                          context.scene, "light_presets", context.scene, "light_preset_index")
        col = row.column(align=True)
        col.operator(ydr_ops.SOLLUMZ_OT_save_light_preset.bl_idname, text="", icon="ADD")
        col.operator(ydr_ops.SOLLUMZ_OT_delete_light_preset.bl_idname, text="", icon="REMOVE")
        row = layout.row()
        row.operator(ydr_ops.SOLLUMZ_OT_load_light_preset.bl_idname, icon='CHECKMARK')

        layout.separator()
        row = layout.row(align=True)
        row.operator(ydr_ops.SOLLUMZ_OT_create_light.bl_idname)
        row.prop(context.scene, "create_light_type", text="")


class SOLLUMZ_UL_LIGHT_PRESET_LIST(bpy.types.UIList):
    bl_idname = "SOLLUMZ_UL_LIGHT_PRESET_LIST"

    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            row = layout.row()
            row.label(text=item.name, icon="BOOKMARKS")
        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.prop(item, "name",
                        text=item.name, emboss=False, icon="BOOKMARKS")


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
            ydr_ops.SOLLUMZ_OT_translation_bone_flags.bl_idname, text="Translation")
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

    def draw_header(self, context):
        icon_manager.icon_label("sollumz_icon", self)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        bone = context.active_bone

        row = layout.row(align=True)
        row.prop(bone.bone_properties, "tag")
        row.prop(bone.bone_properties, "use_manual_tag", toggle=True, icon="MODIFIER_ON", icon_only=True)
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
                SPLIT_FACTOR = 0.2
                split = layout.split(factor=SPLIT_FACTOR)
                split.alignment = "RIGHT"
                split.label(text=n.name)
                split.template_ID(n, "image", open="image.open")

                if n.image is not None:
                    split = layout.split(factor=SPLIT_FACTOR)  # split to align the props with the image selector
                    _ = split.row()
                    row = split.row()
                    row.enabled = n.image.filepath != ""
                    row.prop(n.texture_properties, "embedded")
                    row.prop(n.image.colorspace_settings, "name", text="Color Space")

                # TODO: verify if Usage can be completely removed
                # box.prop(n.texture_properties, "usage")


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
            if isinstance(n, SzShaderNodeParameter):
                n.draw(context, layout, label=n.name, compact=True)


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
