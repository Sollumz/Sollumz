import bpy
from bpy.types import (
    SpaceView3D,
    Object,
)
import gpu
from gpu_extras import batch
import blf
from mathutils import Vector
from collections.abc import Sequence
from ..sollumz_preferences import get_theme_settings
from .cloth import (
    ClothAttr,
    is_cloth_mesh_object,
    mesh_get_cloth_attribute_values,
)
from .cloth_diagnostics import (
    ClothDiagnosticsOverlayFlags,
    cloth_last_export_contexts,
)
import bmesh

if bpy.app.version >= (4, 5, 0):
    POINT_UNIFORM_COLOR_SHADER_NAME = "POINT_UNIFORM_COLOR"
else:
    POINT_UNIFORM_COLOR_SHADER_NAME = "UNIFORM_COLOR"


class ClothOverlaysDrawHandler:
    """Manages drawing the cloth overlays used to display the attributes at each vertex."""

    def __init__(self):
        self.handler_text = None
        self.handler_geometry = None

    def register(self):
        self.handler_text = SpaceView3D.draw_handler_add(self.draw_text, (), "WINDOW", "POST_PIXEL")
        self.handler_geometry = SpaceView3D.draw_handler_add(self.draw_geometry, (), "WINDOW", "POST_VIEW")

    def unregister(self):
        SpaceView3D.draw_handler_remove(self.handler_text, "WINDOW")
        SpaceView3D.draw_handler_remove(self.handler_geometry, "WINDOW")

    def can_draw_anything(self) -> bool:
        context = bpy.context
        wm = context.window_manager
        if (
            not wm.sz_ui_cloth_vertex_weight_visualize and
            not wm.sz_ui_cloth_inflation_scale_visualize and
            not wm.sz_ui_cloth_pinned_visualize and
            not wm.sz_ui_cloth_pin_radius_visualize and
            not wm.sz_ui_cloth_force_transform_visualize and
            not wm.sz_ui_cloth_edge_compression_visualize and
            not wm.sz_ui_cloth_binding_distance_visualize
        ):
            return False

        obj = context.active_object
        if not is_cloth_mesh_object(obj):
            return False

        return True

    def draw_text(self):
        if not self.can_draw_anything():
            return

        context = bpy.context
        wm = context.window_manager
        obj = context.active_object

        attrs = []
        if wm.sz_ui_cloth_vertex_weight_visualize:
            attrs.append(ClothAttr.VERTEX_WEIGHT)
        if wm.sz_ui_cloth_inflation_scale_visualize:
            attrs.append(ClothAttr.INFLATION_SCALE)
        if wm.sz_ui_cloth_pin_radius_visualize:
            attrs.append(ClothAttr.PIN_RADIUS)
        if wm.sz_ui_cloth_force_transform_visualize:
            attrs.append(ClothAttr.FORCE_TRANSFORM)

        if attrs:
            self.draw_attribute_values(obj, attrs)

        # Draw edge compression values
        if wm.sz_ui_cloth_edge_compression_visualize:
            self.draw_edge_compression_values(obj)

    def draw_geometry(self):
        context = bpy.context
        wm = context.window_manager

        if (
            wm.sz_ui_cloth_diag_material_errors_visualize or
            wm.sz_ui_cloth_diag_binding_errors_visualize
            # wm.sz_ui_cloth_diag_bindings_visualize
        ):
            self.draw_diagnostics_overlays()

        if not self.can_draw_anything():
            return

        obj = context.active_object

        if wm.sz_ui_cloth_pinned_visualize:
            self.draw_pinned_geometry(obj)

        if wm.sz_ui_cloth_binding_distance_visualize:
            self.draw_binding_distance_circles(obj)

    def draw_attribute_values(self, cloth_obj: Object, attrs: Sequence[ClothAttr]):
        context = bpy.context
        wm = context.window_manager
        region = context.region
        rv3d = context.region_data
        mesh = cloth_obj.data

        font_id = 0
        blf.size(font_id, 11)
        blf.color(font_id, 1.0, 1.0, 1.0, 1.0)
        blf.enable(font_id, blf.SHADOW)
        blf.shadow(font_id, 3, 0.0, 0.0, 0.0, 1.0)
        blf.shadow_offset(font_id, 2, -2)

        matrix_world = cloth_obj.matrix_world

        pin_radius_set_index = wm.sz_ui_cloth_pin_radius_set - 1

        def _draw_vertex_attributes(pos: Vector, attr_values):
            from bpy_extras.view3d_utils import location_3d_to_region_2d
            pos = matrix_world @ pos
            pos = location_3d_to_region_2d(region, rv3d, pos)
            if pos:
                for i, attr_value in enumerate(attr_values):
                    attr_type = attrs[i].type
                    if attrs[i] == ClothAttr.PIN_RADIUS:
                        attr_str = f"{attr_value[pin_radius_set_index]:.2g}"
                    elif attr_type == "FLOAT_VECTOR":
                        attr_str = f"{attr_value[0]:.2g}  {attr_value[1]:.2g}"
                    elif attr_type == "FLOAT_COLOR":
                        attr_str = f"{attr_value[0]:.2g}  {attr_value[1]:.2g}  {attr_value[2]:.2g}  {attr_value[3]:.2g}"
                    elif attr_type == "INT":
                        attr_str = f"{attr_value}"
                    else:  # FLOAT
                        attr_str = f"{attr_value:.6g}"
                    w, h = blf.dimensions(font_id, attr_str)
                    attr_pos = pos - Vector((w * 0.5, h * i * 2 - (h * len(attr_values) / 2)))
                    blf.position(font_id, attr_pos.x, attr_pos.y, 0.0)
                    blf.draw(font_id, attr_str)

        if cloth_obj.mode == "EDIT":
            edit_mesh = bmesh.from_edit_mesh(mesh)
            try:
                attr_layers = [(
                    edit_mesh.verts.layers.float_vector if attr.type == "FLOAT_VECTOR"
                    else edit_mesh.verts.layers.int if attr.type == "INT"
                    else edit_mesh.verts.layers.float_color if attr.type == "FLOAT_COLOR"
                    else edit_mesh.verts.layers.float
                ).get(attr, None) for attr in attrs]
                for v in edit_mesh.verts:
                    attr_values = [attr.default_value if attr_layers[i] is None else v[attr_layers[i]]
                                   for i, attr in enumerate(attrs)]
                    _draw_vertex_attributes(v.co, attr_values)
            finally:
                edit_mesh.free()
        else:
            all_attr_values = [mesh_get_cloth_attribute_values(mesh, attr) for attr in attrs]
            for v in mesh.vertices:
                attr_values = [all_attr_values[i][v.index] for i, attr in enumerate(attrs)]
                _draw_vertex_attributes(v.co, attr_values)

        blf.disable(font_id, blf.SHADOW)

    def draw_edge_compression_values(self, cloth_obj: Object):
        context = bpy.context
        region = context.region
        rv3d = context.region_data
        mesh = cloth_obj.data

        font_id = 0
        blf.size(font_id, 11)
        blf.color(font_id, 1.0, 1.0, 1.0, 1.0)  # White color for edge values
        blf.enable(font_id, blf.SHADOW)
        blf.shadow(font_id, 3, 0.0, 0.0, 0.0, 1.0)
        blf.shadow_offset(font_id, 2, -2)

        matrix_world = cloth_obj.matrix_world

        def _draw_edge_attribute(edge_center: Vector, compression_value: float):
            from bpy_extras.view3d_utils import location_3d_to_region_2d
            pos = matrix_world @ edge_center
            pos = location_3d_to_region_2d(region, rv3d, pos)
            if pos:
                attr_str = f"{compression_value:.2g}"
                w, h = blf.dimensions(font_id, attr_str)
                attr_pos = pos - Vector((w * 0.5, h * 0.5))
                blf.position(font_id, attr_pos.x, attr_pos.y, 0.0)
                blf.draw(font_id, attr_str)

        if cloth_obj.mode == "EDIT":
            edit_mesh = bmesh.from_edit_mesh(mesh)
            try:
                compression_layer = edit_mesh.edges.layers.float.get(ClothAttr.EDGE_COMPRESSION, None)
                for edge in edit_mesh.edges:
                    compression_value = ClothAttr.EDGE_COMPRESSION.default_value if compression_layer is None else edge[compression_layer]
                    edge_center = (edge.verts[0].co + edge.verts[1].co) * 0.5
                    _draw_edge_attribute(edge_center, compression_value)
            finally:
                edit_mesh.free()
        else:
            compression_values = mesh_get_cloth_attribute_values(mesh, ClothAttr.EDGE_COMPRESSION) if mesh.attributes.get(ClothAttr.EDGE_COMPRESSION) else None
            for edge in mesh.edges:
                compression_value = ClothAttr.EDGE_COMPRESSION.default_value if compression_values is None else compression_values[edge.index]
                edge_center = (Vector(mesh.vertices[edge.vertices[0]].co) + Vector(mesh.vertices[edge.vertices[1]].co)) * 0.5
                _draw_edge_attribute(edge_center, compression_value)

        blf.disable(font_id, blf.SHADOW)

    def draw_pinned_geometry(self, cloth_obj: Object):
        transform = cloth_obj.matrix_world
        mesh = cloth_obj.data

        coords = []

        if cloth_obj.mode == "EDIT":
            edit_mesh = bmesh.from_edit_mesh(mesh)
            try:
                pinned_layer = edit_mesh.verts.layers.int.get(ClothAttr.PINNED, None)
                for v in edit_mesh.verts:
                    is_pinned = ClothAttr.PINNED.default_value if pinned_layer is None else v[pinned_layer]
                    if is_pinned:
                        coords.append(transform @ v.co)
            finally:
                edit_mesh.free()
        else:
            pinned_values = mesh_get_cloth_attribute_values(mesh, ClothAttr.PINNED)
            for v in mesh.vertices:
                is_pinned = pinned_values[v.index] != 0
                if is_pinned:
                    coords.append(transform @ v.co)

        theme = get_theme_settings()
        gpu.state.point_size_set(theme.cloth_overlay_pinned_size)
        gpu.state.blend_set("ALPHA")
        shader = gpu.shader.from_builtin(POINT_UNIFORM_COLOR_SHADER_NAME)
        pinned_verts_batch = batch.batch_for_shader(shader, "POINTS", {"pos": coords})
        shader.uniform_float("color", theme.cloth_overlay_pinned)
        pinned_verts_batch.draw(shader)

    def draw_binding_distance_circles(self, cloth_obj: Object):
        """Draw transparent red prisms around each cloth triangle showing the binding distance perpendicular to smooth vertex normals."""
        wm = bpy.context.window_manager
        transform = cloth_obj.matrix_world
        mesh = cloth_obj.data
        binding_distance = wm.sz_ui_cloth_binding_distance
        
        all_coords = []
        
        def add_smooth_prism_for_triangle(v0_world, v1_world, v2_world, n0_world, n1_world, n2_world):
            """Add triangles for a prism extruded using smooth vertex normals."""
            # Extrude each vertex along its smooth normal
            v0_top = v0_world + n0_world * binding_distance
            v1_top = v1_world + n1_world * binding_distance
            v2_top = v2_world + n2_world * binding_distance
            
            v0_bot = v0_world - n0_world * binding_distance
            v1_bot = v1_world - n1_world * binding_distance
            v2_bot = v2_world - n2_world * binding_distance
            
            # Top cap
            all_coords.append(v0_top)
            all_coords.append(v1_top)
            all_coords.append(v2_top)
            
            # Bottom cap
            all_coords.append(v0_bot)
            all_coords.append(v2_bot)
            all_coords.append(v1_bot)
            
            # Side faces (3 quads = 6 triangles)
            # Side 1 (v0-v1 edge)
            all_coords.append(v0_bot)
            all_coords.append(v1_bot)
            all_coords.append(v1_top)
            
            all_coords.append(v0_bot)
            all_coords.append(v1_top)
            all_coords.append(v0_top)
            
            # Side 2 (v1-v2 edge)
            all_coords.append(v1_bot)
            all_coords.append(v2_bot)
            all_coords.append(v2_top)
            
            all_coords.append(v1_bot)
            all_coords.append(v2_top)
            all_coords.append(v1_top)
            
            # Side 3 (v2-v0 edge)
            all_coords.append(v2_bot)
            all_coords.append(v0_bot)
            all_coords.append(v0_top)
            
            all_coords.append(v2_bot)
            all_coords.append(v0_top)
            all_coords.append(v2_top)
        
        # Get cloth triangles and create prisms using smooth vertex normals
        if cloth_obj.mode == "EDIT":
            edit_mesh = bmesh.from_edit_mesh(mesh)
            try:
                for face in edit_mesh.faces:
                    if len(face.verts) == 3:  # Only process triangles
                        v0 = transform @ face.verts[0].co
                        v1 = transform @ face.verts[1].co
                        v2 = transform @ face.verts[2].co
                        # Use smooth vertex normals instead of flat face normal
                        n0 = (transform.to_3x3() @ face.verts[0].normal).normalized()
                        n1 = (transform.to_3x3() @ face.verts[1].normal).normalized()
                        n2 = (transform.to_3x3() @ face.verts[2].normal).normalized()
                        add_smooth_prism_for_triangle(v0, v1, v2, n0, n1, n2)
            finally:
                edit_mesh.free()
        else:
            for poly in mesh.polygons:
                if len(poly.vertices) == 3:  # Only process triangles
                    v0_idx, v1_idx, v2_idx = poly.vertices
                    v0 = transform @ mesh.vertices[v0_idx].co
                    v1 = transform @ mesh.vertices[v1_idx].co
                    v2 = transform @ mesh.vertices[v2_idx].co
                    # Use smooth vertex normals instead of flat face normal
                    n0 = (transform.to_3x3() @ mesh.vertices[v0_idx].normal).normalized()
                    n1 = (transform.to_3x3() @ mesh.vertices[v1_idx].normal).normalized()
                    n2 = (transform.to_3x3() @ mesh.vertices[v2_idx].normal).normalized()
                    add_smooth_prism_for_triangle(v0, v1, v2, n0, n1, n2)
        
        if all_coords:
            gpu.state.blend_set("ALPHA")
            gpu.state.depth_test_set("LESS_EQUAL")
            gpu.state.depth_mask_set(False)
            shader = gpu.shader.from_builtin("UNIFORM_COLOR")
            spheres_batch = batch.batch_for_shader(shader, "TRIS", {"pos": all_coords})
            shader.uniform_float("color", (1.0, 0.0, 0.0, 0.15))  # Red with high transparency
            spheres_batch.draw(shader)
            gpu.state.depth_mask_set(True)

    def draw_diagnostics_overlays(self):
        last = cloth_last_export_contexts()
        if not last:
            return

        wm = bpy.context.window_manager

        flags = ClothDiagnosticsOverlayFlags(0)
        if wm.sz_ui_cloth_diag_material_errors_visualize:
            flags |= ClothDiagnosticsOverlayFlags.MATERIAL_ERRORS
        if wm.sz_ui_cloth_diag_binding_errors_visualize:
            flags |= ClothDiagnosticsOverlayFlags.BINDING_ERRORS
        # if wm.sz_ui_cloth_diag_bindings_visualize:
        #     flags |= ClothDiagnosticsOverlayFlags.BINDINGS

        for context in last.values():
            for diagnostics in context.all_diagnostics.values():
                diagnostics.draw_overlay(flags)


draw_handlers = []


def register():
    handler = ClothOverlaysDrawHandler()
    handler.register()
    draw_handlers.append(handler)


def unregister():
    for handler in draw_handlers:
        handler.unregister()
    draw_handlers.clear()
