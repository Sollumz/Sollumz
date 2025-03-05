import bpy
from ..sollumz_helper import SOLLUMZ_OT_base
from ..sollumz_properties import SollumType
from ..tools.blenderhelper import create_empty_object
from .waterimport import create_quad_object
from dataclasses import dataclass

class SOLLUMZ_OT_create_water_data(SOLLUMZ_OT_base, bpy.types.Operator):
    """Create a water.xml hierarchy object"""
    bl_idname = "sollumz.createwaterdata"
    bl_label = f"Create Water Data"
    bl_description = "Create Water Data Hierarchy"

    @classmethod
    def poll(cls, context):
        for obj in context.scene.objects:
            if obj.sollum_type == SollumType.WATER_DATA:
                return False
        return True

    def run(self, context):
        
        water_obj = create_empty_object(SollumType.WATER_DATA)
        water_obj.lock_location = (True, True, True)
        water_obj.lock_rotation = (True, True, True)
        water_obj.lock_scale = (True, True, True)

        quad_types = [SollumType.WATER_QUADS, SollumType.CALMING_QUADS, SollumType.WAVE_QUADS]

        for quads in quad_types:
            child_obj = create_empty_object(quads)
            child_obj.lock_location = (True, True, True)
            child_obj.lock_rotation = (True, True, True)
            child_obj.lock_scale = (False, False, True)
            child_obj.parent = water_obj

        return {"FINISHED"}


@dataclass
class DefaultQuad:
    minX: float = -1
    maxX: float = 1
    minY: float = -1
    maxY: float = 1
    z: float = 0
    type: int = 0
    invisible: bool = False
    limited_depth: bool = False
    a1: float = 0
    a2: float = 0
    a3: float = 0
    a4: float = 0
    no_stencil: bool = False
    dampening: float = 0
    amplitude: float = 0
    xdirection: int = 0
    ydirection: int = 0


class SOLLUMZ_OT_create_water_quad(SOLLUMZ_OT_base, bpy.types.Operator):
    """Create a standard water quad"""
    bl_idname = "sollumz.createwaterquad"
    bl_label = f"Create Water Quad"
    bl_description = "Create a Standard Water Quad"

    @classmethod
    def poll(cls, context):
        aobj = context.active_object
        sobj = context.selected_objects[0] if len(context.selected_objects) == 1 else None

        if aobj and aobj == sobj and aobj.sollum_type in [SollumType.WATER_QUADS, SollumType.CALMING_QUADS, SollumType.WAVE_QUADS]:
            return True
        return False

    def run(self, context):
        aobj = context.active_object

        if aobj.sollum_type == SollumType.WATER_QUADS:
            q = create_quad_object(DefaultQuad, SollumType.WATER_QUAD)
            q.parent = aobj
            return {"FINISHED"}

        if aobj.sollum_type == SollumType.CALMING_QUADS:
            q = create_quad_object(DefaultQuad, SollumType.CALMING_QUAD)
            q.parent = aobj
            return {"FINISHED"}
        
        if aobj.sollum_type == SollumType.WAVE_QUADS:
            q = create_quad_object(DefaultQuad, SollumType.WAVE_QUAD)
            q.parent = aobj
            return {"FINISHED"}