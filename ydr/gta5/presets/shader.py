"""
Shader preset category.

Target is a Sollumz shader Material. Data is per-shader-parameter values
extracted from the material's node tree.

JSON schema:

    {
        "params": [
            {"name": "<param node name>", "x": 0.0, "y": 0.0, "z": 0.0, "w": 0.0},
            {"name": "<texture param node name>", "texture": "<texture filename>"},
            ...
        ]
    }

Float-vector params and texture params are stored as separate dict shapes.
The applier matches the shader's `parameter_map` so applying a preset saved
for one shader to a material of a different shader silently skips fields
that don't exist on the target.
"""

import bpy
from bpy.props import BoolProperty
from bpy.types import Material, ShaderNodeTexImage
from pathlib import Path

from szio.gta5.shader import (
    ShaderParameterFloatVectorDef,
    ShaderParameterTextureDef,
    ShaderManager,
)
from ....shared.presets import (
    PresetCategory,
    register_preset_category,
    make_get_targets_from_objects,
    PresetSaveOperatorBase,
    PresetLoadOperatorBase,
    PresetDeleteOperatorBase,
    PresetPanel,
)
from ....shared.presets import migration
from ....shared.shader_nodes import SzShaderNodeParameter
from ....sollumz_properties import MaterialType
from ....sollumz_preferences import get_addon_preferences


def shader_preset_capture_dict(material):
    """Capture material shader parameters as a dict suitable for the preset
    file. Public so the legacy converters and external tools can reuse it."""
    shader_def = ShaderManager.find_shader(material.shader_properties.filename)
    if shader_def is None:
        return {"params": []}

    params = []
    for node in material.node_tree.nodes:
        param_def = shader_def.parameter_map.get(node.name, None)
        if param_def is None:
            continue

        if (
            isinstance(node, SzShaderNodeParameter)
            and isinstance(param_def, ShaderParameterFloatVectorDef)
            and not param_def.is_array
        ):
            entry = {"name": node.name}
            entry["x"] = node.get(0)
            if node.num_cols > 1:
                entry["y"] = node.get(1)
            if node.num_cols > 2:
                entry["z"] = node.get(2)
            if node.num_cols > 3:
                entry["w"] = node.get(3)
            params.append(entry)
        elif isinstance(node, ShaderNodeTexImage) and isinstance(param_def, ShaderParameterTextureDef):
            params.append({"name": node.name, "texture": node.sollumz_texture_name})
    return {"params": params}


def shader_preset_apply_dict(material, data, apply_textures=True):
    """Apply preset data to a material. Missing param-defs are skipped."""
    shader_def = ShaderManager.find_shader(material.shader_properties.filename)
    if shader_def is None:
        return

    for param in data.get("params", []) or []:
        name = param.get("name")
        if not name:
            continue
        param_def = shader_def.parameter_map.get(name)
        if param_def is None:
            continue
        node = material.node_tree.nodes.get(name)
        if node is None:
            continue

        if (
            isinstance(node, SzShaderNodeParameter)
            and isinstance(param_def, ShaderParameterFloatVectorDef)
            and not param_def.is_array
        ):
            if node.num_cols > 0 and param.get("x") is not None:
                node.set(0, param["x"])
            if node.num_cols > 1 and param.get("y") is not None:
                node.set(1, param["y"])
            if node.num_cols > 2 and param.get("z") is not None:
                node.set(2, param["z"])
            if node.num_cols > 3 and param.get("w") is not None:
                node.set(3, param["w"])
        elif (
            apply_textures and isinstance(node, ShaderNodeTexImage) and isinstance(param_def, ShaderParameterTextureDef)
        ):
            tex = param.get("texture")
            if not tex:
                continue
            img = bpy.data.images.get(tex) or bpy.data.images.get(tex + ".dds")
            if img is None:
                from ...ydrimport_io import lookup_texture_file, is_non_color_texture

                texture_path = lookup_texture_file(tex, None)
                if texture_path:
                    img = bpy.data.images.load(str(texture_path), check_existing=True)
                    if img and is_non_color_texture(shader_def.filename, name):
                        img.colorspace_settings.is_data = True
            if img:
                node.image = img


def _target_from_obj(obj):
    if obj is None:
        return None
    mat = obj.active_material
    if mat is None or mat.sollum_type != MaterialType.SHADER:
        return None
    return mat


def _get_target(context):
    return _target_from_obj(context.active_object)


def _poll(context):
    obj = context.active_object
    if obj is None:
        return False, "Select an object with a Sollumz shader material."
    mat = obj.active_material
    if mat is None or mat.sollum_type != MaterialType.SHADER:
        return False, "Active material is not a Sollumz shader."
    return True, ""


SHADER_PRESET_CATEGORY = PresetCategory(
    id="shader",
    label="Shader",
    game="gta5",
    bundled_defaults_path=Path(__file__).parent / "shader_presets.json",
    get_target=_get_target,
    get_targets=make_get_targets_from_objects(_target_from_obj),
    poll=_poll,
    capture_fn=shader_preset_capture_dict,
    apply_fn=shader_preset_apply_dict,
)


def _convert_legacy_xml(xml_path):
    import xml.etree.ElementTree as ET

    tree = ET.parse(str(xml_path))
    root = tree.getroot()
    presets = []
    for shader_preset in root.iterfind(".//ShaderPreset"):
        name = shader_preset.get("name", "")
        if not name:
            continue
        params = []
        for param in shader_preset.iterfind(".//Param") or []:
            entry = {"name": param.get("name", "")}
            for attr in ("x", "y", "z", "w"):
                val = param.get(attr)
                if val is not None:
                    try:
                        entry[attr] = float(val)
                    except ValueError:
                        pass
            tex = param.get("texture")
            if tex:
                entry["texture"] = tex
            params.append(entry)
        presets.append({"name": name, "data": {"params": params}})
    return presets


register_preset_category(SHADER_PRESET_CATEGORY)
migration.register_legacy_migration(SHADER_PRESET_CATEGORY, _convert_legacy_xml)


class SOLLUMZ_OT_save_shader_preset(PresetSaveOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.save_shader_preset"
    bl_label = "Save Shader Preset"
    bl_description = "Save current shader parameters as a named preset"
    category = SHADER_PRESET_CATEGORY


class SOLLUMZ_OT_load_shader_preset(PresetLoadOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.load_shader_preset"
    bl_label = "Apply Shader Preset"
    bl_description = "Apply a saved shader preset to the active material"
    category = SHADER_PRESET_CATEGORY

    apply_textures: BoolProperty(name="Apply Textures", default=True)

    def _apply_options(self, context):
        return {"apply_textures": bool(self.apply_textures)}


class SOLLUMZ_OT_delete_shader_preset(PresetDeleteOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.delete_shader_preset"
    bl_label = "Delete Shader Preset"
    bl_description = "Remove a saved shader preset"
    category = SHADER_PRESET_CATEGORY


class SOLLUMZ_PT_shader_presets(PresetPanel, bpy.types.Panel):
    bl_label = "Shader Presets"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_options = {"INSTANCED"}

    category = SHADER_PRESET_CATEGORY
    save_operator = SOLLUMZ_OT_save_shader_preset.bl_idname
    load_operator = SOLLUMZ_OT_load_shader_preset.bl_idname
    delete_operator = SOLLUMZ_OT_delete_shader_preset.bl_idname

    def draw_extra(self, context):
        # Expose the apply-textures toggle (stored on addon preferences so it
        # persists across sessions, matching the previous behavior).
        prefs = get_addon_preferences(context)
        if prefs is not None:
            self.layout.separator()
            self.layout.prop(prefs, "shader_preset_apply_textures", text="Apply Textures")

    def extra_load_operator_props(self, context):
        prefs = get_addon_preferences(context)
        if prefs is None:
            return None
        return {"apply_textures": bool(prefs.shader_preset_apply_textures)}
