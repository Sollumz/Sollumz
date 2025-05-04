import numpy as np
from bpy.types import (
    Object,
    Material,
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
    EnvironmentCloth,
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
    SOLLUMZ_UI_NAMES,
    LODLevel,
)
from ..ybn.ybnexport import (
    create_composite_xml,
    get_scale_to_apply_to_bound,
)
from .vertex_buffer_builder import VBBuilderDomain
from .ydrexport import (
    get_bone_index,
    create_model_xml,
    append_model_xml,
    set_drawable_xml_extents,
)
from .cloth_diagnostics import (
    ClothDiagMeshBindingError,
    cloth_export_context,
    cloth_enter_export_context,
)
from .. import logger

CLOTH_ENV_MAX_VERTICES = 1000


def cloth_env_find_mesh_objects(frag_obj: Object, silent: bool = False) -> list[Object]:
    """Returns a list of mesh objects that use a cloth material in the fragment. If not silent, warns the user if a mesh
    has a cloth material but also other materials or multiple cloth materials.
    """
    mesh_objs = []
    for obj in frag_obj.children_recursive:
        if obj.sollum_type != SollumType.DRAWABLE_MODEL or obj.type != "MESH":
            continue

        mesh = obj.data
        num_cloth_materials = 0
        num_other_materials = 0
        for material in mesh.materials:
            shader_def = ShaderManager.find_shader(material.shader_properties.filename)
            is_cloth_material = shader_def is not None and shader_def.is_cloth
            if is_cloth_material:
                num_cloth_materials += 1
            else:
                num_other_materials += 1

        match (num_cloth_materials, num_other_materials):
            case (1, 0):
                # Only cloth
                mesh_objs.append(obj)
            case (0, _):
                # Not cloth, ignore
                pass
            case (_, 0):
                # More than one cloth material, warning
                if not silent:
                    logger.warning(
                        f"Drawable model '{obj.name}' has multiple cloth materials! "
                        f"This is not supported, only a single cloth material per mesh is supported."
                    )
            case (_, _):
                # Multiple materials including cloth, warning
                if not silent:
                    logger.warning(
                        f"Drawable model '{obj.name}' has a cloth material along with other materials! "
                        f"This is not supported, only a single cloth material per mesh is supported."
                    )

    return mesh_objs


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
                verlet_edge = VerletClothEdge()
                verlet_edge.vertex0 = 0
                verlet_edge.vertex1 = 0
                verlet_edge.length_sqr = 1e8
                verlet_edge.weight0 = 0.0
                verlet_edge.compression_weight = 0.0
                new_edges.append(verlet_edge)

    return new_edges


def cloth_env_export(frag_obj: Object, drawable_xml: Drawable, materials: list[Material]) -> Optional[EnvironmentCloth]:
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
            return _cloth_env_export(frag_obj, cloth_obj, drawable_xml, materials)


def _cloth_env_export(frag_obj: Object, cloth_obj: Object, drawable_xml: Drawable, materials: list[Material]) -> Optional[EnvironmentCloth]:
    cloth_bone = get_child_of_bone(cloth_obj)
    if cloth_bone is None:
        logger.error(
            f"Fragment cloth '{cloth_obj.name}' is not attached to a bone! "
            "Attach it to a bone via a Copy Transforms constraint."
        )
        return None

    from .cloth import mesh_get_cloth_attribute_values, mesh_has_cloth_attribute, ClothAttr

    env_cloth = EnvironmentCloth()
    env_cloth.flags = 0
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

    triangles = cloth_mesh.loop_triangles

    controller = env_cloth.controller
    controller.name = remove_number_suffix(frag_obj.name) + "_cloth"
    controller.morph_controller.map_data_high.poly_count = len(triangles)
    controller.flags = 3  # owns morph controller + owns bridge
    bridge = controller.bridge
    bridge.vertex_count_high = num_vertices
    if mesh_has_cloth_attribute(cloth_mesh, ClothAttr.PIN_RADIUS):
        pin_radius = mesh_get_cloth_attribute_values(cloth_mesh, ClothAttr.PIN_RADIUS)
        bridge.pin_radius_high = [
            pin_radius[mi][0]  # env cloth only ever has 1 pin radius set
            for mi in cloth_to_mesh_vertex_map
        ]
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
        env_cloth.user_data = " ".join(str(force_transform[mi]) for mi in cloth_to_mesh_vertex_map)
    else:
        env_cloth.user_data = None

    def _create_verlet_edge(mesh_v0: int, mesh_v1: int) -> VerletClothEdge:
        verlet_edge = VerletClothEdge()
        verlet_edge.vertex0 = mesh_to_cloth_vertex_map[mesh_v0]
        verlet_edge.vertex1 = mesh_to_cloth_vertex_map[mesh_v1]
        verlet_edge.length_sqr = Vector(vertices[verlet_edge.vertex0] -
                                        vertices[verlet_edge.vertex1]).length_squared
        verlet_edge.weight0 = 0.0 if pinned[mesh_v0] else 1.0 if pinned[mesh_v1] else 0.5
        verlet_edge.compression_weight = 0.25  # TODO(cloth): compression_weight
        return verlet_edge

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

    verlet = controller.cloth_high  # TODO(cloth): other lods
    verlet.vertex_positions = vertices
    verlet.vertex_normals = None  # env cloth never has vertex normals
    verlet.bb_min = Vector(np.min(vertices, axis=0))
    verlet.bb_max = Vector(np.max(vertices, axis=0))
    verlet.switch_distance_up = 500.0  # TODO(cloth): switch distance? think it is only needed with multiple lods
    verlet.switch_distance_down = 0.0
    verlet.flags = 0  # TODO(cloth): flags
    verlet.dynamic_pin_list_size = (num_vertices + 31) // 32
    verlet.cloth_weight = cloth_props.weight
    verlet.edges = edges
    verlet.pinned_vertices_count = num_pinned
    verlet.custom_edges = custom_edges

    # Remove elements for other LODs for now
    controller.cloth_med = None
    controller.cloth_low = None
    controller.cloth_vlow = None
    controller.morph_controller.map_data_high.morph_map_high_weights = None
    controller.morph_controller.map_data_high.morph_map_high_vertex_index = None
    controller.morph_controller.map_data_high.morph_map_high_index0 = None
    controller.morph_controller.map_data_high.morph_map_high_index1 = None
    controller.morph_controller.map_data_high.morph_map_high_index2 = None
    controller.morph_controller.map_data_high.morph_map_med_weights = None
    controller.morph_controller.map_data_high.morph_map_med_vertex_index = None
    controller.morph_controller.map_data_high.morph_map_med_index0 = None
    controller.morph_controller.map_data_high.morph_map_med_index1 = None
    controller.morph_controller.map_data_high.morph_map_med_index2 = None
    controller.morph_controller.map_data_high.morph_map_low_weights = None
    controller.morph_controller.map_data_high.morph_map_low_vertex_index = None
    controller.morph_controller.map_data_high.morph_map_low_index0 = None
    controller.morph_controller.map_data_high.morph_map_low_index1 = None
    controller.morph_controller.map_data_high.morph_map_low_index2 = None
    controller.morph_controller.map_data_high.morph_map_vlow_weights = None
    controller.morph_controller.map_data_high.morph_map_vlow_vertex_index = None
    controller.morph_controller.map_data_high.morph_map_vlow_index0 = None
    controller.morph_controller.map_data_high.morph_map_vlow_index1 = None
    controller.morph_controller.map_data_high.morph_map_vlow_index2 = None
    controller.morph_controller.map_data_high.index_map_high = None
    controller.morph_controller.map_data_high.index_map_med = None
    controller.morph_controller.map_data_high.index_map_low = None
    controller.morph_controller.map_data_high.index_map_vlow = None
    controller.morph_controller.map_data_med = None
    controller.morph_controller.map_data_low = None
    controller.morph_controller.map_data_vlow = None
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

    cloth_drawable_xml = env_cloth.drawable
    cloth_drawable_xml.name = "skel"
    cloth_drawable_xml.shader_group = drawable_xml.shader_group
    cloth_drawable_xml.skeleton = drawable_xml.skeleton
    cloth_drawable_xml.joints = drawable_xml.joints

    scale = get_scale_to_apply_to_bound(cloth_obj)
    transforms_to_apply = Matrix.Diagonal(scale).to_4x4()

    # TODO(cloth): lods
    model_xml = create_model_xml(
        cloth_obj, LODLevel.HIGH, materials,
        transforms_to_apply=transforms_to_apply,
        # Force vertex domain because we don't want to possibly export a vertex per face corner since cloth mesh and
        # drawable mesh need to have the same number of vertices, otherwise the display map binding below may fail
        mesh_domain_override=VBBuilderDomain.VERTEX,
    )
    model_xml.bone_index = get_bone_index(frag_obj.data, cloth_bone)

    # Given we are limited to CLOTH_MAX_VERTICES, it should always only generate a single geometry
    assert len(model_xml.geometries) == 1, "Only a single geometry should be exported"
    geom = model_xml.geometries[0]

    append_model_xml(cloth_drawable_xml, model_xml, LODLevel.HIGH)

    set_drawable_xml_extents(cloth_drawable_xml)

    # Cloth require a different FVF than the default one
    geom.vertex_buffer.get_element("layout").type = (
        "GTAV2"
        if get_tangent_required(cloth_obj_eval.data.materials[0])
        else "GTAV3"
    )

    from ..ydr.ydrexport import set_drawable_xml_flags, set_drawable_xml_properties
    set_drawable_xml_flags(cloth_drawable_xml)
    assert cloth_obj.parent.sollum_type == SollumType.DRAWABLE
    set_drawable_xml_properties(cloth_obj.parent, cloth_drawable_xml)

    # Sort the geometry vertices to match the display map
    geom_to_mesh_map = [-1] * len(geom.vertex_buffer.data)
    mesh_to_geom_map = [-1] * len(geom.vertex_buffer.data)
    num_extra_matches_per_cloth_vertex = [0] * len(verlet.vertex_positions)
    for geom_vertex_index, geom_vertex in enumerate(geom.vertex_buffer.data["Position"]):
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

    geom.vertex_buffer.data = geom.vertex_buffer.data[mesh_to_geom_map]
    geom.index_buffer.data = geom_to_mesh_map[geom.index_buffer.data]

    del geom_to_mesh_map
    del mesh_to_geom_map

    cloth_obj_eval.to_mesh_clear()

    # Apply tuning
    if cloth_props.enable_tuning:
        env_cloth.flags |= 16  # 'owns instance tuning' flag
        if cloth_props.tuning_flags.is_in_interior:
            env_cloth.flags |= 32  # 'is in interior' flag
        t = env_cloth.tuning
        t.rotation_rate = cloth_props.rotation_rate
        t.angle_threshold = cloth_props.angle_threshold
        t.extra_force = cloth_props.extra_force
        t.flags = int(cloth_props.tuning_flags.total)
        t.weight = cloth_props.weight_override
        t.distance_threshold = cloth_props.distance_threshold
        if cloth_props.tuning_flags.wind_feedback:
            t.pin_vert = mesh_to_cloth_vertex_map[cloth_props.pin_vert]
            t.non_pin_vert0 = mesh_to_cloth_vertex_map[cloth_props.non_pin_vert0]
            t.non_pin_vert1 = mesh_to_cloth_vertex_map[cloth_props.non_pin_vert1]
        else:
            t.pin_vert = 0
            t.non_pin_vert0 = 0
            t.non_pin_vert1 = 0
    else:
        env_cloth.tuning = None

    if cloth_props.world_bounds:
        verlet.bounds = create_composite_xml(cloth_props.world_bounds, allow_planes=True)

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
        verlet.bounds = None

    return env_cloth
