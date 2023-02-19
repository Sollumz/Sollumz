import bpy
from ..sollumz_ui import SOLLUMZ_PT_OBJECT_PANEL
from ..ydr.ui import SOLLUMZ_PT_BONE_PANEL
from ..sollumz_properties import SollumType, BOUND_TYPES, SOLLUMZ_UI_NAMES
from ..sollumz_helper import find_fragment_parent
from ..ydr.properties import DrawableProperties
from .properties import GroupProperties, FragmentProperties, VehicleWindowProperties


class SOLLUMZ_PT_FRAGMENT_TOOL_PANEL(bpy.types.Panel):
    bl_label = "Fragment Tools"
    bl_idname = "SOLLUMZ_PT_FRAGMENT_TOOL_PANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_category = "Sollumz Tools"
    bl_order = 6

    def draw_header(self, context):
        self.layout.label(text="", icon="PACKAGE")

    def draw(self, context):
        pass


class SOLLUMZ_PT_FRAGMENT_PANEL(bpy.types.Panel):
    bl_label = "Fragment"
    bl_idname = "SOLLUMZ_PT_FRAGMENT_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_options = {"HIDE_HEADER"}
    bl_parent_id = SOLLUMZ_PT_OBJECT_PANEL.bl_idname

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.sollum_type == SollumType.FRAGMENT

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        obj = context.active_object

        for prop in FragmentProperties.__annotations__:
            if prop == "lod_properties":
                continue

            self.layout.prop(obj.fragment_properties, prop)


class SOLLUMZ_PT_FRAGMENT_DRAWABLE_PANEL(bpy.types.Panel):
    bl_label = "Drawable Properties"
    bl_idname = "SOLLUMZ_PT_FRAGMENT_DRAWABLE_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_FRAGMENT_PANEL.bl_idname

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        obj = context.active_object

        for prop in DrawableProperties.__annotations__:
            if prop == "lod_properties":
                continue

            self.layout.prop(obj.drawable_properties, prop)


class SOLLUMZ_PT_FRAG_DRAWABLE_MODEL_PANEL(bpy.types.Panel):
    bl_label = "LOD Properties"
    bl_idname = "SOLLUMZ_PT_FRAG_DRAWABLE_MODEL_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_OBJECT_PANEL.bl_idname

    @classmethod
    def poll(cls, context):
        obj = context.active_object

        if obj is None:
            return False

        active_lod = obj.sollumz_lods.active_lod

        return active_lod is not None and obj.sollum_type == SollumType.FRAG_GEOM and obj.type == "MESH"

    def draw(self, context):
        layout = self.layout
        layout.use_property_decorate = False
        layout.use_property_split = True

        obj = context.active_object
        active_lod_level = obj.sollumz_lods.active_lod.type
        mesh = obj.data
        frag_parent = find_fragment_parent(obj)

        model_props = mesh.drawable_model_properties

        col = layout.column()
        col.alignment = "RIGHT"
        col.enabled = False

        is_skinned_model = obj.vertex_groups and frag_parent is not None and not obj.sollumz_is_physics_child_mesh

        # All skinned objects (objects with vertex groups) go in the same drawable model
        if is_skinned_model:
            model_props = frag_parent.skinned_model_properties.get_lod(
                active_lod_level)

            # col.label(text="*Skinned Model")
            col.label(
                text=f"Active LOD: {SOLLUMZ_UI_NAMES[active_lod_level]} (Skinned)")
        else:
            col.label(
                text=f"Active LOD: {SOLLUMZ_UI_NAMES[active_lod_level]}")

        col.separator()

        layout.prop(model_props, "render_mask")
        layout.prop(model_props, "unknown_1")
        layout.prop(model_props, "flags")


class SOLLUMZ_PT_VEH_WINDOW_PANEL(bpy.types.Panel):
    bl_label = "Vehicle Window"
    bl_idname = "SOLLUMZ_PT_VEHICLE_WINDOW_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_options = {"HIDE_HEADER"}
    bl_parent_id = SOLLUMZ_PT_OBJECT_PANEL.bl_idname

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.sollum_type == SollumType.FRAGVEHICLEWINDOW

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        obj = context.active_object

        for prop in VehicleWindowProperties.__annotations__:
            self.layout.prop(obj.vehicle_window_properties, prop)


class SOLLUMZ_PT_PHYS_LODS_PANEL(bpy.types.Panel):
    bl_label = "Physics LOD Properties"
    bl_idname = "SOLLUMZ_PT_PHYS_LODS_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_FRAGMENT_PANEL.bl_idname

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        obj = context.view_layer.objects.active
        lod_props = obj.fragment_properties.lod_properties

        for prop in lod_props.__annotations__:
            if prop == "archetype_properties":
                continue
            layout.prop(lod_props, prop)


class SOLLUMZ_PT_FRAG_ARCHETYPE_PANEL(bpy.types.Panel):
    bl_label = "Archetype Properties"
    bl_idname = "SOLLUMZ_PT_FRAG_ARCHETYPE_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_FRAGMENT_PANEL.bl_idname

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        obj = context.view_layer.objects.active
        arch_props = obj.fragment_properties.lod_properties.archetype_properties

        for prop in arch_props.__annotations__:
            layout.prop(arch_props, prop)


class SOLLUMZ_PT_BONE_PHYSICS_PANEL(bpy.types.Panel):
    bl_label = "Physics"
    bl_idname = "SOLLUMZ_PT_BONE_PHYSICS_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "bone"
    bl_options = {"HIDE_HEADER", "DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_BONE_PANEL.bl_idname

    @classmethod
    def poll(cls, context):
        return context.active_bone is not None and context.active_object.sollum_type == SollumType.FRAGMENT

    def draw(self, context):
        layout = self.layout

        bone = context.active_bone
        layout.separator()
        layout.label(text="Fragment")
        layout.prop(bone, "sollumz_use_physics")


class SOLLUMZ_PT_BONE_PHYSICS_SUBPANEL(bpy.types.Panel):
    bl_label = "Physics"
    bl_idname = "SOLLUMZ_PT_BONE_PHYSICS_SUBPANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "bone"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_BONE_PHYSICS_PANEL.bl_idname

    @classmethod
    def poll(cls, context):
        return context.active_bone is not None and context.active_bone.sollumz_use_physics == True

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        bone = context.active_bone

        # Display mass first and separated from other properties
        # since it is most important
        layout.prop(bone.group_properties, "mass")
        layout.separator()

        for prop in GroupProperties.__annotations__:
            if prop == "mass":
                continue

            layout.prop(bone.group_properties, prop)


class SOLLUMZ_PT_PHYSICS_CHILD_PANEL(bpy.types.Panel):
    bl_label = "Physics"
    bl_idname = "SOLLUMZ_PT_PHYSICS_CHILD_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_OBJECT_PANEL.bl_idname

    @classmethod
    def poll(cls, context):
        aobj = context.active_object
        return aobj is not None and aobj.sollum_type in BOUND_TYPES and find_fragment_parent(aobj)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        aobj = context.active_object

        child_props = aobj.child_properties

        layout.prop(child_props, "mass")
        layout.prop(child_props, "Damaged")


class SOLLUMZ_PT_FRAGMENT_GEOMETRY_PANEL(bpy.types.Panel):
    bl_label = "Physics"
    bl_idname = "SOLLUMZ_PT_FRAGMENT_GEOMETRY_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options = {"HIDE_HEADER"}
    bl_parent_id = SOLLUMZ_PT_OBJECT_PANEL.bl_idname

    @classmethod
    def poll(cls, context):
        aobj = context.active_object
        return aobj is not None and aobj.sollum_type == SollumType.FRAG_GEOM

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.prop(context.active_object, "sollumz_is_physics_child_mesh")
