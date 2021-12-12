def draw_child_properties(layout, obj):
    for prop in obj.child_properties.__annotations__:
        layout.prop(obj.child_properties, prop)


def draw_group_properties(layout, obj):
    layout.prop(obj, "name")
    for prop in obj.group_properties.__annotations__:
        layout.prop(obj.group_properties, prop)


def draw_archetype_properties(layout, obj):
    layout.label(text="Archetype Properties")
    for prop in obj.lod_properties.__annotations__:
        layout.prop(obj.lod_properties, prop)


def draw_lod_properties(layout, obj):
    for prop in obj.lod_properties.__annotations__:
        layout.prop(obj.lod_properties, prop)
    draw_archetype_properties(layout, obj)


def draw_fragment_properties(layout, obj):
    for prop in obj.fragment_properties.__annotations__:
        layout.prop(obj.fragment_properties, prop)
