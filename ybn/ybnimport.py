import bpy
from .properties import CollisionMatFlags
from ..cwxml import bound as ybnxml
from ..sollumz_properties import SollumType, MaterialType, SOLLUMZ_UI_NAMES
from .collision_materials import create_collision_material_from_index
from ..tools.meshhelper import create_box, create_vertexcolor_layer, create_disc
from ..tools.utils import get_direction_of_vectors, get_distance_of_vectors, abs_vector
from ..tools.blenderhelper import create_mesh_object
import os
from mathutils import Matrix, Vector


def init_poly_obj(poly, sollum_type, materials):
    name = SOLLUMZ_UI_NAMES[sollum_type]
    mesh = bpy.data.meshes.new(name)
    if poly.material_index < len(materials):
        mesh.materials.append(materials[poly.material_index])

    obj = bpy.data.objects.new(name, mesh)
    obj.sollum_type = sollum_type.value

    return obj


def poly_to_obj(poly, materials, vertices) -> bpy.types.Object:
    if type(poly) == ybnxml.Box:
        obj = init_poly_obj(poly, SollumType.BOUND_POLY_BOX, materials)

        v1 = vertices[poly.v1]
        v2 = vertices[poly.v2]
        v3 = vertices[poly.v3]
        v4 = vertices[poly.v4]
        center = (v1 + v2 + v3 + v4) * 0.25

        # Get edges from the 4 opposing corners of the box
        a1 = ((v3 + v4) - (v1 + v2)) * 0.5
        v2 = v1 + a1
        v3 = v3 - a1
        v4 = v4 - a1

        minedge = Vector((0.0001, 0.0001, 0.0001))
        edge1 = max(v2 - v1, minedge)
        edge2 = max(v3 - v1, minedge)
        edge3 = max((v4 - v1), minedge)

        # Order edges
        s1 = False
        s2 = False
        s3 = False
        if edge2.length > edge1.length:
            t1 = edge1
            edge1 = edge2
            edge2 = t1
            s1 = True
        if edge3.length > edge1.length:
            t1 = edge1
            edge1 = edge3
            edge3 = t1
            s2 = True
        if edge3.length > edge2.length:
            t1 = edge2
            edge2 = edge3
            edge3 = t1
            s3 = True

        # Ensure all edge vectors are perpendicular to each other
        b1 = edge1.normalized()
        b2 = edge2.normalized()
        b3 = b1.cross(b2).normalized()
        b2 = b1.cross(b3).normalized()
        edge2 = b2 * edge2.dot(b2)
        edge3 = b3 * edge3.dot(b3)

        # Unswap edges
        if s3 == True:
            t1 = edge2
            edge2 = edge3
            edge3 = t1
        if s2 == True:
            t1 = edge1
            edge1 = edge3
            edge3 = t1
        if s1 == True:
            t1 = edge1
            edge1 = edge2
            edge2 = t1

        mat = Matrix()
        mat[0] = edge1.x, edge2.x, edge3.x, center.x
        mat[1] = edge1.y, edge2.y, edge3.y, center.y
        mat[2] = edge1.z, edge2.z, edge3.z, center.z

        create_box(obj.data, size=1)
        obj.matrix_basis = mat

        return obj
    elif type(poly) == ybnxml.Sphere:
        sphere = init_poly_obj(poly, SollumType.BOUND_POLY_SPHERE, materials)
        sphere.bound_radius = poly.radius

        sphere.location = vertices[poly.v]

        return sphere
    elif type(poly) == ybnxml.Capsule:
        capsule = init_poly_obj(poly, SollumType.BOUND_POLY_CAPSULE, materials)
        v1 = vertices[poly.v1]
        v2 = vertices[poly.v2]
        rot = get_direction_of_vectors(v1, v2)
        capsule.bound_radius = poly.radius * 2
        capsule.bound_length = ((v1 - v2).length + (poly.radius * 2)) / 2

        capsule.location = (v1 + v2) / 2
        capsule.rotation_euler = rot

        return capsule
    elif type(poly) == ybnxml.Cylinder:
        cylinder = init_poly_obj(
            poly, SollumType.BOUND_POLY_CYLINDER, materials)
        v1 = vertices[poly.v1]
        v2 = vertices[poly.v2]

        rot = get_direction_of_vectors(v1, v2)

        cylinder.bound_radius = poly.radius
        cylinder.bound_length = get_distance_of_vectors(v1, v2)
        cylinder.matrix_world = Matrix()

        cylinder.location = (v1 + v2) / 2
        cylinder.rotation_euler = rot

        return cylinder


def mat_to_obj(gmat):
    mat = create_collision_material_from_index(gmat.type)
    mat.sollum_type = MaterialType.COLLISION
    mat.collision_properties.procedural_id = gmat.procedural_id
    mat.collision_properties.room_id = gmat.room_id
    mat.collision_properties.ped_density = gmat.ped_density
    mat.collision_properties.material_color_index = gmat.material_color_index

    # Assign flags
    for flag_name in CollisionMatFlags.__annotations__.keys():
        if f"FLAG_{flag_name.upper()}" in gmat.flags:
            setattr(mat.collision_flags, flag_name, True)

    return mat


def bound_geometry_to_obj(geometry: ybnxml.BoundGeometry):
    geom_obj = init_bound_item_obj(geometry, SollumType.BOUND_GEOMETRY)
    materials = create_geometry_materials(geometry)

    create_bvh_polys(geometry, materials, geom_obj)

    triangles = get_poly_triangles(geometry.polygons)

    mesh = create_bound_mesh_data(
        geometry.vertices, triangles, geometry, materials)
    mesh.transform(Matrix.Translation(geometry.geometry_center))
    geom_obj.data = mesh

    if geometry.vertices_2:
        create_deformed_shape_keys(
            geom_obj, triangles, geometry, materials)

    return geom_obj


def create_deformed_shape_keys(geom_obj: bpy.types.Object, triangles: list[ybnxml.Triangle], geometry: ybnxml.BoundGeometry, materials: list[bpy.types.Material]):
    geom_obj.shape_key_add(name="Basis")
    deformed_key = geom_obj.shape_key_add(name="Deformed")

    mesh_damaged = create_bound_mesh_data(
        geometry.vertices_2, triangles, geometry, materials)
    mesh_damaged.transform(Matrix.Translation(geometry.geometry_center))

    for i, vert in enumerate(mesh_damaged.vertices):
        deformed_key.data[i].co = vert.co

    bpy.data.meshes.remove(mesh_damaged)


def bvh_to_obj(bvh: ybnxml.BoundGeometryBVH):
    bvh_obj = init_bound_item_obj(bvh, SollumType.BOUND_GEOMETRYBVH)
    materials = create_geometry_materials(bvh)

    create_bvh_polys(bvh, materials, bvh_obj)

    triangles = get_poly_triangles(bvh.polygons)

    mesh = create_bound_mesh_data(bvh.vertices, triangles, bvh, materials)
    bound_geom_obj = create_mesh_object(
        SollumType.BOUND_POLY_TRIANGLE, mesh=mesh)
    bound_geom_obj.location = bvh.geometry_center
    bound_geom_obj.parent = bvh_obj

    return bvh_obj


def create_geometry_materials(geometry: ybnxml.BoundGeometryBVH):
    materials: list[bpy.types.Material] = []

    for gmat in geometry.materials:
        materials.append(mat_to_obj(gmat))

    return materials


def create_bvh_polys(bvh: ybnxml.BoundGeometryBVH, materials: list[bpy.types.Material], bvh_obj: bpy.types.Object):
    for poly in bvh.polygons:
        if type(poly) is ybnxml.Triangle:
            continue

        poly_obj = poly_to_obj(poly, materials, bvh.vertices)

        bpy.context.collection.objects.link(poly_obj)
        poly_obj.location += bvh.geometry_center
        poly_obj.parent = bvh_obj


def get_poly_triangles(polys: list[ybnxml.Polygon]):
    return [poly for poly in polys if isinstance(poly, ybnxml.Triangle)]


def create_bound_mesh_data(vertices: list[Vector], triangles: list[ybnxml.Triangle], geometry: ybnxml.BoundGeometryBVH, materials: list[bpy.types.Material]):
    # obj = create_mesh_object(SollumType.BOUND_POLY_TRIANGLE)
    mesh = bpy.data.meshes.new(
        SOLLUMZ_UI_NAMES[SollumType.BOUND_POLY_TRIANGLE])

    verts, faces = get_bound_geom_mesh_data(vertices, triangles)

    mesh.from_pydata(verts, [], faces)

    if geometry.vertex_colors:
        create_vertexcolor_layer(mesh, 0, geometry.vertex_colors)

    apply_bound_geom_materials(mesh, triangles, materials)

    mesh.validate()

    return mesh


def get_bound_geom_mesh_data(vertices: list[Vector], triangles: list[ybnxml.Triangle]):
    verts = []
    faces = []

    for poly in triangles:
        face = []
        v1 = vertices[poly.v1]
        v2 = vertices[poly.v2]
        v3 = vertices[poly.v3]
        if not v1 in verts:
            verts.append(v1)
            face.append(len(verts) - 1)
        else:
            face.append(verts.index(v1))
        if not v2 in verts:
            verts.append(v2)
            face.append(len(verts) - 1)
        else:
            face.append(verts.index(v2))
        if not v3 in verts:
            verts.append(v3)
            face.append(len(verts) - 1)
        else:
            face.append(verts.index(v3))
        faces.append(face)

    return verts, faces


def apply_bound_geom_materials(mesh: bpy.types.Mesh, triangles: list[ybnxml.Triangle], materials: list[bpy.types.Material]):
    for mat in materials:
        mesh.materials.append(mat)

    for i, poly_xml in enumerate(triangles):
        mesh.polygons[i].material_index = poly_xml.material_index


def init_bound_item_obj(bound, sollum_type):
    obj = init_bound_obj(bound, sollum_type)
    # assign obj composite flags
    for prop in dir(obj.composite_flags1):
        for f in bound.composite_flags1:
            if f.lower() == prop:
                setattr(obj.composite_flags1, prop, True)

    for prop in dir(obj.composite_flags2):
        for f in bound.composite_flags2:
            if f.lower() == prop:
                setattr(obj.composite_flags2, prop, True)

    obj.matrix_world = bound.composite_transform.transposed()

    bpy.context.collection.objects.link(obj)

    return obj


def init_bound_obj(bound, sollum_type):
    obj = None
    name = SOLLUMZ_UI_NAMES[sollum_type]
    if not (sollum_type == SollumType.BOUND_COMPOSITE or sollum_type == SollumType.BOUND_GEOMETRYBVH):
        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, mesh)
        mat_index = bound.material_index
        try:
            mat = create_collision_material_from_index(mat_index)
            mesh.materials.append(mat)
        except IndexError:
            print(
                f"Warning: Failed to set materials for {name}. Material index {mat_index} does not exist in collisionmats list.")
    else:
        obj = bpy.data.objects.new(name, None)

    obj.empty_display_size = 0
    obj.sollum_type = sollum_type.value

    obj.bound_properties.procedural_id = bound.procedural_id
    obj.bound_properties.room_id = bound.room_id
    obj.bound_properties.ped_density = bound.ped_density
    obj.bound_properties.poly_flags = bound.poly_flags
    obj.bound_properties.inertia = bound.inertia
    obj.bound_properties.unk_flags = bound.unk_flags
    obj.margin = bound.margin
    obj.bound_properties.volume = bound.volume

    if sollum_type == SollumType.BOUND_GEOMETRY:
        obj.bound_properties.unk_float_1 = bound.unk_float_1
        obj.bound_properties.unk_float_2 = bound.unk_float_2

    return obj


def bound_to_obj(bound):
    if bound.type == "Box":
        box = init_bound_item_obj(bound, SollumType.BOUND_BOX)
        box.bound_dimensions = abs_vector(bound.box_max - bound.box_min)
        box.data.transform(Matrix.Translation(bound.box_center))

        return box
    elif bound.type == "Sphere":
        sphere = init_bound_item_obj(bound, SollumType.BOUND_SPHERE)
        sphere.bound_radius = bound.sphere_radius

        return sphere
    elif bound.type == "Capsule":
        capsule = init_bound_item_obj(bound, SollumType.BOUND_CAPSULE)
        bbmin, bbmax = bound.box_min, bound.box_max
        capsule.bound_length = bbmax.z - bbmin.z
        capsule.bound_radius = bound.sphere_radius

        return capsule
    elif bound.type == "Cylinder":
        cylinder = init_bound_item_obj(bound, SollumType.BOUND_CYLINDER)
        bbmin, bbmax = bound.box_min, bound.box_max
        extent = bbmax - bbmin
        cylinder.bound_length = extent.y
        cylinder.bound_radius = extent.x * 0.5

        return cylinder
    elif bound.type == "Disc":
        disc = init_bound_item_obj(bound, SollumType.BOUND_DISC)
        bbmin, bbmax = bound.box_min, bound.box_max
        disc.bound_radius = bound.sphere_radius
        create_disc(disc.data, bound.sphere_radius, bound.margin * 2)

        return disc
    elif bound.type == "Cloth":
        cloth = init_bound_item_obj(bound, SollumType.BOUND_CLOTH)
        return cloth
    elif bound.type == "Geometry":
        geometry = bound_geometry_to_obj(bound)
        return geometry
    elif bound.type == "GeometryBVH":
        bvh = bvh_to_obj(bound)
        return bvh


def composite_to_obj(bounds, name, from_drawable=False):
    if from_drawable:
        composite = bounds
    else:
        composite = bounds.composite

    obj = init_bound_obj(composite, SollumType.BOUND_COMPOSITE)
    obj.name = name

    for child in composite.children:
        child_obj = bound_to_obj(child)
        if child_obj:
            child_obj.parent = obj

    bpy.context.collection.objects.link(obj)

    return obj


def import_ybn(filepath):
    ybn_xml = ybnxml.YBN.from_xml_file(filepath)
    composite_to_obj(ybn_xml, os.path.basename(
        filepath.replace(ybnxml.YBN.file_extension, "")))
