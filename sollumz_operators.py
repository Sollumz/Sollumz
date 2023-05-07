import traceback
import os
import pathlib
import bpy
from bpy_extras.io_utils import ImportHelper
from .sollumz_helper import SOLLUMZ_OT_base
from .sollumz_properties import SollumType, SOLLUMZ_UI_NAMES, BOUND_TYPES, SollumzExportSettings, SollumzImportSettings, TimeFlags, ArchetypeType
from .cwxml.drawable import YDR, YDD
from .cwxml.fragment import YFT
from .cwxml.bound import YBN
from .cwxml.navmesh import YNV
from .cwxml.clipsdictionary import YCD
from .cwxml.ytyp import YTYP
from .cwxml.ymap import YMAP
from .ydr.ydrimport import import_ydr
from .ydr.ydrexport import export_ydr
from .ydd.yddimport import import_ydd
from .ydd.yddexport import export_ydd
from .yft.yftimport import import_yft
from .yft.yftexport import export_yft
from .ybn.ybnimport import import_ybn
from .ybn.ybnexport import export_ybn
from .ynv.ynvimport import import_ynv
from .ycd.ycdimport import import_ycd
from .ycd.ycdexport import export_ycd
from .ymap.ymapimport import import_ymap
from .ymap.ymapexport import export_ymap
from .tools.blenderhelper import get_terrain_texture_brush, remove_number_suffix
from .tools.ytyphelper import ytyp_from_objects


class SOLLUMZ_OT_import(SOLLUMZ_OT_base, bpy.types.Operator, ImportHelper):
    """Imports xml files exported by codewalker"""
    bl_idname = "sollumz.import"
    bl_label = "Import Codewalker XML"
    bl_action = "import"
    bl_showtime = True
    bl_update_view = True

    files: bpy.props.CollectionProperty(
        name="File Path",
        type=bpy.types.OperatorFileListElement,
    )

    filter_glob: bpy.props.StringProperty(
        default=f"*{YDR.file_extension};*{YDD.file_extension};*{YFT.file_extension};*{YBN.file_extension};*{YNV.file_extension};*{YCD.file_extension};*{YMAP.file_extension};",
        options={"HIDDEN"},
        maxlen=255,
    )

    import_settings: bpy.props.PointerProperty(type=SollumzImportSettings)

    filename_exts = [YDR.file_extension, YDD.file_extension,
                     YFT.file_extension, YBN.file_extension,
                     YNV.file_extension, YCD.file_extension,
                     YMAP.file_extension]

    def draw(self, context):
        pass

    def import_file(self, filepath, ext):
        try:
            valid_type = False
            if ext == YDR.file_extension:
                import_ydr(filepath, self.import_settings)
                valid_type = True
            elif ext == YDD.file_extension:
                import_ydd(self, filepath, self.import_settings)
                valid_type = True
            elif ext == YFT.file_extension:
                import_yft(filepath, self)
                valid_type = True
            elif ext == YBN.file_extension:
                import_ybn(filepath)
                valid_type = True
            elif ext == YNV.file_extension:
                import_ynv(filepath)
            elif ext == YCD.file_extension:
                import_ycd(self, filepath, self.import_settings)
            elif ext == YMAP.file_extension:
                import_ymap(self, filepath, self.import_settings)
                valid_type = True
            if valid_type:
                self.message(f"Succesfully imported: {filepath}")
        except:
            self.error(
                f"Error importing: {filepath} \n {traceback.format_exc()}")
            return False

        return True

    def run(self, context):
        result = False
        if self.import_settings.batch_mode == "DIRECTORY":
            folderpath = os.path.dirname(self.filepath)
            for file in os.listdir(folderpath):
                ext = "".join(pathlib.Path(file).suffixes)
                if ext in self.filename_exts:
                    filepath = os.path.join(folderpath, file)
                    result = self.import_file(filepath, ext)
        else:
            for file_elem in self.files:
                directory = os.path.dirname(self.filepath)
                filepath = os.path.join(directory, file_elem.name)
                if os.path.isfile(filepath):
                    ext = "".join(pathlib.Path(filepath).suffixes)
                    result = self.import_file(filepath, ext)

        if not result:
            self.bl_showtime = False

        return True


class SOLLUMZ_OT_export(SOLLUMZ_OT_base, bpy.types.Operator):
    """Exports codewalker xml files"""
    bl_idname = "sollumz.export"
    bl_label = "Export Codewalker XML"
    bl_action = "export"
    bl_showtime = True

    export_settings: bpy.props.PointerProperty(type=SollumzExportSettings)

    filter_glob: bpy.props.StringProperty(
        default=f"*{YDR.file_extension};*{YDD.file_extension};*{YFT.file_extension};*{YBN.file_extension};*{YCD.file_extension};*{YMAP.file_extension};",
        options={"HIDDEN"},
        maxlen=255,
    )

    directory: bpy.props.StringProperty(
        name="Output directory",
        description="Select export output directory",
        subtype="DIR_PATH",
    )

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def draw(self, context):
        pass

    def get_data_name(self, obj_name):
        mode = self.export_settings.batch_mode
        if mode == "COLLECTION":
            for col in bpy.data.collections:
                for obj in col.objects:
                    if obj.name == obj_name:
                        return col.name
        elif mode in {"SCENE_COLLECTION", "ACTIVE_SCENE_COLLECTION"}:
            scenes = [
                bpy.context.scene] if mode == "ACTIVE_SCENE_COLLECTION" else bpy.data.scenes
            for scene in scenes:
                if not scene.objects:
                    self.error(f"No objects in scene {scene.name} to export.")
                for obj in scene.collection.objects:
                    if obj.name == obj_name:
                        return f"{scene.name}_{scene.collection.name}"
        else:
            for scene in bpy.data.scenes:
                if not scene.objects:
                    self.error(f"No objects in scene {scene.name} to export.")
                for obj in scene.objects:
                    if obj.name == obj_name:
                        return scene.name
        return ""

    def make_directory(self, name):
        dir = os.path.join(self.directory, self.get_data_name(
            name) if self.export_settings.batch_mode != "OFF" else name)
        if not os.path.exists(dir):
            os.mkdir(dir)
        return dir

    def get_filepath(self, name, ext):
        return os.path.join(self.make_directory(name), name + ext) if self.export_settings.use_batch_own_dir else os.path.join(self.directory, name + ext)

    def get_only_parent_objs(self, objs):
        pobjs = []
        for obj in objs:
            if obj.parent is None:
                pobjs.append(obj)
        return pobjs

    def collect_objects(self, context):
        mode = self.export_settings.batch_mode
        objects = []
        if mode == "OFF":
            if self.export_settings.use_active_collection:
                if self.export_settings.use_selection:
                    objects = [
                        obj for obj in context.view_layer.active_layer_collection.collection.all_objects if obj.select_get()]
                else:
                    objects = context.view_layer.active_layer_collection.collection.all_objects
            else:
                if self.export_settings.use_selection:
                    objects = context.selected_objects
                else:
                    objects = context.view_layer.objects
        else:
            if mode == "COLLECTION":
                data_block = tuple(
                    (coll, coll.name, "objects") for coll in bpy.data.collections if coll.objects)
            elif mode in {"SCENE_COLLECTION", "ACTIVE_SCENE_COLLECTION"}:
                scenes = [
                    context.scene] if mode == "ACTIVE_SCENE_COLLECTION" else bpy.data.scenes
                data_block = []
                for scene in scenes:
                    if not scene.objects:
                        continue
                    todo_collections = [(scene.collection, "_".join(
                        (scene.name, scene.collection.name)))]
                    while todo_collections:
                        coll, coll_name = todo_collections.pop()
                        todo_collections.extend(
                            ((c, c.name) for c in coll.children if c.all_objects))
                        data_block.append((coll, coll_name, "all_objects"))
            else:
                data_block = tuple((scene, scene.name, "objects")
                                   for scene in bpy.data.scenes if scene.objects)

            # this is how you can create the folder names if the user clicks "use_batch_own_dir"
            for data, _, data_obj_paramname in data_block:
                objects = getattr(
                    data, data_obj_paramname).values()

        result = []

        types = self.export_settings.sollum_types
        for obj in objects:
            if obj.sollum_type in BOUND_TYPES:
                # this is to make sure we get all bound objects without having to specify its specific type
                if any(bound_type.value in types for bound_type in BOUND_TYPES):
                    result.append(obj)
            else:
                if obj.sollum_type in types:
                    result.append(obj)

        return result

    def export_object(self, obj):
        try:
            valid_type = False
            filepath = None
            if obj.sollum_type == SollumType.DRAWABLE:
                filepath = self.get_filepath(
                    remove_number_suffix(obj.name.lower()), YDR.file_extension)
                export_ydr(self, obj, filepath)
                valid_type = True
            elif obj.sollum_type == SollumType.DRAWABLE_DICTIONARY:
                filepath = self.get_filepath(
                    remove_number_suffix(obj.name.lower()), YDD.file_extension)
                export_ydd(self, obj, filepath, self.export_settings)
                valid_type = True
            elif obj.sollum_type == SollumType.FRAGMENT:
                filepath = self.get_filepath(
                    remove_number_suffix(obj.name.lower()), YFT.file_extension)
                export_yft(self, obj, filepath, self.export_settings)
                valid_type = True
            elif obj.sollum_type == SollumType.CLIP_DICTIONARY:
                filepath = self.get_filepath(
                    remove_number_suffix(obj.name.lower()), YCD.file_extension)
                export_ycd(self, obj, filepath, self.export_settings)
                valid_type = True
            elif obj.sollum_type in BOUND_TYPES:
                filepath = self.get_filepath(
                    remove_number_suffix(obj.name.lower()), YBN.file_extension)
                export_ybn(obj, filepath)
                valid_type = True
            elif obj.sollum_type == SollumType.YMAP:
                filepath = self.get_filepath(
                    remove_number_suffix(obj.name.lower()), YMAP.file_extension)
                export_ymap(self, obj, filepath, self.export_settings)
                valid_type = True
            if valid_type:
                self.message(f"Succesfully exported: {filepath}")
        except:
            self.error(
                f"Error exporting: {filepath} \n {traceback.format_exc()}")
            return False
        return True

    def run(self, context):
        objects = self.get_only_parent_objs(self.collect_objects(context))

        if len(objects) == 0:
            self.warning(
                f"No objects of type: {' or '.join([SOLLUMZ_UI_NAMES[t].lower() for t in self.export_settings.sollum_types])} to export.")
            return False

        mode = "OBJECT"
        if context.active_object:
            mode = context.active_object.mode
            if mode != "OBJECT":
                bpy.ops.object.mode_set(mode="OBJECT")

        if len(objects) > 0:
            for obj in objects:
                result = self.export_object(obj)
                # Dont show time on failure
                if not result:
                    self.bl_showtime = False

            if self.export_settings.export_with_ytyp:
                ytyp = ytyp_from_objects(objects)
                fp = self.get_filepath(
                    ytyp.name, YTYP.file_extension)
                ytyp.write_xml(fp)

        if context.active_object:
            if context.active_object.mode != mode:
                bpy.ops.object.mode_set(mode=mode)

        return True


class SOLLUMZ_OT_paint_vertices(SOLLUMZ_OT_base, bpy.types.Operator):
    """Paint All Vertices Of Selected Object"""
    bl_idname = "sollumz.paint_vertices"
    bl_label = "Paint"
    bl_action = "Paint Vertices"

    color: bpy.props.FloatVectorProperty(
        subtype="COLOR_GAMMA",
        default=(1.0, 1.0, 1.0, 1.0),
        min=0,
        max=1,
        size=4
    )

    def paint_map(self, color_attr, color):
        for datum in color_attr.data:
            # Uses color_srgb to match the behavior of the old
            # vertex_colors code. Requires 3.4+.
            datum.color_srgb = color

    def paint_mesh(self, mesh, color):
        if not mesh.color_attributes:
            mesh.color_attributes.new("Color", 'BYTE_COLOR', 'CORNER')
        self.paint_map(mesh.attributes.active_color, color)

    def run(self, context):
        objs = context.selected_objects

        if len(objs) > 0:
            for obj in objs:
                if obj.sollum_type == SollumType.DRAWABLE_GEOMETRY:
                    self.paint_mesh(obj.data, self.color)
                    self.messages.append(
                        f"{obj.name} was successfully painted.")
                else:
                    self.messages.append(
                        f"{obj.name} will be skipped because it is not a {SOLLUMZ_UI_NAMES[SollumType.DRAWABLE_GEOMETRY]} type.")
        else:
            self.message("No objects selected to paint.")
            return False

        return True


class SOLLUMZ_OT_paint_terrain_tex1(SOLLUMZ_OT_base, bpy.types.Operator):
    """Paint Texture 1 On Selected Object"""
    bl_idname = "sollumz.paint_tex1"
    bl_label = "Paint Texture 1"

    def run(self, context):
        get_terrain_texture_brush(1)
        return True


class SOLLUMZ_OT_paint_terrain_tex2(SOLLUMZ_OT_base, bpy.types.Operator):
    """Paint Texture 2 On Selected Object"""
    bl_idname = "sollumz.paint_tex2"
    bl_label = "Paint Texture 2"

    def run(self, context):
        get_terrain_texture_brush(2)
        return True


class SOLLUMZ_OT_paint_terrain_tex3(SOLLUMZ_OT_base, bpy.types.Operator):
    """Paint Texture 3 On Selected Object"""
    bl_idname = "sollumz.paint_tex3"
    bl_label = "Paint Texture 3"

    def run(self, context):
        get_terrain_texture_brush(3)
        return True


class SOLLUMZ_OT_paint_terrain_tex4(SOLLUMZ_OT_base, bpy.types.Operator):
    """Paint Texture 4 On Selected Object"""
    bl_idname = "sollumz.paint_tex4"
    bl_label = "Paint Texture 4"

    def run(self, context):
        get_terrain_texture_brush(4)
        return True


class SOLLUMZ_OT_paint_terrain_alpha(SOLLUMZ_OT_base, bpy.types.Operator):
    """Paint Lookup Sampler Alpha On Selected Object"""
    bl_idname = "sollumz.paint_a"
    bl_label = "Paint Alpha"

    def run(self, context):
        get_terrain_texture_brush(5)
        return True


class SelectTimeFlagsRange(SOLLUMZ_OT_base):
    """Select range of time flags"""
    bl_label = "Select"

    def get_flags(self, context):
        return None

    def run(self, context):
        flags = self.get_flags(context)
        if not flags:
            return False
        start = int(flags.time_flags_start)
        end = int(flags.time_flags_end)
        index = 0
        for prop in TimeFlags.__annotations__:
            if index < 24:
                if start < end:
                    if index >= start and index < end:
                        flags[prop] = True
                elif start > end:
                    if index < end or index >= start:
                        flags[prop] = True
                elif start == 0 and end == 0:
                    flags[prop] = True
            index += 1
        flags.update_flag(context)
        return True


class ClearTimeFlags(SOLLUMZ_OT_base):
    """Clear all time flags"""
    bl_label = "Clear Selection"

    def get_flags(self, context):
        return None

    def run(self, context):
        flags = self.get_flags(context)
        if not flags:
            return False
        for prop in TimeFlags.__annotations__:
            flags[prop] = False
        flags.update_flag(context)
        return True


def sollumz_menu_func_import(self, context):
    self.layout.operator(SOLLUMZ_OT_import.bl_idname,
                         text=f"Codewalker XML({YDR.file_extension}, {YDD.file_extension}, {YFT.file_extension}, {YBN.file_extension}, {YCD.file_extension})")


def sollumz_menu_func_export(self, context):
    self.layout.operator(SOLLUMZ_OT_export.bl_idname,
                         text=f"Codewalker XML({YDR.file_extension}, {YDD.file_extension}, {YFT.file_extension}, {YBN.file_extension}, {YCD.file_extension})")


class SOLLUMZ_OT_debug_hierarchy(SOLLUMZ_OT_base, bpy.types.Operator):
    """Debug: Fix incorrect Sollum Type after update. Must set correct type for top-level object first."""
    bl_idname = "sollumz.debug_hierarchy"
    bl_label = "Fix Hierarchy"
    bl_action = bl_label
    bl_order = 100

    def run(self, context):
        sollum_type = context.scene.debug_sollum_type
        for obj in context.selected_objects:
            if len(obj.children) < 1:
                self.message(f"{obj.name} has no children! Skipping...")
                continue

            obj.sollum_type = sollum_type
            if sollum_type == SollumType.DRAWABLE:
                for model in obj.children:
                    if model.type == "EMPTY":
                        model.sollum_type = SollumType.DRAWABLE_MODEL
                        for geom in model.children:
                            if geom.type == "MESH":
                                geom.sollum_type = SollumType.DRAWABLE_GEOMETRY
            elif sollum_type == SollumType.DRAWABLE_DICTIONARY:
                for draw in obj.children:
                    if draw.type == "EMPTY":
                        draw.sollum_type = SollumType.DRAWABLE
                        for model in draw.children:
                            if model.type == "EMPTY":
                                model.sollum_type = SollumType.DRAWABLE_MODEL
                                for geom in model.children:
                                    if geom.type == "MESH":
                                        geom.sollum_type = SollumType.DRAWABLE_GEOMETRY
            elif sollum_type == SollumType.BOUND_COMPOSITE:
                for bound in obj.children:
                    if bound.type == "EMPTY":
                        if "CLOTH" in bound.name:
                            bound.sollum_type = SollumType.BOUND_CLOTH
                            continue

                        if "BVH" in bound.name:
                            bound.sollum_type = SollumType.BOUND_GEOMETRYBVH
                        else:
                            bound.sollum_type = SollumType.BOUND_GEOMETRY
                        for geom in bound.children:
                            if geom.type == "MESH":
                                if "Box" in geom.name:
                                    geom.sollum_type = SollumType.BOUND_POLY_BOX
                                elif "Sphere" in geom.name:
                                    geom.sollum_type = SollumType.BOUND_POLY_SPHERE
                                elif "Capsule" in geom.name:
                                    geom.sollum_type = SollumType.BOUND_POLY_CAPSULE
                                elif "Cylinder" in geom.name:
                                    geom.sollum_type = SollumType.BOUND_POLY_CYLINDER
                                else:
                                    geom.sollum_type = SollumType.BOUND_POLY_TRIANGLE
                    if bound.type == "MESH":
                        if "Box" in bound.name:
                            bound.sollum_type = SollumType.BOUND_POLY_BOX
                        elif "Sphere" in bound.name:
                            bound.sollum_type = SollumType.BOUND_POLY_SPHERE
                        elif "Capsule" in bound.name:
                            bound.sollum_type = SollumType.BOUND_POLY_CAPSULE
                        elif "Cylinder" in bound.name:
                            bound.sollum_type = SollumType.BOUND_POLY_CYLINDER
                        else:
                            bound.sollum_type = SollumType.BOUND_POLY_TRIANGLE
        self.message("Hierarchy successfuly set.")
        return True


class SOLLUMZ_OT_debug_set_sollum_type(SOLLUMZ_OT_base, bpy.types.Operator):
    """Debug: Set Sollum Type"""
    bl_idname = "sollumz.debug_set_sollum_type"
    bl_label = "Set Sollum Type"
    bl_action = bl_label
    bl_order = 100

    def run(self, context):
        sel_sollum_type = context.scene.all_sollum_type
        for obj in context.selected_objects:
            obj.sollum_type = sel_sollum_type
        self.message(
            f"Sollum Type successfuly set to {SOLLUMZ_UI_NAMES[sel_sollum_type]}.")
        return True


class SOLLUMZ_OT_debug_fix_light_intensity(bpy.types.Operator):
    bl_idname = "sollumz.debug_fix_light_intensity"
    bl_label = "Re-adjust Light Intensity"
    bl_description = "Multiply light intensity by a factor of 500 to make older projects compatible with the light intensity change"
    bl_options = {"UNDO"}

    def execute(self, context):
        only_selected = context.scene.debug_lights_only_selected

        objects = context.selected_objects if only_selected else context.scene.objects
        light_objs = [obj for obj in objects if obj.type ==
                      "LIGHT" and obj.sollum_type == SollumType.LIGHT]

        if not light_objs:
            self.report(
                {"INFO"}, "No Sollumz lights selected" if only_selected else "No Sollumz lights in the scene.")
            return {"CANCELLED"}

        lights: list[bpy.types.Light] = []
        for light_obj in light_objs:
            if light_obj.data not in lights:
                lights.append(light_obj.data)

        for light in lights:
            light.energy = light.energy * 500

        return {"FINISHED"}


class SOLLUMZ_OT_debug_reload_entity_sets(bpy.types.Operator):
    bl_idname = "sollumz.debug_reload_entity_sets"
    bl_label = "Reload Entity Sets"
    bl_description = "Reload old entity set entities."
    bl_options = {"UNDO"}

    def execute(self, context):
        for ytyp in context.scene.ytyps:
            for archetype in ytyp.archetypes:
                if archetype.type != ArchetypeType.MLO:
                    continue

                for entity_set in archetype.entity_sets:
                    for entity in entity_set.entities:
                        new_entity = archetype.new_entity()
                        for k, v in entity.items():
                            new_entity[k] = v

                        new_entity.attached_entity_set_id = str(entity_set.id)

        return {"FINISHED"}


class SearchEnumHelper:
    """Helper class for searching and setting enums"""
    bl_label = "Search"

    def get_data_block(self, context):
        """Get the data-block containing the enum property"""
        ...

    def execute(self, context):
        data_block = self.get_data_block(context)
        prop_name = getattr(self, "bl_property")
        enum_value = getattr(self, prop_name)

        setattr(data_block, prop_name, enum_value)

        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.invoke_search_popup(self)

        return {'FINISHED'}


def register():
    bpy.types.TOPBAR_MT_file_import.append(sollumz_menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(sollumz_menu_func_export)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(sollumz_menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(sollumz_menu_func_export)
