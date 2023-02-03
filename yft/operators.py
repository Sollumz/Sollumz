import bpy
from mathutils import Matrix
from ..sollumz_properties import SollumType
from ..tools.blenderhelper import create_blender_object
from ..ydr.create_drawable_models import add_armature_constraint


class SOLLUMZ_OT_CREATE_FRAGMENT(bpy.types.Operator):
    """Create a Fragment object"""
    bl_idname = "sollumz.createfragment"
    bl_label = "Create Fragment"

    def execute(self, context):
        selected = context.selected_objects

        if selected:
            parent = selected[0]
        else:
            parent = None

        armature = bpy.data.armatures.new(name="skel")
        frag_obj = create_blender_object(
            SollumType.FRAGMENT, object_data=armature)
        frag_obj.parent = parent

        return {"FINISHED"}


class SOLLUMZ_OT_CREATE_BONES_AT_OBJECTS(bpy.types.Operator):
    """Create bones with physics enabled for all selected objects. Bones are positioned at the location of each object"""
    bl_idname = "sollumz.createbonesatobjects"
    bl_label = "Create Physics Bones at Object(s)"
    bl_options = {"UNDO"}

    def execute(self, context):
        armature_obj: bpy.types.Object = context.scene.create_bones_fragment
        selected = [
            obj for obj in context.selected_objects if obj != armature_obj]
        parent_to_selected = context.scene.create_bones_parent_to_selected
        # parent_bone: bpy.types.Bone | None = context.scene.create_bones_parent_bone

        if not selected:
            self.report({"INFO"}, "No objects selected!")
            return {"CANCELLED"}

        if armature_obj.type != "ARMATURE":
            self.report({"INFO"}, f"{armature_obj.name} is not an armature!")
            return {"CANCELLED"}

        armature: bpy.types.Armature = armature_obj.data

        # Need to go into edit mode to modify edit bones
        bpy.ops.object.mode_set(mode="EDIT")

        if context.selected_bones and parent_to_selected:
            parent = context.selected_bones[0]
        else:
            parent = None

        for obj in selected:
            edit_bone = armature.edit_bones.new(obj.name)

            edit_bone.head = (0, 0, 0)
            edit_bone.tail = (0, 0.05, 0)

            edit_bone.matrix = Matrix.Translation(obj.location)

            if parent is not None:
                edit_bone.parent = parent

        bpy.ops.object.mode_set(mode="OBJECT")

        for obj in selected:
            armature.bones[obj.name].sollumz_use_physics = True

            add_armature_constraint(
                obj, armature_obj, obj.name, set_transforms=False)

        return {"FINISHED"}


class SOLLUMZ_OT_SET_MASS(bpy.types.Operator):
    """Set the mass of all selected objects"""
    bl_idname = "sollumz.setmass"
    bl_label = "Set Mass"
    bl_options = {"UNDO"}

    def execute(self, context):
        set_mass_amount = context.scene.set_mass_amount

        for obj in context.selected_objects:
            obj.child_properties.mass = set_mass_amount

        return {"FINISHED"}
