import bpy
from ..sollumz_helper import SOLLUMZ_OT_base
from ..sollumz_properties import SOLLUMZ_UI_NAMES, SollumType
from ..tools.blenderhelper import create_empty_object, get_children_recursive
from ..tools.boundhelper import convert_selected_to_bound
from ..tools.fragmenthelper import convert_selected_to_fragment


class SOLLUMZ_OT_create_fragment(SOLLUMZ_OT_base, bpy.types.Operator):
    """Create a sollumz fragment of the selected type."""
    bl_idname = "sollumz.createfragment"
    bl_label = f"Create fragment"
    bl_action = "Create a fragment"
    bl_update_view = True


    def run(self, context):
        aobj = context.active_object
        selected = context.selected_objects
        fragment_type = context.scene.create_fragment_type
        if fragment_type == SollumType.FRAGMENT and len(selected) > 0:
            # converts selected object to fragment if an object is selected and a fragment type is selected in the fragment tools panel
            dobjs = convert_selected_to_fragment(
                selected, context.scene.use_mesh_name, context.scene.create_seperate_objects, context.scene.create_center_to_selection)
                # converts object to fragment and checks what options are selected
            if context.scene.auto_create_embedded_col:
                cobjs = convert_selected_to_bound(
                    context.selected_objects, use_name=False, multiple=context.scene.create_seperate_objects, bvhs=True, replace_original=False, do_center=False)
                    # if auto embedded collision option is selected
                for index, composite in enumerate(cobjs):
                    composite.parent = dobjs[index]
                    # sets bound composite's parent to drawable object
                    if context.scene.create_center_to_selection:
                        for child in get_children_recursive(composite):
                            if child.type == "MESH":
                                child.location -= dobjs[index].location
                                # sets object location to center of the selected object

            self.message(
                f"Succesfully converted {', '.join([obj.name for obj in context.selected_objects])} to a {SOLLUMZ_UI_NAMES[SollumType.DRAWABLE]}.")
            return True
        else:
            obj = create_empty_object(fragment_type)
            if aobj:
                obj.parent = aobj
            return True