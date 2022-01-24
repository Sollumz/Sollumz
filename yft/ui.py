from ..sollumz_ui import SOLLUMZ_PT_OBJECT_PANEL
from ..sollumz_properties import SollumType


def draw_veh_window_properties(self, context):
    obj = context.active_object
    if obj.sollum_type == SollumType.FRAGVEHICLEWINDOW:
        for prop in obj.vehicle_window_properties.__annotations__:
            self.layout.prop(obj.vehicle_window_properties, prop)


def draw_child_properties(self, context):
    obj = context.active_object
    if obj.sollum_type == SollumType.FRAGCHILD:
        for prop in obj.child_properties.__annotations__:
            self.layout.prop(obj.child_properties, prop)


def draw_group_properties(self, context):
    obj = context.active_object
    if obj.sollum_type == SollumType.FRAGGROUP:
        layout = self.layout
        layout.prop(obj, "name")
        for prop in obj.group_properties.__annotations__:
            layout.prop(obj.group_properties, prop)


def draw_lod_properties(self, context):
    obj = context.active_object
    if obj.sollum_type == SollumType.FRAGLOD:
        layout = self.layout
        for prop in obj.lod_properties.__annotations__:
            if "archetype" in prop:
                break
            layout.prop(obj.lod_properties, prop)
        layout.separator()
        layout.label(text="Archetype Properties")
        for prop in obj.lod_properties.__annotations__:
            if not "archetype" in prop:
                continue
            layout.prop(obj.lod_properties, prop)


def draw_fragment_properties(self, context):
    obj = context.active_object
    if obj.sollum_type == SollumType.FRAGMENT:
        for prop in obj.fragment_properties.__annotations__:
            self.layout.prop(obj.fragment_properties, prop)


def register():
    SOLLUMZ_PT_OBJECT_PANEL.append(draw_fragment_properties)
    SOLLUMZ_PT_OBJECT_PANEL.append(draw_lod_properties)
    SOLLUMZ_PT_OBJECT_PANEL.append(draw_group_properties)
    SOLLUMZ_PT_OBJECT_PANEL.append(draw_child_properties)
    SOLLUMZ_PT_OBJECT_PANEL.append(draw_veh_window_properties)


def unregister():
    SOLLUMZ_PT_OBJECT_PANEL.remove(draw_fragment_properties)
    SOLLUMZ_PT_OBJECT_PANEL.remove(draw_lod_properties)
    SOLLUMZ_PT_OBJECT_PANEL.remove(draw_group_properties)
    SOLLUMZ_PT_OBJECT_PANEL.remove(draw_child_properties)
    SOLLUMZ_PT_OBJECT_PANEL.remove(draw_veh_window_properties)
