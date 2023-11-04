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
        pie.operator("sollumz.autoconvertmaterial",
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
        pie.operator("sollumz.import",
                     text="Import CodeWalker XML", icon='IMPORT')
        # Top-right
        if context.scene.sollumz_export_path != "":
            op = pie.operator("sollumz.export", text="Export CodeWalker XML", icon='EXPORT')
            op.directory = context.scene.sollumz_export_path
            op.direct_export = True
        else:
            pie.operator("sollumz.export", text="Export CodeWalker XML", icon='EXPORT')
        # Bottom-left
        pie.operator("sollumz.converttodrawable", icon='CUBE')
        # Bottom-right
        pie.operator("sollumz.converttocomposite", icon='CUBE')


class SOLLUMZ_MT_view_pie_menu(Menu):
    bl_idname = "SOLLUMZ_MT_view_pie_menu"
    bl_label = "Sollumz Object Visibility"

    def draw(self, context):
        layout = self.layout

        pie = layout.menu_pie()
        # Left
        if context.scene.sollumz_show_collisions:
            pie.operator("sollumz.hide_collisions")
        else:
            pie.operator("sollumz.show_collisions")
        # Right
        pie.operator("sollumz.set_lod_med")
        # Bottom
        pie.operator("sollumz.set_lod_vlow")
        # Top
        pie.operator("sollumz.set_lod_very_high")
        # Top-left
        if context.scene.sollumz_show_shattermaps:
            pie.operator("sollumz.hide_shattermaps")
        else:
            pie.operator("sollumz.show_shattermaps")
        # Top-right
        pie.operator("sollumz.set_lod_high")
        # Bottom-left
        pie.operator("sollumz.hide_object", text="Hide")
        # Bottom-right
        pie.operator("sollumz.set_lod_low")


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
