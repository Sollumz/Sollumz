import bpy
from typing import Optional
from ..sollumz_properties import SollumType, BOUND_TYPES
from ..tools.meshhelper import (
    create_box,
    create_sphere,
    create_cylinder,
    create_capsule,
    create_disc,
    create_plane,
)
from ..ybn.properties import load_flag_presets, flag_presets, BoundFlags
from .blenderhelper import create_blender_object, create_empty_object, remove_number_suffix
from mathutils import Vector, Matrix
from math import radians


def create_bound_shape(bound_type: SollumType):
    if bound_type == SollumType.BOUND_BOX:
        return create_bound_box()
    elif bound_type == SollumType.BOUND_SPHERE:
        return create_bound_sphere()
    elif bound_type == SollumType.BOUND_CAPSULE:
        return create_bound_capsule()
    elif bound_type == SollumType.BOUND_CYLINDER:
        return create_bound_cylinder()
    elif bound_type == SollumType.BOUND_DISC:
        return create_bound_disc()
    elif bound_type == SollumType.BOUND_PLANE:
        return create_bound_plane()
    elif bound_type == SollumType.BOUND_POLY_BOX:
        return create_bound_poly_box()
    elif bound_type == SollumType.BOUND_POLY_SPHERE:
        return create_bound_poly_sphere()
    elif bound_type == SollumType.BOUND_POLY_CAPSULE:
        return create_bound_poly_capsule()
    elif bound_type == SollumType.BOUND_POLY_CYLINDER:
        return create_bound_poly_cylinder()
    else:
        assert False, f"Unsupported bound type '{bound_type}'"


def create_bound_box():
    bound_obj = create_blender_object(SollumType.BOUND_BOX)
    create_box(bound_obj.data, 1, Matrix.Identity(3))
    return bound_obj


def create_bound_poly_box():
    bound_obj = create_blender_object(SollumType.BOUND_POLY_BOX)
    create_box(bound_obj.data)
    return bound_obj


def create_bound_sphere():
    bound_obj = create_blender_object(SollumType.BOUND_SPHERE)
    create_sphere(bound_obj.data, radius=1.0)
    return bound_obj


def create_bound_poly_sphere():
    bound_obj = create_blender_object(SollumType.BOUND_POLY_SPHERE)
    create_sphere(bound_obj.data, radius=1.0)
    return bound_obj


def create_bound_capsule():
    bound_obj = create_blender_object(SollumType.BOUND_CAPSULE)
    create_capsule(bound_obj.data, radius=0.5, length=1.0, axis="Y")
    return bound_obj


def create_bound_poly_capsule():
    bound_obj = create_blender_object(SollumType.BOUND_POLY_CAPSULE)
    create_capsule(bound_obj.data, radius=0.5, length=1.0, axis="Z")
    return bound_obj


def create_bound_cylinder():
    bound_obj = create_blender_object(SollumType.BOUND_CYLINDER)
    create_cylinder(bound_obj.data, radius=1.0, length=2.0, axis="Y")
    return bound_obj


def create_bound_poly_cylinder():
    bound_obj = create_blender_object(SollumType.BOUND_POLY_CYLINDER)
    create_cylinder(bound_obj.data, radius=1.0, length=2.0, axis="Z")
    return bound_obj


def create_bound_disc():
    bound_obj = create_blender_object(SollumType.BOUND_DISC)
    create_disc(bound_obj.data, radius=1.0, length=0.04 * 2)
    return bound_obj


def create_bound_plane():
    bound_obj = create_blender_object(SollumType.BOUND_PLANE)
    # matrix to rotate plane so it faces towards +Y, by default faces +Z
    create_plane(bound_obj.data, 2.0, matrix=Matrix.Rotation(radians(90.0), 4, "X"))
    return bound_obj


def convert_objs_to_composites(objs: list[bpy.types.Object], bound_child_type: SollumType, flag_preset_index: Optional[int] = None):
    """Convert each object in ``objs`` to a Bound Composite."""
    for obj in objs:
        convert_obj_to_composite(obj, bound_child_type, flag_preset_index)


def convert_objs_to_single_composite(objs: list[bpy.types.Object], bound_child_type: SollumType, flag_preset_index: Optional[int] = None):
    """Create a single composite from all ``objs``."""
    composite_obj = create_empty_object(SollumType.BOUND_COMPOSITE)
    for obj in objs:
        if bound_child_type == SollumType.BOUND_GEOMETRY:
            convert_obj_to_geometry(obj, flag_preset_index)
            obj.parent = composite_obj
        else:
            bvh_obj = convert_obj_to_bvh(obj, flag_preset_index)
            bvh_obj.parent = composite_obj
            bvh_obj.location = obj.location
            obj.location = Vector()
    return composite_obj


def center_composite_to_children(composite_obj: bpy.types.Object):
    child_objs = [
        child for child in composite_obj.children if child.sollum_type in BOUND_TYPES]

    center = Vector()

    for obj in child_objs:
        center += obj.location

    center /= len(child_objs)

    composite_obj.location = center

    for obj in child_objs:
        obj.location -= center


def convert_obj_to_composite(obj: bpy.types.Object, bound_child_type: SollumType, flag_preset_index: Optional[int] = None):
    composite_obj = create_empty_object(SollumType.BOUND_COMPOSITE)
    composite_obj.location = obj.location
    composite_obj.parent = obj.parent
    name = obj.name

    if bound_child_type == SollumType.BOUND_GEOMETRY:
        convert_obj_to_geometry(obj, flag_preset_index)
        obj.parent = composite_obj
    else:
        bvh_obj = convert_obj_to_bvh(obj, flag_preset_index)
        bvh_obj.parent = composite_obj

    composite_obj.name = name
    obj.location = Vector()

    return composite_obj


def convert_obj_to_geometry(obj: bpy.types.Object, flag_preset_index: Optional[int] = None):
    obj.sollum_type = SollumType.BOUND_GEOMETRY
    obj.name = f"{remove_number_suffix(obj.name)}.bound_geom"

    if flag_preset_index is not None:
        apply_flag_preset(obj, flag_preset_index)


def convert_obj_to_bvh(obj: bpy.types.Object, flag_preset_index: Optional[int] = None):
    obj_name = remove_number_suffix(obj.name)

    bvh_obj = create_empty_object(SollumType.BOUND_GEOMETRYBVH)
    bvh_obj.name = f"{obj_name}.bvh"

    obj.sollum_type = SollumType.BOUND_POLY_TRIANGLE
    obj.name = f"{obj_name}.poly_mesh"
    obj.parent = bvh_obj

    if flag_preset_index is not None:
        apply_flag_preset(bvh_obj, flag_preset_index)

    return bvh_obj


def apply_flag_preset(obj: bpy.types.Object, preset_index: int, reload_presets: bool = True) -> bool:
    if reload_presets:
        load_flag_presets()

    if preset_index < 0 or preset_index >= len(flag_presets.presets):
        return False

    preset = flag_presets.presets[preset_index]

    for flag_name in BoundFlags.__annotations__.keys():
        obj.composite_flags1[flag_name] = flag_name in preset.flags1
        obj.composite_flags2[flag_name] = flag_name in preset.flags2

    return True
