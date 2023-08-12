from math import radians
import bpy
import bmesh
from mathutils import Matrix, Vector

from ..tools.meshhelper import calculate_volume, get_combined_bound_box

from ..sollumz_helper import find_sollumz_parent
from ..sollumz_properties import BOUND_POLYGON_TYPES, BOUND_TYPES, MaterialType, SollumType, VehicleLightID
from ..tools.blenderhelper import add_child_of_bone_constraint, create_blender_object, create_empty_object, get_child_of_bone
from ..ybn.collision_materials import collisionmats


class SOLLUMZ_OT_CREATE_FRAGMENT(bpy.types.Operator):
    """Create a Fragment object. If a Drawable or Bound Composite is selected,
    they will be parented to the Fragment."""
    bl_idname = "sollumz.createfragment"
    bl_label = "Create Fragment"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        armature = bpy.data.armatures.new(name="skel")
        frag_obj = create_blender_object(
            SollumType.FRAGMENT, object_data=armature)

        self.parent_selected_objs(frag_obj, context)

        return {"FINISHED"}

    def parent_selected_objs(self, frag_obj: bpy.types.Object, context):
        selected = context.selected_objects

        for obj in selected:
            if obj.sollum_type in [SollumType.DRAWABLE, SollumType.BOUND_COMPOSITE]:
                obj.parent = frag_obj


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


class SOLLUMZ_OT_GENERATE_WHEEL_INSTANCES(bpy.types.Operator):
    """
    Generate instances of wheel mesh to preview all 4 wheels at once (has no effect on export)
    """
    bl_idname = "sollumz.generate_wheel_instances"
    bl_label = "Generate Wheel Instances"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        aobj = context.active_object

        return aobj is not None and aobj.sollumz_is_physics_child_mesh and aobj.type == "MESH"

    def execute(self, context):
        aobj = context.active_object
        frag_obj = find_sollumz_parent(aobj, SollumType.FRAGMENT)

        if frag_obj is None:
            self.report({"INFO"}, "Object must be parented to a Fragment!")
            return {"CANCELLED"}

        child_of_bone = get_child_of_bone(aobj)

        if child_of_bone is None:
            self.report(
                {"WARNING"}, "Failed to create instances. The object has no Child Of constraint or the constraint bone is not set!")
            return {"CANCELLED"}

        wheel_bones = {"wheel_lf", "wheel_lr", "wheel_rf", "wheel_rr"}
        empty = create_empty_object(
            SollumType.NONE, f"{frag_obj.name}.wheel_previews")
        empty.parent = frag_obj

        for bone_name in wheel_bones:
            if bone_name == child_of_bone.name or bone_name not in frag_obj.data.bones:
                continue

            instance = create_blender_object(
                SollumType.NONE, f"{bone_name}.preview", aobj.data)
            add_child_of_bone_constraint(instance, frag_obj, bone_name)

            # Rotate wheels on the other side
            if ("_l" in child_of_bone.name and "_r" in bone_name) or ("_r" in child_of_bone.name and "_l" in bone_name):
                instance.matrix_world = Matrix.Rotation(
                    radians(180), 4, "Y") @ instance.matrix_world
            instance.parent = empty

        return {"FINISHED"}


class SOLLUMZ_OT_CALCULATE_MASS(bpy.types.Operator):
    """Calculate (approximate) mass for collision based on it's volume and density"""
    bl_idname = "sollumz.calculate_mass"
    bl_label = "Calculate Collision Mass"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(self, context):
        return context.selected_objects

    def execute(self, context):
        for obj in context.selected_objects:
            if obj.sollum_type in BOUND_POLYGON_TYPES:
                self.report(
                    {"INFO"}, f"{obj.name} is a Bound Polygon! Select the Bound Geometry BVH instead! Skipping...")
                continue

            if obj.sollum_type not in BOUND_TYPES or obj.sollum_type == SollumType.BOUND_COMPOSITE:
                self.report(
                    {"INFO"}, f"{obj.name} not a Sollumz bound type! Skipping...")
                continue

            if obj.sollum_type == SollumType.BOUND_GEOMETRYBVH:
                mass = self.calculate_bvh_mass(obj)
                obj.child_properties.mass = mass
                continue

            mat = self.get_collision_mat(obj)

            if mat is None:
                self.report(
                    {"INFO"}, f"{obj.name} has no collision materials! Skipping...")
                continue

            mass = self.calculate_mass(obj, mat)

            obj.child_properties.mass = mass

        self.report({"INFO"}, "Mass successfully calculated.")

        return {"FINISHED"}

    def calculate_bvh_mass(self, obj: bpy.types.Object) -> float:
        mass = 0.0

        for child in obj.children:
            if child.sollum_type not in BOUND_POLYGON_TYPES or child.type != "MESH":
                continue

            mat = self.get_collision_mat(child)

            if mat is None:
                continue

            mass += self.calculate_mass(child, mat)

        return mass

    def calculate_mass(self, obj: bpy.types.Object, mat: bpy.types.Material) -> float:
        bbmin, bbmax = get_combined_bound_box(obj, use_world=True)
        volume = calculate_volume(bbmin, bbmax)
        density = collisionmats[mat.collision_properties.collision_index].density

        return volume * density

    def get_collision_mat(self, obj: bpy.types.Object):
        for mat in obj.data.materials:
            if mat.sollum_type == MaterialType.COLLISION:
                return mat
