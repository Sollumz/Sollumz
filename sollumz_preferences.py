import bpy
from bpy.types import (
    bpy_struct,
    bpy_prop_array,
    bpy_prop_collection,
    PropertyGroup,
    Operator,
    UIList,
    UILayout,
    AddonPreferences,
)
from bpy.props import (
    StringProperty,
    IntProperty,
    BoolProperty,
    EnumProperty,
    CollectionProperty,
    PointerProperty,
    FloatVectorProperty,
    FloatProperty,
)
import rna_keymap_ui
import os
import ast
import textwrap
from typing import Any
from configparser import ConfigParser
from typing import Optional

PREFS_FILE_NAME = "sollumz_prefs.ini"


def _save_preferences_on_update(self, context):
    _save_preferences()


class SollumzExportSettings(PropertyGroup):
    limit_to_selected: BoolProperty(
        name="Limit to Selected",
        description="Export selected and visible objects only",
        default=True,
        update=_save_preferences_on_update
    )

    exclude_skeleton: BoolProperty(
        name="Exclude Skeleton",
        description="Exclude skeleton from export. Usually done with mp ped components",
        default=False,
        update=_save_preferences_on_update
    )

    export_with_ytyp: BoolProperty(
        name="Export with ytyp",
        description="Exports a .ytyp.xml with an archetype for every drawable or drawable dictionary being exported",
        default=False,
        update=_save_preferences_on_update
    )

    ymap_exclude_entities: BoolProperty(
        name="Exclude Entities",
        description="If enabled, ignore all Entities from the selected ymap(s)",
        default=False,
        update=_save_preferences_on_update
    )

    ymap_box_occluders: BoolProperty(
        name="Exclude Box Occluders",
        description="If enabled, ignore all Box occluders from the selected ymap(s)",
        default=False,
        update=_save_preferences_on_update
    )

    ymap_model_occluders: BoolProperty(
        name="Exclude Model Occluders",
        description="If enabled, ignore all Model occluders from the selected ymap(s)",
        default=False,
        update=_save_preferences_on_update
    )

    ymap_car_generators: BoolProperty(
        name="Exclude Car Generators",
        description="If enabled, ignore all Car Generators from the selected ymap(s)",
        default=False,
        update=_save_preferences_on_update
    )

    export_lods: EnumProperty(
        name="Toggle LODs",
        description="Toggle LODs to export",
        options={"ENUM_FLAG"},
        default=({"sollumz_export_very_high", "sollumz_export_main_lods"}),
        items=(
            ("sollumz_export_very_high", "Very High", "Export Very High LODs into a _hi.yft"),
            ("sollumz_export_main_lods", "High - Very Low", "Export all LODs except Very High")
        ),
        update=_save_preferences_on_update
    )

    apply_transforms: BoolProperty(
        name="Apply Parent Transforms",
        description="Apply Drawable/Fragment scale and rotation",
        default=False,
        update=_save_preferences_on_update
    )

    mesh_domain: EnumProperty(
        name="Mesh Domain",
        description="Domain considered for exporting meshes",
        default="FACE_CORNER",
        items=(
            (
                "FACE_CORNER", "Face Corner",
                "Mesh is exported allowing each face corner to have their own set of "
                "attributes. Recommended default setting."
            ),
            (
                "VERTEX", "Vertex",
                "Mesh is exported only allowing a single set of attributes per vertex. Recommended for when it is important "
                "that the vertex order and count remains the same during import and export, such as with MP freemode head "
                "models.\n\n"
                "If face corners attached to the vertex have different attributes (vertex colors, UVs, etc.), only the "
                "attributes of one of the face corners is used. In the case of normals, the average of the face corner "
                "normals is used."
            )
        ),
        update=_save_preferences_on_update
    )

    @property
    def export_hi(self) -> bool:
        return "sollumz_export_very_high" in self.export_lods

    @property
    def export_non_hi(self) -> bool:
        return "sollumz_export_main_lods" in self.export_lods


class SollumzImportSettings(PropertyGroup):
    import_as_asset: BoolProperty(
        name="Import To Asset Library",
        description="Imports the selected file as an asset to the current blend file asset library",
        default=False,
        update=_save_preferences_on_update
    )

    split_by_group: BoolProperty(
        name="Split Mesh by Vertex Group",
        description="Splits the mesh by the vertex groups",
        default=True,
        update=_save_preferences_on_update
    )

    import_ext_skeleton: BoolProperty(
        name="Import External Skeleton",
        description="Imports the first found yft skeleton in the same folder as the selected file",
        default=False,
        update=_save_preferences_on_update
    )

    ymap_skip_missing_entities: BoolProperty(
        name="Skip Missing Entities",
        description="If enabled, missing entities wont be created as an empty object",
        default=True,
        update=_save_preferences_on_update
    )

    ymap_exclude_entities: BoolProperty(
        name="Exclude Entities",
        description="If enabled, ignore all entities from the selected ymap(s)",
        default=False,
        update=_save_preferences_on_update
    )

    ymap_box_occluders: BoolProperty(
        name="Exclude Box Occluders",
        description="If enabled, ignore all Box occluders from the selected ymap(s)",
        default=False,
        update=_save_preferences_on_update
    )

    ymap_model_occluders: BoolProperty(
        name="Exclude Model Occluders",
        description="If enabled, ignore all Model occluders from the selected ymap(s)",
        default=False,
        update=_save_preferences_on_update
    )

    ymap_car_generators: BoolProperty(
        name="Exclude Car Generators",
        description="If enabled, ignore all Car Generators from the selected ymap(s)",
        default=False,
        update=_save_preferences_on_update
    )

    ymap_instance_entities: BoolProperty(
        name="Instance Entities",
        description="If enabled, instance all entities from the selected ymap(s)",
        default=False,
        update=_save_preferences_on_update
    )

    ytyp_mlo_instance_entities: BoolProperty(
        name="Instance MLO Entities",
        description=(
            "If enabled, MLO entities will be linked to a copy of the object matching the archetype name, instead of"
            "the object itself"
        ),
        default=True,
        update=_save_preferences_on_update
    )


class SollumzThemeSettings(PropertyGroup):
    def RGBAProperty(name: str, default: tuple[float, float, float]):
        return FloatVectorProperty(
            name=name,
            subtype="COLOR",
            min=0, max=1,
            size=4,
            default=default,
            update=_save_preferences_on_update,
        )

    mlo_gizmo_room: RGBAProperty("Room", (0.31, 0.38, 1.0, 0.7))
    mlo_gizmo_room_selected: RGBAProperty("Room Selected", (0.62, 0.76, 1.0, 0.9))
    mlo_gizmo_portal: RGBAProperty("Portal", (0.45, 0.98, 0.55, 0.5))
    mlo_gizmo_portal_selected: RGBAProperty("Portal Selected", (0.93, 1.0, 1.0, 0.7))
    mlo_gizmo_portal_direction: RGBAProperty("Portal Direction Arrow", (0.0, 0.6, 1.0, 0.3))
    mlo_gizmo_portal_direction_size: FloatProperty(name="Portal Direction Arrow Size", default=0.3, min=0.1, max=5.0)

    cable_overlay_radius: RGBAProperty("Radius", (1.0, 0.0, 0.0, 1.0))

    cloth_overlay_pinned: RGBAProperty("Pinned", (1.0, 0.65, 0.0, 0.5))
    cloth_overlay_pinned_size: IntProperty(name="Pinned Size", default=12, min=1, max=50)
    cloth_overlay_material_errors: RGBAProperty("Material Errors", (1.0, 0.05, 0.025, 0.45))
    cloth_overlay_binding_errors: RGBAProperty("Binding Errors", (1.0, 0.05, 0.025, 0.75))
    cloth_overlay_binding_errors_size: IntProperty(name="Binding Errors Size", default=12, min=1, max=50)

    def reset(self):
        for prop_name, annotation in SollumzThemeSettings.__annotations__.items():
            setattr(self, prop_name, annotation.keywords["default"])


class SOLLUMZ_OT_prefs_theme_reset(Operator):
    bl_idname = "sollumz.prefs_theme_reset"
    bl_label = "Reset Theme"
    bl_description = "Reset all theme settings to their default values"

    def execute(self, context):
        get_theme_settings(context).reset()
        _save_preferences()
        return {"FINISHED"}


class SzSharedTexturesDirectory(PropertyGroup):
    path: StringProperty(
        name="Path",
        description="Path to a directory with textures",
        subtype="DIR_PATH",
        update=_save_preferences_on_update,
    )
    recursive: BoolProperty(
        name="Recursive",
        description="Search this directory recursively",
        default=True,
        update=_save_preferences_on_update,
    )


class SOLLUMZ_UL_prefs_shared_textures_directories(UIList):
    bl_idname = "SOLLUMZ_UL_prefs_shared_textures_directories"

    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        layout.prop(item, "path", text="", emboss=False)
        layout.prop(item, "recursive", text="", icon="OUTLINER")


class SOLLUMZ_OT_prefs_shared_textures_directory_add(Operator):
    bl_idname = "sollumz.prefs_shared_textures_directory_add"
    bl_label = "Add Shared Textures Directory"
    bl_description = "Add a new directory to search textures in"

    path: StringProperty(
        name="Path",
        description="Path to a directory with textures",
        subtype="DIR_PATH",
    )
    recursive: BoolProperty(
        name="Recursive",
        description="Search this directory recursively",
        default=True,
    )

    def execute(self, context):
        prefs = get_addon_preferences(context)
        d = prefs.shared_textures_directories.add()
        d.path = self.path
        d.recursive = self.recursive
        prefs.shared_textures_directories_index = len(prefs.shared_textures_directories) - 1
        _save_preferences()
        return {"FINISHED"}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class SOLLUMZ_OT_prefs_shared_textures_directory_remove(Operator):
    bl_idname = "sollumz.prefs_shared_textures_directory_remove"
    bl_label = "Remove Shared Textures Directory"
    bl_description = "Remove the selected directory"

    @classmethod
    def poll(cls, context):
        prefs = get_addon_preferences(context)
        return 0 <= prefs.shared_textures_directories_index < len(prefs.shared_textures_directories)

    def execute(self, context):
        prefs = get_addon_preferences(context)
        prefs.shared_textures_directories.remove(prefs.shared_textures_directories_index)
        context.scene.ytyps.remove(context.scene.ytyp_index)
        prefs.shared_textures_directories_index = max(prefs.shared_textures_directories_index - 1, 0)
        _save_preferences()
        return {"FINISHED"}


class SOLLUMZ_OT_prefs_shared_textures_directory_move_up(Operator):
    bl_idname = "sollumz.prefs_shared_textures_directory_move_up"
    bl_label = "Increase Shared Texture Directory Priority"
    bl_description = "Increase search priority of this directory"

    @classmethod
    def poll(self, context):
        prefs = get_addon_preferences(context)
        return 0 < prefs.shared_textures_directories_index < len(prefs.shared_textures_directories)

    def execute(self, context):
        prefs = get_addon_preferences(context)
        indexA = prefs.shared_textures_directories_index
        indexB = prefs.shared_textures_directories_index - 1
        prefs.swap_shared_textures_directories(indexA, indexB)
        prefs.shared_textures_directories_index -= 1
        return {"FINISHED"}


class SOLLUMZ_OT_prefs_shared_textures_directory_move_down(Operator):
    bl_idname = "sollumz.prefs_shared_textures_directory_move_down"
    bl_label = "Decrease Shared Texture Directory Priority"
    bl_description = "Decrease search priority of this directory"

    @classmethod
    def poll(self, context):
        prefs = get_addon_preferences(context)
        return 0 <= prefs.shared_textures_directories_index < (len(prefs.shared_textures_directories) - 1)

    def execute(self, context):
        prefs = get_addon_preferences(context)
        indexA = prefs.shared_textures_directories_index
        indexB = prefs.shared_textures_directories_index + 1
        prefs.swap_shared_textures_directories(indexA, indexB)
        prefs.shared_textures_directories_index += 1
        return {"FINISHED"}


class SzFavoriteEntry(PropertyGroup):
    name: StringProperty(
        name="Name",
    )


class SollumzAddonPreferences(AddonPreferences):
    bl_idname = __package__

    show_vertex_painter: BoolProperty(
        name="Show Vertex Painter",
        description="Show the Vertex Painter panel in General Tools (Includes Terrain Painter)",
        default=True,
        update=_save_preferences_on_update
    )

    extra_color_swatches: BoolProperty(
        name="Extra Vertex Color Swatches",
        description="Add 3 extra color swatches to the Vertex Painter Panel (Max 6)",
        default=True,
        update=_save_preferences_on_update
    )

    sollumz_icon_header: BoolProperty(
        name="Show Sollumz icon",
        description="Show the Sollumz icon in properties section headers",
        default=True,
        update=_save_preferences_on_update
    )
    use_text_name_as_mat_name: BoolProperty(
        name="Use Texture Name as Material Name",
        description="Use the name of the texture as the material name",
        default=True,
        update=_save_preferences_on_update
    )

    shader_preset_apply_textures: BoolProperty(
        name="Apply Textures from Shader Preset",
        description=(
            "Enable to replace the material's existing textures with those from the shader preset. Disable to keep the "
            "current textures unchanged"
        ),
        default=True,
        update=_save_preferences_on_update
    )

    default_flags_portal: IntProperty(
        name="Default Portal Flags",
        description="The default flags for MLO portals",
        default=0,
        update=_save_preferences_on_update
    )

    default_flags_room: IntProperty(
        name="Default Room Flags",
        description="The default flags for MLO rooms",
        default=0,
        update=_save_preferences_on_update
    )

    default_flags_entity: IntProperty(
        name="Default Entity Flags",
        description="The default flags for MLO entities",
        default=0,
        update=_save_preferences_on_update
    )

    default_flags_archetype: IntProperty(
        name="Default Archetype Flags",
        description="The default flags for archetypes",
        default=0,
        update=_save_preferences_on_update
    )

    shared_textures_directories: CollectionProperty(
        name="Shared Textures",
        type=SzSharedTexturesDirectory,
    )
    shared_textures_directories_index: IntProperty(
        name="Selected Shared Textures Directory",
        min=0
    )

    favorite_shaders: CollectionProperty(
        name="Favorite Shaders",
        type=SzFavoriteEntry,
    )
    favorite_collision_materials: CollectionProperty(
        name="Favorite Collision Materials",
        type=SzFavoriteEntry,
    )

    export_settings: PointerProperty(type=SollumzExportSettings, name="Export Settings")
    import_settings: PointerProperty(type=SollumzImportSettings, name="Import Settings")
    theme: PointerProperty(type=SollumzThemeSettings, name="Theme")

    tab: EnumProperty(
        items=(
            ("GENERAL", "General", "", "SETTINGS", 0),
            ("IMPORT_EXPORT", "Import / Export", "", "IMPORT", 1),
            ("KEYMAP", "Keymap", "", "KEY_TAB", 3),
            ("UI", "UI", "", "WINDOW", 4),
            ("THEME", "Theme", "", "COLOR", 5),
            ("ABOUT", "About", "", "INFO_LARGE", 6),
        )
    )

    def swap_shared_textures_directories(self, indexA: int, indexB: int):
        a = self.shared_textures_directories[indexA]
        b = self.shared_textures_directories[indexB]
        pathA, recA = a.path, a.recursive
        pathB, recB = b.path, b.recursive
        a.path, a.recursive = pathB, recB
        b.path, b.recursive = pathA, recA

    def _is_favorite(self, favorites, entry_name: str) -> bool:
        for entry in favorites:
            if entry.name == entry_name:
                return True

        return False

    def _toggle_favorite(self, favorites, entry_name: str, favorite: bool):
        found = None
        for i, entry in enumerate(favorites):
            if entry.name == entry_name:
                found = i
                break

        updated = False
        if favorite:
            # Set as favorite
            if found is None:
                s = favorites.add()
                s.name = entry_name
                updated = True
        else:
            # Remove from favorites
            if found is not None:
                favorites.remove(found)
                updated = True

        if updated:
            _save_preferences()

    def is_favorite_shader(self, shader_name: str) -> bool:
        return self._is_favorite(self.favorite_shaders, shader_name)

    def is_favorite_collision_material(self, collision_material_name: str) -> bool:
        return self._is_favorite(self.favorite_collision_materials, collision_material_name)

    def toggle_favorite_shader(self, shader_name: str, favorite: bool):
        self._toggle_favorite(self.favorite_shaders, shader_name, favorite)

    def toggle_favorite_collision_material(self, collision_material_name: str, favorite: bool):
        self._toggle_favorite(self.favorite_collision_materials, collision_material_name, favorite)

    def draw(self, context):
        layout = self.layout
        layout.row().prop(self, "tab", expand=True)

        # Based on CenterAlignMixIn from Blender's scripts/startup/bl_ui/space_userpref.py
        width = context.region.width
        ui_scale = context.preferences.system.ui_scale
        # No horizontal margin if region is rather small.
        is_wide = width > (550 * ui_scale)

        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        row = layout.row()
        if is_wide:
            row.label()  # Needed so col below is centered.

        col = row.column()
        col.ui_units_x = 95

        match self.tab:
            case "GENERAL":
                self.draw_general(context, col)
            case "IMPORT_EXPORT":
                self.draw_import_export(context, col)
            case "KEYMAP":
                self.draw_keymap(context, col)
            case "UI":
                self.draw_ui(context, col)
            case "THEME":
                self.draw_theme(context, col)
            case "ABOUT":
                self.draw_about(context, col)

        if is_wide:
            row.label()  # Needed so col above is centered.

    def draw_general(self, context, layout: UILayout):
        layout.prop(self, "use_text_name_as_mat_name")
        layout.prop(self, "shader_preset_apply_textures")

        col = layout.column(align=True)
        col.prop(self, "default_flags_portal", text="Default Flags for Portals")
        col.prop(self, "default_flags_room", text="Rooms")
        col.prop(self, "default_flags_entity", text="Entities")
        col.prop(self, "default_flags_archetype", text="Archetypes")

        from .sollumz_ui import draw_list_with_add_remove
        layout.separator()
        layout.label(text="Shared Textures")
        _, side_col = draw_list_with_add_remove(
            layout,
            SOLLUMZ_OT_prefs_shared_textures_directory_add.bl_idname,
            SOLLUMZ_OT_prefs_shared_textures_directory_remove.bl_idname,
            SOLLUMZ_UL_prefs_shared_textures_directories.bl_idname, "",
            self, "shared_textures_directories",
            self, "shared_textures_directories_index",
            rows=4
        )
        side_col.separator()
        subcol = side_col.column(align=True)
        subcol.operator(SOLLUMZ_OT_prefs_shared_textures_directory_move_up.bl_idname, text="", icon="TRIA_UP")
        subcol.operator(SOLLUMZ_OT_prefs_shared_textures_directory_move_down.bl_idname, text="", icon="TRIA_DOWN")

    def draw_import_export(self, context, layout: UILayout):
        def _section_header(layout: UILayout, text: str):
            _line_separator(layout)
            row = layout.row()
            row.alignment = "LEFT"
            row.label(text="", icon="BLANK1")
            row.label(text=text, icon="BLANK1")

        # Import settings
        box = layout.box()
        box.label(text="Import", icon="IMPORT")
        settings = self.import_settings
        box.prop(settings, "import_as_asset")
        _section_header(box, text="Fragment")
        box.prop(settings, "split_by_group")
        _section_header(box, "Drawable Dictionary")
        box.prop(settings, "import_ext_skeleton")  # Drawable Dictionary

        _section_header(box, "YTYP")
        box.prop(settings, "ytyp_mlo_instance_entities")

        _section_header(box, "YMAP")
        box.prop(settings, "ymap_skip_missing_entities")
        box.prop(settings, "ymap_exclude_entities")
        box.prop(settings, "ymap_instance_entities")
        box.prop(settings, "ymap_box_occluders")
        box.prop(settings, "ymap_model_occluders")
        box.prop(settings, "ymap_car_generators")

        # Export settings
        box = layout.box()
        box.label(text="Export", icon="EXPORT")
        settings = self.export_settings

        row = box.row(heading="Limit To")
        row.prop(settings, "limit_to_selected", text="Selected Objects")

        _section_header(box, "Drawable")
        box.prop(settings, "apply_transforms")
        box.prop(settings, "export_with_ytyp")
        box.prop(settings, "mesh_domain", expand=True)

        _section_header(box, "Fragment")
        box.column().prop(settings, "export_lods")

        _section_header(box, "Drawable Dictionary")
        box.prop(settings, "exclude_skeleton")

        _section_header(box, "YMAP")
        box.prop(settings, "ymap_exclude_entities")
        box.prop(settings, "ymap_box_occluders")
        box.prop(settings, "ymap_model_occluders")
        box.prop(settings, "ymap_car_generators")

    def draw_keymap(self, context, layout: UILayout):
        wm = bpy.context.window_manager
        kc = wm.keyconfigs.user

        keymaps = (
            "3D View",
            "3D View Tool: Object, Edit Archetype Extensions",
            "Dopesheet",
            "NLA Editor"
        )

        for keymap in keymaps:
            km = kc.keymaps.get(keymap)

            column = layout.column(align=True)
            row = column.row()
            row.label(text=keymap)

            for kmi in km.keymap_items:
                if (
                    (kmi.idname == "wm.call_menu_pie" and kmi.name.startswith("Sollumz")) or
                    kmi.idname.startswith("sollumz.")
                ):
                    column = layout.column(align=True)
                    row = column.row()
                    rna_keymap_ui.draw_kmi(["ADDON", "USER", "DEFAULT"], kc, km, kmi, row, 1)

            if keymap != keymaps[-1]:
                _line_separator(layout)

    def draw_ui(self, context, layout: UILayout):
        layout.prop(self, "show_vertex_painter")
        layout.prop(self, "extra_color_swatches")
        layout.prop(self, "sollumz_icon_header")

    def draw_theme(self, context, layout: UILayout):
        def _section_header(layout: UILayout, text: str, icon: str, first: bool = False):
            if not first:
                _line_separator(layout)
            row = layout.row()
            row.label(text=text, icon=icon)

        row = layout.row()
        row.alignment = "RIGHT"
        row.operator(SOLLUMZ_OT_prefs_theme_reset.bl_idname, text="      Reset      ", icon="LOOP_BACK")

        layout.separator()

        theme = self.theme
        _section_header(layout, "MLO Gizmos", "HOME", True)
        layout.prop(theme, "mlo_gizmo_room")
        layout.prop(theme, "mlo_gizmo_room_selected")
        layout.prop(theme, "mlo_gizmo_portal")
        layout.prop(theme, "mlo_gizmo_portal_selected")
        layout.prop(theme, "mlo_gizmo_portal_direction")
        layout.prop(theme, "mlo_gizmo_portal_direction_size")

        _section_header(layout, "Cable Overlays", "OUTLINER_DATA_GREASEPENCIL")
        layout.prop(theme, "cable_overlay_radius")

        _section_header(layout, "Cloth Overlays", "MATCLOTH")
        layout.prop(theme, "cloth_overlay_pinned")
        layout.prop(theme, "cloth_overlay_pinned_size")
        layout.prop(theme, "cloth_overlay_material_errors")
        layout.prop(theme, "cloth_overlay_binding_errors")
        layout.prop(theme, "cloth_overlay_binding_errors_size")

    def draw_about(self, context, layout: UILayout):
        row = layout.row()
        row.operator("wm.url_open", text="Discord", icon="COMMUNITY").url = "https://discord.gg/bZuWBWaQBg"
        row.operator("wm.url_open", text="Documentation", icon="HELP").url = "https://docs.sollumz.org/"
        row.operator("wm.url_open", text="Issue Tracker", icon="URL").url = "https://github.com/Sollumz/Sollumz/issues"

        layout.separator(factor=4.0)

        # TODO: should store benefactors lists somewhere else that can be easily updated
        studio_benefactors = [("TStudio by TurboSaif", "https://turbosaif.tebex.io/")]
        silver_benefactors = ["Tafé", "P-lauski", "Apollo"]
        benefactors = "BrunX • Clementinise • Kuz • Eryxiz • rkangur • DOIIDAUM • L'kid • Unknown-TV • Ktoś • Reveler • SevenLife"

        row = layout.row()
        row.alignment = "CENTER"
        row.label(text="Thank You")

        row = layout.row()
        row.alignment = "CENTER"
        row.label(text="", icon="KEYTYPE_EXTREME_VEC")
        row.label(text="Studio Benefactors")
        row.label(text="", icon="KEYTYPE_EXTREME_VEC")
        layout.separator()
        for name, url in studio_benefactors:
            row = layout.row()
            row.alignment = "CENTER"
            row.emboss = "PULLDOWN_MENU"
            row.operator("wm.url_open", text=f"   {name}   ", icon="URL").url = url

        _line_separator(layout, factor=2.0)
        row = layout.row()
        row.alignment = "CENTER"
        row.label(text="", icon="HANDLETYPE_FREE_VEC")
        row.label(text="Silver Benefactors")
        row.label(text="", icon="HANDLETYPE_FREE_VEC")
        layout.separator()
        for name in silver_benefactors:
            row = layout.row()
            row.alignment = "CENTER"
            row.label(text=name)

        _line_separator(layout, factor=2.0)
        row = layout.row()
        row.alignment = "CENTER"
        row.label(text="", icon="REMOVE")
        row.label(text="Benefactors")
        row.label(text="", icon="REMOVE")
        layout.separator()
        # https://b3d.interplanety.org/en/multiline-text-in-blender-interface-panels/
        chars = int(context.region.width * 0.75 / 7)   # 7 pix on 1 character, 0.75 for margins
        wrapper = textwrap.TextWrapper(width=chars)
        text_lines = wrapper.wrap(text=benefactors)
        for text_line in text_lines:
            row = layout.row()
            row.alignment = "CENTER"
            row.label(text=text_line)

        layout.separator(factor=4.0)

        row = layout.row()
        row.alignment = "CENTER"
        row.label(text="Help Support Development")
        row = layout.row()
        row.operator("wm.url_open", text="Open Collective", icon="URL").url = "https://opencollective.com/sollumz"
        row.operator("wm.url_open", text="GitHub Sponsors", icon="URL").url = "https://github.com/sponsors/Sollumz/"

        layout.separator()

        pass

    def register():
        _load_preferences()


def _line_separator(layout: UILayout, factor: float = 1.0):
    if bpy.app.version >= (4, 2, 0):
        layout.separator(type="LINE", factor=factor)
    else:
        layout.separator(factor=factor)


def get_addon_preferences(context: Optional[bpy.types.Context] = None) -> SollumzAddonPreferences:
    return context.preferences.addons[__package__].preferences


def get_import_settings(context: Optional[bpy.types.Context] = None) -> SollumzImportSettings:
    return get_addon_preferences(context or bpy.context).import_settings


def get_export_settings(context: Optional[bpy.types.Context] = None) -> SollumzExportSettings:
    return get_addon_preferences(context or bpy.context).export_settings


def get_theme_settings(context: Optional[bpy.types.Context] = None) -> SollumzThemeSettings:
    return get_addon_preferences(context or bpy.context).theme


def _save_preferences():
    addon_prefs = get_addon_preferences(bpy.context)
    prefs_path = get_prefs_path()

    config = ConfigParser()
    prefs_dict = _get_bpy_struct_as_dict(addon_prefs)
    main_prefs: dict[str, Any] = {}

    for key, value in prefs_dict.items():
        if isinstance(value, dict):
            config[key] = value
            continue

        main_prefs[key] = value

    config["main"] = main_prefs

    with open(prefs_path, "w") as f:
        config.write(f)


def _load_preferences():
    # Preferences are loaded via an ini file in <user_blender_path>/<version>/config/sollumz_prefs.ini
    addon_prefs = get_addon_preferences(bpy.context)
    if addon_prefs is None:
        return

    prefs_path = get_prefs_path()
    if not os.path.isfile(prefs_path):
        return

    config = ConfigParser()
    config.read(prefs_path)
    config_dict = {}
    for section in config.keys():
        if section == "DEFAULT":
            continue

        if section == "main":
            config_dict.update(config["main"])
        else:
            config_dict[section] = dict(config[section])

    _update_bpy_struct_from_dict(addon_prefs, config_dict, eval_strings=True)


def _get_bpy_struct_as_dict(struct: bpy_struct) -> dict:
    def _prop_to_value(key: str):
        prop = getattr(struct, key)
        if isinstance(prop, str):
            prop = repr(prop)  # repr adds quotes and escapes the string, so ast.literal_eval can parse it correctly later
        elif isinstance(prop, bpy_prop_array):
            prop = tuple(prop)
        elif isinstance(prop, bpy_prop_collection):
            prop = _get_bpy_collection_as_list(prop)
        elif isinstance(prop, bpy_struct):
            prop = _get_bpy_struct_as_dict(prop)

        return prop

    return {
        key: _prop_to_value(key)
        for key in struct.__annotations__.keys()
    }


def _update_bpy_struct_from_dict(struct: bpy_struct, values: dict, eval_strings: bool = False):
    for key in struct.__annotations__.keys():
        value = values.get(key, None)
        if value is None:
            continue

        if eval_strings and isinstance(value, str):
            value = ast.literal_eval(value)

        prop = getattr(struct, key)
        if isinstance(prop, bpy_prop_collection):
            assert isinstance(value, list)
            _update_bpy_collection_from_list(prop, value)
        elif isinstance(prop, bpy_struct):
            assert isinstance(value, dict)
            _update_bpy_struct_from_dict(prop, value, eval_strings=eval_strings)
        else:
            setattr(struct, key, value)


def _get_bpy_collection_as_list(collection: bpy_prop_collection) -> list:
    return list(
        entry_tuple if len(entry_tuple) > 1 else entry_tuple[0]
        for entry_tuple in map(_get_bpy_struct_as_tuple, collection)
    )


def _update_bpy_collection_from_list(collection: bpy_prop_collection, entries: list):
    collection.clear()
    for entry_tuple in entries:
        entry = collection.add()
        _update_bpy_struct_from_tuple(entry, entry_tuple)


def _get_bpy_struct_as_tuple(struct: bpy_struct) -> tuple:
    return tuple(
        getattr(struct, key)
        for key in struct.__annotations__.keys()
    )


def _update_bpy_struct_from_tuple(struct: bpy_struct, values: tuple | object):
    keys = list(struct.__annotations__.keys())
    values_is_tuple = isinstance(values, tuple)
    num_values = len(values) if values_is_tuple else 1
    if len(keys) != num_values:
        raise ValueError(f"Incorrect number of values in tuple: expected {len(keys)}, got {len(values)}")

    if not values_is_tuple:
        values = (values,)

    for key, value in zip(keys, values):
        setattr(struct, key, value)


def get_prefs_path():
    return os.path.join(bpy.utils.user_resource(resource_type="CONFIG"), PREFS_FILE_NAME)


def get_config_directory_path() -> str:
    return bpy.utils.user_resource(resource_type="CONFIG", path="sollumz", create=True)


def register():
    bpy.utils.register_class(SollumzAddonPreferences)


def unregister():
    bpy.utils.unregister_class(SollumzAddonPreferences)
