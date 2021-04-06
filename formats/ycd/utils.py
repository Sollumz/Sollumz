import bpy

def find_armatures():
    armatures = []
    for obj in bpy.context.scene.collection.objects:
        if isinstance(obj.data, bpy.types.Armature):
            if find_bone_by_tag(obj, 0):
                armatures.append(obj)

    return armatures

def find_bone_by_tag(armature, tag):
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')

    for bone in armature.pose.bones:
        if bone.bone.bone_properties.tag == tag:
            return bone

    return None
