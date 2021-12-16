import bpy
from ..sollumz_helper import SOLLUMZ_OT_base
from ..sollumz_properties import SOLLUMZ_UI_NAMES, ArchetypeType, AssetType, SollumType, EntityPriorityLevel, EntityLodLevel
from ..tools.blenderhelper import get_selected_vertices
from ..tools.meshhelper import get_bound_extents, get_bound_center, get_obj_radius
from ..tools.utils import get_min_vector_list, get_max_vector_list
from ..resources.ytyp import *
from ..resources.ymap import *
from .properties import *
from bpy_extras.io_utils import ImportHelper

import os
import traceback


class SOLLUMZ_OT_create_ytyp(SOLLUMZ_OT_base, bpy.types.Operator):
    """Add a ytyp to the project"""
    bl_idname = "sollumz.createytyp"
    bl_label = "Create YTYP"

    def run(self, context):
        item = context.scene.ytyps.add()
        index = len(context.scene.ytyps)
        item.name = f"YTYP.{index}"
        context.scene.ytyp_index = index - 1

        return True


class SOLLUMZ_OT_delete_ytyp(SOLLUMZ_OT_base, bpy.types.Operator):
    """Delete a ytyp from the project"""
    bl_idname = "sollumz.deleteytyp"
    bl_label = "Delete YTYP"

    def run(self, context):
        context.scene.ytyps.remove(context.scene.ytyp_index)
        context.scene.ytyp_index = max(context.scene.ytyp_index - 1, 0)

        return True


class SOLLUMZ_OT_create_archetype(SOLLUMZ_OT_base, bpy.types.Operator):
    """Add an archetype to the selected ytyp"""
    bl_idname = "sollumz.createarchetype"
    bl_label = "Create Archetype"

    @classmethod
    def poll(cls, context):
        return get_selected_ytyp(context) is not None

    def run(self, context):
        selected_ytyp = get_selected_ytyp(context)
        item = selected_ytyp.archetypes.add()
        index = len(selected_ytyp.archetypes)
        item.name = f"{SOLLUMZ_UI_NAMES[ArchetypeType.BASE]}.{index}"
        selected_ytyp.archetype_index = index - 1

        return True


class SOLLUMZ_OT_create_archetype_from_selected(SOLLUMZ_OT_base, bpy.types.Operator):
    """Create archetype from selected"""
    bl_idname = "sollumz.createarchetypefromselected"
    bl_label = "Auto-Create From Selected"

    allowed_types = [SollumType.DRAWABLE,
                     SollumType.BOUND_COMPOSITE, SollumType.FRAGMENT, SollumType.DRAWABLE_DICTIONARY]

    @classmethod
    def poll(cls, context):
        return get_selected_ytyp(context) is not None

    def run(self, context):
        selected_objs = context.selected_objects
        found = False
        for obj in selected_objs:
            archetype_type = context.scene.create_archetype_type
            if not obj.sollum_type in self.allowed_types:
                continue
            if archetype_type == ArchetypeType.MLO:
                if obj.sollum_type != SollumType.BOUND_COMPOSITE:
                    self.message(
                        f"MLO asset '{obj.name}' must be a {SOLLUMZ_UI_NAMES[SollumType.BOUND_COMPOSITE]}!")
                    continue
            found = True
            selected_ytyp = get_selected_ytyp(context)
            item = selected_ytyp.archetypes.add()
            index = len(selected_ytyp.archetypes)
            selected_ytyp.archetype_index = index - 1

            item.name = obj.name
            item.asset = obj

            item.type = archetype_type

            if obj.sollum_type == SollumType.DRAWABLE:
                item.asset_type = AssetType.DRAWABLE
            elif obj.sollum_type == SollumType.DRAWABLE_DICTIONARY:
                item.asset_type = AssetType.DRAWABLE_DICTIONARY
            elif obj.sollum_type == SollumType.BOUND_COMPOSITE:
                item.asset_type = AssetType.ASSETLESS
            elif obj.sollum_type == SollumType.FRAGMENT:
                item.asset_type = AssetType.FRAGMENT
        if not found:
            self.message(
                f"No asset of type '{','.join([SOLLUMZ_UI_NAMES[type] for type in self.allowed_types])}' found!")
            return False
        return True


class SOLLUMZ_OT_delete_archetype(SOLLUMZ_OT_base, bpy.types.Operator):
    """Delete archetype from selected ytyp"""
    bl_idname = "sollumz.deletearchetype"
    bl_label = "Delete Archetype"

    @classmethod
    def poll(cls, context):
        return len(context.scene.ytyps) > 0

    def run(self, context):
        selected_ytyp = get_selected_ytyp(context)
        selected_ytyp.archetypes.remove(selected_ytyp.archetype_index)
        selected_ytyp.archetype_index = max(
            selected_ytyp.archetype_index - 1, 0)

        return True


class SOLLUMZ_OT_create_room(SOLLUMZ_OT_base, bpy.types.Operator):
    """Add a room to the selected archetype"""
    bl_idname = "sollumz.createroom"
    bl_label = "Create Room"

    @classmethod
    def poll(cls, context):
        selected_archetype = get_selected_archetype(context)
        return selected_archetype and selected_archetype.type == ArchetypeType.MLO

    def run(self, context):
        selected_archetype = get_selected_archetype(context)
        selected_archetype.new_room()

        return True


class SOLLUMZ_OT_create_limbo_room(SOLLUMZ_OT_base, bpy.types.Operator):
    """Automatically create a limbo room for the selected archetype (requires linked object to be specified)."""
    bl_idname = "sollumz.createlimboroom"
    bl_label = "Create Limbo Room"

    @classmethod
    def poll(cls, context):
        selected_archetype = get_selected_archetype(context)
        return selected_archetype and selected_archetype.type == ArchetypeType.MLO and selected_archetype.asset is not None

    def run(self, context):
        selected_archetype = get_selected_archetype(context)
        room = selected_archetype.new_room()
        bbmin, bbmax = get_bound_extents(selected_archetype.asset)
        room.bb_min = bbmin
        room.bb_max = bbmax
        room.name = "limbo"

        return True


class SOLLUMZ_OT_set_bounds_from_selection(SOLLUMZ_OT_base, bpy.types.Operator):
    """Set room bounds from selection (must be in edit mode)"""
    bl_idname = "sollumz.setroomboundsfromselection"
    bl_label = "Set Bounds From Selection"

    @classmethod
    def poll(cls, context):
        return get_selected_room(context) is not None and (context.active_object and context.active_object.mode == "EDIT")

    def run(self, context):
        selected_archetype = get_selected_archetype(context)
        selected_room = get_selected_room(context)
        selected_verts = []
        for obj in context.objects_in_mode:
            selected_verts.extend(get_selected_vertices(obj))
        if not len(selected_verts) > 1:
            self.message("You must select at least 2 vertices!")
            return False
        if not selected_archetype.asset:
            self.message("You must set an asset for the archetype.")
            return False

        pos = selected_archetype.asset.location

        selected_room.bb_max = get_max_vector_list(
            selected_verts) - pos
        selected_room.bb_min = get_min_vector_list(
            selected_verts) - pos
        return True


class SOLLUMZ_OT_delete_room(SOLLUMZ_OT_base, bpy.types.Operator):
    """Delete room from selected archetype"""
    bl_idname = "sollumz.deleteroom"
    bl_label = "Delete Room"

    @classmethod
    def poll(cls, context):
        return get_selected_room(context) is not None

    def run(self, context):
        selected_archetype = get_selected_archetype(context)
        selected_archetype.rooms.remove(selected_archetype.room_index)
        selected_archetype.room_index = max(
            selected_archetype.room_index - 1, 0)
        return True


class SOLLUMZ_OT_create_portal(SOLLUMZ_OT_base, bpy.types.Operator):
    """Add a portal to the selected archetype"""
    bl_idname = "sollumz.createportal"
    bl_label = "Create Portal"

    @classmethod
    def poll(cls, context):
        return get_selected_archetype(context) is not None

    def run(self, context):
        selected_archetype = get_selected_archetype(context)
        selected_archetype.new_portal()

        return True


class SOLLUMZ_OT_create_portal_from_selection(SOLLUMZ_OT_base, bpy.types.Operator):
    """Create a portal from selected verts"""
    bl_idname = "sollumz.createportalfromselection"
    bl_label = "Create Portal From Verts"

    @classmethod
    def poll(cls, context):
        return get_selected_archetype(context) is not None and (context.active_object and context.active_object.mode == "EDIT")

    def run(self, context):
        selected_archetype = get_selected_archetype(context)
        selected_verts = []

        for obj in context.objects_in_mode:
            selected_verts.extend(get_selected_vertices(obj))

        if len(selected_verts) != 4:
            self.message("You must select exactly 4 vertices.")
            return False

        if not selected_archetype.asset:
            self.message("You must select an asset.")
            return False

        corners = selected_verts
        corners.sort()

        pos = selected_archetype.asset.location
        new_portal = selected_archetype.new_portal()
        new_portal.corner1 = corners[0] - pos
        new_portal.corner2 = corners[1] - pos
        new_portal.corner3 = corners[3] - pos
        new_portal.corner4 = corners[2] - pos

        return True


class SOLLUMZ_OT_delete_portal(SOLLUMZ_OT_base, bpy.types.Operator):
    """Delete portal from selected archetype"""
    bl_idname = "sollumz.deleteportal"
    bl_label = "Delete Portal"

    @classmethod
    def poll(cls, context):
        return get_selected_portal(context)

    def run(self, context):
        selected_archetype = get_selected_archetype(context)
        selected_archetype.portals.remove(selected_archetype.portal_index)
        selected_archetype.portal_index = max(
            selected_archetype.portal_index - 1, 0)
        return True


class SetPortalRoomHelper(SOLLUMZ_OT_base):
    bl_label = "Set to Selected"
    room_from = False
    room_to = False

    @classmethod
    def poll(cls, context):
        return get_selected_portal(context) is not None

    def run(self, context):
        selected_room = get_selected_room(context)
        selected_portal = get_selected_portal(context)
        if selected_portal is None:
            self.message("No portal selected!")
            return False

        if selected_room is None:
            self.message("No room selected!")
            return False

        if self.room_from:
            selected_portal.room_from_id = selected_room.id
        elif self.room_to:
            selected_portal.room_to_id = selected_room.id
        return True


class SOLLUMZ_OT_set_portal_room_from(SetPortalRoomHelper, bpy.types.Operator):
    """Set 'room from' to selected room"""
    bl_idname = "sollumz.setportalroomfrom"
    room_from = True


class SOLLUMZ_OT_set_portal_room_to(SetPortalRoomHelper, bpy.types.Operator):
    """Set 'room to' to selected room"""
    bl_idname = "sollumz.setportalroomto"
    room_to = True


class SOLLUMZ_OT_create_mlo_entity(SOLLUMZ_OT_base, bpy.types.Operator):
    """Add an entity to the selected mlo archetype"""
    bl_idname = "sollumz.createmloentity"
    bl_label = "Create Entity"

    @classmethod
    def poll(cls, context):
        return get_selected_archetype(context) is not None

    def run(self, context):
        selected_archetype = get_selected_archetype(context)
        selected_archetype.entities.add()
        return True


class SOLLUMZ_OT_add_obj_as_entity(SOLLUMZ_OT_base, bpy.types.Operator):
    """Add an object as an entity to the selected mlo archetype"""
    bl_idname = "sollumz.addobjasmloentity"
    bl_label = "Add Selected Object as Entity"

    @classmethod
    def poll(cls, context):
        return get_selected_archetype(context) is not None

    def run(self, context):
        selected_archetype = get_selected_archetype(context)
        item = selected_archetype.entities.add()
        item.linked_object = context.active_object
        item.archetype_name = context.active_object.name
        return True


class SOLLUMZ_OT_delete_mlo_entity(SOLLUMZ_OT_base, bpy.types.Operator):
    """Delete an entity from the selected mlo archetype"""
    bl_idname = "sollumz.deletemloentity"
    bl_label = "Delete Entity"

    @classmethod
    def poll(cls, context):
        return get_selected_entity(context) is not None

    def run(self, context):
        selected_archetype = get_selected_archetype(context)
        selected_archetype.entities.remove(
            selected_archetype.entity_index)
        selected_archetype.entity_index = max(
            selected_archetype.entity_index - 1, 0)
        return True


class SOLLUMZ_OT_set_mlo_entity_room(SOLLUMZ_OT_base, bpy.types.Operator):
    """Set entity attached room"""
    bl_idname = "sollumz.setmloentityroom"
    bl_label = "Set to Selected"

    @classmethod
    def poll(cls, context):
        return get_selected_entity(context) is not None

    def run(self, context):
        selected_entity = get_selected_entity(context)
        selected_room = get_selected_room(context)

        selected_entity.attached_room_id = selected_room.id
        return True


class SOLLUMZ_OT_clear_mlo_entity_room(SOLLUMZ_OT_base, bpy.types.Operator):
    """Clear entity attached room"""
    bl_idname = "sollumz.clearmloentityroom"
    bl_label = "Clear Room"

    @classmethod
    def poll(cls, context):
        return get_selected_entity(context) is not None

    def run(self, context):
        selected_entity = get_selected_entity(context)

        selected_entity.attached_room_id = -1
        return True


class SOLLUMZ_OT_set_mlo_entity_portal(SOLLUMZ_OT_base, bpy.types.Operator):
    """Set entity attached portal"""
    bl_idname = "sollumz.setmloentityportal"
    bl_label = "Set to Selected"

    @classmethod
    def poll(cls, context):
        return get_selected_entity(context) is not None

    def run(self, context):
        selected_entity = get_selected_entity(context)
        selected_portal = get_selected_portal(context)

        selected_entity.attached_portal_id = selected_portal.id
        return True


class SOLLUMZ_OT_clear_mlo_entity_portal(SOLLUMZ_OT_base, bpy.types.Operator):
    """Clear entity attached portal"""
    bl_idname = "sollumz.clearmloentityportal"
    bl_label = "Clear Portal"

    @classmethod
    def poll(cls, context):
        return get_selected_entity(context) is not None

    def run(self, context):
        selected_entity = get_selected_entity(context)

        selected_entity.attached_portal_id = -1
        return True


class SOLLUMZ_OT_create_timecycle_modifier(SOLLUMZ_OT_base, bpy.types.Operator):
    """Add a timecycle modifier to the selected archetype"""
    bl_idname = "sollumz.createtimecyclemodifier"
    bl_label = "Create Timecycle Modifier"

    @classmethod
    def poll(cls, context):
        return get_selected_archetype(context) is not None

    def run(self, context):
        selected_archetype = get_selected_archetype(context)
        item = selected_archetype.timecycle_modifiers.add()
        item.name = f"Timecycle Modifier.{len(selected_archetype.timecycle_modifiers)}"
        return True


class SOLLUMZ_OT_delete_timecycle_modifier(SOLLUMZ_OT_base, bpy.types.Operator):
    """Delete timecycle modifier from selected archetype"""
    bl_idname = "sollumz.deletetimecyclemodifier"
    bl_label = "Delete Timecycle Modifier"

    @classmethod
    def poll(cls, context):
        return get_selected_archetype(context) is not None

    def run(self, context):
        selected_archetype = get_selected_archetype(context)
        selected_archetype.timecycle_modifiers.remove(
            selected_archetype.tcm_index)
        selected_archetype.tcm_index = max(selected_archetype.tcm_index - 1, 0)
        return True


class SOLLUMZ_OT_import_ytyp(SOLLUMZ_OT_base, bpy.types.Operator, ImportHelper):
    """Import a ytyp.xml"""
    bl_idname = "sollumz.importytyp"
    bl_label = "Import ytyp.xml"
    bl_action = "Import a YTYP"

    filename_ext = ".ytyp.xml"

    filter_glob: bpy.props.StringProperty(
        default="*.ytyp.xml",
        options={'HIDDEN'},
        maxlen=255,
    )

    def run(self, context):
        try:
            ytyp_xml = YTYP.from_xml_file(self.filepath)
            ytyp = context.scene.ytyps.add()
            ytyp.name = ytyp_xml.name
            for arch_xml in ytyp_xml.archetypes:
                arch = ytyp.archetypes.add()
                arch.name = arch_xml.name
                arch.flags.total = str(arch_xml.flags)
                arch.special_attribute = arch_xml.special_attribute
                arch.hd_texture_dist = arch_xml.hd_texture_dist
                arch.texture_dictionary = arch_xml.texture_dictionary
                arch.clip_dictionary = arch_xml.clip_dictionary
                arch.drawable_dictionary = arch_xml.drawable_dictionary
                arch.physics_dictionary = arch_xml.physics_dictionary
                arch.bb_min = arch_xml.bb_min
                arch.bb_max = arch_xml.bb_max
                arch.bs_center = arch_xml.bs_center
                arch.bs_radius = arch_xml.bs_radius
                arch.asset_name = arch_xml.asset_name
                # Find asset in scene
                for obj in context.scene.collection.all_objects:
                    if obj.name == arch.asset_name:
                        arch.asset = obj

                if arch_xml.type == "CBaseArchetypeDef":
                    arch.type = ArchetypeType.BASE
                elif arch_xml.type == "CTimeArchetypeDef":
                    arch.type = ArchetypeType.TIME
                    arch.time_flags.total = str(arch_xml.time_flags)
                elif arch_xml.type == "CMloArchetypeDef":
                    arch.type = ArchetypeType.MLO
                    arch.mlo_flags.total = str(arch_xml.mlo_flags)
                    for entity_index, entity_xml in enumerate(arch_xml.entities):
                        entity = arch.entities.add()
                        entity.position = entity_xml.position
                        entity.rotation = entity_xml.rotation
                        entity.scale_xy = entity_xml.scale_xy
                        entity.scale_z = entity_xml.scale_z
                        for obj in context.collection.all_objects:
                            if entity_xml.archetype_name == obj.name and obj.name in context.view_layer.objects:
                                entity.linked_object = obj
                        entity.archetype_name = entity_xml.archetype_name
                        entity.flags.total = str(entity_xml.flags)
                        entity.guid = entity_xml.guid
                        entity.parent_index = entity_xml.parent_index
                        entity.lod_dist = entity_xml.lod_dist
                        entity.child_lod_dist = entity_xml.child_lod_dist
                        entity.lod_level = EntityLodLevel[entity_xml.lod_level]
                        entity.priority_level = EntityPriorityLevel[entity_xml.priority_level]
                        entity.num_children = entity_xml.num_children
                        entity.ambient_occlusion_multiplier = entity_xml.ambient_occlusion_multiplier
                        entity.artificial_ambient_occlusion = entity_xml.artificial_ambient_occlusion
                        entity.tint_value = entity_xml.tint_value
                    for room_xml in arch_xml.rooms:
                        room = arch.new_room()
                        room.name = room_xml.name
                        room.bb_min = room_xml.bb_min
                        room.bb_max = room_xml.bb_max
                        room.blend = room_xml.blend
                        room.timecycle = room_xml.timecycle_name
                        room.secondary_timecycle = room_xml.secondary_timecycle_name
                        room.flags.total = str(room_xml.flags)
                        room.floor_id = room_xml.floor_id
                        room.exterior_visibility_depth = room_xml.exterior_visibility_depth
                        for index in room_xml.attached_objects:
                            arch.entities[index].attached_room_id = room.id
                    for portal_xml in arch_xml.portals:
                        portal = arch.new_portal()
                        for index, corner in enumerate(portal_xml.corners):
                            setattr(portal, f"corner{index + 1}", corner.value)
                        portal.room_from_id = arch.rooms[portal_xml.room_from].id
                        portal.room_to_id = arch.rooms[portal_xml.room_to].id
                        portal.flags.total = str(portal_xml.flags)
                        portal.mirror_priority = portal_xml.mirror_priority
                        portal.opacity = portal_xml.opacity
                        portal.audio_occlusion = portal_xml.audio_occlusion
                        for index in portal_xml.attached_objects:
                            arch.entities[index].attached_portal_id = portal.id
                    for tcm_xml in arch_xml.timecycle_modifiers:
                        tcm = arch.timecycle_modifiers.add()
                        tcm.name = tcm_xml.name
                        tcm.sphere = tcm_xml.sphere
                        tcm.percentage = tcm_xml.percentage
                        tcm.range = tcm_xml.range
                        tcm.start_hour = tcm_xml.start_hour
                        tcm.end_hour = tcm_xml.end_hour

                if arch_xml.asset_type == "ASSET_TYPE_UNINITIALIZED":
                    arch.asset_type = AssetType.UNITIALIZED
                elif arch_xml.asset_type == "ASSET_TYPE_FRAGMENT":
                    arch.asset_type = AssetType.FRAGMENT
                elif arch_xml.asset_type == "ASSET_TYPE_DRAWABLE":
                    arch.asset_type = AssetType.DRAWABLE
                elif arch_xml.asset_type == "ASSET_TYPE_DRAWABLE_DICTIONARY":
                    arch.asset_type = AssetType.DRAWABLE_DICTIONARY
                elif arch_xml.asset_type == "ASSET_TYPE_ASSETLESS":
                    arch.asset_type = AssetType.ASSETLESS

            self.message(f"Successfully imported: {self.filepath}")
            return True
        except:
            self.error(f"Error during import: {traceback.format_exc()}")
            return False


class SOLLUMZ_OT_export_ytyp(SOLLUMZ_OT_base, bpy.types.Operator):
    """Export the selected YTYP."""
    bl_idname = "sollumz.exportytyp"
    bl_label = "Export ytyp.xml"
    bl_action = "Export a YTYP"

    filter_glob: bpy.props.StringProperty(
        default="*.ytyp.xml",
        options={'HIDDEN'},
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

    @classmethod
    def poll(cls, context):
        num_ytyps = len(context.scene.ytyps)
        return num_ytyps > 0 and context.scene.ytyp_index < num_ytyps

    def get_filepath(self, name):
        return os.path.join(self.directory, name + ".ytyp.xml")

    @staticmethod
    def set_room_attached_objects(room_xml, room_index, entities):
        for index, entity in enumerate(entities):
            if entity.attached_room_index == room_index:
                room_xml.attached_objects.append(index)

    @staticmethod
    def set_portal_attached_objects(portal_xml, portal_index, entities):
        for index, entity in enumerate(entities):
            if entity.attached_portal_index == portal_index:
                portal_xml.attached_objects.append(index)

    @staticmethod
    def get_portal_count(room, portals):
        count = 0
        for portal in portals:
            if portal.room_from_id == room.id or portal.room_to_id == room.id:
                count += 1
        return count

    @staticmethod
    def init_archetype(arch_xml, arch):
        arch_xml.lod_dist = arch.lod_dist
        arch_xml.flags = arch.flags.total
        arch_xml.special_attribute = arch.special_attribute
        arch_xml.hd_texture_dist = arch.hd_texture_dist
        arch_xml.name = arch.name
        arch_xml.texture_dictionary = arch.texture_dictionary
        arch_xml.clip_dictionary = arch.clip_dictionary
        arch_xml.drawable_dictionary = arch.drawable_dictionary
        arch_xml.physics_dictionary = arch.physics_dictionary
        if arch.asset:
            bbmin, bbmax = get_bound_extents(arch.asset, world=False)
            arch_xml.bb_min = bbmin
            arch_xml.bb_max = bbmax
            arch_xml.bs_center = get_bound_center(arch.asset, world=False)
            arch_xml.bs_radius = get_obj_radius(arch.asset, world=False)
        else:
            arch_xml.bb_min = Vector(arch.bb_min)
            arch_xml.bb_max = Vector(arch.bb_max)
            arch_xml.bs_center = Vector(arch.bs_center)
            arch_xml.bs_radius = arch.bs_radius
        asset_type = arch.asset_type
        arch_xml.asset_name = arch.asset_name
        if asset_type == AssetType.UNITIALIZED:
            arch_xml.asset_type = "ASSET_TYPE_UNINITIALIZED"
        elif asset_type == AssetType.FRAGMENT:
            arch_xml.asset_type = "ASSET_TYPE_FRAGMENT"
        elif asset_type == AssetType.DRAWABLE:
            arch_xml.asset_type = "ASSET_TYPE_DRAWABLE"
        elif asset_type == AssetType.DRAWABLE_DICTIONARY:
            arch_xml.asset_type = "ASSET_TYPE_DRAWABLE_DICTIONARY"
        elif asset_type == AssetType.ASSETLESS:
            arch_xml.asset_type = "ASSET_TYPE_ASSETLESS"
        return arch_xml

    def run(self, context):
        try:
            selected_ytyp = context.scene.ytyps[context.scene.ytyp_index]
            ytyp = CMapTypes()
            ytyp.name = selected_ytyp.name
            for archetype in selected_ytyp.archetypes:
                archetype_xml = None
                if archetype.type == ArchetypeType.BASE:
                    archetype_xml = self.init_archetype(
                        BaseArchetype(), archetype)
                elif archetype.type == ArchetypeType.TIME:
                    archetype_xml = self.init_archetype(
                        TimeArchetype(), archetype)
                    archetype_xml.time_flags = archetype.time_flags.total
                elif archetype.type == ArchetypeType.MLO:
                    archetype_xml = self.init_archetype(
                        MloArchetype(), archetype)
                    archetype_xml.mlo_flags = archetype.mlo_flags.total
                    for entity in archetype.entities:
                        entity_xml = EntityItem()
                        entity_obj = entity.linked_object
                        if entity_obj:
                            entity_xml.position = entity_obj.location
                            entity_xml.rotation = entity_obj.rotation_euler.to_quaternion()
                            entity_xml.scale_xy = entity_obj.scale.x
                            entity_xml.scale_z = entity_obj.scale.z
                        else:
                            entity_xml.position = Vector(entity.position)
                            entity_xml.rotation = Quaternion(entity.rotation)
                            entity_xml.scale_xy = entity.scale_xy
                            entity_xml.scale_z = entity.scale_z
                        entity_xml.archetype_name = entity.archetype_name
                        entity_xml.flags = entity.flags.total
                        entity_xml.parent_index = entity.parent_index
                        entity_xml.lod_dist = entity.lod_dist
                        entity_xml.child_lod_dist = entity.child_lod_dist
                        lod_level = next(name for name, value in vars(
                            EntityLodLevel).items() if value == (entity.lod_level))
                        entity_xml.lod_level = lod_level
                        priority_level = next(name for name, value in vars(
                            EntityPriorityLevel).items() if value == (entity.priority_level))
                        entity_xml.priority_level = priority_level
                        entity_xml.ambient_occlusion_multiplier = entity.ambient_occlusion_multiplier
                        entity_xml.artificial_ambient_occlusion = entity.artificial_ambient_occlusion
                        entity_xml.tint_value = entity.tint_value
                        archetype_xml.entities.append(entity_xml)

                    for room_index, room in enumerate(archetype.rooms):
                        room_xml = Room()
                        room_xml.name = room.name
                        room_xml.bb_min = room.bb_min
                        room_xml.bb_max = room.bb_max
                        room_xml.blend = room.blend
                        room_xml.timecycle_name = room.timecycle
                        room_xml.secondary_timecycle_name = room.secondary_timecycle
                        room_xml.flags = room.flags.total
                        room_xml.floor_id = room.floor_id
                        room_xml.exterior_visibility_depth = room.exterior_visibility_depth
                        room_xml.portal_count = self.get_portal_count(
                            room, archetype.portals)

                        self.set_room_attached_objects(
                            room_xml, room_index, archetype.entities)
                        archetype_xml.rooms.append(room_xml)
                    for portal_index, portal in enumerate(archetype.portals):
                        portal_xml = Portal()
                        for i in range(4):
                            corner = getattr(portal, f"corner{i + 1}")
                            corner_xml = Corner()
                            corner_xml.value = corner
                            portal_xml.corners.append(corner_xml)

                        portal_xml.room_from = portal.room_from_index
                        portal_xml.room_to = portal.room_to_index
                        portal_xml.flags = portal.flags.total
                        portal_xml.mirror_priority = portal.mirror_priority
                        self.set_portal_attached_objects(
                            portal_xml, portal_index, archetype.entities)
                        portal_xml.opacity = portal.opacity
                        portal_xml.audio_occlusion = portal.audio_occlusion
                        archetype_xml.portals.append(portal_xml)
                    for tcm in archetype.timecycle_modifiers:
                        tcm_xml = TimeCycleModifier()
                        tcm_xml.name = tcm.name
                        tcm_xml.sphere = tcm.sphere
                        tcm_xml.percentage = tcm.percentage
                        tcm_xml.range = tcm.range
                        tcm_xml.start_hour = tcm.start_hour
                        tcm_xml.end_hour = tcm.end_hour
                        archetype_xml.timecycle_modifiers.append(tcm_xml)
                else:
                    continue
                ytyp.archetypes.append(archetype_xml)
            filepath = self.get_filepath(ytyp.name)
            ytyp.write_xml(filepath)
            self.message(f"Successfully exported: {filepath}")
            return True
        except:
            self.error(f"Error during export: {traceback.format_exc()}")
            return False
