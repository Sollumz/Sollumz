import bpy
from ..sollumz_properties import SollumType
from ..sollumz_ui import SOLLUMZ_PT_OBJECT_PANEL
from . import operators as ycd_ops
from .properties import AnimationTracks
from ..ydr.ui import SOLLUMZ_PT_BONE_PANEL

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


animation_target_id_type_to_collection_name = {
    "ARMATURE": "armatures",
    "CAMERA": "cameras",
    "DRAWABLE_GEOMETRY": "meshes",
}


# https://blender.stackexchange.com/a/293222
def template_animation_target_ID(layout: bpy.types.UILayout, data, property: str, type_property: str,
                    text: str = "", text_ctxt: str = "", translate: bool = True):
    split = layout.split(factor=0.33)

    # FIRST PART
    row = split.row()

    # Label - either use the provided text, or will become "ID-Block:"
    if text != "":
        row.label(text=text, text_ctxt=text_ctxt, translate=translate)
    elif data.bl_rna.properties[property].name != "":
        row.label(text=data.bl_rna.properties[property].name, text_ctxt=text_ctxt, translate=translate)
    else:
        row.label(text="ID-Block:")

    # SECOND PART
    row = split.row(align=True)

    # ID-Type Selector - just have a menu of icons

    # HACK: special group just for the enum,
    # otherwise we get ugly layout with text included too...
    sub = row.row(align=True)
    sub.alignment = "LEFT"

    sub.prop(data, type_property, icon_only=True)

    # ID-Block Selector - just use pointer widget...

    # HACK: special group to counteract the effects of the previous enum,
    # which now pushes everything too far right.
    sub = row.row(align=True)
    sub.alignment = "EXPAND"

    type_name = getattr(data, type_property)
    if type_name in animation_target_id_type_to_collection_name:
        icon = data.bl_rna.properties[type_property].enum_items[type_name].icon
        sub.prop_search(data, property, bpy.data, animation_target_id_type_to_collection_name[type_name],
                        text="", icon=icon)


def draw_animation_properties(self, context):
    obj = context.active_object
    if obj and obj.sollum_type == SollumType.ANIMATION:
        layout = self.layout

        animation_properties = obj.animation_properties

        layout.prop(animation_properties, "hash")
        layout.prop(animation_properties, "frame_count")
        layout.prop(animation_properties, "action")
        r = layout.row()
        r.use_property_split = True
        r.use_property_decorate = False
        template_animation_target_ID(r, animation_properties, "target_id", "target_id_type")


def draw_clip_dictionary_properties(self, context):
    obj = context.active_object
    if obj and obj.sollum_type == SollumType.CLIP_DICTIONARY:
        layout = self.layout

        clip_dict_properties = obj.clip_dict_properties

        layout.prop(clip_dict_properties, "armature")
        layout.prop(clip_dict_properties, "uv_obj")


class SOLLUMZ_PT_OBJECT_ANIMATION_TRACKS(bpy.types.Panel):
    bl_label = "Animation Tracks"
    bl_idname = "SOLLUMZ_PT_OBJECT_ANIMATION_TRACKS"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_OBJECT_PANEL.bl_idname

    @classmethod
    def poll(cls, context):
        return context.active_object is not None  # and obj.sollum_type == SollumType.DRAWABLE

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        animation_tracks = context.active_object.animation_tracks
        for prop in AnimationTracks.__annotations__:
            layout.prop(animation_tracks, prop)


class SOLLUMZ_PT_POSE_BONE_ANIMATION_TRACKS(bpy.types.Panel):
    bl_label = "Animation Tracks"
    bl_idname = "SOLLUMZ_PT_POSE_BONE_ANIMATION_TRACKS"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "bone"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_BONE_PANEL.bl_idname

    @classmethod
    def poll(cls, context):
        return context.active_pose_bone is not None

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        p_bone = context.active_pose_bone
        # animation_tracks = context.active_pose_bone.animation_tracks
        for prop in AnimationTracks.__annotations__:
            layout.prop(p_bone, f"animation_tracks_{prop}")


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
