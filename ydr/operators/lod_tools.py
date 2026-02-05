import bpy
from bpy.types import Operator


class SOLLUMZ_OT_material_merge_bake(Operator):
    """Bake all materials from selected object into a single material with unified texture"""
    bl_idname = "sollumz.material_merge_bake"
    bl_label = "Bake Materials"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj is not None and obj.type == "MESH" and len(obj.data.materials) > 0)

    def execute(self, context):
        obj = context.active_object
        settings = context.scene.sollumz_material_merge_settings

        original_engine = context.scene.render.engine
        original_samples = context.scene.cycles.samples if hasattr(context.scene, "cycles") else 128

        try:
            context.scene.render.engine = "CYCLES"
            context.scene.cycles.samples = settings.samples
            tex_size = int(settings.texture_size)

            uv_layer_name = "MaterialMerge_UV"
            if uv_layer_name not in obj.data.uv_layers:
                obj.data.uv_layers.new(name=uv_layer_name)

            obj.data.uv_layers[uv_layer_name].active = True
            obj.data.uv_layers[uv_layer_name].active_render = True

            self.smart_unwrap_object(context, obj, settings.uv_margin)

            image_name = f"{obj.name}_BakedMaterial"
            if image_name in bpy.data.images:
                bpy.data.images.remove(bpy.data.images[image_name])

            bake_image = bpy.data.images.new(
                name=image_name,
                width=tex_size,
                height=tex_size,
                alpha=True
            )
            bake_image.colorspace_settings.name = "sRGB" if settings.bake_type != "NORMAL" else "Non-Color"

            original_nodes = self.setup_bake_nodes(obj, bake_image)

            bake = context.scene.render.bake
            bake.margin = int(settings.uv_margin * tex_size)
            bake.use_clear = True

            if settings.bake_type == "DIFFUSE":
                bake.use_pass_direct = False
                bake.use_pass_indirect = False
                bake.use_pass_color = True

            bpy.ops.object.bake(type=settings.bake_type)

            merged_mat = self.create_merged_material(obj.name, bake_image, settings.bake_type)

            self.restore_original_nodes(obj, original_nodes)

            obj.data.materials.clear()
            obj.data.materials.append(merged_mat)

            self.report({"INFO"}, f"Successfully baked {len(original_nodes)} materials into '{merged_mat.name}'")

        except Exception as e:
            self.report({"ERROR"}, f"Baking failed: {str(e)}")
            return {"CANCELLED"}

        finally:
            context.scene.render.engine = original_engine
            if hasattr(context.scene, "cycles"):
                context.scene.cycles.samples = original_samples

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
            scale_to_bounds=True
        )

        bpy.ops.object.mode_set(mode=original_mode if original_mode != "EDIT" else "OBJECT")

    def setup_bake_nodes(self, obj, bake_image):
        original_nodes = {}

        for mat_slot in obj.material_slots:
            mat = mat_slot.material
            if mat is None or not mat.use_nodes:
                continue

            tree = mat.node_tree

            original_nodes[mat.name] = {
                "active": tree.nodes.active,
                "added_node": None
            }

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

    def create_merged_material(self, obj_name, bake_image, bake_type):
        mat_name = f"{obj_name}_MergedMaterial"

        if mat_name in bpy.data.materials:
            bpy.data.materials.remove(bpy.data.materials[mat_name])

        mat = bpy.data.materials.new(name=mat_name)
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

        if bake_type == "NORMAL":
            normal_map = nodes.new(type="ShaderNodeNormalMap")
            normal_map.location = (-100, -200)
            links.new(img_node.outputs["Color"], normal_map.inputs["Color"])
            links.new(normal_map.outputs["Normal"], principled.inputs["Normal"])
        elif bake_type == "ROUGHNESS":
            links.new(img_node.outputs["Color"], principled.inputs["Roughness"])
        elif bake_type == "METALLIC":
            links.new(img_node.outputs["Color"], principled.inputs["Metallic"])
        else:
            links.new(img_node.outputs["Color"], principled.inputs["Base Color"])

        links.new(principled.outputs["BSDF"], output.inputs["Surface"])

        return mat
