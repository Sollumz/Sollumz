import bpy
import numpy as np
from ..sollumz_properties import SollumType, MaterialType
from ..sollumz_ui import SOLLUMZ_PT_OBJECT_PANEL, SOLLUMZ_PT_MAT_PANEL
from . import operators as ycd_ops
from .properties import AnimationTracks
from ..ydr.ui import SOLLUMZ_PT_BONE_PANEL
from ..tools.animationhelper import is_any_sollumz_animation_obj

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


animation_target_id_type_to_collection_name = {
    "ARMATURE": "armatures",
    "CAMERA": "cameras",
    "MATERIAL": "materials",
}


# https://blender.stackexchange.com/a/293222
def template_animation_target_ID(layout: bpy.types.UILayout, data, property: str, type_property: str,
                    text: str = "", text_ctxt: str = "", translate: bool = True):
    split = layout.split(factor=0.33, align=True)

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
        layout.prop(animation_properties, "action")
        r = layout.row()
        r.use_property_split = True
        r.use_property_decorate = False
        template_animation_target_ID(r, animation_properties, "target_id", "target_id_type")

def draw_clip_dictionary_properties(self, context):
    obj = context.active_object
    if obj and obj.sollum_type == SollumType.CLIP_DICTIONARY:
        layout = self.layout

        # nothing currently


def draw_range_properties(layout, obj, prop_start, prop_end, label):
    """Draw two properties in a row aligned to each other, with label on the left."""
    split = layout.split(factor=0.4, align=True)
    label_row = split.row()
    label_row.alignment = 'RIGHT'
    label_row.label(text=label)
    value_row = split.row(align=True)
    value_row.use_property_split = False
    value_row.prop(obj, prop_start, text="Start")
    value_row.prop(obj, prop_end, text="End")


def draw_item_box_header(
        layout, obj, label, delete_op_cls,
        show_expanded_prop="ui_show_expanded",
        visible_prop=None,
        color_prop=None
):
    """
    Draw a box header with a 'expand' button, label, optional visibility toggle, optional color picker
    and 'delete' button.
    Returns the delete operator properties to fill in.
    """
    header = layout.row(align=True)
    is_expanded = getattr(obj, show_expanded_prop)
    expanded_icon = "DISCLOSURE_TRI_DOWN" if is_expanded else "DISCLOSURE_TRI_RIGHT"
    header.prop(obj, show_expanded_prop, text="", emboss=False, icon=expanded_icon)
    if label:
        header.label(text=label)
    else:
        header.label(text="Not Set")

    if visible_prop is not None:
        is_visible = getattr(obj, visible_prop)
        visible_icon = "HIDE_OFF" if is_visible else "HIDE_ON"
        header.prop(obj, visible_prop, text="", emboss=False, icon=visible_icon)

    if color_prop is not None:
        row = header.row()
        row.scale_x = 0.35  # make the color picker smaller
        row.prop(obj, color_prop, text="")

    delete_op = header.operator(delete_op_cls.bl_idname,
                                text="", emboss=False, icon="X")
    return delete_op


def draw_clip_attribute(layout, attr, delete_op_cls):
    split = layout.split(factor=0.6)
    left_row = split.row(align=True)
    left_row.prop(attr, "name", text="")
    left_row.prop(attr, "type", text="")
    right_row = split.row()
    if attr.type == "Float":
        right_row.prop(attr, "value_float", text="")
    elif attr.type == "Int":
        right_row.prop(attr, "value_int", text="")
    elif attr.type == "Bool":
        right_row.alignment = "RIGHT"
        right_row.prop(attr, "value_bool", text="")
    elif attr.type == "Vector3":
        right_row.prop(attr, "value_vec3", text="")
    elif attr.type == "Vector4":
        right_row.prop(attr, "value_vec4", text="")
    elif attr.type == "String":
        right_row.prop(attr, "value_string", text="")
    elif attr.type == "HashString":
        right_row.prop(attr, "value_string", text="")

    del_op = right_row.operator(delete_op_cls.bl_idname,
                                text="", emboss=False, icon='X')
    return del_op


class SOLLUMZ_UL_uv_transforms_list(bpy.types.UIList):
    bl_idname = "SOLLUMZ_UL_uv_transforms_list"

    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        split = layout.split(factor=0.25)
        split.use_property_split = False

        row = split.row(align=True)
        row.label(icon="DRIVER_TRANSFORM")
        row.prop(item, "mode", text="", emboss=False)

        row = split.row(align=True)
        if item.mode == "TRANSLATE":
            row.prop(item, "translation", text="X", index=0)
            row.prop_decorator(item, "translation", index=0)
            row.prop(item, "translation", text="Y", index=1)
            row.prop_decorator(item, "translation", index=1)
        elif item.mode == "ROTATE":
            row.prop(item, "rotation", text="")
            row.prop_decorator(item, "rotation")
        elif item.mode == "SCALE":
            row.prop(item, "scale", text="X", index=0)
            row.prop_decorator(item, "scale", index=0)
            row.prop(item, "scale", text="Y", index=1)
            row.prop_decorator(item, "scale", index=1)
        elif item.mode == "SHEAR":
            row.prop(item, "shear", text="X", index=0)
            row.prop_decorator(item, "shear", index=0)
            row.prop(item, "shear", text="Y", index=1)
            row.prop_decorator(item, "shear", index=1)
        elif item.mode == "REFLECT":
            row.prop(item, "reflect", text="X", index=0)
            row.prop_decorator(item, "reflect", index=0)
            row.prop(item, "reflect", text="Y", index=1)
            row.prop_decorator(item, "reflect", index=1)

    def draw_filter(self, context, layout):
        # filtering doesn't make sense for this list, instead we show the final UV matrix in this subpanel
        # mainly for debugging purposes
        animation_tracks = context.animation_tracks

        layout.label(text="Final Transformation Matrix")
        col = layout.column(align=True)
        col.enabled = False  # read-only view
        col.use_property_decorate = False
        col.use_property_split = False
        row = col.row(align=True)
        for i in range(3):
            row.prop(animation_tracks, "uv0", index=i, text="")
        row = col.row(align=True)
        for i in range(3):
            row.prop(animation_tracks, "uv1", index=i, text="")

# TODO: show in armature panel and camera panel
#
# class SOLLUMZ_PT_OBJECT_ANIMATION_TRACKS(bpy.types.Panel):
#     bl_label = "Animation Tracks"
#     bl_idname = "SOLLUMZ_PT_OBJECT_ANIMATION_TRACKS"
#     bl_space_type = "PROPERTIES"
#     bl_region_type = "WINDOW"
#     bl_context = "object"
#     bl_options = {"DEFAULT_CLOSED"}
#     bl_parent_id = SOLLUMZ_PT_OBJECT_PANEL.bl_idname
#     bl_order = 9999
#
#     @classmethod
#     def poll(cls, context):
#         if context.active_object is None:
#             return False
#
#         obj = context.active_object
#         if obj and obj.sollum_type == SollumType.ANIMATION:
#             # UV tracks are stored in the animation object instead of the geometry object to try to
#             # future-proof for when Sollumz-yft branch is released, where geometry objects have been removed
#             return isinstance(obj.animation_properties.target_id, bpy.types.Mesh)
#
#         data = obj.data
#         return data is not None and (isinstance(data, bpy.types.Armature) or
#                                      isinstance(data, bpy.types.Camera))
#
#     def draw(self, context):
#         layout = self.layout
#         layout.use_property_split = True
#
#         obj = context.active_object
#         if obj.sollum_type == SollumType.ANIMATION:
#             animation_tracks = obj.animation_properties.animation_tracks
#         else:
#             animation_tracks = obj.animation_tracks
#             target_is_armature = isinstance(obj.data, bpy.types.Armature)
#             target_is_camera = isinstance(obj.data, bpy.types.Camera)
#             target_is_material = isinstance(obj.data, bpy.types.Material)
#
#         if target_is_armature:
#             for prop in AnimationTracks.__annotations__:
#                 if prop.startswith("camera_") or prop.startswith("uv"):
#                     continue
#
#                 layout.prop(animation_tracks, prop)
#         elif target_is_camera:
#             for prop in AnimationTracks.__annotations__:
#                 if not prop.startswith("camera_"):
#                     continue
#
#                 layout.prop(animation_tracks, prop)
#         elif target_is_mesh:
#
#             layout.label(text="UV Transformations")
#             row = layout.row()
#             row.template_list(SOLLUMZ_UL_uv_transforms_list.bl_idname, "",
#                               animation_tracks, "uv_transforms", animation_tracks, "uv_transforms_active_index")
#
#             col = row.column(align=True)
#             col.operator(ycd_ops.SOLLUMZ_OT_uv_transform_add.bl_idname, icon='ADD', text="")
#             col.operator(ycd_ops.SOLLUMZ_OT_uv_transform_remove.bl_idname, icon='REMOVE', text="")
#             col.separator()
#             col.operator(ycd_ops.SOLLUMZ_OT_uv_transform_move.bl_idname, icon='TRIA_UP', text="").direction = 'UP'
#             col.operator(ycd_ops.SOLLUMZ_OT_uv_transform_move.bl_idname, icon='TRIA_DOWN', text="").direction = 'DOWN'
#
#
#         box = layout.box()
#         box.use_property_split = True
#         box.use_property_decorate = False
#         header = box.row(align=True)
#         is_expanded = obj.animation_tracks_ui_show_advanced
#         expanded_icon = "DISCLOSURE_TRI_DOWN" if is_expanded else "DISCLOSURE_TRI_RIGHT"
#         header.prop(obj, "animation_tracks_ui_show_advanced", text="", emboss=False, icon=expanded_icon)
#         header.label(text="Advanced")
#
#         if obj.animation_tracks_ui_show_advanced:
#             for prop in AnimationTracks.__annotations__:
#                 box.prop(animation_tracks, prop)
#


class SOLLUMZ_PT_MATERIAL_ANIMATION_TRACKS(bpy.types.Panel):
    bl_label = "Animation Tracks"
    bl_idname = "SOLLUMZ_PT_MATERIAL_ANIMATION_TRACKS"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_MAT_PANEL.bl_idname
    bl_order = 9999

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if not obj:
            return False

        mat = obj.active_material
        if not mat:
            return False

        return mat.sollum_type == MaterialType.SHADER

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        mat = context.active_object.active_material
        animation_tracks = mat.animation_tracks

        layout.label(text="UV Transformations")
        row = layout.row()
        with context.temp_override(animation_tracks=animation_tracks):
            row.template_list(SOLLUMZ_UL_uv_transforms_list.bl_idname, "",
                              animation_tracks, "uv_transforms", animation_tracks, "uv_transforms_active_index")

        col = row.column(align=True)
        col.operator(ycd_ops.SOLLUMZ_OT_uv_transform_add.bl_idname, icon="ADD", text="")
        col.operator(ycd_ops.SOLLUMZ_OT_uv_transform_remove.bl_idname, icon="REMOVE", text="")
        col.separator()
        col.operator(ycd_ops.SOLLUMZ_OT_uv_transform_move.bl_idname, icon="TRIA_UP", text="").direction = "UP"
        col.operator(ycd_ops.SOLLUMZ_OT_uv_transform_move.bl_idname, icon="TRIA_DOWN", text="").direction = "DOWN"

        layout.operator(ycd_ops.SOLLUMZ_OT_uv_sprite_sheet_anim.bl_idname)

        box = layout.box()
        box.use_property_split = True
        box.use_property_decorate = False
        header = box.row(align=True)
        is_expanded = mat.animation_tracks_ui_show_advanced
        expanded_icon = "DISCLOSURE_TRI_DOWN" if is_expanded else "DISCLOSURE_TRI_RIGHT"
        header.prop(mat, "animation_tracks_ui_show_advanced", text="", emboss=False, icon=expanded_icon)
        header.label(text="Advanced")

        if mat.animation_tracks_ui_show_advanced:
            for prop in AnimationTracks.__annotations__:
                box.prop(animation_tracks, prop)


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

        layout.operator(ycd_ops.SOLLUMZ_OT_clip_new_animation.bl_idname,
                        text="New", icon="ADD")

        for animation_index, clip_animation in enumerate(clip_properties.animations):
            box = layout.box()

            label = clip_animation.animation.name if clip_animation.animation else None
            delete_op = draw_item_box_header(box, clip_animation, label, ycd_ops.SOLLUMZ_OT_clip_delete_animation)
            delete_op.animation_index = animation_index

            if clip_animation.ui_show_expanded:
                box.use_property_split = True
                box.use_property_decorate = False
                box.prop(clip_animation, "animation", text="Animation")

                draw_range_properties(box, clip_animation, "start_frame", "end_frame", "Frame Range")


class SOLLUMZ_PT_CLIP_TAGS(bpy.types.Panel):
    bl_label = "Tags"
    bl_description = "Tags are used to mark specific points in time (events) in a clip."
    bl_idname = "SOLLUMZ_PT_CLIP_TAGS"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_OBJECT_PANEL.bl_idname
    bl_order = 1

    @classmethod
    def poll(cls, context):
        obj = context.active_object

        return obj and obj.sollum_type == SollumType.CLIP

    def draw(self, context):
        layout = self.layout

        obj = context.active_object
        clip_properties = obj.clip_properties

        row = layout.split(factor=0.625, align=True)
        row.operator(ycd_ops.SOLLUMZ_OT_clip_new_tag.bl_idname,
                     text="New", icon="ADD").ignore_template = True
        row.operator_menu_enum(ycd_ops.SOLLUMZ_OT_clip_new_tag.bl_idname, "template",
                               text="From Template", icon="MENU_PANEL").ignore_template = False

        for tag_index, clip_tag in enumerate(clip_properties.tags):
            box = layout.box()

            del_op = draw_item_box_header(box, clip_tag, clip_tag.name, ycd_ops.SOLLUMZ_OT_clip_delete_tag,
                                          visible_prop="ui_view_on_timeline",
                                          color_prop="ui_timeline_color")
            del_op.tag_index = tag_index

            if clip_tag.ui_show_expanded:
                box.use_property_split = True
                box.use_property_decorate = False
                box.prop(clip_tag, "name")

                draw_range_properties(box, clip_tag, "start_phase", "end_phase", "Phase Range")

                attr_box = box.box()
                attr_header = attr_box.row(align=True)
                attr_header.label(text="Attributes")
                new_op = attr_header.operator(ycd_ops.SOLLUMZ_OT_clip_new_tag_attribute.bl_idname,
                                      text="", icon="ADD")
                new_op.tag_index = tag_index
                for attr_index, attr in enumerate(clip_tag.attributes):
                    del_op = draw_clip_attribute(attr_box, attr, ycd_ops.SOLLUMZ_OT_clip_delete_tag_attribute)
                    del_op.tag_index = tag_index
                    del_op.attribute_index = attr_index


class SOLLUMZ_PT_CLIP_PROPERTIES(bpy.types.Panel):
    bl_label = "Properties"
    bl_description = ""
    bl_idname = "SOLLUMZ_PT_CLIP_PROPERTIES"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_OBJECT_PANEL.bl_idname
    bl_order = 2

    @classmethod
    def poll(cls, context):
        obj = context.active_object

        return obj and obj.sollum_type == SollumType.CLIP

    def draw(self, context):
        layout = self.layout

        obj = context.active_object
        clip_properties = obj.clip_properties

        layout.operator(ycd_ops.SOLLUMZ_OT_clip_new_property.bl_idname,
                        text="New", icon="ADD")

        box = layout.box()
        for prop_index, prop in enumerate(clip_properties.properties):
            del_op = draw_clip_attribute(box, prop, ycd_ops.SOLLUMZ_OT_clip_delete_property)
            del_op.property_index = prop_index


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

        if len(context.selected_objects) > 0:
            active_object = context.selected_objects[0]

            if is_any_sollumz_animation_obj(active_object):
                layout.operator(ycd_ops.SOLLUMZ_OT_create_clip.bl_idname)
                layout.operator(ycd_ops.SOLLUMZ_OT_create_animation.bl_idname)
            else:
                row = layout.row(align=False)
                row.operator(ycd_ops.SOLLUMZ_OT_create_clip_dictionary.bl_idname)

            row = layout.row(align=True)
            row.use_property_split = True
            row.use_property_decorate = False
            template_animation_target_ID(row, context.scene,
                                         "sollumz_animations_target_id",
                                         "sollumz_animations_target_id_type", text=" ")
            row.operator(ycd_ops.SOLLUMZ_OT_animations_set_target.bl_idname)
        else:
            layout.operator(
                ycd_ops.SOLLUMZ_OT_create_clip_dictionary.bl_idname)


class ClipTagsOnTimelineDrawHandler:
    """Manages drawing the tag markers for the selected clip on the timeline.
    User input is handled by operator SOLLUMZ_OT_timeline_clip_tags_drag.
    """

    def __init__(self, cls):
        self.cls = cls
        self.handler = None
        self.overlay_verts_pos = np.empty((0, 3), dtype=np.float32)
        self.overlay_verts_color = np.empty((0, 4), dtype=np.float32)
        self.marker_verts_pos = np.empty((0, 3), dtype=np.float32)
        self.marker_verts_color = np.empty((0, 4), dtype=np.float32)

    def register(self):
        self.handler = self.cls.draw_handler_add(self.draw, (), "WINDOW", "POST_PIXEL")

    def unregister(self):
        self.cls.draw_handler_remove(self.handler, "WINDOW")

    def draw(self):
        import gpu
        import gpu_extras
        import blf
        import time

        context = bpy.context
        clip_obj = context.active_object
        if clip_obj is None or clip_obj.sollum_type != SollumType.CLIP:
            return
        # t_start = time.perf_counter_ns()

        clip_properties = clip_obj.clip_properties

        num_tags = len(clip_properties.tags)
        if num_tags == 0:
            return

        if num_tags != len(self.overlay_verts_pos) // 6:
            self.overlay_verts_pos = np.empty((num_tags * 6, 3), dtype=np.float32)
            self.overlay_verts_color = np.empty((num_tags * 6, 4), dtype=np.float32)
            self.marker_verts_pos = np.empty((num_tags * 12, 3), dtype=np.float32)
            self.marker_verts_color = np.empty((num_tags * 12, 4), dtype=np.float32)

        clip_frame_count = clip_properties.get_frame_count()

        region = context.region
        view = region.view2d
        scrubber_height = 22.5
        h = region.height
        h -= scrubber_height  # reduce region height to place markers below the scrubber

        notch_size = 5
        names = []
        num_visible_tags = 0
        for clip_tag in clip_properties.tags:
            if not clip_tag.ui_view_on_timeline:
                continue

            i = num_visible_tags

            start_phase = clip_tag.start_phase
            end_phase = clip_tag.end_phase

            start_frame = clip_frame_count * start_phase
            end_frame = clip_frame_count * end_phase
            color = clip_tag.ui_timeline_color
            color_highlight = (color[0] + (1.0 - color[0]) * 0.25,
                               color[1] + (1.0 - color[1]) * 0.25,
                               color[2] + (1.0 - color[2]) * 0.25,
                               color[3])
            highlight_start = clip_tag.ui_timeline_hovered_start or clip_tag.ui_timeline_drag_start
            highlight_end = clip_tag.ui_timeline_hovered_end or clip_tag.ui_timeline_drag_end
            color_start = color_highlight if highlight_start else color
            color_end = color_highlight if highlight_end else color
            overlay_color = (color[0], color[1], color[2], color[3] * 0.2)

            start_x, _ = view.view_to_region(start_frame, 0, clip=False)
            end_x, _ = view.view_to_region(end_frame, 0, clip=False)
            y = h

            # tag area highlight
            o = i * 6
            self.overlay_verts_pos[o:o + 6] = (
                (start_x, y, 0.0),  # top left triangle
                (start_x, y - h, 0.0),
                (end_x, y, 0.0),
                (end_x, y, 0.0),  # bottom right triangle
                (end_x, y - h, 0.0),
                (start_x, y - h, 0.0),
            )
            self.overlay_verts_color[o: o + 6] = overlay_color

            o = i * 12
            self.marker_verts_pos[o:o + 12] = (
                # start marker
                (start_x, y, 0.0),  # start vertical line top
                (start_x, y - h, 0.0),  # start vertical line bottom
                (start_x, y, 0.0),  # start notch
                (start_x - notch_size, y, 0.0),
                (start_x - notch_size, y, 0.0),
                (start_x, y - notch_size, 0.0),
                # end marker
                (end_x, y, 0.0),  # end marker vertical line top
                (end_x, y - h, 0.0),  # end marker vertical line bottom
                (end_x, y, 0.0),  # end marker notch
                (end_x + notch_size, y, 0.0),
                (end_x + notch_size, y, 0.0),
                (end_x, y - notch_size, 0.0),
            )
            self.marker_verts_color[o: o + 6] = color_start
            self.marker_verts_color[o + 6: o + 12] = color_end

            # tag name
            text_offset = 30 + 25 * (i % 4 + 1)
            text_x = start_x + 5
            text_y = y - h + text_offset
            names.append((clip_tag.name, text_x, text_y))

            num_visible_tags += 1

        gpu.state.line_width_set(3)
        gpu.state.blend_set("ALPHA")

        shader_smooth_color = gpu.shader.from_builtin("SMOOTH_COLOR")
        batch = gpu_extras.batch.batch_for_shader(shader_smooth_color, "TRIS", {
            "pos": self.overlay_verts_pos[:num_visible_tags * 6],
            "color": self.overlay_verts_color[:num_visible_tags * 6]
        })
        batch.draw(shader_smooth_color)

        batch = gpu_extras.batch.batch_for_shader(shader_smooth_color, "LINES", {
            "pos": self.marker_verts_pos[:num_visible_tags * 12],
            "color": self.marker_verts_color[:num_visible_tags * 12]
        })
        batch.draw(shader_smooth_color)

        theme = context.preferences.themes[0]
        text_color = theme.dopesheet_editor.space.text
        text_color = (text_color[0], text_color[1], text_color[2], 1.0)
        font_id = 0
        font_size = 14 * (context.preferences.system.dpi / 72)
        for name, x, y in names:
            blf.position(font_id, x, y, 0)
            blf.color(font_id, *text_color)
            blf.size(font_id, font_size)
            blf.draw(font_id, name)

        # t_end = time.perf_counter_ns()
        # print(f"draw_tags_on_timeline  {t_end - t_start} ns  ({(t_end - t_start) / 1000000} ms)")


draw_handlers = []


def register():
    SOLLUMZ_PT_OBJECT_PANEL.append(draw_clip_properties)
    SOLLUMZ_PT_OBJECT_PANEL.append(draw_animation_properties)
    SOLLUMZ_PT_OBJECT_PANEL.append(draw_clip_dictionary_properties)

    for cls in (bpy.types.SpaceDopeSheetEditor, bpy.types.SpaceNLA):
        handler = ClipTagsOnTimelineDrawHandler(cls)
        handler.register()
        draw_handlers.append(handler)


def unregister():
    SOLLUMZ_PT_OBJECT_PANEL.remove(draw_clip_properties)
    SOLLUMZ_PT_OBJECT_PANEL.remove(draw_animation_properties)
    SOLLUMZ_PT_OBJECT_PANEL.remove(draw_clip_dictionary_properties)

    for handler in draw_handlers:
        handler.unregister()
    draw_handlers.clear()
