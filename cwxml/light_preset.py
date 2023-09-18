from .element import VectorProperty, AttributeProperty, ValueProperty, TextProperty, ElementTree, ListProperty


class LightPresetsFile(ElementTree):
    tag_name = "LightPresetsFile"

    def __init__(self):
        super().__init__()
        self.presets = LightPresets()


class LightPreset(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.name = AttributeProperty("name", "NULL")

        # Blender properties
        self.color = VectorProperty("Color")
        self.energy = ValueProperty("Energy")
        self.cutoff_distance = ValueProperty("CutoffDistance")
        self.shadow_soft_size = ValueProperty("ShadowSoftSize")
        self.volume_factor = ValueProperty("VolumeFactor")
        self.shadow_buffer_clip_start = ValueProperty("ShadowBufferClipStart")
        self.spot_size = ValueProperty("SpotSize")
        self.spot_blend = ValueProperty("SpotBlend")
 
        # RAGE properties
        self.time_flags = ValueProperty("TimeFlags")
        self.flags = ValueProperty("Flags")
        self.projected_texture_hash = TextProperty("ProjectedTextureHash")
        self.flashiness = ValueProperty("Flashiness")
        self.volume_size_scale = ValueProperty("VolumeSizeScale")
        self.volume_outer_color = VectorProperty("VolumeOuterColor")
        self.volume_outer_intensity = ValueProperty("VolumeOuterIntensity")
        self.volume_outer_exponent = ValueProperty("VolumeOuterExponent")
        self.light_fade_distance = ValueProperty("LightFadeDistance")
        self.shadow_fade_distance = ValueProperty("ShadowFadeDistance")
        self.specular_fade_distance = ValueProperty("SpecularFadeDistance")
        self.volumetric_fade_distance = ValueProperty("VolumetricFadeDistance")
        self.culling_plane_normal = VectorProperty("CullingPlaneNormal")
        self.culling_plane_offset = ValueProperty("CullingPlaneOffset")
        self.corona_size = ValueProperty("CoronaSize")
        self.corona_intensity = ValueProperty("CoronaIntensity")
        self.corona_z_bias = ValueProperty("CoronaZBias")
        self.unknown_45 = ValueProperty("Unknown45")
        self.unknown_46 = ValueProperty("Unknown46")
        self.shadow_blur = ValueProperty("ShadowBlur")

        self.cone_inner_angle = ValueProperty("ConeInnerAngle")
        self.cone_outer_angle = ValueProperty("ConeOuterAngle")
        self.extent = VectorProperty("Extent")


class LightPresets(ListProperty):
    list_type = LightPreset
    tag_name = "LightPresets"
