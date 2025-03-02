import bpy
from ..sollumz_properties import SollumType
from .. import logger

def create_materials(mat_name, color):

    mat = bpy.data.materials.get(mat_name)

    if not mat:
        alpha = 0.8
        mat = bpy.data.materials.new(mat_name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        principled_bsdf = nodes.get("Principled BSDF")
        principled_bsdf.inputs['Base Color'].default_value = (color[0], color[1], color[2], alpha)
        principled_bsdf.inputs['Alpha'].default_value = alpha

        material_output = mat.node_tree.nodes.get('Material Output')

        mat.node_tree.links.new(material_output.inputs[0], principled_bsdf.outputs[0])
        mat.diffuse_color = (color[0], color[1], color[2], alpha)

    return mat


def normalize_verts(minX, maxX, minY, maxY):
    rounded = False

    if isinstance(minX, float) and not minX.is_integer():
        minX = round(minX)
        rounded = True
    if isinstance(maxX, float) and not maxX.is_integer():
        maxX = round(maxX)
        rounded = True
    if isinstance(minY, float) and not minY.is_integer():
        minY = round(minY)
        rounded = True
    if isinstance(maxY, float) and not maxY.is_integer():
        maxY = round(maxY)
        rounded = True

    return rounded, minX, maxX, minY, maxY


def ensure_quad_data(quad):
    mesh = quad.data
    global_coords = [quad.matrix_world @ vert.co for vert in mesh.vertices]

    minX = min(coord.x for coord in global_coords)
    maxX = max(coord.x for coord in global_coords)
    minY = min(coord.y for coord in global_coords)
    maxY = max(coord.y for coord in global_coords)

    rounded, minX, maxX, minY, maxY = normalize_verts(minX, maxX, minY, maxY)
    if rounded:
        logger.warning(f"Object {quad.name} has been rounded. (Vertices)")

    expected_vertices = {
        (minX, minY),
        (maxX, minY),
        (maxX, maxY),
        (minX, maxY)}
    
    actual_vertices = {(round(coord.x), round(coord.y)) for coord in global_coords}
    
    if expected_vertices != actual_vertices:
        logger.error(f"Object {quad.name} will be skipped because is not uniform. (Vertices)")
        return None

    if quad.sollum_type == SollumType.WATER_QUAD:
        z_values = [coord.z for coord in global_coords]

        if not all(z == z_values[0] for z in z_values): 
            logger.error(f"Object {quad.name} will be skipped because is not uniform. (Height)")
            return None

        return minX, maxX, minY, maxY, z_values[0]
    
    return minX, maxX, minY, maxY