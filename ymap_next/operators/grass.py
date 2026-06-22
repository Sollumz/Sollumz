import bpy
import numpy as np
from bpy.types import (
    Operator,
)

from ...sollumz_properties import SollumType
from ...tools.blenderhelper import create_blender_object
from ..context import (
    active_grass_batch,
    active_group,
)
from ..grass.geonodes import (
    add_grass_batch_modifier,
    create_grass_batch_geonodes,
    is_grass_batch_geonodes_supported,
)
from ..properties.map import get_maps


class SOLLUMZ_OT_map_grass_bake_color(Operator):
    bl_idname = "sollumz.map_grass_bake_color"
    bl_label = "Bake Grass Color and AO On Active Object"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        aobj = context.active_object
        return aobj and aobj.type == "MESH" and aobj.mode == "OBJECT" and context.selected_objects

    def execute(self, context):
        ATTR_GRASS_COLOR_AO = ".grass.source_color_ao"
        ATTR_GRASS_TMP = ".grass.bake_tmp"

        aobj = context.active_object
        objs = [aobj] + [obj for obj in context.selected_objects if obj != aobj and obj.type == "MESH"]
        old_active_attrs = []
        tmp_attrs = []
        tmp_buffers = []

        # Setup temporary scene and attributes
        tmp_scene = bpy.data.scenes.new("TemporarySceneForGrassBake")
        tmp_scene.render.engine = "CYCLES"  # only Cycles can bake
        tmp_scene.render.bake.target = "VERTEX_COLORS"
        tmp_scene.cycles.device = "GPU"
        for obj in objs:
            tmp_scene.collection.objects.link(obj)

            attributes = obj.data.attributes
            if not (attr := attributes.get(ATTR_GRASS_COLOR_AO, None)):
                attr = attributes.new(ATTR_GRASS_COLOR_AO, "BYTE_COLOR", "CORNER")

            # Temporary attribute where we will bake to
            tmp_attr = attributes.new(ATTR_GRASS_TMP, "BYTE_COLOR", attr.domain)
            old_active_attrs.append(attributes.active_color_name)
            attributes.active_color_name = tmp_attr.name  # bake uses the active attribute
            tmp_attrs.append(tmp_attr.name)

            n = attributes.domain_size(tmp_attr.domain)
            tmp_buffers.append(np.empty((n, 4), dtype=np.float32))

        with bpy.context.temp_override(scene=tmp_scene):
            # Bake color
            tmp_scene.cycles.bake_type = "DIFFUSE"
            tmp_scene.render.bake.use_pass_direct = False
            tmp_scene.render.bake.use_pass_indirect = False
            tmp_scene.render.bake.use_pass_color = True
            bpy.ops.object.bake(type="DIFFUSE")

            # Store baked color values
            for obj, tmp_buffer in zip(objs, tmp_buffers):
                tmp_attr = obj.data.attributes.active_color
                tmp_attr.data.foreach_get("color_srgb", tmp_buffer.ravel())

            # Bake AO
            tmp_scene.cycles.bake_type = "AO"
            bpy.ops.object.bake(type="AO")

            # Read baked AO values and combine color+AO in final attribute
            for obj, tmp_buffer in zip(objs, tmp_buffers):
                combined_buffer = np.copy(tmp_buffer)

                tmp_attr = obj.data.attributes.active_color
                tmp_attr.data.foreach_get("color_srgb", tmp_buffer.ravel())

                # Write AO to alpha channel
                combined_buffer[:, 3] = tmp_buffer[:, 0]

                attr = obj.data.attributes[ATTR_GRASS_COLOR_AO]
                attr.data.foreach_set("color_srgb", combined_buffer.ravel())

        # Restore objects to initial state
        for obj, tmp_attr_name, old_active_attr_name in zip(objs, tmp_attrs, old_active_attrs):
            attributes = obj.data.attributes
            if tmp_attr := attributes.get(tmp_attr_name, None):
                attributes.remove(tmp_attr)
            attributes.active_color_name = old_active_attr_name

            obj.data.update_tag()

        bpy.data.scenes.remove(tmp_scene)

        return {"FINISHED"}


class SOLLUMZ_OT_map_grass_create_geonodes(Operator):
    bl_idname = "sollumz.map_grass_create_geonodes"
    bl_label = "Update Grass Geometry Nodes"
    bl_description = "Create or refresh the geometry nodes for this grass batch based on its templates"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        if not is_grass_batch_geonodes_supported():
            cls.poll_message_set("Grass geometry nodes require Blender 5.0 or newer.")
            return False

        group = active_group(context)
        return group and group.grass_batches

    def execute(self, context):
        group = active_group(context)
        for grass_batch in group.grass_batches.selected_items:
            create_grass_batch_geonodes(grass_batch)
        return {"FINISHED"}


class SOLLUMZ_OT_map_grass_add_modifier(Operator):
    bl_idname = "sollumz.map_grass_add_modifier"
    bl_label = "Add Grass Modifier To Active Object"
    bl_description = ""
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        aobj = context.active_object
        if aobj and aobj.type == "MESH" and aobj.mode == "OBJECT":
            grass_batch = active_grass_batch(context)
            return grass_batch and grass_batch.modifier_ng is not None

        return False

    def execute(self, context):
        aobj = context.active_object
        grass_batch = active_grass_batch(context)
        add_grass_batch_modifier(aobj, grass_batch)
        return {"FINISHED"}


class SOLLUMZ_OT_map_grass_create_instances_mesh(Operator):
    bl_idname = "sollumz.map_grass_create_instances_mesh"
    bl_label = "Create Grass Instances Mesh"
    bl_description = ""
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        grass_batch = active_grass_batch(context)
        return grass_batch and grass_batch.linked_object is None

    def execute(self, context):
        grass_batch = active_grass_batch(context)

        # TODO(ymap): link new grass instances mesh to correct collection
        name = f"{grass_batch.name}.instances"
        mesh = bpy.data.meshes.new(name)
        obj = create_blender_object(SollumType.NONE, name, mesh)
        grass_batch.linked_object = obj
        if grass_batch.modifier_ng is None and is_grass_batch_geonodes_supported():
            create_grass_batch_geonodes(grass_batch)
        add_grass_batch_modifier(obj, grass_batch)

        return {"FINISHED"}
