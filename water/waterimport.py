import bpy
from ..cwxml.water import WaterData
from ..sollumz_properties import SollumType
from ..tools.blenderhelper import create_blender_object, create_empty_object
from .utils import create_materials
from .. import logger

def create_quad_object(quad, type):

    # Avoid Z-Fighing
    height_mapping = {
        SollumType.WATER_QUAD: quad.z,
        SollumType.CALMING_QUAD: -0.01,
        SollumType.WAVE_QUAD: -0.02}

    height = height_mapping.get(type, 0.0)

    vertices = [
        (quad.minX, quad.minY, height),
        (quad.maxX, quad.minY, height),
        (quad.maxX, quad.maxY, height),
        (quad.minX, quad.maxY, height)]
    faces = [(0, 1, 2, 3)]

    if type == SollumType.WATER_QUAD:
        mesh = bpy.data.meshes.new("WaterQuad")
        mesh.from_pydata(vertices, [], faces)
        quad_obj = create_blender_object(SollumType.WATER_QUAD, object_data=mesh)
        quad_obj.data.materials.append(create_materials("WaterQuad", (0, 0.18, 1)))
        quad_obj.water_quad_properties.type = quad.type
        quad_obj.water_quad_properties.invisible = quad.invisible
        quad_obj.water_quad_properties.limited_depth = quad.limited_depth
        quad_obj.water_quad_properties.a1 = quad.a1
        quad_obj.water_quad_properties.a2 = quad.a2
        quad_obj.water_quad_properties.a3 = quad.a3
        quad_obj.water_quad_properties.a4 = quad.a4
        quad_obj.water_quad_properties.no_stencil = quad.no_stencil
        quad_obj.lock_location = (False, False, False)
        quad_obj.lock_rotation = (True, True, True)
        quad_obj.lock_scale = (False, False, True)
        return quad_obj

    elif type == SollumType.CALMING_QUAD:
        mesh = bpy.data.meshes.new("CalmingQuad")
        mesh.from_pydata(vertices, [], faces)
        quad_obj = create_blender_object(SollumType.CALMING_QUAD, object_data=mesh)
        quad_obj.data.materials.append(create_materials("CalmingQuad", (0, 0.66, 1)))
        quad_obj.calming_quad_properties.dampening = quad.dampening
        quad_obj.lock_location = (False, False, True)
        quad_obj.lock_rotation = (True, True, True)
        quad_obj.lock_scale = (False, False, True)
        return quad_obj

    elif type == SollumType.WAVE_QUAD:
        mesh = bpy.data.meshes.new("WaveQuad")
        mesh.from_pydata(vertices, [], faces)
        quad_obj = create_blender_object(SollumType.WAVE_QUAD, object_data=mesh)
        quad_obj.data.materials.append(create_materials("WaveQuad", (0, 1, 0.4)))
        quad_obj.wave_quad_properties.amplitude = quad.amplitude
        quad_obj.wave_quad_properties.xdirection = quad.xdirection
        quad_obj.wave_quad_properties.ydirection = quad.ydirection
        quad_obj.lock_location = (False, False, True)
        quad_obj.lock_rotation = (True, True, True)
        quad_obj.lock_scale = (False, False, True)
        return quad_obj


def water_to_obj(water):
    water_obj = create_empty_object(SollumType.WATER_DATA)
    water_obj.lock_location = (True, True, True)
    water_obj.lock_rotation = (True, True, True)
    water_obj.lock_scale = (True, True, True)

    water_quads = create_empty_object(SollumType.WATER_QUADS)
    water_quads.lock_location = (True, True, True)
    water_quads.lock_rotation = (True, True, True)
    water_quads.lock_scale = (True, True, True)
    water_quads.parent = water_obj
    if len(water.water) > 0:
        for quad in water.water:
            quad_obj = create_quad_object(quad, SollumType.WATER_QUAD)
            quad_obj.parent = water_quads
    
    calming_quads = create_empty_object(SollumType.CALMING_QUADS)
    calming_quads.lock_location = (True, True, True)
    calming_quads.lock_rotation = (True, True, True)
    calming_quads.lock_scale = (True, True, True)
    calming_quads.parent = water_obj
    if len(water.calming) > 0:
        for quad in water.calming:
            quad_obj = create_quad_object(quad, SollumType.CALMING_QUAD)
            quad_obj.parent = calming_quads

    wave_quads = create_empty_object(SollumType.WAVE_QUADS)
    wave_quads.lock_location = (True, True, True)
    wave_quads.lock_rotation = (True, True, True)
    wave_quads.lock_scale = (True, True, True)
    wave_quads.parent = water_obj
    if len(water.wave) > 0:
        for quad in water.wave:
            quad_obj = create_quad_object(quad, SollumType.WAVE_QUAD)
            quad_obj.parent = wave_quads

    return water_obj


def import_water(filepath):
    water_xml: WaterData = WaterData.from_xml_file(filepath)
    found = False
    for obj in bpy.context.scene.objects:
        if obj.sollum_type == SollumType.WATER_DATA:
            logger.error(
                "Another water.xml is already present in the scene. Aborting.")
            found = True
            break
    if not found:
        obj = water_to_obj(water_xml)