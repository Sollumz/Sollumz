import xml.etree.ElementTree as ET

import sys
import os

PACKAGE_PARENT = '..'
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))

import tools.xmlhelper as xmlhelper

class Texture:

    def __init__(self):
        self.name = "" #pull name from filename?
        self.unk32 = 0
        self.usage = [] #enum?
        self.usage_flags = [] #enum?
        self.extra_flags = 0
        self.width = 0
        self.height = 0
        self.miplevels = 0
        self.format = [] #enum?
        self.filename = ""

    def read_xml(self, root):
        self.name = root.find("Name").text
        self.unk32 = xmlhelper.ReadInt(root.find("Unk32"))
        self.usage = root.find("Usage").text #ENUM?
        self.usage_flags = root.find("UsageFlags").text
        self.extra_flags = xmlhelper.ReadInt(root.find("ExtraFlags"))
        self.width = xmlhelper.ReadInt(root.find("Width"))
        self.height = xmlhelper.ReadInt(root.find("Height"))
        self.miplevels = xmlhelper.ReadInt(root.find("MipLevels"))
        self.format = root.find("Format").text
        self.filename = root.find("FileName").text

class TextureDictionary:

    def __init__(self):
        self.textures = [] #of textures 

    def read_xml(self, root):
        for node in root:
            t = Texture()
            t.read_xml(node)
            self.textures.append(t)

class ShaderTextureParameter:

    def __init__(self):
        self.name = ""
        self.type = "" #enum?
        self.texture_name = ""

    def read_xml(self, root):
        self.name = root.attrib["name"]
        self.type = root.attrib["type"]
        self.texture_name = root.find("Name").text

class ShaderValueParameter:

    def __init__(self):
        self.name = ""
        self.type = "" #enum?
        self.quaternion = []

    def read_xml(self, root):
        self.name = root.attrib["name"]
        self.type = root.attrib["type"]
        self.quaternion = xmlhelper.ReadQuaternion(root)

class Shader:

    def __init__(self):
        self.name = ""
        self.filename = ""
        self.render_bucket = 0
        self.parameters = [] #texture parameters and value parameters

    def read_xml(self, root):
        self.name = root.find("Name").text
        self.filename = root.find("FileName").text
        self.render_bucket = xmlhelper.ReadFloat(root.find("RenderBucket"))
        
        for node in root.find("Parameters"):
            if(node.attrib["type"] == "Texture"):
                p = ShaderTextureParameter()
                p.read_xml(node)
                self.parameters.append(p)
            else:
                p = ShaderValueParameter()
                p.read_xml(node)
                self.parameters.append(p)

class ShaderGroup:

    def __init__(self):
        self.unknown_30 = 0
        self.texture_dictionary = None
        self.shaders = [] 
    
    def read_xml(self, root):
        self.unknown_30 = xmlhelper.ReadFloat(root.find("Unknown30"))

        node = root.find("TextureDictionary")

        if(node != None):
            texture_dictionary = TextureDictionary()
            texture_dictionary.read_xml(node)

            self.texture_dictionary = texture_dictionary

        for node in root.find("Shaders"):
            s = Shader()
            s.read_xml(node)
            self.shaders.append(s)

class Bone:

    def __init__(self):
        self.name = ""
        self.tag = 0
        self.index = 0
        self.parent_index = 0
        self.sibling_index =0 
        self.flags = ""
        self.translation = []
        self.rotation = []
        self.scale = []
        self.transform_unk = []

    def read_xml(self, root):
        self.name = root.find("Name").text
        self.tag = xmlhelper.ReadInt(root.find("Tag"))
        self.index = xmlhelper.ReadInt(root.find("Index"))
        self.parent_index = xmlhelper.ReadFloat(root.find("ParentIndex"))
        self.sibling_index = xmlhelper.ReadFloat(root.find("SiblingIndex"))
        self.flags = root.find("Flags").text
        self.translation = xmlhelper.ReadVector(root.find("Translation"))
        self.rotation = xmlhelper.ReadQuaternion(root.find("Rotation"))
        self.scale = xmlhelper.ReadVector(root.find("Scale"))
        self.transform_unk = xmlhelper.ReadQuaternion(root.find("TransformUnk"))

class Skeleton:

    def __init__(self):
        self.unknown_1c = 0
        self.unknown_50 = 0
        self.unknown_54 = 0
        self.unknown_58 = 0
        self.bones = []

    def read_xml(self, root):
        self.unknown_1c = xmlhelper.ReadInt(root.find("Unknown1C"))
        self.unknown_50 = xmlhelper.ReadInt(root.find("Unknown50"))
        self.unknown_54 = xmlhelper.ReadInt(root.find("Unknown54"))
        self.unknown_58 = xmlhelper.ReadInt(root.find("Unknown58"))

        for node in root.find("Bones"):
            b = Bone()
            b.read_xml(node)
            self.bones.append(b)

class Vertex:

    def __init__(self):
        self.position = None
        self.blendweights = None
        self.blendindicies = None
        self.colors0 = None
        self.colors1 = None
        self.texcoord0 = None
        self.texcoord1 = None
        self.texcoord2 = None
        self.texcoord3 = None
        self.texcoord4 = None
        self.texcoord5 = None
        self.texcoord6 = None
        self.texcoord7 = None
        self.tangent = None
        self.normal = None

    @staticmethod    
    def from_xml(layout, data):
        
        result = Vertex()

        for i in range(len(layout)):
            current_data = xmlhelper.StringListToFloatList(data[i].split())
            current_layout_key = layout[i]
            if(current_layout_key == "Position"):
                result.position = current_data
            elif(current_layout_key == "BlendWeights"):
                result.blendweights = current_data
            elif(current_layout_key == "BlendIndicies"):
                result.blendindicies = current_data
            elif(current_layout_key == "Colour0"):
                result.colors0 = current_data
            elif(current_layout_key == "Colour1"):
                result.colors1 = current_data
            elif(current_layout_key == "TexCoord0"):
                result.texcoord0 = current_data
            elif(current_layout_key == "TexCoord1"):
                result.texcoord1 = current_data
            elif(current_layout_key == "TexCoord2"):
                result.texcoord2 = current_data
            elif(current_layout_key == "TexCoord3"):
                result.texcoord3 = current_data
            elif(current_layout_key == "TexCoord4"):
                result.texcoord4 = current_data
            elif(current_layout_key == "TexCoord5"):
                result.texcoord5 = current_data
            elif(current_layout_key == "TexCoord6"):
                result.texcoord6 = current_data
            elif(current_layout_key == "TexCoord7"):
                result.texcoord7 = current_data
            elif(current_layout_key == "Tangent"):
                result.tangent = current_data
            elif(current_layout_key == "Normal"):
                result.normal = current_data

        return result

class VertexBuffer:

    def __init__(self):
        self.flags = 0
        self.layout = []
        self.data = ""
        self.vertices = []

    def read_xml(self, root):
        self.flags = xmlhelper.ReadInt(root.find("Flags"))

        layout = root.find("Layout")
        for node in layout:
            self.layout.append(node.tag)

        self.data = root.find("Data").text.strip()

        lines = self.data.split("\n")
        for line in lines:
            v = Vertex.from_xml(self.layout, line.strip().split(" " * 3))
            self.vertices.append(v)

class Geometry:

    def __init__(self):
        self.shader_index = 0
        self.bounding_box_min = []
        self.bounding_box_max = []
        self.vertex_buffer = "" 
        self.index_buffer = []

    def read_xml(self, root):
        self.shader_index = xmlhelper.ReadInt(root.find("ShaderIndex"))
        self.bounding_box_min = xmlhelper.ReadVector(root.find("BoundingBoxMin"))
        self.bounding_box_max = xmlhelper.ReadVector(root.find("BoundingBoxMax"))

        vb = VertexBuffer()
        vb.read_xml(root.find("VertexBuffer"))
        self.vertex_buffer = vb
        
        index_buffer = root.find("IndexBuffer")[0].text.strip().replace("\n", "").split()
        
        i_buf = []
        for num in index_buffer:
            i_buf.append(int(num))

        self.index_buffer = [i_buf[i * 3:(i + 1) * 3] for i in range((len(i_buf) + 3 - 1) // 3 )] #split index buffer into 3s for each triangle

class DrawableModel:

    def __init__(self):
        self.render_mask = 0
        self.flags = 0
        self.has_skin = False
        self.bone_index = 0
        self.unknown_1 = 0
        self.geometries = [] 

    def read_xml(self, root):
        self.render_mask = xmlhelper.ReadInt(root.find("RenderMask"))
        self.flags = xmlhelper.ReadInt(root.find("Flags"))
        if(xmlhelper.ReadFloat(root.find("HasSkin")) == 1):
            self.has_skin = True
        self.bone_index = xmlhelper.ReadInt(root.find("BoneIndex"))
        self.unknown_1 = xmlhelper.ReadInt(root.find("Unknown1"))

        for node in root.find("Geometries"):
            g = Geometry()
            g.read_xml(node)
            self.geometries.append(g)

class Drawable:

    def __init__(self):
        self.name = ""
        self.bounding_sphere_center = [0, 0, 0]
        self.bounding_sphere_radius = 0
        self.bounding_box_min = [0, 0, 0]
        self.bounding_box_max = [0, 0, 0]
        self.lod_dist_high = 0 #9998?
        self.lod_dist_med= 0 #9998?
        self.lod_dist_low = 0 #9998?
        self.lod_dist_vlow = 0 #9998?
        self.flags_high = 0 
        self.flags_med = 0 
        self.flags_low = 0  
        self.flags_vlow = 0
        self.unknown_9A = 0

        self.skeleton = None
        self.shader_group = None
        self.drawable_models_high = []
        self.drawable_models_med = []
        self.drawable_models_low = []
        self.drawable_models_vlow = []

    def read_xml(self, root):
        self.name = root.find("Name").text
        self.bounding_sphere_center = xmlhelper.ReadVector(root.find("BoundingSphereCenter"))
        self.bounding_sphere_radius = xmlhelper.ReadFloat(root.find("BoundingSphereRadius"))
        self.bounding_box_min = xmlhelper.ReadVector(root.find("BoundingBoxMin"))
        self.bounding_box_max = xmlhelper.ReadVector(root.find("BoundingBoxMax"))
        self.lod_dist_high = xmlhelper.ReadFloat(root.find("LodDistHigh"))
        self.lod_dist_med = xmlhelper.ReadFloat(root.find("LodDistMed"))
        self.lod_dist_low = xmlhelper.ReadFloat(root.find("LodDistLow"))
        self.lod_dist_vlow = xmlhelper.ReadFloat(root.find("LodDistVlow"))
        self.flags_high = xmlhelper.ReadFloat(root.find("FlagsHigh"))
        self.flags_med = xmlhelper.ReadFloat(root.find("FlagsMed"))
        self.flags_low = xmlhelper.ReadFloat(root.find("FlagsLow"))
        self.flags_vlow = xmlhelper.ReadFloat(root.find("FlagsVlow"))
        self.unknown_9A = xmlhelper.ReadFloat(root.find("Unknown9A"))

        sg = root.find("ShaderGroup")
        if(sg != None):
            shader_group = ShaderGroup()
            shader_group.read_xml(root.find("ShaderGroup"))
            self.shader_group = shader_group
        
        skel = root.find("Skeleton")
        if(skel != None):
            skeleton = Skeleton()
            skeleton.read_xml(skel)
            self.skeleton = skeleton

        dmh = root.find("DrawableModelsHigh")
        if(dmh != None):
            for node in dmh:
                dm = DrawableModel()
                dm.read_xml(node)
                self.drawable_models_high.append(dm)

        dmm = root.find("DrawableModelsMed")
        if(dmm != None):
            for node in dmm:
                dm = DrawableModel()
                dm.read_xml(node)
                self.drawable_models_med.append(dm)

        dml = root.find("DrawableModelsLow")
        if(dml != None):
            for node in dml:
                dm = DrawableModel()
                dm.read_xml(node)
                self.drawable_models_low.append(dm)

        dmvl = root.find("DrawableModelsVlow")
        if(dmvl != None):
            for node in dmvl:
                dm = DrawableModel()
                dm.read_xml(node)
                self.drawable_models_vlow.append(dm)