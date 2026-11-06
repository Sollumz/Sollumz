import bpy

from ..iecontext import ExportContext, ExportSettings, export_context_scope
from ..tools.drawablehelper import convert_obj_to_drawable
from ..tools.meshhelper import mesh_add_missing_uv_maps, mesh_rename_color_attrs_by_order
from ..ydr.shader_materials import create_shader
from ..ydr.ydrexport import export_ydr
from .shared import log_capture


def _export_ydr(drawable_obj: bpy.types.Object):
    with export_context_scope(ExportContext("test", ExportSettings(targets=()))):
        return export_ydr(drawable_obj)


def test_export_no_missing_color_attrs_warning_after_rename_by_order(plane_object):
    mesh = plane_object.data
    mesh.materials.append(create_shader("default.sps"))
    mesh.color_attributes.new("my_color", "BYTE_COLOR", "CORNER")
    mesh_add_missing_uv_maps(mesh)
    drawable_obj = convert_obj_to_drawable(plane_object)
    # Evaluate before renaming so the evaluated mesh would keep the old name if the rename didn't tag an update
    bpy.context.evaluated_depsgraph_get()

    mesh_rename_color_attrs_by_order(mesh)

    with log_capture() as logs:
        _export_ydr(drawable_obj)

    assert not [w for w in logs.warnings if "missing" in w]
