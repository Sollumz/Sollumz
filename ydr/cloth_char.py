import numpy as np
from numpy.typing import NDArray
import bpy
from bpy.types import (
    Object,
    Mesh,
)
from typing import Optional, NamedTuple
from mathutils import (
    Vector,
    Matrix,
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
from ..shared.geometry import (
    tris_normals,
    tris_areas,
    tris_areas_from_verts,
    distance_signed_point_to_planes,
)


def calculate_smooth_vertex_normals(vertices: NDArray[np.float32], triangles: NDArray[np.uint32]) -> NDArray[np.float32]:
    """Calculate smooth vertex normals by averaging face normals weighted by face area."""
    num_verts = len(vertices)
    vertex_normals = np.zeros((num_verts, 3), dtype=np.float32)
    
    # Get triangle vertices and calculate face normals
    tri_verts = vertices[triangles]
    face_normals = tris_normals(tri_verts)
    face_areas = tris_areas(tri_verts)
    
    # Accumulate area-weighted normals for each vertex
    for tri_idx, tri in enumerate(triangles):
        normal = face_normals[tri_idx] * face_areas[tri_idx]
        for vert_idx in tri:
            vertex_normals[vert_idx] += normal
    
    # Normalize the accumulated normals
    norms = np.linalg.norm(vertex_normals, axis=1, keepdims=True)
    norms = np.where(norms > 0, norms, 1.0)  # Avoid division by zero
    vertex_normals = vertex_normals / norms
    
    return vertex_normals
from ..sollumz_properties import (
    SollumType,
    SOLLUMZ_UI_NAMES,
)
from ..ybn.ybnexport import (
    create_composite_xml,
)
from .cloth import (
    mesh_get_cloth_attribute_values,
    mesh_has_cloth_attribute,
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
    dwd_obj: Object,
    drawable_obj: Object,
    controller_name: str,
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
    from .ydrexport import create_skeleton_xml
    armature_obj = drawable_obj if drawable_obj.type == "ARMATURE" else dwd_obj
    assert armature_obj.type == "ARMATURE", "Drawable with cloth or its parent drawable dictionary must have an armature"
    skeleton = create_skeleton_xml(armature_obj)

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
        bones = skeleton.bones
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

    char_cloth_props = drawable_obj.drawable_properties.char_cloth

    controller = char_cloth.controller
    controller.name = controller_name
    controller.flags = 2  # owns bridge
    controller.pin_radius_scale = char_cloth_props.pin_radius_scale
    controller.pin_radius_threshold = char_cloth_props.pin_radius_threshold
    controller.wind_scale = char_cloth_props.wind_scale
    controller.vertices = vertices
    bridge = controller.bridge
    bridge.vertex_count_high = num_vertices
    if mesh_has_cloth_attribute(cloth_mesh, ClothAttr.PIN_RADIUS):
        pin_radius = mesh_get_cloth_attribute_values(cloth_mesh, ClothAttr.PIN_RADIUS)
        bridge.pin_radius_high = [
            pin_radius[mi][set_idx]
            for set_idx in range(char_cloth_props.num_pin_radius_sets)
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
        
        # Get compression weight from edge attribute (default 0.8 if not set)
        edge_index = None
        for edge in cloth_mesh.edges:
            if (edge.vertices[0] == mesh_v0 and edge.vertices[1] == mesh_v1) or \
               (edge.vertices[0] == mesh_v1 and edge.vertices[1] == mesh_v0):
                edge_index = edge.index
                break
        
        if edge_index is not None and cloth_mesh.attributes.get(".cloth.edge_compression"):
            verlet_edge.compression_weight = cloth_mesh.attributes[".cloth.edge_compression"].data[edge_index].value
        else:
            verlet_edge.compression_weight = 0.0  # Default for edges without manual compression set
        
        return verlet_edge

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

    from .cloth_env import _cloth_sort_verlet_edges
    edges = _cloth_sort_verlet_edges(edges)
    custom_edges = _cloth_sort_verlet_edges(custom_edges)

    # Calculate cloth thickness distances based on triangle normal casting
    def calculate_cloth_vertex_distances():
        MAX_CAST_DISTANCE = 0.05  # 5cm limit to prevent cross-binding
        
        # Initialize vertex distances (W component)
        vertex_distances = np.zeros(num_vertices)
        
        # Get triangle data
        cloth_tris = np.array(cloth_mesh.loop_triangles)
        
        for tri in cloth_tris:
            # Get triangle vertices
            v0_idx, v1_idx, v2_idx = tri.vertices
            v0 = vertices[v0_idx]
            v1 = vertices[v1_idx] 
            v2 = vertices[v2_idx]
            
            # Calculate triangle center and normal
            tri_center = (v0 + v1 + v2) / 3.0
            tri_normal = (v1 - v0).cross(v2 - v0).normalized()
            
            # Cast rays in both directions from triangle center
            forward_hit_distance = None
            backward_hit_distance = None
            
            # Cast forward along normal
            ray_origin = tri_center
            ray_direction = tri_normal
            
            # Check intersection with other triangles within distance limit
            for other_tri in cloth_tris:
                if other_tri.index == tri.index:
                    continue
                    
                # Get other triangle vertices
                ov0_idx, ov1_idx, ov2_idx = other_tri.vertices
                ov0 = vertices[ov0_idx]
                ov1 = vertices[ov1_idx]
                ov2 = vertices[ov2_idx]
                
                # Simple ray-triangle intersection check along normal direction
                # Project other triangle center onto ray direction
                other_center = (ov0 + ov1 + ov2) / 3.0
                to_other = other_center - ray_origin
                projection_dist = to_other.dot(ray_direction)
                
                # Check if within casting distance and in correct direction
                if 0 < projection_dist <= MAX_CAST_DISTANCE:
                    if forward_hit_distance is None or projection_dist < forward_hit_distance:
                        forward_hit_distance = projection_dist
                
                # Check backward direction  
                if -MAX_CAST_DISTANCE <= projection_dist < 0:
                    backward_dist = abs(projection_dist)
                    if backward_hit_distance is None or backward_dist < backward_hit_distance:
                        backward_hit_distance = backward_dist
            
            # Calculate thickness for this triangle's vertices
            if forward_hit_distance is not None and backward_hit_distance is not None:
                # Use total distance between forward and backward hits
                thickness = forward_hit_distance + backward_hit_distance
            elif forward_hit_distance is not None:
                # Only forward hit, use that distance
                thickness = forward_hit_distance
            elif backward_hit_distance is not None:
                # Only backward hit, use that distance  
                thickness = backward_hit_distance
            else:
                # No hits within range, use minimal thickness
                thickness = 1.152031E-19  # Original minimal value
            
            # Apply thickness to triangle vertices
            vertex_distances[v0_idx] = max(vertex_distances[v0_idx], thickness)
            vertex_distances[v1_idx] = max(vertex_distances[v1_idx], thickness)
            vertex_distances[v2_idx] = max(vertex_distances[v2_idx], thickness)
        
        # Create vertices with calculated distances as W component
        vertices_with_distance = []
        for i, (vertex, distance) in enumerate(zip(vertices, vertex_distances)):
            vertex_with_w = Vector((vertex.x, vertex.y, vertex.z, distance))
            vertices_with_distance.append(vertex_with_w)
            
        return vertices_with_distance
    
    vertices_with_distances = calculate_cloth_vertex_distances()

    controller.indices = indices
    verlet = controller.cloth_high
    verlet.vertex_positions = vertices_with_distances
    verlet.vertex_normals = normals
    verlet.bb_min = Vector(np.min(vertices, axis=0))
    verlet.bb_max = Vector(np.max(vertices, axis=0))
    verlet.switch_distance_up = 9999.0
    verlet.switch_distance_down = 9999.0
    verlet.flags = 0
    verlet.dynamic_pin_list_size = (num_vertices + 31) // 32
    verlet.cloth_weight = char_cloth_props.weight
    verlet.edges = edges
    verlet.pinned_vertices_count = num_pinned
    verlet.custom_edges = custom_edges
    verlet.bounds = None  # char cloth doesn't have embedded world bounds

    # Cloth vertex bindings to bones
    bind_weights, bind_indices, bind_bone_indices = _cloth_char_get_cloth_to_bone_bindings(
        cloth_mesh, cloth_obj_eval, armature_obj
    )
    bind_bone_ids = [skeleton.bones[i].tag for i in bind_bone_indices]
    bindings = [None] * num_vertices
    for i in range(num_vertices):
        binding = CharacterClothBinding()
        binding.weights = Vector(bind_weights[i])
        binding.indices = tuple(bind_indices[i])
        bindings[mesh_to_cloth_vertex_map[i]] = binding

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


def _cloth_char_get_cloth_to_bone_bindings(
    cloth_mesh: Mesh,
    cloth_obj: Object,
    armature_obj: Object
) -> tuple[NDArray[np.float32], NDArray[np.uint32], list[int]]:
    from .vertex_buffer_builder import normalize_weights, get_sorted_vertex_group_elements, try_get_bone_by_vgroup

    bone_by_vgroup = try_get_bone_by_vgroup(cloth_obj, armature_obj)
    assert bone_by_vgroup is not None

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


def cloth_char_get_mesh_to_cloth_bindings(
    cloth: CharacterCloth,
    mesh_binded_verts: NDArray[np.float32],
    mesh_binded_verts_normals: NDArray[np.float32],
    max_distance: float | None = None,
) -> tuple[NDArray[np.float32], NDArray[np.uint32], list[ClothDiagMeshBindingError]]:
    # Max distance from mesh vertex to cloth triangle to be considered
    # Get from user property if not explicitly provided
    if max_distance is None:
        max_distance = bpy.context.window_manager.sz_ui_cloth_binding_distance
    MAX_DISTANCE_THRESHOLD = max_distance

    errors = []

    num_binded_verts = len(mesh_binded_verts)

    cloth_verts = np.array(cloth.controller.vertices)
    cloth_tris = np.array(cloth.controller.indices).reshape((-1, 3))
    cloth_tris_verts = cloth_verts[cloth_tris]
    
    # Calculate smooth vertex normals for the cloth mesh
    cloth_vertex_normals = calculate_smooth_vertex_normals(cloth_verts, cloth_tris)
    cloth_tris_vertex_normals = cloth_vertex_normals[cloth_tris]  # Shape: (num_tris, 3, 3) - for each tri, 3 vertex normals
    
    # Still need flat normals for initial rough projection and face orientation
    cloth_tris_normals = tris_normals(cloth_tris_verts)
    cloth_tris_normals_neg = -cloth_tris_normals
    cloth_tris_areas = tris_areas(cloth_tris_verts)
    cloth_tris_v0, cloth_tris_v1, cloth_tris_v2 = cloth_tris_verts[:, 0], cloth_tris_verts[:, 1], cloth_tris_verts[:, 2]

    # Compute the dot product to determine which verts are facing inside or outside by comparing the normals and the
    # direction to the origin (0,0). Flattened to 2D on the XY plane (ignore Z) to reduce issues with the angled cloth
    # or cloth far from the origin (i.e. face bandanas). Most cloths wrap the ped model around the Z axis (i.e. vertical
    # tube), so when the verts are flattened it will be kind of a circle around the origin. This probably won't work
    # well if the cloth is placed more like a horizontal tube (on an animal maybe?). Will need more complex logic or
    # some user input to handle that, we ignore it for now.
    mesh_binded_dot_product = np.sum(mesh_binded_verts_normals[:,:2] * -mesh_binded_verts[:,:2], axis=1)
    mesh_binded_verts_facing_inside = mesh_binded_dot_product > 0.0

    ind_arr = np.empty((num_binded_verts, 4), dtype=np.uint32)
    weights_arr = np.empty((num_binded_verts, 4), dtype=np.float32)

    # Bind each mesh vertex to a cloth triangle using smooth normal interpolation
    for mesh_vert_idx in range(num_binded_verts):
        mesh_vert = mesh_binded_verts[mesh_vert_idx]
        mesh_vert_facing_inside = mesh_binded_verts_facing_inside[mesh_vert_idx]

        if mesh_vert_facing_inside:
            # Flip winding order
            this_cloth_tris_normals = cloth_tris_normals_neg
            this_cloth_tris_vertex_normals = -cloth_tris_vertex_normals  # Flip smooth normals too
            this_cloth_tris_v0 = cloth_tris_v1
            this_cloth_tris_v1 = cloth_tris_v0
        else:
            this_cloth_tris_normals = cloth_tris_normals
            this_cloth_tris_vertex_normals = cloth_tris_vertex_normals
            this_cloth_tris_v0 = cloth_tris_v0
            this_cloth_tris_v1 = cloth_tris_v1

        # Step 1: Initial projection using flat triangle normals (fast)
        distance_to_tris = distance_signed_point_to_planes(mesh_vert, this_cloth_tris_v0, this_cloth_tris_normals)
        projected_to_tris = mesh_vert - this_cloth_tris_normals * distance_to_tris[:, np.newaxis]

        # Calculate initial barycentric coordinates
        tris_areas0 = tris_areas_from_verts(this_cloth_tris_v1, cloth_tris_v2, projected_to_tris)
        tris_areas1 = tris_areas_from_verts(cloth_tris_v2, this_cloth_tris_v0, projected_to_tris)
        tris_areas2 = tris_areas_from_verts(this_cloth_tris_v0, this_cloth_tris_v1, projected_to_tris)

        tris_w0 = tris_areas0 / cloth_tris_areas
        tris_w1 = tris_areas1 / cloth_tris_areas
        tris_w2 = tris_areas2 / cloth_tris_areas

        # Filter to candidate triangles based on initial projection
        condition_projection = (tris_w0 + tris_w1 + tris_w2) < 1.05
        condition_distance = np.abs(distance_to_tris) < MAX_DISTANCE_THRESHOLD
        valid_tris_mask = condition_projection & condition_distance
        valid_tris_indices = np.where(valid_tris_mask)[0]
        
        if not valid_tris_mask.any():
            errors.append(ClothDiagMeshBindingError(
                Vector(mesh_vert),
                error_projection=not condition_projection.any(),
                error_distance=not condition_distance.any(),
                error_multiple_matches=False,
            ))
            continue

        # Step 2: Refine projection for candidate triangles using smooth normals
        # For each candidate triangle, iteratively find the projection using interpolated smooth normals
        best_tri_index = None
        best_distance = float('inf')
        best_weights = None
        best_actual_distance = None
        
        for tri_idx in valid_tris_indices:
            # Get triangle data
            v0 = this_cloth_tris_v0[tri_idx]
            v1 = this_cloth_tris_v1[tri_idx]
            v2 = cloth_tris_v2[tri_idx]
            n0, n1, n2 = this_cloth_tris_vertex_normals[tri_idx]
            
            # Start with initial barycentric weights from flat projection
            w0, w1, w2 = tris_w0[tri_idx], tris_w1[tri_idx], tris_w2[tri_idx]
            
            # Iteratively refine projection using interpolated smooth normals
            MAX_ITERATIONS = 3
            for iteration in range(MAX_ITERATIONS):
                # Clamp weights to valid range
                w0 = max(0.0, min(1.0, w0))
                w1 = max(0.0, min(1.0, w1))
                w2 = max(0.0, min(1.0, w2))
                
                # Normalize weights to sum to 1
                weight_sum = w0 + w1 + w2
                if weight_sum > 0:
                    w0 /= weight_sum
                    w1 /= weight_sum
                    w2 /= weight_sum
                else:
                    # Fallback to triangle center
                    w0 = w1 = w2 = 1.0 / 3.0
                
                # Interpolate smooth normal at current barycentric position
                interpolated_normal = (n0 * w0 + n1 * w1 + n2 * w2)
                norm = np.linalg.norm(interpolated_normal)
                if norm > 0:
                    interpolated_normal = interpolated_normal / norm
                else:
                    interpolated_normal = this_cloth_tris_normals[tri_idx]
                
                # Project mesh vertex onto triangle using interpolated normal
                projected_point = v0 * w0 + v1 * w1 + v2 * w2
                vec_to_mesh = mesh_vert - projected_point
                signed_distance = np.dot(vec_to_mesh, interpolated_normal)
                projected_point = mesh_vert - interpolated_normal * signed_distance
                
                # Recalculate barycentric coordinates for new projection
                area0 = tris_areas_from_verts(v1[np.newaxis], v2[np.newaxis], projected_point[np.newaxis])[0]
                area1 = tris_areas_from_verts(v2[np.newaxis], v0[np.newaxis], projected_point[np.newaxis])[0]
                area2 = tris_areas_from_verts(v0[np.newaxis], v1[np.newaxis], projected_point[np.newaxis])[0]
                
                tri_area = cloth_tris_areas[tri_idx]
                new_w0 = area0 / tri_area
                new_w1 = area1 / tri_area
                new_w2 = area2 / tri_area
                
                # Check for convergence
                if abs(new_w0 - w0) < 0.001 and abs(new_w1 - w1) < 0.001 and abs(new_w2 - w2) < 0.001:
                    break
                
                w0, w1, w2 = new_w0, new_w1, new_w2
            
            # Calculate final error (3D distance from mesh vertex to projected point)
            final_projected = v0 * w0 + v1 * w1 + v2 * w2
            error = np.sum((mesh_vert - final_projected) ** 2)
            
            # Check if this triangle is better than current best
            if error < best_distance:
                best_tri_index = tri_idx
                best_distance = error
                best_weights = (w0, w1, w2)
                best_actual_distance = signed_distance

        if best_tri_index is None:
            errors.append(ClothDiagMeshBindingError(
                Vector(mesh_vert),
                error_projection=True,
                error_distance=False,
                error_multiple_matches=False,
            ))
            continue

        # Store the best binding
        b0, b1, b2 = cloth_tris[best_tri_index]
        w0, w1, w2 = best_weights
        d = best_actual_distance

        if mesh_vert_facing_inside:
            # Flip winding order back
            b1, b0 = b0, b1

        ind_arr[mesh_vert_idx, 0] = b1
        ind_arr[mesh_vert_idx, 1] = b0
        ind_arr[mesh_vert_idx, 2] = 255
        ind_arr[mesh_vert_idx, 3] = b2

        weights_arr[mesh_vert_idx, 0] = w0
        weights_arr[mesh_vert_idx, 1] = w1
        weights_arr[mesh_vert_idx, 2] = w2
        weights_arr[mesh_vert_idx, 3] = d * 10.0 + 0.5

    # Make sure weights stay in the [0, 1] range
    weights_arr.clip(0.0, 1.0, out=weights_arr)

    return weights_arr, ind_arr, errors


def cloth_char_export_dictionary(dwd_obj: Object) -> Optional[ClothDictionary]:
    cloth_dict = None

    for drawable_obj in dwd_obj.children:
        if drawable_obj.sollum_type != SollumType.DRAWABLE:
            continue

        with cloth_export_context().enter_drawable_context(drawable_obj):
            cloth = cloth_char_export(dwd_obj, drawable_obj, remove_number_suffix(dwd_obj.name))

        if cloth is None:
            continue

        if cloth_dict is None:
            cloth_dict = ClothDictionary()

        cloth_dict.append(cloth)

    return cloth_dict
