import bpy
from ..sollumz_properties import SollumType
from .operators import *

class SOLLUMZ_PT_ANIM_PANEL(bpy.types.Panel):
    bl_label = "Sollumz Animation"
    bl_idname = "SOLLUMZ_PT_ANIM_PANEL"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_options = {'DEFAULT_CLOSED'}
    bl_context = 'object'

    @classmethod
    def poll(cls, context):

        if len(bpy.context.selected_objects) > 0:
            active_object = bpy.context.selected_objects[0]

            if active_object.sollum_type == SollumType.CLIP or active_object.sollum_type == SollumType.ANIMATION or \
                active_object.sollum_type == SollumType.CLIP_DICTIONARY:

                return True

        return False

    def draw(self, context):
        layout = self.layout

        if len(bpy.context.selected_objects) <= 0:
            layout.label(text = "No objects selected")
            return

        active_object = bpy.context.selected_objects[0]

        if active_object.sollum_type != SollumType.CLIP and active_object.sollum_type != SollumType.ANIMATION and \
            active_object.sollum_type != SollumType.CLIP_DICTIONARY:
            layout.label(text='Selected object has no animation meta')

            return

        if active_object.sollum_type == SollumType.CLIP:
            clip_properties = active_object.clip_properties

            toolbox = layout.box()
            toolbox.label(text='Clip')

            toolbox.prop(clip_properties, 'hash')
            toolbox.prop(clip_properties, 'name')

            toolbox.prop(clip_properties, 'duration')

            toolbox.operator(SOLLUMZ_OT_CLIP_APPLY_NLA.bl_idname, text='Apply clip to NLA')
            toolbox.operator(SOLLUMZ_OT_CLIP_NEW_ANIMATION.bl_idname, text='New animation')

            for clip_animation in clip_properties.animations:
                toolbox_animation = toolbox.box()
                toolbox_animation.prop(clip_animation, 'animation')
                toolbox_animation.prop(clip_animation, 'start_frame')
                toolbox_animation.prop(clip_animation, 'end_frame')

                delete_op = toolbox_animation.operator(SOLLUMZ_OT_CLIP_DELETE_ANIMATION.bl_idname, text='Delete')
                delete_op.animation_hash = clip_animation.animation.animation_properties.hash
        elif active_object.sollum_type == SollumType.ANIMATION:
            animation_properties = active_object.animation_properties

            toolbox = layout.box()
            toolbox.label(text='Animation')
            toolbox.prop(animation_properties, 'hash')
            toolbox.prop(animation_properties, 'frame_count')
            toolbox.prop(animation_properties, 'base_action')
            toolbox.prop(animation_properties, 'root_motion_location_action')
            toolbox.prop(animation_properties, 'root_motion_rotation_action')
        elif active_object.sollum_type == SollumType.CLIP_DICTIONARY:
            clip_dict_properties = active_object.clip_dict_properties

            toolbox = layout.box()
            toolbox.prop(clip_dict_properties, 'armature')


class SOLLUMZ_PT_ANIMATIONS_TOOL_PANEL(bpy.types.Panel):
    bl_label = "Animations Tools"
    bl_idname = "SOLLUMZ_PT_ANIMATIONS_TOOL_PANEL"
    bl_category = "Sollumz Tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 1

    @classmethod
    def poll(cls, context):

        if len(bpy.context.selected_objects) > 0:
            active_object = bpy.context.selected_objects[0]

            if active_object.sollum_type == SollumType.CLIP or active_object.sollum_type == SollumType.ANIMATION or \
                active_object.sollum_type == SollumType.ANIMATIONS or active_object.sollum_type == SollumType.CLIPS or \
                active_object.sollum_type == SollumType.CLIP_DICTIONARY or isinstance(active_object.data, bpy.types.Armature):

                return True

        return False

    def draw_header(self, context):
        self.layout.label(text="", icon="ARMATURE_DATA")

    def draw(self, context):
        layout = self.layout

        if len(bpy.context.selected_objects) > 0:
            active_object = bpy.context.selected_objects[0]

            if active_object.sollum_type == SollumType.CLIP or active_object.sollum_type == SollumType.ANIMATION or \
                active_object.sollum_type == SollumType.ANIMATIONS or active_object.sollum_type == SollumType.CLIPS or \
                active_object.sollum_type == SollumType.CLIP_DICTIONARY:
                    layout.operator(SOLLUMZ_OT_CREATE_CLIP.bl_idname)
                    layout.operator(SOLLUMZ_OT_CREATE_ANIMATION.bl_idname)

                    if (active_object.sollum_type == SollumType.ANIMATION):
                        layout.operator(SOLLUMZ_OT_ANIMATION_FILL.bl_idname)
            else:
                layout.operator(SOLLUMZ_OT_CREATE_CLIP_DICTIONARY.bl_idname)
        else:
            layout.operator(SOLLUMZ_OT_CREATE_CLIP_DICTIONARY.bl_idname)
