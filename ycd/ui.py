import bpy
from ..sollumz_properties import SollumType
from ..sollumz_ui import SOLLUMZ_PT_OBJECT_PANEL
from .operators import *

def draw_clip_properties(self, context):
    obj = context.active_object
    if obj and obj.sollum_type == SollumType.CLIP:
        layout = self.layout

        clip_properties = obj.clip_properties

        layout.prop(clip_properties, 'hash')
        layout.prop(clip_properties, 'name')
        layout.prop(clip_properties, 'duration')

        layout.operator(SOLLUMZ_OT_CLIP_APPLY_NLA.bl_idname, text='Apply Clip to NLA')
        layout.operator(SOLLUMZ_OT_CLIP_NEW_ANIMATION.bl_idname, text='Add a new Animation Link')

def draw_animation_properties(self, context):
    obj = context.active_object
    if obj and obj.sollum_type == SollumType.ANIMATION:
        layout = self.layout

        animation_properties = obj.animation_properties

        layout.prop(animation_properties, 'hash')
        layout.prop(animation_properties, 'frame_count')

def draw_clip_dictionary_properties(self, context):
    obj = context.active_object
    if obj and obj.sollum_type == SollumType.CLIP_DICTIONARY:
        layout = self.layout

        clip_dict_properties = obj.clip_dict_properties

        layout.prop(clip_dict_properties, 'armature')


class SOLLUMZ_PT_CLIP_ANIMATIONS(bpy.types.Panel):
    bl_label = "Linked Animations"
    bl_idname = 'SOLLUMZ_PT_CLIP_ANIMATIONS'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = SOLLUMZ_PT_OBJECT_PANEL.bl_idname
    bl_order = 0

    @classmethod
    def poll(cls, context):
        obj = context.active_object

        return obj and obj.sollum_type == SollumType.CLIP

    def draw(self, context):
        layout = self.layout

        obj = context.active_object
        clip_properties = obj.clip_properties

        for animation_index, clip_animation in enumerate(clip_properties.animations):
            toolbox_animation = layout.box()
            toolbox_animation.prop(clip_animation, 'animation')
            toolbox_animation.prop(clip_animation, 'start_frame')
            toolbox_animation.prop(clip_animation, 'end_frame')

            delete_op = toolbox_animation.operator(SOLLUMZ_OT_CLIP_DELETE_ANIMATION.bl_idname, text='Delete')
            delete_op.animation_index = animation_index


class SOLLUMZ_PT_ANIMATION_ACTIONS(bpy.types.Panel):
    bl_label = "Actions"
    bl_idname = 'SOLLUMZ_PT_ANIMATION_ACTIONS'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = SOLLUMZ_PT_OBJECT_PANEL.bl_idname
    bl_order = 0

    @classmethod
    def poll(cls, context):
        obj = context.active_object

        return obj and obj.sollum_type == SollumType.ANIMATION

    def draw(self, context):
        layout = self.layout

        obj = context.active_object

        animation_properties = obj.animation_properties

        layout.prop(animation_properties, 'base_action')
        layout.prop(animation_properties, 'root_motion_location_action')
        layout.prop(animation_properties, 'root_motion_rotation_action')


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


def register():
    SOLLUMZ_PT_OBJECT_PANEL.append(draw_clip_properties)
    SOLLUMZ_PT_OBJECT_PANEL.append(draw_animation_properties)
    SOLLUMZ_PT_OBJECT_PANEL.append(draw_clip_dictionary_properties)


def unregister():
    SOLLUMZ_PT_OBJECT_PANEL.remove(draw_clip_properties)
    SOLLUMZ_PT_OBJECT_PANEL.remove(draw_animation_properties)
    SOLLUMZ_PT_OBJECT_PANEL.remove(draw_clip_dictionary_properties)
