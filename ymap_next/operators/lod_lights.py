from bpy.types import Operator

from ..lod_lights.bake import (
    build_lod_light_maps,
    collect_lod_lights,
)
from ..properties.map import MapLodLightBakePropertiesBase, get_maps


def _active_group(context):
    maps = get_maps(context)
    if maps and maps.groups:
        return maps.groups.active_item
    return None


class SOLLUMZ_OT_map_bake_lod_lights(MapLodLightBakePropertiesBase, Operator):
    bl_idname = "sollumz.map_bake_lod_lights"
    bl_label = "Bake LOD Lights"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return _active_group(context) is not None

    def execute(self, context):
        # TODO(ymap): maybe print some statistics about generated lod lights
        # TODO(ymap): allow baking from multiple map groups
        group = _active_group(context)
        settings = self.get_settings()
        ll = collect_lod_lights(group, settings)
        if ll is None:
            self.report({"WARNING"}, f"No LOD lights found in '{group.name}' map group")
            return {"CANCELLED"}

        build_lod_light_maps(group, ll, settings)
        return {"FINISHED"}
