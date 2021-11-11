from .codewalker_xml import *


class YMAP:

    @staticmethod
    def from_xml_file(filepath):
        return CMapData.from_xml_file(filepath)

    @staticmethod
    def write_xml(cmap_data, filepath):
        return cmap_data.write_xml(filepath)


class EntityItem(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.type = AttributeProperty("type", "CEntityDef")
        self.archetype_name = TextProperty("archetypeName")
        self.flags = ValueProperty("flags", 0)
        self.guid = ValueProperty("guid", 0)
        self.position = VectorProperty("position")
        self.rotation = QuaternionProperty("rotation")
        self.scale_xy = ValueProperty("scaleXY", 0)
        self.scale_z = ValueProperty("scaleZ", 0)
        self.parent_index = ValueProperty("parentIndex", 0)
        self.lod_dist = ValueProperty("lodDist", 0)
        self.child_lod_dist = ValueProperty("childLodDist", 0)
        self.lod_level = TextProperty("lodLevel")
        self.num_children = ValueProperty("numChildren", 0)
        self.priority_level = TextProperty("priorityLevel")
        self.extensions = None
        self.ambient_occlusion_multiplier = ValueProperty(
            "ambientOcclusionMultiplier", 0)
        self.artificial_ambient_occlusion = ValueProperty(
            "artificialAmbientOcclusion", 0)
        self.tint_value = ValueProperty("tintValue", 0)


class EntityListProperty(ListProperty):
    list_type = EntityItem
    tag_name = "entities"


class CMapData(ElementTree, AbstractClass):
    tag_name = "CMapData"

    def __init__(self):
        super().__init__()
        self.name = TextProperty("name")
        self.parent = TextProperty("parent")
        self.flags = ValueProperty("flags", 0)
        self.content_flags = ValueProperty("contentFlags", 0)
        self.streaming_extents_min = VectorProperty("streamingExtentsMin")
        self.streaming_extents_max = VectorProperty("streamingExtentsMax")
        self.entities_extents_min = VectorProperty("entitiesExtentsMin")
        self.entities_extents_max = VectorProperty("entitiesExtentsMax")
        self.entities = EntityListProperty()
