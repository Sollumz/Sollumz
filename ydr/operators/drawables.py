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
from ..shader_materials import shadermats_by_filename


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
    bl_options = {"UNDO"}
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

        shader_order = aobj.drawable_properties.shader_order
        shader_order.order_items.clear()
        return {"FINISHED"}

    def invoke(self, context, event):
        wm = context.window_manager

        aobj = context.active_object
        self.add_initial_items(aobj)

        return wm.invoke_props_dialog(self, width=1000)

    def add_initial_items(self, drawable_obj: bpy.types.Object):
        """Add initial shader sort items based on materials from drawable_obj"""
        shader_order: DrawableShaderOrder = drawable_obj.drawable_properties.shader_order
        mat_to_model = {}
        mats = get_sollumz_materials(drawable_obj, out_material_to_models=mat_to_model)
        self.validate_indices(mats)

        shader_order.order_items.clear()

        for mat in mats:
            s = shadermats_by_filename.get(mat.shader_properties.filename, None)
            item = shader_order.order_items.add()
            item.index = mat.shader_properties.index
            item.material = mat
            item.name = mat.name
            item.shader = (s and s.ui_name) or mat.shader_properties.filename
            item.user_models = ", ".join(o.name for o in mat_to_model[mat])

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
        for order_item in shader_order.order_items:
            order_item.material.shader_properties.index = order_item.index

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
        "Generate drawable model LODs via decimation. Supports multiple methods, per-LOD ratios, "
        "preserve options, and automatic LOD distance calculation"
    )

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.sollum_type == SollumType.DRAWABLE_MODEL

    def execute(self, context: Context):
        aobj = context.active_object
        settings = context.scene.sollumz_auto_lod_settings
        ref_mesh = settings.ref_mesh

        if ref_mesh is None:
            self.report({"INFO"}, "No reference mesh specified! You must specify a mesh to use as the highest LOD level!")
            return {"CANCELLED"}

        lods = self._get_selected_lods_sorted(settings)

        if not lods:
            self.report({"INFO"}, "No LOD levels selected!")
            return {"CANCELLED"}

        obj_lods: LODLevels = aobj.sz_lods

        previous_mode = aobj.mode
        previous_lod_level = obj_lods.active_lod_level
        last_mesh = ref_mesh

        for i, lod_level in enumerate(lods):
            bpy.ops.object.mode_set(mode="OBJECT")

            source_mesh = ref_mesh if settings.decimate_from_original else last_mesh
            mesh = source_mesh.copy()
            mesh.name = self._get_lod_mesh_name(aobj.name, lod_level)

            obj_lods.get_lod(lod_level).mesh = mesh
            obj_lods.active_lod_level = lod_level

            self._apply_decimation(context, aobj, settings, lod_level, i, source_mesh)

            last_mesh = mesh

        bpy.ops.object.mode_set(mode="OBJECT")

        if settings.auto_merge_materials:
            for lod_level in lods:
                obj_lods.active_lod_level = lod_level
                self._merge_materials(context, aobj, lod_level)

        obj_lods.active_lod_level = previous_lod_level
        bpy.ops.object.mode_set(mode=previous_mode)

        if settings.auto_set_distances:
            self._set_auto_distances(aobj, ref_mesh, lods)

        self._report_stats(aobj, lods, obj_lods)

        return {"FINISHED"}

    def _merge_materials(self, context: Context, obj, lod_level: LODLevel):
        """Run material merge bake on the current LOD mesh."""
        if obj.data is None or len(obj.data.materials) <= 1:
            return

        result = bpy.ops.sollumz.material_merge_bake()
        if result == {"CANCELLED"}:
            self.report({"WARNING"}, f"Material merge failed for {SOLLUMZ_UI_NAMES[lod_level]}")
            return

        # Rename the baked image and material to be unique per LOD level,
        # otherwise the next LOD's bake will delete them (same name).
        lod_suffix = SOLLUMZ_UI_NAMES[lod_level].lower().replace(" ", "_")

        old_image_name = f"{obj.name}_BakedMaterial"
        if old_image_name in bpy.data.images:
            bpy.data.images[old_image_name].name = f"{obj.name}_{lod_suffix}_BakedMaterial"

        old_mat_name = f"{obj.name}_MergedMaterial"
        if old_mat_name in bpy.data.materials:
            bpy.data.materials[old_mat_name].name = f"{obj.name}_{lod_suffix}_MergedMaterial"

    def _apply_decimation(self, context: Context, obj, settings, lod_level: LODLevel, index: int, source_mesh):
        """Apply decimation to the active LOD mesh using the modifier API."""
        method = settings.decimate_method

        mod = obj.modifiers.new(name="AutoLOD_Decimate", type="DECIMATE")

        if method == "COLLAPSE":
            ratio = self._get_effective_ratio(settings, lod_level, index, source_mesh)
            mod.decimate_type = "COLLAPSE"
            mod.ratio = ratio
            mod.use_collapse_triangulate = True

            delimit = set()
            if settings.preserve_uvs:
                delimit.add("UV")
            if settings.preserve_sharp:
                delimit.add("SHARP")
            if settings.preserve_materials:
                delimit.add("MATERIAL")
            if delimit:
                mod.delimit = delimit

            if settings.preserve_vertex_groups and hasattr(mod, "use_symmetry"):
                # Vertex group preservation is handled by the delimit options
                # and by Blender's internal weighting in collapse mode
                pass

        elif method == "UNSUBDIV":
            mod.decimate_type = "UNSUBDIV"
            mod.iterations = settings.unsubdiv_iterations

        elif method == "DISSOLVE":
            mod.decimate_type = "DISSOLVE"
            mod.angle_limit = settings.planar_angle_limit
            if settings.preserve_materials:
                mod.delimit = {"MATERIAL"}

        try:
            bpy.ops.object.modifier_apply(modifier=mod.name)
        except RuntimeError as e:
            self.report({"WARNING"}, f"Modifier apply failed for {SOLLUMZ_UI_NAMES[lod_level]}: {e}")
            if mod.name in obj.modifiers:
                obj.modifiers.remove(mod)

    def _get_effective_ratio(self, settings, lod_level: LODLevel, index: int, source_mesh) -> float:
        """Calculate the decimation ratio for a given LOD level."""
        if settings.use_per_lod_ratios:
            lod_settings = settings.get_lod_settings(lod_level)
            if lod_settings.use_target_tri_count:
                source_tri_count = len(source_mesh.polygons)
                if source_tri_count > 0:
                    return max(0.01, min(1.0, lod_settings.target_tri_count / source_tri_count))
                return 1.0
            else:
                return lod_settings.ratio
        else:
            step = settings.decimate_step
            if settings.decimate_from_original:
                return max(0.01, 1.0 - step * (index + 1))
            else:
                return 1.0 - step

    def _set_auto_distances(self, obj, ref_mesh, lods: tuple[LODLevel]):
        """Calculate and set LOD distances on the parent Drawable."""
        drawable = find_sollumz_parent(obj, SollumType.DRAWABLE)
        if drawable is None:
            return

        verts = ref_mesh.vertices
        if len(verts) == 0:
            return

        import mathutils
        center = mathutils.Vector((0, 0, 0))
        for v in verts:
            center += v.co
        center /= len(verts)

        radius = max((v.co - center).length for v in verts)
        if radius < 0.01:
            radius = 1.0

        props = drawable.drawable_properties
        dist_map = {
            LODLevel.HIGH: min(9998, round(radius * 10)),
            LODLevel.MEDIUM: min(9998, round(radius * 25)),
            LODLevel.LOW: min(9998, round(radius * 50)),
            LODLevel.VERYLOW: min(9998, round(radius * 100)),
        }

        attr_map = {
            LODLevel.HIGH: "lod_dist_high",
            LODLevel.MEDIUM: "lod_dist_med",
            LODLevel.LOW: "lod_dist_low",
            LODLevel.VERYLOW: "lod_dist_vlow",
        }

        for lod_level in lods:
            attr = attr_map.get(lod_level)
            if attr:
                setattr(props, attr, float(dist_map[lod_level]))

    def _report_stats(self, obj, lods: tuple[LODLevel], obj_lods: LODLevels):
        """Report triangle/vertex counts for each generated LOD."""
        stats = []
        for lod_level in lods:
            mesh = obj_lods.get_lod(lod_level).mesh
            if mesh is not None:
                tri_count = sum(max(1, len(p.vertices) - 2) for p in mesh.polygons)
                stats.append(f"{SOLLUMZ_UI_NAMES[lod_level]}: {tri_count} tris, {len(mesh.vertices)} verts")

        if stats:
            self.report({"INFO"}, "LODs generated - " + " | ".join(stats))

    def _get_lod_mesh_name(self, obj_name: str, lod_level: LODLevel):
        return f"{obj_name}.{SOLLUMZ_UI_NAMES[lod_level].lower()}"

    def _get_selected_lods_sorted(self, settings) -> tuple[LODLevel]:
        return tuple(lod for lod in LODLevel if lod in settings.levels)


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
        return context.active_object is not None

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
        return context.active_object is not None

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
        return context.active_object is not None

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
        return context.active_object is not None

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
