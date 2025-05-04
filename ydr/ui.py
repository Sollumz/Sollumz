import bpy
from bpy.types import (
    Context
)
from bpy.props import (
    BoolProperty
)
import os
from . import (
    operators as ydr_ops,
    cloth_operators as cloth_ops,
)
from .shader_materials import shadermats
from .cable import is_cable_mesh
from .cloth import ClothAttr
from .cloth_diagnostics import cloth_last_export_contexts
from ..cwxml.shader import ShaderManager
from ..sollumz_ui import SOLLUMZ_PT_OBJECT_PANEL, SOLLUMZ_PT_MAT_PANEL
from ..sollumz_properties import SollumType, MaterialType, LightType, SOLLUMZ_UI_NAMES
from ..sollumz_ui import FlagsPanel, TimeFlagsPanel
from ..sollumz_helper import find_sollumz_parent
from ..sollumz_preferences import get_addon_preferences
from ..icons import icon_manager
from ..shared.shader_nodes import SzShaderNodeParameter
from ..tools.meshhelper import (
    get_uv_map_name,
    get_color_attr_name,
    get_mesh_used_texcoords_indices,
    get_mesh_used_colors_indices,
)


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


class SOLLUMZ_PT_CHAR_CLOTH_PANEL(bpy.types.Panel):
    bl_label = "Character Cloth"
    bl_idname = "SOLLUMZ_PT_CHAR_CLOTH_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_DRAWABLE_PANEL.bl_idname
    bl_order = 1

    @property
    def has_cloth(self) -> bool:
        from ..ydr.cloth_char import cloth_char_find_mesh_objects
        obj = bpy.context.view_layer.objects.active
        cloth_objs = cloth_char_find_mesh_objects(obj, silent=True)
        return bool(cloth_objs)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        obj = context.view_layer.objects.active
        cloth_props = obj.drawable_properties.char_cloth

        has_cloth = self.has_cloth
        if not has_cloth:
            layout.label(text="No character cloth in the active drawable.", icon="ERROR")
        col = layout.column()
        col.active = has_cloth
        col.prop(cloth_props, "weight")
        col.prop(cloth_props, "num_pin_radius_sets")
        # These properties seem to be overwritten at runtime, so they won't have any effect
        # col.prop(cloth_props, "pin_radius_scale")
        # col.prop(cloth_props, "pin_radius_threshold")
        # col.prop(cloth_props, "wind_scale")


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

        sollumz_parent = find_sollumz_parent(obj, parent_type=SollumType.DRAWABLE)

        return obj.sollum_type == SollumType.DRAWABLE_MODEL and obj.type == "MESH" and sollumz_parent is not None

    def draw(self, context):
        layout = self.layout
        layout.use_property_decorate = False
        layout.use_property_split = True

        obj = context.active_object
        active_lod_level = obj.sz_lods.active_lod_level
        mesh = obj.data
        sollumz_parent = find_sollumz_parent(obj, parent_type=SollumType.DRAWABLE)

        model_props = mesh.drawable_model_properties

        col = layout.column()
        col.alignment = "RIGHT"
        col.enabled = False

        is_skinned_model = obj.vertex_groups and sollumz_parent is not None and not obj.sollumz_is_physics_child_mesh

        # All skinned objects (objects with vertex groups) go in the same drawable model
        if is_skinned_model:
            model_props = sollumz_parent.skinned_model_properties.get_lod(active_lod_level)

            col.label(text=f"Active LOD: {SOLLUMZ_UI_NAMES[active_lod_level]} (Skinned)")
        else:
            col.label(text=f"Active LOD: {SOLLUMZ_UI_NAMES[active_lod_level]}")

        col.separator()

        layout.prop(model_props, "render_mask")


class SOLLUMZ_UL_SHADER_MATERIALS_LIST(bpy.types.UIList):
    bl_idname = "SOLLUMZ_UL_SHADER_MATERIALS_LIST"

    use_filter_favorites: BoolProperty(name="Filter Favorites")

    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        name = shadermats[item.index].ui_name
        # If the object is selected
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            row = layout.row()
            row.label(text=name, icon="SHADING_TEXTURE")
            favorite_icon = "SOLO_ON" if item.favorite else "SOLO_OFF"
            row.prop(item, "favorite", text="", toggle=True, emboss=False, icon=favorite_icon)
        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.prop(item, "name",
                        text=name, emboss=False, icon="SHADING_TEXTURE")

    def draw_filter(self, context, layout):
        row = layout.row()

        subrow = row.row(align=True)
        subrow.prop(self, "filter_name", text="")
        subrow.prop(self, "use_filter_invert", text="", toggle=True, icon="ARROW_LEFTRIGHT")

        subrow = row.row(align=True)
        subrow.prop(self, "use_filter_sort_alpha", text="", toggle=True, icon="SORTALPHA")
        icon = "SORT_DESC" if self.use_filter_sort_reverse else "SORT_ASC"
        subrow.prop(self, "use_filter_sort_reverse", text="", toggle=True, icon=icon)

        subrow = row.row(align=True)
        subrow.prop(self, "use_filter_favorites", text="", toggle=True, icon="SOLO_ON")

    def filter_items(self, context, data, propname):
        shader_materials = getattr(data, propname)
        helper_funcs = bpy.types.UI_UL_list

        # Default return values.
        flt_flags = []
        flt_neworder = []

        # Filtering by name
        if self.filter_name:
            filter_name = self.filter_name.replace(" ", "").replace("_", "")
            flt_flags = helper_funcs.filter_items_by_name(
                filter_name, self.bitflag_filter_item, shader_materials, "search_name",
                reverse=self.use_filter_sort_reverse
            )

        # Filter favorites.
        if self.use_filter_favorites:
            if not flt_flags:
                flt_flags = [self.bitflag_filter_item] * len(shader_materials)

            # NOTE: shader_material.favorite is O(n) where n is the number of favorite shaders. The user probably won't
            # have more than 20-30 favorites so this shouldn't be a problem. Also tested by setting all shaders as
            # favorite and didn't notice any major lag in the UI.
            # If there starts to be noticeable performance drops, we could cache the list of favorite shaders in a set.
            for idx, shader_material in enumerate(shader_materials):
                if not shader_material.favorite:
                    flt_flags[idx] &= ~self.bitflag_filter_item

        # Reorder by name or average weight.
        if self.use_filter_sort_alpha:
            flt_neworder = helper_funcs.sort_items_by_name(shader_materials, "search_name")

        return flt_flags, flt_neworder


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
                    box.prop(light, "spot_blend", text="Cone Inner Angle")
                case LightType.CAPSULE:
                    box = layout.box()
                    box.label(text="Capsule Properties")
                    box.prop(light.light_properties, "extent", index=0)

            # Misc Properties
            box = layout.box()
            box.label(text="Misc Properties")
            box.prop(light.light_properties, "light_hash")
            # box.prop(light.light_properties, "group_id") # this property is unused
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
            row = box.row()
            row.use_property_split = False
            row.use_property_decorate = False
            row.prop(light.light_flags, "enable_culling_plane", text="")
            row.label(text="Culling Plane")
            col = box.column()
            col.active = light.light_flags.enable_culling_plane
            col.prop(light.light_properties, "culling_plane_normal", text="Normal")
            col.prop(light.light_properties, "culling_plane_offset", text="Offset")

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
        wm = context.window_manager
        layout = self.layout
        layout.label(text="Create")
        layout.template_list(
            SOLLUMZ_UL_SHADER_MATERIALS_LIST.bl_idname, "",
            wm, "sz_shader_materials", wm, "sz_shader_material_index"
        )
        row = layout.row()
        op = row.operator(ydr_ops.SOLLUMZ_OT_create_shader_material.bl_idname)
        op.shader_index = wm.sz_shader_material_index
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
        grid = layout.grid_flow(align=True)
        row.operator(
            ydr_ops.SOLLUMZ_OT_update_tinted_shader_graph.bl_idname, icon="NODETREE")


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
                          context.window_manager, "sz_light_presets", context.window_manager, "sz_light_preset_index")
        col = row.column(align=True)
        col.operator(ydr_ops.SOLLUMZ_OT_save_light_preset.bl_idname, text="", icon="ADD")
        col.operator(ydr_ops.SOLLUMZ_OT_delete_light_preset.bl_idname, text="", icon="REMOVE")
        col.separator()
        col.menu(SOLLUMZ_MT_light_presets_context_menu.bl_idname, icon="DOWNARROW_HLT", text="")

        row = layout.row()
        row.operator(ydr_ops.SOLLUMZ_OT_load_light_preset.bl_idname, icon='CHECKMARK')

        layout.separator()
        row = layout.row(align=True)
        row.operator(ydr_ops.SOLLUMZ_OT_create_light.bl_idname)
        row.prop(context.scene, "create_light_type", text="")


class SOLLUMZ_MT_light_presets_context_menu(bpy.types.Menu):
    bl_label = "Light Presets Specials"
    bl_idname = "SOLLUMZ_MT_light_presets_context_menu"

    def draw(self, _context):
        layout = self.layout

        from .properties import get_light_presets_path
        path = get_light_presets_path()
        layout.enabled = os.path.exists(path)
        layout.operator("wm.path_open", text="Open Presets File").filepath = path


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


class SOLLUMZ_PT_SHADER_PRESET_PANEL(bpy.types.Panel):
    bl_label = "Shader Presets"
    bl_idname = "SOLLUMZ_PT_SHADER_PRESET_PANEL"
    bl_category = "Sollumz Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_SHADER_TOOLS_PANEL.bl_idname

    bl_order = 1

    def draw_header(self, context):
        self.layout.label(text="", icon="BOOKMARKS")

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager

        row = layout.row()
        row.template_list(
            SOLLUMZ_UL_SHADER_PRESET_LIST.bl_idname, "shader_presets",
            wm, "sz_shader_presets",
            wm, "sz_shader_preset_index"
        )
        col = row.column(align=True)
        col.operator(ydr_ops.SOLLUMZ_OT_save_shader_preset.bl_idname, text="", icon="ADD")
        col.operator(ydr_ops.SOLLUMZ_OT_delete_shader_preset.bl_idname, text="", icon="REMOVE")
        col.separator()
        col.menu(SOLLUMZ_MT_shader_presets_context_menu.bl_idname, icon="DOWNARROW_HLT", text="")

        row = layout.row(align=True)
        op = row.operator(ydr_ops.SOLLUMZ_OT_load_shader_preset.bl_idname, icon="CHECKMARK")
        op.apply_textures = get_addon_preferences(context).shader_preset_apply_textures
        row.menu(SOLLUMZ_MT_shader_presets_apply_context_menu.bl_idname, icon="DOWNARROW_HLT", text="")


class SOLLUMZ_MT_shader_presets_context_menu(bpy.types.Menu):
    bl_label = "Shader Presets Specials"
    bl_idname = "SOLLUMZ_MT_shader_presets_context_menu"

    def draw(self, _context):
        layout = self.layout

        from .properties import get_shader_presets_path
        path = get_shader_presets_path()
        layout.enabled = os.path.exists(path)
        layout.operator("wm.path_open", text="Open Presets File").filepath = path


class SOLLUMZ_MT_shader_presets_apply_context_menu(bpy.types.Menu):
    bl_label = "Shader Presets Apply Options"
    bl_idname = "SOLLUMZ_MT_shader_presets_apply_context_menu"

    def draw(self, context):
        layout = self.layout
        layout.prop(get_addon_preferences(context), "shader_preset_apply_textures", text="Apply Textures")


class SOLLUMZ_UL_SHADER_PRESET_LIST(bpy.types.UIList):
    bl_idname = "SOLLUMZ_UL_SHADER_PRESET_LIST"

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

        subrow = row.row(align=True)
        subrow.prop(mat.shader_properties, "ui_name")
        subrow.popover(SOLLUMZ_PT_change_shader.bl_idname, icon="DOWNARROW_HLT", text="")


class SOLLUMZ_PT_change_shader(bpy.types.Panel):
    bl_idname = "SOLLUMZ_PT_change_shader"
    bl_space_type = "PROPERTIES"
    bl_region_type = "HEADER"
    bl_label = "Change Shader"
    bl_ui_units_x = 18  # make popup wider to fit all shader names

    def draw(self, context):
        wm = context.window_manager
        layout = self.layout
        layout.template_list(
            SOLLUMZ_UL_SHADER_MATERIALS_LIST.bl_idname, "",
            wm, "sz_shader_materials", wm, "sz_shader_material_index"
        )
        op = layout.operator(ydr_ops.SOLLUMZ_OT_change_shader.bl_idname)
        op.shader_index = wm.sz_shader_material_index


def collect_parameter_nodes(mat: bpy.types.Material, filter_func) -> list[bpy.types.Node]:
    """Filters nodes from ``mat`` and sorts them based on ``ShaderDef.parameter_ui_order``."""
    shader = ShaderManager.find_shader(mat.shader_properties.filename)

    def _valid(n: bpy.types.Node) -> bool:
        if filter_func(n):
            p = shader.parameter_map.get(n.name, None)
            return p and not p.hidden

        return False

    nodes = [n for n in mat.node_tree.nodes if _valid(n)]
    if shader is not None:
        # order changes when the active node changes, sort so the UI stays stable
        nodes = sorted(nodes, key=lambda n: shader.parameter_ui_order.get(n.name, -1))

    return nodes


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

        nodes = collect_parameter_nodes(mat, lambda n: isinstance(n, bpy.types.ShaderNodeTexImage) and n.is_sollumz)
        for n in nodes:
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

        nodes = collect_parameter_nodes(mat, lambda n: isinstance(n, SzShaderNodeParameter))
        for n in nodes:
            n.draw(context, layout, label=n.name, compact=True)


class SOLLUMZ_PT_COPY_TRANSFORMS_SUBPANEL(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_label = "Sollumz"
    bl_parent_id = "OBJECT_PT_bTransLikeConstraint"

    def draw(self, context):
        layout = self.layout
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


class SOLLUMZ_PT_CABLE_TOOLS_PANEL(bpy.types.Panel):
    bl_label = "Cable Tools"
    bl_idname = "SOLLUMZ_PT_CABLE_TOOLS_PANEL"
    bl_category = "Sollumz Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_DRAWABLE_TOOL_PANEL.bl_idname

    bl_order = 5

    def draw_header(self, context):
        self.layout.label(text="", icon="OUTLINER_DATA_GREASEPENCIL")

    def draw(self, context):
        from . import cable_operators as cable_ops
        from .cable import CableAttr

        wm = context.window_manager

        layout = self.layout

        def _visible_icon_prop(layout, obj, prop_name):
            visible_icon = "HIDE_OFF" if getattr(obj, prop_name, False) else "HIDE_ON"
            layout.prop(obj, prop_name, text="", emboss=False, icon=visible_icon)

        row = layout.row(align=True)
        row.label(text=CableAttr.RADIUS.label)
        _visible_icon_prop(row, wm, "sz_ui_cable_radius_visualize")

        row = layout.row(align=True)
        op = row.operator(cable_ops.SOLLUMZ_OT_cable_set_radius.bl_idname, text="Set")
        op.value = wm.sz_ui_cable_radius
        row.prop(wm, "sz_ui_cable_radius", text="")

        row = layout.row(align=True)
        row.label(text=CableAttr.DIFFUSE_FACTOR.label)
        _visible_icon_prop(row, wm, "sz_ui_cable_diffuse_factor_visualize")

        row = layout.row(align=True)
        op = row.operator(cable_ops.SOLLUMZ_OT_cable_set_diffuse_factor.bl_idname, text="Set")
        op.value = wm.sz_ui_cable_diffuse_factor
        row.prop(wm, "sz_ui_cable_diffuse_factor", text="")

        row = layout.row(align=True)
        row.label(text=CableAttr.UM_SCALE.label)
        _visible_icon_prop(row, wm, "sz_ui_cable_um_scale_visualize")

        row = layout.row(align=True)
        op = row.operator(cable_ops.SOLLUMZ_OT_cable_set_um_scale.bl_idname, text="Set")
        op.value = wm.sz_ui_cable_um_scale
        row.prop(wm, "sz_ui_cable_um_scale", text="")

        row = layout.row(align=True)
        row.label(text=CableAttr.PHASE_OFFSET.label)
        _visible_icon_prop(row, wm, "sz_ui_cable_phase_offset_visualize")

        row = layout.row(align=True)
        op = row.operator(cable_ops.SOLLUMZ_OT_cable_set_phase_offset.bl_idname, text="Set")
        op.value = wm.sz_ui_cable_phase_offset
        row.prop(wm, "sz_ui_cable_phase_offset", text="")

        row = layout.row(align=True)
        op = row.operator(cable_ops.SOLLUMZ_OT_cable_randomize_phase_offset.bl_idname, text="Randomize")

        row = layout.row(align=True)
        row.label(text=CableAttr.MATERIAL_INDEX.label)
        _visible_icon_prop(row, wm, "sz_ui_cable_material_index_visualize")

        row = layout.row(align=True)
        op = row.operator(cable_ops.SOLLUMZ_OT_cable_set_material_index.bl_idname, text="Set")
        op.value = wm.sz_ui_cable_material_index
        row.prop(wm, "sz_ui_cable_material_index", text="")


def _visible_icon_prop(layout, obj, prop_name):
    visible_icon = "HIDE_OFF" if getattr(obj, prop_name, False) else "HIDE_ON"
    layout.prop(obj, prop_name, text="", emboss=False, icon=visible_icon)


class SOLLUMZ_PT_CLOTH_TOOLS_PANEL(bpy.types.Panel):
    bl_label = "Cloth Tools"
    bl_idname = "SOLLUMZ_PT_CLOTH_TOOLS_PANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_DRAWABLE_TOOL_PANEL.bl_idname

    bl_order = 6

    def draw_header(self, context):
        self.layout.label(text="", icon="MATCLOTH")

    def draw(self, context):

        wm = context.window_manager

        layout = self.layout

        row = layout.row(align=True)
        row.label(text=ClothAttr.VERTEX_WEIGHT.label)
        _visible_icon_prop(row, wm, "sz_ui_cloth_vertex_weight_visualize")

        row = layout.row(align=True)
        op = row.operator(cloth_ops.SOLLUMZ_OT_cloth_set_vertex_weight.bl_idname, text="Set")
        op.value = wm.sz_ui_cloth_vertex_weight
        row.prop(wm, "sz_ui_cloth_vertex_weight", text="")

        row = layout.row(align=True)
        row.label(text=ClothAttr.INFLATION_SCALE.label)
        _visible_icon_prop(row, wm, "sz_ui_cloth_inflation_scale_visualize")

        row = layout.row(align=True)
        op = row.operator(cloth_ops.SOLLUMZ_OT_cloth_set_inflation_scale.bl_idname, text="Set")
        op.value = wm.sz_ui_cloth_inflation_scale
        row.prop(wm, "sz_ui_cloth_inflation_scale", text="")

        row = layout.row(align=True)
        row.label(text=ClothAttr.PINNED.label)
        _visible_icon_prop(row, wm, "sz_ui_cloth_pinned_visualize")

        row = layout.row(align=True)
        op = row.operator(cloth_ops.SOLLUMZ_OT_cloth_set_pinned.bl_idname, text="Pin")
        op.value = True
        op = row.operator(cloth_ops.SOLLUMZ_OT_cloth_set_pinned.bl_idname, text="Unpin")
        op.value = False

        row = layout.row(align=True)
        split = row.split(factor=0.5)
        row = split.row()
        row.label(text=ClothAttr.PIN_RADIUS.label)
        row = split.row()
        split = row.split(factor=0.5)
        row = split.row()
        row.prop(wm, "sz_ui_cloth_pin_radius_set", text="")
        row = split.row()
        row.alignment = "RIGHT"
        _visible_icon_prop(row, wm, "sz_ui_cloth_pin_radius_visualize")

        row = layout.row(align=True)
        op = row.operator(cloth_ops.SOLLUMZ_OT_cloth_set_pin_radius.bl_idname, text="Set")
        op.set_number = wm.sz_ui_cloth_pin_radius_set
        op.value = wm.sz_ui_cloth_pin_radius
        row.prop(wm, "sz_ui_cloth_pin_radius", text="")

        row = layout.row(align=True)
        split = row.split(factor=0.5, align=True)
        row = split.row(align=True)
        op = row.operator(cloth_ops.SOLLUMZ_OT_cloth_set_pin_radius_gradient.bl_idname, text="Fill Gradient")
        op.min_value = wm.sz_ui_cloth_pin_radius_gradient_min
        op.max_value = wm.sz_ui_cloth_pin_radius_gradient_max
        op.set_number = wm.sz_ui_cloth_pin_radius_set
        row = split.row(align=True)
        row.prop(wm, "sz_ui_cloth_pin_radius_gradient_min", text="")
        row.prop(wm, "sz_ui_cloth_pin_radius_gradient_max", text="")

        row = layout.row(align=True)
        row.label(text=ClothAttr.FORCE_TRANSFORM.label)
        _visible_icon_prop(row, wm, "sz_ui_cloth_force_transform_visualize")

        row = layout.row(align=True)
        op = row.operator(cloth_ops.SOLLUMZ_OT_cloth_set_force_transform.bl_idname, text="Set")
        op.value = wm.sz_ui_cloth_force_transform
        row.prop(wm, "sz_ui_cloth_force_transform", text="")


class SOLLUMZ_PT_CLOTH_DIAGNOSTICS_PANEL(bpy.types.Panel):
    bl_label = "Diagnostics"
    bl_idname = "SOLLUMZ_PT_CLOTH_DIAGNOSTICS_PANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_CLOTH_TOOLS_PANEL.bl_idname

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.operator(cloth_ops.SOLLUMZ_OT_cloth_refresh_diagnostics.bl_idname, text="Refresh", icon="FILE_REFRESH")

        if last := cloth_last_export_contexts():
            for c in last.values():
                for d in c.all_diagnostics.values():
                    d.draw_ui(layout, context)
        else:
            layout.label(text="No diagnostics")


def uv_maps_panel_draw(self, context):
    me = context.mesh

    if is_cable_mesh(me):
        # We don't use UVs with cable meshes
        return

    texcoords = get_mesh_used_texcoords_indices(me)
    texcoords_names = [get_uv_map_name(t) for t in texcoords]
    if all(n in me.uv_layers for n in texcoords_names):
        return

    layout = self.layout
    layout.label(text="Missing UV maps used by Sollumz shaders:", icon="ERROR")
    split = layout.split(factor=0.5, align=True)
    split.operator(ydr_ops.SOLLUMZ_OT_uv_maps_rename_by_order.bl_idname, text="Rename by Order")
    split.operator(ydr_ops.SOLLUMZ_OT_uv_maps_add_missing.bl_idname, text="Add Missing")
    for texcoord, name in zip(texcoords, texcoords_names):
        exists = name in me.uv_layers
        layout.label(text=name, icon="CHECKMARK" if exists else "X")


def color_attributes_panel_draw(self, context):
    me = context.mesh

    if is_cable_mesh(me):
        # We don't use color attributes with cable meshes
        return

    colors = get_mesh_used_colors_indices(me)
    colors_names = [get_color_attr_name(c) for c in colors]
    if all(n in me.color_attributes and
           me.color_attributes[n].domain == "CORNER" and
           me.color_attributes[n].data_type == "BYTE_COLOR"
           for n in colors_names):
        return

    layout = self.layout
    layout.label(text="Missing color attributes used by Sollumz shaders:", icon="ERROR")
    split = layout.split(factor=0.5, align=True)
    split.operator(ydr_ops.SOLLUMZ_OT_color_attrs_rename_by_order.bl_idname, text="Rename by Order")
    split.operator(ydr_ops.SOLLUMZ_OT_color_attrs_add_missing.bl_idname, text="Add Missing")
    for color, name in zip(colors, colors_names):
        exists = name in me.color_attributes
        if exists:
            attr = me.color_attributes[name]
            has_correct_format = attr.domain == "CORNER" and attr.data_type == "BYTE_COLOR"

        msg = name
        if exists and not has_correct_format:
            msg += "    (Incorrect format, must be 'Face Corner ▶ Byte Color')"
        layout.label(text=msg, icon="CHECKMARK" if exists and has_correct_format else "X")


def register():
    bpy.types.DATA_PT_uv_texture.append(uv_maps_panel_draw)
    bpy.types.DATA_PT_vertex_colors.append(color_attributes_panel_draw)


def unregister():
    bpy.types.DATA_PT_uv_texture.remove(uv_maps_panel_draw)
    bpy.types.DATA_PT_vertex_colors.remove(color_attributes_panel_draw)
