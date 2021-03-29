import bpy
import os
import xml.etree.ElementTree as ET
from mathutils import Vector, Quaternion
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator
import time
import random 
from .tools import cats as Cats
from .ydrimport import read_ydr_xml, read_ydr_shaders, build_bones_dict
from .ybnimport import read_composite_info

class ImportYFT(Operator, ImportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "importxml.yft"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Import Yft"

    # ImportHelper mixin class uses this
    filename_ext = ".yft.xml"

    filter_glob: StringProperty(
        default="*.yft.xml",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def execute(self, context):
        start = time.time()

        tree = ET.parse(self.filepath)
        root = tree.getroot()

        fragment_name = root.find("Name").text

        armature = bpy.data.armatures.new(fragment_name + ".skel")
        node_fragment = bpy.data.objects.new(fragment_name, armature)
        context.scene.collection.objects.link(node_fragment)
        context.view_layer.objects.active = node_fragment

        # Drawable
        drawable = root.find('Drawable')
        shaders = read_ydr_shaders(self, context, self.filepath, drawable)
        ydr_objs = read_ydr_xml(self, context, self.filepath, drawable, shaders)
        node_fragment.sollumtype = "Fragment"

        for obj in ydr_objs:
            context.scene.collection.objects.link(obj)
            obj.parent = node_fragment
            mod = obj.modifiers.new("Armature", 'ARMATURE')
            mod.object = node_fragment

        # Physics
        Physics = root.find('Physics')
        LOD1 = Physics.find('LOD1')
        node_physics = bpy.data.objects.new('Physics', None)
        context.scene.collection.objects.link(node_physics)
        node_physics.parent = node_fragment

        node_lod1 = bpy.data.objects.new('LOD1', None)
        context.scene.collection.objects.link(node_lod1)
        node_lod1.parent = node_physics

        # Collision
        archetype = LOD1.find('Archetype')

        if archetype != None:
            node_archetype = bpy.data.objects.new('Archetype', None)
            context.scene.collection.objects.link(node_archetype)
            node_archetype.parent = node_lod1

            archetype_name = archetype.find('Name').text
            bounds = archetype.find('Bounds')
            
            node_bounds = read_composite_info(archetype_name, bounds)
            context.scene.collection.objects.link(node_bounds)
            node_bounds.parent = node_archetype

        bones_dict = build_bones_dict(node_fragment)

        for item in LOD1.find('Children').getchildren():

            bone_tag = int(item.find('BoneTag').get('value'))

            loc = armature.bones[bones_dict[bone_tag]].head

            node_item = bpy.data.objects.new('Item', None)
            context.scene.collection.objects.link(node_item)
            node_item.parent = node_lod1

            item_drawable = item.find('Drawable')
            ydr_objs = read_ydr_xml(self, context, self.filepath, item_drawable, shaders)
            # matrix = list(map(lambda line : line.strip().split(), item_drawable.find('Matrix').text.strip().split('\n')))

            node_item.location = loc # should be somehow offsetted
            

            for obj in ydr_objs:
                context.scene.collection.objects.link(obj)
                obj.parent = node_item
                mod = obj.modifiers.new("Armature", 'ARMATURE')
                mod.object = node_fragment

        finished = time.time()
        
        difference = finished - start
        
        print("start time: " + str(start))
        print("end time: " + str(finished))
        print("difference in seconds: " + str(difference))
        print("difference in milliseconds: " + str(difference * 1000))
                
        return {'FINISHED'}

# Only needed if you want to add into a dynamic menu
def menu_func_import_yft(self, context):
    self.layout.operator(ImportYFT.bl_idname, text="Yft (.yft.xml)")

def register():
    bpy.utils.register_class(ImportYFT)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import_yft)

def unregister():
    bpy.utils.unregister_class(ImportYFT)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import_yft)
