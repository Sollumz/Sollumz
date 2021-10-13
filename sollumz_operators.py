import bpy

class SollumzExportHelper():
    """Export by directory"""
    bl_options = {"REGISTER"}
    filename_ext = bpy.props.StringProperty(name='File Extension', description='File extension to be appended to exported file')
    # Define this to tell 'fileselect_add' that we want a directoy
    directory: bpy.props.StringProperty(
        name="Output directory",
        description="Select export output directory",
        subtype="DIR_PATH",
    )

    def get_filepath(self, obj):
        return f"{self.directory}\{obj.name}{self.filename_ext}"
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}