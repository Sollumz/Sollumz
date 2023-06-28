import bpy
import bmesh
from mathutils import Matrix, Vector
from ..sollumz_properties import SollumType, VehicleLightID
from ..tools.blenderhelper import add_child_of_bone_constraint, create_blender_object


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
        bpy.context.view_layer.objects.active = armature_obj
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

            add_child_of_bone_constraint(obj, armature_obj, obj.name)
            obj.location = Vector()

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


class SOLLUMZ_OT_SET_LIGHT_ID(bpy.types.Operator):
    """
    Set the vehicle light ID of the selected vertices (must be in edit mode). 
    This determines which action causes the emissive shader to activate, and is stored in the alpha channel of the vertex colors
    """
    bl_idname = "sollumz.setlightid"
    bl_label = "Set Light ID"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        selected_mesh_objs = [
            obj for obj in context.selected_objects if obj.type == "MESH"]

        face_mode = context.scene.tool_settings.mesh_select_mode[2]

        return selected_mesh_objs and context.mode == "EDIT_MESH" and face_mode

    def execute(self, context):
        selected_mesh_objs = [
            obj for obj in context.selected_objects if obj.type == "MESH"]

        set_light_id = context.scene.set_vehicle_light_id

        if set_light_id == VehicleLightID.CUSTOM:
            light_id = context.scene.set_custom_vehicle_light_id
        else:
            light_id = int(set_light_id)

        alpha = light_id / 255

        for obj in selected_mesh_objs:
            bm = bmesh.from_edit_mesh(obj.data)

            if not bm.loops.layers.color:
                self.report(
                    {"INFO"}, f"'{obj.name}' has no 'Face Corner > Byte Color' color attribute layers! Skipping...")
                continue

            color_layer = bm.loops.layers.color[0]

            for face in bm.faces:
                if not face.select:
                    continue

                for loop in face.loops:
                    loop[color_layer][3] = alpha

        return {"FINISHED"}


class SOLLUMZ_OT_SELECT_LIGHT_ID(bpy.types.Operator):
    """
    Select vertices that have this light ID
    """
    bl_idname = "sollumz.selectlightid"
    bl_label = "Select Light ID"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        selected_mesh_objs = [
            obj for obj in context.selected_objects if obj.type == "MESH"]

        face_mode = context.scene.tool_settings.mesh_select_mode[2]

        return selected_mesh_objs and context.mode == "EDIT_MESH" and face_mode

    def execute(self, context):
        selected_mesh_objs = [
            obj for obj in context.selected_objects if obj.type == "MESH"]

        select_light_id = context.scene.select_vehicle_light_id

        if select_light_id == VehicleLightID.CUSTOM:
            light_id = context.scene.select_custom_vehicle_light_id
        else:
            light_id = int(select_light_id)

        for obj in selected_mesh_objs:
            mesh = obj.data
            bm = bmesh.from_edit_mesh(mesh)

            if not bm.loops.layers.color:
                continue

            color_layer = bm.loops.layers.color[0]

            face_inds = self.get_light_id_faces(bm, color_layer, light_id)

            mode = obj.mode
            if obj.mode != "OBJECT":
                bpy.ops.object.mode_set(mode="OBJECT")

            for i in face_inds:
                mesh.polygons[i].select = True

            bpy.ops.object.mode_set(mode=mode)

        return {"FINISHED"}

    def get_light_id_faces(self, bm: bmesh.types.BMesh, color_layer: bmesh.types.BMLayerCollection, light_id: int):
        """Get light id of the given selection of ``mesh``. Returns -1 if not found or vertices contain different light IDs"""
        face_inds: list[int] = []

        for face in bm.faces:
            for loop in face.loops:
                loop_light_id = int(loop[color_layer][3] * 255)

                if loop_light_id == light_id:
                    face_inds.append(face.index)
                    break

        return face_inds
