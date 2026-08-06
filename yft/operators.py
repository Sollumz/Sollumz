import bpy
import bmesh
import gpu
import numpy as np
from math import radians
from mathutils import Matrix, Vector
from itertools import chain

from szio.gta5 import AssetFormat, AssetVersion, AssetTarget, FragVehicleWindow
from ..tools.meshhelper import get_combined_bound_box
from ..shared.geometry import get_mass_properties_of_box
from ..sollumz_helper import find_sollumz_parent
from ..sollumz_properties import BOUND_POLYGON_TYPES, BOUND_TYPES, MaterialType, SollumType, VehicleLightID
from ..tools.blenderhelper import add_child_of_bone_constraint, create_blender_object, create_empty_object, get_child_of_bone
from ..ybn.collision_materials import collisionmats
from ..dependencies import IS_SZIO_NATIVE_AVAILABLE


class SOLLUMZ_OT_CREATE_FRAGMENT(bpy.types.Operator):
    """Create a Fragment object. If a Drawable or Bound Composite is selected, they will be parented to the Fragment"""
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


class SOLLUMZ_OT_COPY_FRAG_BONE_PHYSICS(bpy.types.Operator):
    """Copy the physics properties of the active bone to all selected bones. Can only be used in Pose Mode"""
    bl_idname = "sollumz.copy_frag_bone_physics"
    bl_label = "Copy Bone Physics"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return context.mode == "POSE" and context.active_pose_bone is not None and len(context.selected_pose_bones) > 1

    def execute(self, context):
        src_pose_bone = context.active_pose_bone
        src_props = src_pose_bone.bone.group_properties
        num_dst_bones = 0
        for dst_pose_bone in context.selected_pose_bones:
            if dst_pose_bone == src_pose_bone:
                continue

            dst_props = dst_pose_bone.bone.group_properties
            dst_props.flags = src_props.flags
            dst_props.glass_type = src_props.glass_type
            dst_props.strength = src_props.strength
            dst_props.force_transmission_scale_up = src_props.force_transmission_scale_up
            dst_props.force_transmission_scale_down = src_props.force_transmission_scale_down
            dst_props.joint_stiffness = src_props.joint_stiffness
            dst_props.min_soft_angle_1 = src_props.min_soft_angle_1
            dst_props.max_soft_angle_1 = src_props.max_soft_angle_1
            dst_props.max_soft_angle_2 = src_props.max_soft_angle_2
            dst_props.max_soft_angle_3 = src_props.max_soft_angle_3
            dst_props.rotation_speed = src_props.rotation_speed
            dst_props.rotation_strength = src_props.rotation_strength
            dst_props.restoring_strength = src_props.restoring_strength
            dst_props.restoring_max_torque = src_props.restoring_max_torque
            dst_props.latch_strength = src_props.latch_strength
            dst_props.min_damage_force = src_props.min_damage_force
            dst_props.damage_health = src_props.damage_health
            dst_props.weapon_health = src_props.weapon_health
            dst_props.weapon_scale = src_props.weapon_scale
            dst_props.vehicle_scale = src_props.vehicle_scale
            dst_props.ped_scale = src_props.ped_scale
            dst_props.ragdoll_scale = src_props.ragdoll_scale
            dst_props.explosion_scale = src_props.explosion_scale
            dst_props.object_scale = src_props.object_scale
            dst_props.ped_inv_mass_scale = src_props.ped_inv_mass_scale
            dst_props.melee_scale = src_props.melee_scale

            num_dst_bones += 1

        self.report({'INFO'},
                    f"Physics properties of '{src_pose_bone.name}' copied to {num_dst_bones} bones successfully")
        return {'FINISHED'}


class SOLLUMZ_OT_SET_LIGHT_ID(bpy.types.Operator):
    bl_idname = "sollumz.setlightid"
    bl_label = "Set Light ID"
    bl_options = {"UNDO"}
    bl_description = (
        "Set the vehicle light ID of the selected vertices (must be in edit mode).\n\n"
        "This determines which action causes the emissive shader to activate, and is stored in the alpha channel of "
        "the vertex colors"
    )

    @classmethod
    def poll(cls, context):
        cls.poll_message_set("Must be in Edit Mode > Face Selection")

        selected_mesh_objs = [obj for obj in context.selected_objects if obj.type == "MESH"]

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
            try:
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
            finally:
                bm.free()

        return {"FINISHED"}


class SOLLUMZ_OT_SELECT_LIGHT_ID(bpy.types.Operator):
    """Select vertices that have this light ID"""
    bl_idname = "sollumz.selectlightid"
    bl_label = "Select Light ID"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        cls.poll_message_set("Must be in Edit Mode > Face Selection")

        selected_mesh_objs = [obj for obj in context.selected_objects if obj.type == "MESH"]

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
            try:
                if not bm.loops.layers.color:
                    continue

                color_layer = bm.loops.layers.color[0]

                face_inds = self.get_light_id_faces(bm, color_layer, light_id)
            finally:
                bm.free()

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
    """Generate instances of wheel meshes to preview all wheels at once (has no effect on export)"""
    bl_idname = "sollumz.generate_wheel_instances"
    bl_label = "Generate Wheel Instances"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object

        return obj is not None and find_sollumz_parent(obj, SollumType.FRAGMENT) is not None

    def execute(self, context):
        obj = context.active_object
        frag_obj = find_sollumz_parent(obj, SollumType.FRAGMENT)

        drawable_obj = next((obj for obj in frag_obj.children if obj.sollum_type == SollumType.DRAWABLE), None)
        if drawable_obj is None:
            self.report({"WARNING"}, "This fragment object is missing the drawable object!")
            return {"CANCELLED"}

        wheel_bones_front = {
            "wheel_lf", "wheel_rf",
        }
        wheel_bones_rear = {
            "wheel_lr", "wheel_lm1", "wheel_lm2", "wheel_lm3",
            "wheel_rr", "wheel_rm1", "wheel_rm2", "wheel_rm3",
        }

        wheel_front_obj = None
        wheel_rear_obj = None
        for model_obj in drawable_obj.children:
            if model_obj.sollum_type != SollumType.DRAWABLE_MODEL or not model_obj.sollumz_is_physics_child_mesh:
                continue

            parent_bone = get_child_of_bone(model_obj)
            if parent_bone.name in wheel_bones_front:
                wheel_front_obj = model_obj
            elif parent_bone.name in wheel_bones_rear:
                wheel_rear_obj = model_obj

        if wheel_front_obj is None and wheel_rear_obj is None:
            self.report({"WARNING"}, "No wheel meshes found in this fragment object!")
            return {"CANCELLED"}

        if wheel_front_obj is None:
            wheel_front_obj = wheel_rear_obj
        if wheel_rear_obj is None:
            wheel_rear_obj = wheel_front_obj

        # create objects in same collection as the fragment object
        with context.temp_override(collection=frag_obj.users_collection[0]):
            empty = create_empty_object(SollumType.NONE, f"{frag_obj.name}.wheel_previews")
            empty.parent = frag_obj

            for bone_name in chain(wheel_bones_front, wheel_bones_rear):
                if bone_name not in frag_obj.data.bones:
                    continue

                wheel_obj = wheel_front_obj if bone_name in wheel_bones_front else wheel_rear_obj
                wheel_obj_bone_name = get_child_of_bone(wheel_obj).name
                if wheel_obj_bone_name == bone_name:
                    continue

                instance = create_blender_object(SollumType.NONE, f"{bone_name}.preview", wheel_obj.data)
                add_child_of_bone_constraint(instance, frag_obj, bone_name)

                # Rotate wheels on the other side
                instance_is_left_side = "_l" in bone_name
                wheel_is_left_side = "_l" in wheel_obj_bone_name
                if instance_is_left_side != wheel_is_left_side:
                    instance.matrix_world = Matrix.Rotation(radians(180), 4, "Y") @ instance.matrix_world

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
        # TODO: here we could calculate the volume based on shape like we do on ybnexport for more accurate results
        volume = get_mass_properties_of_box(bbmin, bbmax).volume
        density = collisionmats[mat.collision_properties.collision_index].density

        return volume * density

    def get_collision_mat(self, obj: bpy.types.Object):
        for mat in obj.data.materials:
            if mat.sollum_type == MaterialType.COLLISION:
                return mat


class SOLLUMZ_OT_vehicle_preview_generated_windows(bpy.types.Operator):
    bl_idname = "sollumz.vehicle_preview_generated_windows"
    bl_label = "Preview Vehicle Windows"
    bl_action = "Preview Vehicle Windows"
    bl_description = "Preview the automatically generated window shattermaps for this vehicle"

    @classmethod
    def poll(cls, context):
        if not IS_SZIO_NATIVE_AVAILABLE:
            cls.poll_message_set(
                "PyMateria is not available. Cannot automatically generate vehicle window shattermaps."
            )
            return False

        obj = context.active_object
        return obj is not None and find_sollumz_parent(obj, SollumType.FRAGMENT) is not None

    def modal(self, context, event):
        context.area.tag_redraw()

        if event.type == "ESC":
            bpy.types.SpaceView3D.draw_handler_remove(self._handle_px, "WINDOW")
            bpy.types.SpaceView3D.draw_handler_remove(self._handle_view, "WINDOW")
            return {"FINISHED"}

        return {"PASS_THROUGH"}

    def invoke(self, context, event):
        if context.area.type == "VIEW_3D":
            self._windows = self._generate_vehicle_windows(context)
            self._aobj = find_sollumz_parent(context.active_object, SollumType.FRAGMENT)
            self._handle_px = bpy.types.SpaceView3D.draw_handler_add(
                self._draw_px, (context,), "WINDOW", "POST_PIXEL"
            )
            self._handle_view = bpy.types.SpaceView3D.draw_handler_add(
                self._draw_view, (context,), "WINDOW", "POST_VIEW"
            )

            context.window_manager.modal_handler_add(self)
            return {"RUNNING_MODAL"}
        else:
            self.report({"WARNING"}, "View3D not found, cannot run operator")
            return {"CANCELLED"}

    def _generate_vehicle_windows(
        self, context
    ) -> tuple[list[FragVehicleWindow], list[str], list[gpu.types.GPUTexture | None], list[gpu.types.GPUBatch | None]]:
        obj = context.active_object
        frag_obj = find_sollumz_parent(obj, SollumType.FRAGMENT)

        from gpu_extras.batch import batch_for_shader
        from ..tools.utils import multiply_homogeneous
        from ..iecontext import export_context_scope, ExportContext, ExportSettings
        from .yftexport_io import export_yft
        with export_context_scope(ExportContext(frag_obj.name, ExportSettings((AssetTarget(AssetFormat.NATIVE, AssetVersion.GEN8),)))):
            frag_bundle = export_yft(frag_obj)

        if not frag_bundle:
            self.report({"WARNING"}, "Found errors on fragment. Check Info Log for details.")
            return {"CANCELLED"}

        frag = frag_bundle.main_asset
        vw: list[FragVehicleWindow] = frag.vehicle_windows
        self.report({"INFO"}, f"Generated {len(vw)} windows!")

        vw_bone_names = []
        vw_textures = []
        vw_batches = []
        children = frag.physics.lod1.children
        for w in vw:
            child = children[w.component_id]
            window_bone = None
            for bone in frag_obj.data.bones:
                if bone.bone_properties.tag != child.bone_tag:
                    continue

                window_bone = bone
                break

            vw_bone_names.append(window_bone.name)

            shattermap = w.shattermap
            height, width = shattermap.shape
            if height != 0 and width != 0:
                pixels = np.empty((height, width, 4), dtype=np.float32)
                pixels[:, :, 0] = shattermap
                pixels[:, :, 1] = shattermap
                pixels[:, :, 2] = shattermap
                pixels[:, :, 3] = 1.0  # shattermap != 0
                pixels = gpu.types.Buffer("FLOAT", width * height * 4, pixels)

                shattermap_tex = gpu.types.GPUTexture((width, height), format="RGBA32F", data=pixels)
                vw_textures.append(shattermap_tex)

                proj_mat = Matrix(w.basis)
                proj_mat[3][3] = 1
                proj_mat.transpose()
                proj_mat.invert_safe()

                vw_min = Vector((0, 0, 0))
                vw_max = Vector((w.width, w.height, 1))

                v0 = multiply_homogeneous(proj_mat, Vector((vw_min.x, vw_min.y, 0)))
                v1 = multiply_homogeneous(proj_mat, Vector((vw_min.x, vw_max.y, 0)))
                v2 = multiply_homogeneous(proj_mat, Vector((vw_max.x, vw_max.y, 0)))
                v3 = multiply_homogeneous(proj_mat, Vector((vw_max.x, vw_min.y, 0)))

                shader = gpu.shader.from_builtin("IMAGE")
                batch = batch_for_shader(
                    shader, "TRI_FAN",
                    {
                        "pos": (v0, v1, v2, v3),
                        "texCoord": ((0, 1), (0, 0), (1, 0), (1, 1)),
                    },
                )
                vw_batches.append(batch)
            else:
                vw_textures.append(None)
                vw_batches.append(None)

        # Sort by bone names
        merge = list(zip(vw, vw_bone_names, vw_textures, vw_batches))
        merge.sort(key=lambda x: x[1])
        vw, vw_bone_names, vw_textures, vw_batches = map(list, zip(*merge))

        return vw, vw_bone_names, vw_textures, vw_batches

    def _draw_px(self, context):
        import blf
        from gpu_extras.presets import draw_texture_2d

        vw, vw_bone_names, vw_textures, _ = self._windows

        font_id = 0
        font_size = 18.0

        x = 25
        xstart = x
        blf.position(font_id, x, 15, 0)
        blf.size(font_id, font_size)
        blf.color(font_id, 1.0, 1.0, 1.0, 1.0)
        blf.draw(font_id, "Press Esc to stop preview.")

        y = 40
        ystart = y
        ymax = y
        xindent = 20
        tex_scale = 1.5
        for i, (name, tex) in enumerate(zip(vw_bone_names, vw_textures)):
            blf.size(font_id, font_size)
            _, h = blf.dimensions(font_id, name)
            tex_height = tex.height if tex else 8
            text_x = x + xindent
            text_y = y + tex_height * tex_scale * 0.5 - h * 0.25
            blf.position(font_id, text_x, text_y, 0)
            blf.color(font_id, 1.0, 1.0, 1.0, 1.0)
            blf.draw(font_id, name)

            if tex is not None:
                draw_texture_2d(tex, (text_x + 125, y), tex.width * tex_scale, tex.height * tex_scale)
            else:
                # generated an empty shattermap which means it used the CAR_GLASS_BULLETPROOF collision material
                blf.size(font_id, font_size - 4.0)
                blf.position(font_id, text_x + 125, text_y, 0)
                blf.color(font_id, 0.75, 0.75, 0.75, 1.0)
                blf.draw(font_id, "BULLETPROOF")

            y += tex_height * 1.5 + 10
            ymax = max(ymax, y)
            if ((i + 1) % 4) == 0:
                y = ystart
                x += 250

        blf.position(font_id, xstart, ymax, 0)
        blf.size(font_id, font_size)
        blf.color(font_id, 1.0, 1.0, 1.0, 1.0)
        blf.draw(font_id, f"Generated {len(vw)} window(s):")

    def _draw_view(self, context):

        vw, _, vw_textures, vw_batches = self._windows

        shader = gpu.shader.from_builtin("IMAGE")

        old_depth_test, old_depth_mask = gpu.state.depth_test_get(), gpu.state.depth_mask_get()
        gpu.state.depth_test_set("LESS_EQUAL")
        gpu.state.depth_mask_set(True)

        transform = self._aobj.matrix_world
        with gpu.matrix.push_pop():
            gpu.matrix.multiply_matrix(transform)
            for w, tex, batch in zip(vw, vw_textures, vw_batches):
                if tex is None or batch is None:
                    continue

                shader.bind()
                shader.uniform_sampler("image", tex)
                batch.draw(shader)

        gpu.state.depth_test_set(old_depth_test)
        gpu.state.depth_mask_set(old_depth_mask)
