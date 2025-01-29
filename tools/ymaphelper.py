import bpy
from pathlib import Path
from mathutils import Vector
from ..sollumz_properties import SOLLUMZ_UI_NAMES, SollumType
from ..tools.blenderhelper import find_bsdf_and_material_output, remove_number_suffix
from ..shared.obj_reader import obj_read_from_file
from ..tools.meshhelper import get_combined_bound_box, get_sphere_radius

# TODO: This is not a real flag calculation, definitely need to do better


def calculate_ymap_content_flags(selected_ymap=None, sollum_type=None):
    content_flags = []
    if sollum_type == SollumType.YMAP_ENTITY_GROUP:
        selected_ymap.ymap_properties.content_flags_toggle.has_hd = True
        selected_ymap.ymap_properties.content_flags_toggle.has_physics = True
        selected_ymap.ymap_properties.content_flags_toggle.has_occl = False
    elif sollum_type == SollumType.YMAP_MODEL_OCCLUDER_GROUP or sollum_type == SollumType.YMAP_BOX_OCCLUDER_GROUP:
        selected_ymap.ymap_properties.content_flags_toggle.has_hd = False
        selected_ymap.ymap_properties.content_flags_toggle.has_physics = False
        selected_ymap.ymap_properties.content_flags_toggle.has_occl = True

    return content_flags


def create_ymap(name="ymap", sollum_type=SollumType.YMAP):
    empty = bpy.data.objects.new(SOLLUMZ_UI_NAMES[sollum_type], None)
    empty.empty_display_size = 0
    empty.sollum_type = sollum_type
    empty.name = name
    bpy.context.collection.objects.link(empty)
    return empty


def create_ymap_group(sollum_type=None, selected_ymap=None, empty_name=None, select=True):
    empty = bpy.data.objects.new(SOLLUMZ_UI_NAMES[sollum_type], None)
    empty.empty_display_size = 0
    empty.sollum_type = sollum_type
    empty.name = empty_name
    bpy.context.collection.objects.link(empty)
    if sollum_type == SollumType.YMAP_ENTITY_GROUP:
        selected_ymap.ymap_properties.content_flags_toggle.has_hd = True
        selected_ymap.ymap_properties.content_flags_toggle.has_physics = True
    elif sollum_type == SollumType.YMAP_BOX_OCCLUDER_GROUP or sollum_type == SollumType.YMAP_MODEL_OCCLUDER_GROUP:
        selected_ymap.ymap_properties.content_flags_toggle.has_occl = True
    empty.parent = selected_ymap
    calculate_ymap_content_flags(selected_ymap, sollum_type)

    if select:
        bpy.ops.object.select_all(action='DESELECT')
        empty.select_set(True)
        bpy.context.view_layer.objects.active = empty

    return empty


def add_occluder_material(sollum_type=None):
    """Get occluder material or create it if not exist."""
    mat_name = ""
    mat_color = []
    mat_transparency = 0.5

    if sollum_type == SollumType.YMAP_MODEL_OCCLUDER:
        mat_name = "model_occluder_material"
        mat_color = (1, 0, 0, mat_transparency)
    elif sollum_type == SollumType.YMAP_BOX_OCCLUDER:
        mat_name = "box_occluder_material"
        mat_color = (0, 0, 1, mat_transparency)

    material = bpy.data.materials.get(mat_name) or bpy.data.materials.new(mat_name)
    material.blend_method = "BLEND"
    material.use_nodes = True
    bsdf, _ = find_bsdf_and_material_output(material)
    bsdf.inputs["Alpha"].default_value = mat_transparency
    bsdf.inputs["Base Color"].default_value = mat_color
    bsdf.inputs["Specular IOR Level"].default_value = 0
    bsdf.inputs["Roughness"].default_value = 1
    bsdf.inputs["Metallic"].default_value = 0

    # For display in solid mode
    material.diffuse_color = mat_color
    material.roughness = 1

    return material


CARGEN_MESH_NAME = ".sollumz.cargen_mesh"


def get_cargen_mesh() -> bpy.types.Mesh:
    mesh = bpy.data.meshes.get(CARGEN_MESH_NAME, None)
    if mesh is None:
        file_path = Path(__file__).parent.joinpath("car_model.obj")
        cargen_obj_mesh = obj_read_from_file(file_path)
        mesh = cargen_obj_mesh.as_bpy_mesh(CARGEN_MESH_NAME)

    return mesh

class ExtentsData:
    def __init__(self, lod_dist, bb_min, bb_max, bs_radius, scale):
        self.lod_dist = lod_dist
        self.bb_min = bb_min
        self.bb_max = bb_max
        self.bs_radius = bs_radius
        self.scale = scale
def get_extents_data(obj, entity_extents_data):
    archetype_name = remove_number_suffix(obj.name)

    if archetype_name in entity_extents_data:
        return entity_extents_data[archetype_name]

    def create_extents_data_from_archetype(archetype):
        return ExtentsData(
            lod_dist=archetype.lod_dist,
            bb_min=Vector((archetype.bb_min[0], archetype.bb_min[1], archetype.bb_min[2])),
            bb_max=Vector((archetype.bb_max[0], archetype.bb_max[1], archetype.bb_max[2])),
            bs_radius=archetype.bs_radius,
            scale=Vector((1, 1, 1))
        )

    # Search in all ytyps
    for ytyp in bpy.context.scene.ytyps:
        if ytyp.archetypes:
            for archetype in ytyp.archetypes:
                if archetype.name == archetype_name:
                    entity_extents_data[archetype_name] = create_extents_data_from_archetype(archetype)
                    return entity_extents_data[archetype_name]

    # No ytyp so we calculate bb
    bbmin, bbmax = get_combined_bound_box(obj, use_world=False)
    bs_radius = get_sphere_radius(bbmin, bbmax)
    entity_extents_data[archetype_name] = ExtentsData(lod_dist=60, bb_min=bbmin, bb_max=bbmax, bs_radius=bs_radius, scale=Vector((1, 1, 1)))

    return entity_extents_data[archetype_name]

def generate_ymap_extents(selected_ymap=None):
    emin = Vector((float('inf'), float('inf'), float('inf')))
    emax = Vector((float('-inf'), float('-inf'), float('-inf')))
    smin = Vector((float('inf'), float('inf'), float('inf')))
    smax = Vector((float('-inf'), float('-inf'), float('-inf')))

    entity_extents_data = {}

    # Clone of CodeWalker's ymap extents calculations
    for child in selected_ymap.children:
        if child.sollum_type == SollumType.YMAP_ENTITY_GROUP:
            for entity_obj in child.children:
                if entity_obj.sollum_type == SollumType.DRAWABLE or entity_obj.sollum_type == SollumType.FRAGMENT:
                    position = entity_obj.location
                    orientation = entity_obj.rotation_euler.to_matrix()

                    extents_data = get_extents_data(entity_obj, entity_extents_data)
                    lod_dist = (entity_obj.entity_properties.lod_dist
                                if entity_obj.entity_properties.lod_dist > -1.0
                                else extents_data.lod_dist)

                    bbmin = extents_data.bb_min * extents_data.scale
                    bbmax = extents_data.bb_max * extents_data.scale

                    corners = [
                        orientation @ Vector((bbmin.x, bbmin.y, bbmin.z)),
                        orientation @ Vector((bbmin.x, bbmin.y, bbmax.z)),
                        orientation @ Vector((bbmin.x, bbmax.y, bbmin.z)),
                        orientation @ Vector((bbmin.x, bbmax.y, bbmax.z)),
                        orientation @ Vector((bbmax.x, bbmin.y, bbmin.z)),
                        orientation @ Vector((bbmax.x, bbmin.y, bbmax.z)),
                        orientation @ Vector((bbmax.x, bbmax.y, bbmin.z)),
                        orientation @ Vector((bbmax.x, bbmax.y, bbmax.z))
                    ]

                    stream_bbmin = bbmin - Vector((lod_dist, lod_dist, lod_dist))
                    stream_bbmax = bbmax + Vector((lod_dist, lod_dist, lod_dist))

                    stream_corners = [
                        orientation @ Vector((stream_bbmin.x, stream_bbmin.y, stream_bbmin.z)),
                        orientation @ Vector((stream_bbmin.x, stream_bbmin.y, stream_bbmax.z)),
                        orientation @ Vector((stream_bbmin.x, stream_bbmax.y, stream_bbmin.z)),
                        orientation @ Vector((stream_bbmin.x, stream_bbmax.y, stream_bbmax.z)),
                        orientation @ Vector((stream_bbmax.x, stream_bbmin.y, stream_bbmin.z)),
                        orientation @ Vector((stream_bbmax.x, stream_bbmin.y, stream_bbmax.z)),
                        orientation @ Vector((stream_bbmax.x, stream_bbmax.y, stream_bbmin.z)),
                        orientation @ Vector((stream_bbmax.x, stream_bbmax.y, stream_bbmax.z))
                    ]

                    for corner in corners:
                        corner_world = position + corner
                        emin = Vector(min(emin[i], corner_world[i]) for i in range(3))
                        emax = Vector(max(emax[i], corner_world[i]) for i in range(3))

                    for stream_corner in stream_corners:
                        stream_corner_world = position + stream_corner
                        smin = Vector(min(smin[i], stream_corner_world[i]) for i in range(3))
                        smax = Vector(max(smax[i], stream_corner_world[i]) for i in range(3))

        elif child.sollum_type == SollumType.YMAP_BOX_OCCLUDER_GROUP:
            for box_obj in child.children:
                if box_obj.sollum_type == SollumType.YMAP_BOX_OCCLUDER:
                    position = box_obj.location
                    size = box_obj.dimensions

                    bbmin = position - size
                    bbmax = position + size

                    emin = Vector(min(emin[i], bbmin[i]) for i in range(3))
                    emax = Vector(max(emax[i], bbmax[i]) for i in range(3))
                    smin = Vector(min(smin[i], bbmin[i]) for i in range(3))
                    smax = Vector(max(smax[i], bbmax[i]) for i in range(3))

        elif child.sollum_type == SollumType.YMAP_MODEL_OCCLUDER_GROUP:
            for model_obj in child.children:
                if model_obj.sollum_type == SollumType.YMAP_MODEL_OCCLUDER:
                    bbmin, bbmax = get_combined_bound_box(model_obj, use_world=True)

                    emin = Vector(min(emin[i], bbmin[i]) for i in range(3))
                    emax = Vector(max(emax[i], bbmax[i]) for i in range(3))
                    smin = Vector(min(smin[i], bbmin[i]) for i in range(3))
                    smax = Vector(max(smax[i], bbmax[i]) for i in range(3))

        elif child.sollum_type == SollumType.YMAP_CAR_GENERATOR_GROUP:
            for cargen_obj in child.children:
                if cargen_obj.sollum_type == SollumType.YMAP_CAR_GENERATOR:
                    position = cargen_obj.location
                    perpendicular_length = Vector((
                        cargen_obj.ymap_cargen_properties.perpendicular_length,
                        cargen_obj.ymap_cargen_properties.perpendicular_length,
                        cargen_obj.ymap_cargen_properties.perpendicular_length
                    ))

                    bbmin = position - perpendicular_length
                    bbmax = position + perpendicular_length

                    emin = Vector(min(emin[i], bbmin[i]) for i in range(3))
                    emax = Vector(max(emax[i], bbmax[i]) for i in range(3))

                    sbmin = position - perpendicular_length * 2.0
                    sbmax = position + perpendicular_length * 2.0

                    smin = Vector(min(smin[i], sbmin[i]) for i in range(3))
                    smax = Vector(max(smax[i], sbmax[i]) for i in range(3))

        # TODO: grass

        # TODO: lod lights

        # TODO: distant lod lights

    selected_ymap.ymap_properties.entities_extents_min = emin
    selected_ymap.ymap_properties.entities_extents_max = emax
    selected_ymap.ymap_properties.streaming_extents_min = smin
    selected_ymap.ymap_properties.streaming_extents_max = smax
