import bpy
from ..cwxml.water import *
from ..sollumz_properties import SollumType
from .utils import ensure_quad_data

def water_quad_from_object(quad):
    water_quad = Water()

    result = ensure_quad_data(quad)
    if result is not None:
        minX, maxX, minY, maxY, z = result
    else:
        return None

    water_quad.minX = minX
    water_quad.maxX = maxX
    water_quad.minY = minY
    water_quad.maxY = maxY
    water_quad.z = z
    water_quad.type = quad.water_quad_properties.type
    water_quad.invisible = quad.water_quad_properties.invisible
    water_quad.limited_depth = quad.water_quad_properties.limited_depth
    water_quad.a1 = quad.water_quad_properties.a1
    water_quad.a2 = quad.water_quad_properties.a2
    water_quad.a3 = quad.water_quad_properties.a3
    water_quad.a4 = quad.water_quad_properties.a4
    water_quad.no_stencil = quad.water_quad_properties.no_stencil

    return water_quad


def calming_quad_from_object(quad):
    calming_quad = Calming()

    result = ensure_quad_data(quad)
    if result is not None:
        minX, maxX, minY, maxY = result
    else:
        return None

    calming_quad.minX = minX
    calming_quad.maxX = maxX
    calming_quad.minY = minY
    calming_quad.maxY = maxY

    calming_quad.dampening = quad.calming_quad_properties.dampening

    return calming_quad

def wave_quad_from_object(quad):
    wave_quad = Wave()

    result = ensure_quad_data(quad)
    if result is not None:
        minX, maxX, minY, maxY = result
    else:
        return None

    wave_quad.minX = minX
    wave_quad.maxX = maxX
    wave_quad.minY = minY
    wave_quad.maxY = maxY

    wave_quad.amplitude = quad.wave_quad_properties.amplitude
    wave_quad.xdirection = quad.wave_quad_properties.xdirection
    wave_quad.ydirection = quad.wave_quad_properties.ydirection

    return wave_quad


def water_from_object(obj):
    water = WaterData()

    for child in obj.children:

        if child.sollum_type == SollumType.WATER_QUADS:
            for quad in child.children:
                quad_xml = water_quad_from_object(quad)
                if quad_xml: water.water.append(quad_xml)
                else: continue

        if child.sollum_type == SollumType.CALMING_QUADS:
            for quad in child.children:
                quad_xml = calming_quad_from_object(quad)
                if quad_xml: water.calming.append(quad_xml)
                else: continue

        if child.sollum_type == SollumType.WAVE_QUADS:
            for quad in child.children:
                quad_xml = wave_quad_from_object(quad)
                if quad_xml: water.wave.append(quad_xml)
                else: continue

    return water

def export_water(obj: bpy.types.Object, filepath: str) -> bool:
    water = water_from_object(obj)
    water.write_xml(filepath)
    return True