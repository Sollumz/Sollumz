import bpy

from cwxml.ymap import CMapData


def register():
    bpy.types.Scene.ymaps = bpy.props.CollectionProperty(
        type=CMapData, name="YMAPS")
    bpy.types.Scene.ymaps_index = bpy.props.IntProperty(name="YMAPS Index")



def unregister():
    del bpy.types.Scene.ymaps
    del bpy.types.Scene.ymaps_index