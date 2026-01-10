import bpy
from bpy.types import (
    Object
)
from szio.gta5 import (
    EmbeddedTexture,
    AssetDrawableDictionary,
    AssetClothDictionary,
    create_asset_drawable_dictionary,
)
from ..ydr.ydrexport_io import create_drawable_asset
from ..ydr.cloth_char_io import cloth_char_export_dictionary
from ..ydr.cloth_diagnostics import (
    cloth_export_context,
    cloth_enter_export_context,
)
from ..tools.blenderhelper import remove_number_suffix
from ..sollumz_properties import SollumType
from ..iecontext import export_context, ExportBundle


def export_ydd(dwd_obj: Object) -> ExportBundle:
    embedded_tex = []
    with cloth_enter_export_context(dwd_obj):
        cld = cloth_char_export_dictionary(dwd_obj)
        dwd = create_drawable_dictionary_asset(dwd_obj, cld, out_embedded_textures=embedded_tex)

    return export_context().make_bundle(dwd, ("", cld), extra_files=[t.data for t in embedded_tex])


def create_drawable_dictionary_asset(
    dwd_obj: Object,
    cloth_dictionary: AssetClothDictionary | None,
    out_embedded_textures: list[EmbeddedTexture] | None = None,
) -> AssetDrawableDictionary | None:
    dwd_armature = find_ydd_armature(dwd_obj) if dwd_obj.type != "ARMATURE" else dwd_obj

    exclude_skeleton = export_context().settings.exclude_skeleton

    cloths = cloth_dictionary.cloths if cloth_dictionary else {}

    drawables = {}
    for child in dwd_obj.children:
        if child.sollum_type != SollumType.DRAWABLE:
            continue

        if child.type != "ARMATURE":
            armature_obj = dwd_armature
        else:
            armature_obj = None

        cloth = cloths.get(remove_number_suffix(child.name), None) if cloths else None

        with cloth_export_context().enter_drawable_context(child):
            drawable = create_drawable_asset(
                child,
                armature_obj=armature_obj,
                out_embedded_textures=out_embedded_textures,
                char_cloth=cloth,
            )

        if exclude_skeleton or child.type != "ARMATURE":
            drawable.skeleton = None

        drawables[drawable.name] = drawable

    dwd = create_asset_drawable_dictionary(export_context().settings.targets)
    dwd.drawables = drawables
    return dwd


def find_ydd_armature(ydd_obj: bpy.types.Object):
    """Find first drawable with an armature in ``ydd_obj``."""
    for child in ydd_obj.children:
        if child.type == "ARMATURE":
            return child
