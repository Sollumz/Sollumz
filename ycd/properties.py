import bpy
from ..sollumz_properties import SollumType
from ..tools.jenkhash import Generate
from ..tools.animationhelper import retarget_animation


def animations_filter(self, object):
    if len(bpy.context.selected_objects) <= 0:
        return False

    active_object = bpy.context.selected_objects[0]

    if active_object.sollum_type != SollumType.CLIP:
        return False

    return object.sollum_type == SollumType.ANIMATION and active_object.parent.parent == object.parent.parent


def update_hashes(self, context):
    assert False, "update_hashes is outdated"
    animation = context.object
    clip_dict = animation.parent.parent
    anim_drawable_mesh = clip_dict.clip_dict_properties.uv_obj
    anim_drawable_model = anim_drawable_mesh.parent.parent.name
    material_index = None
    for index, mat in enumerate(anim_drawable_mesh.data.materials):
        if mat == self.material:
            material_index = index
            break

    if material_index is None:
        raise Exception("Selected material does not exist with UV object")

    anim_hash = anim_drawable_model + "_uv_" + str(material_index)
    clip_hash = "hash_" + hex(Generate(anim_drawable_model) + (material_index + 1)).strip("0x").upper()
    clip_name = anim_hash + ".clip"
    
    animation.animation_properties.hash = anim_hash

    for item in clip_dict.children:
        if item.sollum_type == SollumType.CLIPS:
            for clip in item.children:
                clip_linked_anims = clip.clip_properties.animations
                for anim in clip_linked_anims:
                    if anim.animation.name == animation.name:
                        clip.clip_properties.hash = clip_hash
                        clip.clip_properties.name = clip_name
                        break


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
    name: bpy.props.StringProperty(name="Name", default="")

    start_phase: bpy.props.FloatProperty(
        name="Start Phase", default=0, min=0, max=1, description="Start phase of the tag")
    end_phase: bpy.props.FloatProperty(
        name="End Phase", default=0, min=0, max=1, description="End phase of the tag")

    attributes: bpy.props.CollectionProperty(name="Attributes", type=ClipAttribute)

    ui_show_expanded: bpy.props.BoolProperty(
        name="Show Expanded", default=True, description="Show details of the tag")
    ui_active_attribute_index: bpy.props.IntProperty()


class ClipAnimation(bpy.types.PropertyGroup):
    start_frame: bpy.props.IntProperty(
        name="Start Frame", default=0, min=0, description="First frame of the playback area")
    end_frame: bpy.props.IntProperty(
        name="End Frame", default=0, min=0, description="Last frame (inclusive) of the playback area")

    animation: bpy.props.PointerProperty(
        name="Animation", type=bpy.types.Object, poll=animations_filter)

    ui_show_expanded: bpy.props.BoolProperty(
        name="Show Expanded", default=True, description="Show details of the linked animation")


class ClipProperties(bpy.types.PropertyGroup):
    hash: bpy.props.StringProperty(name="Hash", default="")
    name: bpy.props.StringProperty(name="Name", default="")

    duration: bpy.props.FloatProperty(
        name="Duration", default=0, min=0, description="Duration of the clip in seconds")

    start_frame: bpy.props.IntProperty(name="Start Frame", default=0, min=0)
    end_frame: bpy.props.IntProperty(name="End Frame", default=0, min=0)

    animations: bpy.props.CollectionProperty(name="Animations", type=ClipAnimation)

    tags: bpy.props.CollectionProperty(name="Tags", type=ClipTag)


class AnimationProperties(bpy.types.PropertyGroup):
    def on_target_update(self, context):
        print(f"Target updated: {self.target_id} (prev {self.target_id_prev})")
        if self.target_id != self.target_id_prev:
            print("  Retargeting animation")
            retarget_animation(self.action, self.target_id_prev, self.target_id)

        self.target_id_prev = self.target_id

    hash: bpy.props.StringProperty(name="Hash", default="")
    frame_count: bpy.props.IntProperty(name="Frame Count", default=1, min=1)
    action: bpy.props.PointerProperty(name="Action", type=bpy.types.Action)

    target_id: bpy.props.PointerProperty(name="Target", type=bpy.types.ID, update=on_target_update)
    target_id_prev: bpy.props.PointerProperty(name="Target (Prev)", type=bpy.types.ID)
    target_id_type: bpy.props.EnumProperty(name="Target Type", items=[
        ("ARMATURE", "Armature", "Armature", "OUTLINER_DATA_ARMATURE", 0),
        ("CAMERA", "Camera", "Camera", "OUTLINER_DATA_CAMERA", 1),
        ("DRAWABLE_GEOMETRY", "Drawable Geometry", "Drawable Geometry", "OUTLINER_DATA_MESH", 2),
    ], default="ARMATURE")


class AnimationTracks(bpy.types.PropertyGroup):
    @staticmethod
    def Vec3Prop(name, subtype="TRANSLATION", default=(0.0, 0.0, 0.0)):
        return bpy.props.FloatVectorProperty(name=name, size=3, subtype=subtype, default=default)
    @staticmethod
    def QuatProp(name, default=(1.0, 0.0, 0.0, 0.0)):
        return bpy.props.FloatVectorProperty(name=name, size=4, subtype="QUATERNION", default=default)
    @staticmethod
    def FloatProp(name, default=0.0):
        return bpy.props.FloatProperty(name=name, default=default)

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
    camera_fov: FloatProp("Camera FOV")  # in degrees, 1.0-130.0
    camera_dof: Vec3Prop("Camera DOF", subtype="XYZ")  # x=near, y=far, z=unused
    unk_29: Vec3Prop("Unk 29", subtype="XYZ")
    unk_30: FloatProp("Unk 30")
    unk_31: FloatProp("Unk 31")
    unk_32: FloatProp("Unk 32")
    unk_33: FloatProp("Unk 33")
    unk_34: Vec3Prop("Unk 34", subtype="XYZ")
    camera_dof_strength: FloatProp("Camera DOF Strength")  # 0.0-1.0
    camera_unk_39: FloatProp("Camera Unk 39")  # boolean flag, true= >0.5, false= <=0.5
    unk_40: FloatProp("Unk 40")
    unk_41: FloatProp("Unk 41")
    unk_42: Vec3Prop("Unk 42", subtype="XYZ")
    # alternative to camera_dof track, all 4 must be set to be used
    camera_dof_plane_near_unk: FloatProp("Camera DOF Plane Near Unk")
    camera_dof_plane_near: FloatProp("Camera DOF Plane Near")
    camera_dof_plane_far_unk: FloatProp("Camera DOF Plane Far Unk")
    camera_dof_plane_far: FloatProp("Camera DOF Plane Far")
    unk_47: FloatProp("Unk 47")
    camera_unk_48: FloatProp("Camera Unk 48")  # boolean flag, true= >0.5, false= <=0.5
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


def unregister():
    del bpy.types.Object.clip_properties
    del bpy.types.Object.animation_properties

    del bpy.types.Object.animation_properties_v2

    unregister_tracks(bpy.types.PoseBone, inline=True)
    unregister_tracks(bpy.types.Object)
