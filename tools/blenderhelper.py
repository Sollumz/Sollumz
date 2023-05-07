import bpy
import bmesh
from mathutils import Vector

from ..sollumz_properties import SOLLUMZ_UI_NAMES, SollumType, SollumzAddonPreferences


def get_addon_preferences(context: bpy.types.Context) -> SollumzAddonPreferences:
    return context.preferences.addons[__package__.split(".")[0]].preferences


def remove_number_suffix(string: str):
    """Remove the .00# at that Blender puts at the end of object names."""
    return string.split(".")[0]


def create_brush(name):
    bpy.data.brushes.new(name=name, mode="VERTEX_PAINT")
    return bpy.data.brushes[name]


def apply_brush_settings(brush, idx):
    if idx < 5:
        brush.blend = "MIX"
    if idx == 1:
        brush.color = (0, 0, 0)
        brush.strength = 1
    elif idx == 2:
        brush.color = (0, 0, 1)
        brush.strength = 1
    elif idx == 3:
        brush.color = (0, 1, 0)
        brush.strength = 1
    elif idx == 4:
        brush.color = (0, 1, 1)
        brush.strength = 1
    elif idx == 5:
        alpha = bpy.context.scene.vert_paint_alpha
        if alpha > 0:
            brush.color = (1, 1, 1)
            brush.blend = "ADD_ALPHA"
            brush.strength = alpha
        else:
            brush.color = (0, 0, 0)
            brush.blend = "ERASE_ALPHA"
            brush.strength = alpha * -1
    return brush


def get_terrain_texture_brush(idx):
    name = "TerrainBrush"

    try:
        brush = bpy.data.brushes[name]
    except:
        brush = create_brush(name)
    apply_brush_settings(brush, idx)
    bpy.context.scene.tool_settings.vertex_paint.brush = brush
    return brush


def material_from_image(img, name="Material", nodename="Image"):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    node_tree = mat.node_tree
    links = node_tree.links
    bsdf = node_tree.nodes["Principled BSDF"]
    imgnode = node_tree.nodes.new("ShaderNodeTexImage")
    imgnode.name = nodename
    links.new(imgnode.outputs[0], bsdf.inputs[0])
    imgnode.image = img
    return mat


def select_object_and_children(obj):
    if obj.hide_get():
        obj.hide_set(False)
    obj.select_set(True)
    for child in obj.children:
        if child.hide_get():
            child.hide_set(False)
        child.select_set(True)
        for grandchild in child.children:
            select_object_and_children(grandchild)


def duplicate_object(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.ops.object.duplicate()
    return bpy.context.selected_objects[0]


def split_object(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.ops.mesh.separate(type="MATERIAL")
    return list(bpy.context.selected_objects)


def join_objects(objs):
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = objs[0]
    meshes = []
    for obj in objs:
        meshes.append(obj.data)
        obj.select_set(True)
    bpy.ops.object.join()
    bpy.ops.object.select_all(action="DESELECT")
    joined_obj = bpy.context.view_layer.objects.active
    # Delete leftover meshes
    for mesh in meshes:
        if mesh == joined_obj.data:
            continue
        bpy.data.meshes.remove(mesh)
    return joined_obj


def remove_unused_materials(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.ops.object.material_slot_remove_unused()

# MIT License

# Copyright (c) 2017 GiveMeAllYourCats

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# Code author: GiveMeAllYourCats
# Repo: https://github.com/michaeldegroot/cats-blender-plugin
# Edits by: GiveMeAllYourCats, Hotox


def remove_unused_vertex_groups_of_mesh(mesh):
    remove_count = 0
    mesh.update_from_editmode()

    vgroup_used = {i: False for i, k in enumerate(mesh.vertex_groups)}

    for v in mesh.data.vertices:
        for g in v.groups:
            if g.weight > 0.0:
                vgroup_used[g.group] = True

    for i, used in sorted(vgroup_used.items(), reverse=True):
        if not used:
            mesh.vertex_groups.remove(mesh.vertex_groups[i])
            remove_count += 1
    return remove_count


def get_selected_vertices(obj):
    mode = obj.mode
    if obj.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    # We need to switch from Edit mode to Object mode so the vertex selection gets updated (disgusting!)
    verts = [obj.matrix_world @ Vector((v.co.x, v.co.y, v.co.z))
             for v in obj.data.vertices if v.select]
    bpy.ops.object.mode_set(mode=mode)
    return verts


def get_selected_edit_vertices(mesh: bpy.types.Mesh) -> list[Vector]:
    """Get selected vertices of edit mode``mesh``."""
    bm = bmesh.from_edit_mesh(mesh)

    return [Vector(v.co) for v in bm.verts if v.select]


def find_parent(obj, parent_name):
    if obj.parent:
        if obj.parent.name == parent_name:
            return obj
        return find_parent(obj.parent, parent_name)
    else:
        return None


def find_child_by_type(parent, sollum_type):
    for obj in bpy.data.objects:
        if obj.parent == parent and obj.sollum_type == sollum_type:
            return obj


def build_tag_bone_map(armature):
    if armature is None:
        return None

    if armature.pose is None:
        return None

    tag_bone_map = {}
    for pose_bone in armature.pose.bones:
        tag_bone_map[pose_bone.bone.bone_properties.tag] = pose_bone.name

    return tag_bone_map


def build_name_bone_map(armature):
    if armature is None:
        return None

    if armature.pose is None:
        return None

    tag_bone_map = {}
    for pose_bone in armature.pose.bones:
        tag_bone_map[pose_bone.name] = pose_bone.bone.bone_properties.tag

    return tag_bone_map


def build_bone_map(armature):
    if armature is None:
        return None

    if armature.pose is None:
        return None

    tag_bone_map = {}
    for pose_bone in armature.pose.bones:
        tag_bone_map[pose_bone.bone.bone_properties.tag] = pose_bone

    return tag_bone_map


def get_armature_obj(armature):
    for obj in bpy.data.objects:
        if obj.data == armature:
            return obj


def get_children_recursive(obj) -> list[bpy.types.Object]:
    children = []

    if obj is None:
        return children

    if len(obj.children) < 1:
        return children

    for child in obj.children:
        children.append(child)
        if len(child.children) > 0:
            children.extend(get_children_recursive(child))

    return children


def get_object_with_children(obj):
    """Get the object including the whole child hierarchy"""
    objs = [obj]
    for child in get_children_recursive(obj):
        objs.append(child)
    return objs


def create_mesh_object(sollum_type: SollumType, name: str = None) -> bpy.types.Object:
    """Create a bpy mesh object of the given sollum type and link it to the scene."""
    name = name or SOLLUMZ_UI_NAMES[sollum_type]
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    obj.sollum_type = sollum_type
    bpy.context.collection.objects.link(obj)

    return obj


def create_empty_object(sollum_type: SollumType, name: str = None) -> bpy.types.Object:
    """Create a bpy empty object of the given sollum type and link it to the scene."""
    name = name or SOLLUMZ_UI_NAMES[sollum_type]
    obj = bpy.data.objects.new(name, None)
    obj.empty_display_size = 0
    obj.sollum_type = sollum_type
    bpy.context.collection.objects.link(obj)

    return obj
