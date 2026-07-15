from enum import Enum

import numpy as np
from bpy.types import (
    Attribute,
    Depsgraph,
    Mesh,
    Object,
)
from mathutils import Vector


class GrassBatchAttr(str, Enum):
    COLOR_AO = ".grass.color_ao"
    NORMAL_SCALE = ".grass.normal_scale"
    TEMPLATE_INDEX = ".grass.template_index"
    PARTITION_INDEX = ".grass.partition_index"

    @property
    def type(self):
        match self:
            case GrassBatchAttr.COLOR_AO:
                return "BYTE_COLOR"
            case GrassBatchAttr.NORMAL_SCALE:
                return "FLOAT_VECTOR"
            case GrassBatchAttr.TEMPLATE_INDEX | GrassBatchAttr.PARTITION_INDEX:
                return "INT"

    @property
    def domain(self):
        return "POINT"

    @property
    def default_value(self) -> object:
        match self:
            case GrassBatchAttr.COLOR_AO:
                return (1.0, 1.0, 1.0, 1.0)
            case GrassBatchAttr.NORMAL_SCALE:
                return Vector((0.0, 0.0, 0.0))
            case GrassBatchAttr.TEMPLATE_INDEX | GrassBatchAttr.PARTITION_INDEX:
                return 0
            case _:
                assert False, f"Default value not set for grass batch attribute '{self}'"


def mesh_add_grass_batch_attribute(mesh: Mesh, attr: GrassBatchAttr) -> Attribute:
    mesh_attr = mesh.attributes.get(attr, None)
    return mesh.attributes.new(attr, attr.type, attr.domain) if mesh_attr is None else mesh_attr


def mesh_has_grass_batch_attribute(mesh: Mesh, attr: GrassBatchAttr) -> bool:
    return attr in mesh.attributes


def mesh_get_grass_batch_attribute_values(mesh: Mesh, attr: GrassBatchAttr) -> np.ndarray:
    num = len(mesh.vertices)

    match attr.type:
        case "BYTE_COLOR":
            values = np.full((num, 4), attr.default_value, dtype=np.float32)
            prop_name = "color_srgb"
        case "FLOAT_VECTOR":
            values = np.full((num, 3), attr.default_value, dtype=np.float32)
            prop_name = "vector"
        case "INT":
            values = np.full(num, attr.default_value, dtype=np.int32)
            prop_name = "value"
        case _:
            assert False, f"Unhandled grass batch attribute type '{attr.type}'"

    mesh_attr = mesh.attributes.get(attr, None)
    if mesh_attr is not None:
        mesh_attr.data.foreach_get(prop_name, values.ravel())

    return values


def evaluated_grass_batch_instances_from_object(
    obj: Object, depsgrah: Depsgraph
) -> tuple[
    np.ndarray,  # Position
    np.ndarray,  # Color (XYZ) AO (W)
    np.ndarray,  # Normal (XY) - Scale (Z)
    np.ndarray,  # Template Indices
    np.ndarray,  # Partition Indices
]:
    """Caller must make sure all GrassBatchGen modifiers have preview disabled."""

    obj_eval = obj.evaluated_get(depsgrah)

    mesh_eval = obj_eval.to_mesh()
    try:
        num_verts = len(mesh_eval.vertices)

        # Read vertex positions
        positions = np.empty(num_verts * 3, dtype=np.float32)
        mesh_eval.vertices.foreach_get("co", positions)
        positions = positions.reshape(num_verts, 3)

        color_ao = mesh_get_grass_batch_attribute_values(mesh_eval, GrassBatchAttr.COLOR_AO)
        normal_scale = mesh_get_grass_batch_attribute_values(mesh_eval, GrassBatchAttr.NORMAL_SCALE)
        template_indices = mesh_get_grass_batch_attribute_values(mesh_eval, GrassBatchAttr.TEMPLATE_INDEX)
        partition_indices = mesh_get_grass_batch_attribute_values(mesh_eval, GrassBatchAttr.PARTITION_INDEX)

        return positions, color_ao, normal_scale, template_indices, partition_indices
    finally:
        obj_eval.to_mesh_clear()


MAX_GRASS_INSTANCES_PER_LIST = 1023
MAX_GRASS_LIST_HORIZONTAL_EXTENT = 256.0


def partition_grass_batch_instances(positions: np.ndarray, template_indices: np.ndarray) -> np.ndarray:
    n = len(positions)
    if n == 0:
        return np.zeros(0, dtype=np.int32)

    partition_ids = np.full(n, -1, dtype=np.int32)
    next_id = [0]
    for tidx in np.unique(template_indices):
        idx = np.flatnonzero(template_indices == tidx)
        _split_template_recursive(positions, idx, partition_ids, next_id)
    return partition_ids


def _split_template_recursive(
    positions: np.ndarray, indices: np.ndarray, partition_ids: np.ndarray, next_id: list[int]
):
    n = len(indices)
    if n == 0:
        return
    pts = positions[indices]
    pmin = pts.min(axis=0)
    pmax = pts.max(axis=0)
    extents = pmax - pmin
    fits_count = n <= MAX_GRASS_INSTANCES_PER_LIST
    fits_extent = extents[0] <= MAX_GRASS_LIST_HORIZONTAL_EXTENT and extents[1] <= MAX_GRASS_LIST_HORIZONTAL_EXTENT
    if fits_count and fits_extent:
        partition_ids[indices] = next_id[0]
        next_id[0] += 1
        return

    axis = 0 if extents[0] >= extents[1] else 1
    if extents[axis] > 0:
        centroid = pts[:, axis].mean()
        left_mask = pts[:, axis] < centroid
        if left_mask.any() and not left_mask.all():
            _split_template_recursive(positions, indices[left_mask], partition_ids, next_id)
            _split_template_recursive(positions, indices[~left_mask], partition_ids, next_id)
            return

    # Geometric split failed (points coincident on this axis): fall back to
    # an index-median split so the count constraint can still be satisfied.
    order = np.argsort(pts[:, axis], kind="stable")
    mid = n // 2
    if mid == 0:
        partition_ids[indices] = next_id[0]
        next_id[0] += 1
        return
    _split_template_recursive(positions, indices[order[:mid]], partition_ids, next_id)
    _split_template_recursive(positions, indices[order[mid:]], partition_ids, next_id)
