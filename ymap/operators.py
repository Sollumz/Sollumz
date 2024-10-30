import bpy
from ..sollumz_helper import SOLLUMZ_OT_base, set_object_collection
from ..tools.ymaphelper import add_occluder_material, create_ymap, create_ymap_group, get_cargen_mesh, generate_ymap_extents
from ..sollumz_properties import SollumType
from .utils import get_selected_ymap, get_active_element_list


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


class SOLLUMZ_OT_add_ymap_element(SOLLUMZ_OT_base, bpy.types.Operator):
    """Add the selected object to a ymap"""
    bl_idname = "sollumz.addelement"
    bl_label = "Add Selected"
    bl_action = "Add an Element"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.select_get()
    
    def execute(self, context):
        selected_objects = bpy.context.selected_objects
        active_ymap = get_selected_ymap(context)
        
        list_name, index_attr = get_active_element_list(context)
        element_list = getattr(active_ymap, list_name, None)
        
        for active_obj in selected_objects:
            if active_obj.select_get():
                new_item = element_list.add()
                new_item.name = active_obj.name
        
        setattr(active_ymap, index_attr, len(element_list) - 1)
        
        return {'FINISHED'}


class SOLLUMZ_OT_del_ymap_element(SOLLUMZ_OT_base, bpy.types.Operator):
    """Delete the selected ymap element"""
    bl_idname = "sollumz.delelement"
    bl_label = "Delete Selected"
    bl_action = "Delete an Element"

    @classmethod
    def poll(cls, context):
        active_ymap = get_selected_ymap(context)
        list_name, index_attr = get_active_element_list(context)
        element_list = getattr(active_ymap, list_name, None)
        return active_ymap is not None and element_list and len(element_list) > 0
    
    def execute(self, context):
        active_ymap = get_selected_ymap(context)
        list_name, index_attr = get_active_element_list(context)
        element_list = getattr(active_ymap, list_name, None)
        
        active_index = getattr(active_ymap, index_attr)
        element_list.remove(active_index)
        
        setattr(active_ymap, index_attr, max(getattr(active_ymap, index_attr) - 1, 0))
        
        return {'FINISHED'}


class SOLLUMZ_OT_generate_ymap_extents(bpy.types.Operator):
    bl_idname = "sollumz.generate_ymap_extents"
    bl_label = "Generate Ymap Extents"
    bl_description = "Generate the YMAP's streaming and entity extents (using YMAP and YMAP entities data)"

    def execute(self, context):
        generate_ymap_extents(selected_ymap=context.active_object)
        return {"FINISHED"}
