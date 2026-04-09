import bpy
import numpy as np
import pytest

from .shared import log_capture


def _make_cable_segment_vertices(pos_a, pos_b, normal, color=(0, 0, 0, 255), radius=0.03, um_dist=0.0):
    """Create the 4 raw vertices for one cable segment (2 per point: negative and positive radius).

    Returns a list of 4 vertex tuples: [A_neg, A_pos, B_neg, B_pos].
    """
    return [
        (pos_a, normal, color, (-radius, um_dist)),
        (pos_a, normal, color, (radius, um_dist)),
        (pos_b, normal, color, (-radius, um_dist)),
        (pos_b, normal, color, (radius, um_dist)),
    ]


def _make_segment_indices(base):
    """Create the 6 triangle indices for one cable segment (forward + backward tri).

    base is the index of the first raw vertex (A_neg) in the segment's 4 vertices.
    Layout: A_neg=base, A_pos=base+1, B_neg=base+2, B_pos=base+3
    Forward tri: (A_neg, B_neg, A_pos) -> v0=A_neg, v1=B_neg, v2=A_pos
    Backward tri: (A_pos, B_neg, B_pos) -> v0=A_pos, v1=B_neg, v2=B_pos
    """
    return [base, base + 2, base + 1, base + 1, base + 2, base + 3]


def _build_vertex_array(vertex_tuples):
    """Build a structured numpy array from a list of (position, normal, color, texcoord) tuples."""
    from szio.gta5.cwxml import VertexBuffer

    dtype = [VertexBuffer.VERT_ATTR_DTYPES[name] for name in ("Position", "Normal", "Colour0", "TexCoord0")]
    n = len(vertex_tuples)
    arr = np.empty(n, dtype=dtype)
    for i, (pos, nrm, col, tc) in enumerate(vertex_tuples):
        arr[i]["Position"] = pos
        arr[i]["Normal"] = nrm
        arr[i]["Colour0"] = col
        arr[i]["TexCoord0"] = tc
    return arr


@pytest.fixture()
def cable_material():
    """Create a minimal cable material, cleaned up after test."""
    mat = bpy.data.materials.new("test_cable_mat")
    mat.shader_properties.filename = "cable.sps"
    yield mat
    bpy.data.materials.remove(mat)


def _build_cable(name, vertex_arr, ind_arr, mat_inds, materials):
    """Build a cable mesh and return it. Caller must clean up via bpy.data.meshes.remove()."""
    from ..ydr.cable_mesh_builder import CableMeshBuilder

    builder = CableMeshBuilder(name, vertex_arr, ind_arr, mat_inds, materials)
    return builder.build()


def test_cables_happy_path_two_segment_cable(cable_material):
    """Normal 3-point cable A-B-C with no corruption. Verifies the non-corrupted path produces
    correct vertices, edges, and attributes.
    Expected: 3 vertices, 2 edges, correct radius/phase/diffuse attributes, no warnings.
    """
    normal = (1.0, 0.0, 0.0)
    pos_a = (0.0, 0.0, 0.0)
    pos_b = (1.0, 0.0, 0.0)
    pos_c = (2.0, 0.0, 0.0)
    color = (50, 100, 0, 200)
    radius = 0.025

    verts = _make_cable_segment_vertices(pos_a, pos_b, normal, color=color, radius=radius, um_dist=0.0)
    verts.extend(_make_cable_segment_vertices(pos_b, pos_c, normal, color=color, radius=radius, um_dist=0.5))

    vertex_arr = _build_vertex_array(verts)
    ind_arr = np.array(
        _make_segment_indices(0) + _make_segment_indices(4),
        dtype=np.uint32,
    )
    mat_inds = np.zeros(4, dtype=np.uint32)

    with log_capture() as logs:
        mesh = _build_cable("test_happy", vertex_arr, ind_arr, mat_inds, [cable_material])

    try:
        assert len(mesh.vertices) == 3, f"Expected 3 vertices, got {len(mesh.vertices)}"
        assert len(mesh.edges) == 2, f"Expected 2 edges, got {len(mesh.edges)}"
        assert len(logs.warnings) == 0, f"Expected no warnings, got {logs.warnings}"

        # Check that cable attributes are present and have correct length
        from ..ydr.cable import CableAttr

        assert CableAttr.RADIUS in mesh.attributes
        assert len(mesh.attributes[CableAttr.RADIUS].data) == 3
        # Check radius value (abs of TexCoord0.x)
        assert abs(mesh.attributes[CableAttr.RADIUS].data[0].value - radius) < 1e-6
        # Check phase_offset (Colour0.r/255, Colour0.g/255)
        assert CableAttr.PHASE_OFFSET in mesh.attributes
        phase = mesh.attributes[CableAttr.PHASE_OFFSET].data[0].vector
        assert abs(phase[0] - 50 / 255) < 1e-3
        assert abs(phase[1] - 100 / 255) < 1e-3
        # Check diffuse_factor (Colour0.a/255)
        assert CableAttr.DIFFUSE_FACTOR in mesh.attributes
        assert abs(mesh.attributes[CableAttr.DIFFUSE_FACTOR].data[0].value - 200 / 255) < 1e-3
    finally:
        bpy.data.meshes.remove(mesh)


def test_cables_orphaned_vertex_skipped(cable_material):
    """A 3-point cable A-B-C where the last backward tri references a displaced vertex D.
    After dedup by (Position, Normal), D becomes an orphaned single-point piece.
    Expected: mesh has 3 vertices and 2 edges (A-B-C cable), warning about removed single-point piece.
    """
    normal = (1.0, 0.0, 0.0)
    pos_a = (0.0, 0.0, 0.0)
    pos_b = (1.0, 0.0, 0.0)
    pos_c = (2.0, 0.0, 0.0)
    pos_d = (2.0, 0.0, 0.001)  # Displaced from C

    # Segment A-B: 4 raw vertices (indices 0-3)
    verts = _make_cable_segment_vertices(pos_a, pos_b, normal)

    # Segment B-C forward tri + corrupted backward tri: 4 raw vertices (indices 4-7)
    # B_neg=4, B_pos=5, C_neg=6, D_pos=7 (D has different position from C)
    verts.extend(
        [
            (pos_b, normal, (0, 0, 0, 255), (-0.03, 0.0)),  # 4: B_neg
            (pos_b, normal, (0, 0, 0, 255), (0.03, 0.0)),  # 5: B_pos
            (pos_c, normal, (0, 0, 0, 255), (-0.03, 0.0)),  # 6: C_neg
            (pos_d, normal, (0, 0, 0, 255), (0.03, 0.0)),  # 7: D_pos (corrupted!)
        ]
    )

    vertex_arr = _build_vertex_array(verts)

    # Segment A-B: forward (0,2,1) backward (1,2,3)
    # Segment B-C: forward (4,6,5) backward (5,6,7) <- corrupted backward tri
    ind_arr = np.array([0, 2, 1, 1, 2, 3, 4, 6, 5, 5, 6, 7], dtype=np.uint32)
    mat_inds = np.zeros(4, dtype=np.uint32)  # 4 faces, all material 0

    with log_capture() as logs:
        mesh = _build_cable("test_orphan", vertex_arr, ind_arr, mat_inds, [cable_material])

    try:
        assert len(mesh.vertices) == 3, f"Expected 3 vertices, got {len(mesh.vertices)}"
        assert len(mesh.edges) == 2, f"Expected 2 edges, got {len(mesh.edges)}"
        assert len(logs.warnings) == 1
        assert "removed single-point piece" in logs.warnings[0]
    finally:
        bpy.data.meshes.remove(mesh)


def test_cables_duplicate_cables_merged(cable_material):
    """Two cables sharing exact same geometry.
    After dedup, both cables map to the same unique vertices, creating duplicate forward tris.
    Expected: mesh has 3 vertices and 2 edges (single cable), no warnings.
    """
    normal = (1.0, 0.0, 0.0)
    col = (128, 0, 0, 255)
    pos_a = (0.0, 0.0, 0.0)
    pos_b = (1.0, 0.0, 0.0)
    pos_c = (2.0, 0.0, 0.0)

    verts = _make_cable_segment_vertices(pos_a, pos_b, normal, color=col)  # 0-3
    verts.extend(_make_cable_segment_vertices(pos_b, pos_c, normal, color=col))  # 4-7

    verts.extend(_make_cable_segment_vertices(pos_a, pos_b, normal, color=col))  # 8-11
    verts.extend(_make_cable_segment_vertices(pos_b, pos_c, normal, color=col))  # 12-15

    vertex_arr = _build_vertex_array(verts)

    # Cable 1 triangles + Cable 2 triangles
    ind_arr = np.array(
        _make_segment_indices(0) + _make_segment_indices(4) + _make_segment_indices(8) + _make_segment_indices(12),
        dtype=np.uint32,
    )
    mat_inds = np.zeros(len(ind_arr) // 3, dtype=np.uint32)

    with log_capture() as logs:
        mesh = _build_cable("test_dup", vertex_arr, ind_arr, mat_inds, [cable_material])

    try:
        assert len(mesh.vertices) == 3, f"Expected 3 vertices, got {len(mesh.vertices)}"
        assert len(mesh.edges) == 2, f"Expected 2 edges, got {len(mesh.edges)}"
        # Duplicate connections are silently skipped, no warnings
        assert len(logs.warnings) == 0, f"Expected no warnings, got {logs.warnings}"
    finally:
        bpy.data.meshes.remove(mesh)


def test_cables_conflicting_junction_handled(cable_material):
    """Cable 1: A-B-C. Cable 2: D-E-C sharing terminal endpoint C with identical Normal.
    Cable 2's E->C face has incoming conflict (prev_map[C] = B from Cable 1).
    C should be duplicated so both cables are preserved.
    Expected: 6 vertices (A,B,C,D,E,C'), 4 edges, no warnings.
    """
    normal = (1.0, 0.0, 0.0)
    pos_a = (0.0, 0.0, 0.0)
    pos_b = (1.0, 0.0, 0.0)
    pos_c = (2.0, 0.0, 0.0)
    pos_d = (0.0, 1.0, 0.0)
    pos_e = (1.0, 1.0, 0.0)

    # Cable 1: A-B (0-3), B-C (4-7)
    verts = _make_cable_segment_vertices(pos_a, pos_b, normal)
    verts.extend(_make_cable_segment_vertices(pos_b, pos_c, normal))

    # Cable 2: D-E (8-11), E-C (12-15) - shares terminal endpoint C with same Normal
    col2 = (128, 128, 0, 255)
    verts.extend(_make_cable_segment_vertices(pos_d, pos_e, normal, color=col2))
    verts.extend(_make_cable_segment_vertices(pos_e, pos_c, normal, color=col2))

    vertex_arr = _build_vertex_array(verts)

    ind_arr = np.array(
        _make_segment_indices(0) + _make_segment_indices(4) + _make_segment_indices(8) + _make_segment_indices(12),
        dtype=np.uint32,
    )
    mat_inds = np.zeros(len(ind_arr) // 3, dtype=np.uint32)

    with log_capture() as logs:
        mesh = _build_cable("test_conflict", vertex_arr, ind_arr, mat_inds, [cable_material])

    try:
        # Both cables preserved: A-B-C and D-E-C' (C duplicated)
        assert len(mesh.vertices) == 6, f"Expected 6 vertices, got {len(mesh.vertices)}"
        assert len(mesh.edges) == 4, f"Expected 4 edges, got {len(mesh.edges)}"
        assert len(logs.warnings) == 0, f"Expected no warnings, got {logs.warnings}"
    finally:
        bpy.data.meshes.remove(mesh)


def test_cables_corrupted_normal_forward_tri(cable_material):
    """Cable A-B-C where the B-C segment's forward tri has divergent normals at B.
    B_neg has normal1 but B_pos has normal2, so after dedup B creates 2 unique vertices.
    The incoming A-B segment connects to B(normal1). The corrupted B-C forward tri should
    still connect B(normal1)->C using the position-matching fallback.
    Expected: 3 vertices, 2 edges (complete A-B-C cable), 1 warning about orphaned B(normal2).
    """
    normal = (1.0, 0.0, 0.0)
    normal_bad = (0.0, 1.0, 0.0)  # Corrupted normal at B
    pos_a = (0.0, 0.0, 0.0)
    pos_b = (1.0, 0.0, 0.0)
    pos_c = (2.0, 0.0, 0.0)

    # Segment A-B: normal forward/backward (indices 0-3)
    verts = _make_cable_segment_vertices(pos_a, pos_b, normal)

    # Segment B-C: B_neg has correct normal, B_pos has WRONG normal (indices 4-7)
    verts.extend(
        [
            (pos_b, normal, (0, 0, 0, 255), (-0.03, 0.0)),  # 4: B_neg (correct normal)
            (pos_b, normal_bad, (0, 0, 0, 255), (0.03, 0.0)),  # 5: B_pos (WRONG normal!)
            (pos_c, normal, (0, 0, 0, 255), (-0.03, 0.0)),  # 6: C_neg
            (pos_c, normal, (0, 0, 0, 255), (0.03, 0.0)),  # 7: C_pos
        ]
    )

    vertex_arr = _build_vertex_array(verts)

    # Segment A-B: forward (0,2,1) backward (1,2,3)
    # Segment B-C: forward (4,6,5) backward (5,6,7) <- forward tri has divergent normals at B
    ind_arr = np.array([0, 2, 1, 1, 2, 3, 4, 6, 5, 5, 6, 7], dtype=np.uint32)
    mat_inds = np.zeros(4, dtype=np.uint32)

    with log_capture() as logs:
        mesh = _build_cable("test_bad_normal", vertex_arr, ind_arr, mat_inds, [cable_material])

    try:
        # Full cable A-B-C should be intact despite corrupted normal
        assert len(mesh.vertices) == 3, f"Expected 3 vertices, got {len(mesh.vertices)}"
        assert len(mesh.edges) == 2, f"Expected 2 edges, got {len(mesh.edges)}"
        # The B(normal_bad) vertex is silently suppressed (position covered by B in chain)
        assert len(logs.warnings) == 0, f"Expected no warnings, got {logs.warnings}"
    finally:
        bpy.data.meshes.remove(mesh)


def test_cables_corrupted_position_forward_tri(cable_material):
    """Cable A-B-C where point A's neg/pos pair has different positions (same Normal).
    After dedup, A creates 2 unique vertices. The corrupted forward tri should keep both
    as separate cable points, forming a chain: A_neg → A_pos → B → C.
    Expected: 4 vertices, 3 edges (both positions preserved), no warnings.
    """
    normal = (1.0, 0.0, 0.0)
    pos_a = (0.0, 0.0, 0.0)
    pos_a_displaced = (0.05, 0.0, 0.0)  # Corrupted A_pos position
    pos_b = (1.0, 0.0, 0.0)
    pos_c = (2.0, 0.0, 0.0)

    # Segment A-B: A_neg at pos_a, A_pos at pos_a_displaced (corrupted!)
    verts = [
        (pos_a, normal, (0, 0, 0, 255), (-0.03, 0.0)),  # 0: A_neg
        (pos_a_displaced, normal, (0, 0, 0, 255), (0.03, 0.0)),  # 1: A_pos (DIFFERENT position!)
        (pos_b, normal, (0, 0, 0, 255), (-0.03, 0.0)),  # 2: B_neg
        (pos_b, normal, (0, 0, 0, 255), (0.03, 0.0)),  # 3: B_pos
    ]

    # Segment B-C: normal
    verts.extend(_make_cable_segment_vertices(pos_b, pos_c, normal))  # 4-7

    vertex_arr = _build_vertex_array(verts)

    # Segment A-B: forward (0,2,1) backward (1,2,3)
    # Segment B-C: forward (4,6,5) backward (5,6,7)
    ind_arr = np.array([0, 2, 1, 1, 2, 3, 4, 6, 5, 5, 6, 7], dtype=np.uint32)
    mat_inds = np.zeros(4, dtype=np.uint32)

    with log_capture() as logs:
        mesh = _build_cable("test_pos_corrupt", vertex_arr, ind_arr, mat_inds, [cable_material])

    try:
        # Both A positions preserved + B + C = 4 vertices, 3 edges
        assert len(mesh.vertices) == 4, f"Expected 4 vertices, got {len(mesh.vertices)}"
        assert len(mesh.edges) == 3, f"Expected 3 edges, got {len(mesh.edges)}"
        assert len(logs.warnings) == 0, f"Expected no warnings, got {logs.warnings}"
    finally:
        bpy.data.meshes.remove(mesh)


def test_cables_mutual_cycle_handled(cable_material):
    """Cable 1: A->B. Cable 2: B->A with same Normal at both points.
    Cable 2's B->A forward tri would create a cycle with Cable 1's A->B.
    Expected: Cable 1 intact (2 verts, 1 edge). Warning about mutual connection.
    """
    normal = (1.0, 0.0, 0.0)
    pos_a = (0.0, 0.0, 0.0)
    pos_b = (1.0, 0.0, 0.0)

    # Cable 1: A->B (0-3)
    verts = _make_cable_segment_vertices(pos_a, pos_b, normal)

    # Cable 2: B->A (4-7) - reverse direction, same Normal
    col2 = (200, 200, 0, 255)
    verts.extend(_make_cable_segment_vertices(pos_b, pos_a, normal, color=col2))

    vertex_arr = _build_vertex_array(verts)

    ind_arr = np.array(
        _make_segment_indices(0) + _make_segment_indices(4),
        dtype=np.uint32,
    )
    mat_inds = np.zeros(len(ind_arr) // 3, dtype=np.uint32)

    with log_capture() as logs:
        mesh = _build_cable("test_cycle", vertex_arr, ind_arr, mat_inds, [cable_material])

    try:
        # Cable 1 (A-B) should be intact
        assert len(mesh.vertices) == 2, f"Expected 2 vertices, got {len(mesh.vertices)}"
        assert len(mesh.edges) == 1, f"Expected 1 edge, got {len(mesh.edges)}"
        assert len(logs.warnings) == 1
        assert "mutual connection" in logs.warnings[0]
    finally:
        bpy.data.meshes.remove(mesh)


def test_cables_degenerate_v1_eq_v2(cable_material):
    """Bridge vertex pattern: A_bridge has different normal from B's neg/pos pair.
    After dedup, A_bridge becomes a separate unique vertex, B_neg and B_pos merge.
    Forward tri (A_bridge, B_neg, B_pos) -> (U_bridge, U_B, U_B) with dist < 0.1 and v1==v2.
    Should be treated as simple forward tri: U_bridge -> U_B.
    Expected: 3 vertices (A_bridge, B, C), 2 edges, no warnings.
    (e.g. sc1_05_cablemesh28159_thvy -- bridge vertex at cable junction)
    """
    normal = (1.0, 0.0, 0.0)
    normal_bridge = (0.0, 1.0, 0.0)  # Different normal for bridge vertex
    pos_a = (0.0, 0.0, 0.0)
    pos_b = (0.05, 0.0, 0.0)  # Close to A (< 0.1)
    pos_c = (1.0, 0.0, 0.0)

    verts = [
        (pos_a, normal_bridge, (0, 0, 0, 255), (0.0, 0.0)),  # 0: A_bridge (unique normal+pos)
        (pos_b, normal, (0, 0, 0, 255), (-0.03, 0.0)),  # 1: B_neg
        (pos_b, normal, (0, 0, 0, 255), (0.03, 0.0)),  # 2: B_pos (merges with B_neg)
    ]
    # Segment B-C: normal
    verts.extend(_make_cable_segment_vertices(pos_b, pos_c, normal))  # 3-6

    vertex_arr = _build_vertex_array(verts)

    # Bridge forward tri: (A_bridge, B_neg, B_pos) = (0, 1, 2)
    # Segment B-C: forward (3, 5, 4) backward (4, 5, 6)
    ind_arr = np.array([0, 1, 2, 3, 5, 4, 4, 5, 6], dtype=np.uint32)
    mat_inds = np.zeros(3, dtype=np.uint32)

    with log_capture() as logs:
        mesh = _build_cable("test_degen", vertex_arr, ind_arr, mat_inds, [cable_material])

    try:
        # A_bridge -> B -> C = 3 vertices, 2 edges
        assert len(mesh.vertices) == 3, f"Expected 3 vertices, got {len(mesh.vertices)}"
        assert len(mesh.edges) == 2, f"Expected 2 edges, got {len(mesh.edges)}"
        assert len(logs.warnings) == 0, f"Expected no warnings, got {logs.warnings}"
    finally:
        bpy.data.meshes.remove(mesh)


def test_cables_bridge_forward_tri(cable_material):
    """Bridge forward tri: v0 and v1 at same position with different normals (bridge + neg/pos
    pair), v2 at next cable point. Connection direction is reversed: next_map[v2] = pair_vertex.
    The bridge orphan is silently suppressed (position covered by connected vertex).
    Expected: 3 vertices (A, B, C), 2 edges, no warnings.
    (e.g. sc1_05_cablemesh28159_thvy — bridge forward tris at cable junctions)
    """
    normal_cable = (1.0, 0.0, 0.0)
    normal_bridge = (0.0, 1.0, 0.0)
    pos_a = (0.0, 0.0, 0.0)
    pos_b = (1.0, 0.0, 0.0)  # Bridge point (3 raw vertices)
    pos_c = (2.0, 0.0, 0.0)

    verts = [
        # Standard segment B->C (4 raw vertices)
        (pos_b, normal_cable, (0, 0, 0, 255), (-0.03, 0.0)),  # 0: B_neg
        (pos_b, normal_cable, (0, 0, 0, 255), (0.03, 0.0)),  # 1: B_pos
        (pos_c, normal_cable, (0, 0, 0, 255), (-0.03, 0.0)),  # 2: C_neg
        (pos_c, normal_cable, (0, 0, 0, 255), (0.03, 0.0)),  # 3: C_pos
        # Bridge forward tri vertices: B_neg, B_bridge, A_neg
        (pos_b, normal_cable, (0, 0, 0, 255), (-0.03, 0.0)),  # 4: B_neg (dup of 0)
        (pos_b, normal_bridge, (0, 0, 0, 255), (0.0, 0.0)),  # 5: B_bridge (unique normal)
        (pos_a, normal_cable, (0, 0, 0, 255), (-0.03, 0.0)),  # 6: A_neg
    ]

    vertex_arr = _build_vertex_array(verts)

    # After dedup by (Position, Normal):
    #   U_B = B (from 0,1,4 — same Position+Normal)
    #   U_C = C (from 2,3)
    #   U_bridge = B_bridge (from 5 — unique Normal)
    #   U_A = A (from 6)
    #
    # Face 0: Standard forward B->C: (0, 2, 1) -> (U_B, U_C, U_B) -> v0==v2
    # Face 1: Backward B->C: (1, 2, 3) -> skipped
    # Face 2: Bridge forward: (4, 5, 6) -> (U_B, U_bridge, U_A)
    #   pos[v0]==pos[v1] (both at pos_b), v0!=v1 -> bridge forward
    #   U_B is connected, pair=U_B, src=U_A, v1=U_B
    #   next_map[U_A]=U_B -> chain: A -> B -> C
    ind_arr = np.array(
        [
            0,
            2,
            1,  # standard forward B->C
            1,
            2,
            3,  # backward B->C (skipped)
            4,
            5,
            6,  # bridge forward (B_neg, B_bridge, A_neg)
        ],
        dtype=np.uint32,
    )
    mat_inds = np.zeros(3, dtype=np.uint32)

    with log_capture() as logs:
        mesh = _build_cable("test_bridge_fwd", vertex_arr, ind_arr, mat_inds, [cable_material])

    try:
        # A -> B -> C = 3 vertices, 2 edges
        assert len(mesh.vertices) == 3, f"Expected 3 vertices, got {len(mesh.vertices)}"
        assert len(mesh.edges) == 2, f"Expected 2 edges, got {len(mesh.edges)}"
        # Bridge orphan silently suppressed (position covered by B in chain)
        assert len(logs.warnings) == 0, f"Expected no warnings, got {logs.warnings}"
    finally:
        bpy.data.meshes.remove(mesh)


def test_cables_false_match_close_adjacent_points(cable_material):
    """Backward tri between two close adjacent cable points (distance < _MAX_CORRUPTED_PAIR_DISTANCE).
    The proximity check should reject this as a false match because d_pair/d_seg >= _FALSE_MATCH_RATIO.
    Expected: 3 vertices (A, B, C), 2 edges, no warnings. The backward tri is skipped.
    (e.g. sc1_05_cablemesh28159_thvy — backward tri between close adjacent points)
    """
    normal = (1.0, 0.0, 0.0)
    pos_a = (0.0, 0.0, 0.0)
    pos_b = (0.08, 0.0, 0.0)  # Close to A (< 0.1) but adjacent, not corrupted pair
    pos_c = (1.0, 0.0, 0.0)

    # Segment A-B: forward + backward
    verts = _make_cable_segment_vertices(pos_a, pos_b, normal)  # 0-3
    # Segment B-C: forward + backward
    verts.extend(_make_cable_segment_vertices(pos_b, pos_c, normal))  # 4-7

    vertex_arr = _build_vertex_array(verts)

    # Normal triangles — the backward tri of A-B has v0=A_pos(at A), v2=B_pos(at B)
    # with distance 0.08, which is < 0.1 threshold. But d_pair/d_seg = 0.08/0.08 = 1.0,
    # which is >= 0.5, so it's correctly rejected as a false match.
    ind_arr = np.array(
        _make_segment_indices(0) + _make_segment_indices(4),
        dtype=np.uint32,
    )
    mat_inds = np.zeros(4, dtype=np.uint32)

    with log_capture() as logs:
        mesh = _build_cable("test_false_match", vertex_arr, ind_arr, mat_inds, [cable_material])

    try:
        assert len(mesh.vertices) == 3, f"Expected 3 vertices, got {len(mesh.vertices)}"
        assert len(mesh.edges) == 2, f"Expected 2 edges, got {len(mesh.edges)}"
        assert len(logs.warnings) == 0, f"Expected no warnings, got {logs.warnings}"
    finally:
        bpy.data.meshes.remove(mesh)


def test_cables_triple_junction_duplicated(cable_material):
    """Three cables sharing the same terminal endpoint C with identical Normal.
    Cable 1: A-B-C. Cable 2: D-E-C. Cable 3: F-G-C.
    C should be duplicated twice so all three cables are preserved.
    Expected: 9 vertices (A,B,C,D,E,C',F,G,C''), 6 edges, no warnings.
    """
    normal = (1.0, 0.0, 0.0)
    pos_a = (0.0, 0.0, 0.0)
    pos_b = (1.0, 0.0, 0.0)
    pos_c = (2.0, 0.0, 0.0)
    pos_d = (0.0, 1.0, 0.0)
    pos_e = (1.0, 1.0, 0.0)
    pos_f = (0.0, 2.0, 0.0)
    pos_g = (1.0, 2.0, 0.0)

    # Cable 1: A-B-C
    verts = _make_cable_segment_vertices(pos_a, pos_b, normal)
    verts.extend(_make_cable_segment_vertices(pos_b, pos_c, normal))
    # Cable 2: D-E-C
    verts.extend(_make_cable_segment_vertices(pos_d, pos_e, normal))
    verts.extend(_make_cable_segment_vertices(pos_e, pos_c, normal))
    # Cable 3: F-G-C
    verts.extend(_make_cable_segment_vertices(pos_f, pos_g, normal))
    verts.extend(_make_cable_segment_vertices(pos_g, pos_c, normal))

    vertex_arr = _build_vertex_array(verts)

    ind_arr = np.array(
        _make_segment_indices(0)
        + _make_segment_indices(4)
        + _make_segment_indices(8)
        + _make_segment_indices(12)
        + _make_segment_indices(16)
        + _make_segment_indices(20),
        dtype=np.uint32,
    )
    mat_inds = np.zeros(len(ind_arr) // 3, dtype=np.uint32)

    with log_capture() as logs:
        mesh = _build_cable("test_triple", vertex_arr, ind_arr, mat_inds, [cable_material])

    try:
        # All three cables: A-B-C, D-E-C', F-G-C'' = 9 vertices, 6 edges
        assert len(mesh.vertices) == 9, f"Expected 9 vertices, got {len(mesh.vertices)}"
        assert len(mesh.edges) == 6, f"Expected 6 edges, got {len(mesh.edges)}"
        assert len(logs.warnings) == 0, f"Expected no warnings, got {logs.warnings}"
    finally:
        bpy.data.meshes.remove(mesh)
