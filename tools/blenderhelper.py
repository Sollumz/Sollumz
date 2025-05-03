import re
import bpy
import bmesh
from mathutils import Matrix, Vector
from typing import Optional, Tuple

from ..sollumz_properties import SOLLUMZ_UI_NAMES, LODLevel

from ..sollumz_properties import SOLLUMZ_UI_NAMES, SollumType


def get_all_collections():
    return [bpy.context.scene.collection, *bpy.data.collections]


def remove_number_suffix(string: str):
    """Remove the .00# at that Blender puts at the end of object names."""
    match = re.search("\.[0-9]", string)

    if match is None:
        return string

    return string[:match.start()]


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
    bsdf, _ = find_bsdf_and_material_output(mat)
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
    try:
        return [Vector(v.co) for v in bm.verts if v.select]
    finally:
        bm.free()


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


def get_data_obj(data):
    if data is None:
        return None

    for obj in bpy.data.objects:
        if obj.data == data:
            return obj

    return None


def get_armature_obj(armature):
    return get_data_obj(armature)


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


# Sollumz types for which Object.hide_render should be set to false when created.
_types_to_hide_in_render = {
    SollumType.BOUND_BOX, SollumType.BOUND_SPHERE, SollumType.BOUND_CAPSULE, SollumType.BOUND_CYLINDER,
    SollumType.BOUND_DISC, SollumType.BOUND_PLANE, SollumType.BOUND_GEOMETRY, SollumType.BOUND_GEOMETRYBVH,
    SollumType.BOUND_COMPOSITE, SollumType.BOUND_POLY_BOX, SollumType.BOUND_POLY_CAPSULE,
    SollumType.BOUND_POLY_CYLINDER, SollumType.BOUND_POLY_SPHERE, SollumType.BOUND_POLY_TRIANGLE,

    SollumType.SHATTERMAP,

    SollumType.CHARACTER_CLOTH_MESH,
}


def create_blender_object(sollum_type: SollumType, name: Optional[str] = None, object_data: Optional[bpy.types.Mesh] = None) -> bpy.types.Object:
    """Create a bpy object of the given sollum type and link it to the scene."""
    name = name or SOLLUMZ_UI_NAMES[sollum_type]
    object_data = object_data or bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, object_data)
    obj.sollum_type = sollum_type
    obj.hide_render = sollum_type in _types_to_hide_in_render
    bpy.context.collection.objects.link(obj)

    return obj


def create_empty_object(sollum_type: SollumType, name: Optional[str] = None) -> bpy.types.Object:
    """Create a bpy empty object of the given sollum type and link it to the scene."""
    name = name or SOLLUMZ_UI_NAMES[sollum_type]
    obj = bpy.data.objects.new(name, None)
    obj.empty_display_size = 0
    obj.sollum_type = sollum_type
    obj.hide_render = sollum_type in _types_to_hide_in_render
    bpy.context.collection.objects.link(obj)

    return obj


def delete_hierarchy(obj: bpy.types.Object):
    for child in obj.children:
        delete_hierarchy(child)

    bpy.data.objects.remove(obj)


def add_armature_modifier(obj: bpy.types.Object, armature_obj: bpy.types.Object):
    mod: bpy.types.ArmatureModifier = obj.modifiers.new("skel", "ARMATURE")
    mod.object = armature_obj

    return mod


def add_child_of_bone_constraint(obj: bpy.types.Object, armature_obj: bpy.types.Object, target_bone: Optional[str] = None):
    """Add constraint to parent the object to a bone. Also sets target space and owner space so that parenting is evaluated properly.

    Note: we are using COPY_TRANSFORMS instead of CHILD_OF constraint because CHILD_OF does not behave as expected when
    ``obj`` is a child of the ``armature_obj`` hierarchy. It applies the parent transform and then the offset transform
    coming from the CHILD_OF constraint. Instead, we just want ``obj`` to use the bone transform directly.
    In previous versions, Sollumz used CHILD_OF but changing the target/owner space, which seemed to work but was
    possibly undefined behaviour as the target/owner space properties are not shown in the UI, unlike with other
    constraints. After Blender 4.2, this approach broke and we had to change to COPY_TRANSFORMS.
    """
    constraint = obj.constraints.new("COPY_TRANSFORMS")
    constraint.target = armature_obj
    if target_bone is not None:
        constraint.subtarget = target_bone
    set_child_of_constraint_space(constraint)
    return constraint


def set_child_of_constraint_space(constraint: bpy.types.CopyTransformsConstraint):
    """Set constraint target space and owner space such that it matches the behavior of bone parenting."""
    constraint.mix_mode = "BEFORE_FULL"
    constraint.target_space = "POSE"
    constraint.owner_space = "LOCAL"


def get_bone_pose_matrix(obj: bpy.types.Object) -> Matrix:
    """Get the 4x4 pose matrix of the bone set in the child of constraint. Returns identity matrix if not found."""
    pose_bone = get_child_of_pose_bone(obj)

    if pose_bone is None:
        return Matrix()

    return pose_bone.matrix


def get_pose_inverse(obj: bpy.types.Object) -> Matrix:
    """Get matrix that inverts the pose of the bone in the first child of constraint. Returns identity matrix if no bone is found."""
    bone = get_child_of_bone(obj)
    pose_bone = get_child_of_pose_bone(obj)

    if bone and pose_bone:
        return (bone.matrix_local.inverted() @ pose_bone.matrix).inverted()

    return Matrix()


def get_child_of_bone(obj: bpy.types.Object) -> Optional[bpy.types.Bone]:
    """Get the bone linked to the first armature child of constraint in obj. Returns None if not found."""
    constraint = get_child_of_constraint(obj)

    if constraint is None:
        return None

    armature = constraint.target.data

    return armature.bones.get(constraint.subtarget)


def get_child_of_pose_bone(obj: bpy.types.Object) -> Optional[bpy.types.PoseBone]:
    """Get the pose bone linked to the first armature child of constraint in obj. Returns None if not found."""
    constraint = get_child_of_constraint(obj)

    if constraint is None:
        return None

    armature = constraint.target

    return armature.pose.bones.get(constraint.subtarget)


def get_child_of_constraint(obj: bpy.types.Object) -> Optional[bpy.types.CopyTransformsConstraint]:
    """Get first child of constraint with armature target and bone subtarget set. Returns None if not found."""
    for constraint in obj.constraints:
        if constraint.type != "COPY_TRANSFORMS":
            continue

        if constraint.target and constraint.target.type == "ARMATURE" and constraint.subtarget:
            return constraint


def get_evaluated_obj(obj: bpy.types.Object) -> bpy.types.Object:
    """Evaluate the object and it's mesh."""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    obj_eval = obj.evaluated_get(depsgraph)

    return obj_eval


def parent_objs(objs: list[bpy.types.Object], parent_obj: bpy.types.Object):
    for obj in objs:
        obj.parent = parent_obj


def lod_level_enum_flag_prop_factory(default: set[LODLevel] = None):
    """Returns an EnumProperty as a flag with all LOD levels"""
    default = default or {LODLevel.HIGH,
                          LODLevel.MEDIUM, LODLevel.LOW, LODLevel.VERYLOW}
    return bpy.props.EnumProperty(
        items=(
            (LODLevel.VERYHIGH.value,
             SOLLUMZ_UI_NAMES[LODLevel.VERYHIGH], SOLLUMZ_UI_NAMES[LODLevel.VERYHIGH]),
            (LODLevel.HIGH.value,
             SOLLUMZ_UI_NAMES[LODLevel.HIGH], SOLLUMZ_UI_NAMES[LODLevel.HIGH]),
            (LODLevel.MEDIUM.value,
             SOLLUMZ_UI_NAMES[LODLevel.MEDIUM], SOLLUMZ_UI_NAMES[LODLevel.MEDIUM]),
            (LODLevel.LOW.value,
             SOLLUMZ_UI_NAMES[LODLevel.LOW], SOLLUMZ_UI_NAMES[LODLevel.LOW]),
            (LODLevel.VERYLOW.value,
             SOLLUMZ_UI_NAMES[LODLevel.VERYLOW], SOLLUMZ_UI_NAMES[LODLevel.VERYLOW]),
        ), options={"ENUM_FLAG"}, default=default)


def tag_redraw(context: bpy.types.Context, space_type: str = "PROPERTIES", region_type: str = "WINDOW"):
    """Redraw all panels in the given space_type and region_type"""
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.spaces[0].type == space_type:
                for region in area.regions:
                    if region.type == region_type:
                        region.tag_redraw()


def find_bsdf_and_material_output(material: bpy.types.Material) -> Tuple[bpy.types.ShaderNodeBsdfPrincipled, bpy.types.ShaderNodeOutputMaterial]:
    material_output = None
    bsdf = None
    for node in material.node_tree.nodes:
        if isinstance(node, bpy.types.ShaderNodeOutputMaterial):
            material_output = node
        elif isinstance(node, bpy.types.ShaderNodeBsdfPrincipled):
            bsdf = node

    return bsdf, material_output
