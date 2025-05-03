import os
import bpy
import numpy as np
from traceback import format_exc
from mathutils import Matrix, Vector, Quaternion
from typing import Optional
from .fragment_merger import FragmentMerger
from ..tools.blenderhelper import add_child_of_bone_constraint, create_empty_object, material_from_image, create_blender_object
from ..tools.meshhelper import create_uv_attr
from ..tools.utils import multiply_homogeneous, get_filename
from ..sollumz_properties import BOUND_TYPES, SollumType, MaterialType
from ..sollumz_preferences import get_import_settings
from ..cwxml.fragment import YFT, Fragment, PhysicsLOD, PhysicsGroup, PhysicsChild, Window, Archetype, GlassWindow
from ..cwxml.drawable import Drawable, Bone
from ..ydr.ydrimport import apply_translation_limits, create_armature_obj_from_skel, create_drawable_skel, apply_rotation_limits, create_joint_constraints, create_light_objs, create_drawable_obj, create_drawable_as_asset, shadergroup_to_materials, create_drawable_models
from ..ybn.ybnimport import create_bound_object, create_bound_composite
from .. import logger
from .properties import LODProperties, FragArchetypeProperties, GlassTypes, FragmentTemplateAsset
from ..tools.blenderhelper import get_child_of_bone


def import_yft(filepath: str):
    import_settings = get_import_settings()

    if is_hi_yft_filepath(filepath):
        # User selected a _hi.yft.xml, look for the base .yft.xml file
        non_hi_filepath = make_non_hi_yft_filepath(filepath)
        hi_filepath = filepath

        if not os.path.exists(non_hi_filepath):
            logger.error("Trying to import a _hi.yft.xml without its base .yft.xml! Please, make sure the non-hi "
                         f"{os.path.basename(non_hi_filepath)} is in the same folder as {os.path.basename(hi_filepath)}.")
            return None
    else:
        # User selected the base .yft.xml, optionally look for the _hi.yft.xml
        non_hi_filepath = filepath
        hi_filepath = make_hi_yft_filepath(filepath)
    name = get_filename(non_hi_filepath)
    yft_xml = YFT.from_xml_file(non_hi_filepath)

    # Import the _hi.yft.xml if it exists
    hi_xml = YFT.from_xml_file(hi_filepath) if os.path.exists(hi_filepath) else None

    if import_settings.import_as_asset:
        return create_fragment_as_asset(yft_xml, hi_xml, name, non_hi_filepath)

    return create_fragment_obj(yft_xml, non_hi_filepath, name,
                               split_by_group=import_settings.split_by_group, hi_xml=hi_xml)


def is_hi_yft_filepath(yft_filepath: str):
    """Is this a _hi.yft.xml file?"""
    return os.path.basename(yft_filepath).endswith("_hi.yft.xml")


def make_hi_yft_filepath(yft_filepath: str) -> str:
    """Get the _hi.yft.xml filepath at the provided non-hi yft filepath."""
    yft_dir = os.path.dirname(yft_filepath)
    yft_name = get_filename(yft_filepath)

    hi_path = os.path.join(yft_dir, f"{yft_name}_hi.yft.xml")
    return hi_path


def make_non_hi_yft_filepath(yft_filepath: str) -> str:
    """Get the base .yft.xml filepath at the provided hi yft filepath."""
    yft_dir = os.path.dirname(yft_filepath)
    yft_name = get_filename(yft_filepath)
    if yft_name.endswith("_hi"):
        yft_name = yft_name[:-3]  # trim '_hi'

    non_hi_path = os.path.join(yft_dir, f"{yft_name}.yft.xml")
    return non_hi_path


def create_fragment_obj(frag_xml: Fragment, filepath: str, name: Optional[str] = None, split_by_group: bool = False, hi_xml: Optional[Fragment] = None):
    if hi_xml is not None:
        frag_xml = merge_hi_fragment(frag_xml, hi_xml)

    drawable_xml = frag_xml.drawable
    if drawable_xml.is_empty and frag_xml.cloths and not frag_xml.cloths[0].drawable.is_empty:
        # We have a fragment without a main drawable, only the cloth drawable. So shallow-copy properties we may need
        # from the cloth drawable, except the drawable models. Creating the cloth drawable model will be handled by
        # `create_env_cloth_meshes`
        cloth_drawable_xml = frag_xml.cloths[0].drawable
        drawable_xml.name = cloth_drawable_xml.name
        drawable_xml.bounding_sphere_center = cloth_drawable_xml.bounding_sphere_center
        drawable_xml.bounding_sphere_radius = cloth_drawable_xml.bounding_sphere_radius
        drawable_xml.bounding_box_min = cloth_drawable_xml.bounding_box_min
        drawable_xml.bounding_box_max = cloth_drawable_xml.bounding_box_max
        drawable_xml.lod_dist_high = cloth_drawable_xml.lod_dist_high
        drawable_xml.lod_dist_med = cloth_drawable_xml.lod_dist_med
        drawable_xml.lod_dist_low = cloth_drawable_xml.lod_dist_low
        drawable_xml.lod_dist_vlow = cloth_drawable_xml.lod_dist_vlow
        drawable_xml.shader_group = cloth_drawable_xml.shader_group
        drawable_xml.skeleton = cloth_drawable_xml.skeleton
        drawable_xml.joints = cloth_drawable_xml.joints

    materials = shadergroup_to_materials(drawable_xml.shader_group, filepath)

    # Need to append [PAINT_LAYER] extension at the end of the material names
    for mat in materials:
        if "matDiffuseColor" in mat.node_tree.nodes:
            from .properties import _update_mat_paint_name
            _update_mat_paint_name(mat)

    frag_obj = create_frag_armature(frag_xml, name)

    drawable_obj = create_fragment_drawable(frag_xml, frag_obj, filepath, materials, split_by_group)
    damaged_drawable_obj = create_fragment_drawable(
        frag_xml, frag_obj, filepath, materials, split_by_group, damaged=True)

    create_frag_collisions(frag_xml, frag_obj)
    if damaged_drawable_obj is not None:
        create_frag_collisions(frag_xml, frag_obj, damaged=True)

        if frag_xml.physics.lod1.damaged_archetype is not None:
            a = frag_xml.physics.lod1.archetype
            b = frag_xml.physics.lod1.damaged_archetype
            # We assume that these archetype properties are the same in both the undamaged and damaged archetypes so the
            # user only has to set them once in the UI
            assert a.unknown_48 == b.unknown_48, "gravity_factor different in damaged archetype. Open an issue!"
            assert a.unknown_4c == b.unknown_4c, "max_speed factor different in damaged archetype. Open an issue!"
            assert a.unknown_50 == b.unknown_50, "max_ang_speed different in damaged archetype. Open an issue!"
            assert a.unknown_54 == b.unknown_54, "buoyancy_factor different in damaged archetype. Open an issue!"

    create_phys_lod(frag_xml, frag_obj)
    set_all_bone_physics_properties(frag_obj.data, frag_xml)

    create_phys_child_meshes(frag_xml, frag_obj, drawable_obj, materials)

    create_env_cloth_meshes(frag_xml, frag_obj, drawable_obj, materials)

    if frag_xml.vehicle_glass_windows:
        create_vehicle_windows(frag_xml, frag_obj, materials)

    if frag_xml.glass_windows:
        set_all_glass_window_properties(frag_xml, frag_obj)

    if frag_xml.lights:
        create_frag_lights(frag_xml, frag_obj)

    return frag_obj


def create_frag_armature(frag_xml: Fragment, name: Optional[str] = None):
    """Create the fragment armature along with the bones and rotation limits."""
    name = name or frag_xml.name.replace("pack:/", "")
    drawable_xml = frag_xml.drawable
    frag_obj = create_armature_obj_from_skel(drawable_xml.skeleton, name, SollumType.FRAGMENT)
    create_joint_constraints(frag_obj, drawable_xml.joints)

    set_fragment_properties(frag_xml, frag_obj)

    return frag_obj


def create_fragment_drawable(frag_xml: Fragment, frag_obj: bpy.types.Object, filepath: str, materials: list[bpy.types.Material], split_by_group: bool = False, damaged: bool = False) -> Optional[bpy.types.Object]:
    if damaged:
        if not frag_xml.extra_drawables:
            return None

        drawable_xml = frag_xml.extra_drawables[0]
        drawable_name = f"{frag_obj.name}.damaged.mesh"
    else:
        drawable_xml = frag_xml.drawable
        drawable_name = f"{frag_obj.name}.mesh"

    drawable_obj = create_drawable_obj(
        drawable_xml,
        filepath,
        name=drawable_name,
        materials=materials,
        split_by_group=split_by_group,
        external_armature=frag_obj
    )
    drawable_obj.parent = frag_obj

    return drawable_obj


def merge_hi_fragment(frag_xml: Fragment, hi_xml: Fragment) -> Fragment:
    """Merge the _hi.yft variant of a Fragment (highest LOD, only used for vehicles)."""
    non_hi_children = frag_xml.physics.lod1.children
    hi_children = hi_xml.physics.lod1.children

    if len(non_hi_children) != len(hi_children):
        logger.warning(
            f"Failed to merge Fragments, {frag_xml.name} and {hi_xml.name} have different physics data!")
        return frag_xml

    frag_xml = FragmentMerger(frag_xml, hi_xml).merge()

    return frag_xml


def create_phys_lod(frag_xml: Fragment, frag_obj: bpy.types.Object):
    """Create the Fragment.Physics.LOD1 data-block. (Currently LOD1 is only supported)"""
    lod_xml = frag_xml.physics.lod1

    if not lod_xml.groups:
        return

    lod_props: LODProperties = frag_obj.fragment_properties.lod_properties
    set_lod_properties(lod_xml, lod_props)
    set_archetype_properties(lod_xml.archetype, lod_props.archetype_properties)


def set_all_bone_physics_properties(armature: bpy.types.Armature, frag_xml: Fragment):
    """Set the physics group properties for all bones in the armature."""
    groups_xml: list[PhysicsGroup] = frag_xml.physics.lod1.groups

    for group_xml in groups_xml:
        if group_xml.name not in armature.bones:
            # Bone not found, try a case-insensitive search
            group_name_lower = group_xml.name.lower()
            for armature_bone in armature.bones:
                if group_name_lower == armature_bone.name.lower():
                    group_xml.name = armature_bone.name  # update group name to match actual bone name
                    bone = armature_bone
                    break
            else:
                # Still no bone found
                logger.warning(f"No bone exists for the physics group {group_xml.name}! Skipping...")
                continue
        else:
            bone = armature.bones[group_xml.name]

        bone.sollumz_use_physics = True
        set_group_properties(group_xml, bone)


def create_frag_collisions(frag_xml: Fragment, frag_obj: bpy.types.Object, damaged: bool = False) -> Optional[bpy.types.Object]:
    lod1 = frag_xml.physics.lod1
    bounds_xml = lod1.damaged_archetype.bounds if damaged else lod1.archetype.bounds

    if bounds_xml is None or not bounds_xml.children:
        return None

    col_name_suffix = ".damaged.col" if damaged else ".col"
    composite_name = f"{frag_obj.name}{col_name_suffix}"
    composite_obj = create_empty_object(SollumType.BOUND_COMPOSITE, name=composite_name)
    composite_obj.parent = frag_obj

    for i, bound_xml in enumerate(bounds_xml.children):
        if bound_xml is None:
            continue

        bound_obj = create_bound_object(bound_xml)
        bound_obj.parent = composite_obj

        bone = find_bound_bone(i, frag_xml)
        if bone is None:
            continue

        bound_obj.name = f"{bone.name}{col_name_suffix}"

        if bound_obj.data is not None:
            bound_obj.data.name = bound_obj.name

        phys_child = lod1.children[i]
        bound_obj.child_properties.mass = phys_child.damaged_mass if damaged else phys_child.pristine_mass
        # NOTE: we currently lose damaged mass or pristine mass if the phys child only has a pristine bound or damaged
        # bound, but archetype still use this mass. Is this important?

        add_child_of_bone_constraint(bound_obj, frag_obj, bone.name)
        drawable = phys_child.damaged_drawable if damaged else phys_child.drawable
        bound_obj.matrix_local = drawable.frag_bound_matrix.transposed()


def find_bound_bone(bound_index: int, frag_xml: Fragment) -> Bone | None:
    """Get corresponding bound bone based on children"""
    children = frag_xml.physics.lod1.children

    if bound_index >= len(children):
        return

    corresponding_child = children[bound_index]
    for bone in frag_xml.drawable.skeleton.bones:
        if bone.tag != corresponding_child.bone_tag:
            continue

        return bone


def create_phys_child_meshes(frag_xml: Fragment, frag_obj: bpy.types.Object, drawable_obj: bpy.types.Object, materials: list[bpy.types.Material]):
    """Create all Fragment.Physics.LOD1.Children meshes. (Only LOD1 currently supported)"""
    lod_xml = frag_xml.physics.lod1
    children_xml: list[PhysicsChild] = lod_xml.children
    bones = frag_xml.drawable.skeleton.bones

    bone_name_by_tag: dict[str, Bone] = {
        bone.tag: bone.name for bone in bones}

    for child_xml in children_xml:
        if child_xml.drawable.is_empty:
            continue

        if child_xml.bone_tag not in bone_name_by_tag:
            logger.warning(
                "A fragment child has an invalid bone tag! Skipping...")
            continue

        bone_name = bone_name_by_tag[child_xml.bone_tag]

        create_phys_child_models(
            child_xml.drawable, frag_obj, materials, bone_name, drawable_obj)


def create_phys_child_models(drawable_xml: Drawable, frag_obj: bpy.types.Object, materials: list[bpy.types.Material], bone_name: str, drawable_obj: bpy.types.Object):
    """Create a single physics child mesh"""
    # There is usually only one drawable model in each frag child
    child_objs = create_drawable_models(
        drawable_xml, materials, f"{bone_name}.child")

    for child_obj in child_objs:
        add_child_of_bone_constraint(child_obj, frag_obj, bone_name)

        child_obj.sollumz_is_physics_child_mesh = True
        child_obj.parent = drawable_obj

    return child_objs


def create_env_cloth_meshes(frag_xml: Fragment, frag_obj: bpy.types.Object, drawable_obj: bpy.types.Object, materials: list[bpy.types.Material]):
    if not frag_xml.cloths:
        return

    from ..cwxml.cloth import EnvironmentCloth
    from ..ydr.cloth import ClothAttr, mesh_add_cloth_attribute

    cloth: EnvironmentCloth = frag_xml.cloths[0]  # game only supports a single environment cloth per fragment
    if cloth.drawable.is_empty:
        return

    model_objs = create_drawable_models(cloth.drawable, materials, f"{frag_obj.name}.cloth")
    assert model_objs and len(model_objs) == 1, "Too many models in cloth drawable!"

    model_obj = model_objs[0]
    model_obj.parent = drawable_obj

    bones = cloth.drawable.skeleton.bones
    bone_index = cloth.drawable.drawable_models_high[0].bone_index
    bone_name = bones[bone_index].name
    add_child_of_bone_constraint(model_obj, frag_obj, bone_name)

    mesh = model_obj.data

    # LOD specific data
    # TODO: handle LODs
    pin_radius = cloth.controller.bridge.pin_radius_high
    weights = cloth.controller.bridge.vertex_weights_high
    inflation_scale = cloth.controller.bridge.inflation_scale_high
    mesh_to_cloth_map = np.array(cloth.controller.bridge.display_map_high)
    cloth_to_mesh_map = np.empty_like(mesh_to_cloth_map)
    cloth_to_mesh_map[mesh_to_cloth_map] = np.arange(len(mesh_to_cloth_map))
    pinned_vertices_count = cloth.controller.cloth_high.pinned_vertices_count
    vertices_count = len(cloth.controller.cloth_high.vertex_positions)
    force_transform = np.fromstring(cloth.user_data or "", dtype=int, sep=" ")
    # TODO: store switch distances somewhere or maybe on export can be derived from existing LOD distances
    # switch_distance_up = cloth.controller.cloth_high.switch_distance_up
    # switch_distance_down = cloth.controller.cloth_high.switch_distance_down

    # TODO: pin radius
    #       There can be multiple pin radius per vertex, find a model with pin radius set
    #       Check if pin radius is only used with character cloth
    has_pinned = pinned_vertices_count > 0
    has_pin_radius = len(pin_radius) > 0
    num_pin_radius_sets = len(pin_radius) // vertices_count
    has_weights = len(weights) > 0
    has_inflation_scale = len(inflation_scale) > 0
    has_force_transform = len(force_transform) > 0

    if has_pinned:
        mesh_add_cloth_attribute(mesh, ClothAttr.PINNED)
    if has_pin_radius:
        mesh_add_cloth_attribute(mesh, ClothAttr.PIN_RADIUS)
        if num_pin_radius_sets > 4:
            logger.warning(f"Found {num_pin_radius_sets} pin radius sets, only up to 4 sets are supported!")
            num_pin_radius_sets = 4
    if has_weights:
        mesh_add_cloth_attribute(mesh, ClothAttr.VERTEX_WEIGHT)
    if has_inflation_scale:
        mesh_add_cloth_attribute(mesh, ClothAttr.INFLATION_SCALE)
    if has_force_transform:
        mesh_add_cloth_attribute(mesh, ClothAttr.FORCE_TRANSFORM)

    for mesh_vert_index, cloth_vert_index in enumerate(mesh_to_cloth_map):
        if has_pinned:
            pinned = cloth_vert_index < pinned_vertices_count
            mesh.attributes[ClothAttr.PINNED].data[mesh_vert_index].value = 1 if pinned else 0

        if has_pin_radius:
            pin_radii = [
                pin_radius[cloth_vert_index + (set_idx * vertices_count)]
                if set_idx < num_pin_radius_sets else 0.0
                for set_idx in range(4)
            ]
            mesh.attributes[ClothAttr.PIN_RADIUS].data[mesh_vert_index].color = pin_radii

        if has_weights:
            mesh.attributes[ClothAttr.VERTEX_WEIGHT].data[mesh_vert_index].value = weights[cloth_vert_index]

        if has_inflation_scale:
            mesh.attributes[ClothAttr.INFLATION_SCALE].data[mesh_vert_index].value = inflation_scale[cloth_vert_index]

        if has_force_transform:
            mesh.attributes[ClothAttr.FORCE_TRANSFORM].data[mesh_vert_index].value = force_transform[cloth_vert_index]

    custom_edges = [e for e in (cloth.controller.cloth_high.custom_edges or []) if e.vertex0 != e.vertex1]
    if custom_edges:
        next_edge = len(mesh.edges)
        mesh.edges.add(len(custom_edges))
        for custom_edge in custom_edges:
            v0 = custom_edge.vertex0
            v1 = custom_edge.vertex1
            mv0 = int(cloth_to_mesh_map[v0])
            mv1 = int(cloth_to_mesh_map[v1])
            mesh.edges[next_edge].vertices = mv0, mv1
            next_edge += 1

    # Debug code to visualize the verlet cloth edges.
    # debug_edges = [e for e in (cloth.controller.cloth_high.edges or []) if e.vertex0 != e.vertex1]
    # if debug_edges:
    #     debug_mesh = bpy.data.meshes.new(f"{mesh.name}.debug")
    #     debug_obj = bpy.data.objects.new(f"{mesh.name}.debug", debug_mesh)
    #     debug_mesh.vertices.add(len(mesh.vertices))
    #     for v in mesh.vertices:
    #         debug_mesh.vertices[v.index].co = v.co
    #     next_edge = len(debug_mesh.edges)
    #     debug_mesh.edges.add(len(debug_edges))
    #     for edge in debug_edges:
    #         v0 = edge.vertex0
    #         v1 = edge.vertex1
    #         mv0 = int(cloth_to_mesh_map[v0])
    #         mv1 = int(cloth_to_mesh_map[v1])
    #         debug_mesh.edges[next_edge].vertices = mv0, mv1
    #         next_edge += 1
    #
    #     bpy.context.collection.objects.link(debug_obj)

    cloth_props = frag_obj.fragment_properties.cloth
    cloth_props.weight = cloth.controller.cloth_high.cloth_weight
    if cloth.tuning:
        tuning = cloth.tuning
        cloth_props.enable_tuning = True
        cloth_props.tuning_flags.total = str(tuning.flags)
        cloth_props.extra_force = tuning.extra_force
        cloth_props.weight_override = tuning.weight
        cloth_props.distance_threshold = tuning.distance_threshold
        if cloth_props.tuning_flags.wind_feedback:
            cloth_props.rotation_rate = tuning.rotation_rate
            cloth_props.angle_threshold = tuning.angle_threshold
            cloth_props.pin_vert = cloth_to_mesh_map[tuning.pin_vert]
            cloth_props.non_pin_vert0 = cloth_to_mesh_map[tuning.non_pin_vert0]
            cloth_props.non_pin_vert1 = cloth_to_mesh_map[tuning.non_pin_vert1]

    if cloth.controller.cloth_high.bounds:
        cloth_bounds = create_bound_composite(cloth.controller.cloth_high.bounds)
        cloth_bounds.name = f"{frag_obj.name}.cloth_world_bounds"
        cloth_props.world_bounds = cloth_bounds


def create_vehicle_windows(frag_xml: Fragment, frag_obj: bpy.types.Object, materials: list[bpy.types.Material]):
    for window_xml in frag_xml.vehicle_glass_windows:
        window_bone = get_window_bone(window_xml, frag_xml, frag_obj.data.bones)
        col_obj = get_window_col(frag_obj, window_bone.name)

        window_name = f"{window_bone.name}_shattermap"

        if col_obj is None:
            logger.warning(
                f"Window with ItemID {window_xml.item_id} has no associated collision! Is the file malformed?")
            continue

        col_obj.child_properties.is_veh_window = True

        window_mat = get_veh_window_material(window_xml, frag_xml.drawable, materials)

        if window_mat is not None:
            col_obj.child_properties.window_mat = window_mat

        if window_xml.shattermap:
            shattermap_obj = create_shattermap_obj(window_xml, window_name, window_bone.matrix_local)
            shattermap_obj.parent = col_obj

        set_veh_window_properties(window_xml, col_obj)


def get_window_col(frag_obj: bpy.types.Object, bone_name: str) -> Optional[bpy.types.Object]:
    for obj in frag_obj.children_recursive:
        if obj.sollum_type in BOUND_TYPES:
            col_bone = get_child_of_bone(obj)

            if col_bone is not None and col_bone.name == bone_name:
                return obj


def get_veh_window_material(window_xml: Window, drawable_xml: Drawable, materials: list[bpy.types.Material]):
    """Get vehicle window material based on UnkUShort1."""
    # UnkUShort1 indexes the geometry that the window uses.
    # The VehicleGlassWindow uses the same material that the geometry uses.
    geometry_index = window_xml.unk_ushort_1
    return get_geometry_material(drawable_xml, materials, geometry_index)


def get_window_bone(window_xml: Window, frag_xml: Fragment, bpy_bones: bpy.types.ArmatureBones) -> bpy.types.Bone:
    """Get bone connected to window based on the bone tag of the physics child associated with the window."""
    children_xml: list[PhysicsChild] = frag_xml.physics.lod1.children

    child_id: int = window_xml.item_id

    if child_id < 0 or child_id >= len(children_xml):
        return bpy_bones[0]

    child_xml = children_xml[child_id]

    for bone in bpy_bones:
        if bone.bone_properties.tag != child_xml.bone_tag:
            continue

        return bone

    # Return root bone if no bone is found
    return bpy_bones[0]


def create_shattermap_obj(window_xml: Window, name: str, window_matrix: Matrix):
    try:
        mesh = create_shattermap_mesh(window_xml, name, window_matrix)
    except:
        logger.error(f"Error during creation of vehicle window mesh:\n{format_exc()}")
        return

    shattermap_obj = create_blender_object(SollumType.SHATTERMAP, name, mesh)

    if window_xml.shattermap:
        shattermap_mat = shattermap_to_material(window_xml.shattermap, name)
        mesh.materials.append(shattermap_mat)

    return shattermap_obj


def create_shattermap_mesh(window_xml: Window, name: str, window_matrix: Matrix):
    verts = calculate_window_verts(window_xml)
    faces = [[0, 1, 2, 3]]

    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.transform(window_matrix.inverted())

    uvs = np.array([[0.0, 1.0], [0.0, 0.0], [1.0, 0.0], [1.0, 1.0]], dtype=np.float64)
    create_uv_attr(mesh, 0, initial_values=uvs)

    return mesh


def calculate_window_verts(window_xml: Window):
    """Calculate the 4 vertices of the window from the projection matrix."""
    proj_mat = get_window_projection_matrix(window_xml)

    min = Vector((0, 0, 0))
    max = Vector((window_xml.width / 2, window_xml.height, 1))

    v0 = multiply_homogeneous(proj_mat, Vector((min.x, min.y, 0)))
    v1 = multiply_homogeneous(proj_mat, Vector((min.x, max.y, 0)))
    v2 = multiply_homogeneous(proj_mat, Vector((max.x, max.y, 0)))
    v3 = multiply_homogeneous(proj_mat, Vector((max.x, min.y, 0)))

    return v0, v1, v2, v3


def get_window_projection_matrix(window_xml: Window):
    proj_mat: Matrix = window_xml.projection_matrix
    # proj_mat[3][3] is currently an unknown value so it is set to 1 (CW does the same)
    proj_mat[3][3] = 1

    return proj_mat.transposed().inverted_safe()


def get_rgb(value):
    if value == "##":
        return [0, 0, 0, 1]
    elif value == "--":
        return [1, 1, 1, 1]
    else:
        value = int(value, 16)
        return [value / 255, value / 255, value / 255, 1]


def shattermap_to_image(shattermap, name):
    width = int(len(shattermap[0]) / 2)
    height = int(len(shattermap))

    img = bpy.data.images.new(name, width, height)

    pixels = []
    i = 0
    for row in reversed(shattermap):
        frow = [row[x:x + 2] for x in range(0, len(row), 2)]
        # Need to check for malformed shattermaps. ZModeler shattermaps seem to be missing a value of "--" when "--" appears in a row. We check for this specific case and insert a "--" to the row.
        # We don't handle other malformed data, an error will be logged in the try/except below.
        if len(frow) == (width - 1):
            try:
                idx = frow.index("--")
            except ValueError:
                idx = None
            if idx is not None:
                frow.insert(idx, "--")
        for value in frow:
            pixels.append(get_rgb(value))
            i += 1

    pixels = [chan for px in pixels for chan in px]
    try:
        img.pixels = pixels
    except ValueError:
        logger.error("Cannot create shattermap, shattermap data is malformed")

    return img


def shattermap_to_material(shattermap, name):
    img = shattermap_to_image(shattermap, name)
    img.pack()
    mat = material_from_image(img, name, "ShatterMap")
    mat.sollum_type = MaterialType.SHATTER_MAP

    return mat


def get_geometry_material(drawable_xml: Drawable, materials: list[bpy.types.Material], geometry_index: int) -> bpy.types.Material | None:
    """Get the material that the given geometry uses."""
    for dmodel in drawable_xml.drawable_models_high:
        geometries = dmodel.geometries

        if geometry_index > len(geometries):
            return None

        geometry = geometries[geometry_index]
        shader_index = geometry.shader_index

        if shader_index > len(materials):
            return None

        return materials[shader_index]


def set_all_glass_window_properties(frag_xml: Fragment, frag_obj: bpy.types.Object):
    """Set the glass window properties for all bones in the fragment."""
    groups_xml: list[PhysicsGroup] = frag_xml.physics.lod1.groups
    glass_windows_xml: list[GlassWindow] = frag_xml.glass_windows
    armature: bpy.types.Armature = frag_obj.data

    for group_xml in groups_xml:
        if (group_xml.glass_flags & 2) == 0:  # flag 2 indicates that the group has a glass window
            continue
        if group_xml.name not in armature.bones:
            continue

        glass_window_xml = glass_windows_xml[group_xml.glass_window_index]
        glass_type_idx = glass_window_xml.flags & 0xFF
        if glass_type_idx >= len(GlassTypes):
            continue

        bone = armature.bones[group_xml.name]
        bone.group_properties.glass_type = GlassTypes[glass_type_idx][0]


def create_frag_lights(frag_xml: Fragment, frag_obj: bpy.types.Object):
    lights_parent = create_light_objs(frag_xml.lights, frag_obj)
    lights_parent.name = f"{frag_obj.name}.lights"
    lights_parent.parent = frag_obj


def set_fragment_properties(frag_xml: Fragment, frag_obj: bpy.types.Object):
    # unknown_c0 include "entity class" and "attach bottom end" but those are always 0 in game assets and seem unused
    frag_obj.fragment_properties.template_asset = FragmentTemplateAsset((frag_xml.unknown_c0 >> 8) & 0xFF).name
    frag_obj.fragment_properties.unbroken_elasticity = frag_xml.unknown_cc
    frag_obj.fragment_properties.gravity_factor = frag_xml.gravity_factor
    frag_obj.fragment_properties.buoyancy_factor = frag_xml.buoyancy_factor


def set_lod_properties(lod_xml: PhysicsLOD, lod_props: LODProperties):
    lod_props.min_move_force = lod_xml.unknown_1c
    lod_props.unbroken_cg_offset = lod_xml.unknown_50
    lod_props.damping_linear_c = lod_xml.damping_linear_c
    lod_props.damping_linear_v = lod_xml.damping_linear_v
    lod_props.damping_linear_v2 = lod_xml.damping_linear_v2
    lod_props.damping_angular_c = lod_xml.damping_angular_c
    lod_props.damping_angular_v = lod_xml.damping_angular_v
    lod_props.damping_angular_v2 = lod_xml.damping_angular_v2


def set_archetype_properties(arch_xml: Archetype, arch_props: FragArchetypeProperties):
    arch_props.name = arch_xml.name
    arch_props.gravity_factor = arch_xml.unknown_48
    arch_props.max_speed = arch_xml.unknown_4c
    arch_props.max_ang_speed = arch_xml.unknown_50
    arch_props.buoyancy_factor = arch_xml.unknown_54


def set_group_properties(group_xml: PhysicsGroup, bone: bpy.types.Bone):
    bone.group_properties.name = group_xml.name
    for i in range(len(bone.group_properties.flags)):
        bone.group_properties.flags[i] = (group_xml.glass_flags & (1 << i)) != 0
    bone.group_properties.strength = group_xml.strength
    bone.group_properties.force_transmission_scale_up = group_xml.force_transmission_scale_up
    bone.group_properties.force_transmission_scale_down = group_xml.force_transmission_scale_down
    bone.group_properties.joint_stiffness = group_xml.joint_stiffness
    bone.group_properties.min_soft_angle_1 = group_xml.min_soft_angle_1
    bone.group_properties.max_soft_angle_1 = group_xml.max_soft_angle_1
    bone.group_properties.max_soft_angle_2 = group_xml.max_soft_angle_2
    bone.group_properties.max_soft_angle_3 = group_xml.max_soft_angle_3
    bone.group_properties.rotation_speed = group_xml.rotation_speed
    bone.group_properties.rotation_strength = group_xml.rotation_strength
    bone.group_properties.restoring_strength = group_xml.restoring_strength
    bone.group_properties.restoring_max_torque = group_xml.restoring_max_torque
    bone.group_properties.latch_strength = group_xml.latch_strength
    bone.group_properties.min_damage_force = group_xml.min_damage_force
    bone.group_properties.damage_health = group_xml.damage_health
    bone.group_properties.weapon_health = group_xml.unk_float_5c
    bone.group_properties.weapon_scale = group_xml.unk_float_60
    bone.group_properties.vehicle_scale = group_xml.unk_float_64
    bone.group_properties.ped_scale = group_xml.unk_float_68
    bone.group_properties.ragdoll_scale = group_xml.unk_float_6c
    bone.group_properties.explosion_scale = group_xml.unk_float_70
    bone.group_properties.object_scale = group_xml.unk_float_74
    bone.group_properties.ped_inv_mass_scale = group_xml.unk_float_78
    bone.group_properties.melee_scale = group_xml.unk_float_a8


def set_veh_window_properties(window_xml: Window, window_obj: bpy.types.Object):
    window_obj.vehicle_window_properties.data_min = window_xml.unk_float_17
    window_obj.vehicle_window_properties.data_max = window_xml.unk_float_18
    window_obj.vehicle_window_properties.cracks_texture_tiling = window_xml.cracks_texture_tiling


def create_fragment_as_asset(frag_xml: Fragment, hi_frag_xml: Optional[Fragment], name: str, filepath: str):
    """Create fragment as an asset with all meshes joined together."""
    if hi_frag_xml is not None:
        frag_xml = merge_hi_fragment(frag_xml, hi_frag_xml)

    frag_xml.drawable.drawable_models_low = []
    frag_xml.drawable.drawable_models_med = []
    frag_xml.drawable.drawable_models_vlow = []

    from ..ydr.ydrimport import convert_object_to_asset
    frag_obj = create_fragment_obj(frag_xml, filepath, name)
    convert_object_to_asset(name, frag_obj)
