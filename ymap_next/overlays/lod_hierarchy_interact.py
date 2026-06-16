import blf
import bpy
import gpu
from bpy.types import Operator, SpaceView3D
from bpy_extras.view3d_utils import location_3d_to_region_2d
from gpu_extras.batch import batch_for_shader

from ...shared.multiselection import SelectMode
from ..context import active_entity, active_group
from ..properties.map import MapLodLevel
from . import lod_hierarchy
from .lod_hierarchy import E_COL_IDX, E_LOD, E_NAME, E_POS, E_VISUAL

CLICK_THRESHOLD_PX = 20
DRAG_THRESHOLD_PX = 5
CYCLE_POS_THRESHOLD_PX = 5
COLOCATED_EPSILON_SQ = 1.0  # Screen-space distance^2 to consider entities co-located

COLOR_VALID = (0.3, 1.0, 0.3, 0.8)
COLOR_INVALID = (1.0, 0.3, 0.3, 0.8)
COLOR_NO_TARGET = (1.0, 1.0, 1.0, 0.4)


def _is_valid_parent(child_lod: str, parent_lod: str) -> bool:
    """Parent must be exactly one LOD level coarser than the child."""
    return MapLodLevel[child_lod].parent_level is MapLodLevel[parent_lod]


def _find_entities_near_cursor(handler, context, mx, my) -> list[int]:
    """Return all entity indices co-located at the nearest screen position within click threshold."""
    region = context.region
    rv3d = context.region_data
    if rv3d is None:
        return []

    visible = handler.visible_levels
    threshold_sq = CLICK_THRESHOLD_PX**2
    best_dist_sq = threshold_sq
    hits: list[int] = []

    for i, e in enumerate(handler.entities):
        if e[E_VISUAL] not in visible:
            continue

        screen = location_3d_to_region_2d(region, rv3d, e[E_POS])
        if screen is None:
            continue

        dx = screen.x - mx
        dy = screen.y - my
        dist_sq = dx * dx + dy * dy
        if dist_sq > threshold_sq:
            continue

        if not hits or dist_sq < best_dist_sq - COLOCATED_EPSILON_SQ:
            # New closest, discard previous hits
            best_dist_sq = dist_sq
            hits = [i]
        elif dist_sq <= best_dist_sq + COLOCATED_EPSILON_SQ:
            # Within epsilon of the best, co-located
            hits.append(i)

    return hits


class SOLLUMZ_OT_map_lod_overlay_interact(Operator):
    """Click to select entities, drag to link child to parent."""

    bl_idname = "sollumz.map_lod_overlay_interact"
    bl_label = "LOD Overlay Interact"
    bl_description = "Click to select entities, drag to link child to parent"
    bl_options = {"UNDO"}

    toggle: bpy.props.BoolProperty(
        name="Toggle",
        description="Toggle selection instead of replacing it",
        default=False,
    )

    @classmethod
    def poll(cls, context):
        return active_group(context) is not None and lod_hierarchy._active_handler is not None

    def invoke(self, context, event):
        self._handler = lod_hierarchy._active_handler

        mx, my = event.mouse_region_x, event.mouse_region_y
        self._press_mx = mx
        self._press_my = my

        # Find entity at press position and handle click cycling
        hits = _find_entities_near_cursor(self._handler, context, mx, my)
        if hits:
            # Check if clicking at the same position (cycle through overlapping entities)
            dx = mx - self._handler.cycle_pos[0]
            dy = my - self._handler.cycle_pos[1]
            same_pos = (dx * dx + dy * dy) < CYCLE_POS_THRESHOLD_PX**2

            if same_pos and hits == self._handler.cycle_hits and len(hits) > 1:
                self._handler.cycle_index = (self._handler.cycle_index + 1) % len(hits)
            else:
                self._handler.cycle_hits = hits
                self._handler.cycle_pos = (mx, my)
                self._handler.cycle_index = 0

            self._press_entity_idx = hits[self._handler.cycle_index]
        else:
            self._press_entity_idx = None
            self._handler.cycle_hits = []
            self._handler.cycle_index = 0

        # Drag state
        self._dragging = False
        self._drag_source_indices: list[int] = []
        self._drag_source_indices_set: set[int] = set()
        self._drag_source_lods: set[str] = set()
        self._drag_mx = mx
        self._drag_my = my
        self._drag_target_idx = None
        self._drag_target_hits: list[int] = []
        self._drag_target_cycle: int = 0
        self._drag_valid = False

        self._drag_draw_handle = SpaceView3D.draw_handler_add(self._draw_drag_feedback, (), "WINDOW", "POST_PIXEL")

        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def modal(self, context, event):
        mx, my = event.mouse_region_x, event.mouse_region_y

        # Scroll wheel: cycle drag target
        if self._dragging and event.type in {"WHEELUPMOUSE", "WHEELDOWNMOUSE"}:
            if len(self._drag_target_hits) > 1:
                delta = 1 if event.type == "WHEELUPMOUSE" else -1
                self._drag_target_cycle = (self._drag_target_cycle + delta) % len(self._drag_target_hits)
                self._set_drag_target(self._drag_target_hits[self._drag_target_cycle])
                context.area.tag_redraw()
            return {"RUNNING_MODAL"}

        if event.type == "MOUSEMOVE":
            if self._press_entity_idx is not None and not self._dragging:
                dx = mx - self._press_mx
                dy = my - self._press_my
                if dx * dx + dy * dy >= DRAG_THRESHOLD_PX**2:
                    self._dragging = True
                    self._drag_source_indices = self._compute_drag_sources(context)
                    self._drag_source_indices_set = set(self._drag_source_indices)
                    entities = self._handler.entities
                    self._drag_source_lods = {entities[si][E_LOD] for si in self._drag_source_indices}

            if self._dragging:
                self._drag_mx = mx
                self._drag_my = my
                self._update_drag_target(context, mx, my)
                context.area.tag_redraw()
            return {"RUNNING_MODAL"}

        if event.type == "LEFTMOUSE" and event.value == "RELEASE":
            changed = False
            if self._dragging:
                if self._drag_target_idx is not None and self._drag_valid:
                    self._link_entities_multi(context, self._drag_source_indices, self._drag_target_idx)
                    changed = True
            elif self._press_entity_idx is not None:
                mode = SelectMode.TOGGLE if self.toggle else SelectMode.SET
                self._select_entity(context, self._press_entity_idx, mode)
                changed = True

            self._cleanup(context)
            # CANCELLED on empty clicks so the UNDO flag doesn't push an empty undo step
            return {"FINISHED"} if changed else {"CANCELLED"}

        if event.type in {"RIGHTMOUSE", "ESC"}:
            self._cleanup(context)
            return {"CANCELLED"}

        return {"RUNNING_MODAL"}

    def _cleanup(self, context):
        if self._drag_draw_handle is not None:
            SpaceView3D.draw_handler_remove(self._drag_draw_handle, "WINDOW")
            self._drag_draw_handle = None
        context.area.tag_redraw()

    def _compute_drag_sources(self, context) -> list[int]:
        """Determine which entity cache indices to drag.

        If the pressed entity is part of the current multi-selection, drag all
        selected entities. Otherwise, drag only the pressed entity.
        """
        handler = self._handler
        press_idx = self._press_entity_idx
        if press_idx is None:
            return []

        group = active_group(context)
        if group is None:
            return [press_idx]

        press_col_idx = handler.entities[press_idx][E_COL_IDX]
        selected_col_indices = set(group.entities.selected_items_indices)

        if press_col_idx not in selected_col_indices:
            return [press_idx]

        # Map selected collection indices back to cache indices
        sources = [cache_idx for cache_idx, e in enumerate(handler.entities) if e[E_COL_IDX] in selected_col_indices]
        return sources or [press_idx]

    def _update_drag_target(self, context, mx, my):
        hits = _find_entities_near_cursor(self._handler, context, mx, my)
        # Filter out source entities
        filtered = [h for h in hits if h not in self._drag_source_indices_set]

        if filtered != self._drag_target_hits:
            self._drag_target_hits = filtered
            self._drag_target_cycle = 0

        self._set_drag_target(filtered[self._drag_target_cycle % len(filtered)] if filtered else None)

    def _set_drag_target(self, idx: int | None):
        if idx == self._drag_target_idx:
            return
        self._drag_target_idx = idx
        if idx is None:
            self._drag_valid = False
        else:
            parent_lod = self._handler.entities[idx][E_LOD]
            self._drag_valid = all(_is_valid_parent(lod, parent_lod) for lod in self._drag_source_lods)

    def _draw_drag_feedback(self):
        if not self._dragging or not self._drag_source_indices:
            return

        handler = self._handler
        context = bpy.context
        region = context.region
        rv3d = context.region_data
        if rv3d is None:
            return

        mx, my = self._drag_mx, self._drag_my

        # Determine line color
        if self._drag_target_idx is not None:
            color = COLOR_VALID if self._drag_valid else COLOR_INVALID
        else:
            color = COLOR_NO_TARGET

        # Collect line segments: each source -> cursor
        line_coords = []
        for si in self._drag_source_indices:
            screen = location_3d_to_region_2d(region, rv3d, handler.entities[si][E_POS])
            if screen is None:
                continue
            line_coords.append((screen.x, screen.y))
            line_coords.append((mx, my))

        if not line_coords:
            return

        # Draw lines
        gpu.state.blend_set("ALPHA")
        shader = gpu.shader.from_builtin("UNIFORM_COLOR")
        gpu.state.line_width_set(2)
        batch = batch_for_shader(shader, "LINES", {"pos": line_coords})
        shader.uniform_float("color", color)
        batch.draw(shader)
        gpu.state.line_width_set(1)
        gpu.state.blend_set("NONE")

        # Draw label near cursor
        font_id = 0
        blf.size(font_id, 12)
        blf.enable(font_id, blf.SHADOW)
        blf.shadow(font_id, 3, 0.0, 0.0, 0.0, 1.0)
        blf.shadow_offset(font_id, 2, -2)

        count = len(self._drag_source_indices)
        if count == 1:
            child_e = handler.entities[self._drag_source_indices[0]]
            child_label = f"{child_e[E_NAME]} [{child_e[E_LOD]}]"
        else:
            child_label = f"{count} entities"

        if self._drag_target_idx is not None:
            target_e = handler.entities[self._drag_target_idx]
            target_label = f"{target_e[E_NAME]} [{target_e[E_LOD]}]"
            n_targets = len(self._drag_target_hits)
            if n_targets > 1:
                target_label += f" ({self._drag_target_cycle + 1}/{n_targets} scroll to cycle)"
            if self._drag_valid:
                label = f"{child_label} \u2192 {target_label}"
                blf.color(font_id, *COLOR_VALID)
            else:
                label = f"{child_label} \u2192 {target_label} (invalid)"
                blf.color(font_id, *COLOR_INVALID)
        else:
            label = f"{child_label} \u2192 ?"
            blf.color(font_id, *COLOR_NO_TARGET)

        blf.position(font_id, mx + 15, my + 15, 0.0)
        blf.draw(font_id, label)
        blf.disable(font_id, blf.SHADOW)

    def _select_entity(self, context, entity_idx, mode):
        group = active_group(context)
        if group is None:
            return

        col_idx = self._handler.entities[entity_idx][E_COL_IDX]
        group.entities.select(col_idx, mode=mode)

    def _link_entities_multi(self, context, child_indices: list[int], parent_idx: int):
        group = active_group(context)
        if group is None:
            return

        if group.incomplete_lod_hierarchy_lock:
            # Hierarchy is frozen: linking is disabled (selection via click still works).
            return

        handler = self._handler
        parent_uuid = group.entities[handler.entities[parent_idx][E_COL_IDX]].uuid

        linked_col_indices = []
        for child_idx in child_indices:
            col_idx = handler.entities[child_idx][E_COL_IDX]
            group.set_entity_parent(group.entities[col_idx], parent_uuid)
            handler.patch_link(child_idx, parent_uuid)
            linked_col_indices.append(col_idx)

        if linked_col_indices:
            group.entities.select_many(linked_col_indices)


class SOLLUMZ_OT_map_lod_overlay_unlink(Operator):
    bl_idname = "sollumz.map_lod_overlay_unlink"
    bl_label = "Unlink Entity"
    bl_description = "Unlink the selected entity from its parent"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        entity = active_entity(context)
        if entity is None or not entity.parent_uuid:
            return False
        group = active_group(context)
        if group is not None and group.incomplete_lod_hierarchy_lock:
            cls.poll_message_set("LOD hierarchy is incomplete. Cannot unlink entities!")
            return False
        return True

    def execute(self, context):
        group = active_group(context)
        entity = group.entities.active_item
        group.set_entity_parent(entity, b"")

        handler = lod_hierarchy._active_handler
        if handler is not None:
            cache_idx = handler.uuid_to_idx.get(entity.uuid)
            if cache_idx is not None:
                handler.patch_link(cache_idx, b"")
            else:
                handler.invalidate_cache()

        return {"FINISHED"}
