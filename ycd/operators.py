import bpy
from ..sollumz_helper import SOLLUMZ_OT_base
from ..sollumz_properties import SollumType
from ..tools.blenderhelper import find_child_by_type, get_data_obj
from ..tools.meshhelper import flip_uv
from .ycdimport import create_clip_dictionary_template, create_anim_obj


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

        clip_dictionary_obj = clip_obj.parent.parent
        # TODO: animation may be None, or not all animations have the same target/are filled in
        target = clip_properties.animations[0].animation.animation_properties.get_target()
        if target is None:
            return {"FINISHED"}

        clip_frame_count = round(clip_properties.duration * bpy.context.scene.render.fps)

        groups = {}

        for clip_animation in clip_properties.animations:
            if clip_animation.animation is None:
                continue

            animation_properties = clip_animation.animation.animation_properties

            start_frames = clip_animation.start_frame
            end_frames = clip_animation.end_frame

            action = animation_properties.action

            if action.name not in groups:
                groups[action.name] = []

            group = groups[action.name]

            group.append({
                "name": clip_properties.hash,
                "start_frames": start_frames,
                "end_frames": end_frames,
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
                action_frames_count = clip["end_frames"] - clip["start_frames"]

                nla_strip = track.strips.new(clip["name"], 0, clip["action"])
                nla_strip.frame_start = 0
                nla_strip.frame_end = clip_frame_count

                bpy.context.scene.frame_start = 0
                bpy.context.scene.frame_end = int(nla_strip.frame_end)

                nla_strip.blend_type = "COMBINE"
                nla_strip.extrapolation = "NOTHING"
                nla_strip.name = clip["name"]

                nla_strip.scale = clip_frame_count / action_frames_count
                nla_strip.action_frame_start = clip["start_frames"]
                nla_strip.action_frame_end = clip["end_frames"]

        return {"FINISHED"}


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
    bl_description = "Add a new tag to the clip"

    def run(self, context):
        if len(bpy.context.selected_objects) <= 0:
            return {"FINISHED"}

        active_object = bpy.context.selected_objects[0]

        if active_object.sollum_type != SollumType.CLIP:
            return {"FINISHED"}

        clip_properties = active_object.clip_properties

        clip_properties.tags.add()

        return {"FINISHED"}


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


class SOLLUMZ_OT_animation_fill(SOLLUMZ_OT_base, bpy.types.Operator):
    bl_idname = "sollumz.animation_fill"
    bl_label = "Fill animation data"

    def run(self, context):
        if len(bpy.context.selected_objects) <= 0:
            return {"FINISHED"}

        active_object = bpy.context.selected_objects[0]

        animation_properties = active_object.animation_properties

        action_list = []

        if animation_properties.base_action:
            action_list.append(animation_properties.base_action.frame_range)

        if animation_properties.root_motion_location_action:
            action_list.append(
                animation_properties.root_motion_location_action.frame_range)

        if animation_properties.root_motion_rotation_action:
            action_list.append(
                animation_properties.root_motion_rotation_action.frame_range)

        frames = (
            sorted(set([item for sublist in action_list for item in sublist])))

        start_frame = frames[0]
        end_frame = frames[-1]

        frame_count = end_frame - start_frame

        animation_properties.frame_count = int(frame_count)

        return {"FINISHED"}


class SOLLUMZ_OT_uv_transform_add(SOLLUMZ_OT_base, bpy.types.Operator):
    bl_idname = "sollumz.uv_transform_add"
    bl_label = "Add UV Transformation"
    bl_description = "Add new UV transformation"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def run(self, context):
        if len(bpy.context.selected_objects) <= 0:
            return {"FINISHED"}

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
        if len(bpy.context.selected_objects) <= 0:
            return {"FINISHED"}

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
        if len(bpy.context.selected_objects) <= 0:
            return {"FINISHED"}

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
    frame_duration: bpy.props.FloatProperty(
        name="Frame Duration",
        description="Duration of each frame",
        min=0.0, default=1.0, subtype="TIME_ABSOLUTE")
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
        for y in range(self.frames_vertical):
            for x in range(self.frames_horizontal):
                i = y * self.frames_horizontal + x
                frame = self.frames[i]
                if frame.use:
                    frame_x = frame_offset_x + x * frame_w + x * frame_sep_x
                    frame_y = frame_offset_y + y * frame_h + y * frame_sep_y

                    frame_idx = round(frame.order * self.frame_duration * bpy.context.scene.render.fps)
                    translate_transform.translation = (frame_x, frame_y)
                    translate_transform.keyframe_insert(data_path="translation", frame=frame_idx)
                    next_frame_idx = round((frame.order + 1) * self.frame_duration * bpy.context.scene.render.fps)
                    frame_end = max(frame_end, next_frame_idx)

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

        col = layout.column(align=True)
        col.prop(self, "frames_horizontal", text="Frames Horizontal")
        col.prop(self, "frames_vertical", text="Vertical")

        col = layout.column(align=True)
        col.prop(self, "frame_width", text="Frame Width")
        col.prop(self, "frame_height", text="Height")

        col = layout.column(align=True)
        col.prop(self, "offset_x", text="Offset X")
        col.prop(self, "offset_y", text="Y")

        col = layout.column(align=True)
        col.prop(self, "separation_horizontal", text="Separation Horizontal")
        col.prop(self, "separation_vertical", text="Vertical")

        layout.prop(self, "frame_duration")

        layout.prop(self, "use_dst_frame", text="Destination Frame")
        col = layout.column(align=True)
        col.active = col.enabled = self.use_dst_frame
        col.prop(self, "dst_frame_offset_x", text="Offset X")
        col.prop(self, "dst_frame_offset_y", text="Offset Y")
        col.prop(self, "dst_frame_width", text="Width")
        col.prop(self, "dst_frame_height", text="Height")

        layout.separator()
        col = layout.column(align=True)
        col.use_property_split = False
        row = col.row()
        row.label(text="Frames to Use")
        row = row.row(align=True)
        row.operator(SOLLUMZ_OT_uv_sprite_sheet_anim_select_all_frames.bl_idname)
        row.operator(SOLLUMZ_OT_uv_sprite_sheet_anim_clear_frames.bl_idname)
        col.separator()
        row = col.row(align=True)
        for y in range(self.frames_vertical):
            for x in range(self.frames_horizontal):
                i = y * self.frames_horizontal + x
                frame = self.frames[i]
                row.prop(frame, "use", text=f"{frame.order}" if frame.use else " ", toggle=True)
            row = col.row(align=True)
        layout.separator()

    def render_callback(self, context):
        import gpu
        import gpu_extras
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
                    batch = gpu_extras.batch.batch_for_shader(self._render_color_shader, "LINES",
                                                              {"pos": pos, "color": color})
                    batch.draw(self._render_color_shader)
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
        return context.window_manager.invoke_props_dialog(self)
