from typing import Iterable

import bpy
import math
from mathutils import Matrix, Vector
from ..sollumz_properties import SollumType
from ..tools.animationhelper import retarget_animation, get_target_from_id, update_uv_clip_hash, get_scene_fps


def animations_filter(self, object):
    if len(bpy.context.selected_objects) <= 0:
        return False

    active_object = bpy.context.selected_objects[0]

    if active_object.sollum_type != SollumType.CLIP:
        return False

    return object.sollum_type == SollumType.ANIMATION and active_object.parent.parent == object.parent.parent


ClipAttributeTypes = [
    ("Float", "Float", "Float", 0),
    ("Int", "Int", "Int", 1),
    ("Bool", "Bool", "Bool", 2),
    ("Vector3", "Vector3", "Vector3", 3),
    ("Vector4", "Vector4", "Vector4", 4),
    ("String", "String", "String", 5),
    ("HashString", "HashString", "HashString", 6),
]


class ClipAttribute(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name", default="")
    type: bpy.props.EnumProperty(name="Type", items=ClipAttributeTypes)
    value_float: bpy.props.FloatProperty(name="Value", default=0.0)
    value_int: bpy.props.IntProperty(name="Value", default=0)
    value_bool: bpy.props.BoolProperty(name="Value", default=False)
    value_vec3: bpy.props.FloatVectorProperty(name="Value", default=(0.0, 0.0, 0.0), size=3)
    value_vec4: bpy.props.FloatVectorProperty(name="Value", default=(0.0, 0.0, 0.0, 0.0), size=4)
    value_string: bpy.props.StringProperty(name="Value", default="")  # used with String and HashString


class ClipTag(bpy.types.PropertyGroup):
    def on_start_phase_changed(self, context):
        if self.end_phase < self.start_phase:
            self.end_phase = self.start_phase

    def on_end_phase_changed(self, context):
        if self.start_phase > self.end_phase:
            self.start_phase = self.end_phase

    name: bpy.props.StringProperty(name="Name", default="")

    start_phase: bpy.props.FloatProperty(
        name="Start Phase", description="Start phase of the tag",
        default=0, min=0, max=1, step=1, update=on_start_phase_changed)
    end_phase: bpy.props.FloatProperty(
        name="End Phase", description="End phase of the tag",
        default=0, min=0, max=1, step=1, update=on_end_phase_changed)

    attributes: bpy.props.CollectionProperty(name="Attributes", type=ClipAttribute)

    ui_active_attribute_index: bpy.props.IntProperty()
    ui_show_expanded: bpy.props.BoolProperty(
        name="Show Expanded", description="Show details of the tag",
        default=True)
    ui_view_on_timeline: bpy.props.BoolProperty(
        name="View on Timeline", description="Show tag on the timeline",
        default=True)
    ui_timeline_color: bpy.props.FloatVectorProperty(
        name="Timeline Color", description="Color of the tag on the timeline",
        default=(1.0, 0.0, 0.0, 1.0), size=4, subtype="COLOR", min=0.0, max=1.0)
    ui_timeline_hovered_start: bpy.props.BoolProperty(
        name="Timeline Hovered Start", description="Is the tag start marker hovered on the timeline?",
        default=False, options={"HIDDEN", "SKIP_SAVE"})
    ui_timeline_hovered_end: bpy.props.BoolProperty(
        name="Timeline Hovered End", description="Is the tag end marker hovered on the timeline?",
        default=False, options={"HIDDEN", "SKIP_SAVE"})
    ui_timeline_drag_start: bpy.props.BoolProperty(
        name="Timeline Drag Start", description="Is the tag start marker being dragged on the timeline?",
        default=False, options={"HIDDEN", "SKIP_SAVE"})
    ui_timeline_drag_end: bpy.props.BoolProperty(
        name="Timeline Drag End", description="Is the tag end marker being dragged on the timeline?",
        default=False, options={"HIDDEN", "SKIP_SAVE"})


class ClipProperty(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name", default="")
    attributes: bpy.props.CollectionProperty(name="Attributes", type=ClipAttribute)

    ui_show_expanded: bpy.props.BoolProperty(
        name="Show Expanded", default=True, description="Show details of the property")


class ClipAnimation(bpy.types.PropertyGroup):
    def on_animation_changed(self, context):
        if self.animation is None:
            return

        animation_properties = self.animation.animation_properties
        action = animation_properties.action
        if action is not None:
            # set frame range to the full action frame range by default
            frame_range = action.frame_range
            self.start_frame = frame_range[0]
            self.end_frame = frame_range[1]

        if isinstance(animation_properties.get_target(), bpy.types.Material):
            # if UV animation, automatically calculate clip hash
            clip_obj = self.id_data
            update_uv_clip_hash(clip_obj)

    start_frame: bpy.props.FloatProperty(
        name="Start Frame", default=0, min=0, step=100, description="First frame of the playback area")
    end_frame: bpy.props.FloatProperty(
        name="End Frame", default=0, min=0, step=100, description="Last frame (inclusive) of the playback area")

    animation: bpy.props.PointerProperty(
        name="Animation", type=bpy.types.Object, poll=animations_filter, update=on_animation_changed)

    ui_show_expanded: bpy.props.BoolProperty(
        name="Show Expanded", default=True, description="Show details of the linked animation")


class ClipProperties(bpy.types.PropertyGroup):
    hash: bpy.props.StringProperty(name="Hash", default="")
    name: bpy.props.StringProperty(name="Name", default="")

    duration: bpy.props.FloatProperty(
        name="Duration", description="Duration of the clip in seconds",
        default=0, min=0, subtype="TIME_ABSOLUTE")

    animations: bpy.props.CollectionProperty(name="Animations", type=ClipAnimation)

    tags: bpy.props.CollectionProperty(name="Tags", type=ClipTag)

    properties: bpy.props.CollectionProperty(name="Properties", type=ClipProperty)

    def get_duration_in_frames(self) -> float:
        """Number of frames this clip lasts. Includes subframes."""
        return self.duration * get_scene_fps()


AnimationTargetIDTypes = [
    ("ARMATURE", "Armature", "Armature", "ARMATURE_DATA", 0),
    ("CAMERA", "Camera", "Camera", "CAMERA_DATA", 1),
    ("MATERIAL", "Material", "Material", "MATERIAL_DATA", 2),
]


class AnimationProperties(bpy.types.PropertyGroup):
    def on_target_update(self, context):
        # print(f"Target updated: {self.target_id} (prev {self.target_id_prev})")
        if self.target_id != self.target_id_prev and self.action:
            # print("  Retargeting animation")
            retarget_animation(self.id_data, self.target_id_prev, self.target_id)

        self.target_id_prev = self.target_id

    hash: bpy.props.StringProperty(name="Hash", default="")
    action: bpy.props.PointerProperty(name="Action", type=bpy.types.Action)

    target_id: bpy.props.PointerProperty(name="Target", type=bpy.types.ID, update=on_target_update)
    target_id_prev: bpy.props.PointerProperty(name="Target (Prev)", type=bpy.types.ID)
    target_id_type: bpy.props.EnumProperty(name="Target Type", items=AnimationTargetIDTypes, default="ARMATURE")

    def get_target(self) -> bpy.types.ID:
        """Returns the ID instance where the animation data should be created to play the animation."""
        return get_target_from_id(self.target_id)


UVTransformModes = [
    ("TRANSLATE", "Translate", "Translate", 0),
    ("ROTATE", "Rotate", "Rotate", 1),
    ("SCALE", "Scale", "Scale", 2),
    ("SHEAR", "Shear", "Shear", 3),
    ("REFLECT", "Reflect", "Reflect across an axis", 4),
]


class UVTransform(bpy.types.PropertyGroup):
    def on_update(self, context):
        if self.id_data is not None and self.update_uv_transform_matrix_on_change:
            self.id_data.animation_tracks.update_uv_transform_matrix()

    # we use custom getters/setters because the properties update callback is not called during animation playback
    # and the UV matrix would not get updated when the value is changed by an animation
    def values_array(self):
        values = self.get("values")
        if not values:
            # tx, ty, rotation, scale_x, scale_y, shear_x, shear_y, reflect_x, reflect_y
            self["values"] = [0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 1.0, 0.0]
            values = self["values"]  # lookup again to get array converted to a IDPropertyArray instance
        return values

    @staticmethod
    def _float_getter(index):
        def getter(self):
            return self.values_array()[index]
        return getter

    @staticmethod
    def _float_setter(index):
        def setter(self, value):
            self.values_array()[index] = value
            self.on_update(None)
        return setter

    @staticmethod
    def _vec2_getter(index_x, index_y):
        def getter(self):
            values = self.values_array()
            return (values[index_x], values[index_y])
        return getter

    @staticmethod
    def _vec2_setter(index_x, index_y):
        def setter(self, value):
            values = self.values_array()
            values[index_x] = value[0]
            values[index_y] = value[1]
            self.on_update(None)
        return setter

    update_uv_transform_matrix_on_change: bpy.props.BoolProperty(default=True, options={"HIDDEN", "SKIP_SAVE"})
    mode: bpy.props.EnumProperty(
        name="Transformation Mode", items=UVTransformModes, default="TRANSLATE", update=on_update, options=set())
    translation: bpy.props.FloatVectorProperty(
        name="Translation", size=2, subtype="XYZ", get=_vec2_getter(0, 1), set=_vec2_setter(0, 1))
    rotation: bpy.props.FloatProperty(
        name="Rotation", subtype="ANGLE", unit="ROTATION", get=_float_getter(2), set=_float_setter(2))
    scale: bpy.props.FloatVectorProperty(
        name="Scale", size=2, subtype="XYZ", get=_vec2_getter(3, 4), set=_vec2_setter(3, 4))
    shear: bpy.props.FloatVectorProperty(
        name="Shear", size=2, subtype="XYZ", get=_vec2_getter(5, 6), set=_vec2_setter(5, 6))
    reflect: bpy.props.FloatVectorProperty(
        name="Reflection Axis", size=2, subtype="XYZ", get=_vec2_getter(7, 8), set=_vec2_setter(7, 8))

    def get_matrix(self) -> Matrix:
        """
        Returns the affine matrix for this transform.
        """
        if self.mode == "TRANSLATE":
            return Matrix((
                (1.0, 0.0, self.translation[0]),
                (0.0, 1.0, self.translation[1]),
                (0.0, 0.0, 1.0)
            ))
        elif self.mode == "ROTATE":
            cos = math.cos(self.rotation)
            sin = math.sin(self.rotation)
            return Matrix((
                (cos, -sin, 0.0),
                (sin, cos, 0.0),
                (0.0, 0.0, 1.0)
            ))
        elif self.mode == "SCALE":
            return Matrix((
                (self.scale[0], 0.0, 0.0),
                (0.0, self.scale[1], 0.0),
                (0.0, 0.0, 1.0)
            ))
        elif self.mode == "SHEAR":
            return Matrix((
                (1.0, self.shear[0], 0.0),
                (self.shear[1], 1.0, 0.0),
                (0.0, 0.0, 1.0)
            ))
        elif self.mode == "REFLECT":
            v = Vector(self.reflect)
            if v.length_squared == 0.0:
                return Matrix.Identity(3)
            v.normalize()
            a = v.x ** 2 - v.y ** 2
            b = 2 * v.x * v.y
            c = b
            d = v.y ** 2 - v.x ** 2
            return Matrix((
                (a, b, 0.0),
                (c, d, 0.0),
                (0.0, 0.0, 1.0)
            ))
        else:
            return Matrix.Identity(3)

    def copy_from(self, other: "UVTransform"):
        self.mode = other.mode
        self_values = self.values_array()
        other_values = other.values_array()
        for i in range(len(self_values)):
            self_values[i] = other_values[i]


class AnimationTracks(bpy.types.PropertyGroup):
    @staticmethod
    def Vec3Prop(name, subtype="TRANSLATION", default=(0.0, 0.0, 0.0)):
        return bpy.props.FloatVectorProperty(name=name, size=3, subtype=subtype, default=default)

    @staticmethod
    def QuatProp(name, default=(1.0, 0.0, 0.0, 0.0)):
        return bpy.props.FloatVectorProperty(name=name, size=4, subtype="QUATERNION", default=default)

    @staticmethod
    def FloatProp(name, subtype="NONE", default=0.0, min=-3.402823e+38, max=3.402823e+38):
        return bpy.props.FloatProperty(name=name, subtype=subtype, default=default, min=min, max=max)

    mover_location: Vec3Prop("Mover Location")  # aka root motion
    mover_rotation: QuatProp("Mover Rotation")
    camera_location: Vec3Prop("Camera Location")
    camera_rotation: QuatProp("Camera Rotation")
    uv0: Vec3Prop("UV 0", subtype="XYZ", default=(1.0, 0.0, 0.0))
    uv1: Vec3Prop("UV 1", subtype="XYZ", default=(0.0, 1.0, 0.0))
    unk_22: FloatProp("Unk 22")
    unk_24: FloatProp("Unk 24")
    unk_25: Vec3Prop("Unk 25", subtype="XYZ")
    unk_26: QuatProp("Unk 26")
    camera_fov: FloatProp("Camera FOV", default=39.6, min=1.0, max=130.0)  # in degrees, 1.0-130.0
    camera_dof: Vec3Prop("Camera DOF", subtype="XYZ")  # x=near, y=far, z=unused
    unk_29: Vec3Prop("Unk 29", subtype="XYZ")
    unk_30: FloatProp("Unk 30")
    unk_31: FloatProp("Unk 31")
    unk_32: FloatProp("Unk 32")
    unk_33: FloatProp("Unk 33") # high heels related (used on BONETAG_HIGH_HEELS, which doesn't seem to be a real bone)
    unk_34: Vec3Prop("Unk 34", subtype="XYZ")
    camera_dof_strength: FloatProp("Camera DOF Strength", min=0.0, max=1.0)  # 0.0-1.0
    camera_unk_39: FloatProp("Camera Unk 39", min=0.0, max=1.0)  # boolean flag, true= >0.5, false= <=0.5
    unk_40: FloatProp("Unk 40")
    unk_41: FloatProp("Unk 41")
    unk_42: Vec3Prop("Unk 42", subtype="XYZ")
    # alternative to camera_dof track, all 4 must be set to be used
    camera_dof_plane_near_unk: FloatProp("Camera DOF Plane Near Unk")
    camera_dof_plane_near: FloatProp("Camera DOF Plane Near")
    camera_dof_plane_far_unk: FloatProp("Camera DOF Plane Far Unk")
    camera_dof_plane_far: FloatProp("Camera DOF Plane Far")
    unk_47: FloatProp("Unk 47")
    camera_unk_48: FloatProp("Camera Unk 48", min=0.0, max=1.0)  # boolean flag, true= >0.5, false= <=0.5
    camera_dof_unk_49: FloatProp("Camera DOF Unk 49")  # used with camera_dof_plane_* tracks
    unk_50: FloatProp("Unk 50")
    camera_dof_unk_51: FloatProp("Camera DOF Unk 51")  # used with camera_dof_plane_* tracks
    unk_52: FloatProp("Unk 52")
    unk_53: FloatProp("Unk 53")
    unk_134: FloatProp("Unk 134")
    unk_136: FloatProp("Unk 136")
    unk_137: FloatProp("Unk 137")
    unk_138: FloatProp("Unk 138")
    unk_139: FloatProp("Unk 139")
    unk_140: FloatProp("Unk 140")

    def update_uv_transform_matrix(self):
        mat = calculate_final_uv_transform_matrix(self.uv_transforms)
        self.uv0[0] = mat[0][0]
        self.uv0[1] = mat[0][1]
        self.uv0[2] = mat[0][2]
        self.uv1[0] = mat[1][0]
        self.uv1[1] = mat[1][1]
        self.uv1[2] = mat[1][2]

        if bpy.context.screen is not None:
            for area in bpy.context.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()

    uv_transforms: bpy.props.CollectionProperty(type=UVTransform,
                                                name="UV Transformations")
    uv_transforms_active_index: bpy.props.IntProperty(name="Active UV Transformation", options=set())


def calculate_final_uv_transform_matrix(uv_transforms: Iterable[UVTransform]) -> Matrix:
    mat = Matrix.Identity(3)
    for transform in uv_transforms:
        mat = transform.get_matrix() @ mat
    return mat


def register_tracks(cls, inline=False):
    if inline:
        # Workaround for https://projects.blender.org/blender/blender/issues/48975
        # "Custom Properties within PropertyGroups cannot be animated when attached to a PoseBone"
        # So we have to add the properties directly to the class instead of using a PointerProperty
        for prop, info in AnimationTracks.__annotations__.items():
            setattr(cls, f"animation_tracks_{prop}", info)
    else:
        cls.animation_tracks = bpy.props.PointerProperty(name="Animation Tracks", type=AnimationTracks)


def unregister_tracks(cls, inline=False):
    if inline:
        for prop, info in AnimationTracks.__annotations__.items():
            delattr(cls, f"animation_tracks_{prop}")
    else:
        del cls.animation_tracks


def register():
    bpy.types.Object.clip_properties = bpy.props.PointerProperty(
        type=ClipProperties)
    bpy.types.Object.animation_properties = bpy.props.PointerProperty(
        type=AnimationProperties)

    register_tracks(bpy.types.PoseBone, inline=True)
    register_tracks(bpy.types.Object)
    register_tracks(bpy.types.Material)

    # used during export to temporarily store UV transforms
    bpy.types.ID.export_uv_transforms = bpy.props.CollectionProperty(
        type=UVTransform, options={"HIDDEN", "SKIP_SAVE"})

    # used with operator SOLLUMZ_OT_animations_set_target
    bpy.types.Scene.sollumz_animations_target_id = bpy.props.PointerProperty(
        name="Target", type=bpy.types.ID, options={"HIDDEN", "SKIP_SAVE"})
    bpy.types.Scene.sollumz_animations_target_id_type = bpy.props.EnumProperty(
        name="Target Type", items=AnimationTargetIDTypes, default="ARMATURE", options={"HIDDEN", "SKIP_SAVE"})


def unregister():
    del bpy.types.Object.clip_properties
    del bpy.types.Object.animation_properties

    unregister_tracks(bpy.types.PoseBone, inline=True)
    unregister_tracks(bpy.types.Object)
    unregister_tracks(bpy.types.Material)
