import bpy


class WaterQuadProperties(bpy.types.PropertyGroup):
    type: bpy.props.IntProperty(name="Type")
    invisible: bpy.props.BoolProperty(name="Is Invisible")
    limited_depth: bpy.props.BoolProperty(name="Has Limited Depth")
    a1: bpy.props.IntProperty(name="A1")
    a2: bpy.props.IntProperty(name="A2")
    a3: bpy.props.IntProperty(name="A3")
    a4: bpy.props.IntProperty(name="A4")
    no_stencil: bpy.props.BoolProperty(name="No Stencil")

class CalmingQuadProperties(bpy.types.PropertyGroup):
    dampening: bpy.props.FloatProperty(name="Dampening")

class WaveQuadProperties(bpy.types.PropertyGroup):
    amplitude: bpy.props.FloatProperty(name="Amplitude")
    xdirection: bpy.props.FloatProperty(name="X Direction")
    ydirection: bpy.props.FloatProperty(name="Y Direction")


def register():
    bpy.types.Object.water_quad_properties = bpy.props.PointerProperty(type=WaterQuadProperties)
    bpy.types.Object.calming_quad_properties = bpy.props.PointerProperty(type=CalmingQuadProperties)
    bpy.types.Object.wave_quad_properties = bpy.props.PointerProperty(type=WaveQuadProperties)

def unregister():
    del bpy.types.Object.water_quad_properties
    del bpy.types.Object.calming_quad_properties
    del bpy.types.Object.wave_quad_properties