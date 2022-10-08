import os
import traceback
import bpy
from mathutils import Vector
from cwxml.ymap import YMAP, CMapData, EntityItem
from bpy_extras.io_utils import ImportHelper
from sollumz_helper import SOLLUMZ_OT_base
from sollumz_properties import SollumType
from tools.blenderhelper import remove_number_suffix
from tools.meshhelper import get_bound_extents
from tools.utils import add_to_vector, get_max_vector, get_min_vector, subtract_from_vector

class SOLLUMZ_OT_import_ymap(SOLLUMZ_OT_base, bpy.types.Operator, ImportHelper):
    """Imports .ymap.xml file exported from codewalker"""
    bl_idname = "sollumz.importymap"
    bl_label = "Import ymap.xml"
    filename_ext = ".ymap.xml"
    bl_action = "Import a YMAP"
    bl_showtime = True
    bl_update_view = True

    filter_glob: bpy.props.StringProperty(
        default="*.ymap.xml",
        options={"HIDDEN"},
        maxlen=255,
    )

    def apply_entity_properties(self, obj, entity):
        obj.entity_properties.archetype_name = entity.archetype_name
        obj.entity_properties.flags = entity.flags
        obj.entity_properties.guid = entity.guid
        obj.entity_properties.parent_index = entity.parent_index
        obj.entity_properties.lod_dist = entity.lod_dist
        obj.entity_properties.child_lod_dist = entity.child_lod_dist
        obj.entity_properties.lod_level = "sollumz_" + entity.lod_level.lower()
        obj.entity_properties.num_children = entity.num_children
        obj.entity_properties.priority_level = "sollumz_" + entity.priority_level.lower()
        obj.entity_properties.ambient_occlusion_multiplier = entity.ambient_occlusion_multiplier
        obj.entity_properties.artificial_ambient_occlusion = entity.artificial_ambient_occlusion
        obj.entity_properties.tint_value = entity.tint_value

        if entity.type != "CMloInstanceDef":
            # Entities in YMAPs need rotation inverted
            entity.rotation.invert()
        obj.matrix_world = entity.rotation.to_matrix().to_4x4()
        obj.location = entity.position
        obj.scale = Vector(
            (entity.scale_xy, entity.scale_xy, entity.scale_z))

    def run(self, context):

        try:
            ymap = YMAP.from_xml_file(self.filepath)
            found = False
            if ymap.entities:
                for obj in context.collection.all_objects:
                    for entity in ymap.entities:
                        if entity.archetype_name == obj.name and obj.name in context.view_layer.objects:
                            found = True
                            self.apply_entity_properties(obj, entity)
                if found:
                    self.message(f"Succesfully imported: {self.filepath}")
                    return True
                else:
                    self.message(
                        f"No entities from '{self.filepath}' exist in the view layer!")
                    return False
            else:
                self.error(f"{self.filepath} contains no entities to import!")
                return False
        except:
            self.error(f"Error during import: {traceback.format_exc()}")
            return False

class SOLLUMZ_OT_export_ymap(SOLLUMZ_OT_base, bpy.types.Operator):
    """Exports .ymap.xml file exported from codewalker"""
    bl_idname = "sollumz.exportymap"
    bl_label = "Export ymap.xml"
    bl_action = "Export a YMAP"
    bl_showtime = True

    filter_glob: bpy.props.StringProperty(
        default="*.ymap.xml",
        options={"HIDDEN"},
        maxlen=255,
    )

    directory: bpy.props.StringProperty(
        name="Output directory",
        description="Select export output directory",
        subtype="DIR_PATH",
    )

    def get_filepath(self, name):
        return os.path.join(self.directory, name + ".ymap.xml")

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def entity_from_obj(self, obj):
        entity = EntityItem()

        entity.archetype_name = remove_number_suffix(obj.name.lower())
        entity.flags = int(obj.entity_properties.flags)
        entity.guid = int(obj.entity_properties.guid)
        entity.position = obj.location
        entity.rotation = obj.rotation_euler.to_quaternion()
        entity.scale_xy = obj.scale.x
        entity.scale_z = obj.scale.z
        entity.parent_index = int(obj.entity_properties.parent_index)
        entity.lod_dist = obj.entity_properties.lod_dist
        entity.child_lod_dist = obj.entity_properties.child_lod_dist
        entity.lod_level = obj.entity_properties.lod_level.upper().replace("SOLLUMZ_", "")
        entity.num_children = int(obj.entity_properties.num_children)
        entity.priority_level = obj.entity_properties.priority_level.upper().replace("SOLLUMZ_", "")
        entity.ambient_occlusion_multiplier = int(
            obj.entity_properties.ambient_occlusion_multiplier)
        entity.artificial_ambient_occlusion = int(
            obj.entity_properties.artificial_ambient_occlusion)
        entity.tint_value = int(obj.entity_properties.tint_value)

        return entity

    def calculate_extents(self, objs):
        emin = Vector((0, 0, 0))
        emax = Vector((0, 0, 0))
        smin = Vector((0, 0, 0))
        smax = Vector((0, 0, 0))

        for obj in objs:
            loddist = obj.entity_properties.lod_dist
            bbmin, bbmax = get_bound_extents(obj)
            sbmin = subtract_from_vector(bbmin, loddist)
            sbmax = add_to_vector(bbmax, loddist)

            emin = get_min_vector(emin, bbmin)
            emax = get_max_vector(emax, bbmax)
            smin = get_min_vector(smin, sbmin)
            smax = get_max_vector(smax, sbmax)

        return emin, emax, smin, smax

    def run(self, context):

        objs = []
        for obj in context.collection.objects:
            if obj.sollum_type == SollumType.DRAWABLE:
                objs.append(obj)

        if len(objs) == 0:
            self.warning("No entities in scene to export.")
            return False

        try:
            ymap = CMapData()
            name = os.path.splitext(
                os.path.basename(context.blend_data.filepath))[0]
            ymap.name = name if len(name) > 0 else "untitled"
            ymap.parent = ""  # add a property ? if so how?
            ymap.flags = 0
            ymap.content_flags = 0

            for obj in objs:
                ent = self.entity_from_obj(obj)
                ymap.entities.append(ent)

            emin, emax, smin, smax = self.calculate_extents(objs)
            ymap.streaming_extents_min = emin
            ymap.streaming_extents_max = emax
            ymap.entities_extents_min = smin
            ymap.entities_extents_max = smax

            filepath = self.get_filepath(ymap.name)
            ymap.write_xml(filepath)

            self.message(f"Succesfully exported: {filepath}")
            return True
        except:
            self.message(f"Error during export: {traceback.format_exc()}")
            return False