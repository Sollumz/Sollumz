from math import ceil
from ..tools.obb import get_obb, get_obb_extents
import traceback
from ..cwxml.flag_preset import FlagPreset
from ..ybn.properties import BoundFlags, load_flag_presets, flag_presets, get_flag_presets_path
from ..ybn.collision_materials import create_collision_material_from_index
from ..tools.boundhelper import create_bound_shape, convert_objs_to_composites, convert_objs_to_single_composite, center_composite_to_children, apply_flag_preset
from ..tools.meshhelper import create_box_from_extents
from ..sollumz_properties import SollumType, SOLLUMZ_UI_NAMES, BOUND_TYPES, MaterialType, BOUND_POLYGON_TYPES
from ..sollumz_helper import SOLLUMZ_OT_base
from ..tools.blenderhelper import get_selected_vertices, get_children_recursive, create_blender_object, create_empty_object, tag_redraw
import bpy
from mathutils import Vector


class SOLLUMZ_OT_create_polygon_bound(bpy.types.Operator):
    """Create a BVH bound child"""
    bl_idname = "sollumz.createpolygonbound"
    bl_label = "Create BVH Child"

    def execute(self, context):
        bound_type = context.scene.create_poly_bound_type

        selected = context.selected_objects

        if selected:
            parent = selected[0]
        else:
            parent = None

        bound_obj = create_bound_shape(bound_type)
        bound_obj.parent = parent

        return {"FINISHED"}


class SOLLUMZ_OT_create_polygon_box_from_verts(bpy.types.Operator):
    """Creates a Bound Box or Bound Poly Box from the selected vertices"""
    bl_idname = "sollumz.createpolyboxfromverts"
    bl_label = "Create Box from Selection"
    bl_options = {"UNDO", "REGISTER"}

    parent_name: bpy.props.StringProperty(
        name="Parent",
        description="Parent for the new box object. If not set, the parent of the active object is used."
    )
    num_samples: bpy.props.IntProperty(
        name="Number of Samples",
        description="Number of samples to use to find the best orientation for the bounding box",
        default=100,
        min=1,
        max=1000
    )
    angle_step: bpy.props.IntProperty(
        name="Range Precision",
        description="Amount of angle steps to skip, this can be useful in situations where number of samples alone doesn't give a precise result. Lower values mean higher precision",
        default=2,
        min=1,
        max=10
    )
    sollum_type: bpy.props.EnumProperty(
        items=[
            (SollumType.BOUND_POLY_BOX.value, SOLLUMZ_UI_NAMES[SollumType.BOUND_POLY_BOX], "Create a bound polygon box object"),
            (SollumType.BOUND_BOX.value, SOLLUMZ_UI_NAMES[SollumType.BOUND_BOX], "Create a bound box object")],
        name="Type",
        default=None
    )

    @classmethod
    def poll(self, context):
        self.poll_message_set("Must be in Edit Mode.")
        return context.mode == "EDIT_MESH"

    def execute(self, context):
        objects = context.objects_in_mode
        verts: list[Vector] = []
        for obj in objects:
            verts.extend(get_selected_vertices(obj))

        parent = None
        if self.parent_name:
            parent = bpy.data.objects.get(self.parent_name, None)

        if not parent and objects:
            # If no explicit parent chosen by the user, place it as sibling of the active object
            # First object in objects_in_mode is the active object
            parent = objects[0].parent

        if len(verts) < 3:
            self.report({"INFO"}, "Please select at least three vertices.")
            return {"CANCELLED"}

        pobj = create_blender_object(self.sollum_type)

        obb, world_matrix = get_obb(verts, self.num_samples, self.angle_step)
        bbmin, bbmax = get_obb_extents(obb)

        center = world_matrix @ (bbmin + bbmax) / 2
        local_center = (bbmin + bbmax) / 2

        create_box_from_extents(pobj.data, bbmin - local_center, bbmax - local_center)

        pobj.matrix_world = world_matrix
        pobj.location = center

        pobj.parent = parent

        return {"FINISHED"}


class SOLLUMZ_OT_convert_to_composite(bpy.types.Operator):
    """Convert the selected object to a Bound Composite. Applies the selected flag preset to the created bounds"""
    bl_idname = "sollumz.converttocomposite"
    bl_label = "Convert to Composite"
    bl_options = {"UNDO"}

    def execute(self, context):
        selected_meshes = [
            obj for obj in context.selected_objects if obj.type == "MESH"]

        if not selected_meshes:
            self.report({"INFO"}, f"No mesh objects selected!")
            return {"CANCELLED"}

        bound_child_type = context.scene.bound_child_type
        do_center = context.scene.center_composite_to_selection

        flag_preset_index = context.window_manager.sz_flag_preset_index

        if context.scene.create_seperate_composites or len(selected_meshes) == 1:
            convert_objs_to_composites(selected_meshes, bound_child_type, flag_preset_index)
        else:
            composite_obj = convert_objs_to_single_composite(selected_meshes, bound_child_type, flag_preset_index)

            if do_center:
                center_composite_to_children(composite_obj)

        self.report({"INFO"}, f"Succesfully converted all selected objects to a Composite.")

        return {"FINISHED"}


class SOLLUMZ_OT_create_bound(bpy.types.Operator):
    """Create a Sollumz bound of the selected type. Applies the selected flag preset to the created bound"""
    bl_idname = "sollumz.createbound"
    bl_label = "Create Bound"
    bl_options = {"UNDO"}

    def execute(self, context):
        bound_type = context.scene.create_bound_type
        selected = context.selected_objects

        if selected:
            parent = selected[0]
        else:
            parent = None

        # Check the bound type and create the appropriate object
        if bound_type in [SollumType.BOUND_COMPOSITE, SollumType.BOUND_GEOMETRYBVH]:
            bound_obj = create_empty_object(bound_type)  # Create an empty for composites and BVH
        else:
            bound_obj = create_bound_shape(bound_type)  # Create shape for other bounds

        bound_obj.parent = parent

        apply_flag_preset(bound_obj, context.window_manager.sz_flag_preset_index)

        return {"FINISHED"}


class CreateCollisionMatHelper:
    def create_material(self, mat_index: int, obj: bpy.types.Object):
        mat = create_collision_material_from_index(mat_index)
        obj.data.materials.append(mat)

        self.report(
            {"INFO"}, f"Succesfully added {mat.name} material to {obj.name}")

    def execute(self, context):
        selected = context.selected_objects

        if len(selected) < 1:
            self.report({"WARNING"}, "No objects selected")

            return {"CANCELLED"}

        mat_index = context.window_manager.sz_collision_material_index

        for obj in selected:
            self.create_material(mat_index, obj)

        return {"FINISHED"}


class SOLLUMZ_OT_create_collision_material(CreateCollisionMatHelper, bpy.types.Operator):
    """Create a sollumz collision material"""
    bl_idname = "sollumz.createcollisionmaterial"
    bl_label = "Create Collision Material"


class SOLLUMZ_OT_clear_and_create_collision_material(CreateCollisionMatHelper, bpy.types.Operator):
    """Delete all materials on selected object(s) and add selected collision material"""
    bl_idname = "sollumz.clearandcreatecollisionmaterial"
    bl_label = "Clear and Create Collision Material"

    def create_material(self, mat_index: int, obj: bpy.types.Object):
        obj.data.materials.clear()
        super().create_material(mat_index, obj)


class SOLLUMZ_OT_convert_non_collision_materials_to_selected(CreateCollisionMatHelper, bpy.types.Operator):
    """Convert all non-collision materials to the selected collision material"""
    bl_idname = "sollumz.convertnoncollisionmaterialstoselected"
    bl_label = "Convert Non-Collision Materials To Selected"

    def create_material(self, mat_index: int, obj: bpy.types.Object):
        mat = create_collision_material_from_index(mat_index)

        for i, material in enumerate(obj.data.materials):
            if material.sollum_type == MaterialType.COLLISION:
                continue

            obj.data.materials[i] = mat


class SOLLUMZ_OT_convert_to_collision_material(SOLLUMZ_OT_base, bpy.types.Operator):
    """Convert material to a collision material"""
    bl_idname = "sollumz.converttocollisionmaterial"
    bl_label = "Convert To Selected"
    bl_action = f"{bl_label}"

    def run(self, context):
        aobj = context.active_object
        if not aobj:
            self.message("No object selected!")
            return False

        active_mat = aobj.active_material
        if not active_mat:
            self.message("No material selected!")
            return False

        mat = create_collision_material_from_index(context.window_manager.sz_collision_material_index)
        
        if context.scene.convert_all_to_collision_material:
            for obj in bpy.data.objects:
                if obj.type == 'MESH':
                    for i, slot in enumerate(obj.data.materials):
                        if slot == active_mat:
                            obj.data.materials[i] = mat
        else:
            active_mat_index = aobj.active_material_index
            aobj.data.materials[active_mat_index] = mat


class SOLLUMZ_OT_delete_flag_preset(SOLLUMZ_OT_base, bpy.types.Operator):
    """Delete a flag preset"""
    bl_idname = "sollumz.delete_flag_preset"
    bl_label = "Delete Flag Preset"
    bl_action = f"{bl_label}"

    preset_blacklist = [
        "General (Default)",
        "General 2",
        "Water surface",
        "Leaves - Bush",
        "Stair plane",
        "Stair mesh",
        "Deep surface",
    ]

    def run(self, context):
        index = context.window_manager.sz_flag_preset_index
        load_flag_presets()

        try:
            preset = flag_presets.presets[index]
            if preset.name in self.preset_blacklist:
                self.message("Cannot delete a default preset!")
                return False

            filepath = get_flag_presets_path()
            flag_presets.presets.remove(preset)

            try:
                flag_presets.write_xml(filepath)
                load_flag_presets()

                return True
            except:
                self.error(
                    f"Error during deletion of flag preset: {traceback.format_exc()}")
                return False

        except IndexError:
            self.message(
                f"Flag preset does not exist! Ensure the preset file is present in the '{filepath}' directory.")
            return False


class SOLLUMZ_OT_save_flag_preset(SOLLUMZ_OT_base, bpy.types.Operator):
    """Save a flag preset"""
    bl_idname = "sollumz.save_flag_preset"
    bl_label = "Save Flag Preset"
    bl_action = f"{bl_label}"

    name: bpy.props.StringProperty(name="Name")

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.sollum_type in BOUND_TYPES

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def run(self, context):
        self.name = self.name.strip()
        if len(self.name) == 0:
            self.warning("Please specify a name for the new flag preset.")
            return False

        obj = context.active_object

        if not obj:
            self.message("No object selected!")
            return False

        if obj.sollum_type not in BOUND_TYPES:
            self.message("Selected object must be a Sollumz bound!")
            return False

        load_flag_presets()

        for preset in flag_presets.presets:
            if preset.name == self.name:
                self.warning(
                    "A preset with that name already exists! If you wish to overwrite this preset, delete the original.")
                return False

        flag_preset = FlagPreset()
        flag_preset.name = self.name

        for prop in dir(obj.composite_flags1):
            value = getattr(obj.composite_flags1, prop)
            if value is True:
                flag_preset.flags1.append(prop)

        for prop in dir(obj.composite_flags2):
            value = getattr(obj.composite_flags2, prop)
            if value is True:
                flag_preset.flags2.append(prop)

        flag_presets.presets.append(flag_preset)

        filepath = get_flag_presets_path()
        flag_presets.write_xml(filepath)
        load_flag_presets()

        tag_redraw(context, space_type="VIEW_3D", region_type="UI")
        return True


class SOLLUMZ_OT_load_flag_preset(SOLLUMZ_OT_base, bpy.types.Operator):
    """Load a flag preset to the selected bounds"""
    bl_idname = "sollumz.load_flag_preset"
    bl_label = "Apply Flags Preset"
    bl_context = "object"
    bl_options = {"REGISTER", "UNDO"}
    bl_action = f"{bl_label}"

    def run(self, context):
        index = context.window_manager.sz_flag_preset_index
        selected = context.selected_objects
        if len(selected) < 1:
            self.message("No objects selected!")
            return False

        load_flag_presets()

        for obj in selected:
            try:
                if apply_flag_preset(obj, index, reload_presets=False):
                    preset = flag_presets.presets[index]
                    self.message(f"Applied preset '{preset.name}' to: {obj.name}")
            except IndexError:
                filepath = get_flag_presets_path()
                self.error(
                    f"Flag preset does not exist! Ensure the preset file is present in the '{filepath}' directory.")
                return False

        tag_redraw(context)
        return True


class SOLLUMZ_OT_clear_col_flags(SOLLUMZ_OT_base, bpy.types.Operator):
    """Load commonly used collision flags"""
    bl_idname = "sollumz.clear_col_flags"
    bl_label = "Clear Collision Flags"
    bl_action = f"{bl_label}"

    def run(self, context):

        aobj = context.active_object
        if aobj is None:
            self.message("Please select an object.")
            return False

        if aobj.sollum_type in BOUND_TYPES:
            for flag_name in BoundFlags.__annotations__.keys():
                aobj.composite_flags1[flag_name] = False
                aobj.composite_flags2[flag_name] = False

            tag_redraw(context)


        return True
