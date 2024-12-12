"""
Module with shared logic to support multi-selection in Blender PropertyGroups.
"""

import bpy
from bpy.types import (
    PropertyGroup,
    bpy_struct,
    bpy_prop_collection,
    Event,
    UILayout,
    UI_UL_list,
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
from typing import Optional
from collections.abc import Iterator, Sequence
from enum import Enum, auto
import numpy as np


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
    def _on_active_index_update_from_ui(self, value):
        # This callback is only triggered when clicking on the active item in the list once it switched to a textfield
        # instead of buttons
        # Use select() instead of setting active_index to deselected the other items when clicking again on the active
        # item
        self.select(value, ui_callbacks=True)

    active_index: IntProperty(name="Active Index")
    active_index_with_update_callback_for_ui: IntProperty(
        name="Active Index",
        get=lambda s: s.active_index,
        set=_on_active_index_update_from_ui,
    )
    selection_indices: CollectionProperty(type=SelectionIndex)
    selection: PointerProperty(type=MultiSelectAccessMixin)  # should be overwritten by implementors

    def on_active_index_update_from_ui(self, context):
        pass

    @property
    def num_items(self) -> int:
        return len(self.get_collection_property())

    def get_item(self, index: int) -> bpy_struct:
        return self.get_collection_property()[index]

    def get_collection_property(self) -> bpy_prop_collection:
        raise NotImplementedError("get_collection_property")

    @property
    def has_multiple_selection(self) -> bool:
        return len(self.selection_indices) > 1

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

    def select(
        self,
        index: int,
        mode: SelectMode = SelectMode.SET,
        filtered_items: Optional[Sequence[bool]] = None,
        reorder_items: Optional[Sequence[int]] = None,
        ui_callbacks: bool = False,
    ):
        match mode:
            case SelectMode.SET:
                self.selection_indices.clear()
                self.active_index = index
                self.selection_indices.add().index = index
                if ui_callbacks:
                    self.on_active_index_update_from_ui(bpy.context)
            case SelectMode.EXTEND:
                self.selection_indices.clear()
                if reorder_items:
                    assert len(reorder_items) == self.num_items
                    actual_to_reordered_index_map = np.array(reorder_items)
                    reordered_to_actual_index_map = actual_to_reordered_index_map[actual_to_reordered_index_map]
                    index0 = actual_to_reordered_index_map[self.active_index]
                    index1 = actual_to_reordered_index_map[index]
                    start_index = min(index0, index1)
                    end_index = max(index0, index1)
                else:
                    start_index = min(self.active_index, index)
                    end_index = max(self.active_index, index)

                if filtered_items:
                    assert len(filtered_items) == self.num_items

                for i in range(start_index, end_index + 1):
                    if reorder_items:
                        i = reordered_to_actual_index_map[i]
                    is_filtered_out = filtered_items and not filtered_items[i]
                    if not is_filtered_out:
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
                    if ui_callbacks:
                        self.on_active_index_update_from_ui(bpy.context)
                else:
                    # deselect
                    self.selection_indices.remove(index_in_selection)

    def select_all(self):
        self.selection_indices.clear()
        for i in range(self.num_items):
            self.selection_indices.add().index = i


class MultiSelectOperatorMixin:
    bl_options = {"UNDO"}

    index: IntProperty(name="Index")
    extend: BoolProperty(name="Extend")
    toggle: BoolProperty(name="Toggle")

    apply_filter: BoolProperty()
    filter_name: StringProperty()
    bitflag_filter_item: IntProperty()
    use_filter_sort_reverse: BoolProperty()
    use_filter_sort_alpha: BoolProperty()
    use_filter_invert: BoolProperty()

    trigger_ui_callbacks: BoolProperty(default=True)

    def get_collection(self, context) -> MultiSelectCollectionMixin:
        raise NotImplementedError("get_collection")

    def execute(self, context):
        collection = self.get_collection(context)
        filtered_items = None
        reorder_items = None
        if self.apply_filter:
            filter_flags, reorder_items = _default_filter_items(
                collection,
                self.filter_name, self.bitflag_filter_item,
                self.use_filter_sort_reverse, self.use_filter_sort_alpha
            )
            if filter_flags:
                filtered_items = (np.array(filter_flags) & self.bitflag_filter_item) != 0
                if self.use_filter_invert:
                    filtered_items = np.logical_not(filtered_items)
                filtered_items = list(filtered_items)

        mode = (
            SelectMode.EXTEND if self.extend else
            SelectMode.TOGGLE if self.toggle else
            SelectMode.SET
        )
        collection.select(
            self.index,
            mode,
            filtered_items=filtered_items,
            reorder_items=reorder_items,
            ui_callbacks=self.trigger_ui_callbacks
        )
        return {"FINISHED"}

    def invoke(self, context, event: Event):
        self.extend = event.shift
        self.toggle = event.ctrl
        return self.execute(context)


class MultiSelectAllOperatorMixin:
    bl_options = {"UNDO"}

    def get_collection(self, context) -> MultiSelectCollectionMixin:
        raise NotImplementedError("get_collection")

    def execute(self, context):
        collection = self.get_collection(context)
        collection.select_all()
        return {"FINISHED"}


class MultiSelectProperty:
    pass


def multiselect_access(item_cls: type) -> type:
    def _wrap_basic_property(prop_fn, attr_name: str, **kwargs):
        def _getter(self: MultiSelectAccessMixin):
            return getattr(self.active_item, attr_name)

        def _setter(self: MultiSelectAccessMixin, value):
            for item in self.iter_selected_items():
                setattr(item, attr_name, value)

        return prop_fn(**kwargs, get=_getter, set=_setter)

    def _wrap_enum_property(attr_name: str, **kwargs):
        def _getter(self: MultiSelectAccessMixin) -> int:
            enum_str = getattr(self.active_item, attr_name)
            enum_int = self.rna_type.properties[attr_name].enum_items[enum_str].value
            return enum_int

        def _setter(self: MultiSelectAccessMixin, value: int):
            for item in self.iter_selected_items():
                item[attr_name] = value

        return EnumProperty(**kwargs, get=_getter, set=_setter)

    def _decorator(cls: type) -> type:
        assert issubclass(cls, MultiSelectAccessMixin), \
            f"multiselect_access: Class '{cls}' must inherit 'MultiSelectAccessMixin'"
        for name, annotation in cls.__annotations__.items():
            if isinstance(annotation, MultiSelectProperty):
                src_annotation = item_cls.__annotations__.get(name, None)
                assert src_annotation is not None, f"multiselect_access: No property '{name}' found in '{item_cls}'"

                fn = src_annotation.function
                kwargs = dict(src_annotation.keywords)
                if fn is EnumProperty:
                    wrapper_prop = _wrap_enum_property(name, **kwargs)
                elif fn in {IntProperty, FloatProperty, StringProperty}:
                    wrapper_prop = _wrap_basic_property(fn, name, **kwargs)
                else:
                    assert False, f"multiselect_access: Cannot wrap '{src_annotation.function.__name__}'"

                cls.__annotations__[name] = wrapper_prop

        return cls

    return _decorator


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

        selection_indices = collection.selection_indices
        is_selected = len(selection_indices) > 1 and any(i.index == index for i in selection_indices)
        is_active = index == collection.active_index
        layout.active = len(selection_indices) <= 1 or is_selected

        if is_active:
            if self.name_editable:
                layout.prop(item, self.name_prop, text="", emboss=False, icon=icon_str, icon_value=icon_value)
            else:
                layout.label(text=getattr(item, self.name_prop), icon=icon_str, icon_value=icon_value)
        else:
            def _set_op_properties(op):
                op.index = index
                op.apply_filter = True
                op.filter_name = self.filter_name
                op.bitflag_filter_item = self.bitflag_filter_item
                op.use_filter_sort_reverse = self.use_filter_sort_reverse
                op.use_filter_sort_alpha = self.use_filter_sort_alpha
                op.use_filter_invert = self.use_filter_invert

            # hacky way to left-align operator button text by having two buttons
            row = layout.row(align=True)
            subrow = row.row(align=True)
            subrow.alignment = "LEFT"
            op = subrow.operator(
                self.multiselect_operator,
                text=getattr(item, self.name_prop),
                icon=icon_str, icon_value=icon_value,
                emboss=is_selected or is_active,
            )
            _set_op_properties(op)
            subrow = row.row(align=True)
            op = subrow.operator(
                self.multiselect_operator,
                text="",
                emboss=is_selected or is_active,
            )
            _set_op_properties(op)

    def get_item_icon(self, item) -> str | int:
        return self.default_item_icon


# This tries to mimic the default UIList filtering behaviour, because we need to know the filtered items in the
# multiselect operator. For now, assume that multiselectcollections UILists don't implement custom filtering.
# If that is ever needed, we need to provide some customization point here.
def _default_filter_items(
    collection: MultiSelectCollectionMixin,
    filter_name: str,
    bitflag_filter_item: int,
    use_filter_sort_reverse: bool,
    use_filter_sort_alpha: bool,
):
    flt_flags = []
    flt_neworder = []

    if filter_name:
        flt_flags = UI_UL_list.filter_items_by_name(
            filter_name, bitflag_filter_item, collection.get_collection_property(), "name"
        )

    if use_filter_sort_alpha and not use_filter_sort_reverse:
        flt_neworder = UI_UL_list.sort_items_by_name(collection.get_collection_property(), "name")

    return flt_flags, flt_neworder
