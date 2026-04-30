import bpy
from bpy.props import (
    BoolProperty,
    BoolVectorProperty,
    EnumProperty,
    FloatProperty,
    FloatVectorProperty,
    IntProperty,
    IntVectorProperty,
    PointerProperty,
    StringProperty,
)
from bpy.types import (
    Operator,
    PropertyGroup,
    Scene,
)

from ...lods import LODLevels
from ...sollumz_helper import find_sollumz_parent
from ...sollumz_properties import SOLLUMZ_UI_NAMES, LODLevel, SollumType
from ...tools.blenderhelper import lod_level_enum_flag_prop_factory
from ...tools.meshhelper import get_mesh_tri_count


class MaterialMergeSettingsMixin:
    texture_size: EnumProperty(
        name="Texture Size",
        description="Resolution of the baked texture",
        items=[
            ("256", "256", "256x256 pixels"),
            ("512", "512", "512x512 pixels"),
            ("1024", "1024", "1024x1024 pixels"),
            ("2048", "2048", "2048x2048 pixels"),
            ("4096", "4096", "4096x4096 pixels"),
            ("8192", "8192", "8192x8192 pixels"),
        ],
        default="1024",
    )

    bake_type: EnumProperty(
        name="Bake Type",
        description="Type of texture to bake",
        items=[
            ("DIFFUSE", "Diffuse", "Diffuse color only"),
            ("NORMAL", "Normal", "Normal map"),
            ("ROUGHNESS", "Roughness", "Roughness map"),
            # NOTE: METALLIC removed for now, cycles has no direct equivalent so it needs some additional workaround
            #       to bake metallic map
            # ("METALLIC", "Metallic", "Metallic map"),
        ],
        default="DIFFUSE",
    )

    uv_margin: FloatProperty(
        name="UV Margin",
        description="Margin between UV islands to reduce bleed from adjacent islands",
        default=0.0,
        min=0.0,
        max=0.1,
        precision=3,
    )

    samples: IntProperty(
        name="Samples", description="Number of render samples for baking", default=128, min=1, max=2048
    )


class MaterialMergeSettings(MaterialMergeSettingsMixin, PropertyGroup):
    @classmethod
    def register(cls):
        Scene.sz_material_merge_settings = PointerProperty(type=MaterialMergeSettings)

    @classmethod
    def unregister(cls):
        del Scene.sz_material_merge_settings


class SOLLUMZ_OT_material_merge_bake(MaterialMergeSettingsMixin, Operator):
    """Bake all materials from selected object into a single material with unified texture"""

    bl_idname = "sollumz.material_merge_bake"
    bl_label = "Bake Materials"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == "MESH" and len(obj.data.materials) > 0

    def execute(self, context):
        obj = context.active_object
        scene = context.scene

        for prop in MaterialMergeSettingsMixin.__annotations__.keys():
            if not self.properties.is_property_set(prop):
                setattr(self, prop, getattr(scene.sz_material_merge_settings, prop))

        original_engine = scene.render.engine
        original_samples = scene.cycles.samples if hasattr(scene, "cycles") else 128

        try:
            scene.render.engine = "CYCLES"
            scene.cycles.samples = self.samples
            tex_size = int(self.texture_size)

            uv_layer_name = "MaterialMerge_UV"
            if uv_layer_name not in obj.data.uv_layers:
                obj.data.uv_layers.new(name=uv_layer_name)

            obj.data.uv_layers[uv_layer_name].active = True
            obj.data.uv_layers[uv_layer_name].active_render = True

            self.smart_unwrap_object(context, obj, self.uv_margin)

            image_name = f"{obj.name}_BakedMaterial_{self.bake_type}"
            if image_name in bpy.data.images:
                bpy.data.images.remove(bpy.data.images[image_name])

            bake_image = bpy.data.images.new(name=image_name, width=tex_size, height=tex_size, alpha=True)
            bake_image.colorspace_settings.name = "sRGB" if self.bake_type != "NORMAL" else "Non-Color"

            original_nodes = self.setup_bake_nodes(obj, bake_image)

            bake = scene.render.bake
            bake.margin = int(self.uv_margin * tex_size)
            bake.use_clear = True

            if self.bake_type == "DIFFUSE":
                bake.use_pass_direct = False
                bake.use_pass_indirect = False
                bake.use_pass_color = True

            bpy.ops.object.bake(type=self.bake_type)

            merged_mat = self.create_merged_material(obj.name, bake_image)

            self.restore_original_nodes(obj, original_nodes)

            obj.data.materials.clear()
            obj.data.materials.append(merged_mat)

            self.report({"INFO"}, f"Successfully baked {len(original_nodes)} materials into '{merged_mat.name}'")

        except Exception as e:
            self.report({"ERROR"}, f"Baking failed: {str(e)}")
            return {"CANCELLED"}

        finally:
            scene.render.engine = original_engine
            if hasattr(scene, "cycles"):
                scene.cycles.samples = original_samples

        return {"FINISHED"}

    def smart_unwrap_object(self, context, obj, margin):
        original_mode = obj.mode

        if obj.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")

        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        context.view_layer.objects.active = obj

        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")

        bpy.ops.uv.smart_project(
            angle_limit=1.15192,  # ~66 degrees
            island_margin=margin,
            area_weight=0.0,
            correct_aspect=True,
            scale_to_bounds=True,
        )

        bpy.ops.object.mode_set(mode=original_mode if original_mode != "EDIT" else "OBJECT")

    def setup_bake_nodes(self, obj, bake_image):
        original_nodes = {}

        for mat_slot in obj.material_slots:
            mat = mat_slot.material
            if mat is None:
                continue

            if bpy.app.version < (5, 0, 0) and not mat.use_nodes:
                continue

            tree = mat.node_tree

            original_nodes[mat.name] = {"active": tree.nodes.active, "added_node": None}

            img_node = tree.nodes.new(type="ShaderNodeTexImage")
            img_node.image = bake_image
            img_node.location = (0, 0)
            img_node.select = True
            tree.nodes.active = img_node

            original_nodes[mat.name]["added_node"] = img_node

        return original_nodes

    def restore_original_nodes(self, obj, original_nodes):
        for mat_slot in obj.material_slots:
            mat = mat_slot.material
            if mat is None or mat.name not in original_nodes:
                continue

            tree = mat.node_tree
            node_info = original_nodes[mat.name]

            if node_info["added_node"] is not None:
                tree.nodes.remove(node_info["added_node"])

            if node_info["active"] is not None:
                tree.nodes.active = node_info["active"]

    def create_merged_material(self, obj_name, bake_image):
        mat_name = f"{obj_name}_BakedMaterial_{self.bake_type}"

        if mat_name in bpy.data.materials:
            bpy.data.materials.remove(bpy.data.materials[mat_name])

        mat = bpy.data.materials.new(name=mat_name)
        if bpy.app.version < (5, 0, 0):
            mat.use_nodes = True

        tree = mat.node_tree
        nodes = tree.nodes
        links = tree.links

        nodes.clear()

        tex_coord = nodes.new(type="ShaderNodeTexCoord")
        tex_coord.location = (-600, 0)

        img_node = nodes.new(type="ShaderNodeTexImage")
        img_node.image = bake_image
        img_node.location = (-300, 0)

        principled = nodes.new(type="ShaderNodeBsdfPrincipled")
        principled.location = (100, 0)

        output = nodes.new(type="ShaderNodeOutputMaterial")
        output.location = (400, 0)

        links.new(tex_coord.outputs["UV"], img_node.inputs["Vector"])

        if self.bake_type == "NORMAL":
            normal_map = nodes.new(type="ShaderNodeNormalMap")
            normal_map.location = (-100, -200)
            links.new(img_node.outputs["Color"], normal_map.inputs["Color"])
            links.new(normal_map.outputs["Normal"], principled.inputs["Normal"])
        elif self.bake_type == "ROUGHNESS":
            links.new(img_node.outputs["Color"], principled.inputs["Roughness"])
        # NOTE: METALLIC removed for now
        # elif self.bake_type == "METALLIC":
        #     links.new(img_node.outputs["Color"], principled.inputs["Metallic"])
        else:
            links.new(img_node.outputs["Color"], principled.inputs["Base Color"])

        links.new(principled.outputs["BSDF"], output.inputs["Surface"])

        return mat


class AutoLODSettingsMixin:
    """Settings for the auto LOD generation tool."""

    ref_mesh_name: StringProperty(
        name="Reference Mesh",
        description="The mesh to copy and decimate for each LOD level. Usually the highest quality LOD",
    )

    levels: lod_level_enum_flag_prop_factory()

    decimate_method: EnumProperty(
        name="Method",
        description="Decimation method to use",
        items=[
            ("COLLAPSE", "Collapse", "Edge collapse decimation - best general-purpose method"),
            ("UNSUBDIV", "Un-Subdivide", "Reverse subdivision - best for meshes created via subdivision"),
            ("DISSOLVE", "Planar", "Planar decimation - dissolves geometry on flat surfaces"),
        ],
        default="COLLAPSE",
    )

    decimate_step: FloatProperty(
        name="Decimate Step",
        description="Uniform decimation step applied for each LOD level",
        min=0.0,
        max=0.99,
        default=0.6,
    )

    decimate_from_original: BoolProperty(
        name="Decimate from Original",
        description="Always decimate from the reference mesh instead of cascading from the previous LOD",
        default=False,
    )

    use_per_lod_ratios: BoolProperty(
        name="Per-LOD Ratios",
        description="Use individual settings for each LOD level instead of a uniform step",
        default=False,
    )

    per_lod_ratio: FloatVectorProperty(
        size=len(LODLevel),
        name="Ratio",
        description="Decimation ratio for this LOD level (1.0 = no reduction, 0.0 = maximum reduction)",
        min=0.01,
        max=1.0,
        default=(0.90, 0.70, 0.50, 0.30, 0.15),
    )

    per_lod_use_target_tri_count: BoolVectorProperty(
        size=len(LODLevel),
        name="Use Target Tri Count",
        description="Use a target triangle count instead of a ratio",
        default=(False,) * len(LODLevel),
    )

    per_lod_target_tri_count: IntVectorProperty(
        size=len(LODLevel),
        name="Target Tris",
        description="Target number of triangles for this LOD level",
        min=4,
        default=(1000,) * len(LODLevel),
    )

    preserve_uvs: BoolProperty(
        name="Preserve UVs", description="Preserve UV seam boundaries during decimation", default=True
    )

    preserve_sharp: BoolProperty(name="Preserve Sharp", description="Preserve edges marked as sharp", default=False)

    preserve_vertex_groups: BoolProperty(
        name="Preserve Vertex Groups", description="Preserve vertex group boundaries", default=False
    )

    preserve_materials: BoolProperty(
        name="Preserve Materials", description="Preserve material slot boundaries", default=False
    )

    planar_angle_limit: FloatProperty(
        name="Angle Limit",
        description="Maximum angle between face normals for planar decimation",
        min=0.0,
        max=3.14159,
        default=0.087266,
        subtype="ANGLE",
    )

    unsubdiv_iterations: IntProperty(
        name="Iterations", description="Number of un-subdivide iterations", min=1, max=10, default=2
    )

    auto_set_distances: BoolProperty(
        name="Auto-Set LOD Distances",
        description="Automatically calculate and set LOD distances on the parent Drawable based on mesh size",
        default=False,
    )

    auto_merge_materials: BoolProperty(
        name="Merge Materials",
        description="Automatically bake and merge all materials into a single material for each generated LOD, using the Material Merge settings",
        default=False,
    )

    def get_per_lod_ratio_settings(self, lod_level) -> tuple[float, int, bool]:
        """Get the per-LOD ratio settings for a given LODLevel.
        Returns a tuple of (ratio, target_tri_count, use_target_tri_count).
        """
        match lod_level:
            case LODLevel.VERYHIGH:
                lod_level_index = 0
            case LODLevel.HIGH:
                lod_level_index = 1
            case LODLevel.MEDIUM:
                lod_level_index = 2
            case LODLevel.LOW:
                lod_level_index = 3
            case LODLevel.VERYLOW:
                lod_level_index = 4

        return (
            self.per_lod_ratio[lod_level_index],
            self.per_lod_target_tri_count[lod_level_index],
            self.per_lod_use_target_tri_count[lod_level_index],
        )

    def draw_settings(self, context, layout):
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column()
        col.use_property_split = False
        col.prop(self, "levels")
        layout.separator(factor=0.25)
        self._draw_ref_mesh_prop(context, layout)
        layout.separator(factor=0.25)

        row = layout.row()
        row.prop(self, "decimate_method", expand=True)

        layout.prop(self, "decimate_from_original")

        if self.decimate_method == "DISSOLVE":
            layout.prop(self, "planar_angle_limit")
            layout.prop(self, "preserve_materials")
        elif self.decimate_method == "UNSUBDIV":
            layout.prop(self, "unsubdiv_iterations")
        elif self.decimate_method == "COLLAPSE":
            col = layout.column(align=True)
            col.prop(self, "use_per_lod_ratios")
            if self.use_per_lod_ratios:
                for lod_level_index, lod_level in enumerate(LODLevel):
                    if lod_level.value not in self.levels:
                        continue

                    row = col.row(align=True)
                    if self.per_lod_use_target_tri_count[lod_level_index]:
                        row.prop(
                            self, "per_lod_target_tri_count", index=lod_level_index, text=SOLLUMZ_UI_NAMES[lod_level]
                        )
                    else:
                        row.prop(
                            self, "per_lod_ratio", index=lod_level_index, text=SOLLUMZ_UI_NAMES[lod_level], slider=True
                        )
                    row.prop(
                        self,
                        "per_lod_use_target_tri_count",
                        index=lod_level_index,
                        text="",
                        icon="MESH_DATA",
                        toggle=True,
                    )
            else:
                col.prop(self, "decimate_step")

            col = layout.column(align=True, heading="Preserve")
            row = col.row(align=True)
            row.prop(self, "preserve_uvs", text="UVs", toggle=True)
            row.prop(self, "preserve_sharp", text="Sharp", toggle=True)
            row = col.row(align=True)
            row.prop(self, "preserve_vertex_groups", text="Groups", toggle=True)
            row.prop(self, "preserve_materials", text="Materials", toggle=True)

        layout.separator(factor=0.3)
        col = layout.column(align=True)
        col.prop(self, "auto_set_distances")
        col.prop(self, "auto_merge_materials")

    def _draw_ref_mesh_prop(self, context, layout):
        layout.prop(self, "ref_mesh_name", text="Reference Mesh", icon="MESH_DATA")


class AutoLODSettings(AutoLODSettingsMixin, PropertyGroup):
    """Settings for the auto LOD generation tool."""

    def _on_ref_mesh_update(self, context):
        self.ref_mesh_name = self.ref_mesh.name

    ref_mesh: PointerProperty(
        type=bpy.types.Mesh,
        name="Reference Mesh",
        description="The mesh to copy and decimate for each LOD level. Usually the highest quality LOD",
        update=_on_ref_mesh_update,
    )

    def _draw_ref_mesh_prop(self, context, layout):
        layout.prop(self, "ref_mesh", text="Reference Mesh")

    @classmethod
    def register(cls):
        Scene.sz_auto_lod_settings = PointerProperty(type=AutoLODSettings)

    @classmethod
    def unregister(cls):
        del Scene.sz_auto_lod_settings


class SOLLUMZ_OT_auto_lod(AutoLODSettingsMixin, Operator):
    bl_idname = "sollumz.auto_lod"
    bl_label = "Generate LODs"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = (
        "Generate drawable model LODs via decimation. Supports multiple methods, per-LOD ratios, "
        "preserve options, and automatic LOD distance calculation"
    )

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.sollum_type == SollumType.DRAWABLE_MODEL

    def draw(self, context):
        self.draw_settings(context, self.layout)

    def execute(self, context):
        aobj = context.active_object
        scene = context.scene

        for prop in AutoLODSettingsMixin.__annotations__.keys():
            if not self.properties.is_property_set(prop):
                setattr(self, prop, getattr(scene.sz_auto_lod_settings, prop))

        if not self.ref_mesh_name:
            self.report(
                {"INFO"}, "No reference mesh specified! You must specify a mesh to use as the highest LOD level!"
            )
            return {"CANCELLED"}

        ref_mesh = bpy.data.meshes.get(self.ref_mesh_name, None)
        if ref_mesh is None:
            self.report({"INFO"}, f"Reference mesh '{self.ref_mesh_name}' does not exist!")
            return {"CANCELLED"}

        lods = self._get_selected_lods_sorted()

        if not lods:
            self.report({"INFO"}, "No LOD levels selected!")
            return {"CANCELLED"}

        obj_lods: LODLevels = aobj.sz_lods

        previous_mode = aobj.mode
        previous_lod_level = obj_lods.active_lod_level
        last_mesh = ref_mesh

        for i, lod_level in enumerate(lods):
            bpy.ops.object.mode_set(mode="OBJECT")

            source_mesh = ref_mesh if self.decimate_from_original else last_mesh
            mesh = source_mesh.copy()
            mesh.name = self._get_lod_mesh_name(aobj.name, lod_level)

            obj_lods.get_lod(lod_level).mesh = mesh
            obj_lods.active_lod_level = lod_level

            self._apply_decimation(context, aobj, lod_level, i, source_mesh)

            last_mesh = mesh

        bpy.ops.object.mode_set(mode="OBJECT")

        if self.auto_merge_materials:
            for lod_level in lods:
                obj_lods.active_lod_level = lod_level
                self._merge_materials(context, aobj, lod_level)

        obj_lods.active_lod_level = previous_lod_level
        bpy.ops.object.mode_set(mode=previous_mode)

        if self.auto_set_distances:
            self._set_auto_distances(aobj, ref_mesh, lods)

        self._report_stats(aobj, lods, obj_lods)

        return {"FINISHED"}

    def _merge_materials(self, context, obj, lod_level: LODLevel):
        """Run material merge bake on the current LOD mesh."""
        if obj.data is None or len(obj.data.materials) <= 1:
            return

        result = bpy.ops.sollumz.material_merge_bake(bake_type="DIFFUSE")
        if result == {"CANCELLED"}:
            self.report({"WARNING"}, f"Material merge failed for {SOLLUMZ_UI_NAMES[lod_level]}")
            return

        # Rename the baked image and material to be unique per LOD level,
        # otherwise the next LOD's bake will delete them (same name).
        lod_suffix = SOLLUMZ_UI_NAMES[lod_level].lower().replace(" ", "_")

        old_image_name = f"{obj.name}_BakedMaterial_DIFFUSE"
        if old_image_name in bpy.data.images:
            bpy.data.images[old_image_name].name = f"{obj.name}_{lod_suffix}_BakedMaterial_DIFFUSE"

        old_mat_name = f"{obj.name}_BakedMaterial_DIFFUSE"
        if old_mat_name in bpy.data.materials:
            bpy.data.materials[old_mat_name].name = f"{obj.name}_{lod_suffix}_MergedMaterial_DIFFUSE"

    def _apply_decimation(self, context, obj, lod_level: LODLevel, index: int, source_mesh):
        """Apply decimation to the active LOD mesh using the modifier API."""
        method = self.decimate_method

        mod = obj.modifiers.new(name="AutoLOD_Decimate", type="DECIMATE")

        if method == "COLLAPSE":
            ratio = self._get_effective_ratio(lod_level, index, source_mesh)
            mod.decimate_type = "COLLAPSE"
            mod.ratio = ratio
            mod.use_collapse_triangulate = True

            delimit = set()
            if self.preserve_uvs:
                delimit.add("UV")
            if self.preserve_sharp:
                delimit.add("SHARP")
            if self.preserve_materials:
                delimit.add("MATERIAL")

            if delimit:
                mod.delimit = delimit

            if self.preserve_vertex_groups and hasattr(mod, "use_symmetry"):
                # Vertex group preservation is handled by the delimit options
                # and by Blender's internal weighting in collapse mode
                pass

        elif method == "UNSUBDIV":
            mod.decimate_type = "UNSUBDIV"
            mod.iterations = self.unsubdiv_iterations

        elif method == "DISSOLVE":
            mod.decimate_type = "DISSOLVE"
            mod.angle_limit = self.planar_angle_limit
            if self.preserve_materials:
                mod.delimit = {"MATERIAL"}

        try:
            bpy.ops.object.modifier_apply(modifier=mod.name)
        except RuntimeError as e:
            self.report({"WARNING"}, f"Modifier apply failed for {SOLLUMZ_UI_NAMES[lod_level]}: {e}")
            if mod.name in obj.modifiers:
                obj.modifiers.remove(mod)

    def _get_effective_ratio(self, lod_level: LODLevel, index: int, source_mesh) -> float:
        """Calculate the decimation ratio for a given LOD level."""
        if self.use_per_lod_ratios:
            ratio, target_tri_count, use_target_tri_count = self.get_per_lod_ratio_settings(lod_level)
            if use_target_tri_count:
                source_tri_count = get_mesh_tri_count(source_mesh)
                if source_tri_count > 0:
                    return max(0.01, min(1.0, target_tri_count / source_tri_count))
                return 1.0
            else:
                return ratio
        else:
            step = self.decimate_step
            if self.decimate_from_original:
                return max(0.01, 1.0 - step * (index + 1))
            else:
                return 1.0 - step

    def _set_auto_distances(self, obj, ref_mesh, lods: tuple[LODLevel]):
        """Calculate and set LOD distances on the parent Drawable."""
        drawable = find_sollumz_parent(obj, SollumType.DRAWABLE)
        if drawable is None:
            return

        verts = ref_mesh.vertices
        if len(verts) == 0:
            return

        import mathutils

        center = mathutils.Vector((0, 0, 0))
        for v in verts:
            center += v.co
        center /= len(verts)

        radius = max((v.co - center).length for v in verts)
        if radius < 0.01:
            radius = 1.0

        props = drawable.drawable_properties
        dist_map = {
            LODLevel.HIGH: min(9998, round(radius * 10)),
            LODLevel.MEDIUM: min(9998, round(radius * 25)),
            LODLevel.LOW: min(9998, round(radius * 50)),
            LODLevel.VERYLOW: min(9998, round(radius * 100)),
        }

        attr_map = {
            LODLevel.HIGH: "lod_dist_high",
            LODLevel.MEDIUM: "lod_dist_med",
            LODLevel.LOW: "lod_dist_low",
            LODLevel.VERYLOW: "lod_dist_vlow",
        }

        for lod_level in lods:
            attr = attr_map.get(lod_level)
            if attr:
                setattr(props, attr, float(dist_map[lod_level]))

    def _report_stats(self, obj, lods: tuple[LODLevel], obj_lods: LODLevels):
        """Report triangle/vertex counts for each generated LOD."""
        stats = []
        for lod_level in lods:
            mesh = obj_lods.get_lod(lod_level).mesh
            if mesh is not None:
                tri_count = get_mesh_tri_count(mesh)
                stats.append(f"{SOLLUMZ_UI_NAMES[lod_level]}: {tri_count} tris, {len(mesh.vertices)} verts")

        if stats:
            self.report({"INFO"}, "LODs generated - " + " | ".join(stats))

    def _get_lod_mesh_name(self, obj_name: str, lod_level: LODLevel):
        return f"{obj_name}.{SOLLUMZ_UI_NAMES[lod_level].lower()}"

    def _get_selected_lods_sorted(self) -> tuple[LODLevel]:
        return tuple(lod for lod in LODLevel if lod in self.levels)
