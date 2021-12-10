import os
import bpy
from mathutils import Matrix
from .shader_materials import create_shader, create_tinted_shader_graph, get_detail_extra_sampler
from ..ybn.ybnimport import composite_to_obj, bound_to_obj
from ..sollumz_properties import SOLLUMZ_UI_NAMES, LODLevel, TextureFormat, TextureUsage, SollumType, LightType
from ..resources.drawable import *
from ..tools.meshhelper import flip_uv
from ..tools.utils import *
from ..tools.blenderhelper import *
from ..tools.drawablehelper import join_drawable_geometries
from ..resources.shader import ShaderManager


def shadergroup_to_materials(shadergroup, filepath):
    materials = []

    texture_folder = os.path.dirname(
        filepath) + "\\" + os.path.basename(filepath)[:-8]
    for shader in shadergroup.shaders:

        material = create_shader(shader.name, shader.filename)

        material.shader_properties.renderbucket = shader.render_bucket
        material.shader_properties.filename = shader.filename

        for param in shader.parameters:
            for n in material.node_tree.nodes:
                if isinstance(n, bpy.types.ShaderNodeTexImage):
                    if param.name == n.name:
                        texture_path = os.path.join(
                            texture_folder, param.texture_name + ".dds")
                        addon_key = __name__.split('.')[0]
                        shared_folder = bpy.context.preferences.addons[
                            addon_key].preferences.shared_texture_folder
                        shared_folder_dirs = [x[0]
                                              for x in os.walk(shared_folder)]
                        if(os.path.isfile(texture_path)):
                            img = bpy.data.images.load(
                                texture_path, check_existing=True)
                            n.image = img
                        # check shared texture folder
                        else:
                            for d in shared_folder_dirs:
                                t_path = os.path.join(
                                    d, param.texture_name + ".dds")
                                if(os.path.isfile(t_path)):
                                    img = bpy.data.images.load(
                                        t_path, check_existing=True)
                                    n.image = img
                        if not n.image:
                            # Check for existing texture
                            existing_texture = None
                            for image in bpy.data.images:
                                if image.name == param.texture_name:
                                    existing_texture = image
                            texture = bpy.data.images.new(
                                name=param.texture_name, width=512, height=512) if not existing_texture else existing_texture
                            n.image = texture
                            # n.image = bpy.data.images.new(
                            #     name=param.texture_name, width=512, height=512)

                        # assign non color to normal maps
                        if "Bump" in param.name:
                            n.image.colorspace_settings.name = "Non-Color"

                        # Assign embedded texture dictionary properties
                        if shadergroup.texture_dictionary != None:
                            for texture in shadergroup.texture_dictionary:
                                if texture.name == param.texture_name:
                                    n.texture_properties.embedded = True
                                    try:
                                        format = TextureFormat[texture.format.replace(
                                            'D3DFMT_', '')]
                                        n.texture_properties.format = format
                                    except AttributeError:
                                        print(
                                            f"Failed to set texture format: format '{texture.format}' unknown.")

                                    try:
                                        usage = TextureUsage[texture.usage]
                                        n.texture_properties.usage = usage
                                    except AttributeError:
                                        print(
                                            f"Failed to set texture usage: usage '{texture.usage}' unknown.")

                                    n.texture_properties.extra_flags = texture.extra_flags

                                    for prop in dir(n.texture_flags):
                                        for uf in texture.usage_flags:
                                            if(uf.lower() == prop):
                                                setattr(
                                                    n.texture_flags, prop, True)

                        if param.name == "BumpSampler" and hasattr(n.image, 'colorspace_settings'):
                            n.image.colorspace_settings.name = 'Non-Color'

                elif isinstance(n, bpy.types.ShaderNodeValue):
                    if param.name == n.name[:-2]:
                        key = n.name[-1]
                        if key == "x":
                            n.outputs[0].default_value = param.x
                        if key == "y":
                            n.outputs[0].default_value = param.y
                        if key == "z":
                            n.outputs[0].default_value = param.z
                        if key == "w":
                            n.outputs[0].default_value = param.w

        # assign extra detail node image for viewing
        dtl_ext = get_detail_extra_sampler(material)
        if dtl_ext:
            dtl = material.node_tree.nodes["DetailSampler"]
            dtl_ext.image = dtl.image

        materials.append(material)

    return materials


def create_uv_layer(mesh, num, name, texcoords):
    mesh.uv_layers.new()
    uv_layer = mesh.uv_layers[num]
    uv_layer.name = name
    for i in range(len(uv_layer.data)):
        uv = flip_uv(texcoords[mesh.loops[i].vertex_index])
        uv_layer.data[i].uv = uv


def create_vertexcolor_layer(mesh, num, name, colors):
    mesh.vertex_colors.new(name="Vertex Colors " + str(num))
    color_layer = mesh.vertex_colors[num]
    color_layer.name = name
    for i in range(len(color_layer.data)):
        rgba = colors[mesh.loops[i].vertex_index]
        color_layer.data[i].color = divide_list(rgba, 255)


def geometry_to_obj(geometry, bones=None, name=None):

    vertices = []
    faces = []
    normals = []
    texcoords = {}
    colors = {}

    has_normals = False

    # gather data
    data = geometry.vertex_buffer.get_data()
    for vertex in data:
        vertices.append(vertex.position)
        if hasattr(vertex, "normal"):
            has_normals = True
            normals.append(vertex.normal)

        for key, value in vertex._asdict().items():
            if 'texcoord' in key:
                if not key in texcoords.keys():
                    texcoords[key] = []
                texcoords[key].append(value)
            if 'colour' in key:
                if not key in colors.keys():
                    colors[key] = []
                colors[key].append(value)

    indices = geometry.index_buffer.data
    # Split indices into groups of 3
    faces = [indices[i * 3:(i + 1) * 3]
             for i in range((len(indices) + 3 - 1) // 3)]

    # create mesh
    mesh = bpy.data.meshes.new(SOLLUMZ_UI_NAMES[SollumType.DRAWABLE_GEOMETRY])
    mesh.from_pydata(vertices, [], faces)

    # set normals
    if has_normals:
        mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
        mesh.normals_split_custom_set_from_vertices(normals)
        mesh.use_auto_smooth = True

    # set uvs
    i = 0
    for layer_name, coords in texcoords.items():
        create_uv_layer(mesh, i, layer_name, coords)
        i += 1

    # set vertex colors
    i = 0
    for layer_name, color in colors.items():
        create_vertexcolor_layer(mesh, i, layer_name, color)
        i += 1

    obj = bpy.data.objects.new(name + "_mesh", mesh)

    # set weights
    if hasattr(data[0], "blendweights"):
        if (bones != None and len(bones) > 0 and data[0].blendweights is not None and len(data) > 0):
            num = max(256, len(bones))
            for i in range(num):
                if (i < len(bones)):
                    obj.vertex_groups.new(name=bones[i].name)
                else:
                    obj.vertex_groups.new(name="UNKNOWN_BONE." + str(i))

            for vertex_idx, vertex in enumerate(data):
                for i in range(0, 4):
                    weight = vertex.blendweights[i] / 255
                    index = vertex.blendindices[i]
                    if (weight > 0.0):
                        obj.vertex_groups[index].add(
                            [vertex_idx], weight, "ADD")

            remove_unused_vertex_groups_of_mesh(obj)

    return obj


def drawable_model_to_obj(model, materials, name, lod, bones=None):
    dobj = bpy.data.objects.new(
        SOLLUMZ_UI_NAMES[SollumType.DRAWABLE_MODEL], None)
    dobj.sollum_type = SollumType.DRAWABLE_MODEL
    dobj.empty_display_size = 0
    dobj.drawable_model_properties.sollum_lod = lod
    dobj.drawable_model_properties.render_mask = model.render_mask
    dobj.drawable_model_properties.flags = model.flags

    for child in model.geometries:
        child_obj = geometry_to_obj(child, bones=bones, name=name)
        child_obj.sollum_type = SollumType.DRAWABLE_GEOMETRY
        child_obj.data.materials.append(materials[child.shader_index])
        child_obj.parent = dobj
        bpy.context.collection.objects.link(child_obj)
        # do this after because object has to be linked, will do nothing if a tint parameter is not found... kinda stupid way to do it but its how
        # we check if its a tint shader in the first place so ig it makes sense...
        create_tinted_shader_graph(child_obj)

    bpy.context.collection.objects.link(dobj)

    return dobj


def bone_to_obj(bone, armature):

    if armature is None:
        return None

    # bpy.context.view_layer.objects.active = armature
    edit_bone = armature.data.edit_bones.new(bone.name)
    if bone.parent_index != -1:
        edit_bone.parent = armature.data.edit_bones[bone.parent_index]

    # https://github.com/LendoK/Blender_GTA_V_model_importer/blob/master/importer.py
    mat_rot = bone.rotation.to_matrix().to_4x4()
    mat_loc = Matrix.Translation(bone.translation)
    mat_sca = Matrix.Scale(1, 4, bone.scale)

    edit_bone.head = (0, 0, 0)
    edit_bone.tail = (0, 0.05, 0)
    edit_bone.matrix = mat_loc @ mat_rot @ mat_sca
    if edit_bone.parent != None:
        edit_bone.matrix = edit_bone.parent.matrix @ edit_bone.matrix

    return bone.name


def set_bone_properties(bone, armature):

    bl_bone = armature.pose.bones[bone.name].bone
    bl_bone.bone_properties.tag = bone.tag
    # LimitRotation and Unk0 have their special meanings, can be deduced if needed when exporting
    flags_restricted = set(["LimitRotation", "Unk0"])
    for _flag in bone.flags:
        if (_flag in flags_restricted):
            continue

        flag = bl_bone.bone_properties.flags.add()
        flag.name = _flag


def skeleton_to_obj(skeleton, armature):

    if skeleton is None:
        return None

    bpy.context.view_layer.objects.active = armature
    bones = skeleton.bones
    bpy.ops.object.mode_set(mode='EDIT')

    for bone in bones:
        bone_to_obj(bone, armature)

    bpy.ops.object.mode_set(mode='OBJECT')

    for bone in bones:
        set_bone_properties(bone, armature)

    return armature


def set_rotation_limit(joint, bone):

    if bone is None:
        return None

    constraint = bone.constraints.new('LIMIT_ROTATION')
    constraint.owner_space = 'LOCAL'
    constraint.use_limit_x = True
    constraint.use_limit_y = True
    constraint.use_limit_z = True
    constraint.max_x = joint.max.x
    constraint.max_y = joint.max.y
    constraint.max_z = joint.max.z
    constraint.min_x = joint.min.x
    constraint.min_y = joint.min.y
    constraint.min_z = joint.min.z

    # joints don't have an unique name so return the bone name instead
    return bone.name


def rotation_limits_to_obj(rotation_limits, armature):

    # there should be more joint types than RotationLimits
    tag_bone_map = build_tag_bone_map(armature)
    if tag_bone_map is None:
        return None

    bones_with_constraint = []
    for joint in rotation_limits:
        bone = armature.pose.bones.get(tag_bone_map[joint.bone_id])
        bone_name = set_rotation_limit(joint, bone)
        bones_with_constraint.append(bone_name)

    return bones_with_constraint


def light_to_obj(light, idx):
    # WORK AROUND FOR INVALID LIGHT TYPES
    try:
        light_data = bpy.data.lights.new(
            name=f"light{idx}", type=light.type.upper())
    except:
        light_data = bpy.data.lights.new(
            name=f"light{idx}", type="SPOT")

    light_data.color = light.color
    light_data.energy = light.intensity
    # divide by 100 because blender specular is clamped 0 - 1 ????
    light_data.specular_factor = light.flashiness / 100
    #light_data.spot_size = light.cone_outer_angle
    #light_data.spot_blend = light.cone_inner_angle

    lobj = bpy.data.objects.new(name=f"light{idx}", object_data=light_data)
    bpy.context.collection.objects.link(lobj)
    lobj.sollum_type = SollumType.LIGHT
    lobj.location = light.position
    lobj.rotation_euler = light.direction

    if light.type == 'Point':
        lobj.data.light_properties.type = LightType.POINT
    elif light.type == 'Spot':
        lobj.data.light_properties.type = LightType.SPOT
    elif light.type == 'Capsule':
        lobj.data.light_properties.type = LightType.CAPSULE

    lobj.name = SOLLUMZ_UI_NAMES[lobj.data.light_properties.type]
    lobj.data.light_properties.flags = light.flags
    lobj.data.light_properties.bone_id = light.bone_id
    lobj.data.light_properties.group_id = light.group_id
    lobj.data.light_properties.time_flags = light.time_flags
    lobj.data.light_properties.falloff = light.falloff
    lobj.data.light_properties.falloff_exponent = light.falloff_exponent
    lobj.data.light_properties.culling_plane_normal = light.culling_plane_normal
    lobj.data.light_properties.culling_plane_offset = light.culling_plane_offset
    lobj.data.light_properties.unknown_45 = light.unknown_45
    lobj.data.light_properties.unknown_46 = light.unknown_46
    lobj.data.light_properties.volume_intensity = light.volume_intensity
    lobj.data.light_properties.volume_size_scale = light.volume_size_scale
    lobj.data.light_properties.volume_outer_color = light.volume_outer_color
    lobj.data.light_properties.light_hash = light.light_hash
    lobj.data.light_properties.volume_outer_intensity = light.volume_outer_intensity
    lobj.data.light_properties.corona_size = light.corona_size
    lobj.data.light_properties.volume_outer_exponent = light.volume_outer_exponent
    lobj.data.light_properties.light_fade_distance = light.light_fade_distance
    lobj.data.light_properties.shadow_fade_distance = light.shadow_fade_distance
    lobj.data.light_properties.specular_fade_distance = light.specular_fade_distance
    lobj.data.light_properties.volumetric_fade_distance = light.volumetric_fade_distance
    lobj.data.light_properties.shadow_near_clip = light.shadow_near_clip
    lobj.data.light_properties.corona_intensity = light.corona_intensity
    lobj.data.light_properties.corona_z_bias = light.corona_z_bias
    lobj.data.light_properties.tangent = light.tangent
    lobj.data.light_properties.cone_inner_angle = light.cone_inner_angle
    lobj.data.light_properties.cone_outer_angle = light.cone_outer_angle
    lobj.data.light_properties.extent = light.extent
    lobj.data.light_properties.projected_texture_hash = light.projected_texture_hash

    return lobj


def drawable_to_obj(drawable, filepath, name, bones_override=None, materials=None):

    if not materials:
        materials = shadergroup_to_materials(drawable.shader_group, filepath)

    obj = None
    bones = None

    if len(drawable.skeleton.bones) > 0:
        skel = bpy.data.armatures.new(name + ".skel")
        obj = bpy.data.objects.new(name, skel)
    else:
        obj = bpy.data.objects.new(name, None)

    obj.sollum_type = SollumType.DRAWABLE
    obj.empty_display_size = 0
    obj.drawable_properties.lod_dist_high = drawable.lod_dist_high
    obj.drawable_properties.lod_dist_med = drawable.lod_dist_med
    obj.drawable_properties.lod_dist_low = drawable.lod_dist_low
    obj.drawable_properties.lod_dist_vlow = drawable.lod_dist_vlow

    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj

    bones = None
    if len(drawable.skeleton.bones) > 0:
        bones = drawable.skeleton.bones
        skeleton_to_obj(drawable.skeleton, obj)

    if len(drawable.joints.rotation_limits) > 0:
        bones_with_rotation_limits = rotation_limits_to_obj(
            drawable.joints.rotation_limits, obj)

    if bones_override is not None:
        bones = bones_override

    if drawable.bound and drawable.bound.type == SollumType.BOUND_COMPOSITE:
        bobj = composite_to_obj(
            drawable.bound, SOLLUMZ_UI_NAMES[SollumType.BOUND_COMPOSITE], True)
        bobj.parent = obj
    elif drawable.bound:
        bobj = bound_to_obj(drawable.bound)
        if bobj:
            bobj.parent = obj

    for model in drawable.drawable_models_high:
        dobj = drawable_model_to_obj(
            model, materials, drawable.name, LODLevel.HIGH, bones=bones)
        dobj.parent = obj

    for model in drawable.drawable_models_med:
        dobj = drawable_model_to_obj(
            model, materials, drawable.name, LODLevel.MEDIUM, bones=bones)
        dobj.parent = obj

    for model in drawable.drawable_models_low:
        dobj = drawable_model_to_obj(
            model, materials, drawable.name, LODLevel.LOW, bones=bones)
        dobj.parent = obj

    for model in drawable.drawable_models_vlow:
        dobj = drawable_model_to_obj(
            model, materials, drawable.name, LODLevel.VERYLOW, bones=bones)
        dobj.parent = obj

    for model in obj.children:
        if model.sollum_type != SollumType.DRAWABLE_MODEL:
            continue

        for child in model.children:
            if child.sollum_type != SollumType.DRAWABLE_GEOMETRY:
                continue

            mod = child.modifiers.new("Armature", 'ARMATURE')
            mod.object = obj

    for idx, light in enumerate(drawable.lights):
        lobj = light_to_obj(light, idx)
        lobj.parent = obj

    return obj


def import_ydr(filepath, join_geometries):
    ydr_xml = YDR.from_xml_file(filepath)
    drawable = drawable_to_obj(ydr_xml, filepath, os.path.basename(
        filepath.replace(YDR.file_extension, '')))
    if join_geometries:
        join_drawable_geometries(drawable)
