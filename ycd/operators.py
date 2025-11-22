import bpy
from ..sollumz_helper import SOLLUMZ_OT_base
from ..sollumz_properties import SollumType
from ..tools.blenderhelper import find_child_by_type
from ..tools.meshhelper import flip_uv
from ..tools.utils import color_hash
from ..tools.animationhelper import is_any_sollumz_animation_obj, update_uv_clip_hash, get_scene_fps
from .ycdimport import create_clip_dictionary_template, create_anim_obj
from .. import logger


class SOLLUMZ_OT_animations_set_target(SOLLUMZ_OT_base, bpy.types.Operator):
    bl_idname = "sollumz.animations_set_target"
    bl_label = "Set Animations Target"
    bl_description = "Set the same target for all animations in the selected clip dictionaries"

    @classmethod
    def poll(cls, context):
        return (len(context.selected_objects) > 0 and
                any(is_any_sollumz_animation_obj(obj) for obj in context.selected_objects) and
                context.scene.sollumz_animations_target_id is not None)

    def run(self, context):
        scene = context.scene
        animations_objects = self.collect_animations_objects(context)
        target_id = scene.sollumz_animations_target_id
        target_id_type = scene.sollumz_animations_target_id_type

        for animations_obj in animations_objects:
            for animation_obj in animations_obj.children:
                if animation_obj.sollum_type != SollumType.ANIMATION:
                    continue

                animation_obj.animation_properties.target_id_type = target_id_type
                animation_obj.animation_properties.target_id = target_id

        scene.sollumz_animations_target_id = None
        return {"FINISHED"}

    def collect_animations_objects(self, context):
        animations_objects = set()
        for obj in context.selected_objects:
            animations_obj = None
            if obj.sollum_type == SollumType.ANIMATION:
                animations_obj = obj.parent
            elif obj.sollum_type == SollumType.ANIMATIONS:
                animations_obj = obj
            elif obj.sollum_type == SollumType.CLIP:
                animations_obj = find_child_by_type(obj.parent.parent, SollumType.ANIMATIONS)
            elif obj.sollum_type == SollumType.CLIPS:
                animations_obj = find_child_by_type(obj.parent, SollumType.ANIMATIONS)
            elif obj.sollum_type == SollumType.CLIP_DICTIONARY:
                animations_obj = find_child_by_type(obj, SollumType.ANIMATIONS)

            animations_objects.add(animations_obj)

        return animations_objects


class SOLLUMZ_OT_clip_apply_nla(SOLLUMZ_OT_base, bpy.types.Operator):
    bl_idname = "sollumz.anim_apply_nla"
    bl_label = "Apply NLA"
    bl_description = "Applies clip as a Nonlinear Animation for a quick preview"

    def run(self, context):
        if len(bpy.context.selected_objects) <= 0:
            return {"FINISHED"}

        clip_obj = bpy.context.selected_objects[0]

        if clip_obj.sollum_type != SollumType.CLIP:
            return {"FINISHED"}

        clip_properties = clip_obj.clip_properties
        if len(clip_properties.animations) <= 0:
            return {"FINISHED"}

        # TODO: animation may be None, or not all animations have the same target/are filled in
        target = clip_properties.animations[0].animation.animation_properties.get_target()
        if target is None:
            return {"FINISHED"}

        clip_frame_duration = clip_properties.get_duration_in_frames()

        groups = {}

        for clip_animation in clip_properties.animations:
            if clip_animation.animation is None:
                continue

            animation_properties = clip_animation.animation.animation_properties

            start_frame = clip_animation.start_frame
            end_frame = clip_animation.end_frame

            action = animation_properties.action

            if action.name not in groups:
                groups[action.name] = []

            group = groups[action.name]

            group.append({
                "name": clip_properties.hash,
                "start_frame": start_frame,
                "end_frame": end_frame,
                "action": action,
            })

        if target.animation_data is None:
            target.animation_data_create()

        for nla_track in target.animation_data.nla_tracks:
            target.animation_data.nla_tracks.remove(nla_track)

        for group_name, clips in groups.items():
            track = target.animation_data.nla_tracks.new()
            track.name = group_name

            for clip in clips:
                nla_strip = track.strips.new(clip["name"], 0, clip["action"])
                nla_strip.frame_start = 0
                nla_strip.frame_end = clip_frame_duration

                bpy.context.scene.frame_start = 0
                bpy.context.scene.frame_end = int(nla_strip.frame_end)

                nla_strip.blend_type = "COMBINE"
                nla_strip.extrapolation = "NOTHING"
                nla_strip.name = clip["name"]

                action_frame_duration = clip["end_frame"] - clip["start_frame"]
                nla_strip.scale = clip_frame_duration / action_frame_duration
                nla_strip.action_frame_start = clip["start_frame"]
                nla_strip.action_frame_end = clip["end_frame"]

        return {"FINISHED"}


class SOLLUMZ_OT_clip_recalculate_uv_hash(SOLLUMZ_OT_base, bpy.types.Operator):
    bl_idname = "sollumz.clip_recalculate_uv_hash"
    bl_label = "Recalculate UV Clip Hash"
    bl_description = "Recalculate hash based on the target material and model name"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.sollum_type == SollumType.CLIP

    def run(self, context):
        with logger.use_operator_logger(self):
            clip_obj = context.active_object
            if update_uv_clip_hash(clip_obj):
                return {"FINISHED"}
            else:
                return {"CANCELLED"}


class SOLLUMZ_OT_clip_new_animation(SOLLUMZ_OT_base, bpy.types.Operator):
    bl_idname = "sollumz.clip_new_animation"
    bl_label = "Add a new Animation Link"
    bl_description = "Add a new animation link to the clip"

    def run(self, context):
        if len(bpy.context.selected_objects) <= 0:
            return {"FINISHED"}

        active_object = bpy.context.selected_objects[0]

        if active_object.sollum_type != SollumType.CLIP:
            return {"FINISHED"}

        clip_properties = active_object.clip_properties

        clip_properties.animations.add()

        return {"FINISHED"}


class SOLLUMZ_OT_clip_delete_animation(SOLLUMZ_OT_base, bpy.types.Operator):
    bl_idname = "sollumz.clip_delete_animation"
    bl_label = "Delete Animation Link"
    bl_description = "Remove the animation link from the clip"

    animation_index: bpy.props.IntProperty()

    def run(self, context):
        if len(bpy.context.selected_objects) <= 0:
            return {"FINISHED"}

        active_object = bpy.context.selected_objects[0]

        if active_object.sollum_type != SollumType.CLIP:
            return {"FINISHED"}

        clip_properties = active_object.clip_properties

        clip_properties.animations.remove(self.animation_index)

        return {"FINISHED"}


class SOLLUMZ_OT_clip_new_tag(SOLLUMZ_OT_base, bpy.types.Operator):
    bl_idname = "sollumz.clip_new_tag"
    bl_label = "Add a new Tag"
    bl_description = "Add a new tag to the clip based on a template"

    ignore_template: bpy.props.BoolProperty(default=False)
    template: bpy.props.EnumProperty(
        items=[
            ("EMPTY", "Empty", "Add an empty tag", 0),
            ("MOVE_EVENT", "MoVE Event", "Add a MoVE event tag", 1),
            ("AUDIO", "Audio", "Add an audio trigger event tag", 2),
            ("FOOT", "Foot", "Add a foot synchronization tag", 3),
            ("MOVER_FIXUP", "Mover Fixup", "Add a mover fixup tag", 4),
            ("FACIAL", "Facial", "Add a facial tag", 5),
            ("OBJECT", "Object", "Add a object tag", 6),
            ("ARMS_IK", "Arms IK", "Add a arms IK tag", 7),
        ],
        default="EMPTY",
        name="Tag Template",
    )

    @classmethod
    def description(cls, context, properties):
        if properties.ignore_template:
            return "Add a new empty tag to the clip"

        return bpy.types.UILayout.enum_item_description(properties, "template", properties.template)

    def run(self, context):
        if len(bpy.context.selected_objects) <= 0:
            return {"FINISHED"}

        active_object = bpy.context.selected_objects[0]

        if active_object.sollum_type != SollumType.CLIP:
            return {"FINISHED"}

        clip_properties = active_object.clip_properties

        tag = clip_properties.tags.add()
        self.apply_template(tag)

        if clip_properties.duration != 0.0:
            # place the tag at the current frame
            phase = bpy.context.scene.frame_float / get_scene_fps() / clip_properties.duration
            phase = min(max(phase, 0.0), 1.0)
            tag.start_phase = phase
            tag.end_phase = phase

        # redraw the timeline to show the new tag
        for area in context.screen.areas:
            if area.type == "DOPESHEET_EDITOR" or area.type == "NLA_EDITOR":
                area.tag_redraw()

        return {"FINISHED"}

    def apply_template(self, tag):
        print(self.ignore_template, self.template)
        if self.ignore_template or self.template == "EMPTY":
            return

        name = ""
        attrs = []

        # optional attribute used with 'moveevent', 'audio', 'facial' and 'hash_A31D8F23'
        # seems related to animation blending
        # ("hash_368D9C33", "Float"),

        if self.template == "MOVE_EVENT":
            name = "moveevent"
            attrs = [
                ("moveevent", "HashString"),
            ]
        elif self.template == "AUDIO":
            name = "audio"
            attrs = [
                ("id", "HashString"),
            ]
            pass
        elif self.template == "FOOT":
            name = "foot"
            attrs = [
                ("heel", "Bool"),
                ("right", "Bool"),
            ]
        elif self.template == "MOVER_FIXUP":
            name = "moverfixup"
            attrs = [
                ("translation", "Bool"),
                ("transx", "Bool"),
                ("transy", "Bool"),
                ("transz", "Bool"),
                ("rotation", "Bool"),
            ]
        elif self.template == "FACIAL":
            name = "facial"
            attrs = [
                ("nameid", "HashString"),
                ("hash_7DA44A49", "Bool"),
                ("hash_0C905639", "Bool"),
            ]
        elif self.template == "OBJECT":
            name = "object"
            attrs = [
                ("release", "Bool"),
                ("destroy", "Bool"),
                ("create", "Bool"),
            ]
        elif self.template == "ARMS_IK":
            name = "armsik"
            attrs = [
                ("left", "Bool"),
                ("right", "Bool"),
                ("allowed", "Bool"),
                ("blocked", "Bool"),
            ]
        else:
            raise Exception("Invalid template")

        # more tags:
        #  hash_C261B2D3        (first person camera related)
        #    pitchspringinput  Bool
        #    yawspringinput    Bool
        #
        #  hash_1EFF20B5
        #    allowed           Bool
        #    blocked           Bool
        #
        #  ik
        #    right             Bool
        #    on                Bool
        #
        #  hash_44D39D32
        #    hash_70DB63EC     HashString
        #    hash_0398BB95     HashString
        #
        #  door
        #    start             Bool
        #
        #  smash                (no attributes, probably specific to veh@jacking@ animations)
        #
        #  hash_95955F82        (no attributes, probably specific to veh@jacking@ animations)
        #
        #  applyforce
        #    force             Float
        #
        #

        tag.name = name
        tag.ui_timeline_color = color_hash(tag.name)
        for attr_name, attr_type in attrs:
            attr = tag.attributes.add()
            attr.name = attr_name
            attr.type = attr_type


class SOLLUMZ_OT_clip_delete_tag(SOLLUMZ_OT_base, bpy.types.Operator):
    bl_idname = "sollumz.clip_delete_tag"
    bl_label = "Delete Tag"
    bl_description = "Remove the tag from the clip"

    tag_index: bpy.props.IntProperty()

    def run(self, context):
        if len(bpy.context.selected_objects) <= 0:
            return {"FINISHED"}

        active_object = bpy.context.selected_objects[0]

        if active_object.sollum_type != SollumType.CLIP:
            return {"FINISHED"}

        clip_properties = active_object.clip_properties

        clip_properties.tags.remove(self.tag_index)

        # redraw the timeline to stop displaying the deleted tag
        for area in context.screen.areas:
            if area.type == "DOPESHEET_EDITOR" or area.type == "NLA_EDITOR":
                area.tag_redraw()

        return {"FINISHED"}


class SOLLUMZ_OT_clip_new_tag_attribute(SOLLUMZ_OT_base, bpy.types.Operator):
    bl_idname = "sollumz.clip_new_tag_attribute"
    bl_label = "Add a new Tag Attribute"
    bl_description = "Add a new attribute to the tag"

    tag_index: bpy.props.IntProperty()

    def run(self, context):
        if len(bpy.context.selected_objects) <= 0:
            return {"FINISHED"}

        active_object = bpy.context.selected_objects[0]

        if active_object.sollum_type != SollumType.CLIP:
            return {"FINISHED"}

        clip_properties = active_object.clip_properties

        tag = clip_properties.tags[self.tag_index]
        if not tag:
            return {"FINISHED"}

        tag.attributes.add()

        return {"FINISHED"}


class SOLLUMZ_OT_clip_delete_tag_attribute(SOLLUMZ_OT_base, bpy.types.Operator):
    bl_idname = "sollumz.clip_delete_tag_attribute"
    bl_label = "Delete Tag Attribute"
    bl_description = "Remove the attribute from the tag"

    tag_index: bpy.props.IntProperty()
    attribute_index: bpy.props.IntProperty()

    def run(self, context):
        if len(bpy.context.selected_objects) <= 0:
            return {"FINISHED"}

        active_object = bpy.context.selected_objects[0]

        if active_object.sollum_type != SollumType.CLIP:
            return {"FINISHED"}

        clip_properties = active_object.clip_properties

        tag = clip_properties.tags[self.tag_index]
        if not tag:
            return {"FINISHED"}

        tag.attributes.remove(self.attribute_index)

        return {"FINISHED"}


class SOLLUMZ_OT_clip_new_property(SOLLUMZ_OT_base, bpy.types.Operator):
    bl_idname = "sollumz.clip_new_property"
    bl_label = "Add a new Property"
    bl_description = "Add a new property to the clip"

    def run(self, context):
        if len(bpy.context.selected_objects) <= 0:
            return {"FINISHED"}

        active_object = bpy.context.selected_objects[0]

        if active_object.sollum_type != SollumType.CLIP:
            return {"FINISHED"}

        clip_properties = active_object.clip_properties

        clip_properties.properties.add()

        return {"FINISHED"}


class SOLLUMZ_OT_clip_delete_property(SOLLUMZ_OT_base, bpy.types.Operator):
    bl_idname = "sollumz.clip_delete_property"
    bl_label = "Delete Property"
    bl_description = "Remove the property from the clip"

    property_index: bpy.props.IntProperty()

    def run(self, context):
        if len(bpy.context.selected_objects) <= 0:
            return {"FINISHED"}

        active_object = bpy.context.selected_objects[0]

        if active_object.sollum_type != SollumType.CLIP:
            return {"FINISHED"}

        clip_properties = active_object.clip_properties

        clip_properties.properties.remove(self.property_index)

        return {"FINISHED"}


class SOLLUMZ_OT_clip_new_property_attribute(SOLLUMZ_OT_base, bpy.types.Operator):
    bl_idname = "sollumz.clip_new_property_attribute"
    bl_label = "Add a new Property Attribute"
    bl_description = "Add a new attribute to the property"

    property_index: bpy.props.IntProperty()

    def run(self, context):
        if len(bpy.context.selected_objects) <= 0:
            return {"FINISHED"}

        active_object = bpy.context.selected_objects[0]

        if active_object.sollum_type != SollumType.CLIP:
            return {"FINISHED"}

        clip_properties = active_object.clip_properties

        prop = clip_properties.properties[self.property_index]
        if not prop:
            return {"FINISHED"}

        prop.attributes.add()

        return {"FINISHED"}


class SOLLUMZ_OT_clip_delete_property_attribute(SOLLUMZ_OT_base, bpy.types.Operator):
    bl_idname = "sollumz.clip_delete_property_attribute"
    bl_label = "Delete Property Attribute"
    bl_description = "Remove the attribute from the property"

    property_index: bpy.props.IntProperty()
    attribute_index: bpy.props.IntProperty()

    def run(self, context):
        if len(bpy.context.selected_objects) <= 0:
            return {"FINISHED"}

        active_object = bpy.context.selected_objects[0]

        if active_object.sollum_type != SollumType.CLIP:
            return {"FINISHED"}

        clip_properties = active_object.clip_properties

        prop = clip_properties.properties[self.property_index]
        if not prop:
            return {"FINISHED"}

        prop.attributes.remove(self.attribute_index)

        return {"FINISHED"}


class SOLLUMZ_OT_create_clip_dictionary(SOLLUMZ_OT_base, bpy.types.Operator):
    bl_idname = "sollumz.create_clip_dictionary"
    bl_label = "Create clip dictionary template"

    def run(self, context):
        create_clip_dictionary_template("Clip Dictionary")
        return {"FINISHED"}


class SOLLUMZ_OT_create_clip(SOLLUMZ_OT_base, bpy.types.Operator):
    bl_idname = "sollumz.create_clip"
    bl_label = "Create clip"

    def run(self, context):
        if len(bpy.context.selected_objects) <= 0:
            return {"FINISHED"}

        active_object = bpy.context.selected_objects[0]

        clips_obj = None

        if active_object.sollum_type == SollumType.CLIP:
            clips_obj = active_object.parent
        elif active_object.sollum_type == SollumType.ANIMATION:
            clip_dictionary_obj = active_object.parent.parent

            clips_obj = find_child_by_type(
                clip_dictionary_obj, SollumType.CLIPS)
        elif active_object.sollum_type == SollumType.CLIPS:
            clips_obj = active_object
        elif active_object.sollum_type == SollumType.ANIMATIONS:
            clip_dictionary_obj = active_object.parent

            clips_obj = find_child_by_type(
                clip_dictionary_obj, SollumType.CLIPS)
        elif active_object.sollum_type == SollumType.CLIP_DICTIONARY:
            clip_dictionary_obj = active_object

            clips_obj = find_child_by_type(
                clip_dictionary_obj, SollumType.CLIPS)

        if clips_obj is not None:
            animation_obj = create_anim_obj(SollumType.CLIP)

            animation_obj.parent = clips_obj

        return {"FINISHED"}


class SOLLUMZ_OT_create_animation(SOLLUMZ_OT_base, bpy.types.Operator):
    bl_idname = "sollumz.create_animation"
    bl_label = "Create animation"

    def run(self, context):
        if len(bpy.context.selected_objects) <= 0:
            return {"FINISHED"}

        active_object = bpy.context.selected_objects[0]

        animations_obj = None

        if active_object.sollum_type == SollumType.CLIP:
            clip_dictionary_obj = active_object.parent.parent

            animations_obj = find_child_by_type(
                clip_dictionary_obj, SollumType.ANIMATIONS)
        elif active_object.sollum_type == SollumType.ANIMATION:
            animations_obj = active_object.parent
        elif active_object.sollum_type == SollumType.CLIPS:
            clip_dictionary_obj = active_object.parent

            animations_obj = find_child_by_type(
                clip_dictionary_obj, SollumType.ANIMATIONS)
        elif active_object.sollum_type == SollumType.ANIMATIONS:
            animations_obj = active_object
        elif active_object.sollum_type == SollumType.CLIP_DICTIONARY:
            clip_dictionary_obj = active_object

            animations_obj = find_child_by_type(
                clip_dictionary_obj, SollumType.ANIMATIONS)

        if animations_obj is not None:
            animation_obj = create_anim_obj(SollumType.ANIMATION)

            animation_obj.parent = animations_obj

        return {"FINISHED"}


class SOLLUMZ_OT_uv_transform_add(SOLLUMZ_OT_base, bpy.types.Operator):
    bl_idname = "sollumz.uv_transform_add"
    bl_label = "Add UV Transformation"
    bl_description = "Add new UV transformation"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def run(self, context):
        obj = context.active_object
        animation_tracks = obj.active_material.animation_tracks
        animation_tracks.uv_transforms.add()
        animation_tracks.uv_transforms_active_index = len(animation_tracks.uv_transforms) - 1
        animation_tracks.update_uv_transform_matrix()
        return {"FINISHED"}


class SOLLUMZ_OT_uv_transform_remove(SOLLUMZ_OT_base, bpy.types.Operator):
    bl_idname = "sollumz.uv_transform_remove"
    bl_label = "Remove UV Transformation"
    bl_description = "Remove active UV transformation"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def run(self, context):
        obj = context.active_object
        animation_tracks = obj.active_material.animation_tracks
        animation_tracks.uv_transforms.remove(animation_tracks.uv_transforms_active_index)
        length = len(animation_tracks.uv_transforms)
        if length > 0 and animation_tracks.uv_transforms_active_index >= length:
            animation_tracks.uv_transforms_active_index = length - 1
        animation_tracks.update_uv_transform_matrix()
        return {"FINISHED"}


class SOLLUMZ_OT_uv_transform_move(SOLLUMZ_OT_base, bpy.types.Operator):
    bl_idname = "sollumz.uv_transform_move"
    bl_label = "Move UV transformation"
    bl_description = "Move the active UV transformation up/down the transformation stack"

    direction: bpy.props.EnumProperty(items=[
        ("UP", "Up", "Move up", 0),
        ("DOWN", "Down", "Move down", 1),
    ])

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def run(self, context):
        obj = context.active_object
        animation_tracks = obj.active_material.animation_tracks

        src_index = animation_tracks.uv_transforms_active_index
        dst_index = src_index + 1 if self.direction == "DOWN" else src_index - 1
        if dst_index < 0 or dst_index >= len(animation_tracks.uv_transforms):
            return {"FINISHED"}

        animation_tracks.uv_transforms.move(src_index, dst_index)
        animation_tracks.uv_transforms_active_index = dst_index
        animation_tracks.update_uv_transform_matrix()
        return {"FINISHED"}


# helper properties for SOLLUMZ_OT_uv_sprite_sheet_anim
class UVSpriteSheetFrame(bpy.types.PropertyGroup):
    def on_use_changed(self, context):
        if self.use == self.prev_use:
            return

        operator = context.operator_uv_sprite_sheet_anim
        if self.use:
            # frame selected, place it last in the order
            last_order = -1
            for frame in operator.frames:
                if frame != self and frame.use:
                    last_order = max(last_order, frame.order)
            self.order = last_order + 1
        else:
            # frame unselected, move forward all frames after it
            for frame in operator.frames:
                if frame.order > self.order:
                    frame.order -= 1
        self.prev_use = self.use

    use: bpy.props.BoolProperty(name="Use", description="Use frame in animation", default=False, update=on_use_changed)
    prev_use: bpy.props.BoolProperty(name="Prev Use", default=False)
    order: bpy.props.IntProperty(name="Order", default=0, min=0)


class SOLLUMZ_OT_uv_sprite_sheet_anim_select_all_frames(SOLLUMZ_OT_base, bpy.types.Operator):
    bl_idname = "sollumz.uv_sprite_sheet_anim_select_all_frames"
    bl_label = "Select All"
    bl_description = "Use all the frames in the sprite sheet texture"

    def run(self, context):
        operator = context.operator_uv_sprite_sheet_anim

        # clear selected frames to reset order
        for frame in operator.frames:
            frame.use = False

        for frame in operator.frames:
            frame.use = True


class SOLLUMZ_OT_uv_sprite_sheet_anim_clear_frames(SOLLUMZ_OT_base, bpy.types.Operator):
    bl_idname = "sollumz.uv_sprite_sheet_anim_clear_frames"
    bl_label = "Clear"
    bl_description = "Clear frame selection"

    def run(self, context):
        operator = context.operator_uv_sprite_sheet_anim
        for frame in operator.frames:
            frame.use = False


class SOLLUMZ_OT_uv_sprite_sheet_anim(SOLLUMZ_OT_base, bpy.types.Operator):
    bl_idname = "sollumz.uv_sprite_sheet_anim"
    bl_label = "Create Sprite Sheet UV Animation"
    bl_description = "Create a UV animation based on the frames of a sprite sheet texture"

    def on_num_frames_changed(self, context):
        total_frames = self.frames_horizontal * self.frames_vertical
        if total_frames > len(self.frames):
            # add enough frames
            for i in range(total_frames - len(self.frames)):
                self.frames.add()
        elif total_frames < len(self.frames):
            # remove unnecessary frames
            for i in range(len(self.frames) - total_frames):
                self.frames.remove(len(self.frames) - 1)

        # clear selected frames
        for frame in self.frames:
            frame.use = False

        # auto-calculate frame size when number of frames changes
        # cannot use self._image in callbacks, use context pointer instead
        image = context.operator_uv_sprite_sheet_anim_image
        img_w, img_h = image.size
        max_w = img_w - self.offset_x - self.separation_horizontal * (self.frames_horizontal - 1)
        max_h = img_h - self.offset_y - self.separation_vertical * (self.frames_vertical - 1)
        self.frame_width = max_w / self.frames_horizontal
        self.frame_height = max_h / self.frames_vertical

        self.refresh_ui = True

    def on_use_dst_frame_changed(self, context):
        if not self.use_dst_frame:
            # restore auto-calculated frame bounds
            self.dst_frame_offset_x = self.auto_dst_frame_offset_x
            self.dst_frame_offset_y = self.auto_dst_frame_offset_y
            self.dst_frame_width = self.auto_dst_frame_width
            self.dst_frame_height = self.auto_dst_frame_height

    # internal properties
    # blender saves the operator properties after a successful execution,
    # some initialization is only needed the first time
    first_run: bpy.props.BoolProperty(default=True)
    refresh_ui: bpy.props.BoolProperty(default=False)

    # user-editable properties
    frames: bpy.props.CollectionProperty(name="Frames to Use", type=UVSpriteSheetFrame)
    # TODO: prevent settings that create frames out of bounds by updating the other settings to fit in the image bounds
    frames_horizontal: bpy.props.IntProperty(
        name="Frames Horizontal",
        description="Number of horizontal frames in the sprite sheet texture",
        min=1, default=1, update=on_num_frames_changed)
    frames_vertical: bpy.props.IntProperty(
        name="Frames Vertical",
        description="Number of vertical frames in the sprite sheet texture",
        min=1, default=1, update=on_num_frames_changed)
    frame_width: bpy.props.FloatProperty(
        name="Frame Width",
        description="Width of a frame in the sprite sheet texture, in pixels",
        min=1, default=1, subtype="PIXEL", step=100)
    frame_height: bpy.props.FloatProperty(
        name="Frame Height",
        description="Height of a frame in the sprite sheet texture, in pixels",
        min=1, default=1, subtype="PIXEL", step=100)
    offset_x: bpy.props.FloatProperty(
        name="Offset X",
        description="Offset along X-axis of the first frame in the sprite sheet texture, in pixels",
        min=0, default=0, subtype="PIXEL", step=100)
    offset_y: bpy.props.FloatProperty(
        name="Offset Y",
        description="Offset along Y-axis of the first frame in the sprite sheet texture, in pixels",
        min=0, default=0, subtype="PIXEL", step=100)
    separation_horizontal: bpy.props.FloatProperty(
        name="Separation Horizontal",
        description="Horizontal separation between frames in the sprite sheet texture, in pixels",
        min=0, default=0, subtype="PIXEL", step=100)
    separation_vertical: bpy.props.FloatProperty(
        name="Separation Vertical",
        description="Vertical separation between frames in the sprite sheet texture, in pixels",
        min=0, default=0, subtype="PIXEL", step=100)
    keyframe_interval: bpy.props.IntProperty(
        name="Keyframe Interval",
        description="Interval at which keyframes are inserted",
        min=1, default=1)
    use_dst_frame: bpy.props.BoolProperty(
        name="Use Destination Frame",
        description="Specify the destination frame bounds manually instead of auto-calculating them. "
                    "Useful when the UV mapped area is not rectangular",
        default=False, update=on_use_dst_frame_changed)
    dst_frame_offset_x: bpy.props.FloatProperty(
        name="Destination Frame Offset X",
        description="Offset along X-axis of the area UV mapped in the sprite sheet texture, in pixels",
        default=0, subtype="PIXEL", step=100)
    dst_frame_offset_y: bpy.props.FloatProperty(
        name="Destination Frame Offset Y",
        description="Offset along Y-axis of the area UV mapped in the sprite sheet texture, in pixels",
        default=0, subtype="PIXEL", step=100)
    dst_frame_width: bpy.props.FloatProperty(
        name="Destination Frame Width",
        description="Width of the area UV mapped in the sprite sheet texture, in pixels",
        min=1, default=1, subtype="PIXEL", step=100)
    dst_frame_height: bpy.props.FloatProperty(
        name="Destination Frame Height",
        description="Height of the area UV mapped in the sprite sheet texture, in pixels",
        min=1, default=1, subtype="PIXEL", step=100)
    auto_dst_frame_offset_x: bpy.props.FloatProperty(default=0, subtype="PIXEL", step=100)
    auto_dst_frame_offset_y: bpy.props.FloatProperty(default=0, subtype="PIXEL", step=100)
    auto_dst_frame_width: bpy.props.FloatProperty(min=1, default=1, subtype="PIXEL", step=100)
    auto_dst_frame_height: bpy.props.FloatProperty(min=1, default=1, subtype="PIXEL", step=100)

    def run(self, context):
        self.render_shutdown(context)

        obj = context.active_object
        mat = obj.active_material
        animation_tracks = mat.animation_tracks

        if mat.animation_data and mat.animation_data.action:
            # clear uv_transforms channels
            action = mat.animation_data.action
            for fcurve in action.fcurves:
                if fcurve.data_path.startswith("animation_tracks.uv_transforms"):
                    action.fcurves.remove(fcurve)

        animation_tracks.uv_transforms.clear()
        scale_transform = animation_tracks.uv_transforms.add()
        scale_transform.mode = "SCALE"
        translate_transform = animation_tracks.uv_transforms.add()
        translate_transform.mode = "TRANSLATE"

        img_w, img_h = self._image.size
        frame_w = self.frame_width / img_w
        frame_h = self.frame_height / img_h
        scale_x = frame_w * img_w / self.dst_frame_width
        scale_y = frame_h * img_h / self.dst_frame_height
        frame_offset_x = self.offset_x / img_w - (self.dst_frame_offset_x / img_w) * scale_x
        frame_offset_y = self.offset_y / img_h - (self.dst_frame_offset_y / img_h) * scale_y
        frame_sep_x = self.separation_horizontal / img_w
        frame_sep_y = self.separation_vertical / img_h

        scale_transform.scale = (scale_x, scale_y)
        scale_transform.keyframe_insert(data_path="scale", frame=0)

        frame_end = 0
        frame_end_translation = (0.0, 0.0)
        for y in range(self.frames_vertical):
            for x in range(self.frames_horizontal):
                i = y * self.frames_horizontal + x
                frame = self.frames[i]
                if frame.use:
                    frame_x = frame_offset_x + x * frame_w + x * frame_sep_x
                    frame_y = frame_offset_y + y * frame_h + y * frame_sep_y

                    frame_idx = frame.order * self.keyframe_interval
                    translate_transform.translation = (frame_x, frame_y)
                    translate_transform.keyframe_insert(data_path="translation", frame=frame_idx)

                    next_frame_idx = (frame.order + 1) * self.keyframe_interval
                    if next_frame_idx > frame_end:
                        frame_end = next_frame_idx
                        frame_end_translation = (frame_x, frame_y)

        if frame_end != 0:
            # insert one last keyframe to keep the last frame visible for the specified duration before it loops
            translate_transform.translation = frame_end_translation
            translate_transform.keyframe_insert(data_path="translation", frame=frame_end)

        # make all keyframes constant
        action = mat.animation_data.action
        for fcurve in action.fcurves:
            if fcurve.data_path.startswith("animation_tracks.uv_transforms"):
                for keyframe in fcurve.keyframe_points:
                    keyframe.interpolation = "CONSTANT"

        bpy.context.scene.frame_start = 0
        bpy.context.scene.frame_end = frame_end

        return {'FINISHED'}

    def cancel(self, context):
        self.render_shutdown(context)

    def check(self, context):
        refresh = self.refresh_ui
        self.refresh_ui = False
        return refresh

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.context_pointer_set("operator_uv_sprite_sheet_anim", self)
        # for accessing the image in callbacks, operators don't support PointerProperties and
        # instance attributes don't carry over in callbacks nor with the previous context pointer
        layout.context_pointer_set("operator_uv_sprite_sheet_anim_image", self._image)

        split = layout.split(factor=0.55)
        left_col = split.column()
        col = left_col.column(align=True)
        col.prop(self, "frames_horizontal", text="Frames Horizontal")
        col.prop(self, "frames_vertical", text="Vertical")

        col = left_col.column(align=True)
        col.prop(self, "frame_width", text="Frame Width")
        col.prop(self, "frame_height", text="Height")

        col = left_col.column(align=True)
        col.prop(self, "offset_x", text="Offset X")
        col.prop(self, "offset_y", text="Y")

        col = left_col.column(align=True)
        col.prop(self, "separation_horizontal", text="Separation Horizontal")
        col.prop(self, "separation_vertical", text="Vertical")

        left_col.prop(self, "keyframe_interval")

        left_col.prop(self, "use_dst_frame", text="Destination Frame")
        col = left_col.column(align=True)
        col.active = col.enabled = self.use_dst_frame
        col.prop(self, "dst_frame_offset_x", text="Offset X")
        col.prop(self, "dst_frame_offset_y", text="Offset Y")
        col.prop(self, "dst_frame_width", text="Width")
        col.prop(self, "dst_frame_height", text="Height")
        left_col.separator()

        right_col = split.column()
        col = right_col.column(align=True)
        col.use_property_split = False
        row = col.row()
        row.label(text="Frames to Use")
        row = row.row(align=True)
        row.operator(SOLLUMZ_OT_uv_sprite_sheet_anim_select_all_frames.bl_idname)
        row.operator(SOLLUMZ_OT_uv_sprite_sheet_anim_clear_frames.bl_idname)
        col.separator()
        row = col.row(align=True)
        FRAME_BUTTOM_SCALE_Y = 0.825
        row.scale_y = FRAME_BUTTOM_SCALE_Y
        for y in range(self.frames_vertical):
            for x in range(self.frames_horizontal):
                i = y * self.frames_horizontal + x
                frame = self.frames[i]
                row.prop(frame, "use", text=f"{frame.order}" if frame.use else " ", toggle=True)
            row = col.row(align=True)
            row.scale_y = FRAME_BUTTOM_SCALE_Y
        right_col.separator()

    def render_callback(self, context):
        import gpu
        import gpu_extras
        from gpu_extras import batch
        import blf

        img_w, img_h = self._image.size
        dst_x, dst_y, dst_w, dst_h = self._render_image_bounds

        # render settings
        line_width = 2
        theme = context.preferences.themes[0]
        background_color = theme.user_interface.wcol_menu_back.inner
        empty_area_overlay_color = (0.05, 0.05, 0.05, 0.9)
        dst_frame_overlay_color = (0.9, 0.9, 0.9, 0.35)
        frame_bounds_color = theme.user_interface.wcol_toggle.outline
        frame_bounds_color = (frame_bounds_color[0],
                              frame_bounds_color[1],
                              frame_bounds_color[2],
                              1.0)
        selected_frame_bounds_color = theme.user_interface.wcol_toggle.inner_sel
        selected_frame_overlay_color = (selected_frame_bounds_color[0],
                                        selected_frame_bounds_color[1],
                                        selected_frame_bounds_color[2],
                                        0.325)
        selected_frame_order_number_color = theme.user_interface.wcol_toggle.text_sel
        selected_frame_order_number_color = (selected_frame_order_number_color[0],
                                             selected_frame_order_number_color[1],
                                             selected_frame_order_number_color[2],
                                             1.0)
        selected_frame_order_number_font_size = 18 * (bpy.context.preferences.system.dpi / 72)
        selected_frame_order_number_font_id = 0

        # vertex buffers
        rects_pos = [[], []]
        rects_color = [[], []]
        filled_rects_pos = []
        filled_rects_color = []

        def _draw_rect(x, y, w, h, color, layer=0):
            buf_pos = rects_pos[layer]
            buf_color = rects_color[layer]
            buf_pos.append((x, y))
            buf_pos.append((x + w, y))
            buf_pos.append((x + w, y))
            buf_pos.append((x + w, y - h))
            buf_pos.append((x + w, y - h))
            buf_pos.append((x, y - h))
            buf_pos.append((x, y - h))
            buf_pos.append((x, y))
            for _ in range(8):
                buf_color.append(color)

        def _fill_rect(x, y, w, h, color):
            filled_rects_pos.append((x, y))
            filled_rects_pos.append((x + w, y))
            filled_rects_pos.append((x + w, y - h))
            filled_rects_pos.append((x, y))
            filled_rects_pos.append((x, y - h))
            filled_rects_pos.append((x + w, y - h))
            for _ in range(6):
                filled_rects_color.append(color)

        def _render_rects():
            for i in range(len(rects_pos)):
                pos = rects_pos[i]
                color = rects_color[i]
                if len(pos) > 0:
                    batch = gpu_extras.batch.batch_for_shader(self._render_color_line_shader, "LINES",
                                                              {"pos": pos, "color": color})
                    batch.draw(self._render_color_line_shader)
                    pos.clear()
                    color.clear()

            if len(filled_rects_pos) > 0:
                batch = gpu_extras.batch.batch_for_shader(self._render_color_shader, "TRIS",
                                                          {"pos": filled_rects_pos, "color": filled_rects_color})
                batch.draw(self._render_color_shader)
                filled_rects_pos.clear()
                filled_rects_color.clear()

        gpu.state.blend_set("ALPHA")
        gpu.state.line_width_set(line_width)

        # render background
        _fill_rect(dst_x, dst_y, dst_w, dst_h, background_color)
        _render_rects()

        # render image
        img_shader = self._render_image_shader
        img_shader.bind()
        img_shader.uniform_sampler("image", self._render_image_texture)
        self._render_image_batch.draw(img_shader)

        # destination frame bounds
        if self.use_dst_frame:
            _fill_rect(dst_x + self.dst_frame_offset_x / img_h * dst_h,
                       dst_y - self.dst_frame_offset_y / img_h * dst_h,
                       self.dst_frame_width / img_w * dst_w,
                       self.dst_frame_height / img_h * dst_h,
                       dst_frame_overlay_color)

        # calculate frame bounds rectangles
        order_numbers = []
        frame_w = self.frame_width / img_w * dst_w
        frame_h = self.frame_height / img_h * dst_h
        frame_offset_x = self.offset_x / img_w * dst_w
        frame_offset_y = self.offset_y / img_h * dst_h
        frame_sep_x = self.separation_horizontal / img_w * dst_w
        frame_sep_y = self.separation_vertical / img_h * dst_h
        for y in range(self.frames_vertical):
            frame_y = dst_y - frame_offset_y - y * frame_h - y * frame_sep_y
            for x in range(self.frames_horizontal):
                frame_x = dst_x + frame_offset_x + x * frame_w + x * frame_sep_x

                i = y * self.frames_horizontal + x
                frame = self.frames[i]
                rect_x = frame_x + line_width / 2
                rect_y = frame_y - line_width / 2
                rect_w = frame_w - line_width / 2
                rect_h = frame_h - line_width / 2
                if frame.use:
                    _draw_rect(rect_x, rect_y, rect_w, rect_h, selected_frame_bounds_color, layer=1)
                    _fill_rect(rect_x, rect_y, rect_w, rect_h, selected_frame_overlay_color)

                    order_numbers.append(((frame_x, frame_y, frame_w, frame_h), frame.order))
                else:
                    _draw_rect(rect_x, rect_y, rect_w, rect_h, frame_bounds_color, layer=0)

                if frame_sep_x > 0 and x != self.frames_horizontal - 1:
                    _fill_rect(frame_x + frame_w, frame_y, frame_sep_x, frame_h, empty_area_overlay_color)

            if frame_sep_y > 0 and y != self.frames_vertical - 1:
                _fill_rect(dst_x, frame_y - frame_h, dst_w, frame_sep_y, empty_area_overlay_color)
                # TODO: same dark overlay for offset_x/y

        # render frame bounds rectangles
        _render_rects()

        # draw order numbers on selected frames
        k = 0
        blf.enable(selected_frame_order_number_font_id, blf.CLIPPING)
        for bounds, number in order_numbers:
            x, y, w, h = bounds
            blf.position(selected_frame_order_number_font_id, x + 5, y - 25, 0)
            blf.clipping(selected_frame_order_number_font_id, x, y - h, x + w, y)
            blf.color(selected_frame_order_number_font_id, *selected_frame_order_number_color)
            blf.size(selected_frame_order_number_font_id, selected_frame_order_number_font_size)
            blf.draw(selected_frame_order_number_font_id, f"{number}")
            k += 1

    def render_init(self, context):
        import gpu
        import gpu_extras

        self._space = context.space_data
        self._render_color_shader = gpu.shader.from_builtin("FLAT_COLOR")
        if bpy.app.version >= (4, 5, 0):
            self._render_color_line_shader = gpu.shader.from_builtin("POLYLINE_FLAT_COLOR")
        else:
            self._render_color_line_shader = self._render_color_shader
        self._render_image_shader = gpu.shader.from_builtin("IMAGE")
        self._render_image_texture = gpu.texture.from_image(self._image)
        img_w, img_h = self._image.size
        x, y = 24, 16
        if img_w > img_h:  # keep aspect ratio
            w, h = 512, 512 * img_h / img_w
        else:
            w, h = 512 * img_w / img_h, 512

        self._render_image_bounds = (x, y + h, w, h)
        self._render_image_batch = gpu_extras.batch.batch_for_shader(
            self._render_image_shader, "TRI_FAN",
            {
                "pos": ((x, y), (x + w, y), (x + w, y + h), (x, y + h)),
                "texCoord": ((0, 0), (1, 0), (1, 1), (0, 1)),
            })
        self._render_handler = self._space.draw_handler_add(self.render_callback, (context,), 'WINDOW', 'POST_PIXEL')

    def render_shutdown(self, context):
        self._space.draw_handler_remove(self._render_handler, 'WINDOW')

    def search_image(self, context):
        self._image = None
        nodes = context.active_object.active_material.node_tree.nodes
        for n in nodes:
            if isinstance(n, bpy.types.ShaderNodeTexImage) and n.is_sollumz:
                if n.image:
                    self._image = n.image
                    break

        return self._image is not None

    def calc_destination_frame_size(self, context):
        # default to the whole image.
        img_w, img_h = self._image.size
        self.auto_dst_frame_offset_x = 0
        self.auto_dst_frame_offset_y = 0
        self.auto_dst_frame_width = img_w
        self.auto_dst_frame_height = img_h
        self.dst_frame_offset_x = self.auto_dst_frame_offset_x
        self.dst_frame_offset_y = self.auto_dst_frame_offset_y
        self.dst_frame_width = self.auto_dst_frame_width
        self.dst_frame_height = self.auto_dst_frame_height

        mesh = context.active_object.data
        if not isinstance(mesh, bpy.types.Mesh):
            return

        # calculate the UV bounds
        import sys
        uvs = mesh.uv_layers.active.uv
        min_u = sys.float_info.max
        min_v = sys.float_info.max
        max_u = sys.float_info.min
        max_v = sys.float_info.min
        for uv in uvs:
            u, v = flip_uv(uv.vector)
            min_u = min(min_u, u)
            min_v = min(min_v, v)
            max_u = max(max_u, u)
            max_v = max(max_v, v)
        else:
            uvs = mesh.uv_layers.active.data
            for uv_loop in uvs:
                u, v = flip_uv(uv_loop.uv)
                min_u = min(min_u, u)
                min_v = min(min_v, v)
                max_u = max(max_u, u)
                max_v = max(max_v, v)

        if (min_u == sys.float_info.max or min_v == sys.float_info.max or
                max_u == sys.float_info.min or max_v == sys.float_info.min):
            return

        # calculate the UV bounds in pixels
        min_u *= img_w
        min_v *= img_h
        max_u *= img_w
        max_v *= img_h

        self.auto_dst_frame_offset_x = min_u
        self.auto_dst_frame_offset_y = min_v
        self.auto_dst_frame_width = max_u - min_u
        self.auto_dst_frame_height = max_v - min_v
        self.dst_frame_offset_x = self.auto_dst_frame_offset_x
        self.dst_frame_offset_y = self.auto_dst_frame_offset_y
        self.dst_frame_width = self.auto_dst_frame_width
        self.dst_frame_height = self.auto_dst_frame_height

    def invoke(self, context, event):
        if not self.search_image(context):
            self.error("No texture found in material")
            return {"CANCELLED"}

        if self.first_run:
            with context.temp_override(operator_uv_sprite_sheet_anim=self,
                                       operator_uv_sprite_sheet_anim_image=self._image):  # see draw()
                self.frames_horizontal = 4
                self.frames_vertical = 4
                self.calc_destination_frame_size(context)
        self.render_init(context)
        self.first_run = False
        return context.window_manager.invoke_props_dialog(self, width=650)


class SOLLUMZ_OT_timeline_clip_tags_drag(SOLLUMZ_OT_base, bpy.types.Operator):
    bl_idname = "sollumz.timeline_clip_tags_drag"
    bl_label = "Sollumz - Drag Timeline Clip Tags"
    bl_description = "Drag clip tag markers in the timeline"

    @classmethod
    def poll(cls, context):
        return (context.region is not None and
                context.active_object is not None and
                context.active_object.sollum_type == SollumType.CLIP)

    def run(self, context):
        return {"FINISHED"}

    def invoke(self, context, event):
        if event is None:
            return {"PASS_THROUGH"}

        clip_obj = context.active_object
        clip_properties = clip_obj.clip_properties

        num_tags = len(clip_properties.tags)
        clip_frame_duration = clip_properties.get_duration_in_frames()
        if num_tags == 0 or clip_frame_duration == 0:
            return {"PASS_THROUGH"}

        region = context.region

        mouse_x = event.mouse_region_x
        mouse_y = event.mouse_region_y

        if mouse_y >= region.height - 23.5:  # ignore if mouse is on the timeline scrubber
            self.clear_hovered_state(region, clip_obj)
            return {"PASS_THROUGH"}

        dragging = False
        if event.type == "MOUSEMOVE":
            self.update_hovered_state(region, mouse_x, mouse_y, clip_obj)
            dragging = self.handle_dragging(region, mouse_x, mouse_y, clip_obj)
        elif event.type == "LEFTMOUSE" and event.value == "PRESS":
            self.update_hovered_state(region, mouse_x, mouse_y, clip_obj)
            dragging = self.update_drag_state(clip_obj)
        elif event.type == "LEFTMOUSE" and event.value == "RELEASE":
            self.clear_drag_state(clip_obj)
        elif event.type == "LEFTMOUSE" and event.value == "DOUBLE_CLICK":
            self.update_hovered_state(region, mouse_x, mouse_y, clip_obj)
            self.split_hovered_tag(region, clip_obj)

        if dragging:
            region.tag_redraw()
            return {"FINISHED"}
        else:
            return {"PASS_THROUGH"}

    def split_hovered_tag(self, region, clip_obj):
        clip_properties = clip_obj.clip_properties

        for clip_tag in clip_properties.tags:
            if not clip_tag.ui_view_on_timeline:
                continue
            if clip_tag.start_phase != clip_tag.end_phase:
                continue  # already splitted
            if not clip_tag.ui_timeline_hovered_start:
                continue  # not selected

            offset = 0.025
            clip_tag.start_phase = max(clip_tag.start_phase - offset, 0.0)
            clip_tag.end_phase = min(clip_tag.start_phase + offset * 2, 1.0)
            clip_tag.start_phase = max(clip_tag.end_phase - offset * 2, 0.0)
            region.tag_redraw()
            break

    def update_hovered_state(self, region, mouse_x, mouse_y, clip_obj):
        clip_properties = clip_obj.clip_properties
        clip_frame_duration = clip_properties.get_duration_in_frames()

        view = region.view2d

        any_change = False
        for clip_tag in clip_properties.tags:
            if not clip_tag.ui_view_on_timeline:
                continue

            start_phase = clip_tag.start_phase
            end_phase = clip_tag.end_phase

            start_frame = clip_frame_duration * start_phase
            end_frame = clip_frame_duration * end_phase

            start_x, _ = view.view_to_region(start_frame, 0, clip=False)
            end_x, _ = view.view_to_region(end_frame, 0, clip=False)
            hover_threshold = 2

            old_hovered_start = clip_tag.ui_timeline_hovered_start
            old_hovered_end = clip_tag.ui_timeline_hovered_end
            new_hovered_start = start_x - hover_threshold <= mouse_x <= start_x + hover_threshold
            new_hovered_end = end_x - hover_threshold <= mouse_x <= end_x + hover_threshold
            clip_tag.ui_timeline_hovered_start = new_hovered_start
            clip_tag.ui_timeline_hovered_end = new_hovered_end

            any_change = any_change or old_hovered_start != new_hovered_start or old_hovered_end != new_hovered_end

        if any_change:
            region.tag_redraw()

    def clear_hovered_state(self, region, clip_obj):
        clip_properties = clip_obj.clip_properties

        any_change = False
        for clip_tag in clip_properties.tags:
            if not clip_tag.ui_view_on_timeline:
                continue

            old_hovered_start = clip_tag.ui_timeline_hovered_start
            old_hovered_end = clip_tag.ui_timeline_hovered_end
            new_hovered_start = False
            new_hovered_end = False
            clip_tag.ui_timeline_hovered_start = new_hovered_start
            clip_tag.ui_timeline_hovered_end = new_hovered_end

            any_change = any_change or old_hovered_start != new_hovered_start or old_hovered_end != new_hovered_end

        if any_change:
            region.tag_redraw()

    def update_drag_state(self, clip_obj):
        any_dragging = False
        clip_properties = clip_obj.clip_properties
        for clip_tag in reversed(clip_properties.tags):  # reversed so the tag drawn on top is always picked first
            if not clip_tag.ui_view_on_timeline:
                continue

            if any_dragging:
                clip_tag.ui_timeline_drag_start = False
                clip_tag.ui_timeline_drag_end = False
            else:
                clip_tag.ui_timeline_drag_start = clip_tag.ui_timeline_hovered_start
                clip_tag.ui_timeline_drag_end = clip_tag.ui_timeline_hovered_end
                any_dragging = any_dragging or clip_tag.ui_timeline_drag_start or clip_tag.ui_timeline_drag_end
        return any_dragging

    def clear_drag_state(self, clip_obj):
        clip_properties = clip_obj.clip_properties
        for clip_tag in clip_properties.tags:
            clip_tag.ui_timeline_drag_start = False
            clip_tag.ui_timeline_drag_end = False

    def handle_dragging(self, region, mouse_x, mouse_y, clip_obj):
        clip_properties = clip_obj.clip_properties
        clip_frame_duration = clip_properties.get_duration_in_frames()

        view = region.view2d
        curr_frame, _ = view.region_to_view(mouse_x, mouse_y)
        curr_phase = curr_frame / clip_frame_duration

        any_dragging = False
        clip_properties = clip_obj.clip_properties
        for clip_tag in clip_properties.tags:
            if not clip_tag.ui_timeline_drag_start and not clip_tag.ui_timeline_drag_end:
                continue

            any_dragging = True
            if clip_tag.ui_timeline_drag_start:
                clip_tag.start_phase = curr_phase

            if clip_tag.ui_timeline_drag_end:
                clip_tag.end_phase = curr_phase

        return any_dragging


addon_keymaps = []


def register():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        for name, space_type in (("Dopesheet", "DOPESHEET_EDITOR"), ("NLA Editor", "NLA_EDITOR")):
            km = wm.keyconfigs.addon.keymaps.new(name=name, space_type=space_type, region_type="WINDOW")
            kmi = km.keymap_items.new(SOLLUMZ_OT_timeline_clip_tags_drag.bl_idname, "MOUSEMOVE", "ANY")
            addon_keymaps.append((km, kmi))
            kmi = km.keymap_items.new(SOLLUMZ_OT_timeline_clip_tags_drag.bl_idname, "LEFTMOUSE", "ANY")
            addon_keymaps.append((km, kmi))


def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
