import bpy
from ..sollumz_properties import SollumType


class SOLLUMZ_OT_ADD_FRAG_LOD(bpy.types.Operator):
    bl_idname = "sollumz.addfraglod"
    bl_label = "Add LOD"

    @classmethod
    def poll(cls, context):
        active_obj = context.view_layer.objects.active
        if active_obj is None or active_obj.sollum_type != SollumType.FRAGMENT:
            return False

        return 3 > len(active_obj.sollumz_fragment_lods) >= 0

    def execute(self, context):
        active_obj = context.view_layer.objects.active
        frag_lods = active_obj.sollumz_fragment_lods
        frag_lods.add()

        return {"FINISHED"}


class SOLLUMZ_OT_REMOVE_FRAG_LOD(bpy.types.Operator):
    bl_idname = "sollumz.removefraglod"
    bl_label = "Remove LOD"

    @classmethod
    def poll(cls, context):
        active_obj = context.view_layer.objects.active
        if active_obj is None or active_obj.sollum_type != SollumType.FRAGMENT:
            return False

        active_lod_index = active_obj.sollumz_active_frag_lod_index

        return active_lod_index < len(active_obj.sollumz_fragment_lods) or 1 > len(active_obj.sollumz_fragment_lods) > 0

    def execute(self, context):
        active_obj = context.view_layer.objects.active
        frag_lods = active_obj.sollumz_fragment_lods
        active_lod_index = active_obj.sollumz_active_frag_lod_index

        frag_lods.remove(active_lod_index)

        return {"FINISHED"}
