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
    CharacterCloth,
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

    from .cloth import CLOTH_MAX_VERTICES, mesh_get_cloth_attribute_values, mesh_has_cloth_attribute, ClothAttr

    char_cloth = CharacterCloth()
    char_cloth.name = remove_number_suffix(drawable_obj.name)
    bounds_to_index = {}
    char_cloth.bounds = create_composite_xml(cloth_bounds_obj, out_child_obj_to_index=bounds_to_index)
    char_cloth.parent_matrix = Matrix.Identity(4) # TODO(cloth): char cloth parent matrix
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
        # TODO: refactor/optimize this, mostly copied from yftexport
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
    if num_vertices > CLOTH_MAX_VERTICES:
        logger.error(
            f"Drawable '{drawable_obj.name}' has cloth with too many vertices! "
            f"The maximum is {CLOTH_MAX_VERTICES} vertices but cloth mesh '{cloth_obj.name}' has "
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
    # TODO(cloth): controller stuff
    # TODO(cloth): verify indices are not needed, pretty sure the game converts the IDs to indices when loading the cloth
    # controller.bone_indices = InlineValueListProperty("UnknownB0")
    # controller.bone_ids = InlineValueListProperty("BoneIDs")
    # controller.bindings = CharacterClothBindingList()
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

    # cloth_drawable_xml = env_cloth.drawable
    # cloth_drawable_xml.name = "skel"
    # cloth_drawable_xml.shader_group = drawable_xml.shader_group
    # cloth_drawable_xml.skeleton = drawable_xml.skeleton
    # cloth_drawable_xml.joints = drawable_xml.joints
    #
    # scale = get_scale_to_apply_to_bound(cloth_obj)
    # transforms_to_apply = Matrix.Diagonal(scale).to_4x4()
    #
    # # TODO(cloth): lods
    # model_xml = create_model_xml(cloth_obj, LODLevel.HIGH, materials, transforms_to_apply=transforms_to_apply)
    # model_xml.bone_index = get_bone_index(frag_obj.data, cloth_bone)
    #
    # # Given we are limited to CLOTH_MAX_VERTICES, it should always only generate a single geometry
    # assert len(model_xml.geometries) == 1, "Only a single geometry should be exported"
    # geom = model_xml.geometries[0]
    #
    # append_model_xml(cloth_drawable_xml, model_xml, LODLevel.HIGH)
    #
    # set_drawable_xml_extents(cloth_drawable_xml)
    #
    # # Cloth require a different FVF than the default one
    # geom.vertex_buffer.get_element("layout").type = (
    #     "GTAV2"
    #     if get_tangent_required(cloth_obj_eval.data.materials[0])
    #     else "GTAV3"
    # )
    #
    # from ..ydr.ydrexport import set_drawable_xml_flags, set_drawable_xml_properties
    # set_drawable_xml_flags(cloth_drawable_xml)
    # assert cloth_obj.parent.sollum_type == SollumType.DRAWABLE
    # set_drawable_xml_properties(cloth_obj.parent, cloth_drawable_xml)
    #
    # # Sort the geometry vertices to match the display map
    # geom_to_mesh_map = [-1] * len(geom.vertex_buffer.data)
    # mesh_to_geom_map = [-1] * len(geom.vertex_buffer.data)
    # for geom_vertex_index, geom_vertex in enumerate(geom.vertex_buffer.data["Position"]):
    #     matching_cloth_vertex_index = None
    #     for cloth_vertex_index, cloth_vertex in enumerate(verlet.vertex_positions):
    #         if np.allclose(geom_vertex, cloth_vertex, atol=1e-5):
    #             matching_cloth_vertex_index = cloth_vertex_index
    #             break
    #
    #     assert matching_cloth_vertex_index is not None, \
    #         f"Could not match cloth vertex for drawable geometry vertex #{geom_vertex_index} {Vector(geom_vertex)}"
    #
    #     mesh_vertex_index = cloth_to_mesh_vertex_map[matching_cloth_vertex_index]
    #     assert geom_to_mesh_map[geom_vertex_index] == -1, f"Geometry vertex #{geom_vertex_index} already assigned"
    #     assert mesh_to_geom_map[mesh_vertex_index] == -1, f"Mesh vertex #{mesh_vertex_index} already assigned"
    #
    #     geom_to_mesh_map[geom_vertex_index] = mesh_vertex_index
    #     mesh_to_geom_map[mesh_vertex_index] = geom_vertex_index
    #
    # geom_to_mesh_map = np.array(geom_to_mesh_map)
    # mesh_to_geom_map = np.array(mesh_to_geom_map)
    #
    # geom.vertex_buffer.data = geom.vertex_buffer.data[mesh_to_geom_map]
    # geom.index_buffer.data = geom_to_mesh_map[geom.index_buffer.data]
    #
    # del geom_to_mesh_map
    # del mesh_to_geom_map

    cloth_obj_eval.to_mesh_clear()

    return char_cloth


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
