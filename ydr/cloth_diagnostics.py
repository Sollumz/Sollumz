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

if bpy.app.version >= (4, 5, 0):
    POINT_UNIFORM_COLOR_SHADER_NAME = "POINT_UNIFORM_COLOR"
else:
    POINT_UNIFORM_COLOR_SHADER_NAME = "UNIFORM_COLOR"


# class ClothCharDiagMeshBinding(NamedTuple):
#    co: Vector
#    v0: Vector
#    v1: Vector
#    v2: Vector
#    n: Vector


class ClothDiagMeshBindingError(NamedTuple):
    co: Vector
    # Char errors
    error_projection: bool
    error_distance: bool
    # Env errors
    error_multiple_matches: bool


class ClothDiagMeshMaterialError(NamedTuple):
    v0: Vector
    v1: Vector
    v2: Vector


class ClothDiagnosticsOverlayFlags(Flag):
    MATERIAL_ERRORS = auto()
    BINDING_ERRORS = auto()
    BINDINGS = auto()


class ClothDiagnostics:
    def __init__(self, root_obj_name: str, drawable_obj_name: str):
        self.root_obj_name = root_obj_name
        self.drawable_obj_name = drawable_obj_name
        self.drawable_model_obj_name = ""
        self.cloth_obj_name = ""
        self.mesh_material_errors: list[ClothDiagMeshMaterialError] | None = None
        # self.mesh_bindings: list[ClothCharDiagMeshBinding] | None = None
        self.mesh_binding_errors: list[ClothDiagMeshBindingError] | None = None
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

        layout.label(text=f"{self.root_obj_name}  {self.drawable_obj_name}")

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
        # row = layout.row(align=True)
        # row.label(text="        Bindings")
        # _visible_icon_prop(row, wm, "sz_ui_cloth_diag_bindings_visualize")

    def draw_overlay(self, flags: ClothDiagnosticsOverlayFlags):
        if not self.cloth_obj_name or not self.drawable_model_obj_name:
            return

        drawable_mesh_obj = bpy.data.objects.get(self.drawable_model_obj_name, None)
        cloth_obj = bpy.data.objects.get(self.cloth_obj_name, None)
        if not cloth_obj or not drawable_mesh_obj:
            return

        mesh_material_errors = self.mesh_material_errors
        mesh_binding_errors = self.mesh_binding_errors

        # cloth_transform = cloth_obj.matrix_world
        drawable_transform = drawable_mesh_obj.matrix_world

        theme = get_theme_settings()

        if ClothDiagnosticsOverlayFlags.MATERIAL_ERRORS in flags and mesh_material_errors:
            shader = gpu.shader.from_builtin("UNIFORM_COLOR")
            if self._mesh_material_errors_batch is None:
                self._mesh_material_errors_batch = batch.batch_for_shader(
                    shader, "TRIS", {"pos": [v for e in mesh_material_errors for v in (e.v0, e.v1, e.v2)]})

            gpu.state.blend_set("ALPHA")
            with gpu.matrix.push_pop():
                gpu.matrix.multiply_matrix(drawable_transform)
                shader.uniform_float("color", theme.cloth_overlay_material_errors)
                self._mesh_material_errors_batch.draw(shader)

        if ClothDiagnosticsOverlayFlags.BINDING_ERRORS in flags and mesh_binding_errors:
            shader = gpu.shader.from_builtin(POINT_UNIFORM_COLOR_SHADER_NAME)
            if self._mesh_binding_errors_batch is None:
                self._mesh_binding_errors_batch = batch.batch_for_shader(
                    shader, "POINTS", {"pos": [e.co for e in mesh_binding_errors]})

            gpu.state.point_size_set(theme.cloth_overlay_binding_errors_size)
            gpu.state.blend_set("ALPHA")
            with gpu.matrix.push_pop():
                gpu.matrix.multiply_matrix(drawable_transform)
                shader.uniform_float("color", theme.cloth_overlay_binding_errors)
                self._mesh_binding_errors_batch.draw(shader)

        # TODO: bindings need some better overlay to be useful (ideally needed to see which faces were binded facing
        #       inside or outside)
        # if ClothDiagnosticsOverlayFlags.BINDINGS in flags and mesh_bindings:
        #    shader = gpu.shader.from_builtin("UNIFORM_COLOR")
        #    if self._mesh_bindings_drawable_batch is None:
        #        drawable_coords = []
        #        cloth_coords = []
        #        cloth_line_coords = []
        #
        #        for b in mesh_bindings:
        #            drawable_coords.append(b.co)
        #            c = Vector()
        #            v0 = b.v0
        #            v1 = b.v1
        #            v2 = b.v2
        #            for p in (v0, v1, v2):
        #                cloth_coords.append(p)
        #                c += p
        #
        #            c /= 3
        #
        #            n = b.n
        #            cloth_line_coords.append(c)
        #            cloth_line_coords.append(c + n * 0.1)
        #
        #        self._mesh_bindings_drawable_batch = batch.batch_for_shader(shader, "POINTS", {"pos": drawable_coords})
        #        self._mesh_bindings_cloth_batch = batch.batch_for_shader(shader, "TRIS", {"pos": cloth_coords})
        #        self._mesh_bindings_cloth_lines_batch = batch.batch_for_shader(
        #            shader, "LINES", {"pos": cloth_line_coords})
        #
        #    gpu.state.point_size_set(12.5)
        #    gpu.state.blend_set("ALPHA")
        #    with gpu.matrix.push_pop():
        #        gpu.matrix.multiply_matrix(drawable_transform)
        #        shader.uniform_float("color", (0.05, 0.75, 0.05, 0.5))
        #        self._mesh_bindings_drawable_batch.draw(shader)
        #
        #    with gpu.matrix.push_pop():
        #        gpu.matrix.multiply_matrix(cloth_transform)
        #        shader.uniform_float("color", (0.85, 0.05, 0.05, 0.5))
        #        self._mesh_bindings_cloth_batch.draw(shader)
        #
        #        shader.uniform_float("color", (0.85, 0.05, 0.85, 1.0))
        #        self._mesh_bindings_cloth_lines_batch.draw(shader)


class _ClothDiagnosticsDict(dict[str, ClothDiagnostics]):
    def __missing__(self, key):
        self[key] = d = ClothDiagnostics(self._root_obj_name, key)
        return d

    def __init__(self, root_obj_name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._root_obj_name = root_obj_name


class ClothExportContext:

    def __init__(self, root_obj: Object):
        self.root_obj_name = root_obj.name
        self._diagnostics: dict[str, ClothDiagnostics] = _ClothDiagnosticsDict(self.root_obj_name)
        self._current_diagnostics: ClothDiagnostics | None = None

    @contextmanager
    def enter_drawable_context(self, drawable_obj: Object) -> Iterator[ClothDiagnostics]:
        if self._current_diagnostics is not None:
            raise Exception("Not in cloth drawable context!")
        self._current_diagnostics = self._diagnostics[drawable_obj.name]
        try:
            yield self._current_diagnostics
        finally:
            if self._current_diagnostics.mesh_material_errors:
                bpy.context.window_manager.sz_ui_cloth_diag_material_errors_visualize = True
            if self._current_diagnostics.mesh_binding_errors:
                bpy.context.window_manager.sz_ui_cloth_diag_binding_errors_visualize = True
            self._current_diagnostics = None

    @property
    def diagnostics(self) -> ClothDiagnostics:
        if self._current_diagnostics is None:
            raise Exception("Not in cloth drawable context!")
        return self._current_diagnostics

    @property
    def all_diagnostics(self) -> dict[str, ClothDiagnostics]:
        return self._diagnostics


_current_export_context: ClothExportContext | None = None
_last_export_contexts: dict[str, ClothExportContext] = {}


@contextmanager
def cloth_enter_export_context(root_obj: Object) -> Iterator[ClothExportContext]:
    global _current_export_context
    if _current_export_context is not None:
        raise Exception("Already in cloth export context!")

    _current_export_context = ClothExportContext(root_obj)
    try:
        yield _current_export_context
    finally:
        _last_export_contexts[_current_export_context.root_obj_name] = _current_export_context
        _current_export_context = None


def cloth_export_context() -> ClothExportContext:
    if _current_export_context is None:
        raise Exception("Not in cloth export context!")
    return _current_export_context


def cloth_last_export_contexts() -> dict[str, ClothExportContext]:
    return _last_export_contexts
