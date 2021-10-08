import bpy

class SOLLUMZ_OT_BONE_FLAGS_NewItem(bpy.types.Operator): 
    bl_idname = "sollumz.bone_flags_new_item" 
    bl_label = "Add a new item"
    def execute(self, context): 
        bone = context.active_pose_bone.bone
        bone.bone_properties.flags.add() 
        return {'FINISHED'}

class SOLLUMZ_OT_BONE_FLAGS_DeleteItem(bpy.types.Operator): 
    bl_idname = "sollumz.bone_flags_delete_item" 
    bl_label = "Deletes an item" 
    @classmethod 
    def poll(cls, context): 
        return context.active_pose_bone.bone.bone_properties.flags

    def execute(self, context): 
        bone = context.active_pose_bone.bone

        list = bone.bone_properties.flags
        index = bone.bone_properties.ul_index
        list.remove(index) 
        bone.bone_properties.ul_index = min(max(0, index - 1), len(list) - 1) 
        return {'FINISHED'}