import bpy

def find_armatures():
    armatures = []
    for obj in bpy.context.scene.collection.objects:
        if isinstance(obj.data, bpy.types.Armature):
            armatures.append(obj)

    return armatures

def find_bone_by_tag(tag):
    for armature_object in find_armatures():

        bpy.context.view_layer.objects.active = armature_object
        bpy.ops.object.mode_set(mode='POSE')

        for bone in armature_object.pose.bones:
            if bone.bone.bone_properties.tag == tag:
                return bone
    return None
