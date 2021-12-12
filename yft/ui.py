import bpy


def draw_child_properties(layout, obj):
    layout.prop(obj.child_properties, "bone_tag")
    layout.prop(obj.child_properties, "mass_1")
    layout.prop(obj.child_properties, "mass_2")
    layout.prop(obj.child_properties, "unk_vec")
    layout.prop(obj.child_properties, "inertia_tensor")


def draw_group_properties(layout, obj):
    for prop in obj.group_properties.__annotations__:
        layout.prop(obj.group_properties, prop)


def draw_archetype_properties(layout, obj):
    layout.label(text="Archetype Properties")
    layout.prop(obj.lod_properties, "name")
    layout.prop(obj.lod_properties, "mass")
    layout.prop(obj.lod_properties, "mass_inv")
    layout.prop(obj.lod_properties, "unknown_48")
    layout.prop(obj.lod_properties, "unknown_4c")
    layout.prop(obj.lod_properties, "unknown_50")
    layout.prop(obj.lod_properties, "unknown_54")
    layout.prop(obj.lod_properties, "inertia_tensor")
    layout.prop(obj.lod_properties, "inertia_tensor_inv")
    layout.prop(obj.lod_properties, "bound")


def draw_lod_properties(layout, obj):
    layout.prop(obj.lod_properties, "unk_14")
    layout.prop(obj.lod_properties, "unk_18")
    layout.prop(obj.lod_properties, "unk_1c")
    layout.prop(obj.lod_properties, "unk_30")
    layout.prop(obj.lod_properties, "unk_50")
    layout.prop(obj.lod_properties, "unk_60")
    layout.prop(obj.lod_properties, "unk_70")
    layout.prop(obj.lod_properties, "unk_80")
    layout.prop(obj.lod_properties, "unk_90")
    layout.prop(obj.lod_properties, "unk_a0")
    layout.prop(obj.lod_properties, "unk_b0")
    draw_archetype_properties(layout, obj)


def draw_fragment_properties(layout, obj):
    layout.prop(obj.fragment_properties, "unk_b0")
    layout.prop(obj.fragment_properties, "unk_b8")
    layout.prop(obj.fragment_properties, "unk_bc")
    layout.prop(obj.fragment_properties, "unk_c0")
    layout.prop(obj.fragment_properties, "unk_c4")
    layout.prop(obj.fragment_properties, "unk_cc")
    layout.prop(obj.fragment_properties, "unk_d0")
    layout.prop(obj.fragment_properties, "unk_d4")
