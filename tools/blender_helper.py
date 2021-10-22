import bpy
import bmesh


def split_object(obj, parent):
    objs = []
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.separate(type='MATERIAL')
    bpy.ops.object.mode_set(mode='OBJECT')
    for child in parent.children:
        objs.append(child)
    return objs


def join_objects(objs):
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = objs[0]
    for obj in objs:
        obj.select_set(True)
    bpy.ops.object.join()
    bpy.ops.object.select_all(action='DESELECT')
    return


def triangulate_object(mesh):
    bm = bmesh.new()
    bm.from_mesh(mesh)

    bmesh.ops.triangulate(bm, faces=bm.faces[:])

    bm.to_mesh(mesh)
    bm.free()
