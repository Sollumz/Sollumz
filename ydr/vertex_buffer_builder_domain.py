from enum import Enum, auto


class VBBuilderDomain(Enum):
    FACE_CORNER = auto()
    """Mesh is exported allowing each face corner to have their own set of attributes."""
    VERTEX = auto()
    """Mesh is exported only allowing a single set of attributes per vertex. If face corners attached to the vertex
    have different attributes (vertex colors, UVs, etc.), only the attributes of one of the face corners is used. In the
    case of normals, the average of the face corner normals is used.
    """
