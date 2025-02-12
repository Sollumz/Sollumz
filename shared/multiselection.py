"""
Module with shared logic to support multi-selection in Blender PropertyGroups.
"""

import bpy
from bpy.types import (
    ID,
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
    FloatVectorProperty,
)
import typing
from typing import Optional, NamedTuple, Generic, TypeVar
from collections.abc import Iterator, Sequence
from enum import Enum, auto
import numpy as np

_BITFLAG_FILTER_ITEM = (1 << 30)  # same as UIList.bitflag_filter_item


class SelectionIndex(PropertyGroup):
    index: IntProperty(name="Index")


class SelectMode(Enum):
    SET = auto()
    EXTEND = auto()
    TOGGLE = auto()


class MultiSelectAccessMixin:
    _collection_name = None
    _path_split_str = None
    _nested_access_types = None

    def find_owner(self) -> PropertyGroup:
        id_data = self.id_data
        path = self.path_from_id()
        owner_path, _ = path.split(self._path_split_str)
        owner = id_data.path_resolve(owner_path)
        return owner

    def find_owner_collection(self) -> 'MultiSelectCollection':
        return getattr(self.find_owner(), self._collection_name)

    @property
    def active_item(self) -> bpy_struct:
        return self.find_owner_collection().active_item

    def iter_selected_items(self) -> Iterator[bpy_struct]:
        return self.find_owner_collection().iter_selected_items()

    @property
    def selected_items(self) -> list[bpy_struct]:
        return self.find_owner_collection().selected_items


class MultiSelectNestedAccessMixin(MultiSelectAccessMixin):
    _nested_path = None

    def _resolve_nested(self, active_item_root: bpy_struct) -> bpy_struct:
        return active_item_root.path_resolve(self._nested_path)

    @property
    def active_item(self) -> bpy_struct:
        return self._resolve_nested(self.find_owner_collection().active_item)

    def iter_selected_items(self) -> Iterator[bpy_struct]:
        yield from (self._resolve_nested(item) for item in self.find_owner_collection().iter_selected_items())

    @property
    def selected_items(self) -> list[bpy_struct]:
        return [self._resolve_nested(item) for item in self.find_owner_collection().selected_items]


def define_multiselect_collection(name: str, collection_kwargs: dict):
    def _decorator(cls: type) -> type:
        assert name in cls.__annotations__ and typing.get_origin(cls.__annotations__[name]) is MultiSelectCollection, \
            f"'{cls.__name__}' is missing '{name}: MultiSelectCollection[TItem, TItemAccess]' annotation."

        item_cls, item_access_cls = typing.get_args(cls.__annotations__[name])

        assert issubclass(item_cls, PropertyGroup), \
            f"{item_cls.__name__} must be a PropertyGroup"
        assert issubclass(item_access_cls, MultiSelectAccessMixin), \
            f"{item_access_cls.__name__} must implement MultiSelectAccessMixin"

        collection_propname = f"{name}_"
        active_index_propname = f"{name}_active_index_"
        active_index_for_ui_propname = f"{name}_active_index_for_ui_"
        selection_indices_propname = f"{name}_selection_indices_"
        selection_propname = f"{name}_selection_"
        on_active_index_update_from_ui_callback_name = f"on_{name}_active_index_update_from_ui"
        cls.__annotations__[collection_propname] = CollectionProperty(type=item_cls, **collection_kwargs)
        cls.__annotations__[active_index_propname] = IntProperty(name="Active Index")
        cls.__annotations__[active_index_for_ui_propname] = IntProperty(
            name="Active Index",
            get=lambda s: getattr(s, active_index_propname),
            set=lambda s, v: _collection_getter(s)._on_active_index_update_from_ui(v),
        )
        cls.__annotations__[selection_indices_propname] = CollectionProperty(type=SelectionIndex)
        cls.__annotations__[selection_propname] = PointerProperty(type=item_access_cls)
        item_access_cls._path_split_str = f".{selection_propname}"
        item_access_cls._collection_name = name
        if item_access_cls._nested_access_types:
            for nested_access_cls, nested_propname in item_access_cls._nested_access_types:
                assert nested_access_cls._path_split_str is None, \
                    f"Nested access class {nested_access_cls.__name__} already used"
                assert issubclass(nested_access_cls, MultiSelectNestedAccessMixin)
                nested_access_cls._nested_path = f"{nested_propname}"
                nested_access_cls._path_split_str = f".{selection_propname}.{nested_propname}"
                nested_access_cls._collection_name = item_access_cls._collection_name

            del item_access_cls._nested_access_types

        def _collection_getter(self) -> MultiSelectCollection[item_cls, item_access_cls]:
            return MultiSelectCollection(self, collection_propname, active_index_propname, active_index_for_ui_propname, on_active_index_update_from_ui_callback_name, selection_indices_propname, selection_propname)
        setattr(cls, name, property(_collection_getter))
        return cls

    return _decorator


TItem = TypeVar("TItem", bound=PropertyGroup)
TItemAccess = TypeVar("TItemAccess", bound=MultiSelectAccessMixin)


class MultiSelectCollection(Generic[TItem, TItemAccess]):
    def __init__(self, owner: PropertyGroup, collection_propname: str, active_index_propname: str, active_index_for_ui_propname: str, on_active_index_update_from_ui_callback_name: str, selection_indices_propname: str, selection_propname: str):
        self._owner = owner
        self._collection_propname = collection_propname
        self._active_index_propname = active_index_propname
        self._active_index_for_ui_propname = active_index_for_ui_propname
        self._on_active_index_update_from_ui_callback_name = on_active_index_update_from_ui_callback_name
        self._selection_indices_propname = selection_indices_propname
        self._selection_propname = selection_propname

    @property
    def collection(self) -> bpy_prop_collection:
        return getattr(self._owner, self._collection_propname)

    @property
    def active_index(self) -> int:
        return getattr(self._owner, self._active_index_propname)

    @active_index.setter
    def active_index(self, index: int) -> int:
        setattr(self._owner, self._active_index_propname, index)

    @property
    def selection_indices(self) -> bpy_prop_collection:
        return getattr(self._owner, self._selection_indices_propname)

    @property
    def selection(self) -> TItemAccess:
        return getattr(self._owner, self._selection_propname)

    def add(self) -> TItem:
        return self.collection.add()

    def remove(self, index: int):
        self.collection.remove(index)

    def _on_active_index_update_from_ui(self, value):
        # This callback is only triggered when clicking on the active item in the list once it switched to a textfield
        # instead of buttons
        # Use select() instead of setting active_index to deselected the other items when clicking again on the active
        # item
        self.select(value, ui_callbacks=True)

    def on_active_index_update_from_ui(self, context):
        if cb := getattr(self._owner, self._on_active_index_update_from_ui_callback_name, None):
            cb(context)

    def __len__(self) -> int:
        return len(self.collection)

    def __getitem__(self, index: int) -> TItem:
        return self.collection[index]

    @property
    def has_multiple_selection(self) -> bool:
        return len(self.selection_indices) > 1

    @property
    def active_item(self) -> TItem:
        return self[self.active_index]

    def iter_selected_items_indices(self) -> Iterator[int]:
        found_active_item = False
        active_index = self.active_index
        for s in self.selection_indices:
            if s.index == active_index:
                found_active_item = True
            yield s.index

        if not found_active_item:
            # in some edge-cases cases where the active item may not appear in the selection list
            yield active_index

    def iter_selected_items(self) -> Iterator[TItem]:
        found_active_item = False
        active_index = self.active_index
        for s in self.selection_indices:
            item = self[s.index]
            if item is not None:
                if s.index == active_index:
                    found_active_item = True
                yield item

        if not found_active_item:
            # in some edge-cases cases where the active item may not appear in the selection list
            yield self.active_item

    @property
    def selected_items_indices(self) -> list[int]:
        return list(self.iter_selected_items_indices())

    @property
    def selected_items(self) -> list[TItem]:
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
                    assert len(reorder_items) == len(self)
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
                    assert len(filtered_items) == len(self)

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

    def select_all(self, filtered_items: Optional[Sequence[bool]] = None):
        if filtered_items:
            assert len(filtered_items) == len(self)

        self.selection_indices.clear()
        for i in range(len(self)):
            is_filtered_out = filtered_items and not filtered_items[i]
            if not is_filtered_out:
                self.selection_indices.add().index = i

        is_active_item_filtered_out = filtered_items and not filtered_items[self.active_index]
        if is_active_item_filtered_out and len(self.selection_indices) > 0:
            self.active_index = self.selection_indices[0].index


class MultiSelectOperatorBase:
    bl_options = {"UNDO"}

    apply_filter: BoolProperty()
    filter_name: StringProperty()
    use_filter_sort_reverse: BoolProperty()
    use_filter_sort_alpha: BoolProperty()
    use_filter_invert: BoolProperty()

    def get_collection(self, context) -> MultiSelectCollection:
        raise NotImplementedError("get_collection")

    def filter_items(self, context) -> tuple[Optional[list[bool]], Optional[list[int]]]:
        filtered_items = None
        reorder_items = None
        if self.apply_filter:
            filter_flags, filter_order = self._filter_items_impl(context)
            if filter_order:
                reorder_items = filter_order
            if filter_flags:
                filtered_items = (np.array(filter_flags) & _BITFLAG_FILTER_ITEM) != 0
                if self.use_filter_invert:
                    filtered_items = np.logical_not(filtered_items)
                filtered_items = list(filtered_items)

        return filtered_items, reorder_items

    def _filter_items_impl(self, context) -> tuple[list[int], list[int]]:
        return _default_filter_items(
            self.get_collection(context),
            self.filter_name,
            self.use_filter_sort_reverse,
            self.use_filter_sort_alpha
        )


class MultiSelectOneOperator(MultiSelectOperatorBase):
    bl_description = "Select item"

    index: IntProperty(name="Index")
    extend: BoolProperty(name="Extend")
    toggle: BoolProperty(name="Toggle")

    trigger_ui_callbacks: BoolProperty(default=True)

    def execute(self, context):
        collection = self.get_collection(context)
        filtered_items, reorder_items = self.filter_items(context)
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


class MultiSelectAllOperator(MultiSelectOperatorBase):
    bl_description = "Select all items"

    def execute(self, context):
        collection = self.get_collection(context)
        filtered_items, _ = self.filter_items(context)
        collection.select_all(filtered_items=filtered_items)
        return {"FINISHED"}


class MultiSelectProperty:
    pass


class MultiSelectPointerProperty(MultiSelectProperty):
    def __init__(self, pointer_type: type):
        self.pointer_type = pointer_type


def define_multiselect_access(item_cls: type) -> type:
    def _wrap_basic_property(prop_fn, attr_name: str, **kwargs):
        def _getter(self: MultiSelectAccessMixin):
            return getattr(self.active_item, attr_name)

        def _setter(self: MultiSelectAccessMixin, value):
            for item in self.iter_selected_items():
                setattr(item, attr_name, value)

        return prop_fn(**kwargs, get=_getter, set=_setter)

    def _wrap_enum_property(attr_name: str, **kwargs):
        assert "ENUM_FLAG" not in kwargs.get("options", ()), \
            "Flag enum properties not supported. Cannot wrap '{attr_name}'"

        if (items := kwargs.get("items", None)) and callable(items):
            dynamic_items_callback = items
        else:
            dynamic_items_callback = None

        # Enum getters need to return the int value, but reading the properties gives the
        # string name. So we need to lookup the value for the name.
        def _getter(self: MultiSelectAccessMixin) -> int:
            active = self.active_item
            enum_str = getattr(active, attr_name)
            enum_int = active.rna_type.properties[attr_name].enum_items[enum_str].value
            return enum_int

        def _setter(self: MultiSelectAccessMixin, value: int):
            # Need to convert the int value to the corresponding enum name string.
            # We need to use setattr which only accepts the string form. We cannot use dictionary-like access
            # (i.e. `item[attr_name] = value`) because it doesn't trigger the update callback if the property has one.
            enum_items = self.active_item.rna_type.properties[attr_name].enum_items
            for enum_item in enum_items:
                if enum_item.value == value:
                    enum_str = enum_item.identifier
                    break
            else:
                enum_str = enum_items[0].identifier

            for item in self.iter_selected_items():
                setattr(item, attr_name, enum_str)

        def _getter_dynamic(self: MultiSelectAccessMixin) -> int:
            # EnumProperty.enum_items is empty with dynamic enum items, we need to call
            # the callback and search for the correct enum manually.
            # See https://projects.blender.org/blender/blender/issues/86803
            active = self.active_item
            enum_str = getattr(active, attr_name)
            enum_items = dynamic_items_callback(active, bpy.context)
            for i, enum_item in enumerate(enum_items):
                if enum_item[0] == enum_str:
                    n = len(enum_item)
                    if n == 3:
                        return i
                    else:
                        return enum_item[-1]

            return 0  # TODO(multiselect): should this be some other default?

        def _setter_dynamic(self: MultiSelectAccessMixin, value: int):
            # Need to convert the int value to the corresponding enum name string.
            # We need to use setattr which only accepts the string form. We cannot use dictionary-like access
            # (i.e. `item[attr_name] = value`) because it doesn't trigger the update callback if the property has one.
            enum_items = dynamic_items_callback(self.active_item, bpy.context)
            for i, enum_item in enumerate(enum_items):
                n = len(enum_item)
                if (n == 3 and i == value) or (n != 3 and enum_item[-1] == value):
                    enum_str = enum_item[0]
                    break
            else:
                enum_str = enum_items[0][0]

            for item in self.iter_selected_items():
                setattr(item, attr_name, enum_str)

        def _dynamic_items_wrapper(self: MultiSelectAccessMixin, context: Optional[bpy.types.Context]) -> list:
            # Wrapper required to pass the active item to the enum items callback
            # Otherwise the callback is invoked with the MultiSelectAccessMixin as self
            active = self.active_item
            return dynamic_items_callback(active, context)

        if dynamic_items_callback:
            kwargs["items"] = _dynamic_items_wrapper

        return EnumProperty(
            **kwargs,
            get=_getter_dynamic if dynamic_items_callback else _getter,
            set=_setter_dynamic if dynamic_items_callback else _setter,
        )

    def _decorator(cls: type) -> type:
        assert issubclass(cls, MultiSelectAccessMixin), \
            f"'{cls.__name__}' must inherit 'MultiSelectAccessMixin'"
        item_cls_annotations = _get_all_annotations(item_cls)
        for name, annotation in cls.__annotations__.items():
            if isinstance(annotation, MultiSelectProperty):
                src_annotation = item_cls_annotations.get(name, None)
                assert (
                    src_annotation is not None and
                    hasattr(src_annotation, "function") and
                    hasattr(src_annotation, "keywords")
                ), f"No property '{name}' found in '{item_cls.__name__}'"

                fn = src_annotation.function
                kwargs = dict(src_annotation.keywords)

                # Do not copy the callbacks to the wrapper property
                for callback in ("get", "set", "update"):
                    if callback in kwargs:
                        del kwargs[callback]

                if fn is EnumProperty:
                    wrapper_prop = _wrap_enum_property(name, **kwargs)
                elif fn in {BoolProperty, IntProperty, FloatProperty, StringProperty, FloatVectorProperty}:
                    wrapper_prop = _wrap_basic_property(fn, name, **kwargs)
                elif fn in {PointerProperty}:
                    assert not issubclass(kwargs["type"], ID), \
                        f"Cannot wrap 'PointerProperty' of '{kwargs['type'].__name__}' type"
                    assert isinstance(annotation, MultiSelectPointerProperty), \
                        "Must annotate with 'MultiSelectPointerProperty' to wrap 'PointerProperty'"
                    assert issubclass(annotation.pointer_type, MultiSelectNestedAccessMixin), \
                        f"Nested selection access class '{annotation.pointer_type.__name__}' must inherit 'MultiSelectNestedAccessMixin'"

                    del kwargs["type"]
                    wrapper_prop = PointerProperty(**kwargs, type=annotation.pointer_type)
                    if cls._nested_access_types is None:
                        cls._nested_access_types = []
                    cls._nested_access_types.append((annotation.pointer_type, name))
                else:
                    assert False, f"Cannot wrap '{src_annotation.function.__name__}'"

                cls.__annotations__[name] = wrapper_prop

        return cls

    return _decorator


class MultiSelectFilterOptions(NamedTuple):
    filter_name: str
    use_filter_sort_reverse: bool
    use_filter_sort_alpha: bool
    use_filter_invert: bool

    def apply_to_operator(self, op):
        op.apply_filter = True
        op.filter_name = self.filter_name
        op.use_filter_sort_reverse = self.use_filter_sort_reverse
        op.use_filter_sort_alpha = self.use_filter_sort_alpha
        op.use_filter_invert = self.use_filter_invert


class MultiSelectUIListMixin:
    name_prop: str = "name"
    default_item_icon: str = "NONE"
    name_editable: bool = True
    multiselect_operator: str = ""
    last_filter_options: dict[str, MultiSelectFilterOptions] = {}

    def draw_item(
        self, context, layout: UILayout, data, item, icon, active_data, active_propname, index
    ):
        multiselect_collection_name = active_propname[:-21]  # remove '_active_index_for_ui_' suffix

        filter_opts = MultiSelectFilterOptions(
            self.filter_name,
            self.use_filter_sort_reverse,
            self.use_filter_sort_alpha,
            self.use_filter_invert,
        )
        self_cls = type(self)
        if f"{multiselect_collection_name}_{self.list_id}" not in self_cls.last_filter_options:
            self_cls.last_filter_options[f"{multiselect_collection_name}_{self.list_id}"] = filter_opts

        collection: MultiSelectCollection = getattr(data, multiselect_collection_name)
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
                filter_opts.apply_to_operator(op)

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
    collection: MultiSelectCollection,
    filter_name: str,
    use_filter_sort_reverse: bool,
    use_filter_sort_alpha: bool,
    name_prop: str = "name"
) -> tuple[list[int], list[int]]:
    flt_flags = []
    flt_neworder = []

    if filter_name:
        flt_flags = UI_UL_list.filter_items_by_name(
            filter_name, _BITFLAG_FILTER_ITEM, collection.collection, name_prop
        )

    if use_filter_sort_alpha and not use_filter_sort_reverse:
        flt_neworder = UI_UL_list.sort_items_by_name(collection.collection, name_prop)

    return flt_flags, flt_neworder


def multiselect_ui_draw_list(
    layout: UILayout,
    collection: MultiSelectCollection,
    add_operator: str,
    remove_operator: str,
    uilist_cls: type,
    context_menu_cls: type,
    list_id: str
) -> tuple[UILayout, UILayout]:
    from ..sollumz_ui import draw_list_with_add_remove
    full_list_id = f"{collection._collection_propname}{list_id}"
    if full_list_id in uilist_cls.last_filter_options:
        del uilist_cls.last_filter_options[full_list_id]

    owner = collection._owner

    list_col, side_col = draw_list_with_add_remove(
        layout,
        add_operator, remove_operator,
        uilist_cls.bl_idname, list_id,
        owner, collection._collection_propname,
        owner, collection._active_index_for_ui_propname,
        rows=3
    )

    side_col.separator()
    side_col.menu(context_menu_cls.bl_idname, icon="DOWNARROW_HLT", text="")

    return list_col, side_col


def _get_all_annotations(cls):
    """Gets the annotations of the class and all inherited annotations."""
    import inspect
    annotations = {}
    # Reversed MRO iteration so annotations in child classes override parent class
    for base in reversed(inspect.getmro(cls)):
        if hasattr(base, "__annotations__"):
            annotations.update(base.__annotations__)
    return annotations


class MultiSelectUIFlagsPanel:
    bl_label = "Flags"
    bl_options = {"DEFAULT_CLOSED"}

    def get_flags_active(self, context) -> bpy_struct:
        raise NotImplementedError(
            f"Failed to display flags. '{self.__class__.__name__}.get_flags_active()' method not defined.")

    def get_flags_selection(self, context) -> MultiSelectAccessMixin:
        raise NotImplementedError(
            f"Failed to display flags. '{self.__class__.__name__}.get_flags_selection()' method not defined.")

    def draw(self, context):
        active = self.get_flags_active(context)
        selection = self.get_flags_selection(context)
        self.layout.prop(selection, "total")
        self.layout.separator()
        grid = self.layout.grid_flow(columns=2)
        for index, prop_name in enumerate(active.get_flag_names()):
            if index > active.size - 1:
                break
            grid.prop(selection, prop_name)


class MultiSelectUITimeFlagsPanel(MultiSelectUIFlagsPanel):
    bl_label = "Time Flags"
    select_operator = None
    clear_operator = None

    def draw(self, context):
        super().draw(context)
        if self.select_operator is None or self.clear_operator is None:
            raise NotImplementedError(
                f"'select_operator' and 'clear_operator' bl_idnames must be defined for {self.__class__.__name__}!")
        flags = self.get_flags(context)
        row = self.layout.row()
        row.operator(self.select_operator)
        row.prop(flags, "time_flags_start", text="from")
        row.prop(flags, "time_flags_end", text="to")
        row = self.layout.row()
        row.operator(self.clear_operator)
