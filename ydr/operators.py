import traceback
import bpy
from bpy.types import Context

from ..lods import LODLevels
from ..sollumz_helper import SOLLUMZ_OT_base, find_sollumz_parent
from ..sollumz_properties import SOLLUMZ_UI_NAMES, LODLevel, LightType, SollumType, MaterialType
from ..sollumz_operators import SelectTimeFlagsRange, ClearTimeFlags
from ..ydr.shader_materials import create_shader, create_tinted_shader_graph, is_tint_material, shadermats
from ..tools.drawablehelper import MaterialConverter, set_recommended_bone_properties, convert_obj_to_drawable, convert_obj_to_model, convert_objs_to_single_drawable, center_drawable_to_models
from ..tools.boundhelper import convert_obj_to_composite, convert_objs_to_single_composite
from ..tools.blenderhelper import add_armature_modifier, add_child_of_bone_constraint, create_blender_object, create_empty_object, duplicate_object, get_child_of_constraint, set_child_of_constraint_space, tag_redraw
from ..sollumz_helper import get_sollumz_materials
from .properties import DrawableShaderOrder


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

    def execute(self, context):
        selected_meshes = [
            obj for obj in context.selected_objects if obj.type == "MESH"]

        if not selected_meshes:
            self.report({"INFO"}, f"No mesh objects selected!")
            return {"CANCELLED"}

        auto_embed_col = context.scene.auto_create_embedded_col
        do_center = context.scene.center_drawable_to_selection

        if context.scene.create_seperate_drawables or len(selected_meshes) == 1:
            self.convert_separate_drawables(selected_meshes, auto_embed_col)
        else:
            self.convert_to_single_drawable(
                selected_meshes, auto_embed_col, do_center)

        self.report(
            {"INFO"}, f"Succesfully converted all selected objects to a Drawable.")

        return {"FINISHED"}

    def convert_separate_drawables(self, selected_meshes: list[bpy.types.Object], auto_embed_col: bool = False):
        for obj in selected_meshes:
            drawable_obj = convert_obj_to_drawable(obj)

            if auto_embed_col:
                composite_obj = convert_obj_to_composite(
                    duplicate_object(obj), SollumType.BOUND_GEOMETRYBVH, True)
                composite_obj.parent = drawable_obj
                composite_obj.name = f"{drawable_obj.name}.col"

    def convert_to_single_drawable(self, selected_meshes: list[bpy.types.Object], auto_embed_col: bool = False, do_center: bool = False):
        drawable_obj = convert_objs_to_single_drawable(selected_meshes)

        if do_center:
            center_drawable_to_models(drawable_obj)

        if auto_embed_col:
            col_objs = [duplicate_object(o) for o in selected_meshes]
            composite_obj = convert_objs_to_single_composite(
                col_objs, SollumType.BOUND_GEOMETRYBVH, True)
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


class SOLLUMZ_OT_create_light(SOLLUMZ_OT_base, bpy.types.Operator):
    bl_idname = "sollumz.create_light"
    bl_label = "Create Light"
    bl_action = bl_label

    def run(self, context):
        light_type = context.scene.create_light_type
        blender_light_type = "POINT"
        if light_type == LightType.SPOT:
            blender_light_type = "SPOT"

        light_data = bpy.data.lights.new(
            name=SOLLUMZ_UI_NAMES[light_type], type=blender_light_type)
        light_data.light_properties.type = light_type
        obj = bpy.data.objects.new(
            name=SOLLUMZ_UI_NAMES[light_type], object_data=light_data)
        obj.sollum_type = SollumType.LIGHT
        bpy.context.collection.objects.link(obj)


class MaterialConverterHelper:
    bl_options = {"UNDO"}

    def get_materials(self, obj: bpy.types.Object):
        materials = obj.data.materials

        if len(materials) == 0:
            self.report({"INFO"}, f"{obj.name} has no materials to convert!")

        return materials

    def get_shader_name(self):
        return shadermats[bpy.context.scene.shader_material_index].value

    def convert_material(self, obj: bpy.types.Object, material: bpy.types.Material) -> bpy.types.Material | None:
        return MaterialConverter(obj, material).convert(self.get_shader_name())

    def execute(self, context):
        for obj in context.selected_objects:
            materials = self.get_materials(obj)

            for material in materials:
                new_material = self.convert_material(obj, material)

                if new_material is None:
                    continue

                self.report(
                    {"INFO"}, f"Successfuly converted material '{new_material.name}'.")

        return {"FINISHED"}


class SOLLUMZ_OT_convert_allmaterials_to_selected(bpy.types.Operator, MaterialConverterHelper):
    """Convert all materials to the selected sollumz shader"""
    bl_idname = "sollumz.convertallmaterialstoselected"
    bl_label = "Convert All Materials To Selected"


class SOLLUMZ_OT_convert_material_to_selected(bpy.types.Operator, MaterialConverterHelper):
    """Convert objects material to the selected sollumz shader"""
    bl_idname = "sollumz.convertmaterialtoselected"
    bl_label = "Convert Material To Selected Sollumz Shader"

    def get_materials(self, obj: bpy.types.Object):
        if obj.active_material is None:
            self.report({"INFO"}, f"{obj.name} has no active material!")
            return []

        return [obj.active_material]


class SOLLUMZ_OT_auto_convert_material(bpy.types.Operator, MaterialConverterHelper):
    """Attempt to automatically determine shader name from material node setup and convert the material to a Sollumz material."""
    bl_idname = "sollumz.autoconvertmaterial"
    bl_label = "Convert Material To Shader Material"

    def convert_material(self, obj: bpy.types.Object, material: bpy.types.Material) -> bpy.types.Material | None:
        if material.sollum_type == MaterialType.SHADER:
            return None

        return MaterialConverter(obj, material).auto_convert()


class SOLLUMZ_OT_create_shader_material(SOLLUMZ_OT_base, bpy.types.Operator):
    """Create a sollumz shader material"""
    bl_idname = "sollumz.createshadermaterial"
    bl_label = "Create Shader Material"
    bl_action = "Create a Shader Material"

    def create_material(self, context, obj, shader):
        mat = create_shader(shader)
        obj.data.materials.append(mat)

        for n in mat.node_tree.nodes:
            if isinstance(n, bpy.types.ShaderNodeTexImage):
                texture = bpy.data.images.new(
                    name="Texture", width=512, height=512)
                n.image = texture

        if is_tint_material(mat):
            create_tinted_shader_graph(obj)

    def run(self, context):

        objs = bpy.context.selected_objects
        if len(objs) == 0:
            self.warning(
                f"Please select a object to add a shader material to.")
            return False

        for obj in objs:
            shader = shadermats[context.scene.shader_material_index].value
            try:
                self.create_material(context, obj, shader)
                self.message(f"Added a {shader} shader to {obj.name}.")
            except:
                self.message(
                    f"Failed adding {shader} to {obj.name} because : \n {traceback.format_exc()}")

        return True


class SOLLUMZ_OT_set_all_textures_embedded(SOLLUMZ_OT_base, bpy.types.Operator):
    """Sets all textures to embedded on the selected objects active material"""
    bl_idname = "sollumz.setallembedded"
    bl_label = "Set all Textures Embedded"
    bl_action = "Set all Textures Embedded"

    def set_textures_embedded(self, obj):
        mat = obj.active_material
        if mat is None:
            self.message(f"No active material on {obj.name} will be skipped")
            return

        if mat.sollum_type == MaterialType.SHADER:
            for node in mat.node_tree.nodes:
                if isinstance(node, bpy.types.ShaderNodeTexImage):
                    node.texture_properties.embedded = True
            self.message(
                f"Set {obj.name}s material {mat.name} textures to embedded.")
        else:
            self.message(
                f"Skipping object {obj.name} because it does not have a sollumz shader active.")

    def run(self, context):
        objs = [obj for obj in context.selected_objects if obj.type == "MESH"]
        if len(objs) == 0:
            self.message(
                f"No mesh objects selected!")
            return False

        for obj in objs:
            self.set_textures_embedded(obj)

        return True


class SOLLUMZ_OT_set_all_materials_embedded(SOLLUMZ_OT_base, bpy.types.Operator):
    """Sets all materials to embedded"""
    bl_idname = "sollumz.setallmatembedded"
    bl_label = "Set all Materials Embedded"
    bl_action = "Set All Materials Embedded"

    def set_materials_embedded(self, obj):
        for mat in obj.data.materials:
            if mat.sollum_type == MaterialType.SHADER:
                for node in mat.node_tree.nodes:
                    if isinstance(node, bpy.types.ShaderNodeTexImage):
                        node.texture_properties.embedded = True
                self.message(
                    f"Set {obj.name}s material {mat.name} textures to embedded.")
            else:
                self.message(
                    f"Skipping object {obj.name} because it does not have a sollumz shader active.")

    def run(self, context):
        objs = [obj for obj in context.selected_objects if obj.type == "MESH"]
        if len(objs) == 0:
            self.message(
                f"No mesh objects selected!")
            return False

        for obj in objs:
            self.set_materials_embedded(obj)

        return True


class SOLLUMZ_OT_remove_all_textures_embedded(SOLLUMZ_OT_base, bpy.types.Operator):
    """Remove all embeded textures on the selected objects active material"""
    bl_idname = "sollumz.removeallembedded"
    bl_label = "Remove all Embeded Textures"
    bl_action = "Remove all Embeded Textures"

    def set_textures_unembedded(self, obj):
        mat = obj.active_material
        if mat == None:
            self.message(f"No active material on {obj.name} will be skipped")
            return

        if mat.sollum_type == MaterialType.SHADER:
            for node in mat.node_tree.nodes:
                if (isinstance(node, bpy.types.ShaderNodeTexImage)):
                    node.texture_properties.embedded = False
            self.message(
                f"Set {obj.name}s material {mat.name} textures to unembedded.")
        else:
            self.message(
                f"Skipping object {obj.name} because it does not have a sollumz shader active.")

    def run(self, context):
        objs = [obj for obj in context.selected_objects if obj.type == "MESH"]
        if len(objs) == 0:
            self.message(
                f"No mesh objects selected!")
            return False

        for obj in objs:
            self.set_textures_unembedded(obj)

        return True


class SOLLUMZ_OT_unset_all_materials_embedded(SOLLUMZ_OT_base, bpy.types.Operator):
    """Make all materials on the selected object use non-embedded textures"""
    bl_idname = "sollumz.removeallmatembedded"
    bl_label = "Set all Materials Unembedded"
    bl_action = "Set all Materials Unembedded"

    def set_materials_unembedded(self, obj):
        for mat in obj.data.materials:
            if mat.sollum_type == MaterialType.SHADER:
                for node in mat.node_tree.nodes:
                    if (isinstance(node, bpy.types.ShaderNodeTexImage)):
                        node.texture_properties.embedded = False
                self.message(
                    f"Set {obj.name}s materials to unembedded.")
            else:
                self.message(
                    f"Skipping object {obj.name} because it does not have a sollumz shader active.")

    def run(self, context):
        objs = [obj for obj in context.selected_objects if obj.type == "MESH"]
        if len(objs) == 0:
            self.message(
                f"No mesh objects selected!")
            return False

        for obj in objs:
            self.set_materials_unembedded(obj)

        return True


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


class SOLLUMZ_OT_LIGHT_TIME_FLAGS_select_range(SelectTimeFlagsRange, bpy.types.Operator):
    bl_idname = "sollumz.light_time_flags_select_range"

    @classmethod
    def poll(cls, context):
        return context.light and context.active_object.sollum_type == SollumType.LIGHT

    def get_flags(self, context):
        light = context.light
        return light.time_flags


class SOLLUMZ_OT_LIGHT_TIME_FLAGS_clear(ClearTimeFlags, bpy.types.Operator):
    bl_idname = "sollumz.light_time_flags_clear"

    @classmethod
    def poll(cls, context):
        return context.light and context.active_object.sollum_type == SollumType.LIGHT

    def get_flags(self, context):
        light = context.light
        return light.time_flags


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


class ObjectPoseModeRestrictedHelper:
    @classmethod
    def poll(cls, context: Context):
        cls.poll_message_set("Must be in object mode or pose mode.")
        return context.mode == "OBJECT" or context.mode == "POSE"


class SOLLUMZ_OT_clear_bone_flags(bpy.types.Operator, ObjectPoseModeRestrictedHelper):
    bl_idname = "sollumz.removeboneflags"
    bl_label = "Remove Bone Flags"
    bl_description = "Remove all bone flags for selected bones"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        bone = context.active_bone
        bone.bone_properties.flags.clear()
        tag_redraw(context)
        self.report({'INFO'}, "Flags Removed")
        return {'FINISHED'}


class SOLLUMZ_OT_rotation_bone_flags(bpy.types.Operator, ObjectPoseModeRestrictedHelper):
    bl_idname = "sollumz.rotationboneflags"
    bl_label = "Add Rotation Flags"
    bl_description = "Add rotation flags for selected bones"

    def execute(self, context):
        bone = context.active_bone
        new_flag = bone.bone_properties.flags.add()
        new_flag.name = "RotX"
        new_flag = bone.bone_properties.flags.add()
        new_flag.name = "RotY"
        new_flag = bone.bone_properties.flags.add()
        new_flag.name = "RotZ"
        tag_redraw(context)
        self.report({'INFO'}, "Rotation Flags Added")
        return {'FINISHED'}


class SOLLUMZ_OT_transform_bone_flags(bpy.types.Operator, ObjectPoseModeRestrictedHelper):
    bl_idname = "sollumz.transformboneflags"
    bl_label = "Add Transform Flags"
    bl_description = "Add transform flags for selected bones"

    def execute(self, context):
        bone = context.active_bone
        new_flag = bone.bone_properties.flags.add()
        new_flag.name = "TransX"
        new_flag = bone.bone_properties.flags.add()
        new_flag.name = "TransY"
        new_flag = bone.bone_properties.flags.add()
        new_flag.name = "TransZ"
        tag_redraw(context)
        self.report({'INFO'}, "Transform Flags Added")
        return {'FINISHED'}


class SOLLUMZ_OT_scale_bone_flags(bpy.types.Operator, ObjectPoseModeRestrictedHelper):
    bl_idname = "sollumz.scaleboneflags"
    bl_label = "Add Scale Flags"
    bl_description = "Add scale flags for selected bones"

    def execute(self, context):
        bone = context.active_bone
        new_flag = bone.bone_properties.flags.add()
        new_flag.name = "ScaleX"
        new_flag = bone.bone_properties.flags.add()
        new_flag.name = "ScaleY"
        new_flag = bone.bone_properties.flags.add()
        new_flag.name = "ScaleZ"
        tag_redraw(context)
        self.report({'INFO'}, "Scale Flags Added")
        return {'FINISHED'}


class SOLLUMZ_OT_limit_bone_flags(bpy.types.Operator, ObjectPoseModeRestrictedHelper):
    bl_idname = "sollumz.limitboneflags"
    bl_label = "Add Limit Flags"
    bl_description = "Removes selected bone flags and adds the proper limit flags for custom bone locations"

    def execute(self, context):
        bone = context.active_bone
        new_flag = bone.bone_properties.flags.add()
        new_flag.name = "LimitRotation"
        new_flag = bone.bone_properties.flags.add()
        new_flag.name = "LimitTranslation"
        tag_redraw(context)
        self.report({'INFO'}, "Limit Flags Added")
        return {'FINISHED'}


class SOLLUMZ_OT_move_shader_up(bpy.types.Operator):
    bl_idname = "sollumz.move_shader_up"
    bl_label = "Up"
    bl_description = "Move shader up in the rendering order"

    @classmethod
    def poll(self, context):
        aobj = context.active_object

        if aobj is None or aobj.sollum_type != SollumType.DRAWABLE:
            return False

        drawable_props = aobj.drawable_properties
        num_shaders = len(drawable_props.shader_order.items)
        shader_ind = drawable_props.shader_order.get_active_shader_item_index()

        return shader_ind < num_shaders and shader_ind != 0

    def execute(self, context):
        aobj = context.active_object
        drawable_props = aobj.drawable_properties
        shader_ind = drawable_props.shader_order.get_active_shader_item_index()

        drawable_props.shader_order.change_shader_index(
            shader_ind, shader_ind - 1)

        return {"FINISHED"}


class SOLLUMZ_OT_move_shader_down(bpy.types.Operator):
    bl_idname = "sollumz.move_shader_down"
    bl_label = "Down"
    bl_description = "Move shader down in the rendering order"

    @classmethod
    def poll(self, context):
        aobj = context.active_object

        if aobj is None or aobj.sollum_type != SollumType.DRAWABLE:
            return False

        drawable_props = aobj.drawable_properties
        num_shaders = len(drawable_props.shader_order.items)
        shader_ind = drawable_props.shader_order.get_active_shader_item_index()

        return shader_ind < num_shaders - 1 and num_shaders > 1

    def execute(self, context):
        aobj = context.active_object
        drawable_props = aobj.drawable_properties
        shader_ind = drawable_props.shader_order.get_active_shader_item_index()

        drawable_props.shader_order.change_shader_index(
            shader_ind, shader_ind + 1)

        return {"FINISHED"}


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

        col.template_list("SOLLUMZ_UL_SHADER_ORDER_LIST", "", shader_order, "items",
                          shader_order, "active_index", maxrows=40)

        col = row.column(align=True)
        col.operator("sollumz.move_shader_up", text="", icon="TRIA_UP")
        col.operator("sollumz.move_shader_down", text="", icon="TRIA_DOWN")

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

        shader_order.items.clear()

        for mat in mats:
            item = shader_order.items.add()
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

        if len(shader_order.items) != len(mats):
            self.report(
                {"ERROR"}, "Failed to apply order, shader collection size mismatch!")
            return {"CANCELLED"}

        for i, mat in enumerate(mats):
            mat.shader_properties.index = shader_order.items[i].index

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
    bl_description = "Generate Drawable Model LODs via decimate modifier. Uses object's current mesh as highest LOD level"

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

        obj_lods: LODLevels = aobj.sollumz_lods

        if not self.has_sollumz_lods(aobj):
            obj_lods.add_empty_lods()

        decimate_step = context.scene.sollumz_auto_lod_decimate_step
        last_mesh = ref_mesh

        previous_mode = aobj.mode
        previous_lod_level = obj_lods.active_lod.level

        for lod_level in lods:
            mesh = last_mesh.copy()
            mesh.name = self.get_lod_mesh_name(aobj.name, lod_level)

            obj_lods.set_lod_mesh(lod_level, mesh)
            obj_lods.set_active_lod(lod_level)

            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.decimate(ratio=1.0 - decimate_step)
            bpy.ops.object.mode_set(mode=previous_mode)

            last_mesh = mesh

        obj_lods.set_active_lod(previous_lod_level)

        return {"FINISHED"}

    def has_sollumz_lods(self, obj: bpy.types.Object):
        """Ensure obj has sollumz_lods.lods populated"""
        obj_lod_levels = [lod.level for lod in obj.sollumz_lods.lods]
        return all(lod_level in obj_lod_levels for lod_level in LODLevel)

    def get_lod_mesh_name(self, obj_name: str, lod_level: LODLevel):
        return f"{obj_name}.{SOLLUMZ_UI_NAMES[lod_level].lower()}"

    def get_selected_lods_sorted(self, context: Context) -> tuple[LODLevel]:
        lod_levels = [LODLevel.VERYHIGH, LODLevel.HIGH,
                      LODLevel.MEDIUM, LODLevel.LOW, LODLevel.VERYLOW]

        return tuple(lod for lod in lod_levels if lod in context.scene.sollumz_auto_lod_levels)


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

        for lod_level in lod_levels:
            lod = aobj.sollumz_lods.get_lod(lod_level)

            if lod is None or lod.mesh is None:
                continue

            mesh = lod.mesh
            lod_obj = create_blender_object(SollumType.NONE, mesh.name, mesh)
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
