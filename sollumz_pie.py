import bpy
from bpy.types import Menu

def find_missing_files(filepath):
    bpy.ops.file.find_missing_files(directory=filepath)
    return {'FINISHED'}


class OokSollumzPie(Menu):
    bl_idname = "OOK_MT_sollumz_pie"
    bl_label = "Sollumz Pie"

    def draw(self, context):

        layout = self.layout

        pie = layout.menu_pie()
        pie.operator("sollumz.autoconvertmaterial",
                     text="Convert Material", icon='NODE_MATERIAL')
        pie.operator("sollumz.addobjasmloentity",
                     text="Add Objects To Room", icon='OBJECT_DATA')
        pie.operator("sollumz.load_flag_preset",
                     text="Apply Flag Preset", icon='ALIGN_TOP')
        pie.operator("sollumz.createdrawable",
                     text="Create Drawable", icon='CUBE')
        pie.operator("file.find_missing_files",
                     text="Find Missing Textures", icon='VIEWZOOM')
        pie.operator("sollumz.export",
                     text="Export CodeWalker XML", icon='EXPORT')
        pie.operator("sollumz.importymap",
                     text="Import XML YMAP", icon='FILE_VOLUME')
        pie.operator("sollumz.exportymap",
                     text="Export XML YMAP", icon='ASSET_MANAGER')


addon_keymaps = []


def register():

    # Assigns default keybinding
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new(
            "wm.call_menu_pie", type='V', value='PRESS', shift=False)
        kmi.properties.name = "OOK_MT_sollumz_pie"

        addon_keymaps.append((km, kmi))


def unregister():

    # default keybinding
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()


if __name__ == "__main__":
    register()

    bpy.ops.wm.call_menu_pie(name="OOK_MT_sollumz_pie")
