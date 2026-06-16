"""Panel mix-in based on Blender's bl_ui.utils.PresetPanel."""

from . import store
from .core import PresetCategory


class PresetPanel:
    """Panel mix-in. Do not register directly; subclass with bpy.types.Panel."""

    # Subclasses override these:
    category: PresetCategory = None
    save_operator: str = ""  # bl_idname of the save operator
    load_operator: str = ""  # bl_idname of the load operator
    delete_operator: str = ""  # bl_idname of the delete operator

    bl_label = "Presets"
    bl_options = {"INSTANCED"}  # popover, not auto-added to anywhere

    @classmethod
    def draw_panel_header(cls, layout):
        """Embed the popover button in a host panel's header. Call from the
        host panel's `draw_header_preset()` hook."""
        layout.emboss = "NONE"
        layout.popover(panel=cls.__name__, icon="PRESET", text="")

    def draw(self, context):
        layout = self.layout
        category = self.category
        if category is None:
            layout.label(text=f"{type(self).__name__} has no category configured", icon="ERROR")
            return

        wm = context.window_manager

        presets = store.load_presets(category)
        if presets:
            extra_op_props = self.extra_load_operator_props(context) or {}
            col = layout.column(align=True)
            col.emboss = "PULLDOWN_MENU"
            for preset in presets:
                name = preset.get("name", "")
                if not name:
                    continue
                row = col.row(align=True)
                op = row.operator(self.load_operator, text=name)
                op.name = name
                for key, value in extra_op_props.items():
                    setattr(op, key, value)
                if name not in category.blacklist:
                    del_op = row.operator(self.delete_operator, text="", icon="REMOVE")
                    del_op.name = name
            layout.separator()
        else:
            layout.label(text=f"No {category.label.lower()} presets yet.", icon="INFO")
            layout.separator()

        row = layout.row()
        row.operator_context = "EXEC_DEFAULT"  # don't show popup from save_operator
        row.prop(wm, "preset_name", text="")
        subrow = row.row()
        subrow.emboss = "PULLDOWN_MENU"
        op = subrow.operator(self.save_operator, text="", icon="ADD")
        op.name = wm.preset_name

        path = store.user_preset_path(category)
        if path.exists():
            layout.separator()
            layout.operator("wm.path_open", text="Open Presets File", icon="FILE").filepath = str(path)

        self.draw_extra(context)

    def draw_extra(self, context):
        """Hook for subclasses to add category-specific UI (e.g. apply-time
        options) to the bottom of the popover."""
        return

    def extra_load_operator_props(self, context):
        """Hook for subclasses to forward extra kwargs to the load operator
        when each preset row is drawn. Return a dict mapping operator prop
        name -> value, or None for no extras."""
        return None
