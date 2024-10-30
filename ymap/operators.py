import bpy
from ..sollumz_helper import SOLLUMZ_OT_base, set_object_collection
from ..tools.ymaphelper import add_occluder_material, create_ymap, create_ymap_group, get_cargen_mesh, generate_ymap_extents
from ..sollumz_properties import SollumType


class SOLLUMZ_OT_create_ymap(SOLLUMZ_OT_base, bpy.types.Operator):
    """Add a ymap to the project"""
    bl_idname = "sollumz.createymap"
    bl_label = "Create YMAP"

    def run(self, context):
        item = context.scene.ymaps.add()
        index = len(context.scene.ymaps)
        item.name = f"YMAP.{index}"
        context.scene.ymap_index = index - 1

        return True


class SOLLUMZ_OT_delete_ymap(SOLLUMZ_OT_base, bpy.types.Operator):
    """Delete a ymap from the project"""
    bl_idname = "sollumz.deleteymap"
    bl_label = "Delete YMAP"

    @classmethod
    def poll(cls, context):
        return len(context.scene.ymaps) > 0

    def run(self, context):
        context.scene.ymaps.remove(context.scene.ymap_index)
        context.scene.ymap_index = max(context.scene.ymap_index - 1, 0)
        # Force redraw of gizmos
        context.space_data.show_gizmo = context.space_data.show_gizmo

        return True


class SOLLUMZ_OT_import_ymap(SOLLUMZ_OT_base, bpy.types.Operator):
    """Import a ymap.xml"""
    bl_idname = "sollumz.importymap"
    bl_label = "Import ymap.xml"
    bl_action = "Import a YMAP"

    def run(self, context):
        self.report({'INFO'}, "Import YMAP - Work in progress")


class SOLLUMZ_OT_export_ymap(SOLLUMZ_OT_base, bpy.types.Operator):
    """Export a ymap.xml"""
    bl_idname = "sollumz.exportymap"
    bl_label = "Export ymap.xml"
    bl_action = "Export a YMAP"

    @classmethod
    def poll(cls, context):
        num_ymaps = len(context.scene.ymaps)
        return num_ymaps > 0 and context.scene.ymap_index < num_ymaps

    def run(self, context):
        self.report({'INFO'}, "Export YMAP - Work in progress")


class SOLLUMZ_OT_generate_ymap_extents(bpy.types.Operator):
    bl_idname = "sollumz.generate_ymap_extents"
    bl_label = "Generate Ymap Extents"
    bl_description = "Generate the YMAP's streaming and entity extents (using YMAP and YMAP entities data)"

    def execute(self, context):
        generate_ymap_extents(selected_ymap=context.active_object)
        return {"FINISHED"}
