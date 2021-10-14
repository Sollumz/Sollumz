import bpy
from bpy_extras.io_utils import ImportHelper
import os, traceback
from mathutils import Vector, Quaternion, Matrix
from Sollumz.resources.drawable import *
from Sollumz.ydr.ydrimport import drawable_to_obj

def drawable_dict_to_obj(drawable_dict, filepath):

    name = os.path.basename(filepath)[:-8]
    vmodels = []
    # bones are shared in single ydd however they still have to be placed under a paticular drawable

    armature_with_skel_obj = None
    mod_objs = []
    drawable_with_skel = None
    for drawable in drawable_dict.value:
        if len(drawable.skeleton.bones) > 0:
            drawable_with_skel = drawable
            break

    for drawable in drawable_dict.value:
        drawable_obj = drawable_to_obj(drawable, filepath, drawable.name, bones_override=drawable_with_skel.skeleton.bones)
        if (armature_with_skel_obj is None and drawable_with_skel is not None and drawable.skeleton is not None):
            armature_with_skel_obj = drawable_obj

        for drawable_model in drawable_obj.children:
            for geo in drawable_model.children:
                mod_objs.append(geo)
            
        vmodels.append(drawable_obj)
    
    dict_obj = bpy.data.objects.new(name, None)
    dict_obj.sollum_type = "sollumz_drawable_dictionary"

    for vmodel in vmodels:
        vmodel.parent = dict_obj
    
    bpy.context.collection.objects.link(dict_obj)

    if (armature_with_skel_obj is not None):
        for obj in mod_objs:
            mod = obj.modifiers.get("Armature")
            if mod is None:
                continue

            mod.object = armature_with_skel_obj

    return dict_obj

class ImportYddXml(bpy.types.Operator, ImportHelper):
    """Imports .ydd.xml file exported from codewalker."""
    bl_idname = "sollumz.importydd" 
    bl_label = "Import ydd.xml"
    filename_ext = ".ydd.xml"

    filter_glob: bpy.props.StringProperty(
        default="*.ydd.xml",
        options={'HIDDEN'},
        maxlen=255,  
    )

    def execute(self, context):
        
        try:
            ydd_xml = YDD.from_xml_file(self.filepath)
            drawable_dict_to_obj(ydd_xml, self.filepath)
            self.report({'INFO'}, 'YDD Successfully imported.')
        except Exception as e:
            self.report({'ERROR'}, traceback.format_exc())

        return {'FINISHED'}

def ydd_menu_func_import(self, context):
    self.layout.operator(ImportYddXml.bl_idname, text="Import .ydd.xml")

def register():
    bpy.types.TOPBAR_MT_file_import.append(ydd_menu_func_import)

def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(ydd_menu_func_import)