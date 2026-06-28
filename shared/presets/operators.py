"""
Generic preset operator mix-ins.

Per-category subclasses just declare `category` as a class attribute pointing
to the module-level PresetCategory instance. The mix-in does the rest.
"""

from bpy.props import StringProperty

from . import store
from .core import PresetCategory


class PresetSaveOperatorBase:
    """Save the current target as a named preset. Triggered by the `+` button
    in the popover."""

    bl_options = {"REGISTER", "INTERNAL"}

    category: PresetCategory = None  # override in subclass
    get_target = None  # optional classvar override; if set, replaces category.get_target

    name: StringProperty(name="Name", description="Preset name")

    @classmethod
    def poll(cls, context):
        if cls.category is None:
            return False
        ok, reason = cls.category.poll(context)
        if not ok and reason:
            cls.poll_message_set(reason)
        return ok

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        category = self.category
        name = (self.name or "").strip()
        if not name:
            self.report({"WARNING"}, f"Please specify a name for the new {category.label.lower()} preset.")
            return {"CANCELLED"}

        getter = type(self).get_target or category.get_target
        target = getter(context)
        if target is None:
            self.report({"WARNING"}, f"No {category.label.lower()} target available.")
            return {"CANCELLED"}

        data = category.capture(target)
        is_new = store.add_preset(category, name, data)
        action = "Saved" if is_new else "Updated"
        self.report({"INFO"}, f"{action} {category.label.lower()} preset '{name}'.")
        _tag_redraw(context)
        return {"FINISHED"}


class PresetLoadOperatorBase:
    """Apply a named preset to every selected target. Triggered by
    clicking the preset name in the popover."""

    bl_options = {"REGISTER", "UNDO"}

    category: PresetCategory = None
    get_target = None  # optional classvar override; if set, replaces category.get_target
    get_targets = None  # optional classvar override; if set, replaces category.get_targets

    name: StringProperty(name="Preset", description="Preset name to apply")

    @classmethod
    def poll(cls, context):
        if cls.category is None:
            return False
        ok, reason = cls.category.poll(context)
        if not ok and reason:
            cls.poll_message_set(reason)
        return ok

    def execute(self, context):
        category = self.category
        preset = store.find_preset(category, self.name)
        if preset is None:
            self.report({"WARNING"}, f"{category.label} preset '{self.name}' not found.")
            return {"CANCELLED"}

        targets = category.iter_targets(
            context,
            get_target_override=type(self).get_target,
            get_targets_override=type(self).get_targets,
        )
        if not targets:
            self.report({"WARNING"}, f"No {category.label.lower()} target available.")
            return {"CANCELLED"}

        # Subclasses may extend by passing extra apply options as kwargs.
        opts = self._apply_options(context)
        data = preset.get("data", {})
        for target in targets:
            category.apply(target, data, **opts)

        count = len(targets)
        suffix = f" to {count} targets." if count > 1 else "."
        self.report({"INFO"}, f"Applied {category.label.lower()} preset '{self.name}'{suffix}")
        _tag_redraw(context)
        return {"FINISHED"}

    def _apply_options(self, context):
        """Hook for subclasses to forward extra Operator props as kwargs to
        category.apply(). Default: empty dict."""
        return {}


class PresetDeleteOperatorBase:
    """Delete a named preset. Triggered by the `x` button next to each row."""

    bl_options = {"REGISTER", "INTERNAL"}

    category: PresetCategory = None

    name: StringProperty(name="Preset", description="Preset name to delete")

    def execute(self, context):
        category = self.category
        if self.name in category.blacklist:
            self.report({"WARNING"}, f"Cannot delete bundled {category.label.lower()} preset '{self.name}'.")
            return {"CANCELLED"}

        if not store.delete_preset(category, self.name):
            self.report({"WARNING"}, f"{category.label} preset '{self.name}' not found.")
            return {"CANCELLED"}

        self.report({"INFO"}, f"Deleted {category.label.lower()} preset '{self.name}'.")
        _tag_redraw(context)
        return {"FINISHED"}


def _tag_redraw(context):
    for area in getattr(context, "screen", None).areas if context.screen else []:
        area.tag_redraw()
