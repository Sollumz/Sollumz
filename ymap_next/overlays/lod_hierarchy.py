import functools

import blf
import bpy
import gpu
import numpy as np
from bpy.types import SpaceView3D
from bpy_extras.view3d_utils import location_3d_to_region_2d
from gpu_extras.batch import batch_for_shader

from ...sollumz_preferences import get_theme_settings
from ..context import active_group

TOOL_IDNAME = "sollumz.map_lod_hierarchy"

if bpy.app.version >= (4, 5, 0):
    POINT_SHADER_NAME = "POINT_UNIFORM_COLOR"
    POLYLINE_SMOOTH_COLOR_NAME = "POLYLINE_SMOOTH_COLOR"
else:
    POINT_SHADER_NAME = "UNIFORM_COLOR"
    POLYLINE_SMOOTH_COLOR_NAME = "SMOOTH_COLOR"

# Visual category for each entity (HD split into ORPHAN_HD vs HD)
LOD_LEVELS = ("ORPHAN_HD", "HD", "LOD", "SLOD1", "SLOD2", "SLOD3", "SLOD4")

# Visual category → window-manager visibility toggle property name
LOD_LEVEL_VIS_PROPS = {level: f"sz_ui_map_lod_overlay_show_{level.lower()}" for level in LOD_LEVELS}


def _theme_lod_colors(theme) -> dict[str, tuple]:
    """Theme RGBA per visual category (customizable in addon preferences)."""
    return {level: tuple(getattr(theme, f"map_lod_overlay_{level.lower()}")) for level in LOD_LEVELS}


def _brightened(colors: dict[str, tuple]) -> dict[str, tuple]:
    """Brightened RGB of each color, used for chain-highlighted elements (alpha is per use site)."""
    return {level: tuple(min(c + 0.3, 1.0) for c in color[:3]) for level, color in colors.items()}


# Marker size multiplier per visual category (base * factor)
LOD_SIZE_FACTORS = {
    "ORPHAN_HD": 0.5,
    "HD": 0.7,
    "LOD": 1.0,
    "SLOD1": 1.4,
    "SLOD2": 1.8,
    "SLOD3": 2.2,
    "SLOD4": 2.8,
}

# Width of the entity mesh outline glow, in screen pixels
OUTLINE_WIDTH_PX = 3.0

# Entity tuple indices (for readability)
E_UUID = 0
E_POS = 1
E_LOD = 2  # raw lod_level string from entity ("HD", "LOD", etc.)
E_NAME = 3
E_PARENT = 4
E_VISUAL = 5  # visual category ("ORPHAN_HD", "HD", "LOD", etc.)
E_COL_IDX = 6  # index in group.entities collection (for selection)
E_LINKED = 7  # linked_object reference (Object | None)


def _visual_category(lod_level: str, parent_uuid: bytes) -> str:
    """Visual category splits HD into ORPHAN_HD (HD with no parent) vs HD."""
    return "ORPHAN_HD" if lod_level == "HD" and not parent_uuid else lod_level


@functools.cache
def get_outline_shader() -> gpu.types.GPUShader:
    """Inverted-hull shader: expands vertices along their averaged normal by a screen-constant
    pixel amount. Drawn with front-face culling so the expanded shell forms a silhouette glow
    slightly larger than the mesh.
    """
    shader_info = gpu.types.GPUShaderCreateInfo()
    shader_info.push_constant("MAT4", "ModelViewProjectionMatrix")
    shader_info.push_constant("VEC2", "ViewportSize")
    shader_info.push_constant("FLOAT", "Width")
    shader_info.push_constant("VEC4", "Color")
    shader_info.vertex_in(0, "VEC3", "position")
    shader_info.vertex_in(1, "VEC3", "normal")
    shader_info.fragment_out(0, "VEC4", "FragColor")

    shader_info.vertex_source("""
        void main()
        {
            vec4 clip = ModelViewProjectionMatrix * vec4(position, 1.0f);
            vec2 clip_nor = (mat3(ModelViewProjectionMatrix) * normal).xy;
            vec2 dir = clip_nor / max(length(clip_nor), 1e-4f);
            clip.xy += dir * Width * 2.0f / ViewportSize * clip.w;
            gl_Position = clip;
        }
    """)

    shader_info.fragment_source("""
        void main()
        {
            FragColor = Color;
        }
    """)

    return gpu.shader.create_from_info(shader_info)


def _build_outline_mesh_batch(mesh) -> "gpu.types.GPUBatch | None":
    """Build a TRIS batch of (position, averaged vertex normal) in mesh-local space.

    Returns None if the mesh has no triangles or its data is not accessible
    (e.g. read-only library-linked meshes that have no triangulation cached).
    """
    try:
        if not mesh.loop_triangles:
            mesh.calc_loop_triangles()

        num_tris = len(mesh.loop_triangles)
        if num_tris == 0:
            return None

        num_verts = len(mesh.vertices)
        positions = np.empty(num_verts * 3, dtype=np.float32)
        mesh.vertices.foreach_get("co", positions)
        # Averaged per-vertex normals
        normals = np.empty(num_verts * 3, dtype=np.float32)
        mesh.vertex_normals.foreach_get("vector", normals)
        indices = np.empty(num_tris * 3, dtype=np.int32)
        mesh.loop_triangles.foreach_get("vertices", indices)
    except RuntimeError:
        return None

    return batch_for_shader(
        get_outline_shader(),
        "TRIS",
        {"position": positions.reshape((num_verts, 3)), "normal": normals.reshape((num_verts, 3))},
        indices=indices.reshape((num_tris, 3)),
    )


def _is_tool_active(context) -> bool:
    if context.mode != "OBJECT":
        return False
    tool = context.workspace.tools.from_space_view3d_mode(context.mode)
    return tool is not None and tool.idname == TOOL_IDNAME


# Module-level reference so the interactive modal can access cached data
_active_handler: "LodHierarchyOverlayDrawHandler | None" = None


class LodHierarchyOverlayDrawHandler:
    """Draws LOD hierarchy markers, connection lines, and labels in the 3D viewport.

    All entity data and GPU batches are cached and only rebuilt when the underlying
    data or visibility settings change.

    Entity tuple layout:
        (uuid, pos_tuple, lod_level, archetype_name, parent_uuid, visual_category, collection_index,
         linked_object)
    """

    def __init__(self):
        self.handler_geometry = None
        self.handler_labels = None

        # cache keys
        self._cache_group_uuid: bytes = b""
        self._cache_entity_count: int = -1
        self._cache_vis_key = None
        self._cache_selection_key: tuple = ()
        self._cache_outline_key: tuple = ()

        # Cached entity data
        self.entities: list[tuple] = []
        self.uuid_to_idx: dict[bytes, int] = {}
        self._children_by_parent: dict[bytes, list[int]] = {}

        # Visual categories currently enabled in the overlay settings (refreshed each draw)
        self.visible_levels: frozenset[str] = frozenset()

        # Theme color snapshot (refreshed in _ensure_cache when preferences change)
        self.lod_colors: dict[str, tuple] = {}
        self.lod_colors_bright: dict[str, tuple] = {}

        # Cached highlight chain
        self._chain_uuids: set[bytes] = set()

        # Click-cycling state (persisted across per-action modal invocations)
        self.cycle_hits: list[int] = []
        self.cycle_pos: tuple[int, int] = (0, 0)
        self.cycle_index: int = 0

        # Cached GPU batches: list of (batch, color_rgba, point_size), highlighted markers last
        self._marker_batches: list[tuple] = []
        self._line_batch = None
        self._line_shader = None
        self._highlight_line_batch = None

        # Outline (inverted hull) caches
        # mesh.session_uid -> GPUBatch | None; survives chain changes, evicted when outlined meshes change
        self._outline_mesh_batches: dict[int, "gpu.types.GPUBatch | None"] = {}
        # Rebuilt when the chain or outline settings change. List of (mesh_obj, batch, color_rgba).
        # matrix_world is read live at draw time so outlines track object movement.
        self._outline_draw_list: list[tuple] = []
        # Transient outline for the drag&drop hover target, managed by the interact operator
        self._hover_outline_draw_list: list[tuple] = []

    def register(self):
        self.handler_geometry = SpaceView3D.draw_handler_add(self.draw_geometry, (), "WINDOW", "POST_VIEW")
        self.handler_labels = SpaceView3D.draw_handler_add(self.draw_labels, (), "WINDOW", "POST_PIXEL")

    def unregister(self):
        if self.handler_geometry is not None:
            SpaceView3D.draw_handler_remove(self.handler_geometry, "WINDOW")
        if self.handler_labels is not None:
            SpaceView3D.draw_handler_remove(self.handler_labels, "WINDOW")

    def _rebuild_entity_cache(self, group):
        entities = []
        uuid_to_idx = {}
        children_by_parent: dict[bytes, list[int]] = {}

        for col_idx, entity in enumerate(group.entities):
            idx = len(entities)
            obj = entity.linked_object
            pos = tuple(obj.matrix_world.translation) if obj is not None else tuple(entity.position)
            uuid = entity.uuid
            parent_uuid = entity.parent_uuid
            lod_level = entity.lod_level
            visual = _visual_category(lod_level, parent_uuid)

            entities.append((uuid, pos, lod_level, entity.archetype_name, parent_uuid, visual, col_idx, obj))
            uuid_to_idx[uuid] = idx

            if parent_uuid:
                children_by_parent.setdefault(parent_uuid, []).append(idx)

        self.entities = entities
        self.uuid_to_idx = uuid_to_idx
        self._children_by_parent = children_by_parent

    def _rebuild_chain(self, group):
        """Build the union of ancestor/descendant chains for all selected entities."""
        chain: set[bytes] = set()

        # Collect UUIDs of all selected entities as seeds
        seed_uuids = []
        for idx in group.entities.iter_selected_items_indices():
            entity = group.entities[idx]
            uuid = entity.uuid
            if uuid and uuid in self.uuid_to_idx:
                chain.add(uuid)
                seed_uuids.append(uuid)

        # Walk UP from each seed
        for uuid in seed_uuids:
            current = uuid
            while True:
                idx = self.uuid_to_idx.get(current)
                if idx is None:
                    break
                parent_uuid = self.entities[idx][E_PARENT]
                if not parent_uuid or parent_uuid in chain:
                    break
                chain.add(parent_uuid)
                current = parent_uuid

        # Walk DOWN from each seed (BFS)
        queue = list(seed_uuids)
        while queue:
            pu = queue.pop()
            for child_idx in self._children_by_parent.get(pu, ()):
                child_uuid = self.entities[child_idx][E_UUID]
                if child_uuid not in chain:
                    chain.add(child_uuid)
                    queue.append(child_uuid)

        self._chain_uuids = chain

    def _rebuild_geometry_batches(self, wm, theme):
        marker_size = theme.map_lod_overlay_marker_size * bpy.context.preferences.system.ui_scale
        marker_alpha = theme.map_lod_overlay_marker_alpha
        line_alpha = theme.map_lod_overlay_line_alpha
        show_lines = wm.sz_ui_map_lod_overlay_show_lines
        chain = self._chain_uuids
        visible = self.visible_levels

        # Marker batches
        regular_by_vis: dict[str, list] = {}
        highlight_by_vis: dict[str, list] = {}

        for e in self.entities:
            visual = e[E_VISUAL]
            if visual not in visible:
                continue
            if e[E_UUID] in chain:
                highlight_by_vis.setdefault(visual, []).append(e[E_POS])
            else:
                regular_by_vis.setdefault(visual, []).append(e[E_POS])

        point_shader = gpu.shader.from_builtin(POINT_SHADER_NAME)

        # Highlighted markers go last so they draw on top of the regular ones
        batches = []
        for vis, coords in regular_by_vis.items():
            b = batch_for_shader(point_shader, "POINTS", {"pos": coords})
            color = self.lod_colors[vis]
            batches.append((b, (*color[:3], color[3] * marker_alpha), marker_size * LOD_SIZE_FACTORS[vis]))
        for vis, coords in highlight_by_vis.items():
            b = batch_for_shader(point_shader, "POINTS", {"pos": coords})
            bright = (*self.lod_colors_bright[vis], min(1.0, self.lod_colors[vis][3] * marker_alpha + 0.2))
            batches.append((b, bright, marker_size * LOD_SIZE_FACTORS[vis] * 2.0))
        self._marker_batches = batches

        # Line batches
        self._line_batch = None
        self._highlight_line_batch = None

        if show_lines:
            line_coords = []
            line_colors = []
            hl_line_coords = []
            hl_line_colors = []

            for e in self.entities:
                parent_uuid = e[E_PARENT]
                if not parent_uuid:
                    continue
                visual = e[E_VISUAL]
                if visual not in visible:
                    continue
                parent_idx = self.uuid_to_idx.get(parent_uuid)
                if parent_idx is None:
                    continue
                pe = self.entities[parent_idx]
                if pe[E_VISUAL] not in visible:
                    continue

                if e[E_UUID] in chain and parent_uuid in chain:
                    hl_line_coords.append(pe[E_POS])
                    hl_line_coords.append(e[E_POS])
                    hl_line_colors.append((*self.lod_colors_bright[pe[E_VISUAL]], 1.0))
                    hl_line_colors.append((*self.lod_colors_bright[visual], 1.0))
                else:
                    line_coords.append(pe[E_POS])
                    line_coords.append(e[E_POS])
                    line_colors.append((*self.lod_colors[pe[E_VISUAL]][:3], line_alpha))
                    line_colors.append((*self.lod_colors[visual][:3], line_alpha))

            shader = gpu.shader.from_builtin(POLYLINE_SMOOTH_COLOR_NAME)
            self._line_shader = shader

            if line_coords:
                self._line_batch = batch_for_shader(shader, "LINES", {"pos": line_coords, "color": line_colors})
            if hl_line_coords:
                self._highlight_line_batch = batch_for_shader(
                    shader, "LINES", {"pos": hl_line_coords, "color": hl_line_colors}
                )

    def _outline_entries(self, e, color, seen_uids: "set[int] | None" = None) -> list[tuple]:
        """(mesh_obj, batch, color) outline entries for one entity's object (and mesh children),
        using the shared per-mesh batch cache."""
        obj = e[E_LINKED]
        if obj is None:
            return []

        entries = []
        for mesh_obj in (o for o in (obj, *obj.children_recursive) if o.type == "MESH"):
            uid = mesh_obj.data.session_uid
            if uid not in self._outline_mesh_batches:
                self._outline_mesh_batches[uid] = _build_outline_mesh_batch(mesh_obj.data)
            if seen_uids is not None:
                seen_uids.add(uid)

            batch = self._outline_mesh_batches[uid]
            if batch is not None:
                entries.append((mesh_obj, batch, color))
        return entries

    def _rebuild_outline_draw_list(self, wm, theme):
        """Build the per-object outline draw list for chain entities.

        Per-mesh GPU batches are cached by mesh.session_uid so the expensive vertex extraction
        survives chain changes; batches for meshes no longer outlined are evicted.
        """
        draw_list = []
        seen_uids: set[int] = set()

        if wm.sz_ui_map_lod_overlay_show_outlines:
            alpha = theme.map_lod_overlay_outline_alpha
            chain = self._chain_uuids
            visible = self.visible_levels

            for e in self.entities:
                if e[E_UUID] not in chain or e[E_VISUAL] not in visible:
                    continue
                color = (*self.lod_colors_bright[e[E_VISUAL]], alpha)
                draw_list.extend(self._outline_entries(e, color, seen_uids))

        for uid in [uid for uid in self._outline_mesh_batches if uid not in seen_uids]:
            del self._outline_mesh_batches[uid]

        self._outline_draw_list = draw_list

    def set_drag_hover_outline(self, cache_idx: "int | None", color: tuple = ()):
        """Outline the entity currently hovered as a drag&drop link target (None to clear)."""
        if cache_idx is None:
            self._hover_outline_draw_list = []
        else:
            self._hover_outline_draw_list = self._outline_entries(self.entities[cache_idx], color)

    def invalidate_cache(self):
        """Force full rebuild on next draw. Called when entity data changes structurally."""
        self._cache_group_uuid = b""
        self._cache_entity_count = -1

    def patch_link(self, child_cache_idx: int, new_parent_uuid: bytes):
        """Incrementally update cache after a link/unlink operation.

        Only patches the affected entity tuple and parent-child index.
        Avoids the expensive full entity cache rebuild (which re-reads all
        Blender properties). Chain and GPU batches are rebuilt on the next draw.
        """
        old_e = self.entities[child_cache_idx]
        old_parent_uuid = old_e[E_PARENT]

        # Replace tuple with updated parent and visual
        self.entities[child_cache_idx] = (
            old_e[E_UUID],
            old_e[E_POS],
            old_e[E_LOD],
            old_e[E_NAME],
            new_parent_uuid,
            _visual_category(old_e[E_LOD], new_parent_uuid),
            old_e[E_COL_IDX],
            old_e[E_LINKED],
        )

        # Update _children_by_parent
        if old_parent_uuid:
            children = self._children_by_parent.get(old_parent_uuid)
            if children is not None:
                try:
                    children.remove(child_cache_idx)
                except ValueError:
                    pass

        if new_parent_uuid:
            self._children_by_parent.setdefault(new_parent_uuid, []).append(child_cache_idx)

        # Force chain + batch rebuild on next draw (entity cache stays valid)
        self._cache_selection_key = ()
        self._cache_vis_key = None

    def _ensure_cache(self):
        context = bpy.context
        group = active_group(context) if _is_tool_active(context) else None
        if group is None or len(group.entities) == 0:
            # Drop the mesh-batch cache while the overlay has nothing to draw
            if self._outline_mesh_batches or self._outline_draw_list:
                self._outline_mesh_batches.clear()
                self._outline_draw_list = []
                self._cache_outline_key = ()
            return None

        wm = context.window_manager
        entity_count = len(group.entities)
        group_uuid = group.uuid

        visible_levels = frozenset(lvl for lvl, prop in LOD_LEVEL_VIS_PROPS.items() if getattr(wm, prop))
        self.visible_levels = visible_levels

        theme = get_theme_settings()
        lod_colors = _theme_lod_colors(theme)
        if lod_colors != self.lod_colors:
            self.lod_colors = lod_colors
            self.lod_colors_bright = _brightened(lod_colors)
        colors_key = tuple(lod_colors.values())

        vis_key = (
            visible_levels,
            wm.sz_ui_map_lod_overlay_show_lines,
            theme.map_lod_overlay_marker_size,
            theme.map_lod_overlay_marker_alpha,
            theme.map_lod_overlay_line_alpha,
            colors_key,
        )

        active_entity = group.entities.active_item
        active_uuid = active_entity.uuid if active_entity else b""
        selection_key = (active_uuid, tuple(sorted(group.entities.selected_items_indices)))

        data_stale = group_uuid != self._cache_group_uuid or entity_count != self._cache_entity_count
        if data_stale:
            self._rebuild_entity_cache(group)
            self._cache_group_uuid = group_uuid
            self._cache_entity_count = entity_count

        chain_stale = data_stale or (selection_key != self._cache_selection_key)
        if chain_stale:
            self._rebuild_chain(group)
            self._cache_selection_key = selection_key

        batches_stale = chain_stale or vis_key != self._cache_vis_key
        if batches_stale:
            self._rebuild_geometry_batches(wm, theme)
            self._cache_vis_key = vis_key

        outline_key = (
            visible_levels,
            wm.sz_ui_map_lod_overlay_show_outlines,
            theme.map_lod_overlay_outline_alpha,
            colors_key,
        )
        if chain_stale or outline_key != self._cache_outline_key:
            self._rebuild_outline_draw_list(wm, theme)
            self._cache_outline_key = outline_key

        return group

    def _draw_outlines(self):
        # Hover outline last so its color wins where it overlaps a chain outline
        draw_list = self._outline_draw_list + self._hover_outline_draw_list
        if not draw_list:
            return

        region = bpy.context.region
        if region is None:
            return

        shader = get_outline_shader()
        shader.bind()
        shader.uniform_float("ViewportSize", (region.width, region.height))
        shader.uniform_float("Width", OUTLINE_WIDTH_PX)

        gpu.state.blend_set("ALPHA")
        gpu.state.face_culling_set("BACK")

        for mesh_obj, batch, color in draw_list:
            matrix_world = mesh_obj.matrix_world
            with gpu.matrix.push_pop():
                gpu.matrix.multiply_matrix(matrix_world)
                mvp = gpu.matrix.get_projection_matrix() @ gpu.matrix.get_model_view_matrix()
                shader.uniform_float("ModelViewProjectionMatrix", mvp)
                shader.uniform_float("Color", color)
                batch.draw(shader)

        gpu.state.face_culling_set("NONE")
        gpu.state.blend_set("NONE")

    def draw_geometry(self):
        group = self._ensure_cache()
        if group is None:
            return

        self._draw_outlines()

        gpu.state.blend_set("ALPHA")

        point_shader = gpu.shader.from_builtin(POINT_SHADER_NAME)
        for batch, color, size in self._marker_batches:
            gpu.state.point_size_set(size)
            point_shader.uniform_float("color", color)
            batch.draw(point_shader)

        if self._line_batch is not None:
            gpu.state.line_width_set(1)
            self._line_batch.draw(self._line_shader)

        if self._highlight_line_batch is not None:
            gpu.state.line_width_set(3)
            self._highlight_line_batch.draw(self._line_shader)

        gpu.state.blend_set("NONE")
        gpu.state.line_width_set(1)

    def draw_labels(self):
        """Draw name labels for the selected entity's chain."""
        context = bpy.context
        if not _is_tool_active(context):
            return

        if not self.entities:
            return

        region = context.region
        rv3d = context.region_data
        if rv3d is None:
            return

        chain = self._chain_uuids
        visible = self.visible_levels

        font_id = 0
        blf.size(font_id, 11 * context.preferences.system.ui_scale)
        blf.enable(font_id, blf.SHADOW)
        blf.shadow(font_id, 3, 0.0, 0.0, 0.0, 1.0)
        blf.shadow_offset(font_id, 2, -2)

        MAX_LABELS = 200  # a chain can span a whole subtree, so keep a safety cap
        labels_drawn = 0

        for e in self.entities:
            if labels_drawn >= MAX_LABELS:
                break

            if e[E_UUID] not in chain:
                continue

            visual = e[E_VISUAL]
            if visual not in visible:
                continue

            screen_pos = location_3d_to_region_2d(region, rv3d, e[E_POS])
            if screen_pos is None:
                continue

            blf.color(font_id, *self.lod_colors_bright[visual], 1.0)

            label = f"{e[E_NAME]}  [{e[E_LOD]}]"
            w, _h = blf.dimensions(font_id, label)
            blf.position(font_id, screen_pos.x - w * 0.5, screen_pos.y + 8, 0.0)
            blf.draw(font_id, label)
            labels_drawn += 1

        blf.disable(font_id, blf.SHADOW)


@bpy.app.handlers.persistent
def _on_depsgraph_update_post(scene, depsgraph):
    """Evict cached outline batches for meshes whose geometry changed (edits, undo, applied
    transforms), so the outline is rebuilt from the current geometry on the next draw.
    """
    handler = _active_handler
    if handler is None or not handler._outline_mesh_batches:
        return

    evicted = False
    for update in depsgraph.updates:
        if not update.is_updated_geometry:
            continue
        # Geometry updates may be reported on the Mesh itself or on an Object using it
        id_data = update.id
        data = getattr(id_data, "data", None)
        uid = data.session_uid if data is not None else id_data.session_uid
        if uid in handler._outline_mesh_batches:
            del handler._outline_mesh_batches[uid]
            evicted = True

    if evicted:
        handler._cache_outline_key = ()  # rebuild the outline draw list on next draw


def register():
    global _active_handler

    WM = bpy.types.WindowManager

    WM.sz_ui_map_lod_overlay_show_orphan_hd = bpy.props.BoolProperty(
        name="Orphan HD",
        description="Show orphan HD entities (not part of any LOD hierarchy)",
        default=False,
    )
    WM.sz_ui_map_lod_overlay_show_hd = bpy.props.BoolProperty(
        name="HD",
        description="Show HD entities that are part of a LOD hierarchy",
        default=True,
    )
    WM.sz_ui_map_lod_overlay_show_lod = bpy.props.BoolProperty(
        name="LOD",
        description="Show LOD entities in the overlay",
        default=True,
    )
    WM.sz_ui_map_lod_overlay_show_slod1 = bpy.props.BoolProperty(
        name="SLOD1",
        description="Show SLOD1 entities in the overlay",
        default=True,
    )
    WM.sz_ui_map_lod_overlay_show_slod2 = bpy.props.BoolProperty(
        name="SLOD2",
        description="Show SLOD2 entities in the overlay",
        default=False,
    )
    WM.sz_ui_map_lod_overlay_show_slod3 = bpy.props.BoolProperty(
        name="SLOD3",
        description="Show SLOD3 entities in the overlay",
        default=False,
    )
    WM.sz_ui_map_lod_overlay_show_slod4 = bpy.props.BoolProperty(
        name="SLOD4",
        description="Show SLOD4 entities in the overlay",
        default=False,
    )

    WM.sz_ui_map_lod_overlay_show_lines = bpy.props.BoolProperty(
        name="Show Lines",
        description="Draw connection lines between parent and child entities",
        default=True,
    )
    WM.sz_ui_map_lod_overlay_show_outlines = bpy.props.BoolProperty(
        name="Show Outlines",
        description="Draw X-ray silhouette outlines around the meshes of highlighted entities",
        default=True,
    )

    handler = LodHierarchyOverlayDrawHandler()
    handler.register()
    _active_handler = handler

    bpy.app.handlers.depsgraph_update_post.append(_on_depsgraph_update_post)


def unregister():
    global _active_handler

    bpy.app.handlers.depsgraph_update_post.remove(_on_depsgraph_update_post)

    if _active_handler is not None:
        _active_handler.unregister()
        _active_handler = None

    WM = bpy.types.WindowManager
    del WM.sz_ui_map_lod_overlay_show_orphan_hd
    del WM.sz_ui_map_lod_overlay_show_hd
    del WM.sz_ui_map_lod_overlay_show_lod
    del WM.sz_ui_map_lod_overlay_show_slod1
    del WM.sz_ui_map_lod_overlay_show_slod2
    del WM.sz_ui_map_lod_overlay_show_slod3
    del WM.sz_ui_map_lod_overlay_show_slod4
    del WM.sz_ui_map_lod_overlay_show_lines
    del WM.sz_ui_map_lod_overlay_show_outlines
