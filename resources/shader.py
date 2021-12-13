import xml.etree.ElementTree as ET
import os
from .codewalker_xml import *
from .drawable import ParametersListProperty, VertexLayoutListProperty
from ..tools.utils import *


class RenderBucketProperty(ElementProperty):
    value_types = (list)

    def __init__(self, tag_name=None, value=None):
        super().__init__(tag_name or "RenderBucket", value or [])

    @classmethod
    def from_xml(cls, element: ET.Element):
        new = cls()
        items = element.text.strip().split(" ")
        for item in items:
            new.value.append(int(item))
        return items

    def to_xml(self):
        element = ET.Element(self.tag_name)
        element.text = " ".join(self.value)


class FileNameListProperty(ListProperty):
    class FileNameItem(TextProperty):
        tag_name = "Item"

    list_type = FileNameItem
    tag_name = "FileName"


class LayoutListProperty(ListProperty):
    class Layout(VertexLayoutListProperty):
        tag_name = "Item"

    list_type = Layout
    tag_name = "Layout"


class Shader(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.name = TextProperty("Name", "")
        self.filenames = FileNameListProperty()
        self.render_bucket = RenderBucketProperty()
        self.layouts = LayoutListProperty()
        self.parameters = ParametersListProperty("Parameters")

    @property
    def required_tangent(self):
        for layout in self.layouts:
            if "Tangent" in layout.value:
                return True
        return False

    def get_layout_from_semantic(self, vertex_semantic, is_skinned=False):
        for layout in self.layouts:
            if layout.vertex_semantic == vertex_semantic:
                return layout
        #error = f"{vertex_semantic} layout is not found in the shader '{self.name}'"
        #error += "\nThe possible layouts you can have are"
        # for l in self.layouts:
        #    error += f", {l.vertex_semantic}"
        #raise Exception(error)
        if is_skinned:
            for layout in self.layouts:
                if "BlendWeights" in layout.value:
                    return layout

        return self.layouts[0]


class ShaderManager:
    shaderxml = os.path.join(os.path.dirname(__file__), "shaders.xml")
    shaders = {}
    terrains = ["terrain_cb_w_4lyr.sps", "terrain_cb_w_4lyr_lod.sps", "terrain_cb_w_4lyr_spec.sps", "terrain_cb_w_4lyr_spec_pxm.sps", "terrain_cb_w_4lyr_pxm_spm.sps",
                "terrain_cb_w_4lyr_pxm.sps", "terrain_cb_w_4lyr_cm_pxm.sps", "terrain_cb_w_4lyr_cm_tnt.sps", "terrain_cb_w_4lyr_cm_pxm_tnt.sps", "terrain_cb_w_4lyr_cm.sps",
                "terrain_cb_w_4lyr_2tex.sps", "terrain_cb_w_4lyr_2tex_blend.sps", "terrain_cb_w_4lyr_2tex_blend_lod.sps", "terrain_cb_w_4lyr_2tex_blend_pxm.sps",
                "terrain_cb_w_4lyr_2tex_blend_pxm_spm.sps", "terrain_cb_w_4lyr_2tex_pxm.sps", "terrain_cb_4lyr.sps", "terrain_cb_w_4lyr_spec_int_pxm.sps",
                "terrain_cb_w_4lyr_spec_int.sps", "terrain_cb_4lyr_lod.sps"]
    mask_only_terrains = ["terrain_cb_w_4lyr_cm.sps", "terrain_cb_w_4lyr_cm_tnt.sps",
                          "terrain_cb_w_4lyr_cm_pxm_tnt.sps", "terrain_cb_w_4lyr_cm_pxm.sps"]
    cutouts = ["cutout.sps", "cutout_um.sps", "cutout_tnt.sps", "cutout_fence.sps", "cutout_fence_normal.sps", "cutout_hard.sps", "cutout_spec_tnt.sps", "normal_cutout.sps",
               "normal_cutout_tnt.sps", "normal_cutout_um.sps", "normal_spec_cutout.sps", "normal_spec_cutout_tnt.sps", "trees_lod.sps", "trees.sps", "trees_tnt.sps",
               "trees_normal.sps", "trees_normal_spec.sps", "trees_normal_spec_tnt.sps", "trees_normal_diffspec.sps", "trees_normal_diffspec_tnt.sps"]
    alphas = ["normal_spec_alpha.sps", "normal_spec_reflect_alpha.sps", "normal_spec_reflect_emissivenight_alpha.sps", "normal_spec_screendooralpha.sps", "normal_alpha.sps",
              "normal_reflect_alpha.sps", "emissive_alpha.sps", "emissive_alpha_tnt.sps", "emissive_additive_alpha.sps", "emissivenight_alpha.sps", "emissivestrong_alpha.sps",
              "spec_alpha.sps", "spec_reflect_alpha.sps", "alpha.sps", "reflect_alpha.sps", "normal_screendooralpha.sps", "spec_screendooralpha.sps", "cloth_spec_alpha.sps",
              "cloth_normal_spec_alpha.sps"]
    glasses = ["glass.sps", "glass_pv.sps", "glass_pv_env.sps", "glass_env.sps", "glass_spec.sps", "glass_reflect.sps", "glass_emissive.sps", "glass_emissivenight.sps",
               "glass_emissivenight_alpha.sps", "glass_breakable.sps", "glass_breakable_screendooralpha.sps", "glass_displacement.sps", "glass_normal_spec_reflect.sps",
               "glass_emissive_alpha.sps"]
    decals = ["decal.sps", "decal_tnt.sps", "decal_glue.sps", "decal_spec_only.sps", "decal_normal_only.sps", "decal_emissive_only.sps", "decal_emissivenight_only.sps",
              "decal_amb_only.sps", "normal_decal.sps", "normal_decal_pxm.sps", "normal_decal_pxm_tnt.sps", "normal_decal_tnt.sps", "normal_spec_decal.sps", "normal_spec_decal_detail.sps",
              "normal_spec_decal_nopuddle.sps", "normal_spec_decal_tnt.sps", "normal_spec_decal_pxm.sps", "spec_decal.sps", "spec_reflect_decal.sps", "reflect_decal.sps", "decal_dirt.sps",
              "mirror_decal.sps", "distance_map.sps"]
    veh_cutouts = ["vehicle_cutout.sps", "vehicle_badges.sps"]
    veh_glasses = ["vehicle_vehglass.sps", "vehicle_vehglass_inner.sps"]
    veh_decals = ["vehicle_decal.sps", "vehicle_decal2.sps",
                  "vehicle_blurredrotor_emissive.sps"]
    shadow_proxies = ["trees_shadow_proxy.sps"]
    tint_flag_1 = ["trees_normal_diffspec_tnt.sps",
                   "trees_tnt.sps", "trees_normal_spec_tnt.sps"]
    tint_flag_2 = ["weapon_normal_spec_detail_tnt.sps", "weapon_normal_spec_cutout_palette.sps",
                   "weapon_normal_spec_detail_palette.sps", "weapon_normal_spec_palette.sps"]
    em_shaders = ["normal_spec_emissive.sps", "normal_spec_reflect_emissivenight.sps", "emissive.sps", "emissive_clip.sps", "emissive_speclum.sps", "emissive_tnt.sps", "emissivenight.sps",
                  "emissivenight_geomnightonly.sps", "emissivestrong_alpha.sps", "emissivestrong.sps", "normal_spec_reflect_emissivenight_alpha.sps", "emissive_alpha.sps",
                  "emissive_alpha_tnt.sps", "emissive_additive_alpha.sps", "emissivenight_alpha.sps", "glass_emissive.sps", "glass_emissivenight.sps", "glass_emissivenight_alpha.sps",
                  "glass_emissive_alpha.sps", "decal_emissive_only.sps", "decal_emissivenight_only.sps"]

    def tinted_shaders():
        return ShaderManager.cutouts + ShaderManager.alphas + ShaderManager.glasses + ShaderManager.decals + ShaderManager.veh_cutouts + ShaderManager.veh_glasses + ShaderManager.veh_decals + ShaderManager.shadow_proxies

    def cutout_shaders():
        return ShaderManager.cutouts + ShaderManager.veh_cutouts + ShaderManager.shadow_proxies

    @staticmethod
    def load_shaders():
        tree = ET.parse(ShaderManager.shaderxml)
        for node in tree.getroot():
            shader = Shader.from_xml(node)
            ShaderManager.shaders[shader.name] = shader

    @staticmethod
    def print_shader_collection():
        string = ""
        for shader in ShaderManager.shaders.values():
            name = shader.name.upper()
            ui_name = shader.name.replace("_", " ").upper()
            value = shader.name.lower()
            string += "ShaderMaterial(\"" + name + "\", \"" + \
                ui_name + "\", \"" + value + "\"),\n"

        print(string)

    @staticmethod
    def print_all_vertex_semantics():
        sems = []
        for shader in ShaderManager.shaders.values():
            for layout in shader.layouts:
                if layout.vertex_semantic in sems:
                    continue
                else:
                    sems.append(layout.vertex_semantic)

        for s in sems:
            print(s)

    @staticmethod
    def check_bumpmap_to_tangents():
        result = True

        for shader in ShaderManager.shaders.values():
            bumpsamp = False
            tangent = False
            for layout in shader.layouts:
                if "Tangent" in layout.value:
                    tangent = True
            for param in shader.parameters:
                if "BumpSampler" in param.name:
                    bumpsamp = True

            if bumpsamp != tangent:
                result = False
                print(
                    f"shader: {shader.name} bumpsamp: {str(bumpsamp)} tangent: {str(tangent)}")

        if result:
            print(f"{result} dexy is correct")
        else:
            print(f"{result} :(")

    @staticmethod
    def check_if_all_layouts_have_tangents():

        for shader in ShaderManager.shaders.values():
            result = True
            tangent = False
            if "Tangent" in shader.layouts[0].value:
                tangent = True
            for layout in shader.layouts:
                if "Tangent" in layout.value and tangent != True:
                    result = False
                    print(shader.name)
                    break

    @staticmethod
    def print_filename_enum():
        result = []
        for shader in ShaderManager.shaders.values():
            i = 0
            for fn in shader.filenames:
                if fn.value not in result:
                    result.append(f"{shader.name.upper()}{i} = \"{fn.value}\"")
                    i += 1
        print("\t\n".join(result))

    @staticmethod
    def print_all_params():
        result = []
        for shader in ShaderManager.shaders.values():
            for p in shader.parameters:
                if p.name not in result:
                    if p.name:
                        if "sampler" not in p.name.lower():
                            result.append(p.name)
        print(result)
        # print("\t\n".join(result))

    @staticmethod
    def shader_name_fixed(sn):
        result = []
        words = sn.split("_")
        for w in words:
            result.append(w.capitalize())
        return " ".join(result)

    @staticmethod
    def print_layout_github_page():
        result = []

        for shader in ShaderManager.shaders.values():
            res = f"## {ShaderManager.shader_name_fixed(shader.name)} Shader"
            res += "\n"
            res += "### Filenames"
            for f in shader.filenames:
                if f.value != "":
                    res += "\n* " + f.value
            res += "\n"
            res += "### Parameters"
            for p in shader.parameters:
                res += f"\n* {p.type} - {p.name}"
            res += "\n"
            res += "### Vertex Layouts"
            for l in shader.layouts:
                res += f"\n* {l.vertex_semantic} - {l.pretty_vertex_semantic}"
            result.append(res)

        print("\n".join(result))


ShaderManager.load_shaders()
