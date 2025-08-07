import bpy
from bpy.types import Context
from ...lods import LODLevels
from ...sollumz_helper import SOLLUMZ_OT_base, find_sollumz_parent
from ...sollumz_properties import SOLLUMZ_UI_NAMES, LODLevel, SollumType
from ...tools.drawablehelper import set_recommended_bone_properties, convert_obj_to_drawable, convert_obj_to_model, convert_objs_to_single_drawable, center_drawable_to_models
from ...tools.boundhelper import convert_obj_to_composite, convert_objs_to_single_composite
from ...tools.blenderhelper import add_armature_modifier, add_child_of_bone_constraint, create_blender_object, create_empty_object, duplicate_object, get_child_of_constraint, set_child_of_constraint_space, tag_redraw
from ...sollumz_helper import get_sollumz_materials
from ..properties import DrawableShaderOrder
from ...tools.meshhelper import (
    mesh_add_missing_uv_maps,
    mesh_add_missing_color_attrs,
    mesh_rename_uv_maps_by_order,
    mesh_rename_color_attrs_by_order,
)

class SOLLUMZ_OT_create_drawable(bpy.types.Operator):
    """Create a Drawable empty"""
    bl_idname = "sollumz.createdrawable"
    bl_label = "Create Drawable"

    def execute(self, context):
        selected = context.selected_objects

        if selected:
            parent = selected[0]
        else:
            parent = None

        drawable_obj = create_empty_object(SollumType.DRAWABLE)
        drawable_obj.parent = parent

        return {"FINISHED"}


class SOLLUMZ_OT_create_drawable_dict(bpy.types.Operator):
    """Create a Drawable Dictionary empty"""
    bl_idname = "sollumz.createdrawabledict"
    bl_label = "Create Drawable Dictionary"

    def execute(self, context):
        selected = context.selected_objects

        if selected:
            parent = selected[0]
        else:
            parent = None

        ydd_obj = create_empty_object(SollumType.DRAWABLE_DICTIONARY)
        ydd_obj.parent = parent

        return {"FINISHED"}


class SOLLUMZ_OT_convert_to_drawable(bpy.types.Operator):
    """Convert the selected object to a Drawable"""
    bl_idname = "sollumz.converttodrawable"
    bl_label = "Convert to Drawable"
    bl_options = {"UNDO"}

    def execute(self, context: bpy.types.Context):
        selected_meshes = [obj for obj in context.selected_objects if obj.type == "MESH"]

        if not selected_meshes:
            self.report({"INFO"}, "No mesh objects selected!")
            return {"CANCELLED"}

        auto_embed_col = context.scene.auto_create_embedded_col
        do_center = context.scene.center_drawable_to_selection

        if context.scene.create_seperate_drawables or len(selected_meshes) == 1:
            self.convert_separate_drawables(context, selected_meshes, auto_embed_col)
        else:
            self.convert_to_single_drawable(context, selected_meshes, auto_embed_col, do_center)

        self.report({"INFO"}, "Succesfully converted all selected objects to a Drawable.")

        return {"FINISHED"}

    def convert_separate_drawables(
        self,
        context: bpy.types.Context,
        selected_meshes: list[bpy.types.Object],
        auto_embed_col: bool = False
    ):
        for obj in selected_meshes:
            # override selected collection to create the drawable object in the same collection as the mesh
            with context.temp_override(collection=obj.users_collection[0]):
                drawable_obj = convert_obj_to_drawable(obj)

                if auto_embed_col:
                    composite_obj = convert_obj_to_composite(
                        duplicate_object(obj),
                        SollumType.BOUND_GEOMETRYBVH,
                        context.window_manager.sz_flag_preset_index
                    )
                    composite_obj.parent = drawable_obj
                    composite_obj.name = f"{drawable_obj.name}.col"

    def convert_to_single_drawable(
        self,
        context: bpy.types.Context,
        selected_meshes: list[bpy.types.Object],
        auto_embed_col: bool = False,
        do_center: bool = False
    ):
        # override selected collection to create the drawable object in the same collection as the selected meshes
        # the active mesh collection has preference in case the selected meshes are in different collections
        target_coll_obj = context.active_object if context.active_object in selected_meshes else selected_meshes[0]
        target_coll = target_coll_obj.users_collection[0]
        with context.temp_override(collection=target_coll):
            drawable_obj = convert_objs_to_single_drawable(selected_meshes)

            if do_center:
                center_drawable_to_models(drawable_obj)

            if auto_embed_col:
                col_objs = [duplicate_object(o) for o in selected_meshes]
                composite_obj = convert_objs_to_single_composite(
                    col_objs,
                    SollumType.BOUND_GEOMETRYBVH,
                    context.window_manager.sz_flag_preset_index
                )
                composite_obj.parent = drawable_obj


class SOLLUMZ_OT_convert_to_drawable_model(bpy.types.Operator):
    """Convert the selected object to a Drawable Model"""
    bl_idname = "sollumz.converttodrawablemodel"
    bl_label = "Convert to Drawable Model"
    bl_options = {"UNDO"}

    def execute(self, context):
        selected_meshes = [
            obj for obj in context.selected_objects if obj.type == "MESH"]

        if not selected_meshes:
            self.report({"INFO"}, f"No mesh objects selected!")
            return {"CANCELLED"}

        for obj in selected_meshes:
            convert_obj_to_model(obj)
            self.report(
                {"INFO"}, f"Converted {obj.name} to a {SOLLUMZ_UI_NAMES[SollumType.DRAWABLE_MODEL]}.")

        return {"FINISHED"}


class SOLLUMZ_OT_BONE_FLAGS_NewItem(SOLLUMZ_OT_base, bpy.types.Operator):
    bl_idname = "sollumz.bone_flags_new_item"
    bl_label = "Add a new item"
    bl_action = "Add a Bone Flag"

    def run(self, context):
        bone = context.active_bone
        bone.bone_properties.flags.add()
        self.message(f"Added bone flag to bone: {bone.name}")
        return True


class SOLLUMZ_OT_BONE_FLAGS_DeleteItem(SOLLUMZ_OT_base, bpy.types.Operator):
    bl_idname = "sollumz.bone_flags_delete_item"
    bl_label = "Deletes an item"
    bl_action = "Delete a Bone Flag"

    @classmethod
    def poll(cls, context):
        return context.active_bone is not None and context.active_bone.bone_properties.flags

    def run(self, context):
        bone = context.active_bone
        list = bone.bone_properties.flags
        index = bone.bone_properties.ul_index
        list.remove(index)
        bone.bone_properties.ul_index = min(
            max(0, index - 1), len(list) - 1)
        self.message(f"Deleted bone flag from: {bone.name}")
        return True


class SOLLUMZ_OT_apply_bone_properties_to_armature(SOLLUMZ_OT_base, bpy.types.Operator):
    bl_idname = "sollumz.apply_bone_properties_to_armature"
    bl_label = "To Armature"
    bl_action = bl_label

    def run(self, context):
        armature = context.active_object
        if armature is None or armature.type != "ARMATURE":
            return

        if armature.pose is None:
            return

        for pbone in armature.pose.bones:
            bone = pbone.bone
            set_recommended_bone_properties(bone)

        self.message(f"Apply bone properties to armature: {armature.name}")
        return True


class SOLLUMZ_OT_apply_bone_properties_to_selected_bones(SOLLUMZ_OT_base, bpy.types.Operator):
    bl_idname = "sollumz.apply_bone_properties_to_selected_bones"
    bl_label = "To Selected Bones"
    bl_action = bl_label

    def run(self, context):
        pbones = context.selected_pose_bones
        if pbones is None:
            return

        count = 0
        for pbone in pbones:
            bone = pbone.bone
            set_recommended_bone_properties(bone)
            count += 1

        self.message(f"Apply bone properties to {count} bone(s)")
        return True


class BonePoseModeRestrictedHelper:
    @classmethod
    def poll(cls, context: Context):
        cls.poll_message_set("Must be in object mode or pose mode.")
        return context.mode == "POSE" and len(context.selected_pose_bones) > 0


class SOLLUMZ_OT_clear_bone_flags(bpy.types.Operator, BonePoseModeRestrictedHelper):
    bl_idname = "sollumz.removeboneflags"
    bl_label = "Remove Bone Flags"
    bl_description = "Remove all bone flags for selected bones"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        selected_bones = context.selected_pose_bones
        for pBone in selected_bones:
            pBone.bone.bone_properties.flags.clear()
        tag_redraw(context)
        self.report({'INFO'}, "Flags Removed")
        return {'FINISHED'}


class SOLLUMZ_OT_rotation_bone_flags(bpy.types.Operator, BonePoseModeRestrictedHelper):
    bl_idname = "sollumz.rotationboneflags"
    bl_label = "Add Rotation Flags"
    bl_description = "Add rotation flags for selected bones"

    def execute(self, context):
        selected_bones = context.selected_pose_bones
        for pBone in selected_bones:
            new_flag = pBone.bone.bone_properties.flags.add()
            new_flag.name = "RotX"
            new_flag = pBone.bone.bone_properties.flags.add()
            new_flag.name = "RotY"
            new_flag = pBone.bone.bone_properties.flags.add()
            new_flag.name = "RotZ"
        tag_redraw(context)
        self.report({'INFO'}, f'Rotation Flags Added for {len(selected_bones)} bone(s)')
        return {'FINISHED'}


class SOLLUMZ_OT_translation_bone_flags(bpy.types.Operator, BonePoseModeRestrictedHelper):
    bl_idname = "sollumz.transformboneflags"
    bl_label = "Add Translation Flags"
    bl_description = "Add translation flags for selected bones"

    def execute(self, context):
        selected_bones = context.selected_pose_bones
        for pBone in selected_bones:
            new_flag = pBone.bone.bone_properties.flags.add()
            new_flag.name = "TransX"
            new_flag = pBone.bone.bone_properties.flags.add()
            new_flag.name = "TransY"
            new_flag = pBone.bone.bone_properties.flags.add()
            new_flag.name = "TransZ"
        tag_redraw(context)
        self.report({'INFO'}, f'Translation Flags Added for {len(selected_bones)} bone(s)')
        return {'FINISHED'}


class SOLLUMZ_OT_scale_bone_flags(bpy.types.Operator, BonePoseModeRestrictedHelper):
    bl_idname = "sollumz.scaleboneflags"
    bl_label = "Add Scale Flags"
    bl_description = "Add scale flags for selected bones"

    def execute(self, context):
        selected_bones = context.selected_pose_bones
        for pBone in selected_bones:
            new_flag = pBone.bone.bone_properties.flags.add()
            new_flag.name = "ScaleX"
            new_flag = pBone.bone.bone_properties.flags.add()
            new_flag.name = "ScaleY"
            new_flag = pBone.bone.bone_properties.flags.add()
            new_flag.name = "ScaleZ"
        tag_redraw(context)
        self.report({'INFO'}, f'Scale Flags Added for {len(selected_bones)} bone(s)')
        return {'FINISHED'}


class SOLLUMZ_OT_limit_bone_flags(bpy.types.Operator, BonePoseModeRestrictedHelper):
    bl_idname = "sollumz.limitboneflags"
    bl_label = "Add Limit Flags"
    bl_description = "Removes selected bone flags and adds the proper limit flags for custom bone locations"

    def execute(self, context):
        selected_bones = context.selected_pose_bones
        for pBone in selected_bones:
            new_flag = pBone.bone.bone_properties.flags.add()
            new_flag.name = "LimitRotation"
            new_flag = pBone.bone.bone_properties.flags.add()
            new_flag.name = "LimitTranslation"
        tag_redraw(context)
        self.report({'INFO'}, f'Limit Flags Added for {len(selected_bones)} bone(s)')
        return {'FINISHED'}


class OperatorMoveShaderUpBase:
    move_to_top = False

    @classmethod
    def poll(self, context):
        aobj = context.active_object

        if aobj is None or aobj.sollum_type != SollumType.DRAWABLE:
            return False

        drawable_props = aobj.drawable_properties
        num_shaders = len(drawable_props.shader_order.order_items)
        shader_ind = drawable_props.shader_order.get_active_shader_item_index()

        return shader_ind < num_shaders and shader_ind != 0

    def execute(self, context):
        aobj = context.active_object
        drawable_props = aobj.drawable_properties
        shader_ind = drawable_props.shader_order.get_active_shader_item_index()

        if self.move_to_top:
            drawable_props.shader_order.move_shader_to_top(shader_ind)
        else:
            drawable_props.shader_order.move_shader_up(shader_ind)

        return {"FINISHED"}


class OperatorMoveShaderDownBase:
    move_to_bottom = False

    @classmethod
    def poll(self, context):
        aobj = context.active_object

        if aobj is None or aobj.sollum_type != SollumType.DRAWABLE:
            return False

        drawable_props = aobj.drawable_properties
        num_shaders = len(drawable_props.shader_order.order_items)
        shader_ind = drawable_props.shader_order.get_active_shader_item_index()

        return shader_ind < num_shaders - 1 and num_shaders > 1

    def execute(self, context):
        aobj = context.active_object
        drawable_props = aobj.drawable_properties
        shader_ind = drawable_props.shader_order.get_active_shader_item_index()

        if self.move_to_bottom:
            drawable_props.shader_order.move_shader_to_bottom(shader_ind)
        else:
            drawable_props.shader_order.move_shader_down(shader_ind)

        return {"FINISHED"}


class SOLLUMZ_OT_move_shader_up(OperatorMoveShaderUpBase, bpy.types.Operator):
    bl_idname = "sollumz.move_shader_up"
    bl_label = "Up"
    bl_description = "Move shader up in the rendering order"


class SOLLUMZ_OT_move_shader_to_top(OperatorMoveShaderUpBase, bpy.types.Operator):
    bl_idname = "sollumz.move_shader_to_top"
    bl_label = "Move To Top"
    bl_description = "Move shader to the top in the rendering order"

    move_to_top = True


class SOLLUMZ_OT_move_shader_down(OperatorMoveShaderDownBase, bpy.types.Operator):
    bl_idname = "sollumz.move_shader_down"
    bl_label = "Down"
    bl_description = "Move shader down in the rendering order"


class SOLLUMZ_OT_move_shader_to_bottom(OperatorMoveShaderDownBase, bpy.types.Operator):
    bl_idname = "sollumz.move_shader_to_bottom"
    bl_label = "Move To Bottom"
    bl_description = "Move shader to the bottom in the rendering order"

    move_to_bottom = True


class SOLLUMZ_OT_order_shaders(bpy.types.Operator):
    bl_idname = "sollumz.order_shaders"
    bl_label = "Order Shaders"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Determine shader rendering order"

    def draw(self, context):
        layout = self.layout
        shader_order = context.active_object.drawable_properties.shader_order

        row = layout.row()
        col = row.column()

        col.template_list("SOLLUMZ_UL_SHADER_ORDER_LIST", "", shader_order, "order_items",
                          shader_order, "active_index", maxrows=40)

        col = row.column()
        col.operator(SOLLUMZ_OT_move_shader_to_top.bl_idname, text="", icon="TRIA_UP")
        subcol = col.column(align=True)
        subcol.operator(SOLLUMZ_OT_move_shader_up.bl_idname, text="", icon="TRIA_UP")
        subcol.operator(SOLLUMZ_OT_move_shader_down.bl_idname, text="", icon="TRIA_DOWN")
        col.operator(SOLLUMZ_OT_move_shader_to_bottom.bl_idname, text="", icon="TRIA_DOWN")

    def execute(self, context):
        aobj = context.active_object
        self.apply_order(aobj)

        return {"FINISHED"}

    def invoke(self, context, event):
        wm = context.window_manager

        aobj = context.active_object
        self.add_initial_items(aobj)

        return wm.invoke_props_dialog(self, width=800)

    def add_initial_items(self, drawable_obj: bpy.types.Object):
        """Add initial shader sort items based on materials from drawable_obj"""
        shader_order: DrawableShaderOrder = drawable_obj.drawable_properties.shader_order
        mats = get_sollumz_materials(drawable_obj)
        self.validate_indices(mats)

        shader_order.order_items.clear()

        for mat in mats:
            item = shader_order.order_items.add()
            item.index = mat.shader_properties.index
            item.name = mat.name
            item.filename = mat.shader_properties.filename

    def validate_indices(self, mats: list[bpy.types.Material]):
        """Ensure valid and unique shader indices (in-case user changed them or blend file is from previous version)"""
        shader_inds = [mat.shader_properties.index for mat in mats]
        has_repeating_indices = any(
            shader_inds.count(i) > 1 for i in shader_inds)
        inds_out_of_range = any(i >= len(mats) for i in shader_inds)

        if not has_repeating_indices and not inds_out_of_range:
            return

        for i, mat in enumerate(mats):
            mat.shader_properties.index = i

    def apply_order(self, drawable_obj: bpy.types.Object):
        """Set material shader indices based on shader order"""
        shader_order: DrawableShaderOrder = drawable_obj.drawable_properties.shader_order
        mats = get_sollumz_materials(drawable_obj)

        if len(shader_order.order_items) != len(mats):
            self.report(
                {"ERROR"}, "Failed to apply order, shader collection size mismatch!")
            return {"CANCELLED"}

        for i, mat in enumerate(mats):
            mat.shader_properties.index = shader_order.order_items[i].index

        return {"FINISHED"}


class SOLLUMZ_OT_add_child_of_constraint(bpy.types.Operator):
    bl_idname = "sollumz.add_child_of_constraint"
    bl_label = "Add Bone Constraint"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Add Child Of constraint to the selected Drawable Model and set the proper constraint properties"

    @classmethod
    def poll(self, context):
        return len(context.selected_objects) > 0

    def execute(self, context):
        for obj in context.selected_objects:
            parent_obj = find_sollumz_parent(obj)

            if parent_obj is None or parent_obj.type != "ARMATURE":
                self.report(
                    {"INFO"}, f"{obj.name} must be parented to a Drawable armature, or Drawable that is parented to a Fragment!")
                return {"CANCELLED"}

            add_child_of_bone_constraint(obj, armature_obj=parent_obj)

        return {"FINISHED"}


class SOLLUMZ_OT_add_armature_modifier_constraint(bpy.types.Operator):
    bl_idname = "sollumz.add_armature_modifier"
    bl_label = "Add Armature Modifier"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Add armature modifier to object with first Sollumz parent as the modifier object"

    @classmethod
    def poll(self, context):
        return len(context.selected_objects) > 0

    def execute(self, context):
        for obj in context.selected_objects:
            parent_obj = find_sollumz_parent(obj)
            is_drawable_model = obj.sollum_type == SollumType.DRAWABLE_MODEL

            if parent_obj is None or not is_drawable_model:
                self.report(
                    {"INFO"}, f"{obj.name} must be a Drawable Model and parented to a Drawable!")
                return {"CANCELLED"}

            if parent_obj.type != "ARMATURE":
                self.report(
                    {"INFO"}, f"{obj.name} must be parented to a Drawable armature, or Drawable that is parented to a Fragment!")
                return {"CANCELLED"}

            add_armature_modifier(obj, parent_obj)

        return {"FINISHED"}


class SOLLUMZ_OT_set_correct_child_of_space(bpy.types.Operator):
    bl_idname = "sollumz.set_correct_child_of_space"
    bl_label = "Set correct space for bone parenting"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Sets the owner space and target space such that it behaves the same way as bone parenting"

    @classmethod
    def poll(self, context):
        return context.active_object is not None and get_child_of_constraint(context.active_object) is not None

    def execute(self, context):
        constraint = get_child_of_constraint(context.active_object)
        set_child_of_constraint_space(constraint)

        return {"FINISHED"}


class SOLLUMZ_OT_auto_lod(bpy.types.Operator):
    bl_idname = "sollumz.auto_lod"
    bl_label = "Generate LODs"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = (
        "Generate drawable model LODs via decimate modifier. Starts from the selected reference mesh, generating a "
        "new decimated mesh for each selected LOD level"
    )

    @classmethod
    def poll(self, context):
        return context.active_object is not None and context.active_object.sollum_type == SollumType.DRAWABLE_MODEL

    def execute(self, context: Context):
        aobj = context.active_object
        ref_mesh = context.scene.sollumz_auto_lod_ref_mesh

        if ref_mesh is None:
            self.report(
                {"INFO"}, "No reference mesh specified! You must specify a mesh to use as the highest LOD level!")
            return {"CANCELLED"}

        lods = self.get_selected_lods_sorted(context)

        if not lods:
            return {"CANCELLED"}

        obj_lods: LODLevels = aobj.sz_lods

        decimate_step = context.scene.sollumz_auto_lod_decimate_step
        last_mesh = ref_mesh

        previous_mode = aobj.mode
        previous_lod_level = obj_lods.active_lod_level

        for lod_level in lods:
            bpy.ops.object.mode_set(mode="OBJECT")  # make sure we are in object mode before switching LODs
            mesh = last_mesh.copy()
            mesh.name = self.get_lod_mesh_name(aobj.name, lod_level)

            obj_lods.get_lod(lod_level).mesh = mesh
            obj_lods.active_lod_level = lod_level

            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.decimate(ratio=1.0 - decimate_step)

            last_mesh = mesh

        bpy.ops.object.mode_set(mode="OBJECT")
        obj_lods.active_lod_level = previous_lod_level

        bpy.ops.object.mode_set(mode=previous_mode)

        return {"FINISHED"}

    def get_lod_mesh_name(self, obj_name: str, lod_level: LODLevel):
        return f"{obj_name}.{SOLLUMZ_UI_NAMES[lod_level].lower()}"

    def get_selected_lods_sorted(self, context: Context) -> tuple[LODLevel]:
        return tuple(lod for lod in LODLevel if lod in context.scene.sollumz_auto_lod_levels)


class SOLLUMZ_OT_extract_lods(bpy.types.Operator):
    bl_idname = "sollumz.extract_lods"
    bl_label = "Extract LODs"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Extract all meshes of the selected Drawable Model into separate objects"

    @classmethod
    def poll(self, context):
        return context.active_object is not None and context.active_object.sollum_type == SollumType.DRAWABLE_MODEL

    def execute(self, context: Context):
        aobj = context.active_object
        parent = self.create_parent(context, f"{aobj.name}.LODs")
        lod_levels = context.scene.sollumz_extract_lods_levels

        lods = aobj.sz_lods
        for lod_level in lod_levels:
            lod = lods.get_lod(lod_level)
            lod_mesh = lod.mesh
            if lod_mesh is None:
                continue

            lod_obj = create_blender_object(SollumType.NONE, lod_mesh.name, lod_mesh)
            self.parent_object(lod_obj, parent)

        return {"FINISHED"}

    def create_parent(self, context: Context, name: str) -> bpy.types.Object | bpy.types.Collection:
        parent_type = context.scene.sollumz_extract_lods_parent_type

        if parent_type == "sollumz_extract_lods_parent_type_collection":
            parent = bpy.data.collections.new(name)
            context.collection.children.link(parent)
        else:
            parent = create_empty_object(SollumType.NONE, name)

        return parent

    def parent_object(self, obj: bpy.types.Object, parent: bpy.types.Object | bpy.types.Collection):
        if isinstance(parent, bpy.types.Object):
            obj.parent = parent
        elif isinstance(parent, bpy.types.Collection):
            if obj.users_collection:
                obj.users_collection[0].objects.unlink(obj)

            parent.objects.link(obj)


class SOLLUMZ_OT_uv_maps_rename_by_order(bpy.types.Operator):
    """Rename UV maps based on their order in the list. Does not affect UV maps already in use"""
    bl_idname = "sollumz.uv_maps_rename_by_order"
    bl_label = "Rename UV Maps by Order"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(self, context):
        return context.active_object is not None and context.active_object.sollum_type == SollumType.DRAWABLE_MODEL

    def execute(self, context: bpy.types.Context):
        selected_meshes = [obj for obj in context.selected_objects if obj.type == "MESH"]
        if context.active_object.type == "MESH":
            selected_meshes.append(context.active_object)

        if not selected_meshes:
            self.report({"INFO"}, "No mesh objects selected!")
            return {"CANCELLED"}

        for mesh_obj in selected_meshes:
            mesh_rename_uv_maps_by_order(mesh_obj.data)

        return {"FINISHED"}


class SOLLUMZ_OT_uv_maps_add_missing(bpy.types.Operator):
    """Add the missing UV maps used by the Sollumz shaders of the mesh"""
    bl_idname = "sollumz.uv_maps_add_missing"
    bl_label = "Add Missing UV Maps"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(self, context):
        return context.active_object is not None and context.active_object.sollum_type == SollumType.DRAWABLE_MODEL

    def execute(self, context: bpy.types.Context):
        selected_meshes = [obj for obj in context.selected_objects if obj.type == "MESH"]
        if context.active_object.type == "MESH":
            selected_meshes.append(context.active_object)

        if not selected_meshes:
            self.report({"INFO"}, "No mesh objects selected!")
            return {"CANCELLED"}

        for mesh_obj in selected_meshes:
            mesh_add_missing_uv_maps(mesh_obj.data)

        return {"FINISHED"}


class SOLLUMZ_OT_color_attrs_rename_by_order(bpy.types.Operator):
    """Rename colors attributes based on their order in the list. Does not affect color attributes already in use"""
    bl_idname = "sollumz.color_attrs_rename_by_order"
    bl_label = "Rename Color Attributes by Order"
    bl_options = {"UNDO"}

    @classmethod
    def poll(self, context):
        return context.active_object is not None and context.active_object.sollum_type == SollumType.DRAWABLE_MODEL

    def execute(self, context: bpy.types.Context):
        selected_meshes = [obj for obj in context.selected_objects if obj.type == "MESH"]
        if context.active_object.type == "MESH":
            selected_meshes.append(context.active_object)

        if not selected_meshes:
            self.report({"INFO"}, "No mesh objects selected!")
            return {"CANCELLED"}

        for mesh_obj in selected_meshes:
            mesh_rename_color_attrs_by_order(mesh_obj.data)

        return {"FINISHED"}


class SOLLUMZ_OT_color_attrs_add_missing(bpy.types.Operator):
    """Add the missing color attributes used by the Sollumz shaders of the mesh"""
    bl_idname = "sollumz.color_attrs_add_missing"
    bl_label = "Add Missing Color Attributes"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(self, context):
        return context.active_object is not None and context.active_object.sollum_type == SollumType.DRAWABLE_MODEL

    def execute(self, context: bpy.types.Context):
        selected_meshes = [obj for obj in context.selected_objects if obj.type == "MESH"]
        if context.active_object.type == "MESH":
            selected_meshes.append(context.active_object)

        if not selected_meshes:
            self.report({"INFO"}, "No mesh objects selected!")
            return {"CANCELLED"}

        for mesh_obj in selected_meshes:
            mesh_add_missing_color_attrs(mesh_obj.data)

        return {"FINISHED"}
