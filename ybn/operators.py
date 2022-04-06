from math import ceil
from ..tools.obb import get_obb, get_obb_extents
import traceback
from ..resources.flag_preset import FlagPreset
from ..ybn.properties import BoundFlags, load_flag_presets, flag_presets, get_flag_presets_path
from ..ybn.collision_materials import create_collision_material_from_index
from ..tools.boundhelper import *
from ..tools.meshhelper import *
from ..sollumz_properties import BOUND_SHAPE_TYPES, SollumType, SOLLUMZ_UI_NAMES, BOUND_TYPES
from ..sollumz_helper import SOLLUMZ_OT_base
from ..tools.blenderhelper import get_selected_vertices
from ..sollumz_helper import *
import bpy


def handle_load_flag_presets(self):
    try:
        load_flag_presets()
    except FileNotFoundError:
        self.report({'ERROR'}, traceback.format_exc())


class SOLLUMZ_OT_create_polygon_bound(SOLLUMZ_OT_base, bpy.types.Operator):
    """Create a sollumz polygon bound of the selected type."""
    bl_idname = "sollumz.createpolygonbound"
    bl_label = "Create Polygon Bound"
    bl_action = f"{bl_label}"
    bl_update_view = True

    def create_poly_from_verts(self, context, type, parent):
        if not parent:
            self.message("Must specify a parent object!")
            return False
        elif parent.sollum_type != SollumType.BOUND_GEOMETRYBVH and parent.sollum_type != SollumType.BOUND_GEOMETRY:
            self.message(
                f'Parent must be a {SOLLUMZ_UI_NAMES[SollumType.BOUND_GEOMETRYBVH]} or {SOLLUMZ_UI_NAMES[SollumType.BOUND_GEOMETRY]}!')
            return False

        selected = context.selected_objects

        if len(selected) < 1 and context.active_object:
            selected = [context.active_object]

        verts = []
        for obj in selected:
            verts.extend(get_selected_vertices(obj))

        if len(verts) < 3:
            self.message("Please select at least three vertices.")
            return False

        if type != SollumType.BOUND_POLY_TRIANGLE:
            pobj = create_bound_shape(
                type) if type != SollumType.BOUND_POLY_BOX else create_mesh(type)

            obb, world_matrix = get_obb(verts)
            bbmin, bbmax = get_obb_extents(obb)

            center = world_matrix @ (bbmin + bbmax) / 2
            local_center = (bbmin + bbmax) / 2

            # long, short = get_short_long_edge(bbmin, bbmax)

            # if context.scene.poly_edge == 'short':
            #     t1 = long
            #     long = short
            #     short = t1
            #     world_matrix = Matrix.Rotation(
            #         degrees(90), 4, 'Z') @ world_matrix

            if type == SollumType.BOUND_POLY_BOX:
                create_box_from_extents(
                    pobj.data, bbmin - local_center, bbmax - local_center)
            # elif type == SollumType.BOUND_POLY_SPHERE:
            #     pobj.bound_radius = (bbmax - bbmin).magnitude / 2
            # elif type == SollumType.BOUND_POLY_CAPSULE or type == SollumType.BOUND_POLY_CYLINDER:
            #     pobj.bound_radius = short / 2
            #     pobj.bound_length = long
            pobj.matrix_world = world_matrix
            pobj.location = center
        else:
            if obj.mode == 'EDIT':
                bm = bmesh.from_edit_mesh(obj.data)
            else:
                bm = bmesh.new()
                bm.from_mesh(obj.data)
            new_mesh = bmesh.new()

            onm = {}  # old index to new vert map
            selected_verts = [v for v in bm.verts if v.select]

            if len(selected_verts) < 3:
                self.message("Please select at least three vertices.")
                return False

            for v in selected_verts:
                nv = new_mesh.verts.new(v.co)
                onm[v.index] = nv

            for f in [f for f in bm.faces if f.select]:
                nfverts = [onm[v.index] for v in f.verts]
                new_mesh.faces.new(nfverts)

            pobj = create_mesh(type)
            pobj.location = obj.location
            new_mesh.to_mesh(pobj.data)
            bm.free()
            new_mesh.free()

        pobj.parent = parent

        return True

    def run(self, context):
        aobj = context.active_object
        parent = context.scene.poly_parent
        poly_bound_type = context.scene.create_poly_bound_type

        if aobj and aobj.mode == "EDIT":
            return self.create_poly_from_verts(context, context.scene.poly_bound_type_verts, parent)
        else:
            if poly_bound_type == SollumType.BOUND_POLY_TRIANGLE and aobj:
                aobj.sollum_type = poly_bound_type
            else:
                obj = create_bound_shape(poly_bound_type)
                if aobj:
                    obj.parent = aobj
            return True


class SOLLUMZ_OT_create_bound(SOLLUMZ_OT_base, bpy.types.Operator):
    """Create a sollumz bound of the selected type."""
    bl_idname = "sollumz.createbound"
    bl_label = f"Create Bound"
    bl_action = f"{bl_label}"
    bl_update_view = True

    def run(self, context):
        aobj = context.active_object
        selected = context.selected_objects
        bound_type = context.scene.create_bound_type

        if bound_type == SollumType.BOUND_COMPOSITE and len(selected) > 0:
            convert_selected_to_bound(
                selected, context.scene.use_mesh_name, context.scene.create_seperate_objects, context.scene.composite_create_bvh, context.scene.composite_replace_original, context.scene.create_center_to_selection)
            return True
        elif bound_type in BOUND_SHAPE_TYPES:
            obj = create_bound_shape(bound_type)
        else:
            obj = create_bound(bound_type)
        if aobj:
            obj.parent = aobj
        return True


class SOLLUMZ_OT_center_composite(SOLLUMZ_OT_base, bpy.types.Operator):
    f"""Center the selected {SOLLUMZ_UI_NAMES[SollumType.BOUND_COMPOSITE]} with the rest of it's geometry. Note: Has no effect on export"""
    bl_idname = "sollumz.centercomposite"
    bl_label = "Center Composite"
    bl_action = f"{bl_label}"

    def run(self, context):
        aobj = context.active_object
        if not aobj:
            self.message(
                f"No {SOLLUMZ_UI_NAMES[SollumType.BOUND_COMPOSITE]} selected.")
            return False
        if aobj.sollum_type != SollumType.BOUND_COMPOSITE:
            self.message(
                f"{aobj.name} must be a {SOLLUMZ_UI_NAMES[SollumType.BOUND_COMPOSITE]}!")
            return False
        if context.mode != 'OBJECT':
            self.message(f"{self.bl_idname} can only be ran in Object mode.")
            return False

        center = get_bound_center(aobj)
        aobj.location = center
        for obj in aobj.children:
            obj.delta_location = -center
        return True


class SOLLUMZ_OT_create_collision_material(SOLLUMZ_OT_base, bpy.types.Operator):
    """Create a sollumz collision material"""
    bl_idname = "sollumz.createcollisionmaterial"
    bl_label = "Create Collision Material"
    bl_action = f"{bl_label}"

    def run(self, context):

        selected = context.selected_objects
        if len(selected) < 1:
            self.message("No objects selected")
            return False

        for obj in selected:
            try:
                mat = create_collision_material_from_index(
                    context.scene.collision_material_index)
                obj.data.materials.append(mat)
                self.messages.append(
                    f"Succesfully added {mat.name} material to {obj.name}")
            except:
                self.messages.append(f"Failure to add material to {obj.name}")

        return True


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

        mat = create_collision_material_from_index(
            context.scene.collision_material_index)
        active_mat_index = aobj.active_material_index
        aobj.data.materials[active_mat_index] = mat


class SOLLUMZ_OT_clear_and_create_collision_material(SOLLUMZ_OT_base, bpy.types.Operator):
    """Delete all materials on selected object(s) and add selected collision material."""
    bl_idname = "sollumz.clearandcreatecollisionmaterial"
    bl_label = "Clear and Create Collision Material"
    bl_action = f"{bl_label}"

    def run(self, context):
        selected = context.selected_objects
        if len(selected) < 1:
            self.message("No objects selected")
            return False

        for obj in selected:
            try:
                obj.data.materials.clear()
                mat = create_collision_material_from_index(
                    context.scene.collision_material_index)
                obj.data.materials.append(mat)
            except Exception as e:
                self.warning(
                    f"Failure to add material to {obj.name}: {traceback.format_exc()}")

        return True


class SOLLUMZ_OT_split_collision(SOLLUMZ_OT_base, bpy.types.Operator):
    """Split a collision into many parts. Sorted based on location"""
    bl_idname = "sollumz.splitcollision"
    bl_label = "Split Collision"
    bl_action = f"{bl_label}"

    def run(self, context):
        selected = context.selected_objects
        if len(selected) < 1:
            self.message("No objects selected.")
            return False

        # Gather all selected collision objects and store as hierarchy
        selected_composites = {}
        num_bound_polys_selected = 0
        for composite in selected:
            if composite.sollum_type != SollumType.BOUND_COMPOSITE:
                self.message(
                    f"Selected object {composite.name} is not a {SOLLUMZ_UI_NAMES[SollumType.BOUND_COMPOSITE]}, skipping...")
                continue

            # Create list for storing bound polys
            selected_composites[composite] = []
            # Gather GeometryBVH(s)
            for bvh in get_children_recursive(composite):
                if bvh.sollum_type == SollumType.BOUND_GEOMETRYBVH:
                    for bound_poly in bvh.children:
                        if bound_poly.sollum_type in BOUND_POLYGON_TYPES:
                            selected_composites[composite].append(
                                bound_poly)
                            num_bound_polys_selected += 1

        # Split objects
        for composite, bound_polys in selected_composites.items():
            composite_name = composite.name
            composite.name = ""

            parts_per_col = ceil(
                num_bound_polys_selected / context.scene.split_collision_count)

            if num_bound_polys_selected < parts_per_col:
                self.message(
                    f"Can't divide by a value less than the number of Bound Polygon(s) ({num_bound_polys_selected} selected).")
                return False

            new_composite = None

            for i, bound_poly in enumerate(bound_polys):
                if i % parts_per_col == 0:
                    new_composite = create_bound(
                        SollumType.BOUND_COMPOSITE, do_link=False)

                    bound_poly.users_collection[0].objects.link(
                        new_composite)

                    new_composite.name = composite_name
                    new_composite.matrix_world = composite.matrix_world

                if new_composite is None:
                    continue

                if bound_poly is None:
                    continue

                bound_polys[i] = None

                new_bvh = create_bound(
                    SollumType.BOUND_GEOMETRYBVH, do_link=False)

                # Link the new empties to the object's collection (not always the active collection)
                bound_poly.users_collection[0].objects.link(new_bvh)

                bound_poly_mat = bound_poly.matrix_world.copy()

                new_bvh.parent = new_composite

                new_bvh.matrix_world = bound_poly.parent.matrix_world
                new_bvh.matrix_world.translation = bound_poly.matrix_world.translation

                bound_poly.parent = new_bvh

                bound_poly.matrix_world = bound_poly_mat
                bound_poly.location = Vector()

            for child in composite.children:
                if child.sollum_type == SollumType.BOUND_GEOMETRYBVH:
                    bpy.data.objects.remove(child)

            bpy.data.objects.remove(composite)

        return True


class SOLLUMZ_OT_delete_flag_preset(SOLLUMZ_OT_base, bpy.types.Operator):
    """Delete a flag preset"""
    bl_idname = "sollumz.delete_flag_preset"
    bl_label = "Delete Flag Preset"
    bl_action = f"{bl_label}"

    preset_blacklist = ['Default']

    def run(self, context):
        index = context.scene.flag_preset_index
        handle_load_flag_presets(self)

        try:
            preset = flag_presets.presets[index]
            if preset.name in self.preset_blacklist:
                self.message("Cannot delete a default preset!")
                return False

            filepath = get_flag_presets_path()
            flag_presets.presets.remove(preset)

            try:
                flag_presets.write_xml(filepath)
                handle_load_flag_presets(self)

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

    def run(self, context):
        obj = context.active_object
        handle_load_flag_presets(self)

        if not obj:
            self.message("No object selected!")
            return False

        if obj.sollum_type and not (obj.sollum_type == SollumType.BOUND_GEOMETRY or obj.sollum_type == SollumType.BOUND_GEOMETRYBVH):
            self.message(
                f"Selected object must be either a {SOLLUMZ_UI_NAMES[SollumType.BOUND_GEOMETRY]} or {SOLLUMZ_UI_NAMES[SollumType.BOUND_GEOMETRYBVH]}!")
            return False

        name = context.scene.new_flag_preset_name
        if len(name) < 1:
            self.message("Please specify a name for the new flag preset.")
            return False

        flag_preset = FlagPreset()
        flag_preset.name = name

        for prop in dir(obj.composite_flags1):
            value = getattr(obj.composite_flags1, prop)
            if value == True:
                flag_preset.flags1.append(prop)

        for prop in dir(obj.composite_flags2):
            value = getattr(obj.composite_flags2, prop)
            if value == True:
                flag_preset.flags2.append(prop)

        filepath = get_flag_presets_path()

        for preset in flag_presets.presets:
            if preset.name == name:
                self.message(
                    "A preset with that name already exists! If you wish to overwrite this preset, delete the original.")
                return False

        flag_presets.presets.append(flag_preset)
        flag_presets.write_xml(filepath)
        handle_load_flag_presets(self)

        return True


class SOLLUMZ_OT_load_flag_preset(SOLLUMZ_OT_base, bpy.types.Operator):
    """Load a flag preset to the selected Geometry bounds"""
    bl_idname = "sollumz.load_flag_preset"
    bl_label = "Apply Flags Preset"
    bl_context = 'object'
    bl_options = {'REGISTER', 'UNDO'}
    bl_action = f"{bl_label}"

    def run(self, context):
        index = context.scene.flag_preset_index
        selected = context.selected_objects
        if len(selected) < 1:
            self.message("No objects selected!")
            return False

        handle_load_flag_presets(self)

        for obj in selected:
            if obj.sollum_type and not (obj.sollum_type == SollumType.BOUND_GEOMETRY or obj.sollum_type == SollumType.BOUND_GEOMETRYBVH):
                self.message(
                    f"Object: {obj.name} will be skipped because it is not a {SOLLUMZ_UI_NAMES[SollumType.BOUND_GEOMETRY]} or {SOLLUMZ_UI_NAMES[SollumType.BOUND_GEOMETRYBVH]}!")

            try:
                preset = flag_presets.presets[index]

                for flag_name in BoundFlags.__annotations__.keys():
                    if flag_name in preset.flags1:
                        obj.composite_flags1[flag_name] = True
                    else:
                        obj.composite_flags1[flag_name] = False

                    if flag_name in preset.flags2:
                        obj.composite_flags2[flag_name] = True
                    else:
                        obj.composite_flags2[flag_name] = False

                # Hacky way to force the UI to redraw. For some reason setting custom properties will not cause the object properties panel to redraw, so we have to do this.
                obj.location = obj.location
                self.message(
                    f"Applied preset '{preset.name}' to: {obj.name}")
            except IndexError:
                filepath = get_flag_presets_path()
                self.error(
                    f"Flag preset does not exist! Ensure the preset file is present in the '{filepath}' directory.")
                return False

        return True


class SOLLUMZ_OT_clear_col_flags(SOLLUMZ_OT_base, bpy.types.Operator):
    """Load commonly used collision flags"""
    bl_idname = "sollumz.clear_col_flags"
    bl_label = "Clear Collision Flags"
    bl_action = f"{bl_label}"

    def run(self, context):

        aobj = context.active_object
        if(aobj == None):
            self.message("Please select an object.")
            return False

        if aobj.sollum_type in BOUND_TYPES:
            for flag_name in BoundFlags.__annotations__.keys():
                aobj.composite_flags1[flag_name] = False
                aobj.composite_flags2[flag_name] = False

        return True
