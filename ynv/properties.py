import bpy


def register():
    bpy.types.Object.poly_flags = bpy.props.CollectionProperty(
        type=bpy.props.StringProperty)




def unregister():
    del bpy.types.Object.poly_flags
