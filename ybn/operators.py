from abc import abstractmethod
from math import degrees
from ..tools.obb import get_obb, get_obb_extents
import traceback
from ..resources.flag_preset import FlagPreset
from ..ybn.properties import BoundFlags, load_flag_presets, flag_presets, get_flag_presets_path
from ..ybn.collision_materials import create_collision_material_from_index
from ..tools.boundhelper import *
from ..tools.meshhelper import *
from ..sollumz_properties import BoundType, PolygonType, SOLLUMZ_UI_NAMES
from ..sollumz_helper import SOLLUMZ_OT_base, is_sollum_type
from ..tools.blenderhelper import get_selected_vertices
from ..sollumz_properties import BoundType, PolygonType, SOLLUMZ_UI_NAMES
from ..sollumz_helper import *
import bpy


def handle_load_flag_presets(self):
    try:
        load_flag_presets()
    except FileNotFoundError:
        self.report({'ERROR'}, traceback.format_exc())


class CreatePolyHelper(SOLLUMZ_OT_base):
    @property
    @abstractmethod
    def poly_type():
        raise NotImplementedError

    def run(self, context):
        obj = create_bound_shape(self.poly_type)
        context.view_layer.objects.active = bpy.data.objects[obj.name]
        return True


class SOLLUMZ_OT_create_poly_box(CreatePolyHelper, bpy.types.Operator):
    bl_label = SOLLUMZ_UI_NAMES[PolygonType.BOX]
    bl_idname = "sollumz.createpolybox"
    poly_type = PolygonType.BOX


class SOLLUMZ_OT_create_poly_sphere(CreatePolyHelper, bpy.types.Operator):
    bl_label = SOLLUMZ_UI_NAMES[PolygonType.SPHERE]
    bl_idname = "sollumz.createpolysphere"
    poly_type = PolygonType.SPHERE


class SOLLUMZ_OT_create_poly_cylinder(CreatePolyHelper, bpy.types.Operator):
    bl_label = SOLLUMZ_UI_NAMES[PolygonType.CYLINDER]
    bl_idname = "sollumz.createpolycylinder"
    poly_type = PolygonType.CYLINDER


class SOLLUMZ_OT_create_poly_capsule(CreatePolyHelper, bpy.types.Operator):
    bl_label = SOLLUMZ_UI_NAMES[PolygonType.CAPSULE]
    bl_idname = "sollumz.createpolycapsule"
    poly_type = PolygonType.CAPSULE


class SOLLUMZ_OT_create_poly_mesh(CreatePolyHelper, bpy.types.Operator):
    bl_label = SOLLUMZ_UI_NAMES[PolygonType.TRIANGLE]
    bl_idname = "sollumz.createpolymesh"
    poly_type = PolygonType.TRIANGLE


class SOLLUMZ_OT_create_bound_composite(SOLLUMZ_OT_base, bpy.types.Operator):
    """Create a sollumz bound composite"""
    bl_idname = "sollumz.createboundcomposite"
    bl_label = f"Create {SOLLUMZ_UI_NAMES[BoundType.COMPOSITE]}"
    bl_action = f"Create a {SOLLUMZ_UI_NAMES[BoundType.COMPOSITE]}"

    def run(self, context):
        selected = context.selected_objects
        if len(selected) < 1:
            create_bound(BoundType.COMPOSITE)

            return True
        else:
            create_composite_from_selection(
                selected, context.scene.use_mesh_name, context.scene.create_seperate_objects, context.scene.composite_create_bvh)
            return True


class SOLLUMZ_OT_convert_to_poly_mesh(SOLLUMZ_OT_base, bpy.types.Operator):
    """Convert object to a poly mesh"""
    bl_idname = "sollumz.converttopolymesh"
    bl_label = f"Convert to {SOLLUMZ_UI_NAMES[PolygonType.TRIANGLE]}"
    bl_action = bl_label

    def run(self, context):
        selected = context.selected_objects
        if len(selected) < 1:
            self.message("No objects selected.")
            return False

        for obj in selected:
            obj.sollum_type = PolygonType.TRIANGLE
            self.message(
                f"Converted '{obj.name}' to a {SOLLUMZ_UI_NAMES[PolygonType.TRIANGLE]}.")
            return True


class CreateBoundHelper(SOLLUMZ_OT_base):
    @property
    @abstractmethod
    def bound_type():
        raise NotImplementedError

    def run(self, context):
        obj = None
        if self.bound_type == BoundType.GEOMETRY or self.bound_type == BoundType.GEOMETRYBVH:
            obj = create_bound(self.bound_type)
        else:
            obj = create_mesh(self.bound_type)
        if obj:
            context.view_layer.objects.active = bpy.data.objects[obj.name]
        return True


class CreateBoundShapeHelper(SOLLUMZ_OT_base):
    @property
    @abstractmethod
    def bound_type():
        raise NotImplementedError

    def run(self, context):
        obj = create_bound_shape(self.bound_type)
        context.view_layer.objects.active = bpy.data.objects[obj.name]
        return True


class SOLLUMZ_OT_create_geometry_bound(CreateBoundHelper, bpy.types.Operator):
    """Create a sollumz geometry bound"""
    bl_idname = "sollumz.creategeometrybound"
    bl_label = f"Create {SOLLUMZ_UI_NAMES[BoundType.GEOMETRY]}"
    bound_type = BoundType.GEOMETRY


class SOLLUMZ_OT_create_geometrybvh_bound(CreateBoundHelper, bpy.types.Operator):
    """Create a sollumz geometry bound bvh"""
    bl_idname = "sollumz.creategeometryboundbvh"
    bl_label = f"Create {SOLLUMZ_UI_NAMES[BoundType.GEOMETRYBVH]}"
    bound_type = BoundType.GEOMETRYBVH


class SOLLUMZ_OT_create_cloth_bound(CreateBoundHelper, bpy.types.Operator):
    """Create a sollumz cloth bound"""
    bl_idname = "sollumz.createclothbound"
    bl_label = f"Create {SOLLUMZ_UI_NAMES[BoundType.CLOTH]}"
    bound_type = BoundType.CLOTH


class SOLLUMZ_OT_create_box_bound(CreateBoundShapeHelper, bpy.types.Operator):
    """Create a sollumz box bound"""
    bl_idname = "sollumz.createboxbound"
    bl_label = f"Create {SOLLUMZ_UI_NAMES[BoundType.BOX]}"
    bound_type = BoundType.BOX


class SOLLUMZ_OT_create_sphere_bound(CreateBoundShapeHelper, bpy.types.Operator):
    """Create a sollumz sphere bound"""
    bl_idname = "sollumz.createspherebound"
    bl_label = f"Create {SOLLUMZ_UI_NAMES[BoundType.SPHERE]}"
    bound_type = BoundType.SPHERE


class SOLLUMZ_OT_create_capsule_bound(CreateBoundShapeHelper, bpy.types.Operator):
    """Create a sollumz capsule bound"""
    bl_idname = "sollumz.createcapsulebound"
    bl_label = f"Create {SOLLUMZ_UI_NAMES[BoundType.CAPSULE]}"
    bound_type = BoundType.CAPSULE


class SOLLUMZ_OT_create_cylinder_bound(CreateBoundShapeHelper, bpy.types.Operator):
    """Create a sollumz cylinder bound"""
    bl_idname = "sollumz.createcylinderbound"
    bl_label = f"Create {SOLLUMZ_UI_NAMES[BoundType.CYLINDER]}"
    bound_type = BoundType.CYLINDER


class SOLLUMZ_OT_create_disc_bound(CreateBoundShapeHelper, bpy.types.Operator):
    """Create a sollumz disc bound"""
    bl_idname = "sollumz.creatediscbound"
    bl_label = f"Create {SOLLUMZ_UI_NAMES[BoundType.DISC]}"
    bound_type = BoundType.DISC


class SOLLUMZ_OT_create_polygon_bound(SOLLUMZ_OT_base, bpy.types.Operator):
    """Create a sollumz polygon bound"""
    bl_idname = "sollumz.createpolygonbound"
    bl_label = "Create Polygon Bound"
    bl_action = f"{bl_label}"

    # @classmethod
    # def poll(cls, context):
    #     return context.active_object != None

    def create_poly_from_verts(self, context, type, parent):
        if not parent:
            self.message("Must specify a parent object!")
            return False
        elif parent.sollum_type != BoundType.GEOMETRYBVH and parent.sollum_type != BoundType.GEOMETRY:
            self.message(
                f'Parent must be a {SOLLUMZ_UI_NAMES[BoundType.GEOMETRYBVH]} or {SOLLUMZ_UI_NAMES[BoundType.GEOMETRY]}!')
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

        if type != PolygonType.TRIANGLE:
            pobj = create_bound_shape(
                type) if type != PolygonType.BOX else create_mesh(type)

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

            if type == PolygonType.BOX:
                create_box_from_extents(
                    pobj.data, bbmin - local_center, bbmax - local_center)
            # elif type == PolygonType.SPHERE:
            #     pobj.bound_radius = (bbmax - bbmin).magnitude / 2
            # elif type == PolygonType.CAPSULE or type == PolygonType.CYLINDER:
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
        type = context.scene.poly_bound_type
        parent = context.scene.poly_parent

        if aobj and aobj.mode == "EDIT":
            return self.create_poly_from_verts(context, type, parent)
        else:
            create_bound_shape(type)
            return True


class SOLLUMZ_OT_center_composite(SOLLUMZ_OT_base, bpy.types.Operator):
    """Center a bound composite with the rest of it's geometry. Note: Has no effect on export"""
    bl_idname = "sollumz.centercomposite"
    bl_label = "Center Composite"
    bl_action = f"{bl_label}"

    def run(self, context):
        aobj = context.active_object
        if not aobj:
            self.message(
                f"No {SOLLUMZ_UI_NAMES[BoundType.COMPOSITE]} selected.")
            return False
        if aobj.sollum_type != BoundType.COMPOSITE:
            self.message(
                f"{aobj.name} must be a {SOLLUMZ_UI_NAMES[BoundType.COMPOSITE]}!")
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

        if obj.sollum_type and not (obj.sollum_type == BoundType.GEOMETRY or obj.sollum_type == BoundType.GEOMETRYBVH):
            self.message(
                f"Selected object must be either a {SOLLUMZ_UI_NAMES[BoundType.GEOMETRY]} or {SOLLUMZ_UI_NAMES[BoundType.GEOMETRYBVH]}!")
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
            if obj.sollum_type and not (obj.sollum_type == BoundType.GEOMETRY or obj.sollum_type == BoundType.GEOMETRYBVH):
                self.message(
                    f"Object: {obj.name} will be skipped because it is not a {SOLLUMZ_UI_NAMES[BoundType.GEOMETRY]} or {SOLLUMZ_UI_NAMES[BoundType.GEOMETRYBVH]}!")

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

        if is_sollum_type(aobj, BoundType):
            for flag_name in BoundFlags.__annotations__.keys():
                aobj.composite_flags1[flag_name] = False
                aobj.composite_flags2[flag_name] = False

        return True
