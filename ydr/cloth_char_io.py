import numpy as np
from numpy.typing import NDArray
import bpy
from bpy.types import (
    Object,
    Mesh,
)
from mathutils import (
    Vector,
    Matrix,
)
from szio.gta5 import (
    AssetClothDictionary,
    VerletCloth,
    VerletClothEdge,
    ClothBridgeSimGfx,
    CharacterClothBinding,
    CharacterClothController,
    CharacterCloth,
    create_asset_cloth_dictionary,
)
from ..tools.blenderhelper import (
    get_evaluated_obj,
    remove_number_suffix,
    get_child_of_bone,
    create_blender_object,
    add_child_of_bone_constraint,
)
from ..sollumz_properties import (
    SollumType,
    SOLLUMZ_UI_NAMES,
)
from ..ybn.ybnimport_io import create_bound_composite
from ..ybn.ybnexport_io import create_bound_composite_asset
from ..iecontext import export_context
from .cloth import (
    mesh_get_cloth_attribute_values,
    mesh_has_cloth_attribute,
    mesh_add_cloth_attribute,
    ClothAttr,
)
from .cloth_diagnostics import (
    ClothDiagMeshBindingError,
    cloth_export_context,
)
from .. import logger

CLOTH_CHAR_MAX_VERTICES = 254
CLOTH_CHAR_VERTEX_GROUP_NAME = "CLOTH"


def cloth_char_find_mesh_objects(drawable_obj: Object, silent: bool = False) -> list[Object]:
    from .cloth_char import cloth_char_find_mesh_objects as impl
    return impl(drawable_obj, silent)


def cloth_char_find_bounds(char_cloth_obj: Object) -> list[Object]:
    from .cloth_char import cloth_char_find_bounds as impl
    return impl(char_cloth_obj)


def cloth_char_export(
    dwd_obj: Object,
    drawable_obj: Object,
    controller_name: str,
) -> CharacterCloth | None:
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

    cloth_export_context().diagnostics.cloth_obj_name = cloth_obj.name

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

    # Need the bone transforms to calculate the bound transforms
    from .ydrexport_io import create_skeleton
    armature_obj = drawable_obj if drawable_obj.type == "ARMATURE" else dwd_obj
    assert armature_obj.type == "ARMATURE", "Drawable with cloth or its parent drawable dictionary must have an armature"
    skeleton = create_skeleton(armature_obj)

    bounds_to_index = {}
    bounds = create_bound_composite_asset(cloth_bounds_obj, out_child_obj_to_index=bounds_to_index)

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
            return Matrix.LocRotScale(bone.position, bone.rotation, bone.scale)
        bone_transforms = {}
        bones = skeleton.bones
        for b in bones:
            transforms = _get_bone_transforms(b)
            if b.parent_index != -1:
                parent_transforms = bone_transforms[bones[b.parent_index].tag]
                transforms = parent_transforms @ transforms

            bone_transforms[b.tag] = transforms

        bone_transform = bone_transforms[bone.bone_properties.tag]
        bone_inv = bone_transform.inverted()

        bound = bounds.children[bound_index]
        bound.composite_transform = bound.composite_transform @ bone_inv.transposed()

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

    char_cloth_props = drawable_obj.drawable_properties.char_cloth

    if mesh_has_cloth_attribute(cloth_mesh, ClothAttr.PIN_RADIUS):
        pin_radius = mesh_get_cloth_attribute_values(cloth_mesh, ClothAttr.PIN_RADIUS)
        pin_radius = [
            pin_radius[mi][set_idx]
            for set_idx in range(char_cloth_props.num_pin_radius_sets)
            for mi in cloth_to_mesh_vertex_map
        ]
    else:
        pin_radius = []
    vertex_weights = mesh_get_cloth_attribute_values(cloth_mesh, ClothAttr.VERTEX_WEIGHT)
    vertex_weights = [vertex_weights[mi] for mi in cloth_to_mesh_vertex_map]
    inflation_scale = mesh_get_cloth_attribute_values(cloth_mesh, ClothAttr.INFLATION_SCALE)
    inflation_scale = [inflation_scale[mi] for mi in cloth_to_mesh_vertex_map]

    force_transform = mesh_get_cloth_attribute_values(cloth_mesh, ClothAttr.FORCE_TRANSFORM)
    if (force_transform != 0).any():
        logger.warning(
            f"Character cloth mesh '{cloth_obj.name}' has {ClothAttr.FORCE_TRANSFORM.label} attribute, but this "
            "attribute is not supported in character cloth and will be ignored! Only fragment cloth support it."
        )

    def _create_verlet_edge(mesh_v0: int, mesh_v1: int) -> VerletClothEdge:
        vertex0 = mesh_to_cloth_vertex_map[mesh_v0]
        vertex1 = mesh_to_cloth_vertex_map[mesh_v1]
        return VerletClothEdge(
            vertex0=vertex0,
            vertex1=vertex1,
            length_sqr=Vector(vertices[vertex0] - vertices[vertex1]).length_squared,
            weight0=0.0 if pinned[mesh_v0] else 1.0 if pinned[mesh_v1] else 0.5,
            compression_weight=0.25,
        )

    indices = [None] * (len(triangles) * 3)
    edges = []
    edges_added = set()
    for tri in triangles:
        v0, v1, v2 = tri.vertices
        indices[tri.index * 3 + 0] = mesh_to_cloth_vertex_map[v0]
        indices[tri.index * 3 + 1] = mesh_to_cloth_vertex_map[v1]
        indices[tri.index * 3 + 2] = mesh_to_cloth_vertex_map[v2]
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

    from .cloth_env_io import _cloth_sort_verlet_edges
    edges = _cloth_sort_verlet_edges(edges)
    custom_edges = _cloth_sort_verlet_edges(custom_edges)

    verlet = VerletCloth(
        vertex_positions=vertices,
        vertex_normals=normals,
        bb_min=Vector(np.min(vertices, axis=0)),
        bb_max=Vector(np.max(vertices, axis=0)),
        switch_distance_up=9999.0,
        switch_distance_down=9999.0,
        flags=0,
        cloth_weight=char_cloth_props.weight,
        edges=edges,
        custom_edges=custom_edges,
        pinned_vertices_count=num_pinned,
        bounds=None  # char cloth doesn't have embedded world bounds
    )

    # Cloth vertex bindings to bones
    bind_weights, bind_indices, bind_bone_indices = _cloth_char_get_cloth_to_bone_bindings(
        cloth_mesh, cloth_obj_eval, armature_obj
    )
    bind_bone_ids = [skeleton.bones[i].tag for i in bind_bone_indices]
    bindings = [None] * num_vertices
    for i in range(num_vertices):
        bindings[mesh_to_cloth_vertex_map[i]] = CharacterClothBinding(
            weights=tuple(bind_weights[i]),
            indices=tuple(bind_indices[i]),
        )

    cloth_obj_eval.to_mesh_clear()

    bridge = ClothBridgeSimGfx(
        vertex_count_high=num_vertices,
        pin_radius_high=pin_radius,
        vertex_weights_high=vertex_weights,
        inflation_scale_high=inflation_scale,
        display_map_high=mesh_to_cloth_vertex_map,
    )

    controller = CharacterClothController(
        name=controller_name,
        flags=2,  # owns bridge
        pin_radius_scale=char_cloth_props.pin_radius_scale,
        pin_radius_threshold=char_cloth_props.pin_radius_threshold,
        wind_scale=char_cloth_props.wind_scale,
        vertices=vertices,
        indices=indices,
        bone_indices=bind_bone_indices,
        bone_ids=bind_bone_ids,
        bindings=bindings,
        bridge=bridge,
        cloth_high=verlet,
        morph_high_poly_count=None,  # this indicates that there is no morph controller
    )

    return CharacterCloth(
        name=remove_number_suffix(drawable_obj.name),
        parent_matrix=Matrix.Identity(4),
        poses=[],  # TODO(cloth): export char cloth poses
        bounds_bone_ids=bounds_bone_ids,
        bounds_bone_indices=[],  # indices are not needed, the game converts the IDs to indices when loading the cloth
        bounds=bounds,
        controller=controller,
    )


def _cloth_char_get_cloth_to_bone_bindings(
    cloth_mesh: Mesh,
    cloth_obj: Object,
    armature_obj: Object
) -> tuple[NDArray[np.float32], NDArray[np.uint32], list[int]]:
    from .cloth_char import _cloth_char_get_cloth_to_bone_bindings as impl
    return impl(cloth_mesh, cloth_obj, armature_obj)


def cloth_char_get_mesh_to_cloth_bindings(
    cloth: CharacterCloth,
    mesh_binded_verts: NDArray[np.float32],
    mesh_binded_verts_normals: NDArray[np.float32],
) -> tuple[NDArray[np.float32], NDArray[np.uint32], list[ClothDiagMeshBindingError]]:
    from .cloth_char import _cloth_char_get_mesh_to_cloth_bindings_impl as impl
    return impl(
        cloth.controller.vertices,
        cloth.controller.indices,
        mesh_binded_verts,
        mesh_binded_verts_normals,
    )


def cloth_char_export_dictionary(dwd_obj: Object) -> AssetClothDictionary | None:
    cloths = {}
    for drawable_obj in dwd_obj.children:
        if drawable_obj.sollum_type != SollumType.DRAWABLE:
            continue

        with cloth_export_context().enter_drawable_context(drawable_obj):
            cloth = cloth_char_export(dwd_obj, drawable_obj, remove_number_suffix(dwd_obj.name))

        if cloth is None:
            continue

        cloths[cloth.name] = cloth

    if cloths:
        cld = create_asset_cloth_dictionary(export_context().settings.targets)
        cld.cloths = cloths
        return cld
    else:
        return None


def cloth_char_import_mesh(cloth: CharacterCloth, drawable_obj: Object, armature_obj: Object) -> Object:
    controller = cloth.controller
    vertices = controller.vertices
    indices = controller.indices

    vertices = np.array(vertices)
    indices = np.array(indices).reshape((-1, 3))

    mesh = bpy.data.meshes.new(f"{cloth.name}.cloth")
    mesh.from_pydata(vertices, [], indices)
    obj = create_blender_object(SollumType.CHARACTER_CLOTH_MESH, f"{cloth.name}.cloth", mesh)

    pin_radius = controller.bridge.pin_radius_high
    weights = controller.bridge.vertex_weights_high
    inflation_scale = controller.bridge.inflation_scale_high
    mesh_to_cloth_map = np.array(controller.bridge.display_map_high)
    cloth_to_mesh_map = np.empty_like(mesh_to_cloth_map)
    cloth_to_mesh_map[mesh_to_cloth_map] = np.arange(len(mesh_to_cloth_map))
    pinned_vertices_count = controller.cloth_high.pinned_vertices_count
    vertices_count = len(controller.cloth_high.vertex_positions)

    has_pinned = pinned_vertices_count > 0
    has_pin_radius = len(pin_radius) > 0
    num_pin_radius_sets = len(pin_radius) // vertices_count
    has_weights = len(weights) > 0
    has_inflation_scale = len(inflation_scale) > 0

    char_cloth_props = drawable_obj.drawable_properties.char_cloth
    char_cloth_props.pin_radius_scale = controller.pin_radius_scale
    char_cloth_props.pin_radius_threshold = controller.pin_radius_threshold
    char_cloth_props.wind_scale = controller.wind_scale
    char_cloth_props.weight = controller.cloth_high.cloth_weight

    if has_pinned:
        mesh_add_cloth_attribute(mesh, ClothAttr.PINNED)
    if has_pin_radius:
        mesh_add_cloth_attribute(mesh, ClothAttr.PIN_RADIUS)
        if num_pin_radius_sets > 4:
            logger.warning(f"Found {num_pin_radius_sets} pin radius sets, only up to 4 sets are supported!")
            num_pin_radius_sets = 4
        char_cloth_props.num_pin_radius_sets = num_pin_radius_sets
    if has_weights:
        mesh_add_cloth_attribute(mesh, ClothAttr.VERTEX_WEIGHT)
    if has_inflation_scale:
        mesh_add_cloth_attribute(mesh, ClothAttr.INFLATION_SCALE)

    for mesh_vert_index, cloth_vert_index in enumerate(mesh_to_cloth_map):
        mesh_vert_index = cloth_vert_index  # NOTE: in character cloths both are the same?

        if has_pinned:
            pinned = cloth_vert_index < pinned_vertices_count
            mesh.attributes[ClothAttr.PINNED].data[mesh_vert_index].value = 1 if pinned else 0

        if has_pin_radius:
            pin_radii = [
                pin_radius[cloth_vert_index + (set_idx * vertices_count)]
                if set_idx < num_pin_radius_sets else 0.0
                for set_idx in range(4)
            ]
            mesh.attributes[ClothAttr.PIN_RADIUS].data[mesh_vert_index].color = pin_radii

        if has_weights:
            mesh.attributes[ClothAttr.VERTEX_WEIGHT].data[mesh_vert_index].value = weights[cloth_vert_index]

        if has_inflation_scale:
            mesh.attributes[ClothAttr.INFLATION_SCALE].data[mesh_vert_index].value = inflation_scale[cloth_vert_index]

    custom_edges = [e for e in (cloth.controller.cloth_high.custom_edges or []) if e.vertex0 != e.vertex1]
    if custom_edges:
        next_edge = len(mesh.edges)
        mesh.edges.add(len(custom_edges))
        for custom_edge in custom_edges:
            v0 = custom_edge.vertex0
            v1 = custom_edge.vertex1
            mesh.edges[next_edge].vertices = v0, v1
            next_edge += 1

    bones = armature_obj.data.bones

    def _create_group(bone_index: int):
        if bones and bone_index < len(bones):
            bone_name = bones[bone_index].name
        else:
            bone_name = f"UNKNOWN_BONE.{bone_index}"

        return obj.vertex_groups.new(name=bone_name)

    vertex_groups_by_bone_idx = {}
    for vert_idx, binding in enumerate(controller.bindings):
        for weight, idx in zip(binding.weights, binding.indices):
            if weight == 0.0:
                continue

            bone_idx = controller.bone_indices[idx]
            if bone_idx not in vertex_groups_by_bone_idx:
                vertex_groups_by_bone_idx[bone_idx] = _create_group(bone_idx)

            vgroup = vertex_groups_by_bone_idx[bone_idx]
            vgroup.add((vert_idx,), weight, "ADD")

    if cloth.poses:
        # TODO(cloth): export poses
        num_poses = len(cloth.poses) // 2 // vertices_count
        poses = np.array(cloth.poses)[::2, :3]
        obj.show_only_shape_key = True
        obj.shape_key_add(name="Basis")
        for pose_idx in range(num_poses):
            sk = obj.shape_key_add(name=f"Pose#{pose_idx+1}")
            sk.points.foreach_set("co", poses[pose_idx*vertices_count:(pose_idx+1)*vertices_count].ravel())
        mesh.shape_keys.use_relative = False

    return obj


def cloth_char_import_bounds(cloth: CharacterCloth, armature_obj: Object) -> Object:
    bounds_children_objs = []
    bounds_obj = create_bound_composite(cloth.bounds, f"{cloth.name}.cloth.bounds", out_children=bounds_children_objs)
    bones = armature_obj.data.bones
    for bound_obj, bone_id in zip(bounds_children_objs, cloth.bounds_bone_ids):
        if bound_obj is None or bone_id is None:
            continue

        bone_name = next((b.name for b in bones if b.bone_properties.tag == bone_id), None)
        assert bone_name is not None, "Cloth bound attached to non-existing bone."

        add_child_of_bone_constraint(bound_obj, armature_obj, bone_name)

    return bounds_obj
