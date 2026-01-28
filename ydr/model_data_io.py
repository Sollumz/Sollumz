"""Reads DrawableModel mesh data into numpy arrays."""
from collections import defaultdict
import numpy as np
from numpy.typing import NDArray
from typing import NamedTuple, Tuple

from ..sollumz_properties import LODLevel
from szio.gta5 import (
    AssetDrawable,
    Model,
    Geometry,
    SkelBone,
    LodLevel as IOLodLevel,
    STANDARD_VERTEX_ATTR_DTYPES,
)


class MeshData(NamedTuple):
    vert_arr: NDArray
    ind_arr: NDArray[np.uint]
    mat_inds: NDArray[np.uint]


class ModelData(NamedTuple):
    mesh_data_lods: dict[LODLevel, MeshData]
    # Used for storing drawable model properties
    lods: dict[LODLevel, Model]
    bone_index: int


def get_model_data(drawable: AssetDrawable, hi_drawable: AssetDrawable | None) -> list[ModelData]:
    """Get ModelData for each DrawableModel."""
    model_datas: list[ModelData] = []
    models = get_lod_models(drawable, hi_drawable)
    for (bone_index, _), model_lods in models.items():
        model_data = ModelData(
            mesh_data_lods={
                lod_level: mesh_data_from_model(model) for lod_level, model in model_lods.items()
            },
            lods={
                lod_level: model for lod_level, model in model_lods.items()
            },
            bone_index=bone_index
        )

        model_datas.append(model_data)

    return model_datas


def get_model_data_split_by_group(drawable: AssetDrawable, hi_drawable: AssetDrawable | None) -> list[ModelData]:
    model_datas = get_model_data(drawable, hi_drawable)

    return [split_data for model_data in model_datas for split_data in split_model_by_group(model_data, drawable.skeleton.bones)]


def split_model_by_group(model_data: ModelData, bones: list[SkelBone]) -> list[ModelData]:
    """Split ModelData by vertex group"""
    model_datas: list[ModelData] = []
    mesh_data_by_bone: dict[int, dict[LODLevel, MeshData]] = defaultdict(dict)

    for lod_level, mesh_data in model_data.mesh_data_lods.items():
        is_skinned = "BlendWeights" in mesh_data.vert_arr.dtype.names

        if not is_skinned:
            mesh_data_by_bone[model_data.bone_index][lod_level] = mesh_data
            continue

        for i, face_inds in get_group_face_inds(mesh_data, bones).items():
            vert_arr, ind_arr = get_faces_subset(mesh_data.vert_arr, mesh_data.ind_arr, face_inds)

            group_mesh_data = MeshData(
                vert_arr,
                ind_arr,
                mesh_data.mat_inds[face_inds]
            )

            mesh_data_by_bone[i][lod_level] = group_mesh_data

    for i, mesh_data_lods in mesh_data_by_bone.items():
        model_datas.append(ModelData(
            mesh_data_lods=mesh_data_lods,
            lods=model_data.lods,
            bone_index=i
        ))

    return model_datas


def get_group_face_inds(mesh_data: MeshData, bones: list[SkelBone]):
    """Get face indices split by vertex group. Overlapping vertex groups are merged
    based on bone parenting."""
    group_inds: dict[int, set] = defaultdict(list)

    blend_inds = mesh_data.vert_arr["BlendIndices"]
    weights = mesh_data.vert_arr["BlendWeights"]

    num_tris = int(len(mesh_data.ind_arr) / 3)
    faces = mesh_data.ind_arr.reshape((num_tris, 3))

    # Get all the BlendIndices and BlendWeights in each face
    face_blend_inds = blend_inds[faces]
    face_weights = weights[faces]
    # Any given face could be in a maximum of 12 vertex groups (3 verts * 4 possible groups per vert)
    face_blend_inds = face_blend_inds.reshape((num_tris, 12))
    face_weights = face_weights.reshape((num_tris, 12))

    # Mapping of blend indices in each face where (BlendIndex, BlendWeight) pairs are not (0, 0)
    blend_inds_mask = np.logical_or(face_blend_inds != 0, face_weights != 0)
    # Maps group indices to the group index of the object they should be parented to
    parent_map = get_group_parent_map(face_blend_inds, bones)

    for i, all_blend_inds in enumerate(face_blend_inds):
        # Valid BlendIndices are those where either the index or weight is not 0
        valid_blend_inds = all_blend_inds[blend_inds_mask[i]]

        if valid_blend_inds.size == 0:
            group_ind = 0
        else:
            group_ind = parent_map[valid_blend_inds[0]]

        group_inds[group_ind].append(i)

    return {i: np.array(face_inds, dtype=np.uint32) for i, face_inds in group_inds.items()}


def get_group_parent_map(face_blend_inds: NDArray[np.uint32], bones: list[SkelBone]) -> dict[int, set]:
    """Get a mapping of each blend index to the blend index of the object they should be parented to."""
    # Mapping of each blend index to blend indices with overlapping faces
    group_relations: dict[int, set[int]] = defaultdict(set)
    parent_map: dict[int, int] = {}
    group_inds = np.unique(face_blend_inds)

    for group_ind in group_inds:
        occurences = np.any(face_blend_inds == group_ind, axis=1)
        related_groups = np.unique(face_blend_inds[occurences].flatten())
        # Ignore 0 group because all vertex groups are a part of group 0
        group_relations[group_ind] = [
            i for i in related_groups if i != 0 and i != group_ind]

    for blend_ind, blend_inds in group_relations.items():
        # blend_ind does not overlap with any other vertex groups, so it can be created as its own object
        if not blend_inds:
            parent_map[blend_ind] = blend_ind
            continue

        # Find a parent bone that is shared between all blend_inds. All faces with blend_inds vertex groups will be
        # created as a single object
        parent_map[blend_ind] = find_common_bone_parent(blend_inds, bones)

    return parent_map


def find_common_bone_parent(bone_inds: list[int], bones: list[SkelBone]) -> int:
    bone_parents = [get_all_bone_parents(i, bones) for i in bone_inds if bones[i].parent_index > 0]

    if not bone_parents:
        return 0

    common_bones = bone_parents[0]

    for array in bone_parents[1:]:
        common_bones = np.intersect1d(common_bones, array)

    if len(common_bones) == 0:
        return 0

    # Get the parent thats highest in the bone hierarchy
    return np.min(common_bones)


def get_all_bone_parents(bone_ind: int, bones: list[SkelBone]) -> list[int]:
    parent_inds = []
    current_bone_ind = bone_ind

    while bones[current_bone_ind].parent_index > 0:
        current_bone_ind = bones[current_bone_ind].parent_index
        parent_inds.append(current_bone_ind)

    return parent_inds


def get_faces_subset(vert_arr: NDArray, ind_arr: NDArray[np.uint32], face_inds: NDArray[np.uint32]) -> MeshData:
    """Get subset of vertex array and index array by face."""
    # First get valid faces in the subset in case the new subset of indices is not divisble by 3.
    num_tris = int(len(ind_arr) / 3)
    faces = ind_arr.reshape((num_tris, 3))

    subset_inds = faces[face_inds].flatten()

    # Map old vert inds to new vert inds
    # TODO: Remap inds using numpy?
    vert_inds_map: dict[int, int] = {}
    vert_inds = []
    new_inds = []

    for vert_ind in subset_inds:
        if vert_ind in vert_inds_map:
            new_inds.append(vert_inds_map[vert_ind])
        else:
            new_vert_ind = len(vert_inds_map)
            new_inds.append(new_vert_ind)
            vert_inds_map[vert_ind] = new_vert_ind
            vert_inds.append(vert_ind)

    new_vert_arr = vert_arr[vert_inds]
    new_ind_arr = np.array(new_inds, dtype=np.uint32)

    return new_vert_arr, new_ind_arr


def get_lod_models(drawable: AssetDrawable, hi_drawable: AssetDrawable | None) -> dict[(int, int), dict[LODLevel, Model]]:
    """Gets mapping of LOD levels for each DrawableModel, keyed by a (bone index, model per-bone ID) tuple."""
    #
    # NOTE: we assumme that models attached to the same bone appear in the same order at different LODs. This doesn't
    #       quite work when not all models have the same number of LOD levels.
    #
    # For example:
    #   A model could have the following hierarchy in Blender:
    #     Drawable
    #       Dr. Model #0 -> LODs High = A, Med = D
    #       Dr. Model #1 -> LODs High = B, Med = -
    #       Dr. Model #2 -> LODs High = C, Med = E
    #   When exported the XML will have something like this:
    #     DrawableModelsHigh = [A, B, C]
    #     DrawableModelsMedium = [D, E]
    #   If we import back that XML, we have to decide how to connect the models in the different LOD arrays. There is
    #   nothing in the XML that connects different LOD models to form a full "model", the game doesn't need it, the game
    #   just switches between which LOD array to render.
    #
    #   With our approach, the imported drawable will look like this in Blender. Notice that now model #1 has the medium
    #   LOD of model #2.
    #     Drawable
    #       Dr. Model #0 -> LODs High = A, Med = D
    #       Dr. Model #1 -> LODs High = B, Med = E
    #       Dr. Model #2 -> LODs High = C, Med = -
    #
    #   This shouldn't be much of an issue as it doesn't affect how it looks in-game when exported again. Just may
    #   confuse the user a bit at first.
    #   This would only be an issue if the LODs where attached to different bones but ended placed in the same drawable
    #   model when imported, but we handle this case.
    #
    models_map: dict[(int, int), dict[LODLevel, Model]] = defaultdict(dict)

    def _process_lod(lod_level: LODLevel, models: list[Model]):
        model_count_per_bone = defaultdict(int)
        for model in models:
            bone_index = model.bone_index
            # We use `model_per_bone_id` to differentiate multiple models attached to the same bone
            model_per_bone_id = model_count_per_bone[bone_index]
            model_count_per_bone[bone_index] += 1
            models_map[(bone_index, model_per_bone_id)][lod_level] = model

    if hi_drawable is not None:
        hi_models = hi_drawable.models.get(IOLodLevel.HIGH)
        _process_lod(LODLevel.VERYHIGH, hi_models)

    models_by_lod = drawable.models
    for lod_level, models in models_by_lod.items():
        lod_level = LODLevel.from_io(lod_level)
        _process_lod(lod_level, models)

    return models_map


def mesh_data_from_model(model: Model) -> MeshData:
    # geoms = get_valid_geoms(model_xml)
    geoms = model.geometries

    return MeshData(
        ind_arr=get_model_joined_ind_arr(geoms),
        vert_arr=get_model_joined_vert_arr(geoms),
        mat_inds=get_model_poly_mat_inds(geoms)
    )


def get_model_joined_ind_arr(geoms: list[Geometry]) -> NDArray[np.uint32]:
    """Get joined indices array for the model."""
    ind_arrs: list[NDArray[np.uint32]] = []
    num_verts = 0

    for geom in geoms:
        # Make sure indices are at least uint32 (in native format they are stored as uint16, while in CWXML they are
        # already parsed as uint32) to avoid integer overflows when adding num_verts below
        ind_arr = geom.index_buffer.astype(np.uint32, copy=False)

        if num_verts > 0:
            ind_arr += num_verts

        ind_arrs.append(ind_arr)
        num_verts += len(geom.vertex_buffer)

    return np.concatenate(ind_arrs)


def get_model_joined_vert_arr(geoms: list[Geometry]) -> NDArray:
    arr_dtype = get_model_vert_buffer_dtype(geoms)
    vert_arrs: list[NDArray] = []

    for geom in geoms:
        vert_arr = geom.vertex_buffer

        if vert_arr is None:
            continue

        geom_vert_arr = np.zeros(len(vert_arr), dtype=arr_dtype)

        for name in vert_arr.dtype.names:
            geom_vert_arr[name] = vert_arr[name]

        if len(geom.bone_ids) > 0:
            apply_bone_ids(geom_vert_arr, geom.bone_ids)

        vert_arrs.append(geom_vert_arr)

    return np.concatenate(vert_arrs)


def get_model_vert_buffer_dtype(geoms: list[Geometry]) -> np.dtype:
    """Get the dtype of the structured array of the joined geometry vertex buffers."""

    used_attrs: set[Tuple] = set(
        name
        for geom in geoms
        for name in geom.vertex_buffer.dtype.names
    )
    arr_dtype = []

    for attr_name, attr_dtype in STANDARD_VERTEX_ATTR_DTYPES.items():
        if attr_name not in used_attrs:
            continue

        arr_dtype.append(attr_dtype)

    return np.dtype(arr_dtype)


def apply_bone_ids(vert_arr: NDArray, bone_ids: NDArray[np.uint32]):
    from .model_data import apply_bone_ids as impl
    return impl(vert_arr, bone_ids)


def get_model_poly_mat_inds(geoms: list[Geometry]):
    mat_ind_arrs = []

    for geom in geoms:
        num_tris = round(len(geom.index_buffer) / 3)
        mat_inds = np.full((num_tris,), geom.shader_index)

        mat_ind_arrs.append(mat_inds)

    return np.concatenate(mat_ind_arrs)
