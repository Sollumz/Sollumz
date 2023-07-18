import bpy
from ..sollumz_properties import SollumType
from ..sollumz_ui import SOLLUMZ_PT_OBJECT_PANEL
from . import operators as ycd_ops


def draw_clip_properties(self, context):
    obj = context.active_object
    if obj and obj.sollum_type == SollumType.CLIP:
        layout = self.layout

        clip_properties = obj.clip_properties

        layout.prop(clip_properties, "hash")
        layout.prop(clip_properties, "name")
        layout.prop(clip_properties, "duration")

        layout.operator(ycd_ops.SOLLUMZ_OT_clip_apply_nla.bl_idname,
                        text="Apply Clip to NLA")
        layout.operator(ycd_ops.SOLLUMZ_OT_clip_new_animation.bl_idname,
                        text="Add a new Animation Link")


def draw_animation_properties(self, context):
    obj = context.active_object
    if obj and obj.sollum_type == SollumType.ANIMATION:
        layout = self.layout

        animation_properties = obj.animation_properties

        layout.prop(animation_properties, "hash")
        layout.prop(animation_properties, "frame_count")


def draw_clip_dictionary_properties(self, context):
    obj = context.active_object
    if obj and obj.sollum_type == SollumType.CLIP_DICTIONARY:
        layout = self.layout

        clip_dict_properties = obj.clip_dict_properties

        layout.prop(clip_dict_properties, "armature")
        layout.prop(clip_dict_properties, "uv_obj")


class SOLLUMZ_PT_CLIP_ANIMATIONS(bpy.types.Panel):
    bl_label = "Linked Animations"
    bl_idname = "SOLLUMZ_PT_CLIP_ANIMATIONS"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_options = {"DEFAULT_CLOSED"}
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
            toolbox_animation.prop(clip_animation, "animation")
            toolbox_animation.prop(clip_animation, "start_frame")
            toolbox_animation.prop(clip_animation, "end_frame")

            delete_op = toolbox_animation.operator(
                ycd_ops.SOLLUMZ_OT_clip_delete_animation.bl_idname, text="Delete")
            delete_op.animation_index = animation_index


class SOLLUMZ_PT_ANIMATION_ACTIONS(bpy.types.Panel):
    bl_label = "Actions"
    bl_idname = "SOLLUMZ_PT_ANIMATION_ACTIONS"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_OBJECT_PANEL.bl_idname
    bl_order = 0

    @classmethod
    def poll(cls, context):
        obj = context.active_object

        if obj and obj.sollum_type == SollumType.ANIMATION:
            clip_dict = obj.parent.parent
            dict_properties = clip_dict.clip_dict_properties
            if dict_properties.armature != None and dict_properties.uv_obj == None:
                return True
            else:
                return False
        else:
            return False

    def draw(self, context):
        layout = self.layout

        obj = context.active_object

        animation_properties = obj.animation_properties

        layout.prop(animation_properties, "base_action")
        layout.prop(animation_properties, "root_motion_location_action")
        layout.prop(animation_properties, "root_motion_rotation_action")


class SOLLUMZ_PT_UV_ANIMATION_ACTIONS(bpy.types.Panel):
    bl_label = "UV Actions"
    bl_idname = "SOLLUMZ_PT_UV_ANIMATION_ACTIONS"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_OBJECT_PANEL.bl_idname
    bl_order = 1

    @classmethod
    def poll(cls, context):
        obj = context.active_object

        if obj and obj.sollum_type == SollumType.ANIMATION:
            clip_dict = obj.parent.parent
            dict_properties = clip_dict.clip_dict_properties
            if dict_properties.armature == None and dict_properties.uv_obj != None:
                return True
            else:
                return False
        else:
            return False

    def draw(self, context):
        obj = context.active_object
        layout = self.layout
        layout.prop(obj.uv_anim_materials, "material")


class SOLLUMZ_PT_ANIMATIONS_TOOL_PANEL(bpy.types.Panel):
    bl_label = "Animations"
    bl_idname = "SOLLUMZ_PT_ANIMATIONS_TOOL_PANEL"
    bl_category = "Sollumz Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 4

    def draw_header(self, context):
        self.layout.label(text="", icon="ARMATURE_DATA")

    def draw(self, context):
        layout = self.layout

        if len(bpy.context.selected_objects) > 0:
            active_object = bpy.context.selected_objects[0]

            if active_object.sollum_type == SollumType.CLIP or active_object.sollum_type == SollumType.ANIMATION or \
                    active_object.sollum_type == SollumType.ANIMATIONS or active_object.sollum_type == SollumType.CLIPS or \
                    active_object.sollum_type == SollumType.CLIP_DICTIONARY:
                layout.operator(ycd_ops.SOLLUMZ_OT_create_clip.bl_idname)
                layout.operator(ycd_ops.SOLLUMZ_OT_create_animation.bl_idname)

                if active_object.sollum_type == SollumType.ANIMATION:
                    layout.operator(
                        ycd_ops.SOLLUMZ_OT_animation_fill.bl_idname)
            else:
                row = layout.row(align=False)
                row.operator(
                    ycd_ops.SOLLUMZ_OT_create_clip_dictionary.bl_idname)
                row.prop(context.scene, "create_animation_type")
                row = layout.row()
                row.operator(
                    ycd_ops.SOLLUMZ_OT_create_uv_anim_node.bl_idname)
        else:
            layout.operator(
                ycd_ops.SOLLUMZ_OT_create_clip_dictionary.bl_idname)


def register():
    SOLLUMZ_PT_OBJECT_PANEL.append(draw_clip_properties)
    SOLLUMZ_PT_OBJECT_PANEL.append(draw_animation_properties)
    SOLLUMZ_PT_OBJECT_PANEL.append(draw_clip_dictionary_properties)


def unregister():
    SOLLUMZ_PT_OBJECT_PANEL.remove(draw_clip_properties)
    SOLLUMZ_PT_OBJECT_PANEL.remove(draw_animation_properties)
    SOLLUMZ_PT_OBJECT_PANEL.remove(draw_clip_dictionary_properties)
