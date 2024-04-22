import bpy
import typing
import inspect
import pkgutil
import importlib
from pathlib import Path

__all__ = (
    "init",
    "register",
    "unregister",
)

modules = None
ordered_classes = None


def init():
    global modules
    global ordered_classes

    modules = get_all_submodules(Path(__file__).parent)
    ordered_classes = get_ordered_classes_to_register(modules)


def register():
    for cls in ordered_classes:
        bpy.utils.register_class(cls)

    for module in modules:
        if module.__name__ == __name__:
            continue
        if hasattr(module, "register"):
            module.register()


def unregister():
    called = set()
    for module in modules:
        if module.__name__ == __name__:
            continue
        if hasattr(module, "unregister"):
            # Check if unregister method has already been called
            if module.unregister not in called:
                module.unregister()
                called.add(module.unregister)

    for cls in reversed(ordered_classes):
        bpy.utils.unregister_class(cls)


# Import modules
#################################################

def get_all_submodules(directory):
    return list(iter_submodules(directory, directory.name))


def iter_submodules(path, package_name):
    for name in sorted(iter_submodule_names(path)):
        yield importlib.import_module("." + name, package_name)


def iter_submodule_names(path, root=""):
    for _, module_name, is_package in pkgutil.iter_modules([str(path)]):
        yield root + module_name
        if is_package:
            if module_name == "tests":
                continue  # avoid importing `tests/` directory
            sub_path = path / module_name
            sub_root = root + module_name + "."
            yield from iter_submodule_names(sub_path, sub_root)


# Find classes to register
#################################################

def get_ordered_classes_to_register(modules):
    return toposort(get_register_deps_dict(modules))


def get_register_deps_dict(modules):
    my_classes = set(iter_my_classes(modules))
    my_classes_by_idname = {cls.bl_idname: cls for cls in my_classes if hasattr(cls, "bl_idname")}

    deps_dict = {}
    for cls in my_classes:
        deps_dict[cls] = set(iter_my_register_deps(cls, my_classes, my_classes_by_idname))
    return deps_dict


def iter_my_register_deps(cls, my_classes, my_classes_by_idname):
    yield from iter_my_deps_from_annotations(cls, my_classes)
    yield from iter_my_deps_from_parent_id(cls, my_classes_by_idname)


def iter_my_deps_from_annotations(cls, my_classes):
    for value in typing.get_type_hints(cls, {}, {}).values():
        dependency = get_dependency_from_annotation(value)
        if dependency is not None:
            if dependency in my_classes:
                yield dependency


def get_dependency_from_annotation(value):
    if isinstance(value, bpy.props._PropertyDeferred):
        return value.keywords.get("type")
    return None


def iter_my_deps_from_parent_id(cls, my_classes_by_idname):
    if bpy.types.Panel in cls.__bases__:
        parent_idname = getattr(cls, "bl_parent_id", None)
        if parent_idname is not None:
            parent_cls = my_classes_by_idname.get(parent_idname)
            if parent_cls is not None:
                yield parent_cls


def iter_my_classes(modules):
    base_types = get_register_base_types()
    for cls in get_classes_in_modules(modules):
        if any(base in base_types for base in cls.__bases__):
            if not getattr(cls, "is_registered", False):
                yield cls


def get_classes_in_modules(modules):
    classes = set()
    for module in modules:
        for cls in iter_classes_in_module(module):
            classes.add(cls)
    return classes


def iter_classes_in_module(module):
    for value in module.__dict__.values():
        if inspect.isclass(value):
            yield value


def get_register_base_types():
    type_names = [
        "Panel", "Operator", "PropertyGroup",
        "Header", "Menu",
        "Node", "NodeSocket", "NodeTree",
        "UIList", "RenderEngine",
        "Gizmo", "GizmoGroup",
    ]
    if bpy.app.version >= (4, 1, 0):
        type_names.append("FileHandler")

    return set(getattr(bpy.types, name) for name in type_names)


# Find order to register to solve dependencies
#################################################

def toposort(deps_dict):
    sorted_list = []
    sorted_values = set()
    while len(deps_dict) > 0:
        unsorted = []
        # source: https://github.com/JacquesLucke/blender_vscode/pull/118/commits/f0c3a636e251a8f24f22af6f1806d338c838bcea#diff-9738ac67607466100291c17470c593209a6ad718a574d0903d9eb2e8b0a33727
        # JoseConseco forgot this code
        # https://devtalk.blender.org/t/batch-registering-multiple-classes-in-blender-2-8/3253/42
        sorted_list_sub = []      # helper for additional sorting by bl_order - in panels
        for value, deps in deps_dict.items():
            if len(deps) == 0:
                sorted_list_sub.append(value)
                sorted_values.add(value)
            else:
                unsorted.append(value)
        deps_dict = {value: deps_dict[value] -
                     sorted_values for value in unsorted}
        sorted_list_sub.sort(key=lambda cls: getattr(cls, 'bl_order', 0))
        sorted_list.extend(sorted_list_sub)
    return sorted_list
