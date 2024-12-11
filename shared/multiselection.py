"""
Module with shared logic to support multi-selection in Blender PropertyGroups.
"""

from bpy.types import (
    PropertyGroup,
    bpy_struct,
    Event,
    UILayout,
)
from bpy.props import (
    IntProperty,
    FloatProperty,
    StringProperty,
    BoolProperty,
    EnumProperty,
    CollectionProperty,
    PointerProperty,
)
from collections.abc import Iterator
from enum import Enum, auto


class SelectionIndex(PropertyGroup):
    index: IntProperty(name="Index")


class SelectMode(Enum):
    SET = auto()
    EXTEND = auto()
    TOGGLE = auto()


class MultiSelectAccessMixin:
    def find_owner_collection(self) -> 'MultiSelectCollectionMixin':
        id_data = self.id_data
        path = self.path_from_id()
        collection_path, _ = path.split(".selection")
        collection = id_data.path_resolve(collection_path)
        return collection

    @property
    def active_item(self) -> bpy_struct:
        return self.find_owner_collection().active_item

    def iter_selected_items(self) -> Iterator[bpy_struct]:
        return self.find_owner_collection().iter_selected_items()

    @property
    def selected_items(self) -> list[bpy_struct]:
        return self.find_owner_collection().selected_items


class MultiSelectCollectionMixin:
    def _on_active_index_update(self, context):
        self.on_active_index_update(context)

    active_index: IntProperty(name="Active Index")
    active_index_with_update_callback: IntProperty(
        name="Active Index",
        get=lambda s: s.active_index,
        set=_on_active_index_update,
    )
    selection_indices: CollectionProperty(type=SelectionIndex)
    selection: PointerProperty(type=MultiSelectAccessMixin)  # should be overwritten by implementors

    def on_active_index_update(self, context):
        pass

    def get_item(self, index: int) -> bpy_struct:
        raise NotImplementedError("get_item")

    @property
    def active_item(self) -> bpy_struct:
        return self.get_item(self.active_index)

    def iter_selected_items(self) -> Iterator[bpy_struct]:
        found_active_item = False
        for s in self.selection_indices:
            item = self.get_item(s.index)
            if item is not None:
                if s.index == self.active_index:
                    found_active_item = True
                yield item

        if not found_active_item:
            # in some edge-cases cases where the active item may not appear in the selection list
            yield self.active_item

    @property
    def selected_items(self) -> list[bpy_struct]:
        return list(self.iter_selected_items())

    def select(self, index: int, mode: SelectMode = SelectMode.SET):
        match mode:
            case SelectMode.SET:
                self.selection_indices.clear()
                self.active_index = index
                self.selection_indices.add().index = index
            case SelectMode.EXTEND:
                self.selection_indices.clear()
                start_index = min(self.active_index, index)
                end_index = max(self.active_index, index)
                for i in range(start_index, end_index + 1):
                    self.selection_indices.add().index = i
            case SelectMode.TOGGLE:
                for i, s in enumerate(self.selection_indices):
                    if s.index == index:
                        index_in_selection = i
                        break
                else:
                    index_in_selection = None

                if index_in_selection is None:
                    # select
                    self.active_index = index
                    self.selection_indices.add().index = index
                else:
                    # deselect
                    self.selection_indices.remove(index_in_selection)


class MultiSelectOperatorMixin:
    bl_options = {"UNDO"}

    index: IntProperty(name="Index")
    extend: BoolProperty(name="Extend")
    toggle: BoolProperty(name="Toggle")

    @classmethod
    def get_collection(cls, context) -> MultiSelectCollectionMixin:
        raise NotImplementedError("get_collection")

    @classmethod
    def poll(cls, context):
        return cls.get_collection(context) is not None

    def execute(self, context):
        collection = self.get_collection(context)
        mode = (
            SelectMode.EXTEND if self.extend else
            SelectMode.TOGGLE if self.toggle else
            SelectMode.SET
        )
        collection.select(self.index, mode)
        return {"FINISHED"}

    def invoke(self, context, event: Event):
        self.extend = event.shift
        self.toggle = event.ctrl
        return self.execute(context)


def _MultiSelectBasicProperty(prop_fn, attr_name: str, **kwargs):
    def _getter(self: MultiSelectAccessMixin):
        return getattr(self.active_item, attr_name)

    def _setter(self: MultiSelectAccessMixin, value):
        for item in self.iter_selected_items():
            setattr(item, attr_name, value)

    # TODO: somehow access kwards from the propertygroup we are wrapping to avoid code duplication
    return prop_fn(**kwargs, get=_getter, set=_setter)


def MultiSelectIntProperty(attr_name: str, **kwargs):
    return _MultiSelectBasicProperty(IntProperty, attr_name, **kwargs)


def MultiSelectFloatProperty(attr_name: str, **kwargs):
    return _MultiSelectBasicProperty(FloatProperty, attr_name, **kwargs)


def MultiSelectStringProperty(attr_name: str, **kwargs):
    return _MultiSelectBasicProperty(StringProperty, attr_name, **kwargs)


def MultiSelectEnumProperty(attr_name: str, **kwargs):
    def _getter(self: MultiSelectAccessMixin) -> int:
        return self.active_item[attr_name]

    def _setter(self: MultiSelectAccessMixin, value: int):
        for item in self.iter_selected_items():
            item[attr_name] = value

    return EnumProperty(**kwargs, get=_getter, set=_setter)


class MultiSelectUIListMixin:
    name_prop: str = "name"
    default_item_icon: str = "NONE"
    name_editable: bool = True
    multiselect_operator: str = ""

    def draw_item(
        self, context, layout: UILayout, data, item, icon, active_data, active_propname, index
    ):
        collection: MultiSelectCollectionMixin = data
        icon = self.get_item_icon(item)
        match icon:
            case str():
                icon_str, icon_value = icon, 0
            case int():
                icon_str, icon_value = "NONE", icon
            case _:
                raise ValueError(f"Invalid item icon. Only str or int supported, got '{icon}'")

        is_selected = len(collection.selection_indices) > 1 and any(
            i.index == index for i in collection.selection_indices)
        is_active = index == collection.active_index
        layout.active = len(collection.selection_indices) <= 1 or is_selected

        if is_active:
            if self.name_editable:
                layout.prop(item, self.name_prop, text="", emboss=False, icon=icon_str, icon_value=icon_value)
            else:
                layout.label(text=getattr(item, self.name_prop), icon=icon_str, icon_value=icon_value)
        else:
            # hacky way to left-align operator button text by having two buttons
            row = layout.row(align=True)
            subrow = row.row(align=True)
            subrow.alignment = "LEFT"
            op = subrow.operator(
                "sollumz.multiselect_archetype",
                text=getattr(item, self.name_prop),
                icon=icon_str, icon_value=icon_value,
                emboss=is_selected or is_active,
                depress=False
            )
            op.index = index
            subrow = row.row(align=True)
            op = subrow.operator(
                "sollumz.multiselect_archetype",
                text="",
                emboss=is_selected or is_active,
                depress=False
            )
            op.index = index

    def get_item_icon(self, item) -> str | int:
        return self.default_item_icon
