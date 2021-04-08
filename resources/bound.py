import xml.etree.ElementTree as ET
import tools.xmlhelper as xmlhelper

class BoundBase:

    def __init__(self):
        self.box_min = []
        self.box_max = []
        self.box_center = []
        self.sphere_center = []
        self.sphere_radius = 0
        self.margin = 0
        self.volume = 0
        self.inertia = []
        self.material_index = 0
        self.material_color_index = 0
        self.procedural_id = 0
        self.room_id = 0
        self.ped_density = 0
        self.unk_flags = 0
        self.poly_flags = 0
        self.unk_type = 0

    def read_xml(self, root):
        self.box_min = xmlhelper.ReadVector(root.find("BoxMin"))
        self.box_max = xmlhelper.ReadVector(root.find("BoxMax"))
        self.box_center = xmlhelper.ReadVector(root.find("BoxCenter"))
        self.sphere_center = xmlhelper.ReadVector(root.find("SphereCenter"))
        self.sphere_radius = xmlhelper.ReadFloat(root.find("SphereRadius"))
        self.margin = xmlhelper.ReadFloat(root.find("Margin"))
        self.volume = xmlhelper.ReadFloat(root.find("Volume"))
        self.inertia = xmlhelper.ReadVector(root.find("Inertia"))
        self.material_index = xmlhelper.ReadInt(root.find("MaterialIndex"))
        self.material_color_index = xmlhelper.ReadInt(root.find("MaterialColourIndex"))
        self.procedural_id = xmlhelper.ReadInt(root.find("ProceduralID"))
        self.room_id = xmlhelper.ReadInt(root.find("RoomID"))
        self.ped_density = xmlhelper.ReadFloat(root.find("PedDensity"))
        self.unk_flags = xmlhelper.ReadInt(root.find("UnkFlags"))
        self.poly_flags = xmlhelper.ReadInt(root.find("PolyFlags"))
        self.unk_type = xmlhelper.ReadInt(root.find("UnkType"))

class Poly():

    def __init__(self):
        self.type = ""
        self.material_index = 0

    def read_xml(self, root):
        self.type = root.tag 
        self.material_index = int(root.attrib["m"])

        if(self.type == "Triangle"):
            self.v1 = int(root.attrib["v1"])
            self.v2 = int(root.attrib["v2"])
            self.v3 = int(root.attrib["v3"])
            self.f1 = int(root.attrib["f1"])
            self.f2 = int(root.attrib["f2"])
            self.f3 = int(root.attrib["f3"])

        if(self.type == "Sphere"):
            self.v = int(root.attrib["v"]) 
            self.radius = float(root.attrib["radius"]) 
        
        if(self.type == "Capsule"):
            self.v1 = int(root.attrib["v1"])
            self.v2 = int(root.attrib["v2"])
            self.radius = float(root.attrib["radius"]) 

        if(self.type == "Box"):
            self.v1 = int(root.attrib["v1"])
            self.v2 = int(root.attrib["v2"])
            self.v3 = int(root.attrib["v3"])
            self.v4 = int(root.attrib["v4"])
        
        if(self.type == "Cylinder"):
            self.v1 = int(root.attrib["v1"])
            self.v2 = int(root.attrib["v2"])
            self.radius = float(root.attrib["radius"]) 

class PolyMaterial():

    def __init__(self):
        self.type = 0
        self.procedural_id = 0
        self.room_id = 0
        self.ped_density = 0
        self.flags = []
        self.material_color_index = 0
        self.unk = 0

    def read_xml(self, root):
        self.type = xmlhelper.ReadInt(root.find("Type"))
        self.procedural_id = xmlhelper.ReadInt(root.find("ProceduralID"))
        self.room_id = xmlhelper.ReadInt(root.find("RoomID"))
        self.ped_density = xmlhelper.ReadInt(root.find("PedDensity"))
        self.flags = root.find("Flags").text.split()
        self.material_color_index = xmlhelper.ReadInt(root.find("MaterialColourIndex"))
        self.unk = xmlhelper.ReadInt(root.find("Unk"))

class Bound(BoundBase):

    def __init__(self):
        self.type = ""
        #self.children = []
        #self.composite_position = []
        #self.composite_rotation = []
        #self.composite_scale = []
        #self.composite_flags1 = []
        #self.composite_flags2 = []
        #self.polys = []
        #self.vertices = []
        #self.materials = []

    def read_geometry_bound(self, root, isbvh):
        self.isbvh = isbvh
        self.read_composite_transform(root)
        self.geometry_center = xmlhelper.ReadVector(root.find("GeometryCenter"))
        self.unk_float1 = xmlhelper.ReadFloat(root.find("UnkFloat1"))
        self.unk_float2 = xmlhelper.ReadFloat(root.find("UnkFloat2"))
        
        #read mats
        self.materials = []
        for node in root.find("Materials"):
            polymat = PolyMaterial()
            polymat.read_xml(node)
            self.materials.append(polymat)

        #read verts
        self.vertices = [] 
        verts = root.find("Vertices").text.strip().split('\n')
        for v in verts:
            self.vertices.append(xmlhelper.StringListToFloatList(v.strip().replace(',', '').split()))

        #read polys
        self.polygons = []
        for node in root.find("Polygons"):
            poly = Poly()
            poly.read_xml(node)
            self.polygons.append(poly)

    def read_composite_transform(self, root):
        self.composite_position = xmlhelper.ReadVector(root.find("CompositePosition"))
        self.composite_rotation = xmlhelper.ReadQuaternion(root.find("CompositeRotation"))
        self.composite_scale = xmlhelper.ReadVector(root.find("CompositeScale"))
        self.composite_flags1 = root.find("CompositeFlags1").text.split()
        self.composite_flags2 = root.find("CompositeFlags2").text.split()

    def read_xml(self, root):
        super().read_xml(root)

        self.type = root.attrib["type"]

        if(self.type == "Composite"):
            self.children = []
            for node in root.find("Children"):
                child = Bound()
                child.read_xml(node)
                self.children.append(child)

        if(self.type == "Box"):
            self.read_composite_transform(root)
        if(self.type == "Sphere"):
            self.read_composite_transform(root)
        if(self.type == "Capsule"):
            self.read_composite_transform(root)
        if(self.type == "Cylinder"):
            self.read_composite_transform(root)
        if(self.type == "Disc"):
            self.read_composite_transform(root)
        if(self.type == "Cloth"):
            self.read_composite_transform(root)
        if(self.type == "Geometry"):
            self.read_geometry_bound(root, False)
        if(self.type == "GeometryBVH"):
            self.read_geometry_bound(root, True)