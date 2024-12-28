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
    LODLevel,
)
from ..ybn.ybnexport import get_scale_to_apply_to_bound
from .ydrexport import (
    get_bone_index,
    create_model_xml,
    append_model_xml,
    set_drawable_xml_extents,
)
from .. import logger


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

    from .cloth import CLOTH_MAX_VERTICES, mesh_get_cloth_attribute_values, ClothAttr

    env_cloth = EnvironmentCloth()
    # env_cloth.flags = ValueProperty("Unknown78", 1)
    # env_cloth.user_data = TextListProperty("UnknownData")
    # env_cloth.tuning = ClothInstanceTuning()
    cloth_obj_eval = get_evaluated_obj(cloth_obj)
    cloth_mesh = cloth_obj_eval.to_mesh()
    cloth_mesh.calc_loop_triangles()

    num_vertices = len(cloth_mesh.vertices)
    if num_vertices > CLOTH_MAX_VERTICES:
        logger.error(
            f"Fragment '{frag_obj.name}' has cloth with too many vertices! "
            f"The maximum is {CLOTH_MAX_VERTICES} vertices but drawable model '{cloth_obj.name}' has "
            f"{num_vertices} vertices.\n"
            f"Cloth won't be exported!"
        )
        return None

    pinned = np.array(mesh_get_cloth_attribute_values(cloth_mesh, ClothAttr.PINNED)) != 0
    num_pinned = np.sum(pinned)

    mesh_to_cloth_vertex_map = [None] * num_vertices
    cloth_to_mesh_vertex_map = [None] * num_vertices
    vertices = [None] * num_vertices
    cloth_pin_index = 0
    cloth_unpin_index = num_pinned
    for v in cloth_mesh.vertices:
        vi = None
        if pinned[v.index]:
            vi = cloth_pin_index
            cloth_pin_index += 1
        else:
            vi = cloth_unpin_index
            cloth_unpin_index += 1

        vertices[vi] = Vector(v.co)
        mesh_to_cloth_vertex_map[v.index] = vi
        cloth_to_mesh_vertex_map[vi] = v.index

    triangles = cloth_mesh.loop_triangles

    controller = env_cloth.controller
    controller.name = remove_number_suffix(frag_obj.name) + "_cloth"
    controller.morph_controller.map_data_high.poly_count = len(triangles)
    controller.flags = 3  # owns morph controller + owns bridge
    bridge = controller.bridge
    bridge.vertex_count_high = num_vertices
    pin_radius = mesh_get_cloth_attribute_values(cloth_mesh, ClothAttr.PIN_RADIUS)
    vertex_weights = mesh_get_cloth_attribute_values(cloth_mesh, ClothAttr.VERTEX_WEIGHT)
    inflation_scale = mesh_get_cloth_attribute_values(cloth_mesh, ClothAttr.INFLATION_SCALE)
    bridge.pin_radius_high = [pin_radius[mi] for mi in cloth_to_mesh_vertex_map]
    bridge.vertex_weights_high = [vertex_weights[mi] for mi in cloth_to_mesh_vertex_map]
    bridge.inflation_scale_high = [inflation_scale[mi] for mi in cloth_to_mesh_vertex_map]
    bridge.display_map_high = [-1] * num_vertices
    bridge.pinnable_list = [0] * int(np.ceil(num_vertices / 32))  # just need to allocate space for the pinnable list

    edges = []
    edges_added = set()
    for tri in triangles:
        v0, v1, v2 = tri.vertices
        for edge_v0, edge_v1 in ((v0, v1), (v1, v2), (v2, v0)):
            if (edge_v0, edge_v1) in edges_added or (edge_v1, edge_v0) in edges_added:
                continue

            if pinned[edge_v0] and pinned[edge_v1]:
                continue

            verlet_edge = VerletClothEdge()
            verlet_edge.vertex0 = mesh_to_cloth_vertex_map[edge_v0]
            verlet_edge.vertex1 = mesh_to_cloth_vertex_map[edge_v1]
            verlet_edge.length_sqr = Vector(vertices[verlet_edge.vertex0] -
                                            vertices[verlet_edge.vertex1]).length_squared
            verlet_edge.weight0 = 0.0 if pinned[edge_v0] else 1.0 if pinned[edge_v1] else 0.5
            verlet_edge.compression_weight = 0.25  # TODO(cloth): compression_weight
            edges.append(verlet_edge)
            edges_added.add((edge_v0, edge_v1))

    del edges_added

    # Sort edges such that no vertex is repeated within chunks of 8 edges. Required due to how the cloth physics code
    # is vectorized.
    # fairly inefficient algorithm ahead, works for now
    edge_buckets = [[] for _ in range(len(edges) * 4)]
    last_bucket_index = -1
    MAX_EDGES_IN_BUCKET = 8
    for e in edges:
        for bucket_index, bucket in enumerate(edge_buckets):
            if len(bucket) >= MAX_EDGES_IN_BUCKET:
                continue

            can_add_to_bucket = True
            for edge_in_bucket in bucket:
                if (e.vertex0 == edge_in_bucket.vertex0 or e.vertex0 == edge_in_bucket.vertex1 or
                        e.vertex1 == edge_in_bucket.vertex0 or e.vertex1 == edge_in_bucket.vertex1):
                    can_add_to_bucket = False
                    break

            if can_add_to_bucket:
                bucket.append(e)
                if bucket_index > last_bucket_index:
                    last_bucket_index = bucket_index
                break

    new_edges = []
    for bucket_index, bucket in enumerate(edge_buckets):
        if bucket_index > last_bucket_index:
            break

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

    edges = new_edges

    del edge_buckets
    del last_bucket_index
    del new_edges

    verlet = controller.cloth_high  # TODO(cloth): other lods
    verlet.vertex_positions = vertices
    # verlet.vertex_normals = ...  # TODO(cloth): cloth vertex normals, when should be exported? they are not always there
    verlet.bb_min = Vector(np.min(vertices, axis=0))
    verlet.bb_max = Vector(np.max(vertices, axis=0))
    verlet.switch_distance_up = 500.0  # TODO(cloth): switch distance? think it is only needed with multiple lods
    verlet.switch_distance_down = 0.0
    verlet.flags = 0  # TODO(cloth): flags
    verlet.dynamic_pin_list_size = 6  # TODO(cloth): what determines the dynamic pin list size?
    verlet.cloth_weight = 1.0  # TODO(cloth): cloth weight
    verlet.edges = edges
    verlet.pinned_vertices_count = num_pinned
    # verlet.custom_edges = ...  # TODO(cloth): custom edges

    # eds = []
    # for e in verlet.edges:
    #     v0 = verlet.vertex_positions[e.vertex0]
    #     v1 = verlet.vertex_positions[e.vertex1]
    #     if v1.length < v0.length:
    #         v0, v1 = v1, v0
    #     eds.append((v0, v1))
    #
    # eds.sort(key=lambda v: (v[0] + v[1]).length)
    # for v0, v1 in eds:
    #     print(f"{v0.x:.3f}, {v0.y:.3f}, {v0.z:.3f} -- {v1.x:.3f}, {v1.y:.3f}, {v1.z:.3f}")

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
    model_xml = create_model_xml(cloth_obj, LODLevel.HIGH, materials, transforms_to_apply=transforms_to_apply)

    bone = get_child_of_bone(cloth_obj)
    if bone is None:
        logger.error(
            f"Fragment cloth '{cloth_obj.name}' is not attached to a bone! "
            "Attach it to a bone via a Copy Transforms constraint."
        )
        return None

    model_xml.bone_index = get_bone_index(frag_obj.data, bone)

    append_model_xml(cloth_drawable_xml, model_xml, LODLevel.HIGH)

    set_drawable_xml_extents(cloth_drawable_xml)

    # Cloth require a different FVF than the default one
    model_xml.geometries[0].vertex_buffer.get_element(
        "layout").type = "GTAV2" if get_tangent_required(cloth_obj_eval.data.materials[0]) else "GTAV3"

    from ..ydr.ydrexport import set_drawable_xml_flags, set_drawable_xml_properties
    set_drawable_xml_flags(cloth_drawable_xml)
    assert cloth_obj.parent.sollum_type == SollumType.DRAWABLE
    set_drawable_xml_properties(cloth_obj.parent, cloth_drawable_xml)

    # Compute display map
    bridge.display_map_high = [-1] * len(model_xml.geometries[0].vertex_buffer.data["Position"])
    for mesh_vertex_index, mesh_vertex in enumerate(model_xml.geometries[0].vertex_buffer.data["Position"]):
        matching_cloth_vertex_index = None
        for cloth_vertex_index, cloth_vertex in enumerate(verlet.vertex_positions):
            if np.allclose(mesh_vertex, cloth_vertex, atol=1e-3):
                matching_cloth_vertex_index = cloth_vertex_index
                break

        assert matching_cloth_vertex_index is not None

        bridge.display_map_high[mesh_vertex_index] = matching_cloth_vertex_index

    cloth_obj_eval.to_mesh_clear()

    # Apply tuning
    cloth_props = frag_obj.fragment_properties.cloth
    if cloth_props.enable_tuning:
        t = env_cloth.tuning
        t.rotation_rate = cloth_props.rotation_rate
        t.angle_threshold = cloth_props.angle_threshold
        t.extra_force = cloth_props.extra_force
        t.flags = int(cloth_props.tuning_flags.total)
        t.weight = cloth_props.weight
        t.distance_threshold = cloth_props.distance_threshold
        # TODO(cloth): these vertex indices don't match the exported mesh
        t.pin_vert = cloth_props.pin_vert
        t.non_pin_vert0 = cloth_props.non_pin_vert0
        t.non_pin_vert1 = cloth_props.non_pin_vert1
    else:
        env_cloth.tuning = None

    return env_cloth
