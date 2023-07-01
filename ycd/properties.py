import bpy
import math
import mathutils
from ..sollumz_properties import SollumType
from ..tools.jenkhash import Generate
from ..tools.blenderhelper import build_name_bone_map, build_bone_map, get_data_obj


def animations_filter(self, object):
    if len(bpy.context.selected_objects) <= 0:
        return False

    active_object = bpy.context.selected_objects[0]

    if active_object.sollum_type != SollumType.CLIP:
        return False

    return object.sollum_type == SollumType.ANIMATION and active_object.parent.parent == object.parent.parent


def update_hashes(self, context):
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


class ClipDictionary(bpy.types.PropertyGroup):
    pass


class ClipAnimation(bpy.types.PropertyGroup):
    start_frame: bpy.props.IntProperty(
        name="Start Frame", default=0, min=0, description="First frame of the playback area")
    end_frame: bpy.props.IntProperty(
        name="End Frame", default=0, min=0, description="Last frame (inclusive) of the playback area")

    animation: bpy.props.PointerProperty(
        name="Animation", type=bpy.types.Object, poll=animations_filter)


class ClipProperties(bpy.types.PropertyGroup):
    hash: bpy.props.StringProperty(name="Hash", default="")
    name: bpy.props.StringProperty(name="Name", default="")

    duration: bpy.props.FloatProperty(
        name="Duration", default=0, min=0, description="Duration of the clip in seconds")

    start_frame: bpy.props.IntProperty(name="Start Frame", default=0, min=0)
    end_frame: bpy.props.IntProperty(name="End Frame", default=0, min=0)

    animations: bpy.props.CollectionProperty(
        name="Animations", type=ClipAnimation)


def calculate_bone_space_transform_matrix(old_pose_bone, new_pose_bone):
    if old_pose_bone is None:
        old_mat = mathutils.Matrix.Identity(4)
    else:
        old_bone = old_pose_bone.bone
        old_mat = old_bone.matrix_local
        if old_bone.parent is not None:
            old_mat = old_bone.parent.matrix_local.inverted() @ old_mat

    if new_pose_bone is None:
        new_mat = mathutils.Matrix.Identity(4)
    else:
        new_bone = new_pose_bone.bone
        new_mat = new_bone.matrix_local
        if new_bone.parent is not None:
            new_mat = new_bone.parent.matrix_local.inverted() @ new_mat

    return new_mat.inverted() @ old_mat


def transform_bone_location_space(fcurves, old_pose_bone, new_pose_bone):
    """
    Converts the vector3 F-curves from the old pose bone's space to the new pose bone's space.
    Either bone can be None, meaning convert from/to the original local space (as stored in the animation channels).
    """
    x = fcurves[0]
    y = fcurves[1]
    z = fcurves[2]

    if x is None:
        return

    assert len(x.keyframe_points) == len(y.keyframe_points) and len(x.keyframe_points) == len(z.keyframe_points), "TODO: Handle different number of keyframes for each axis"

    transform_mat = calculate_bone_space_transform_matrix(old_pose_bone, new_pose_bone)

    for x_kfp, y_kfp, z_kfp in zip(x.keyframe_points, y.keyframe_points, z.keyframe_points):
        x_co, y_co, z_co = x_kfp.co, y_kfp.co, z_kfp.co
        assert x_co[0] == y_co[0] and x_co[0] == z_co[0], "TODO: Handle different keyframe times"

        old_vec = mathutils.Vector((x_co[1], y_co[1], z_co[1]))
        new_vec = transform_mat @ old_vec
        x_co[1], y_co[1], z_co[1] = new_vec[0], new_vec[1], new_vec[2]

        x_kfp.co, y_kfp.co, z_kfp.co = x_co, y_co, z_co

    x.update()
    y.update()
    z.update()


def transform_bone_rotation_quaternion_space(fcurves, old_pose_bone, new_pose_bone):
    """
    Converts the quaternion F-curves from the old pose bone's space to the new pose bone's space.
    Either bone can be None, meaning convert from/to the original local space (as stored in the animation channels).
    """
    w = fcurves[0]
    x = fcurves[1]
    y = fcurves[2]
    z = fcurves[3]

    if w is None:
        return

    assert len(x.keyframe_points) == len(y.keyframe_points) and len(x.keyframe_points) == len(z.keyframe_points) and len(x.keyframe_points) == len(w.keyframe_points), "TODO: Handle different number of keyframes for each axis"

    transform_mat = calculate_bone_space_transform_matrix(old_pose_bone, new_pose_bone)

    for w_kfp, x_kfp, y_kfp, z_kfp in zip(w.keyframe_points, x.keyframe_points, y.keyframe_points, z.keyframe_points):
        w_co, x_co, y_co, z_co = w_kfp.co, x_kfp.co, y_kfp.co, z_kfp.co
        assert x_co[0] == y_co[0] and x_co[0] == z_co[0] and x_co[0] == w_co[0], "TODO: Handle different keyframe times"

        quat = mathutils.Quaternion((w_co[1], x_co[1], y_co[1], z_co[1]))
        quat.rotate(transform_mat)

        w_co[1], x_co[1], y_co[1], z_co[1] = quat[0], quat[1], quat[2], quat[3]

        w_kfp.co, x_kfp.co, y_kfp.co, z_kfp.co = w_co, x_co, y_co, z_co

    w.update()
    x.update()
    y.update()
    z.update()


def transform_camera_rotation_quaternion(fcurves, old_camera, new_camera):
    """
    Blender cameras aim down the -Z axis, but RAGE cameras aim down the +Y axis.
    Rotate the quaternion F-curves by 90 degrees around the X axis to compensate.
    """
    w = fcurves[0]
    x = fcurves[1]
    y = fcurves[2]
    z = fcurves[3]

    if w is None:
        return

    # changing between blender cameras or non-camera targets, doesn't need to be converted
    if (old_camera is not None and new_camera is not None) or (old_camera is None and new_camera is None):
        return

    assert len(x.keyframe_points) == len(y.keyframe_points) and len(x.keyframe_points) == len(z.keyframe_points) and len(x.keyframe_points) == len(w.keyframe_points), "TODO: Handle different number of keyframes for each axis"

    # if camera is None, we convert from Blender to RAGE; otherwise from RAGE to Blender
    angle_delta = math.radians(-90.0 if new_camera is None else 90.0)
    x_axis = mathutils.Vector((1.0, 0.0, 0.0))

    for w_kfp, x_kfp, y_kfp, z_kfp in zip(w.keyframe_points, x.keyframe_points, y.keyframe_points, z.keyframe_points):
        w_co, x_co, y_co, z_co = w_kfp.co, x_kfp.co, y_kfp.co, z_kfp.co
        assert x_co[0] == y_co[0] and x_co[0] == z_co[0] and x_co[0] == w_co[0], "TODO: Handle different keyframe times"

        quat = mathutils.Quaternion((w_co[1], x_co[1], y_co[1], z_co[1]))
        x_axis_local = quat @ x_axis
        quat.rotate(mathutils.Quaternion(x_axis_local, angle_delta))

        w_co[1], x_co[1], y_co[1], z_co[1] = quat[0], quat[1], quat[2], quat[3]

        w_kfp.co, x_kfp.co, y_kfp.co, z_kfp.co = w_co, x_co, y_co, z_co

    w.update()
    x.update()
    y.update()
    z.update()


def add_driver_variable_obj_prop(fcurve, name, obj, prop_data_path):
    var = fcurve.driver.variables.new()
    var.name = name
    var.type = "SINGLE_PROP"
    var_target = var.targets[0]
    var_target.id_type = "OBJECT"
    var_target.id = obj
    var_target.data_path = prop_data_path
    return var


def setup_camera_for_animation(camera):
    camera_obj = get_data_obj(camera)
    camera_obj.rotation_mode = 'QUATERNION'  # camera rotation track uses rotation_quaternion

    # connect camera_fov track to blender camera
    # NOTE: seems to report a dependency cycle, but works fine, blender bug?
    camera.driver_remove("lens")
    fcurve_lens = camera.driver_add("lens")
    add_driver_variable_obj_prop(fcurve_lens, "fov", camera_obj, "animation_tracks.camera_fov")
    add_driver_variable_obj_prop(fcurve_lens, "sensor", camera_obj, "data.sensor_width")
    fcurve_lens.driver.expression = "(sensor * 0.5) / tan(radians(fov) * 0.5)"
    fcurve_lens.update()


def add_global_anim_uv_drivers(drawable_geometry_obj, x_dot_node, y_dot_node):
    def _add_driver(dot_node, track):
        vec_input = dot_node.inputs[1]
        vec_input.driver_remove("default_value")
        fcurves = vec_input.driver_add("default_value")
        components = ["x", "y", "z"]
        for i in range(3):
            fcurve = fcurves[i]
            comp = components[i]
            add_driver_variable_obj_prop(fcurve, comp, drawable_geometry_obj, f"animation_tracks.{track}.{comp}")
            fcurve.driver.expression = comp
            fcurve.update()

    _add_driver(x_dot_node, "uv0")
    _add_driver(y_dot_node, "uv1")


def add_global_anim_uv_nodes(drawable_geometry_obj, material):
    tree = material.node_tree
    nodes = tree.nodes
    base_tex_node = None
    for node in nodes:
        if node.type == "BSDF_PRINCIPLED":
            base_tex_node = node.inputs[0].links[0].from_node
            break

    if base_tex_node is None:
        raise Exception("Could not find base texture node")

    # operation to perform:
    #   vec uv = ...
    #   vec uvw = vec(uv, 1);
    #   uv.x = dot(uvw, globalAnimUV0.xyz);
    #   uv.y = dot(uvw, globalAnimUV1.xyz);
    uv = nodes.new("ShaderNodeUVMap")
    separate_uv = nodes.new("ShaderNodeSeparateXYZ")
    combine_augmented_uv = nodes.new("ShaderNodeCombineXYZ")
    combine_augmented_uv.inputs["Z"].default_value = 1.0
    x_dot = nodes.new("ShaderNodeVectorMath")
    x_dot.operation = "DOT_PRODUCT"
    y_dot = nodes.new("ShaderNodeVectorMath")
    y_dot.operation = "DOT_PRODUCT"
    combine_new_uv = nodes.new("ShaderNodeCombineXYZ")
    combine_new_uv.inputs["Z"].default_value = 0.0

    tree.links.new(separate_uv.inputs["Vector"], uv.outputs["UV"])
    tree.links.new(combine_augmented_uv.inputs["X"], separate_uv.outputs["X"])
    tree.links.new(combine_augmented_uv.inputs["Y"], separate_uv.outputs["Y"])

    tree.links.new(x_dot.inputs[0], combine_augmented_uv.outputs[0])
    tree.links.new(y_dot.inputs[0], combine_augmented_uv.outputs[0])

    tree.links.new(combine_new_uv.inputs["X"], x_dot.outputs["Value"])
    tree.links.new(combine_new_uv.inputs["Y"], y_dot.outputs["Value"])

    tree.links.new(base_tex_node.inputs["Vector"], combine_new_uv.outputs[0])

    add_global_anim_uv_drivers(drawable_geometry_obj, x_dot, y_dot)


def setup_drawable_geometry_for_animation(drawable_geometry):
    drawable_geometry_obj = get_data_obj(drawable_geometry)

    material = drawable_geometry.materials[0]
    if material.sollum_type == "sollumz_material_none":
        raise Exception("Material is not a Sollumz material")

    add_global_anim_uv_nodes(drawable_geometry_obj, material)


def retarget_animation(action, old_target_id, new_target_id):
    if isinstance(old_target_id, bpy.types.Armature):
        old_bone_map = build_bone_map(get_data_obj(old_target_id))
        old_bone_name_map = build_name_bone_map(get_data_obj(old_target_id))
    else:
        old_bone_map = None
        old_bone_name_map = None

    if isinstance(new_target_id, bpy.types.Armature):
        new_bone_map = build_bone_map(get_data_obj(new_target_id))
    else:
        new_bone_map = None

    new_is_camera = new_target_id is not None and isinstance(new_target_id, bpy.types.Camera)
    new_is_drawable_geometry = new_target_id is not None and isinstance(new_target_id, bpy.types.Mesh)
    disable_camera_tracks = new_target_id is not None and not isinstance(new_target_id, bpy.types.Camera)

    # bone_id -> [fcurves]
    bone_locations_to_transform = {}
    bone_rotations_to_transform = {}

    camera_rotation_to_transform = None

    for fcurve in action.fcurves:
        # TODO: can we somehow store the track ID in the F-Curve to avoid parsing the data paths?
        data_path = fcurve.data_path

        # revert camera/uv tracks data paths to bone IDs
        if not new_is_camera and data_path.startswith("animation_tracks.camera_"):
            data_path = data_path.replace("animation_tracks.", 'pose.bones["#0"].animation_tracks_')
        elif not new_is_drawable_geometry and data_path.startswith("animation_tracks.uv"):
            data_path = data_path.replace("animation_tracks.", 'pose.bones["#0"].animation_tracks_')

        # insert bone names in data paths or revert to bone IDs, and transform bone locations/rotations
        if data_path.startswith('pose.bones["'):  # bone properties
            data_path_parts = data_path.split('"')
            old_bone_name = data_path_parts[1]
            if old_bone_name.startswith("#"):
                bone_id = int(old_bone_name[1:])
            else:
                assert old_bone_name_map is not None, "There should always be an old armature at this point"
                bone_id = old_bone_name_map[old_bone_name]

            if new_bone_map is not None and bone_id in new_bone_map:
                new_bone_name = new_bone_map[bone_id].name
                data_path_parts[1] = new_bone_name
            else:
                data_path_parts[1] = f"#{bone_id}"

            data_path = '"'.join(data_path_parts)

            if data_path_parts[2] == "].location":
                if bone_id not in bone_locations_to_transform:
                    bone_locations_to_transform[bone_id] = [None, None, None]
                bone_locations_to_transform[bone_id][fcurve.array_index] = fcurve
            elif data_path_parts[2] == "].rotation_quaternion":  # TODO: Handle rotation_euler
                if bone_id not in bone_rotations_to_transform:
                    bone_rotations_to_transform[bone_id] = [None, None, None, None]
                bone_rotations_to_transform[bone_id][fcurve.array_index] = fcurve

        # camera tracks
        if data_path == "location":  # camera location
            # Some non-camera animations still have camera tracks with non-0 IDs (left-over from their source
            # animation/editor?) and the f-curves modify the object location/rotation instead of some custom
            # bone property, affecting how the animation plays. So, if the target is not a camera, disable
            # the track evaluation.
            fcurve.mute = disable_camera_tracks
        elif data_path == "rotation_quaternion":  # camera rotation
            fcurve.mute = disable_camera_tracks
            # ID is not stored in the data path, but actual camera animations should only have a single track on ID 0
            if not disable_camera_tracks:
                if camera_rotation_to_transform is None:
                    camera_rotation_to_transform = [None, None, None, None]
                camera_rotation_to_transform[fcurve.array_index] = fcurve
        elif new_is_camera and data_path.startswith('pose.bones["#0"].animation_tracks_camera_'):  # camera properties
            # change data path to modify the actual camera object instead of an armature
            data_path = data_path.replace('pose.bones["#0"].animation_tracks_', "animation_tracks.")
        elif new_is_drawable_geometry and data_path.startswith('pose.bones["#0"].animation_tracks_uv'):  # uv properties
            # change data path to modify the actual drawable geometry object instead of an armature
            data_path = data_path.replace('pose.bones["#0"].animation_tracks_', "animation_tracks.")

        # print(f"<{fcurve.data_path}> -> <{data_path}>")
        fcurve.data_path = data_path

    # perform required transformations
    for bone_id, fcurves in bone_locations_to_transform.items():
        old_bone = old_bone_map.get(bone_id, None) if old_bone_map is not None else None
        new_bone = new_bone_map.get(bone_id, None) if new_bone_map is not None else None
        transform_bone_location_space(fcurves, old_bone, new_bone)

    for bone_id, fcurves in bone_rotations_to_transform.items():
        old_bone = old_bone_map.get(bone_id, None) if old_bone_map is not None else None
        new_bone = new_bone_map.get(bone_id, None) if new_bone_map is not None else None
        transform_bone_rotation_quaternion_space(fcurves, old_bone, new_bone)

    if camera_rotation_to_transform is not None:
        old_camera = old_target_id if isinstance(old_target_id, bpy.types.Camera) else None
        new_camera = new_target_id if isinstance(new_target_id, bpy.types.Camera) else None
        transform_camera_rotation_quaternion(camera_rotation_to_transform, old_camera, new_camera)

    if new_is_camera:
        setup_camera_for_animation(new_target_id)

    if new_is_drawable_geometry:
        setup_drawable_geometry_for_animation(new_target_id)


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


AnimationTrackToPropertyName = {
    17: "uv0",
    18: "uv1",
    22: "unk_22",
    24: "unk_24",
    25: "unk_25",
    26: "unk_26",
    27: "camera_fov",
    28: "camera_dof",
    29: "unk_29",
    30: "unk_30",
    31: "unk_31",
    32: "unk_32",
    33: "unk_33",
    34: "unk_34",
    36: "camera_dof_strength",
    39: "camera_unk_39",
    40: "unk_40",
    41: "unk_41",
    42: "unk_42",
    43: "camera_dof_plane_near_unk",
    44: "camera_dof_plane_near",
    45: "camera_dof_plane_far_unk",
    46: "camera_dof_plane_far",
    47: "unk_47",
    48: "camera_unk_48",
    49: "camera_dof_unk_49",
    50: "unk_50",
    51: "camera_dof_unk_51",
    52: "unk_52",
    53: "unk_53",
    134: "unk_134",
    136: "unk_136",
    137: "unk_137",
    138: "unk_138",
    139: "unk_139",
    140: "unk_140",
}


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
    bpy.types.Object.clip_dict_properties = bpy.props.PointerProperty(
        type=ClipDictionary)
    bpy.types.Object.clip_properties = bpy.props.PointerProperty(
        type=ClipProperties)
    bpy.types.Object.animation_properties = bpy.props.PointerProperty(
        type=AnimationProperties)

    register_tracks(bpy.types.PoseBone, inline=True)
    register_tracks(bpy.types.Object)

    # def location_local_get(p_bone):
    #     mat = p_bone.bone.matrix_local
    #     if p_bone.bone.parent is not None:
    #         mat = p_bone.bone.parent.matrix_local.inverted() @ mat
    #     return mat @ p_bone.location
    #
    # def location_local_set(p_bone, value):
    #     mat = p_bone.bone.matrix_local
    #     if p_bone.bone.parent is not None:
    #         mat = p_bone.bone.parent.matrix_local.inverted() @ mat
    #
    #     mat_decomposed = mat.decompose()
    #
    #     bone_location = mat_decomposed[0]
    #     bone_rotation = mat_decomposed[1]
    #
    #     diff_location = mathutils.Vector((
    #         (value.x - bone_location.x),
    #         (value.y - bone_location.y),
    #         (value.z - bone_location.z),
    #     ))
    #
    #     diff_location.rotate(bone_rotation.inverted())
    #
    #     p_bone.location = diff_location
    #
    # bpy.types.PoseBone.location_local = bpy.props.FloatVectorProperty(
    #     "Local Location", size=3, subtype="TRANSLATION", get=location_local_get, set=location_local_set)


def unregister():
    del bpy.types.Object.clip_dict_properties
    del bpy.types.Object.clip_properties
    del bpy.types.Object.animation_properties

    del bpy.types.Object.animation_properties_v2

    unregister_tracks(bpy.types.PoseBone, inline=True)
    unregister_tracks(bpy.types.Object)
