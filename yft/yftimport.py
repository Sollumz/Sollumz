import bpy
from mathutils import Matrix, Vector
from ..resources.fragment import YFT
from ..ydr.ydrimport import drawable_to_obj, shadergroup_to_materials
from ..ybn.ybnimport import composite_to_obj
from ..sollumz_properties import SOLLUMZ_UI_NAMES, SollumType
from ..tools.blenderhelper import copy_object


def create_lod_obj(name, lod, filepath, materials):
    lobj = bpy.data.objects.new(name, None)
    lobj.empty_display_size = 0
    lobj.sollum_type = SollumType.LOD
    bpy.context.collection.objects.link(lobj)

    lobj.lod_properties.unk_14 = lod.unknown_14
    lobj.lod_properties.unk_18 = lod.unknown_18
    lobj.lod_properties.unk_1c = lod.unknown_1c
    lobj.lod_properties.unk_30 = lod.unknown_30
    lobj.lod_properties.unk_40 = lod.unknown_40
    lobj.lod_properties.unk_50 = lod.unknown_50
    lobj.lod_properties.unk_60 = lod.unknown_60
    lobj.lod_properties.unk_70 = lod.unknown_70
    lobj.lod_properties.unk_80 = lod.unknown_80
    lobj.lod_properties.unk_90 = lod.unknown_90
    lobj.lod_properties.unk_a0 = lod.unknown_a0
    lobj.lod_properties.unk_b0 = lod.unknown_b0

    for group in lod.groups:
        bgroup = lobj.frag_group_properties.add()
        bgroup.name = group.name
        bgroup.index = group.index
        bgroup.parent_index = group.parent_index
        bgroup.unk_byte_4c = group.unk_byte_4c
        bgroup.unk_byte_4f = group.unk_byte_4f
        bgroup.unk_byte_50 = group.unk_byte_50
        bgroup.unk_byte_51 = group.unk_byte_51
        bgroup.unk_byte_52 = group.unk_byte_52
        bgroup.unk_byte_53 = group.unk_byte_53
        bgroup.unk_float_10 = group.unk_float_10
        bgroup.unk_float_14 = group.unk_float_14
        bgroup.unk_float_18 = group.unk_float_18
        bgroup.unk_float_1c = group.unk_float_1c
        bgroup.unk_float_20 = group.unk_float_20
        bgroup.unk_float_24 = group.unk_float_24
        bgroup.unk_float_28 = group.unk_float_28
        bgroup.unk_float_2c = group.unk_float_2c
        bgroup.unk_float_30 = group.unk_float_30
        bgroup.unk_float_34 = group.unk_float_34
        bgroup.unk_float_38 = group.unk_float_38
        bgroup.unk_float_3c = group.unk_float_3c
        bgroup.unk_float_40 = group.unk_float_40
        bgroup.mass = group.mass
        bgroup.unk_float_54 = group.unk_float_54
        bgroup.unk_float_58 = group.unk_float_58
        bgroup.unk_float_5c = group.unk_float_5c
        bgroup.unk_float_60 = group.unk_float_60
        bgroup.unk_float_64 = group.unk_float_64
        bgroup.unk_float_68 = group.unk_float_68
        bgroup.unk_float_6c = group.unk_float_6c
        bgroup.unk_float_70 = group.unk_float_70
        bgroup.unk_float_74 = group.unk_float_74
        bgroup.unk_float_78 = group.unk_float_78
        bgroup.unk_float_a8 = group.unk_float_a8

    aobj = bpy.data.objects.new("Archetype", None)
    aobj.empty_display_size = 0
    aobj.sollum_type = SollumType.ARCHETYPE
    bpy.context.collection.objects.link(aobj)
    aobj.parent = lobj

    aobj.archetype_properties.name = lod.archetype.name
    aobj.archetype_properties.mass = lod.archetype.mass
    aobj.archetype_properties.mass_inv = lod.archetype.mass_inv
    aobj.archetype_properties.unknown_48 = lod.archetype.unknown_48
    aobj.archetype_properties.unknown_4c = lod.archetype.unknown_4c
    aobj.archetype_properties.unknown_50 = lod.archetype.unknown_50
    aobj.archetype_properties.unknown_54 = lod.archetype.unknown_54
    aobj.archetype_properties.inertia_tensor = lod.archetype.inertia_tensor
    aobj.archetype_properties.intertia_tensor_inv = lod.archetype.intertia_tensor_inv

    if lod.archetype.bounds:
        bobj = composite_to_obj(lod.archetype.bounds,
                                SOLLUMZ_UI_NAMES[SollumType.BOUND_COMPOSITE], True)
        bobj.parent = aobj

    wheel_drawable = None
    cobjs = []

    if lod.children:
        cwobj = bpy.data.objects.new("Children", None)
        cwobj.empty_display_size = 0
        bpy.context.collection.objects.link(cwobj)

        for idx, child in enumerate(lod.children):
            cobj = bpy.data.objects.new(f"Child{idx}", None)
            cobj.empty_display_size = 0
            cobj.sollum_type = SollumType.CHILD
            bpy.context.collection.objects.link(cobj)

            cobj.child_properties.group_index = child.group_index
            cobj.child_properties.bone_tag = child.bone_tag
            cobj.child_properties.mass_1 = child.mass_1
            cobj.child_properties.mass_2 = child.mass_2
            cobj.child_properties.unk_vec = child.unk_vec
            cobj.child_properties.inertia_tensor = child.inertia_tensor

            if len(child.drawable.drawable_models_high) > 0:
                dobj = drawable_to_obj(
                    child.drawable, filepath, f"child {idx}", None, materials)
                dobj.parent = cobj

                # set wheel drawable to instantiate
                group = lod.groups[child.group_index]
                if group.name == "wheel_lf":
                    wheel_drawable = dobj

            transform = lod.transforms[idx].value
            a = transform[3][0] + lod.unknown_30.x
            b = transform[3][1] + lod.unknown_30.y
            c = transform[3][2] + lod.unknown_30.z
            transform[3][0] = a
            transform[3][1] = b
            transform[3][2] = c
            cobj.matrix_basis = transform.transposed()

            cobjs.append(cobj)
            cobj.parent = cwobj

        cwobj.parent = lobj

        # instantiate wheels
        for idx, child in enumerate(lod.children):
            group = lod.groups[child.group_index]
            if group.name in ("wheel_rf", "wheel_rr"):
                wheel = copy_object(wheel_drawable, True)
                # rotate 90 degrees for right wheels
                wheel.rotation_euler[2] = 3.14159
                wheel.parent = cobjs[idx]
            elif group.name == "wheel_lr":
                wheel = copy_object(wheel_drawable, True)
                wheel.parent = cobjs[idx]

    return lobj


def fragment_to_obj(fragment, filepath):
    fobj = bpy.data.objects.new(fragment.name, None)
    fobj.empty_display_size = 0
    fobj.sollum_type = SollumType.FRAGMENT
    bpy.context.collection.objects.link(fobj)

    fobj.fragment_properties.unk_b0 = fragment.unknown_b0
    fobj.fragment_properties.unk_b8 = fragment.unknown_b8
    fobj.fragment_properties.unk_bc = fragment.unknown_bc
    fobj.fragment_properties.unk_c0 = fragment.unknown_c0
    fobj.fragment_properties.unk_c4 = fragment.unknown_c4
    fobj.fragment_properties.unk_cc = fragment.unknown_cc
    fobj.fragment_properties.unk_d0 = fragment.unknown_d0
    fobj.fragment_properties.unk_d4 = fragment.unknown_d4

    materials = None
    if fragment.drawable:
        materials = shadergroup_to_materials(
            fragment.drawable.shader_group, filepath)
        dobj = drawable_to_obj(
            fragment.drawable, filepath, fragment.fixed_name(), None, materials)
        dobj.parent = fobj

    if len(fragment.physics.lod1.groups) > 0:
        lobj = create_lod_obj("LOD1", fragment.physics.lod1,
                              filepath, materials)
        lobj.parent = fobj
    if len(fragment.physics.lod2.groups) > 0:
        lobj = create_lod_obj("LOD2", fragment.physics.lod2,
                              filepath, materials)
        lobj.parent = fobj
    if len(fragment.physics.lod3.groups) > 0:
        lobj = create_lod_obj("LOD3", fragment.physics.lod3,
                              filepath, materials)
        lobj.parent = fobj

    allbmodels = []
    for child in dobj.children:
        allbmodels.append(child)
    allfmodels = fragment.drawable.all_models

    pose = fragment.bones_transforms
    if pose:
        modeltransforms = []
        pbc = len(pose)
        for i in range(pbc):
            modeltransforms.append(pose[i].value)

    for i in range(len(allfmodels)):
        model = allfmodels[i]
        bmodel = allbmodels[i]

        boneidx = model.bone_index
        m = modeltransforms[boneidx] if boneidx < len(
            modeltransforms) else Matrix()

        if not model.has_skin:
            bmodel.matrix_basis = m


def import_yft(filepath):
    yft_xml = YFT.from_xml_file(filepath)
    fragment_to_obj(yft_xml, filepath)
