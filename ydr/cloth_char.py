import numpy as np
from numpy.typing import NDArray
from bpy.types import (
    Object,
    Material,
    Mesh,
    MeshVertex,
    VertexGroupElement,
)
from typing import Optional
from mathutils import (
    Vector,
    Matrix,
)
from ..cwxml.shader import ShaderManager
from ..cwxml.drawable import (
    Drawable,
)
from ..cwxml.cloth import (
    CharacterCloth,
    CharacterClothBinding,
    ClothDictionary,
    VerletClothEdge,
)
from ..tools.blenderhelper import (
    get_evaluated_obj,
    remove_number_suffix,
    get_child_of_bone,
)
from ..tools.meshhelper import get_tangent_required
from ..sollumz_properties import (
    SollumType,
    LODLevel,
    SOLLUMZ_UI_NAMES,
)
from ..ybn.ybnexport import (
    get_scale_to_apply_to_bound,
    create_composite_xml,
)
from .ydrexport import (
    get_bone_index,
    create_model_xml,
    append_model_xml,
    set_drawable_xml_extents,
)
from .. import logger

CLOTH_CHAR_MAX_VERTICES = 254


def cloth_char_find_mesh_objects(drawable_obj: Object, silent: bool = False) -> list[Object]:
    """Returns a list of mesh objects that use a cloth material in the fragment. If not silent, warns the user if a mesh
    has a cloth material but also other materials or multiple cloth materials.
    """
    mesh_objs = []
    for obj in drawable_obj.children_recursive:
        if obj.sollum_type != SollumType.CHARACTER_CLOTH_MESH or obj.type != "MESH":
            continue

        # Character cloth mesh are not supposed to have any materials, so don't need to check anything else
        mesh_objs.append(obj)

    return mesh_objs


def cloth_char_find_bounds(char_cloth_obj: Object) -> list[Object]:
    composite_objs = []
    for obj in char_cloth_obj.children:
        if obj.sollum_type != SollumType.BOUND_COMPOSITE:
            continue

        composite_objs.append(obj)

    return composite_objs


def cloth_char_export(
    drawable_obj: Object,
    drawable_xml: Drawable,
    materials: list[Material],
    controller_name: str
) -> Optional[CharacterCloth]:
    cloth_objs = cloth_char_find_mesh_objects(drawable_obj)
    if not cloth_objs:
        return None

    cloth_obj = cloth_objs[0]
    if len(cloth_objs) > 1:
        other_cloth_objs = cloth_objs[1:]
        other_cloth_objs_names = [f"'{o.name}'" for o in other_cloth_objs]
        other_cloth_objs_names = ", ".join(other_cloth_objs_names)
        logger.warning(
            f"Drawable '{drawable_obj.name}' has multiple character cloth meshes! "
            f"Only a single cloth per drawable is supported, mesh '{cloth_obj.name}' will be used.\n"
            f"The following cloth meshes will be ignored: {other_cloth_objs_names}."
        )

    cloth_bounds_objs = cloth_char_find_bounds(cloth_obj)
    cloth_bounds_obj = cloth_bounds_objs[0]
    if len(cloth_bounds_objs) > 1:
        other_cloth_bounds_objs = cloth_bounds_objs[1:]
        other_cloth_bounds_objs_names = [f"'{o.name}'" for o in other_cloth_bounds_objs]
        other_cloth_bounds_objs_names = ", ".join(other_cloth_bounds_objs_names)
        logger.warning(
            f"Character cloth mesh '{cloth_obj.name}' has multiple bound composites! "
            f"Only a single bound composite per cloth mesh is supported, bound composite '{cloth_bounds_obj.name}' "
            "will be used.\n"
            f"The following bound composites will be ignored: {other_cloth_bounds_objs_names}."
        )

    invalid_bounds = [
        c for c in cloth_bounds_obj.children
        if c.sollum_type != SollumType.BOUND_CAPSULE
    ]
    if invalid_bounds:
        invalid_bounds_names = [f"'{o.name}'" for o in invalid_bounds]
        invalid_bounds_names = ", ".join(invalid_bounds_names)
        logger.warning(
            f"Character cloth bounds '{cloth_bounds_obj.name}' has bounds with unsupported types! "
            f"Only {SOLLUMZ_UI_NAMES[SollumType.BOUND_CAPSULE]} type is supported.\n"
            f"The following bounds are unsupported: {invalid_bounds_names}."
        )

    from .cloth import mesh_get_cloth_attribute_values, mesh_has_cloth_attribute, ClothAttr

    char_cloth = CharacterCloth()
    char_cloth.name = remove_number_suffix(drawable_obj.name)
    bounds_to_index = {}
    char_cloth.bounds = create_composite_xml(cloth_bounds_obj, out_child_obj_to_index=bounds_to_index)
    char_cloth.parent_matrix = Matrix.Identity(4)  # TODO(cloth): char cloth parent matrix
    # char_cloth.poses = ... # TODO(cloth): char cloth poses

    bounds_bone_ids = [None] * len(bounds_to_index)
    for bound_obj, bound_index in bounds_to_index.items():
        bone = get_child_of_bone(bound_obj)
        if bone is None:
            logger.warning(
                f"Character cloth bound '{bound_obj.name}' is not attached to a bone! "
                "Attach it to a bone via a Copy Transforms constraint."
            )
            bounds_bone_ids[bound_index] = 0
        else:
            bounds_bone_ids[bound_index] = bone.bone_properties.tag

        # Make bound transform relative to its bone
        # TODO(cloth): refactor/optimize this, mostly copied from yftexport

        def _get_bone_transforms(bone):
            return Matrix.LocRotScale(bone.translation, bone.rotation, bone.scale)
        bone_transforms = {}
        bones = drawable_xml.skeleton.bones
        for b in bones:
            transforms = _get_bone_transforms(b)
            if b.parent_index != -1:
                parent_transforms = bone_transforms[bones[b.parent_index].tag]
                transforms = parent_transforms @ transforms

            bone_transforms[b.tag] = transforms

        bone_transform = bone_transforms[bone.bone_properties.tag]
        bone_inv = bone_transform.inverted()

        bound_xml = char_cloth.bounds.children[bound_index]
        bound_xml.composite_transform = bound_xml.composite_transform @ bone_inv.transposed()

    char_cloth.bounds_bone_ids = bounds_bone_ids
    char_cloth.bounds_bone_indices = None  # indices are not needed, the game converts the IDs to indices when loading the cloth

    cloth_obj_eval = get_evaluated_obj(cloth_obj)
    cloth_mesh = cloth_obj_eval.to_mesh()
    cloth_mesh.calc_loop_triangles()

    num_vertices = len(cloth_mesh.vertices)
    if num_vertices > CLOTH_CHAR_MAX_VERTICES:
        logger.error(
            f"Drawable '{drawable_obj.name}' has cloth with too many vertices! "
            f"The maximum is {CLOTH_CHAR_MAX_VERTICES} vertices but cloth mesh '{cloth_obj.name}' has "
            f"{num_vertices} vertices.\n"
            f"Cloth won't be exported!"
        )
        return None

    pinned = np.array(mesh_get_cloth_attribute_values(cloth_mesh, ClothAttr.PINNED)) != 0
    num_pinned = np.sum(pinned)

    mesh_to_cloth_vertex_map = [None] * num_vertices
    cloth_to_mesh_vertex_map = [None] * num_vertices
    vertices = [None] * num_vertices
    normals = [None] * num_vertices
    for v in cloth_mesh.vertices:
        vi = v.index
        vertices[vi] = Vector(v.co)
        normals[vi] = Vector(v.normal)
        mesh_to_cloth_vertex_map[vi] = vi
        cloth_to_mesh_vertex_map[vi] = vi

    cloth_pin_index = 0
    for v in cloth_mesh.vertices:
        if pinned[v.index]:
            if v.index != cloth_pin_index:
                # Swap vertices so the pinned vertices are placed at the start of the array
                vA = vertices[cloth_pin_index]
                vB = vertices[v.index]
                nA = normals[cloth_pin_index]
                nB = normals[v.index]

                vertices[cloth_pin_index] = vB
                vertices[v.index] = vA
                normals[cloth_pin_index] = nB
                normals[v.index] = nA

                mesh_to_cloth_vertex_map[cloth_to_mesh_vertex_map[cloth_pin_index]] = mesh_to_cloth_vertex_map[v.index]
                cloth_to_mesh_vertex_map[v.index] = cloth_to_mesh_vertex_map[cloth_pin_index]

                mesh_to_cloth_vertex_map[v.index] = cloth_pin_index
                cloth_to_mesh_vertex_map[cloth_pin_index] = v.index

            cloth_pin_index += 1

    triangles = cloth_mesh.loop_triangles

    controller = char_cloth.controller
    controller.name = controller_name
    controller.flags = 2  # owns bridge
    # TODO(cloth): all vanilla char cloths have these same values but we could allow customizing them
    controller.pin_radius_scale = 1.0
    controller.pin_radius_threshold = 0.04
    controller.wind_scale = 1.0
    controller.vertices = vertices
    bridge = controller.bridge
    bridge.vertex_count_high = num_vertices
    # TODO(cloth): multiple pin radius sets support
    if mesh_has_cloth_attribute(cloth_mesh, ClothAttr.PIN_RADIUS):
        pin_radius = mesh_get_cloth_attribute_values(cloth_mesh, ClothAttr.PIN_RADIUS)
        bridge.pin_radius_high = [pin_radius[mi] for mi in cloth_to_mesh_vertex_map]
    else:
        bridge.pin_radius_high = None
    vertex_weights = mesh_get_cloth_attribute_values(cloth_mesh, ClothAttr.VERTEX_WEIGHT)
    inflation_scale = mesh_get_cloth_attribute_values(cloth_mesh, ClothAttr.INFLATION_SCALE)
    bridge.vertex_weights_high = [vertex_weights[mi] for mi in cloth_to_mesh_vertex_map]
    bridge.inflation_scale_high = [inflation_scale[mi] for mi in cloth_to_mesh_vertex_map]
    bridge.display_map_high = mesh_to_cloth_vertex_map
    # just need to allocate space for the pinnable list, unused
    bridge.pinnable_list = [0] * int(np.ceil(num_vertices / 32))

    force_transform = mesh_get_cloth_attribute_values(cloth_mesh, ClothAttr.FORCE_TRANSFORM)
    if (force_transform != 0).any():
        logger.warning(
            f"Character cloth mesh '{cloth_obj.name}' has {ClothAttr.FORCE_TRANSFORM.label} attribute, but this "
            "attribute is not supported in character cloth and will be ignored! Only fragment cloth support it."
        )

    def _create_verlet_edge(mesh_v0: int, mesh_v1: int) -> VerletClothEdge:
        verlet_edge = VerletClothEdge()
        verlet_edge.vertex0 = mesh_to_cloth_vertex_map[mesh_v0]
        verlet_edge.vertex1 = mesh_to_cloth_vertex_map[mesh_v1]
        verlet_edge.length_sqr = Vector(vertices[verlet_edge.vertex0] -
                                        vertices[verlet_edge.vertex1]).length_squared
        verlet_edge.weight0 = 0.0 if pinned[mesh_v0] else 1.0 if pinned[mesh_v1] else 0.5
        verlet_edge.compression_weight = 0.25  # TODO(cloth): compression_weight
        return verlet_edge

    indices = [None] * (len(triangles) * 3)
    edges = []
    edges_added = set()
    for tri in triangles:
        v0, v1, v2 = tri.vertices
        indices[tri.index * 3 + 0] = v0
        indices[tri.index * 3 + 1] = v1
        indices[tri.index * 3 + 2] = v2
        for edge_v0, edge_v1 in ((v0, v1), (v1, v2), (v2, v0)):
            if (edge_v0, edge_v1) in edges_added or (edge_v1, edge_v0) in edges_added:
                continue

            if pinned[edge_v0] and pinned[edge_v1]:
                continue

            verlet_edge = _create_verlet_edge(edge_v0, edge_v1)
            edges.append(verlet_edge)
            edges_added.add((edge_v0, edge_v1))

    # Look for loose edges (not part of any triangle), these work as additional edges to keep the shape/structure
    # of the object, stored in the custom edges array
    custom_edges = []
    for edge in cloth_mesh.edges:
        v0, v1 = edge.vertices
        if (v0, v1) in edges_added or (v1, v0) in edges_added:
            continue

        if pinned[v0] and pinned[v1]:
            continue

        verlet_edge = _create_verlet_edge(v0, v1)
        custom_edges.append(verlet_edge)
        edges_added.add((v0, v1))

    del edges_added

    from .cloth_env import _cloth_sort_verlet_edges
    edges = _cloth_sort_verlet_edges(edges)
    custom_edges = _cloth_sort_verlet_edges(custom_edges)

    controller.indices = indices
    verlet = controller.cloth_high
    verlet.vertex_positions = vertices
    verlet.vertex_normals = normals
    verlet.bb_min = Vector(np.min(vertices, axis=0))
    verlet.bb_max = Vector(np.max(vertices, axis=0))
    verlet.switch_distance_up = 9999.0
    verlet.switch_distance_down = 9999.0
    verlet.flags = 0
    verlet.dynamic_pin_list_size = 6  # TODO(cloth): what determines the dynamic pin list size?
    verlet.cloth_weight = 1.0  # TODO(cloth): cloth weight
    verlet.edges = edges
    verlet.pinned_vertices_count = num_pinned
    verlet.custom_edges = custom_edges
    verlet.bounds = None  # char cloth doesn't have embedded world bounds

    # Cloth vertex bindings to bones
    bind_weights, bind_indices, bind_bone_indices = _cloth_char_get_bindings(cloth_mesh, cloth_obj_eval, drawable_obj)
    bind_bone_ids = [drawable_obj.data.bones[i].bone_properties.tag for i in bind_bone_indices]
    bindings = [None] * num_vertices
    for i in range(num_vertices):
        binding = CharacterClothBinding()
        binding.weights = Vector(bind_weights[i])
        binding.indices = Vector(bind_indices[i])
        bindings[i] = binding

    controller.bone_indices = bind_bone_indices
    controller.bone_ids = bind_bone_ids
    controller.bindings = bindings

    cloth_obj_eval.to_mesh_clear()

    # Remove elements for other LODs. Char cloth only supports a single LOD
    controller.cloth_med = None
    controller.cloth_low = None
    controller.cloth_vlow = None
    controller.morph_controller = None
    # bridge.vertex_count_med = None
    # bridge.vertex_count_low = None
    # bridge.vertex_count_vlow = None
    bridge.pin_radius_med = None
    bridge.pin_radius_low = None
    bridge.pin_radius_vlow = None
    bridge.vertex_weights_med = None
    bridge.vertex_weights_low = None
    bridge.vertex_weights_vlow = None
    bridge.inflation_scale_med = None
    bridge.inflation_scale_low = None
    bridge.inflation_scale_vlow = None
    bridge.display_map_med = None
    bridge.display_map_low = None
    bridge.display_map_vlow = None

    return char_cloth


def _cloth_char_get_bindings(
    cloth_mesh: Mesh,
    cloth_obj: Object,
    drawable_obj: Object
) -> tuple[NDArray[np.float32], NDArray[np.uint32], list[int]]:
    from .vertex_buffer_builder import normalize_weights, get_sorted_vertex_group_elements, get_bone_by_vgroup

    vertex_groups = cloth_obj.vertex_groups
    bones = drawable_obj.data.bones
    bone_by_vgroup = get_bone_by_vgroup(vertex_groups, bones) if bones and vertex_groups else None

    num_verts = len(cloth_mesh.vertices)

    ind_arr = np.zeros((num_verts, 4), dtype=np.uint32)
    weights_arr = np.zeros((num_verts, 4), dtype=np.float32)
    bone_index_map = {}

    ungrouped_verts = 0

    for i, vert in enumerate(cloth_mesh.vertices):
        groups = get_sorted_vertex_group_elements(vert, bone_by_vgroup)
        if not groups:
            ungrouped_verts += 1
            continue

        for j, grp in enumerate(groups):
            if j > 3:
                break

            weights_arr[i][j] = grp.weight
            bone_index = bone_by_vgroup[grp.group]
            ind_arr[i][j] = bone_index_map.setdefault(bone_index, len(bone_index_map))

    if ungrouped_verts != 0:
        logger.warning(
            f"Character cloth mesh '{cloth_mesh.name}' has {ungrouped_verts} vertices not weighted to any vertex group! "
            "These vertices will be weighted to the root bone which may cause parts to float in-game. "
            "In Edit Mode, you can use 'Select > Select All by Trait > Ungrouped vertices' to select "
            "these vertices."
        )

    weights_arr = normalize_weights(weights_arr)
    return weights_arr, ind_arr, list(bone_index_map.keys())


def cloth_char_export_dictionary(dwd_obj: Object, drawable_obj_to_xml: dict[Object, Drawable]) -> Optional[ClothDictionary]:
    cloth_dict = None

    for drawable_obj, drawable_xml in drawable_obj_to_xml.items():
        cloth = cloth_char_export(drawable_obj, drawable_xml, [], remove_number_suffix(dwd_obj.name))
        if cloth is None:
            continue

        if cloth_dict is None:
            cloth_dict = ClothDictionary()

        cloth_dict.append(cloth)

    return cloth_dict
