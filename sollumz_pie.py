import bpy
from bpy.types import Menu


def find_missing_files(filepath):
    bpy.ops.file.find_missing_files(directory=filepath)
    return {'FINISHED'}


class SOLLUMZ_MT_pie_menu(Menu):
    bl_idname = "SOLLUMZ_MT_pie_menu"
    bl_label = "Sollumz Pie Menu"

    def draw(self, context):

        layout = self.layout

        pie = layout.menu_pie()
        # Left
        pie.operator("sollumz.autoconvertmaterials",
                     text="Convert Material", icon='NODE_MATERIAL')
        # Right
        pie.operator("sollumz.addobjasentity", icon='OBJECT_DATA')

        # Bottom
        pie.operator("sollumz.load_flag_preset",
                     text="Apply Flag Preset", icon='ALIGN_TOP')
        # Top
        pie.operator("file.find_missing_files",
                     text="Find Missing Textures", icon='VIEWZOOM')
        # Top-left
        pie.operator("sollumz.import_assets",
                     text="Import CodeWalker XML", icon='IMPORT')
        # Top-right
        if context.scene.sollumz_export_path != "":
            op = pie.operator("sollumz.export_assets", text="Export CodeWalker XML", icon='EXPORT')
            op.directory = context.scene.sollumz_export_path
            op.direct_export = True
        else:
            pie.operator("sollumz.export_assets", text="Export CodeWalker XML", icon='EXPORT')
        # Bottom-left
        pie.operator("sollumz.converttodrawable", icon='CUBE')
        # Bottom-right
        pie.operator("sollumz.converttocomposite", icon='CUBE')


class SOLLUMZ_MT_view_pie_menu(Menu):
    bl_idname = "SOLLUMZ_MT_view_pie_menu"
    bl_label = "Sollumz Object Visibility"

    def draw(self, context):
        from .sollumz_ui import SOLLUMZ_UI_NAMES
        from .lods import (
            LODLevel,
            SOLLUMZ_OT_set_lod_level,
            SOLLUMZ_OT_hide_object,
            SOLLUMZ_OT_HIDE_COLLISIONS,
            SOLLUMZ_OT_HIDE_SHATTERMAPS,
            SOLLUMZ_OT_SHOW_COLLISIONS,
            SOLLUMZ_OT_SHOW_SHATTERMAPS
        )

        layout = self.layout
        scene = context.scene

        pie = layout.menu_pie()
        # Left
        pie.operator((SOLLUMZ_OT_HIDE_COLLISIONS if scene.sollumz_show_collisions else SOLLUMZ_OT_SHOW_COLLISIONS).bl_idname)
        # Right, Bottom, Top
        for lod in (LODLevel.MEDIUM, LODLevel.VERYLOW, LODLevel.VERYHIGH):
            pie.operator(SOLLUMZ_OT_set_lod_level.bl_idname, text=SOLLUMZ_UI_NAMES[lod]).lod_level = lod
        # Top-left
        pie.operator((SOLLUMZ_OT_HIDE_SHATTERMAPS if scene.sollumz_show_shattermaps else SOLLUMZ_OT_SHOW_SHATTERMAPS).bl_idname)
        # Top-right
        pie.operator(SOLLUMZ_OT_set_lod_level.bl_idname, text=SOLLUMZ_UI_NAMES[LODLevel.HIGH]).lod_level = LODLevel.HIGH
        # Bottom-left
        pie.operator(SOLLUMZ_OT_hide_object.bl_idname, text="Hide")
        # Bottom-right
        pie.operator(SOLLUMZ_OT_set_lod_level.bl_idname, text=SOLLUMZ_UI_NAMES[LODLevel.LOW]).lod_level = LODLevel.LOW


addon_keymaps = []


def register():

    # Assigns default keybinding
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new(
            "wm.call_menu_pie", type='V', value='PRESS', shift=False)
        kmi.properties.name = "SOLLUMZ_MT_pie_menu"

        addon_keymaps.append((km, kmi))

        kmi = km.keymap_items.new(
            "wm.call_menu_pie", type='V', value='PRESS', shift=True)
        kmi.properties.name = "SOLLUMZ_MT_view_pie_menu"

        addon_keymaps.append((km, kmi))


def unregister():

    # default keybinding
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()


if __name__ == "__main__":
    register()
