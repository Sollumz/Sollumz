import bpy

class SOLLUMZ_OT_toggle_export(bpy.types.Operator):
    """Toggle object for export"""
    bl_idname = 'sollumz.toggle_export'
    bl_label = 'Toggle Export'

    def execute(self, context):
        aobj = bpy.context.active_object
        if(aobj == None):
            return {'CANCELLED'}
        
        aobj.enable_export = not aobj.enable_export


class SollumzExportHelper():
    """Export by directory"""
    bl_options = {"REGISTER"}
    sollum_type = bpy.props.StringProperty(name='Sollum Type')
    filename_ext = bpy.props.StringProperty(name='File Extension', description='File extension to be appended to exported file')
    # Define this to tell 'fileselect_add' that we want a directoy
    directory : bpy.props.StringProperty(
        name="Output directory",
        description="Select export output directory",
        subtype="DIR_PATH",
    )


    def export(self, obj):
        raise NotImplementedError


    def get_filepath(self, obj):
        return f"{self.directory}\{obj.name}{self.filename_ext}"
    

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}


    def export_all(self):
        objects = bpy.context.collection.objects

        found = False
        if len(objects) > 0:
            for obj in objects:
                print(self.sollum_type)
                if obj.sollum_type == self.sollum_type and obj.enable_export:
                    found = True
                    self.export(obj)

        if not found:
            self.report({'INFO'}, "No bound object types in scene for Sollumz export")
            return {'CANCELLED'}
        
        return {'FINISHED'}
