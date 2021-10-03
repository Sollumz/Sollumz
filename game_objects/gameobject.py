from bpy.types import Object as BlenderObject
from Sollumz.codewalker_xml.codewalker_xml import ElementTree
from abc import ABC as AbstractClass, abstractclassmethod, abstractmethod

class GameObject(AbstractClass):
    """Converts GTA V objects to blender objects"""

    def __init__(self, data: ElementTree) -> None:
        super().__init__()
        """The Codewalker XML structured data."""
        self.data = data

    @abstractmethod
    def to_obj(self) -> BlenderObject:
        pass
    
    @abstractclassmethod
    def from_obj(cls, obj: BlenderObject):
        pass