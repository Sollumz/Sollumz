import bpy
import traceback
import time
from typing import Optional
from abc import abstractmethod
from mathutils import Matrix

from .sollumz_properties import SollumType
from .tools.blenderhelper import get_bone_pose_matrix


from .sollumz_preferences import get_export_settings
from .tools.blenderhelper import get_children_recursive, get_object_with_children
from .sollumz_properties import BOUND_TYPES, SollumType, MaterialType, LODLevel


class SOLLUMZ_OT_base:
    # Deprecated
    bl_options = {"UNDO"}
    bl_action = "do"
    bl_showtime = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.messages = []

    @abstractmethod
    def run(self, context):
        pass

    def execute(self, context):
        start = time.time()
        try:
            result = self.run(context)
        except:
            result = False
            self.error(
                f"Error occured running operator : {self.bl_idname} \n {traceback.format_exc()}")
        end = time.time()

        if self.bl_showtime and result == True:
            self.message(
                f"{self.bl_label} took {round(end - start, 3)} seconds to {self.bl_action}.")

        if len(self.messages) > 0:
            self.message("\n".join(self.messages))

        if result:
            return {"FINISHED"}
        else:
            return {"CANCELLED"}

    def message(self, msg):
        self.report({"INFO"}, msg)

    def warning(self, msg):
        self.report({"WARNING"}, msg)

    def error(self, msg):
        self.report({"ERROR"}, msg)


def set_object_collection(obj):
    target = bpy.context.view_layer.active_layer_collection.collection
    objs = get_object_with_children(obj)
    for obj in objs:
        if len(obj.users_collection) > 0:
            collection = obj.users_collection[0]
            collection.objects.unlink(obj)
        target.objects.link(obj)


def get_sollumz_objects_from_objects(objs, sollum_type):
    robjs = []
    for obj in objs:
        if obj.sollum_type in sollum_type:
            robjs.append(obj)
        for child in obj.children:
            if child.sollum_type in sollum_type:
                robjs.append(child)
    return robjs


def has_embedded_textures(obj):
    for mat in get_sollumz_materials(obj):
        nodes = mat.node_tree.nodes
        for node in nodes:
            if isinstance(node, bpy.types.ShaderNodeTexImage):
                if node.texture_properties.embedded == True:
                    return True
    return False


def has_collision(obj):
    for child in get_children_recursive(obj):
        if child.sollum_type in BOUND_TYPES:
            return True
    return False


def duplicate_object_with_children(obj):
    objs = get_object_with_children(obj)
    new_objs = []
    for o in objs:
        new_obj = o.copy()
        new_obj.animation_data_clear()
        new_objs.append(new_obj)
    new_objs[0].parent = None
    for i in range(1, len(objs)):
        if objs[i].parent:
            new_objs[i].parent = new_objs[objs.index(objs[i].parent)]
    for new_obj in new_objs:
        bpy.context.scene.collection.objects.link(new_obj)
        for constraint in new_obj.constraints:
            if hasattr(constraint, "target") and constraint.target in objs:
                constraint.target = new_objs[objs.index(constraint.target)]
    return new_objs[0]


def find_sollumz_parent(obj: bpy.types.Object, parent_type: Optional[SollumType] = None) -> bpy.types.Object | None:
    """Find parent Fragment or Drawable if one exists. Returns None otherwise."""
    parent_types = [SollumType.FRAGMENT, SollumType.DRAWABLE, SollumType.DRAWABLE_DICTIONARY,
                    SollumType.CLIP_DICTIONARY, SollumType.YMAP, SollumType.BOUND_COMPOSITE]

    if parent_type is not None and obj.parent is not None and obj.parent.sollum_type == parent_type:
        return obj.parent

    if obj.parent is None and obj.sollum_type in parent_types:
        return obj

    if obj.parent is None:
        return None

    return find_sollumz_parent(obj.parent, parent_type)


def get_sollumz_materials(obj: bpy.types.Object):
    """Get all Sollumz materials used by ``drawable_obj``."""
    materials: list[bpy.types.Material] = []
    used_materials: dict[bpy.types.Material, bool] = {}

    for child in get_children_recursive(obj):
        if child.sollum_type != SollumType.DRAWABLE_MODEL:
            continue

        lods = child.sz_lods
        for lod_level in LODLevel:
            lod = lods.get_lod(lod_level)
            lod_mesh = lod.mesh
            if lod_mesh is None:
                continue

            mats = lod_mesh.materials

            for mat in mats:
                if mat.sollum_type != MaterialType.SHADER:
                    continue

                if mat not in used_materials:
                    materials.append(mat)
                    used_materials[mat] = True

    return sorted(materials, key=lambda m: m.shader_properties.index)


def get_export_transforms_to_apply(obj: bpy.types.Object):
    """Get final transforms for a mesh object that should be directly applied to vertices upon export."""
    parent_inverse = get_parent_inverse(obj)
    bone_inverse = get_bone_pose_matrix(obj).inverted()

    # Apply all transforms except any transforms from the current pose, and any parent transforms (depends on "Apply Parent Transforms" option)
    return parent_inverse @ bone_inverse @ obj.matrix_world


def get_parent_inverse(obj: bpy.types.Object) -> Matrix:
    """Get the parent transforms to unapply based on the "Apply Parent Transforms" option"""
    parent_obj = find_sollumz_parent(obj)

    if obj.matrix_world.is_identity or parent_obj is None:
        return Matrix()

    if get_export_settings().apply_transforms:
        if parent_obj.sollum_type == SollumType.BOUND_COMPOSITE:
            return Matrix()
        # Even when apply transforms is enabled, we still don't want to apply location, as Drawables/Fragments should always start from 0,0,0
        return Matrix.Translation(parent_obj.matrix_world.translation).inverted()

    return parent_obj.matrix_world.inverted()
