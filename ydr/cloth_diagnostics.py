import bpy
from bpy.types import (
    Object,
    UILayout,
    Context,
)
from typing import NamedTuple, Iterator
from mathutils import Vector
from contextlib import contextmanager
from enum import Flag, auto
import gpu
from gpu_extras import batch
from ..sollumz_preferences import get_theme_settings


class ClothCharDiagMeshBinding(NamedTuple):
    co: Vector
    v0: Vector
    v1: Vector
    v2: Vector
    n: Vector


class ClothCharDiagMeshBindingError(NamedTuple):
    co: Vector
    error_projection: bool
    error_distance: bool


class ClothCharDiagMeshMaterialError(NamedTuple):
    v0: Vector
    v1: Vector
    v2: Vector


class ClothCharDiagnosticsOverlayFlags(Flag):
    MATERIAL_ERRORS = auto()
    BINDING_ERRORS = auto()
    BINDINGS = auto()


class ClothCharDiagnostics:
    def __init__(self, dwd_obj_name: str, drawable_obj_name: str):
        self.dwd_obj_name = dwd_obj_name
        self.drawable_obj_name = drawable_obj_name
        self.drawable_model_obj_name = ""
        self.cloth_obj_name = ""
        self.mesh_material_errors: list[ClothCharDiagMeshMaterialError] | None = None
        self.mesh_bindings: list[ClothCharDiagMeshBinding] | None = None
        self.mesh_binding_errors: list[ClothCharDiagMeshBindingError] | None = None
        self._mesh_material_errors_batch: gpu.types.GPUBatch | None = None
        self._mesh_binding_errors_batch: gpu.types.GPUBatch | None = None
        self._mesh_bindings_drawable_batch: gpu.types.GPUBatch | None = None
        self._mesh_bindings_cloth_batch: gpu.types.GPUBatch | None = None
        self._mesh_bindings_cloth_lines_batch: gpu.types.GPUBatch | None = None

    def draw_ui(self, layout: UILayout, context: Context):
        if not self.cloth_obj_name or not self.drawable_model_obj_name:
            return

        wm = context.window_manager

        from .ui import _visible_icon_prop

        layout.label(text=f"{self.dwd_obj_name}  {self.drawable_obj_name}")

        if not self.mesh_material_errors and not self.mesh_binding_errors:
            layout.label(text="No material or binding errors.", icon="BLANK1")

        if self.mesh_material_errors:
            row = layout.row(align=True)
            row.label(text=f"{len(self.mesh_material_errors)} material error(s)", icon="ERROR")
            _visible_icon_prop(row, wm, "sz_ui_cloth_diag_material_errors_visualize")

        if self.mesh_binding_errors:
            row = layout.row(align=True)
            row.label(text=f"{len(self.mesh_binding_errors)} binding error(s)", icon="ERROR")
            _visible_icon_prop(row, wm, "sz_ui_cloth_diag_binding_errors_visualize")

        # TODO: better bindings visualization, disabled for now
        #row = layout.row(align=True)
        #row.label(text="        Bindings")
        #_visible_icon_prop(row, wm, "sz_ui_cloth_diag_bindings_visualize")

    def draw_overlay(self, flags: ClothCharDiagnosticsOverlayFlags):
        if not self.cloth_obj_name or not self.drawable_model_obj_name:
            return

        drawable_mesh_obj = bpy.data.objects.get(self.drawable_model_obj_name, None)
        cloth_obj = bpy.data.objects.get(self.cloth_obj_name, None)
        if not cloth_obj or not drawable_mesh_obj:
            return

        mesh_material_errors = self.mesh_material_errors
        mesh_binding_errors = self.mesh_binding_errors
        mesh_bindings = self.mesh_bindings

        cloth_transform = cloth_obj.matrix_world
        drawable_transform = drawable_mesh_obj.matrix_world

        theme = get_theme_settings()

        if ClothCharDiagnosticsOverlayFlags.MATERIAL_ERRORS in flags and mesh_material_errors:
            shader = gpu.shader.from_builtin("UNIFORM_COLOR")
            if self._mesh_material_errors_batch is None:
                self._mesh_material_errors_batch = batch.batch_for_shader(
                    shader, "TRIS", {"pos": [v for e in mesh_material_errors for v in (e.v0, e.v1, e.v2)]})

            gpu.state.blend_set("ALPHA")
            with gpu.matrix.push_pop():
                gpu.matrix.multiply_matrix(drawable_transform)
                shader.uniform_float("color", theme.cloth_overlay_material_errors)
                self._mesh_material_errors_batch.draw(shader)

        if ClothCharDiagnosticsOverlayFlags.BINDING_ERRORS in flags and mesh_binding_errors:
            shader = gpu.shader.from_builtin("UNIFORM_COLOR")
            if self._mesh_binding_errors_batch is None:
                self._mesh_binding_errors_batch = batch.batch_for_shader(
                    shader, "POINTS", {"pos": [e.co for e in mesh_binding_errors]})

            gpu.state.point_size_set(theme.cloth_overlay_binding_errors_size)
            gpu.state.blend_set("ALPHA")
            with gpu.matrix.push_pop():
                gpu.matrix.multiply_matrix(drawable_transform)
                shader.uniform_float("color", theme.cloth_overlay_binding_errors)
                self._mesh_binding_errors_batch.draw(shader)

        if ClothCharDiagnosticsOverlayFlags.BINDINGS in flags and mesh_bindings:
            shader = gpu.shader.from_builtin("UNIFORM_COLOR")
            if self._mesh_bindings_drawable_batch is None:
                drawable_coords = []
                cloth_coords = []
                cloth_line_coords = []

                for b in mesh_bindings:
                    drawable_coords.append(b.co)
                    c = Vector()
                    v0 = b.v0
                    v1 = b.v1
                    v2 = b.v2
                    for p in (v0, v1, v2):
                        cloth_coords.append(p)
                        c += p

                    c /= 3

                    n = b.n
                    cloth_line_coords.append(c)
                    cloth_line_coords.append(c + n * 0.1)

                self._mesh_bindings_drawable_batch = batch.batch_for_shader(shader, "POINTS", {"pos": drawable_coords})
                self._mesh_bindings_cloth_batch = batch.batch_for_shader(shader, "TRIS", {"pos": cloth_coords})
                self._mesh_bindings_cloth_lines_batch = batch.batch_for_shader(
                    shader, "LINES", {"pos": cloth_line_coords})

            gpu.state.point_size_set(12.5)
            gpu.state.blend_set("ALPHA")
            with gpu.matrix.push_pop():
                gpu.matrix.multiply_matrix(drawable_transform)
                shader.uniform_float("color", (0.05, 0.75, 0.05, 0.5))
                self._mesh_bindings_drawable_batch.draw(shader)

            with gpu.matrix.push_pop():
                gpu.matrix.multiply_matrix(cloth_transform)
                shader.uniform_float("color", (0.85, 0.05, 0.05, 0.5))
                self._mesh_bindings_cloth_batch.draw(shader)

                shader.uniform_float("color", (0.85, 0.05, 0.85, 1.0))
                self._mesh_bindings_cloth_lines_batch.draw(shader)


class _ClothCharDiagnosticsDict(dict[str, ClothCharDiagnostics]):
    def __missing__(self, key):
        self[key] = d = ClothCharDiagnostics(self._dwd_obj_name, key)
        return d

    def __init__(self, dwd_obj_name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._dwd_obj_name = dwd_obj_name


class ClothCharExportContext:

    def __init__(self, dwd_obj: Object):
        self.dwd_obj_name = dwd_obj.name
        self._diagnostics: dict[str, ClothCharDiagnostics] = _ClothCharDiagnosticsDict(self.dwd_obj_name)
        self._current_diagnostics: ClothCharDiagnostics | None = None

    @contextmanager
    def enter_drawable_context(self, drawable_obj: Object) -> Iterator[ClothCharDiagnostics]:
        if self._current_diagnostics is not None:
            raise Exception("Not in character cloth drawable context!")
        self._current_diagnostics = self._diagnostics[drawable_obj.name]
        try:
            yield self._current_diagnostics
        finally:
            self._current_diagnostics = None

    @property
    def diagnostics(self) -> ClothCharDiagnostics:
        if self._current_diagnostics is None:
            raise Exception("Not in character cloth drawable context!")
        return self._current_diagnostics

    @property
    def all_diagnostics(self) -> dict[str, ClothCharDiagnostics]:
        return self._diagnostics


_current_export_context: ClothCharExportContext | None = None
_last_export_contexts: dict[str, ClothCharExportContext] = {}


@contextmanager
def cloth_char_enter_export_context(dwd_obj: Object) -> Iterator[ClothCharExportContext]:
    global _current_export_context
    if _current_export_context is not None:
        raise Exception("Already in character cloth export context!")

    _current_export_context = ClothCharExportContext(dwd_obj)
    try:
        yield _current_export_context
    finally:
        _last_export_contexts[_current_export_context.dwd_obj_name] = _current_export_context
        _current_export_context = None


def cloth_char_export_context() -> ClothCharExportContext:
    if _current_export_context is None:
        raise Exception("Not in character cloth export context!")
    return _current_export_context


def cloth_char_last_export_contexts() -> dict[str, ClothCharExportContext]:
    return _last_export_contexts
