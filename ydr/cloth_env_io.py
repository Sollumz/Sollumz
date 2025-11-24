import numpy as np
from bpy.types import (
    Object,
    Material,
)
from mathutils import (
    Vector,
    Matrix,
)
from szio.gta5 import (
    ShaderManager,
    AssetFormat,
    AssetDrawable,
    create_asset_drawable,
    EnvCloth,
    EnvClothTuning,
    VerletCloth,
    VerletClothEdge,
    ClothController,
    ClothBridgeSimGfx,
    LodLevel as IOLodLevel,
    Model,
    VertexDataType,
)
from ..tools.blenderhelper import (
    get_evaluated_obj,
    remove_number_suffix,
    get_child_of_bone,
)
from ..tools.meshhelper import get_tangent_required
from ..sollumz_properties import (
    SollumType,
    SOLLUMZ_UI_NAMES,
    LODLevel,
)
from ..ybn.ybnexport import get_scale_to_apply_to_bound
from ..ybn.ybnexport_io import create_bound_composite_asset
from .vertex_buffer_builder_domain import VBBuilderDomain
from .ydrexport_io import (
    get_bone_index,
    create_model,
    create_shader_group,
)
from .cloth_env import (
    cloth_env_find_mesh_objects,
)
from .cloth_diagnostics import (
    ClothDiagMeshBindingError,
    cloth_export_context,
    cloth_enter_export_context,
)
from ..iecontext import export_context
from .. import logger

CLOTH_ENV_MAX_VERTICES = 1000


def _cloth_sort_verlet_edges(edges: list[VerletClothEdge]) -> list[VerletClothEdge]:
    """Sort edges such that no vertex is repeated within chunks of 8 edges. Required due to how the cloth physics code
    is vectorized.
    """
    # fairly inefficient algorithm ahead, works for now
    edge_buckets: list[list[VerletClothEdge]] = []
    MAX_EDGES_IN_BUCKET = 8
    for e in edges:
        for bucket in edge_buckets:
            if len(bucket) >= MAX_EDGES_IN_BUCKET:
                continue

            can_add_to_bucket = True
            for edge_in_bucket in bucket:
                if (
                    e.vertex0 == edge_in_bucket.vertex0 or e.vertex0 == edge_in_bucket.vertex1 or
                    e.vertex1 == edge_in_bucket.vertex0 or e.vertex1 == edge_in_bucket.vertex1
                ):
                    can_add_to_bucket = False
                    break

            if can_add_to_bucket:
                bucket.append(e)
                break
        else:
            # Could not be added to any existing bucket, create a new bucket
            edge_buckets.append([e])

    new_edges = []
    for bucket in edge_buckets:
        for i in range(MAX_EDGES_IN_BUCKET):
            if i < len(bucket):
                new_edges.append(bucket[i])
            else:
                # insert dummy edge
                verlet_edge = VerletClothEdge(
                    vertex0=0,
                    vertex1=0,
                    length_sqr=1e8,
                    weight0=0.0,
                    compression_weight=0.0,
                )
                new_edges.append(verlet_edge)

    return new_edges


def cloth_env_export(frag_obj: Object, drawable: AssetDrawable, materials: list[Material]) -> EnvCloth | None:
    cloth_objs = cloth_env_find_mesh_objects(frag_obj)
    if not cloth_objs:
        return None

    cloth_obj = cloth_objs[0]
    if len(cloth_objs) > 1:
        other_cloth_objs = cloth_objs[1:]
        other_cloth_objs_names = [f"'{o.name}'" for o in other_cloth_objs]
        other_cloth_objs_names = ", ".join(other_cloth_objs_names)
        logger.warning(
            f"Fragment '{frag_obj.name}' has multiple cloth drawable models! "
            f"Only a single cloth per fragment is supported, drawable model '{cloth_obj.name}' will be used.\n"
            f"The following drawable models will be ignored: {other_cloth_objs_names}."
        )

    with cloth_enter_export_context(frag_obj) as export_context:
        with export_context.enter_drawable_context(cloth_obj) as diagnostics:
            diagnostics.drawable_model_obj_name = cloth_obj.name
            diagnostics.cloth_obj_name = cloth_obj.name
            return _cloth_env_export(frag_obj, cloth_obj, drawable, materials)


def _cloth_env_export(frag_obj: Object, cloth_obj: Object, drawable: AssetDrawable, materials: list[Material]) -> EnvCloth | None:
    cloth_bone = get_child_of_bone(cloth_obj)
    if cloth_bone is None:
        logger.error(
            f"Fragment cloth '{cloth_obj.name}' is not attached to a bone! "
            "Attach it to a bone via a Copy Transforms constraint."
        )
        return None

    from .cloth import mesh_get_cloth_attribute_values, mesh_has_cloth_attribute, ClothAttr

    cloth_obj_eval = get_evaluated_obj(cloth_obj)
    cloth_mesh = cloth_obj_eval.to_mesh()
    cloth_mesh.calc_loop_triangles()

    num_vertices = len(cloth_mesh.vertices)
    if num_vertices > CLOTH_ENV_MAX_VERTICES:
        logger.error(
            f"Fragment '{frag_obj.name}' has cloth with too many vertices! "
            f"The maximum is {CLOTH_ENV_MAX_VERTICES} vertices but drawable model '{cloth_obj.name}' has "
            f"{num_vertices} vertices.\n"
            f"Cloth won't be exported!"
        )
        return None

    pinned = np.array(mesh_get_cloth_attribute_values(cloth_mesh, ClothAttr.PINNED)) != 0
    num_pinned = np.sum(pinned)

    mesh_to_cloth_vertex_map = [None] * num_vertices
    cloth_to_mesh_vertex_map = [None] * num_vertices
    vertices = [None] * num_vertices
    for v in cloth_mesh.vertices:
        vi = v.index
        vertices[vi] = Vector(v.co)
        mesh_to_cloth_vertex_map[vi] = vi
        cloth_to_mesh_vertex_map[vi] = vi

    cloth_pin_index = 0
    for v in cloth_mesh.vertices:
        if pinned[v.index]:
            if v.index != cloth_pin_index:
                # Swap vertices so the pinned vertices are placed at the start of the array
                vA = vertices[cloth_pin_index]
                vB = vertices[v.index]

                vertices[cloth_pin_index] = vB
                vertices[v.index] = vA

                mesh_to_cloth_vertex_map[cloth_to_mesh_vertex_map[cloth_pin_index]] = mesh_to_cloth_vertex_map[v.index]
                cloth_to_mesh_vertex_map[v.index] = cloth_to_mesh_vertex_map[cloth_pin_index]

                mesh_to_cloth_vertex_map[v.index] = cloth_pin_index
                cloth_to_mesh_vertex_map[cloth_pin_index] = v.index

            cloth_pin_index += 1

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

    triangles = cloth_mesh.loop_triangles

    edges = []
    edges_added = set()
    for tri in triangles:
        v0, v1, v2 = tri.vertices
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
        # cloth_obj.data.edges[edge.index].select = True

    del edges_added

    edges = _cloth_sort_verlet_edges(edges)
    custom_edges = _cloth_sort_verlet_edges(custom_edges)

    cloth_props = frag_obj.fragment_properties.cloth

    if cloth_props.world_bounds:
        world_bounds = create_bound_composite_asset(cloth_props.world_bounds, allow_planes=True)

        invalid_bounds = [
            c for c in cloth_props.world_bounds.children
            if c.sollum_type not in {SollumType.BOUND_PLANE, SollumType.BOUND_CAPSULE}
        ]
        if invalid_bounds:
            invalid_bounds_names = [f"'{o.name}'" for o in invalid_bounds]
            invalid_bounds_names = ", ".join(invalid_bounds_names)
            logger.warning(
                f"Fragment '{frag_obj.name}' has cloth world bounds with unsupported types! "
                f"Only {SOLLUMZ_UI_NAMES[SollumType.BOUND_CAPSULE]} and {SOLLUMZ_UI_NAMES[SollumType.BOUND_PLANE]} "
                f"types are supported.\n"
                f"The following bounds are unsupported: {invalid_bounds_names}."
            )
    else:
        world_bounds = None

    verlet = VerletCloth(
        vertex_positions=vertices,
        vertex_normals=[],  # env cloth never has vertex normals
        bb_min=Vector(np.min(vertices, axis=0)),
        bb_max=Vector(np.max(vertices, axis=0)),
        switch_distance_up=500.0,  # TODO(cloth): switch distance? think it is only needed with multiple lods
        switch_distance_down=0.0,
        cloth_weight=cloth_props.weight,
        edges=edges,
        custom_edges=custom_edges,
        pinned_vertices_count=num_pinned,
        bounds=world_bounds,
        flags=2 if world_bounds else 0,
    )

    if mesh_has_cloth_attribute(cloth_mesh, ClothAttr.PIN_RADIUS):
        pin_radius = mesh_get_cloth_attribute_values(cloth_mesh, ClothAttr.PIN_RADIUS)
        pin_radius = [
            pin_radius[mi][0]  # env cloth only ever has 1 pin radius set
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
        user_data = [force_transform[mi] for mi in cloth_to_mesh_vertex_map]
    else:
        user_data = []

    bridge = ClothBridgeSimGfx(
        vertex_count_high=num_vertices,
        pin_radius_high=pin_radius,
        vertex_weights_high=vertex_weights,
        inflation_scale_high=inflation_scale,
        display_map_high=mesh_to_cloth_vertex_map,
    )

    controller = ClothController(
        name=remove_number_suffix(frag_obj.name) + "_cloth",
        flags=3,   # owns morph controller + owns bridge
        bridge=bridge,
        cloth_high=verlet,
        morph_high_poly_count=len(triangles),
    )

    cloth_drawable = create_asset_drawable(export_context().settings.targets, is_frag=True)
    cloth_drawable.name = "skel"
    cloth_drawable.shader_group = create_shader_group(materials)
    cloth_drawable.skeleton = drawable.skeleton
    cloth_drawable.lod_thresholds = drawable.lod_thresholds

    scale = get_scale_to_apply_to_bound(cloth_obj)
    transforms_to_apply = Matrix.Diagonal(scale).to_4x4()

    # TODO(cloth): lods
    model: Model = create_model(
        cloth_obj, LODLevel.HIGH, materials,
        transforms_to_apply=transforms_to_apply,
        # Force vertex domain because we don't want to possibly export a vertex per face corner since cloth mesh and
        # drawable mesh need to have the same number of vertices, otherwise the display map binding below may fail
        mesh_domain_override=VBBuilderDomain.VERTEX,
    )
    model.bone_index = get_bone_index(frag_obj.data, cloth_bone)

    # Given we are limited to CLOTH_MAX_VERTICES, it should always only generate a single geometry
    assert len(model.geometries) == 1, "Only a single geometry should be exported"
    geom = model.geometries[0]
    geom.vertex_data_type = (
        VertexDataType.ENV_CLOTH
        if get_tangent_required(cloth_obj_eval.data.materials[0])
        else VertexDataType.ENV_CLOTH_NO_TANGENT
    )

    # Sort the geometry vertices to match the display map
    geom_to_mesh_map = [-1] * len(geom.vertex_buffer)
    mesh_to_geom_map = [-1] * len(geom.vertex_buffer)
    num_extra_matches_per_cloth_vertex = [0] * len(verlet.vertex_positions)
    for geom_vertex_index, geom_vertex in enumerate(geom.vertex_buffer["Position"]):
        matching_cloth_vertex_index = None
        for cloth_vertex_index, cloth_vertex in enumerate(verlet.vertex_positions):
            if np.allclose(geom_vertex, cloth_vertex, atol=1e-5):
                matching_cloth_vertex_index = cloth_vertex_index
                break

        assert matching_cloth_vertex_index is not None, \
            f"Could not match cloth vertex for drawable geometry vertex #{geom_vertex_index} {Vector(geom_vertex)}"

        mesh_vertex_index = cloth_to_mesh_vertex_map[matching_cloth_vertex_index]
        assert geom_to_mesh_map[geom_vertex_index] == -1, f"Geometry vertex #{geom_vertex_index} already assigned"
        if mesh_to_geom_map[mesh_vertex_index] != -1:
            num_extra_matches_per_cloth_vertex[matching_cloth_vertex_index] += 1

        geom_to_mesh_map[geom_vertex_index] = mesh_vertex_index
        mesh_to_geom_map[mesh_vertex_index] = geom_vertex_index

    num_extra_matches_per_mesh_vertex = np.array(num_extra_matches_per_cloth_vertex)
    if (num_extra_matches_per_mesh_vertex > 0).any():
        extra_matches_indices = np.where(num_extra_matches_per_mesh_vertex > 0)[0]
        extra_matches_positions = np.array(verlet.vertex_positions)[extra_matches_indices]
        cloth_export_context().diagnostics.mesh_binding_errors = [
            ClothDiagMeshBindingError(Vector(p), False, False, True)
            for p in extra_matches_positions
        ]
        n = len(extra_matches_positions)
        logger.error(
            f"Failed to bind {n} {'vertex' if n == 1 else 'vertices'} from cloth drawable model '{cloth_obj.name}'. "
            "Found multiple vertices at the same location."
        )

    geom_to_mesh_map = np.array(geom_to_mesh_map)
    mesh_to_geom_map = np.array(mesh_to_geom_map)

    geom.vertex_buffer = geom.vertex_buffer[mesh_to_geom_map]
    geom.index_buffer = geom_to_mesh_map[geom.index_buffer]

    del geom_to_mesh_map
    del mesh_to_geom_map

    cloth_drawable.models = {IOLodLevel.HIGH: [model]}

    cloth_obj_eval.to_mesh_clear()

    env_cloth_flags = 0
    # Apply tuning
    if cloth_props.enable_tuning:
        env_cloth_flags |= 16  # 'owns instance tuning' flag
        if cloth_props.tuning_flags.is_in_interior:
            env_cloth_flags |= 32  # 'is in interior' flag

        if cloth_props.tuning_flags.wind_feedback:
            pin_vert = mesh_to_cloth_vertex_map[cloth_props.pin_vert]
            non_pin_vert0 = mesh_to_cloth_vertex_map[cloth_props.non_pin_vert0]
            non_pin_vert1 = mesh_to_cloth_vertex_map[cloth_props.non_pin_vert1]
        else:
            pin_vert = 0
            non_pin_vert0 = 0
            non_pin_vert1 = 0

        tuning = EnvClothTuning(
            rotation_rate=cloth_props.rotation_rate,
            angle_threshold=cloth_props.angle_threshold,
            extra_force=Vector(cloth_props.extra_force),
            flags=int(cloth_props.tuning_flags.total),
            weight=cloth_props.weight_override,
            distance_threshold=cloth_props.distance_threshold,
            pin_vert=pin_vert,
            non_pin_vert0=non_pin_vert0,
            non_pin_vert1=non_pin_vert1,
        )
    else:
        tuning = None

    return EnvCloth(
        drawable=cloth_drawable,
        controller=controller,
        user_data=user_data,
        tuning=tuning,
        flags=env_cloth_flags,
    )
