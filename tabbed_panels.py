import bpy
from typing import Optional, Type


class TabbedPanelHelper:
    _tab_panels: dict[str, bpy.types.Panel] = {}
    _panel_toggle_ops: dict[str, bpy.types.Operator] = {}

    use_grid: bool = True
    default_tab: Optional[str] = None

    def draw(self, context: bpy.types.Context):
        self.draw_before(context)
        self._draw_toggle_buttons(context)
        self.draw_after(context)

    def draw_before(self, context: bpy.types.Context):
        """Draw before buttons"""
        ...

    def draw_after(self, context: bpy.types.Context):
        """Draw after buttons"""
        ...

    def _draw_toggle_buttons(self, context: bpy.types.Context):
        layout = self.layout.grid_flow(
            align=True, row_major=True, columns=4) if self.use_grid else self.layout.row(align=True)

        for tab_id, op_cls in self._panel_toggle_ops.items():
            if tab_id not in self._tab_panels:
                continue

            tab_panel = self._tab_panels[tab_id]

            if not tab_panel.poll_tab(context):
                continue

            is_active = tab_panel._get_active_tab() == op_cls.tab_id

            layout.operator(op_cls.bl_idname, text=tab_panel.bl_label,
                            icon=tab_panel.icon, depress=is_active)

    @classmethod
    def register(cls):
        cls._tab_panels = {}
        cls._panel_toggle_ops = {}


class TabPanel:
    parent_tab_panel: Type[TabbedPanelHelper]
    icon: str = "NONE"

    bl_options = {"HIDE_HEADER"}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return cls._is_active and cls.poll_tab(context)

    @classmethod
    def poll_tab(cls, context: bpy.types.Context):
        """Poll method for tabs (do not override poll)"""
        return True

    @classmethod
    def _get_active_tab_propname(cls):
        return f"{cls.bl_parent_id}_active"

    @classmethod
    def _get_active_tab(cls) -> str:
        tabbed_panel = cls.parent_tab_panel
        active_tab = getattr(bpy.context.scene, cls._get_active_tab_propname())

        if active_tab == "NONE":
            return ""

        if active_tab:
            return active_tab

        if tabbed_panel.default_tab is not None and tabbed_panel.default_tab in tabbed_panel._tab_panels:
            return tabbed_panel.default_tab

    @classmethod
    def _set_active_tab(cls, tab_id: str):
        setattr(bpy.context.scene, cls._get_active_tab_propname(), tab_id)

    @classmethod
    @property
    def _is_active(cls):
        return cls._get_active_tab() == cls.bl_idname

    @classmethod
    def register(cls):
        if not hasattr(cls, "parent_tab_panel"):
            raise NotImplementedError(
                f"Panel tab '{cls.__name__}' has no ``parent_tab_panel`` defined!")

        tabbed_panel = cls.parent_tab_panel
        active_tab_prop_name = cls._get_active_tab_propname()

        if not hasattr(bpy.types.Scene, active_tab_prop_name):
            setattr(
                bpy.types.Scene,
                active_tab_prop_name,
                bpy.props.StringProperty()
            )

        toggle_op = cls._tab_toggle_op_factory(cls.bl_idname)
        tabbed_panel._panel_toggle_ops[cls.bl_idname] = toggle_op

        bpy.utils.register_class(toggle_op)

        tabbed_panel._tab_panels[cls.bl_idname] = cls

    @classmethod
    def unregister(cls):
        active_tab_prop_name = cls._get_active_tab_propname()
        if hasattr(bpy.types.Scene, active_tab_prop_name):
            delattr(bpy.types.Scene, active_tab_prop_name)

    @classmethod
    def _tab_toggle_op_factory(cls, _tab_id: str):
        """Dynamically create a tab toggle operator class"""
        class SOLLUMZ_OT_toggle_tab(bpy.types.Operator):
            bl_idname = f"sollumz.toggletab_{_tab_id.lower()}"
            bl_description = f"Toggle the {cls.bl_label} tab"
            bl_label = _tab_id
            tab_id = _tab_id

            def execute(self, context: bpy.types.Context):
                active_tab = cls._get_active_tab()

                if active_tab == self.tab_id:
                    cls._set_active_tab("NONE")
                else:
                    cls._set_active_tab(self.tab_id)

                return {"FINISHED"}

        return SOLLUMZ_OT_toggle_tab
