import bpy
from mathutils import Vector
from .tools import jenkhash as JenkHash
from xml.etree.ElementTree import Element

class ShaderProperty:
    
    def __init__(self, type, name, x = None, y = None, z = None, w = None):
        self.Type = type
        self.Name = name    
        self.X = x
        self.Y = y
        self.Z = z
        self.W = w

    def write(self):
        node = None
        if self.X == None:
            node = Element(self.Type)
            node.set("value", str(self.Name))
        else:
            node = Element(self.Name)
            node.set("x", str(self.X))
            node.set("y", str(self.Y))
            node.set("z", str(self.Z))
            node.set("w", str(self.W))

        return node

    def get_value(self):
        return self.Name

PT = ["Position", "TexCoord0"]
PCTT = ["Position", "Colour0", "TexCoord0", "TexCoord1"]
PNC = ["Position", "Normal", "Colour0"]
PNCT = ["Position", "Normal", "Colour0", "TexCoord0"]
PNCCT = ["Position", "Normal", "Colour0", "Colour1", "TexCoord0"]
PNCTX = ["Position", "Normal", "Colour0", "TexCoord0", "Tangent"]
PNCCTX = ["Position", "Normal", "Colour0", "Colour1", "TexCoord0", "Tangent"]
PNCTTX = ["Position", "Normal", "Colour0", "TexCoord0", "TexCoord1", "Tangent"]
PBBCCT = ["Position", "BlendWeights", "BlendIndices", "Colour0", "Colour1", "TexCoord0"]
PBBNCTX = ["Position", "BlendWeights", "BlendIndices", "Normal", "Colour0", "TexCoord0", "Tangent"]
PBBNCTTX = ["Position", "BlendWeights", "BlendIndices", "Normal", "Colour0", "TexCoord0", "TexCoord1", "Tangent"]
PBBNCTT = ["Position", "BlendWeights", "BlendIndices", "Normal", "Colour0", "TexCoord0", "TexCoord1"]
PBBNCT = ["Position", "BlendWeights", "BlendIndices", "Normal", "Colour0", "TexCoord0"]
PBBNCCT = ["Position", "BlendWeights", "BlendIndices", "Normal", "Colour0", "Colour1", "TexCoord0"]
PBBNCCTX = ["Position", "BlendWeights", "BlendIndices", "Normal", "Colour0", "Colour1", "TexCoord0", "Tangent"]
PBBNCCTTX = ["Position", "BlendWeights", "BlendIndices", "Normal", "Colour0", "Colour1", "TexCoord0", "TexCoord1", "Tangent"]
PNCCTTX = ["Position", "Normal", "Colour0", "Colour1", "TexCoord0", "TexCoord1", "Tangent"]
PNCTTTX = ["Position", "Normal", "Colour0", "TexCoord0", "TexCoord1", "TexCoord2", "Tangent"]
PNCCT3TX = ["Position", "Normal", "Colour0", "Colour1", "TexCoord0", "TexCoord3", "Tangent"]
PNCTT3TX = ["Position", "Normal", "Colour0", "TexCoord0", "TexCoord1", "TexCoord3", "Tangent"]
PBBNCTTT = ["Position", "BlendWeights", "BlendIndices", "Normal", "Colour0", "TexCoord0", "TexCoord1", "TexCoord2"]
PNCCTT = ["Position", "Normal", "Colour0", "Colour1", "TexCoord0", "TexCoord1"]
PNCCTTTT = ["Position", "Normal", "Colour0", "Colour1", "TexCoord0", "TexCoord1", "TexCoord2", "TexCoord3"]
PNCCTTTX = ["Position", "Normal", "Colour0", "Colour1", "TexCoord0", "TexCoord1", "TexCoord3", "Tangent"]
PNCT4T5TX = ["Position", "Normal", "Colour0", "TexCoord0", "TexCoord4", "TexCoord5", "Tangent"]
PNCTT4T5TX = ["Position", "Normal", "Colour0", "TexCoord0", "TexCoord1", "TexCoord4", "TexCoord5", "Tangent"]

blend_2lyrsps = [
                ShaderProperty("Image", "TextureSampler_layer0"),
                ShaderProperty("Image", "BumpSampler_layer0"),
                ShaderProperty("Image", "TextureSampler_layer1"),
                ShaderProperty("Image", "BumpSampler_layer1"),
                ShaderProperty("Image", "LookupSampler"),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 32.0, 0.0, 0.0, 0.0)]

cablesps = [
                ShaderProperty("Layout", PNCT),
                ShaderProperty("Value", "TextureSamp"),
                ShaderProperty("Value", "AlphaTestValue", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gCableParams", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gViewProj", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Shader_cableEmissive", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Shader_cableAmbient", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Shader_cableDiffuse2", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Shader_cableDiffuse", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Shader_windAmount", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Shader_fadeExponent", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Shader_radiusScale", 1.0, 0.0, 0.0, 0.0)]

cloth_defaultsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0)]

cloth_normal_specsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Layout", PNCTX)]

cloth_normal_spec_alphasps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

cloth_normal_spec_cutoutsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

cloth_normal_spec_tntsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "TintPaletteSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

cloth_spec_alphasps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Layout", PNCTX)]

cloth_spec_cutoutsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Layout", PNCTX)]

clouds_altitudesps = [
                ShaderProperty("Layout", PNCTX),
                ShaderProperty("Image", "DensitySampler"),
                ShaderProperty("Image", "NormalSampler"),
                ShaderProperty("Image", "DetailDensitySampler"),
                ShaderProperty("Image", "DetailNormalSampler"),
                ShaderProperty("Image", "DetailDensity2Sampler"),
                ShaderProperty("Image", "DetailNormal2Sampler"),
                ShaderProperty("Image", "DepthMapTexSampler"),
                ShaderProperty("Value", "CloudLayerAnimScale3", 1.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "CloudLayerAnimScale2", 1.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "CloudLayerAnimScale1", 1.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "gSoftParticleRange", 175.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gRescaleUV3", 1.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "gRescaleUV2", 1.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "gRescaleUV1", 1.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "gUVOffset3", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gUVOffset2", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gUVOffset1", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gCameraPos", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gCloudViewProj", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gUVOffset", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gAnimBlendWeights", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gAnimSculpt", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gAnimCombine", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "gNearFarQMult", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gWrapLighting_MSAARef", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "gScaleDiffuseFillAmbient", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "gPiercingLightPower_Strength_NormalStrength_Thickness", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "gScatterG_GSquared_PhaseMult_Scale", -0.75, 0.5625, 2.1, 1.0),
                ShaderProperty("Value", "gDensityShiftScale", 0.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "gBounceColor", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gAmbientColor", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gCloudColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "gSunColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "gSunDirection", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gWestColor", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gEastMinusWestColor", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gSkyColor", 0.0, 0.0, 0.0, 0.0)]

clouds_animsps = [
                ShaderProperty("Layout", PNCTX),
                ShaderProperty("Image", "DensitySampler"),
                ShaderProperty("Image", "NormalSampler"),
                ShaderProperty("Image", "DetailDensitySampler"),
                ShaderProperty("Image", "DetailNormalSampler"),
                ShaderProperty("Image", "DetailDensity2Sampler"),
                ShaderProperty("Image", "DetailNormal2Sampler"),
                ShaderProperty("Image", "DepthMapTexSampler"),
                ShaderProperty("Value", "CloudLayerAnimScale3", 1.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "CloudLayerAnimScale2", 1.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "CloudLayerAnimScale1", 1.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "gSoftParticleRange", 175.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gRescaleUV3", 1.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "gRescaleUV2", 1.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "gRescaleUV1", 1.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "gUVOffset3", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gUVOffset2", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gUVOffset1", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gCameraPos", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gCloudViewProj", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gUVOffset", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gAnimBlendWeights", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gAnimSculpt", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gAnimCombine", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "gNearFarQMult", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gWrapLighting_MSAARef", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "gScaleDiffuseFillAmbient", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "gPiercingLightPower_Strength_NormalStrength_Thickness", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "gScatterG_GSquared_PhaseMult_Scale", -0.75, 0.5625, 2.1, 1.0),
                ShaderProperty("Value", "gDensityShiftScale", 0.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "gBounceColor", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gAmbientColor", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gCloudColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "gSunColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "gSunDirection", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gWestColor", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gEastMinusWestColor", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gSkyColor", 0.0, 0.0, 0.0, 0.0)]

clouds_animsoftsps = [
                ShaderProperty("Layout", PNCTX),
                ShaderProperty("Image", "DensitySampler"),
                ShaderProperty("Image", "NormalSampler"),
                ShaderProperty("Image", "DetailDensitySampler"),
                ShaderProperty("Image", "DetailNormalSampler"),
                ShaderProperty("Image", "DetailDensity2Sampler"),
                ShaderProperty("Image", "DetailNormal2Sampler"),
                ShaderProperty("Image", "DepthMapTexSampler"),
                ShaderProperty("Value", "CloudLayerAnimScale3", 1.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "CloudLayerAnimScale2", 1.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "CloudLayerAnimScale1", 1.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "gSoftParticleRange", 175.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gRescaleUV3", 1.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "gRescaleUV2", 1.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "gRescaleUV1", 1.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "gUVOffset3", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gUVOffset2", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gUVOffset1", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gCameraPos", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gCloudViewProj", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gUVOffset", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gAnimBlendWeights", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gAnimSculpt", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gAnimCombine", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "gNearFarQMult", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gWrapLighting_MSAARef", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "gScaleDiffuseFillAmbient", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "gPiercingLightPower_Strength_NormalStrength_Thickness", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "gScatterG_GSquared_PhaseMult_Scale", -0.75, 0.5625, 2.1, 1.0),
                ShaderProperty("Value", "gDensityShiftScale", 0.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "gBounceColor", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gAmbientColor", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gCloudColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "gSunColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "gSunDirection", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gWestColor", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gEastMinusWestColor", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gSkyColor", 0.0, 0.0, 0.0, 0.0)]

clouds_fastsps = [
                ShaderProperty("Layout", PNCTX),
                ShaderProperty("Image", "DensitySampler"),
                ShaderProperty("Image", "NormalSampler"),
                ShaderProperty("Value", "CloudLayerAnimScale3", 1.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "CloudLayerAnimScale2", 1.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "CloudLayerAnimScale1", 1.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "gRescaleUV3", 1.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "gRescaleUV2", 1.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "gRescaleUV1", 1.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "gUVOffset3", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gUVOffset2", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gUVOffset1", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gCameraPos", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gCloudViewProj", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gUVOffset", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gWrapLighting_MSAARef", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "gScaleDiffuseFillAmbient", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "gPiercingLightPower_Strength_NormalStrength_Thickness", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "gScatterG_GSquared_PhaseMult_Scale", -0.75, 0.5625, 2.1, 1.0),
                ShaderProperty("Value", "gDensityShiftScale", 0.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "gBounceColor", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gAmbientColor", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gCloudColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "gSunColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "gSunDirection", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gWestColor", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gEastMinusWestColor", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gSkyColor", 0.0, 0.0, 0.0, 0.0)]

clouds_fogsps = [
                ShaderProperty("Layout", PNCTX),
                ShaderProperty("Image", "DensitySampler"),
                ShaderProperty("Image", "NormalSampler"),
                ShaderProperty("Image", "DepthMapTexSampler"),
                ShaderProperty("Value", "CloudLayerAnimScale3", 1.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "CloudLayerAnimScale2", 1.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "CloudLayerAnimScale1", 1.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "gSoftParticleRange", 175.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gRescaleUV3", 1.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "gRescaleUV2", 1.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "gRescaleUV1", 1.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "gUVOffset3", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gUVOffset2", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gUVOffset1", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gCameraPos", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gCloudViewProj", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gUVOffset", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gNearFarQMult", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gWrapLighting_MSAARef", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "gScaleDiffuseFillAmbient", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "gPiercingLightPower_Strength_NormalStrength_Thickness", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "gDensityShiftScale", 0.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "gBounceColor", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gAmbientColor", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gCloudColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "gSunColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "gSunDirection", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gWestColor", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gEastMinusWestColor", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gSkyColor", 0.0, 0.0, 0.0, 0.0)]

clouds_softsps = [
                ShaderProperty("Layout", PNCTX),
                ShaderProperty("Image", "DensitySampler"),
                ShaderProperty("Image", "NormalSampler"),
                ShaderProperty("Image", "DepthMapTexSampler"),
                ShaderProperty("Value", "CloudLayerAnimScale3", 1.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "CloudLayerAnimScale2", 1.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "CloudLayerAnimScale1", 1.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "gSoftParticleRange", 175.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gRescaleUV3", 1.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "gRescaleUV2", 1.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "gRescaleUV1", 1.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "gUVOffset3", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gUVOffset2", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gUVOffset1", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gCameraPos", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gCloudViewProj", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gUVOffset", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gNearFarQMult", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gWrapLighting_MSAARef", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "gScaleDiffuseFillAmbient", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "gPiercingLightPower_Strength_NormalStrength_Thickness", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "gScatterG_GSquared_PhaseMult_Scale", -0.75, 0.5625, 2.1, 1.0),
                ShaderProperty("Value", "gDensityShiftScale", 0.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "gBounceColor", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gAmbientColor", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gCloudColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "gSunColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "gSunDirection", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gWestColor", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gEastMinusWestColor", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gSkyColor", 0.0, 0.0, 0.0, 0.0)]

cpv_onlysps = [
                ShaderProperty("Layout", PNC),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0)]

cutout_fencesps = [
                ShaderProperty("Layout", PNCT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0)]

cutout_fence_normalsps = [
                ShaderProperty("Layout", PNCTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

cutout_hardsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0)]

decalsps = [
                ShaderProperty("Layout", PNCT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

decal_amb_onlysps = [
                ShaderProperty("Layout", PNCT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "AmbientDecalMask", 1.0, 0.0, 0.0, 0.0)]

decal_diff_only_umsps = [
                ShaderProperty("Layout", PBBCCT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "umGlobalOverrideParams", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "umGlobalParams", 0.025, 0.025, 1.0, 1.0)]

decal_dirtsps = [
                ShaderProperty("Layout", PNCT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DirtDecalMask", 1.0, 0.0, 0.0, 0.0)]

decal_emissivenight_onlysps = [
                ShaderProperty("Layout", PNCT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "EmissiveMultiplier", 1.0, 0.0, 0.0, 0.0)]

decal_emissive_onlysps = [
                ShaderProperty("Layout", PNCT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "EmissiveMultiplier", 1.0, 0.0, 0.0, 0.0)]

decal_gluesps = [
                ShaderProperty("Layout", PNCT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

decal_normal_onlysps = [
                ShaderProperty("Layout", PNCTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

decal_shadow_onlysps = [
                ShaderProperty("Layout", PNCTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0)]

decal_spec_onlysps = [
                ShaderProperty("Layout", PNCT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

decal_tntsps = [
                ShaderProperty("Layout", PNCT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "TintPaletteSampler"),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

custom_defaultsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

defaultsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

default_noedgesps = [
                ShaderProperty("Layout", PNCT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

gta_defaultsps = [
                ShaderProperty("Layout", PNCT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

alphasps = [
                ShaderProperty("Layout", PNCT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

cutoutsps = [
                ShaderProperty("Layout", PNCT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

default_detailsps = [
                ShaderProperty("Layout", PNCT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DetailSampler"),
                ShaderProperty("Value", "DetailSettings", 0.0, 0.0, 24.0, 24.0),
                ShaderProperty("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0)]

default_specsps = [
                ShaderProperty("Layout", PNCT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

spec_constsps = [
                ShaderProperty("Layout", PNCT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

default_terrain_wetsps = [
                ShaderProperty("Layout", PNCT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

default_tntsps = [
                ShaderProperty("Layout", PNCT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "TintPaletteSampler"),
                ShaderProperty("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

cutout_tntsps = [
                ShaderProperty("Layout", PNCT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "TintPaletteSampler"),
                ShaderProperty("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

default_umsps = [
                ShaderProperty("Layout", PNCCT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "umGlobalOverrideParams", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "umGlobalParams", 0.025, 0.025, 1.0, 1.0)]

cutout_umsps = [
                ShaderProperty("Layout", PNCCT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "umGlobalOverrideParams", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "umGlobalParams", 0.025, 0.025, 1.0, 1.0)]

distance_mapsps = [
                ShaderProperty("Layout", PNCTX),
                ShaderProperty("Image", "DistanceMapSampler"),
                ShaderProperty("Value", "FillColor", 0.0, 0.0, 1.0, 0.0)]

emissivesps = [
                ShaderProperty("Layout", PNCT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "EmissiveMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

emissive_alphasps = [
                ShaderProperty("Layout", PNCT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "EmissiveMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

emissivenightsps = [
                ShaderProperty("Layout", PNCT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "EmissiveMultiplier", 1.0, 0.0, 0.0, 0.0)]

emissivenight_alphasps = [
                ShaderProperty("Layout", PNCT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "EmissiveMultiplier", 1.0, 0.0, 0.0, 0.0)]

emissivenight_geomnightonlysps = [
                ShaderProperty("Layout", PNCT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "EmissiveMultiplier", 1.0, 0.0, 0.0, 0.0)]

emissivestrongsps = [
                ShaderProperty("Layout", PNCT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "EmissiveMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

emissivestrong_alphasps = [
                ShaderProperty("Layout", PNCT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "EmissiveMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

emissive_additive_alphasps = [
                ShaderProperty("Layout", PNCT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "EmissiveMultiplier", 1.0, 0.0, 0.0, 0.0)]

emissive_additive_uv_alphasps = [
                ShaderProperty("Layout", PNCT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "EmissiveMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

emissive_clipsps = [
                ShaderProperty("Layout", PNCT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "EmissiveMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

emissive_speclumsps = [
                ShaderProperty("Layout", PNCT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "EmissiveMultiplier", 1.0, 0.0, 0.0, 0.0)]

emissive_tntsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "TintPaletteSampler"),
                ShaderProperty("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "EmissiveMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

emissive_alpha_tntsps = [
                ShaderProperty("Layout", PNCT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "TintPaletteSampler"),
                ShaderProperty("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "EmissiveMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

glasssps = [
                ShaderProperty("Layout", PNCTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "EnvironmentSampler"),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

glass_breakablesps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "DecalTint", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "CrackDecalBumpAlphaThreshold", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "CrackDecalBumpAmount", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "CrackEdgeBumpAmount", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "CrackDecalBumpTileScale", 1.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "CrackEdgeBumpTileScale", 1.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "BrokenSpecularColor", 0.46, 0.6117647, 0.6117647, 1.0),
                ShaderProperty("Value", "BrokenDiffuseColor", 0.46, 0.6117647, 0.6117647, 0.5686275),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Layout", PNCTTX)]

glass_breakable_screendooralphasps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "DecalTint", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "CrackDecalBumpAlphaThreshold", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "CrackDecalBumpAmount", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "CrackEdgeBumpAmount", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "CrackDecalBumpTileScale", 1.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "CrackEdgeBumpTileScale", 1.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "BrokenSpecularColor", 0.46, 0.6117647, 0.6117647, 1.0),
                ShaderProperty("Value", "BrokenDiffuseColor", 0.46, 0.6117647, 0.6117647, 0.5686275),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

glass_displacementsps = [
                ShaderProperty("Layout", PNCTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Image", "EnvironmentSampler"),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "displParams", 16.0, 16.0, 15.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

glass_emissivesps = [
                ShaderProperty("Layout", PNCTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "EnvironmentSampler"),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "EmissiveMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

glass_emissive_alphasps = [
                ShaderProperty("Layout", PNCTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "EnvironmentSampler"),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "EmissiveMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

glass_emissivenightsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "EnvironmentSampler"),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "EmissiveMultiplier", 1.0, 0.0, 0.0, 0.0)]

glass_emissivenight_alphasps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "EnvironmentSampler"),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "EmissiveMultiplier", 1.0, 0.0, 0.0, 0.0)]

glass_envsps = [
                ShaderProperty("Layout", PNCTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

glass_normal_spec_reflectsps = [
                ShaderProperty("Layout", PNCTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Image", "EnvironmentSampler"),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

glass_pvsps = [
                ShaderProperty("Layout", PNCTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Value", "DecalTint", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "CrackDecalBumpAlphaThreshold", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "CrackDecalBumpAmount", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "CrackEdgeBumpAmount", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "CrackDecalBumpTileScale", 1.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "CrackEdgeBumpTileScale", 1.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "BrokenSpecularColor", 0.46, 0.6117647, 0.6117647, 1.0),
                ShaderProperty("Value", "BrokenDiffuseColor", 0.46, 0.6117647, 0.6117647, 0.5686275),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

glass_pv_envsps = [
                ShaderProperty("Layout", PNCTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Value", "DecalTint", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "CrackDecalBumpAlphaThreshold", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "CrackDecalBumpAmount", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "CrackEdgeBumpAmount", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "CrackDecalBumpTileScale", 1.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "CrackEdgeBumpTileScale", 1.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "BrokenSpecularColor", 0.46, 0.6117647, 0.6117647, 1.0),
                ShaderProperty("Value", "BrokenDiffuseColor", 0.46, 0.6117647, 0.6117647, 0.5686275),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

glass_reflectsps = [
                ShaderProperty("Layout", PNCT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "EnvironmentSampler"),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

glass_specsps = [
                ShaderProperty("Layout", PNCT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

grasssps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "TextureGrassSampler"),
                ShaderProperty("Value", "gAlphaToCoverageScale", 1.3, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ShadowFalloff", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "AlphaTest", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "AlphaScale", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "_fakedGrassNormal", 0.0, 0.0, 1.0, 1.0),
                ShaderProperty("Value", "uMovementParams", 0.05, 0.05, 0.2125, 0.2125),
                ShaderProperty("Value", "FadeAlphaLOD2DistFar0", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "FadeAlphaLOD2Dist", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "FadeAlphaLOD1Dist", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "FadeAlphaDistUmTimer", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "_vecVehColl3R", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "_vecVehColl3M", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "_vecVehColl3B", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "_vecVehColl2R", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "_vecVehColl2M", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "_vecVehColl2B", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "_vecVehColl1R", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "_vecVehColl1M", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "_vecVehColl1B", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "_vecVehColl0R", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "_vecVehColl0M", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "_vecVehColl0B", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "_vecCollParams", 0.5625, 1.777778, 0.0, 0.0),
                ShaderProperty("Value", "_dimensionLOD2", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "vecPlayerPos", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "vecCameraPos", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "GroundColor"),
                ShaderProperty("Value", "PlantColor", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "matGrassTransform", 0.0, 0.0, 0.0, 0.0)]

grass_batchsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Value", "gLodFadeTileScale", 1.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "gLodFadePower", 1.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "gLodFadeRange", 0.05, 0.05, 0.0, 0.0),
                ShaderProperty("Value", "gLodFadeStartDist", -1.0, -1.0, 0.0, 0.0),
                ShaderProperty("Value", "gAlphaToCoverageScale", 1.3, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gAlphaTest", 0.25, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gWindBendScaleVar", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gWindBendingGlobals", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gScaleRange", 1.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "_fakedGrassNormal", 0.0, 0.0, 1.0, 1.0),
                ShaderProperty("Value", "uMovementParams", 0.05, 0.05, 0.2125, 0.2125),
                ShaderProperty("Value", "FadeAlphaDistUmTimer", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "_vecVehColl3R", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "_vecVehColl3M", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "_vecVehColl3B", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "_vecVehColl2R", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "_vecVehColl2M", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "_vecVehColl2B", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "_vecVehColl1R", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "_vecVehColl1M", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "_vecVehColl1B", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "_vecVehColl0R", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "_vecVehColl0M", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "_vecVehColl0B", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "_vecCollParams", 0.5625, 1.777778, 0.0, 0.0),
                ShaderProperty("Value", "vecPlayerPos", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "vecBatchAabbDelta", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "vecBatchAabbMin", 0.0, 0.0, 0.0, 0.0)]

grass_fursps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Image", "ComboHeightSamplerFur01"),
                ShaderProperty("Image", "ComboHeightSamplerFur23"),
                ShaderProperty("Image", "ComboHeightSamplerFur45"),
                ShaderProperty("Image", "ComboHeightSamplerFur67"),
                ShaderProperty("Image", "StippleSampler"),
                ShaderProperty("Value", "FurShadow47", 0.7843137, 0.8627451, 0.9333333, 1.0),
                ShaderProperty("Value", "FurShadow03", 0.3529412, 0.4627451, 0.5803922, 0.6588235),
                ShaderProperty("Value", "FurAlphaClip47", 0.07843138, 0.09803922, 0.1176471, 0.1333333),
                ShaderProperty("Value", "FurAlphaClip03", 0.0, 0.03921569, 0.03921569, 0.05882353),
                ShaderProperty("Value", "FurAlphaDistance", 10.0, 25.0, 0.0, 0.0),
                ShaderProperty("Value", "FurUvScales", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "FurLayerParams", 0.008, 0.0, 0.0, 1.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Layout", PNCT)]

grass_fur_masksps = [
                ShaderProperty("Layout", PNCTTTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Image", "ComboHeightSamplerFur01"),
                ShaderProperty("Image", "ComboHeightSamplerFur23"),
                ShaderProperty("Image", "ComboHeightSamplerFur45"),
                ShaderProperty("Image", "ComboHeightSamplerFur67"),
                ShaderProperty("Image", "FurMaskSampler"),
                ShaderProperty("Image", "DiffuseHfSampler"),
                ShaderProperty("Image", "StippleSampler"),
                ShaderProperty("Value", "FurShadow47", 0.7843137, 0.8627451, 0.9333333, 1.0),
                ShaderProperty("Value", "FurShadow03", 0.3529412, 0.4627451, 0.5803922, 0.6588235),
                ShaderProperty("Value", "FurAlphaClip47", 0.07843138, 0.09803922, 0.1176471, 0.1333333),
                ShaderProperty("Value", "FurAlphaClip03", 0.0, 0.03921569, 0.03921569, 0.05882353),
                ShaderProperty("Value", "FurAlphaDistance", 10.0, 25.0, 0.0, 0.0),
                ShaderProperty("Value", "FurUvScales", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "FurLayerParams", 0.008, 0.0, 0.0, 1.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

minimapsps = [
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0)]

mirror_cracksps = [
                ShaderProperty("Layout", PNCTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "gMirrorCrackSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "gMirrorBounds", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gMirrorCrackAmount", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0)]

mirror_decalsps = [
                ShaderProperty("Layout", PNCTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Value", "gMirrorBounds", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "gMirrorDistortionAmount", 32.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

mirror_defaultsps = [
                ShaderProperty("Layout", PNCTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "gMirrorBounds", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0)]

gta_normalsps = [
                ShaderProperty("Layout", PNCTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

normalsps = [
                ShaderProperty("Layout", PNCTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

normal_alphasps = [
                ShaderProperty("Layout", PNCTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

water_decalsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

normal_cutoutsps = [
                ShaderProperty("Layout", PNCTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

normal_screendooralphasps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

normal_cubemap_reflectsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "EnvironmentSampler"),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Layout", PNCTX)]

normal_decalsps = [
                ShaderProperty("Layout", PNCTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

normal_decal_pxmsps = [
                ShaderProperty("Layout", PNCTTTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "HeightSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ParallaxSelfShadowAmount", 0.95, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightBias", 0.015, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightScale", 0.03, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

normal_decal_pxm_tntsps = [
                ShaderProperty("Layout", PNCTTTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "TintPaletteSampler"),
                ShaderProperty("Image", "HeightSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ParallaxSelfShadowAmount", 0.95, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightBias", 0.015, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightScale", 0.03, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

normal_decal_tntsps = [
                ShaderProperty("Layout", PNCTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "TintPaletteSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

normal_detailsps = [
                ShaderProperty("Layout", PNCTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DetailSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Value", "DetailSettings", 0.0, 0.0, 24.0, 24.0),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

normal_detail_dpmsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DetailSampler"),
                ShaderProperty("Image", "HeightSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Value", "DetailSettings", 0.0, 0.0, 24.0, 24.0),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightBias", -0.5, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightScale", 0.4, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "TessellationMultiplier", 1.0, 0.0, 0.0, 0.0)]

normal_diffspecsps = [
                ShaderProperty("Layout", PNCTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecDesaturateExponent", 0.3, 0.6, 0.1, 0.0625),
                ShaderProperty("Value", "SpecDesaturateIntensity", 0.3, 0.6, 0.1, 0.0625),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

normal_diffspec_detailsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DetailSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Value", "DetailSettings", 0.0, 0.0, 24.0, 24.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecDesaturateExponent", 0.3, 0.6, 0.1, 0.0625),
                ShaderProperty("Value", "SpecDesaturateIntensity", 0.3, 0.6, 0.1, 0.0625),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Layout", PNCTX)]

normal_diffspec_detail_dpmsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DetailSampler"),
                ShaderProperty("Image", "HeightSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Value", "DetailSettings", 0.0, 0.0, 24.0, 24.0),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightBias", -0.5, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightScale", 0.4, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecDesaturateExponent", 0.3, 0.6, 0.1, 0.0625),
                ShaderProperty("Value", "SpecDesaturateIntensity", 0.3, 0.6, 0.1, 0.0625),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "TessellationMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Layout", PNCT4T5TX)]

normal_diffspec_detail_dpm_tntsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "TintPaletteSampler"),
                ShaderProperty("Image", "DetailSampler"),
                ShaderProperty("Image", "HeightSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Value", "DetailSettings", 0.0, 0.0, 24.0, 24.0),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightBias", -0.5, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightScale", 0.4, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecDesaturateExponent", 0.3, 0.6, 0.1, 0.0625),
                ShaderProperty("Value", "SpecDesaturateIntensity", 0.3, 0.6, 0.1, 0.0625),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "TessellationMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

normal_diffspec_detail_tntsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "TintPaletteSampler"),
                ShaderProperty("Image", "DetailSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Value", "DetailSettings", 0.0, 0.0, 24.0, 24.0),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecDesaturateExponent", 0.3, 0.6, 0.1, 0.0625),
                ShaderProperty("Value", "SpecDesaturateIntensity", 0.3, 0.6, 0.1, 0.0625),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

normal_diffspec_tntsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "TintPaletteSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecDesaturateExponent", 0.3, 0.6, 0.1, 0.0625),
                ShaderProperty("Value", "SpecDesaturateIntensity", 0.3, 0.6, 0.1, 0.0625),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

normal_pxmsps = [
                ShaderProperty("Layout", PNCTTTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "HeightSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ParallaxSelfShadowAmount", 0.95, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightBias", 0.015, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightScale", 0.03, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

normal_pxm_tntsps = [
                ShaderProperty("Layout", PNCTTTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "TintPaletteSampler"),
                ShaderProperty("Image", "HeightSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ParallaxSelfShadowAmount", 0.95, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightBias", 0.015, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightScale", 0.03, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

normal_tnt_pxmsps = [
                ShaderProperty("Layout", PNCTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "TintPaletteSampler"),
                ShaderProperty("Image", "HeightSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ParallaxSelfShadowAmount", 0.95, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightBias", 0.015, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightScale", 0.03, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

normal_reflectsps = [
                ShaderProperty("Layout", PNCTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "EnvironmentSampler"),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0)]

normal_reflect_alphasps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "EnvironmentSampler"),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Layout", PNCTX)]

normal_reflect_screendooralphasps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "EnvironmentSampler"),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0)]

normal_reflect_decalsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "EnvironmentSampler"),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0)]

normal_specsps = [
                ShaderProperty("Layout", PNCTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

normal_spec_alphasps = [
                ShaderProperty("Layout", PNCTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

normal_spec_cutoutsps = [
                ShaderProperty("Layout", PNCTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

normal_spec_screendooralphasps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

normal_spec_batchsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "gLodFadeTileScale", 1.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "gLodFadePower", 1.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "gLodFadeRange", 0.05, 0.05, 0.0, 0.0),
                ShaderProperty("Value", "gLodFadeStartDist", -1.0, -1.0, 0.0, 0.0),
                ShaderProperty("Value", "vecBatchAabbMin", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

normal_spec_cubemap_reflectsps = [
                ShaderProperty("Layout", PNCTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Image", "EnvironmentSampler"),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

normal_spec_decalsps = [
                ShaderProperty("Layout", PNCTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

normal_spec_decal_detailsps = [
                ShaderProperty("Layout", PNCTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DetailSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "DetailSettings", 0.0, 0.0, 24.0, 24.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

normal_spec_decal_nopuddlesps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

normal_spec_decal_pxmsps = [
                ShaderProperty("Layout", PNCTTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "HeightSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ParallaxSelfShadowAmount", 0.95, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightBias", 0.015, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightScale", 0.03, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

normal_spec_decal_tntsps = [
                ShaderProperty("Layout", PNCTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "TintPaletteSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

normal_spec_detailsps = [
                ShaderProperty("Layout", PNCTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DetailSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "DetailSettings", 0.0, 0.0, 24.0, 24.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

normal_spec_detail_dpmsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DetailSampler"),
                ShaderProperty("Image", "HeightSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "DetailSettings", 0.0, 0.0, 24.0, 24.0),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightBias", -0.5, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightScale", 0.4, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "TessellationMultiplier", 1.0, 0.0, 0.0, 0.0)]

normal_spec_detail_dpm_tntsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "TintPaletteSampler"),
                ShaderProperty("Image", "DetailSampler"),
                ShaderProperty("Image", "HeightSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "DetailSettings", 0.0, 0.0, 24.0, 24.0),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightBias", -0.5, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightScale", 0.4, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "TessellationMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

normal_spec_detail_dpm_vertdecal_tntsps = [
                ShaderProperty("Layout", PNCTT4T5TX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "TintPaletteSampler"),
                ShaderProperty("Image", "DetailSampler"),
                ShaderProperty("Image", "HeightSampler"),
                ShaderProperty("Image", "DiffuseSampler2"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "DetailSettings", 0.0, 0.0, 24.0, 24.0),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightBias", -0.5, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightScale", 0.4, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "TessellationMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

normal_spec_detail_tntsps = [
                ShaderProperty("Layout", PNCTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "TintPaletteSampler"),
                ShaderProperty("Image", "DetailSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "DetailSettings", 0.0, 0.0, 24.0, 24.0),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

normal_spec_dpmsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "HeightSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightBias", -0.5, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightScale", 0.4, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "TessellationMultiplier", 1.0, 0.0, 0.0, 0.0)]

normal_spec_emissivesps = [
                ShaderProperty("Layout", PNCTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "EmissiveMultiplier", 1.0, 0.0, 0.0, 0.0)]

normal_spec_pxmsps = [
                ShaderProperty("Layout", PNCTTTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "HeightSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ParallaxSelfShadowAmount", 0.95, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightBias", 0.015, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightScale", 0.03, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

normal_spec_pxm_tntsps = [
                ShaderProperty("Layout", PNCTTTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "TintPaletteSampler"),
                ShaderProperty("Image", "HeightSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ParallaxSelfShadowAmount", 0.95, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightBias", 0.015, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightScale", 0.03, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

normal_spec_tnt_pxmsps = [
                ShaderProperty("Layout", PNCTTTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "TintPaletteSampler"),
                ShaderProperty("Image", "HeightSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ParallaxSelfShadowAmount", 0.95, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightBias", 0.015, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightScale", 0.03, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

normal_spec_reflectsps = [
                ShaderProperty("Layout", PNCTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Image", "EnvironmentSampler"),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

normal_spec_reflect_alphasps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Image", "EnvironmentSampler"),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

normal_spec_reflect_decalsps = [
                ShaderProperty("Layout", PNCTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Image", "EnvironmentSampler"),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

normal_spec_reflect_emissivenightsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "EmissiveMultiplier", 1.0, 0.0, 0.0, 0.0)]

normal_spec_reflect_emissivenight_alphasps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "EmissiveMultiplier", 1.0, 0.0, 0.0, 0.0)]

normal_spec_tntsps = [
                ShaderProperty("Layout", PNCTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "TintPaletteSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

normal_spec_cutout_tntsps = [
                ShaderProperty("Layout", PNCTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "TintPaletteSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

normal_spec_umsps = [
                ShaderProperty("Layout", PNCCTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "umGlobalOverrideParams", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "umGlobalParams", 0.025, 0.025, 1.0, 1.0)]

normal_spec_wrinklesps = [
                ShaderProperty("Layout", PBBNCTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "WrinkleMaskSampler_0"),
                ShaderProperty("Image", "WrinkleMaskSampler_1"),
                ShaderProperty("Image", "WrinkleMaskSampler_2"),
                ShaderProperty("Image", "WrinkleMaskSampler_3"),
                ShaderProperty("Image", "WrinkleSampler_A"),
                ShaderProperty("Image", "WrinkleSampler_B"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WrinkleMaskStrengths3", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WrinkleMaskStrengths2", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WrinkleMaskStrengths1", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WrinkleMaskStrengths0", 0.0, 0.0, 0.0, 0.0)]

normal_terrain_wetsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

normal_tntsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "TintPaletteSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

normal_tnt_alphasps = [
                ShaderProperty("Layout", PNCTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "TintPaletteSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

normal_cutout_tntsps = [
                ShaderProperty("Layout", PNCTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "TintPaletteSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

normal_umsps = [
                ShaderProperty("Layout", PNCCTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "umGlobalOverrideParams", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "umGlobalParams", 0.025, 0.025, 1.0, 1.0)]

normal_cutout_umsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "umGlobalOverrideParams", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "umGlobalParams", 0.025, 0.025, 1.0, 1.0)]

normal_um_tntsps = [
                ShaderProperty("Layout", PBBNCTTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "TintPaletteSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "umGlobalOverrideParams", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "umGlobalParams", 0.025, 0.025, 1.0, 1.0)]

parallaxsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ParallaxScaleBias", 0.03, 0.0, 0.0, 0.0)]

parallax_specmapsps = [
                ShaderProperty("Layout", PNCTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ParallaxScaleBias", 0.03, 0.0, 0.0, 0.0)]

pedsps = [
                ShaderProperty("Layout", PBBNCCTTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "VolumeSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "umGlobalParams", 0.0025, 0.0025, 7.0, 7.0),
                ShaderProperty("Value", "envEffFatThickness", 25.0, 25.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DetailSettings", 0.0, 0.0, 24.0, 0.0),
                ShaderProperty("Value", "StubbleControl", 2.0, 0.6, 0.0, 0.0)]

ped_alphasps = [
                ShaderProperty("Layout", PBBNCCTTX),
                ShaderProperty("RenderBucket", 1),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffFatThickness", 25.0, 25.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DetailSettings", 0.0, 0.0, 24.0, 0.0),
                ShaderProperty("Value", "StubbleControl", 2.0, 0.6, 0.0, 0.0)]

ped_clothsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "VolumeSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "umGlobalParams", 0.0025, 0.0025, 7.0, 7.0),
                ShaderProperty("Value", "envEffFatThickness", 25.0, 25.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DetailSettings", 0.0, 0.0, 24.0, 0.0),
                ShaderProperty("Value", "StubbleControl", 2.0, 0.6, 0.0, 0.0)]

ped_cloth_enveffsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "VolumeSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Image", "SnowSampler"),
                ShaderProperty("Value", "umGlobalParams", 0.0025, 0.0025, 7.0, 7.0),
                ShaderProperty("Value", "envEffFatThickness", 25.0, 25.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DetailSettings", 0.0, 0.0, 24.0, 0.0),
                ShaderProperty("Value", "StubbleControl", 2.0, 0.6, 0.0, 0.0)]

ped_decalsps = [
                ShaderProperty("RenderBucket", 2),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "VolumeSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffFatThickness", 25.0, 25.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DetailSettings", 0.0, 0.0, 24.0, 0.0),
                ShaderProperty("Value", "StubbleControl", 2.0, 0.6, 0.0, 0.0)]

ped_decal_decorationsps = [
                ShaderProperty("RenderBucket", 2),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "VolumeSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "umGlobalParams", 0.0025, 0.0025, 7.0, 7.0),
                ShaderProperty("Value", "envEffFatThickness", 25.0, 25.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DetailSettings", 0.0, 0.0, 24.0, 0.0),
                ShaderProperty("Value", "StubbleControl", 2.0, 0.6, 0.0, 0.0)]

ped_decal_expensivesps = [
                ShaderProperty("Layout", PBBNCCTTX),
                ShaderProperty("RenderBucket", 2),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "VolumeSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffFatThickness", 25.0, 25.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DetailSettings", 0.0, 0.0, 24.0, 0.0),
                ShaderProperty("Value", "StubbleControl", 2.0, 0.6, 0.0, 0.0)]

ped_decal_nodiffsps = [
                ShaderProperty("RenderBucket", 2),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "VolumeSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffFatThickness", 25.0, 25.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DetailSettings", 0.0, 0.0, 24.0, 0.0),
                ShaderProperty("Value", "StubbleControl", 2.0, 0.6, 0.0, 0.0)]

ped_defaultsps = [
                ShaderProperty("Layout", PBBNCCT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "VolumeSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffFatThickness", 25.0, 25.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DetailSettings", 0.0, 0.0, 24.0, 0.0),
                ShaderProperty("Value", "StubbleControl", 2.0, 0.6, 0.0, 0.0)]

ped_default_cutoutsps = [
                ShaderProperty("RenderBucket", 3),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "VolumeSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffFatThickness", 25.0, 25.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DetailSettings", 0.0, 0.0, 24.0, 0.0),
                ShaderProperty("Value", "StubbleControl", 2.0, 0.6, 0.0, 0.0)]

ped_default_clothsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "VolumeSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffFatThickness", 25.0, 25.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DetailSettings", 0.0, 0.0, 24.0, 0.0),
                ShaderProperty("Value", "StubbleControl", 2.0, 0.6, 0.0, 0.0)]

ped_default_enveffsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "VolumeSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Image", "SnowSampler"),
                ShaderProperty("Value", "envEffFatThickness", 25.0, 25.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DetailSettings", 0.0, 0.0, 24.0, 0.0),
                ShaderProperty("Value", "StubbleControl", 2.0, 0.6, 0.0, 0.0)]

ped_default_mpsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "VolumeSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffFatThickness", 25.0, 25.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DetailSettings", 0.0, 0.0, 24.0, 0.0),
                ShaderProperty("Value", "StubbleControl", 2.0, 0.6, 0.0, 0.0)]

ped_default_palettesps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "VolumeSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffFatThickness", 25.0, 25.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DetailSettings", 0.0, 0.0, 24.0, 0.0),
                ShaderProperty("Value", "StubbleControl", 2.0, 0.6, 0.0, 0.0)]

ped_emissivesps = [
                ShaderProperty("Layout", PBBNCCTTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "VolumeSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "umGlobalParams", 0.0025, 0.0025, 7.0, 7.0),
                ShaderProperty("Value", "envEffFatThickness", 25.0, 25.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "EmissiveMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DetailSettings", 0.0, 0.0, 24.0, 0.0),
                ShaderProperty("Value", "StubbleControl", 2.0, 0.6, 0.0, 0.0)]

ped_enveffsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "VolumeSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Image", "SnowSampler"),
                ShaderProperty("Value", "umGlobalParams", 0.0025, 0.0025, 7.0, 7.0),
                ShaderProperty("Value", "envEffFatThickness", 25.0, 25.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DetailSettings", 0.0, 0.0, 24.0, 0.0),
                ShaderProperty("Value", "StubbleControl", 2.0, 0.6, 0.0, 0.0)]

ped_fursps = [
                ShaderProperty("Layout", PBBNCCTX),
                ShaderProperty("RenderBucket", 3),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "NoiseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffFatThickness", 25.0, 25.0, 0.0, 0.0),
                ShaderProperty("Value", "FurBendParams", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "FurGlobalParams", 0.0, 0.0, 0.00392157, 0.0),
                ShaderProperty("Value", "FurAttenCoef", 1.21, -0.22, 0.0, 0.0),
                ShaderProperty("Value", "FurAOBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "FurStiffness", 0.75, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "FurSelfShadowMin", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "FurNoiseUVScale", 2.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "FurLength", 0.5, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "FurMaxLayers", 10.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "FurMinLayers", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "OrderNumber", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DetailSettings", 0.0, 0.0, 24.0, 0.0),
                ShaderProperty("Value", "StubbleControl", 2.0, 0.6, 0.0, 0.0)]

ped_hair_cutout_alphasps = [
                ShaderProperty("Layout", PBBNCCTX),
                ShaderProperty("RenderBucket", 3),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "anisoNoiseSpecSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "umGlobalParams", 0.0025, 0.0025, 7.0, 7.0),
                ShaderProperty("Value", "AnisotropicAlphaBias", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffFatThickness", 25.0, 25.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularNoiseMapUVScaleFactor", 2.0, 1.0, 3.0, 1.0),
                ShaderProperty("Value", "AnisotropicSpecularColour", 0.1, 0.1, 0.1, 1.0),
                ShaderProperty("Value", "AnisotropicSpecularExponent", 16.0, 32.0, 0.0, 0.0),
                ShaderProperty("Value", "AnisotropicSpecularIntensity", 0.1, 0.15, 0.0, 0.0),
                ShaderProperty("Value", "DetailSettings", 0.0, 0.0, 24.0, 0.0),
                ShaderProperty("Value", "StubbleControl", 2.0, 0.6, 0.0, 0.0)]

ped_hair_spikedsps = [
                ShaderProperty("Layout", PBBNCCTX),
                ShaderProperty("RenderBucket", 3),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "anisoNoiseSpecSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "umGlobalParams", 0.0025, 0.0025, 7.0, 7.0),
                ShaderProperty("Value", "AnisotropicAlphaBias", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffFatThickness", 25.0, 25.0, 0.0, 0.0),
                ShaderProperty("Value", "OrderNumber", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularNoiseMapUVScaleFactor", 2.0, 1.0, 3.0, 1.0),
                ShaderProperty("Value", "AnisotropicSpecularColour", 0.1, 0.1, 0.1, 1.0),
                ShaderProperty("Value", "AnisotropicSpecularExponent", 16.0, 32.0, 0.0, 0.0),
                ShaderProperty("Value", "AnisotropicSpecularIntensity", 0.1, 0.15, 0.0, 0.0),
                ShaderProperty("Value", "DetailSettings", 0.0, 0.0, 24.0, 0.0),
                ShaderProperty("Value", "StubbleControl", 2.0, 0.6, 0.0, 0.0)]

ped_nopeddamagedecalssps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "VolumeSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "umGlobalParams", 0.0025, 0.0025, 7.0, 7.0),
                ShaderProperty("Value", "envEffFatThickness", 25.0, 25.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DetailSettings", 0.0, 0.0, 24.0, 0.0),
                ShaderProperty("Value", "StubbleControl", 2.0, 0.6, 0.0, 0.0)]

ped_palettesps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "VolumeSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "umGlobalParams", 0.0025, 0.0025, 7.0, 7.0),
                ShaderProperty("Value", "envEffFatThickness", 25.0, 25.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DetailSettings", 0.0, 0.0, 24.0, 0.0),
                ShaderProperty("Value", "StubbleControl", 2.0, 0.6, 0.0, 0.0)]

ped_wrinklesps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "VolumeSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Image", "WrinkleMaskSampler_0"),
                ShaderProperty("Image", "WrinkleMaskSampler_1"),
                ShaderProperty("Image", "WrinkleMaskSampler_2"),
                ShaderProperty("Image", "WrinkleMaskSampler_3"),
                ShaderProperty("Image", "WrinkleSampler_A"),
                ShaderProperty("Image", "WrinkleSampler_B"),
                ShaderProperty("Value", "umGlobalParams", 0.0025, 0.0025, 7.0, 7.0),
                ShaderProperty("Value", "envEffFatThickness", 25.0, 25.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DetailSettings", 0.0, 0.0, 24.0, 0.0),
                ShaderProperty("Value", "StubbleControl", 2.0, 0.6, 0.0, 0.0)]

ped_wrinkle_clothsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "VolumeSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Image", "WrinkleMaskSampler_0"),
                ShaderProperty("Image", "WrinkleMaskSampler_1"),
                ShaderProperty("Image", "WrinkleMaskSampler_2"),
                ShaderProperty("Image", "WrinkleMaskSampler_3"),
                ShaderProperty("Image", "WrinkleSampler_A"),
                ShaderProperty("Image", "WrinkleSampler_B"),
                ShaderProperty("Value", "umGlobalParams", 0.0025, 0.0025, 7.0, 7.0),
                ShaderProperty("Value", "envEffFatThickness", 25.0, 25.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DetailSettings", 0.0, 0.0, 24.0, 0.0),
                ShaderProperty("Value", "StubbleControl", 2.0, 0.6, 0.0, 0.0)]

ped_wrinkle_cloth_enveffsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "VolumeSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Image", "SnowSampler"),
                ShaderProperty("Image", "WrinkleMaskSampler_0"),
                ShaderProperty("Image", "WrinkleMaskSampler_1"),
                ShaderProperty("Image", "WrinkleMaskSampler_2"),
                ShaderProperty("Image", "WrinkleMaskSampler_3"),
                ShaderProperty("Image", "WrinkleSampler_A"),
                ShaderProperty("Image", "WrinkleSampler_B"),
                ShaderProperty("Value", "umGlobalParams", 0.0025, 0.0025, 7.0, 7.0),
                ShaderProperty("Value", "envEffFatThickness", 25.0, 25.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DetailSettings", 0.0, 0.0, 24.0, 0.0),
                ShaderProperty("Value", "StubbleControl", 2.0, 0.6, 0.0, 0.0)]

ped_wrinkle_cssps = [
                ShaderProperty("Layout", PBBNCCTTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "VolumeSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Image", "WrinkleMaskSampler_0"),
                ShaderProperty("Image", "WrinkleMaskSampler_1"),
                ShaderProperty("Image", "WrinkleMaskSampler_2"),
                ShaderProperty("Image", "WrinkleMaskSampler_3"),
                ShaderProperty("Image", "WrinkleMaskSampler_4"),
                ShaderProperty("Image", "WrinkleMaskSampler_5"),
                ShaderProperty("Image", "WrinkleSampler_A"),
                ShaderProperty("Image", "WrinkleSampler_B"),
                ShaderProperty("Value", "umGlobalParams", 0.0025, 0.0025, 7.0, 7.0),
                ShaderProperty("Value", "envEffFatThickness", 25.0, 25.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DetailSettings", 0.0, 0.0, 24.0, 0.0),
                ShaderProperty("Value", "StubbleControl", 2.0, 0.6, 0.0, 0.0)]

ped_wrinkle_enveffsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "VolumeSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Image", "SnowSampler"),
                ShaderProperty("Image", "WrinkleMaskSampler_0"),
                ShaderProperty("Image", "WrinkleMaskSampler_1"),
                ShaderProperty("Image", "WrinkleMaskSampler_2"),
                ShaderProperty("Image", "WrinkleMaskSampler_3"),
                ShaderProperty("Image", "WrinkleSampler_A"),
                ShaderProperty("Image", "WrinkleSampler_B"),
                ShaderProperty("Value", "umGlobalParams", 0.0025, 0.0025, 7.0, 7.0),
                ShaderProperty("Value", "envEffFatThickness", 25.0, 25.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DetailSettings", 0.0, 0.0, 24.0, 0.0),
                ShaderProperty("Value", "StubbleControl", 2.0, 0.6, 0.0, 0.0)
                ]

ptfx_modelsps = [
                ShaderProperty("Layout", PNCT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

gta_radarsps = [
                ShaderProperty("Layout", PCTT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Value", "ClippingPlane", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DiffuseCol", 1.0, 1.0, 1.0, 1.0)]

radarsps = [
                ShaderProperty("Layout", PCTT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Value", "ClippingPlane", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DiffuseCol", 1.0, 1.0, 1.0, 1.0)]

reflectsps = [
                ShaderProperty("Layout", PNCT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "EnvironmentSampler"),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0)]

gta_reflect_alphasps = [
                ShaderProperty("Layout", PNCT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "EnvironmentSampler"),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),]

reflect_alphasps = [
                ShaderProperty("Layout", PBBNCT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "EnvironmentSampler"),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0)]

reflect_decalsps = [
                ShaderProperty("Layout", PNCT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "EnvironmentSampler"),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0)]

sky_systemsps = [
                ShaderProperty("Image", "NoiseSampler"),
                ShaderProperty("Image", "PerlinSampler"),
                ShaderProperty("Image", "HighDetailSampler"),
                ShaderProperty("Image", "StarFieldSampler"),
                ShaderProperty("Image", "DitherSampler"),
                ShaderProperty("Image", "MoonSampler"),
                ShaderProperty("Value", "NoisePhase", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "NoiseDensityOffset", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "NoiseSoftness", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "NoiseThreshold", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "NoiseScale", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "NoiseFrequency", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "MoonColor", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "LunarCycle", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "MoonIntensity", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "MoonPosition", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "MoonDirection", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "StarfieldIntensity", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpeedConstants", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HorizonLevel", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "EffectsConstants", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SmallCloudColorHdr", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SmallCloudConstants", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "CloudConstants2", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "CloudConstants1", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "CloudDetailConstants", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "CloudShadowMinusBaseColourTimesShadowStrength", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "CloudMidColour", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "CloudBaseMinusMidColour", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SunPosition", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SunDirection", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SunConstants", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SunDiscColorHdr", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SunColorHdr", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SunColor", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HDRIntensity", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SkyPlaneParams", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SkyPlaneColor", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ZenithConstants", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ZenithTransitionColor", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ZenithColor", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "AzimuthTransitionPosition", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "AzimuthTransitionColor", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "AzimuthWestColor", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "AzimuthEastColor", 0.0, 0.0, 0.0, 0.0)]

gta_specsps = [
                ShaderProperty("Layout", PNCT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

specsps = [
                ShaderProperty("Layout", PNCT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

spec_alphasps = [
                ShaderProperty("Layout", PNCT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

spec_screendooralphasps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

spec_decalsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

spec_reflectsps = [
                ShaderProperty("Layout", PNCT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Image", "EnvironmentSampler"),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

spec_reflect_alphasps = [
                ShaderProperty("Layout", PNCT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Image", "EnvironmentSampler"),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

spec_reflect_decalsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Image", "EnvironmentSampler"),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

spec_tntsps = [
                ShaderProperty("Layout", PNCT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "TintPaletteSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

cutout_spec_tntsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "TintPaletteSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Layout", PNCT)]

spec_twiddle_tntsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "TintPaletteSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

terrain_cb_4lyrsps = [
                ShaderProperty("Image", "TextureSampler_layer0"),
                ShaderProperty("Image", "BumpSampler_layer0"),
                ShaderProperty("Image", "TextureSampler_layer1"),
                ShaderProperty("Image", "BumpSampler_layer1"),
                ShaderProperty("Image", "TextureSampler_layer2"),
                ShaderProperty("Image", "BumpSampler_layer2"),
                ShaderProperty("Image", "TextureSampler_layer3"),
                ShaderProperty("Image", "BumpSampler_layer3"),
                ShaderProperty("Value", "WetnessMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BumpSelfShadowAmount", 0.3, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 48.0, 0.0, 0.0, 0.0)]

terrain_cb_4lyr_2texsps = [
                ShaderProperty("Image", "TextureSampler_layer0"),
                ShaderProperty("Image", "BumpSampler_layer0"),
                ShaderProperty("Image", "TextureSampler_layer1"),
                ShaderProperty("Image", "BumpSampler_layer1"),
                ShaderProperty("Image", "TextureSampler_layer2"),
                ShaderProperty("Image", "BumpSampler_layer2"),
                ShaderProperty("Image", "TextureSampler_layer3"),
                ShaderProperty("Image", "BumpSampler_layer3"),
                ShaderProperty("Value", "WetnessMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BumpSelfShadowAmount", 0.3, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 48.0, 0.0, 0.0, 0.0)]

terrain_cb_w_4lyrsps = [
                ShaderProperty("Layout", PNCCTX),
                ShaderProperty("Image", "TextureSampler_layer0"),
                ShaderProperty("Image", "BumpSampler_layer0"),
                ShaderProperty("Image", "TextureSampler_layer1"),
                ShaderProperty("Image", "BumpSampler_layer1"),
                ShaderProperty("Image", "TextureSampler_layer2"),
                ShaderProperty("Image", "BumpSampler_layer2"),
                ShaderProperty("Image", "TextureSampler_layer3"),
                ShaderProperty("Image", "BumpSampler_layer3"),
                ShaderProperty("Value", "MaterialWetnessMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BumpSelfShadowAmount", 0.3, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 48.0, 0.0, 0.0, 0.0)]

terrain_cb_w_4lyr_2texsps = [
                ShaderProperty("Image", "TextureSampler_layer0"),
                ShaderProperty("Image", "BumpSampler_layer0"),
                ShaderProperty("Image", "TextureSampler_layer1"),
                ShaderProperty("Image", "BumpSampler_layer1"),
                ShaderProperty("Image", "TextureSampler_layer2"),
                ShaderProperty("Image", "BumpSampler_layer2"),
                ShaderProperty("Image", "TextureSampler_layer3"),
                ShaderProperty("Image", "BumpSampler_layer3"),
                ShaderProperty("Value", "MaterialWetnessMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BumpSelfShadowAmount", 0.3, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 48.0, 0.0, 0.0, 0.0),
                ShaderProperty("Layout", PNCCTTX)]

terrain_cb_w_4lyr_2tex_blendsps = [
                ShaderProperty("Image", "TextureSampler_layer0"),
                ShaderProperty("Image", "BumpSampler_layer0"),
                ShaderProperty("Image", "TextureSampler_layer1"),
                ShaderProperty("Image", "BumpSampler_layer1"),
                ShaderProperty("Image", "TextureSampler_layer2"),
                ShaderProperty("Image", "BumpSampler_layer2"),
                ShaderProperty("Image", "TextureSampler_layer3"),
                ShaderProperty("Image", "BumpSampler_layer3"),
                ShaderProperty("Image", "LookupSampler"),
                ShaderProperty("Value", "MaterialWetnessMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BumpSelfShadowAmount", 0.3, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 48.0, 0.0, 0.0, 0.0),
                ShaderProperty("Layout", PNCCTTX)]

terrain_cb_w_4lyr_2tex_blend_lodsps = [
                ShaderProperty("Image", "TextureSampler_layer0"),
                ShaderProperty("Image", "TextureSampler_layer1"),
                ShaderProperty("Image", "TextureSampler_layer2"),
                ShaderProperty("Image", "TextureSampler_layer3"),
                ShaderProperty("Image", "LookupSampler"),
                ShaderProperty("Value", "MaterialWetnessMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BumpSelfShadowAmount", 0.3, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 48.0, 0.0, 0.0, 0.0),
                ShaderProperty("Layout", PNCCTT)]

terrain_cb_w_4lyr_2tex_blend_pxmsps = [
                ShaderProperty("Layout", PNCCTTTX),
                ShaderProperty("Image", "TextureSampler_layer0"),
                ShaderProperty("Image", "BumpSampler_layer0"),
                ShaderProperty("Image", "HeightMapSamplerLayer0"),
                ShaderProperty("Image", "TextureSampler_layer1"),
                ShaderProperty("Image", "BumpSampler_layer1"),
                ShaderProperty("Image", "HeightMapSamplerLayer1"),
                ShaderProperty("Image", "TextureSampler_layer2"),
                ShaderProperty("Image", "BumpSampler_layer2"),
                ShaderProperty("Image", "HeightMapSamplerLayer2"),
                ShaderProperty("Image", "TextureSampler_layer3"),
                ShaderProperty("Image", "BumpSampler_layer3"),
                ShaderProperty("Image", "HeightMapSamplerLayer3"),
                ShaderProperty("Image", "LookupSampler"),
                ShaderProperty("Value", "MaterialWetnessMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BumpSelfShadowAmount", 0.3, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightBias3", 0.015, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightScale3", 0.03, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightBias2", 0.015, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightScale2", 0.03, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightBias1", 0.015, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightScale1", 0.03, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightBias0", 0.015, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightScale0", 0.03, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ParallaxSelfShadowAmount", 0.95, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 48.0, 0.0, 0.0, 0.0)]

terrain_cb_w_4lyr_2tex_blend_pxm_spmsps = [
                ShaderProperty("Layout", PNCCTTTX),
                ShaderProperty("Image", "TextureSampler_layer0"),
                ShaderProperty("Image", "BumpSampler_layer0"),
                ShaderProperty("Image", "HeightMapSamplerLayer0"),
                ShaderProperty("Image", "TextureSampler_layer1"),
                ShaderProperty("Image", "BumpSampler_layer1"),
                ShaderProperty("Image", "HeightMapSamplerLayer1"),
                ShaderProperty("Image", "TextureSampler_layer2"),
                ShaderProperty("Image", "BumpSampler_layer2"),
                ShaderProperty("Image", "HeightMapSamplerLayer2"),
                ShaderProperty("Image", "TextureSampler_layer3"),
                ShaderProperty("Image", "BumpSampler_layer3"),
                ShaderProperty("Image", "HeightMapSamplerLayer3"),
                ShaderProperty("Image", "LookupSampler"),
                ShaderProperty("Value", "MaterialWetnessMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BumpSelfShadowAmount", 0.3, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightBias3", 0.015, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightScale3", 0.03, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightBias2", 0.015, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightScale2", 0.03, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightBias1", 0.015, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightScale1", 0.03, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightBias0", 0.015, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightScale0", 0.03, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ParallaxSelfShadowAmount", 0.95, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecIntensityAdjust", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMultSpecMap", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecFalloffAdjust", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMultSpecMap", 48.0, 0.0, 0.0, 0.0)]

terrain_cb_w_4lyr_2tex_pxmsps = [
                ShaderProperty("Image", "TextureSampler_layer0"),
                ShaderProperty("Image", "BumpSampler_layer0"),
                ShaderProperty("Image", "HeightMapSamplerLayer0"),
                ShaderProperty("Image", "TextureSampler_layer1"),
                ShaderProperty("Image", "BumpSampler_layer1"),
                ShaderProperty("Image", "HeightMapSamplerLayer1"),
                ShaderProperty("Image", "TextureSampler_layer2"),
                ShaderProperty("Image", "BumpSampler_layer2"),
                ShaderProperty("Image", "HeightMapSamplerLayer2"),
                ShaderProperty("Image", "TextureSampler_layer3"),
                ShaderProperty("Image", "BumpSampler_layer3"),
                ShaderProperty("Image", "HeightMapSamplerLayer3"),
                ShaderProperty("Value", "MaterialWetnessMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BumpSelfShadowAmount", 0.3, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightBias3", 0.015, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightScale3", 0.03, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightBias2", 0.015, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightScale2", 0.03, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightBias1", 0.015, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightScale1", 0.03, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightBias0", 0.015, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightScale0", 0.03, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ParallaxSelfShadowAmount", 0.95, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 48.0, 0.0, 0.0, 0.0)]

terrain_cb_w_4lyr_cmsps = [
                ShaderProperty("Image", "TextureSampler_layer0"),
                ShaderProperty("Image", "BumpSampler_layer0"),
                ShaderProperty("Image", "TextureSampler_layer1"),
                ShaderProperty("Image", "BumpSampler_layer1"),
                ShaderProperty("Image", "TextureSampler_layer2"),
                ShaderProperty("Image", "BumpSampler_layer2"),
                ShaderProperty("Image", "TextureSampler_layer3"),
                ShaderProperty("Image", "BumpSampler_layer3"),
                ShaderProperty("Image", "LookupSampler"),
                ShaderProperty("Value", "MaterialWetnessMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BumpSelfShadowAmount", 0.3, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 48.0, 0.0, 0.0, 0.0)]

terrain_cb_w_4lyr_cm_pxmsps = [
                ShaderProperty("Image", "TextureSampler_layer0"),
                ShaderProperty("Image", "BumpSampler_layer0"),
                ShaderProperty("Image", "HeightMapSamplerLayer0"),
                ShaderProperty("Image", "TextureSampler_layer1"),
                ShaderProperty("Image", "BumpSampler_layer1"),
                ShaderProperty("Image", "HeightMapSamplerLayer1"),
                ShaderProperty("Image", "TextureSampler_layer2"),
                ShaderProperty("Image", "BumpSampler_layer2"),
                ShaderProperty("Image", "HeightMapSamplerLayer2"),
                ShaderProperty("Image", "TextureSampler_layer3"),
                ShaderProperty("Image", "BumpSampler_layer3"),
                ShaderProperty("Image", "HeightMapSamplerLayer3"),
                ShaderProperty("Image", "LookupSampler"),
                ShaderProperty("Value", "MaterialWetnessMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BumpSelfShadowAmount", 0.3, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightBias3", 0.015, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightScale3", 0.03, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightBias2", 0.015, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightScale2", 0.03, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightBias1", 0.015, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightScale1", 0.03, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightBias0", 0.015, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightScale0", 0.03, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ParallaxSelfShadowAmount", 0.95, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 48.0, 0.0, 0.0, 0.0),
                ShaderProperty("Layout", PNCTT3TX)]

terrain_cb_w_4lyr_cm_pxm_tntsps = [
                ShaderProperty("Image", "TintPaletteSampler"),
                ShaderProperty("Image", "TextureSampler_layer0"),
                ShaderProperty("Image", "BumpSampler_layer0"),
                ShaderProperty("Image", "HeightMapSamplerLayer0"),
                ShaderProperty("Image", "TextureSampler_layer1"),
                ShaderProperty("Image", "BumpSampler_layer1"),
                ShaderProperty("Image", "HeightMapSamplerLayer1"),
                ShaderProperty("Image", "TextureSampler_layer2"),
                ShaderProperty("Image", "BumpSampler_layer2"),
                ShaderProperty("Image", "HeightMapSamplerLayer2"),
                ShaderProperty("Image", "TextureSampler_layer3"),
                ShaderProperty("Image", "BumpSampler_layer3"),
                ShaderProperty("Image", "HeightMapSamplerLayer3"),
                ShaderProperty("Image", "LookupSampler"),
                ShaderProperty("Value", "MaterialWetnessMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BumpSelfShadowAmount", 0.3, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightBias3", 0.015, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightScale3", 0.03, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightBias2", 0.015, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightScale2", 0.03, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightBias1", 0.015, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightScale1", 0.03, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightBias0", 0.015, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightScale0", 0.03, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ParallaxSelfShadowAmount", 0.95, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 48.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Layout", PNCTT3TX)]

terrain_cb_w_4lyr_cm_tntsps = [
                ShaderProperty("Image", "TintPaletteSampler"),
                ShaderProperty("Image", "TextureSampler_layer0"),
                ShaderProperty("Image", "BumpSampler_layer0"),
                ShaderProperty("Image", "TextureSampler_layer1"),
                ShaderProperty("Image", "BumpSampler_layer1"),
                ShaderProperty("Image", "TextureSampler_layer2"),
                ShaderProperty("Image", "BumpSampler_layer2"),
                ShaderProperty("Image", "TextureSampler_layer3"),
                ShaderProperty("Image", "BumpSampler_layer3"),
                ShaderProperty("Image", "LookupSampler"),
                ShaderProperty("Value", "MaterialWetnessMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BumpSelfShadowAmount", 0.3, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 48.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

terrain_cb_w_4lyr_lodsps = [
                ShaderProperty("Layout", PNCCT),
                ShaderProperty("Image", "TextureSampler_layer0"),
                ShaderProperty("Image", "TextureSampler_layer1"),
                ShaderProperty("Image", "TextureSampler_layer2"),
                ShaderProperty("Image", "TextureSampler_layer3"),
                ShaderProperty("Value", "MaterialWetnessMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BumpSelfShadowAmount", 0.3, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 48.0, 0.0, 0.0, 0.0)]

terrain_cb_w_4lyr_pxmsps = [
                ShaderProperty("Layout", PNCCT3TX),
                ShaderProperty("Image", "TextureSampler_layer0"),
                ShaderProperty("Image", "BumpSampler_layer0"),
                ShaderProperty("Image", "HeightMapSamplerLayer0"),
                ShaderProperty("Image", "TextureSampler_layer1"),
                ShaderProperty("Image", "BumpSampler_layer1"),
                ShaderProperty("Image", "HeightMapSamplerLayer1"),
                ShaderProperty("Image", "TextureSampler_layer2"),
                ShaderProperty("Image", "BumpSampler_layer2"),
                ShaderProperty("Image", "HeightMapSamplerLayer2"),
                ShaderProperty("Image", "TextureSampler_layer3"),
                ShaderProperty("Image", "BumpSampler_layer3"),
                ShaderProperty("Image", "HeightMapSamplerLayer3"),
                ShaderProperty("Value", "MaterialWetnessMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BumpSelfShadowAmount", 0.3, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightBias3", 0.015, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightScale3", 0.03, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightBias2", 0.015, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightScale2", 0.03, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightBias1", 0.015, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightScale1", 0.03, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightBias0", 0.015, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightScale0", 0.03, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ParallaxSelfShadowAmount", 0.95, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 48.0, 0.0, 0.0, 0.0)]

terrain_cb_w_4lyr_pxm_spmsps = [
                ShaderProperty("Layout", PNCCT3TX),
                ShaderProperty("Image", "TextureSampler_layer0"),
                ShaderProperty("Image", "BumpSampler_layer0"),
                ShaderProperty("Image", "HeightMapSamplerLayer0"),
                ShaderProperty("Image", "TextureSampler_layer1"),
                ShaderProperty("Image", "BumpSampler_layer1"),
                ShaderProperty("Image", "HeightMapSamplerLayer1"),
                ShaderProperty("Image", "TextureSampler_layer2"),
                ShaderProperty("Image", "BumpSampler_layer2"),
                ShaderProperty("Image", "HeightMapSamplerLayer2"),
                ShaderProperty("Image", "TextureSampler_layer3"),
                ShaderProperty("Image", "BumpSampler_layer3"),
                ShaderProperty("Image", "HeightMapSamplerLayer3"),
                ShaderProperty("Value", "MaterialWetnessMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BumpSelfShadowAmount", 0.3, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightBias3", 0.015, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightScale3", 0.03, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightBias2", 0.015, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightScale2", 0.03, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightBias1", 0.015, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightScale1", 0.03, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightBias0", 0.015, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightScale0", 0.03, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ParallaxSelfShadowAmount", 0.95, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecIntensityAdjust", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMultSpecMap", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecFalloffAdjust", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMultSpecMap", 48.0, 0.0, 0.0, 0.0)]

terrain_cb_w_4lyr_specsps = [
                ShaderProperty("Layout", PNCCTX),
                ShaderProperty("Image", "TextureSampler_layer0"),
                ShaderProperty("Image", "BumpSampler_layer0"),
                ShaderProperty("Image", "TextureSampler_layer1"),
                ShaderProperty("Image", "BumpSampler_layer1"),
                ShaderProperty("Image", "TextureSampler_layer2"),
                ShaderProperty("Image", "BumpSampler_layer2"),
                ShaderProperty("Image", "TextureSampler_layer3"),
                ShaderProperty("Image", "BumpSampler_layer3"),
                ShaderProperty("Value", "MaterialWetnessMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BumpSelfShadowAmount", 0.3, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 48.0, 0.0, 0.0, 0.0)]

terrain_cb_w_4lyr_spec_intsps = [
                ShaderProperty("Layout", PNCCTX),
                ShaderProperty("Image", "TextureSampler_layer0"),
                ShaderProperty("Image", "BumpSampler_layer0"),
                ShaderProperty("Image", "TextureSampler_layer1"),
                ShaderProperty("Image", "BumpSampler_layer1"),
                ShaderProperty("Image", "TextureSampler_layer2"),
                ShaderProperty("Image", "BumpSampler_layer2"),
                ShaderProperty("Image", "TextureSampler_layer3"),
                ShaderProperty("Image", "BumpSampler_layer3"),
                ShaderProperty("Value", "MaterialWetnessMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BumpSelfShadowAmount", 0.3, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 48.0, 0.0, 0.0, 0.0)]

terrain_cb_w_4lyr_spec_int_pxmsps = [
                ShaderProperty("Layout", PNCCT3TX),
                ShaderProperty("Image", "TextureSampler_layer0"),
                ShaderProperty("Image", "BumpSampler_layer0"),
                ShaderProperty("Image", "HeightMapSamplerLayer0"),
                ShaderProperty("Image", "TextureSampler_layer1"),
                ShaderProperty("Image", "BumpSampler_layer1"),
                ShaderProperty("Image", "HeightMapSamplerLayer1"),
                ShaderProperty("Image", "TextureSampler_layer2"),
                ShaderProperty("Image", "BumpSampler_layer2"),
                ShaderProperty("Image", "HeightMapSamplerLayer2"),
                ShaderProperty("Image", "TextureSampler_layer3"),
                ShaderProperty("Image", "BumpSampler_layer3"),
                ShaderProperty("Image", "HeightMapSamplerLayer3"),
                ShaderProperty("Value", "MaterialWetnessMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BumpSelfShadowAmount", 0.3, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightBias3", 0.015, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightScale3", 0.03, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightBias2", 0.015, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightScale2", 0.03, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightBias1", 0.015, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightScale1", 0.03, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightBias0", 0.015, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightScale0", 0.03, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ParallaxSelfShadowAmount", 0.95, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 48.0, 0.0, 0.0, 0.0)]

terrain_cb_w_4lyr_spec_pxmsps = [
                ShaderProperty("Layout", PNCCT3TX),
                ShaderProperty("Image", "TextureSampler_layer0"),
                ShaderProperty("Image", "BumpSampler_layer0"),
                ShaderProperty("Image", "HeightMapSamplerLayer0"),
                ShaderProperty("Image", "TextureSampler_layer1"),
                ShaderProperty("Image", "BumpSampler_layer1"),
                ShaderProperty("Image", "HeightMapSamplerLayer1"),
                ShaderProperty("Image", "TextureSampler_layer2"),
                ShaderProperty("Image", "BumpSampler_layer2"),
                ShaderProperty("Image", "HeightMapSamplerLayer2"),
                ShaderProperty("Image", "TextureSampler_layer3"),
                ShaderProperty("Image", "BumpSampler_layer3"),
                ShaderProperty("Image", "HeightMapSamplerLayer3"),
                ShaderProperty("Value", "MaterialWetnessMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BumpSelfShadowAmount", 0.3, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightBias3", 0.015, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightScale3", 0.03, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightBias2", 0.015, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightScale2", 0.03, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightBias1", 0.015, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightScale1", 0.03, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightBias0", 0.015, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HeightScale0", 0.03, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ParallaxSelfShadowAmount", 0.95, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 48.0, 0.0, 0.0, 0.0)]

treessps = [
                ShaderProperty("Layout", PNCCT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Value", "ShadowFalloff", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "AlphaTest", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "AlphaScale", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SelfShadowing", 0.8, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTreeNormals", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WindGlobalParams", 1.0, 5.0, 5.0, 1.0),
                ShaderProperty("Value", "umGlobalParams", 0.025, 0.02, 1.0, 0.5)]

trees_lodsps = [
                ShaderProperty("Layout", PNCCT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Value", "ShadowFalloff", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "AlphaTest", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "AlphaScale", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SelfShadowing", 0.8, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTreeNormals", 1.0, 0.0, 0.0, 0.0)]

trees_lod2sps = [
                ShaderProperty("Layout", PNCCTTTT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Value", "ShadowFalloff", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "AlphaTest", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "AlphaScale", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTreeNormals", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "TreeLod2Normal", 0.0, 0.0, 1.0, 0.0),
                ShaderProperty("Value", "TreeLod2Params", 1.0, 1.0, 0.0, 0.0)]

trees_lod_tntsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "TintPaletteSampler"),
                ShaderProperty("Value", "ShadowFalloff", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "AlphaTest", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "AlphaScale", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SelfShadowing", 0.8, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTreeNormals", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

trees_normalsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Value", "ShadowFalloff", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "AlphaTest", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "AlphaScale", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SelfShadowing", 0.8, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTreeNormals", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WindGlobalParams", 1.0, 5.0, 5.0, 1.0),
                ShaderProperty("Value", "umGlobalParams", 0.025, 0.02, 1.0, 0.5),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Layout", PNCCTX)]

trees_normal_diffspecsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Value", "ShadowFalloff", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "AlphaTest", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "AlphaScale", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SelfShadowing", 0.8, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTreeNormals", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WindGlobalParams", 1.0, 5.0, 5.0, 1.0),
                ShaderProperty("Value", "umGlobalParams", 0.025, 0.02, 1.0, 0.5),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Layout", PNCCTX)]

trees_normal_diffspec_tntsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "TintPaletteSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Value", "ShadowFalloff", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "AlphaTest", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "AlphaScale", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SelfShadowing", 0.8, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTreeNormals", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WindGlobalParams", 1.0, 5.0, 5.0, 1.0),
                ShaderProperty("Value", "umGlobalParams", 0.025, 0.02, 1.0, 0.5),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

trees_normal_specsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Value", "ShadowFalloff", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "AlphaTest", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "AlphaScale", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SelfShadowing", 0.8, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTreeNormals", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WindGlobalParams", 1.0, 5.0, 5.0, 1.0),
                ShaderProperty("Value", "umGlobalParams", 0.025, 0.02, 1.0, 0.5),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Layout", PNCCTX)]

trees_normal_spec_tntsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "TintPaletteSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Value", "ShadowFalloff", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "AlphaTest", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "AlphaScale", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SelfShadowing", 0.8, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTreeNormals", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WindGlobalParams", 1.0, 5.0, 5.0, 1.0),
                ShaderProperty("Value", "umGlobalParams", 0.025, 0.02, 1.0, 0.5),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

trees_shadow_proxysps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Value", "ShadowFalloff", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "AlphaTest", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "AlphaScale", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SelfShadowing", 0.8, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTreeNormals", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WindGlobalParams", 1.0, 5.0, 5.0, 1.0),
                ShaderProperty("Value", "umGlobalParams", 0.025, 0.02, 1.0, 0.5)]

trees_tntsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "TintPaletteSampler"),
                ShaderProperty("Value", "ShadowFalloff", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "AlphaTest", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "AlphaScale", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SelfShadowing", 0.8, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTreeNormals", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WindGlobalParams", 1.0, 5.0, 5.0, 1.0),
                ShaderProperty("Value", "umGlobalParams", 0.025, 0.02, 1.0, 0.5),
                ShaderProperty("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

vehicle_badgessps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DamageSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                ShaderProperty("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Layout", PBBNCTTX)]

vehicle_basicsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DamageSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                ShaderProperty("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_blurredrotorsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                ShaderProperty("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0)]

vehicle_blurredrotor_emissivesps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                ShaderProperty("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "EmissiveMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0)]

vehicle_clothsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DamageSampler"),
                ShaderProperty("Image", "DirtSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                ShaderProperty("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                ShaderProperty("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_cloth2sps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DamageSampler"),
                ShaderProperty("Image", "DiffuseSampler2"),
                ShaderProperty("Image", "DirtSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                ShaderProperty("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Diffuse2SpecMod", 0.8, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                ShaderProperty("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "matDiffuseColor2", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_cutoutsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DamageSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                ShaderProperty("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_dash_emissivesps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DamageSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                ShaderProperty("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DimmerSetPacked", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Layout", PBBNCT)]

vehicle_dash_emissive_opaquesps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DamageSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                ShaderProperty("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_decalsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DamageSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                ShaderProperty("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_decal2sps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DamageSampler"),
                ShaderProperty("Image", "DirtSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                ShaderProperty("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                ShaderProperty("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Layout", PBBNCTX)]

vehicle_detailsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DamageSampler"),
                ShaderProperty("Image", "DetailSampler"),
                ShaderProperty("Image", "DirtSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "DetailSettings", 0.0, 0.0, 24.0, 24.0),
                ShaderProperty("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                ShaderProperty("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                ShaderProperty("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_detail2sps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DamageSampler"),
                ShaderProperty("Image", "DetailSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "DetailSettings", 0.0, 0.0, 24.0, 24.0),
                ShaderProperty("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                ShaderProperty("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Layout", PBBNCTT)]

vehicle_emissive_alphasps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DamageSampler"),
                ShaderProperty("Image", "DirtSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                ShaderProperty("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                ShaderProperty("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "EmissiveMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_emissive_opaquesps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DamageSampler"),
                ShaderProperty("Image", "DirtSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                ShaderProperty("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                ShaderProperty("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "EmissiveMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_genericsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DamageSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                ShaderProperty("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_interiorsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DamageSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                ShaderProperty("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_interior2sps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DamageSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                ShaderProperty("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Layout", PBBNCT)]

vehicle_licenseplatesps = [
                ShaderProperty("Image", "DamageSampler"),
                ShaderProperty("Image", "DirtSampler"),
                ShaderProperty("Image", "plateBgSampler"),
                ShaderProperty("Image", "plateBgBumpSampler"),
                ShaderProperty("Image", "FontSampler"),
                ShaderProperty("Image", "FontNormalSampler"),
                ShaderProperty("Value", "distEpsilonScaleMin", 10.0, 10.0, 0.0, 0.0),
                ShaderProperty("Value", "distMapCenterVal", 0.5, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "FontNormalScale", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "LicensePlateFontTint", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "LicensePlateFontExtents", 0.043, 0.38, 0.945, 0.841),
                ShaderProperty("Value", "numLetters", 16.0, 4.0, 0.0, 0.0),
                ShaderProperty("Value", "LetterSize", 0.0625, 0.25, 0.0, 0.0),
                ShaderProperty("Value", "LetterIndex2", 63.0, 63.0, 62.0, 0.0),
                ShaderProperty("Value", "LetterIndex1", 10.0, 21.0, 10.0, 23.0),
                ShaderProperty("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                ShaderProperty("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                ShaderProperty("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Layout", PBBNCTTX)]

vehicle_lightsemissivesps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DamageSampler"),
                ShaderProperty("Image", "DirtSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                ShaderProperty("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                ShaderProperty("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "DimmerSetPacked", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "EmissiveMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Layout", PBBNCTT)]

vehicle_meshsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DamageSampler"),
                ShaderProperty("Image", "DirtSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                ShaderProperty("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Specular2Color_DirLerp", 0.0, 0.5, 0.0, 0.0),
                ShaderProperty("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                ShaderProperty("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Layout", PBBNCTTX)]

vehicle_mesh2_enveffsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DamageSampler"),
                ShaderProperty("Image", "SnowSampler0"),
                ShaderProperty("Image", "SnowSampler1"),
                ShaderProperty("Image", "DirtSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                ShaderProperty("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecTexTileUV", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                ShaderProperty("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_mesh_enveffsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DamageSampler"),
                ShaderProperty("Image", "SnowSampler0"),
                ShaderProperty("Image", "SnowSampler1"),
                ShaderProperty("Image", "DirtSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                ShaderProperty("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecTexTileUV", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                ShaderProperty("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_paint1sps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DamageSampler"),
                ShaderProperty("Image", "DirtSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                ShaderProperty("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Specular2Color_DirLerp", 0.0, 0.5, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                ShaderProperty("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_nosplashsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DamageSampler"),
                ShaderProperty("Image", "DirtSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                ShaderProperty("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Specular2Color_DirLerp", 0.0, 0.5, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                ShaderProperty("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_nowatersps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DamageSampler"),
                ShaderProperty("Image", "DirtSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                ShaderProperty("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Specular2Color_DirLerp", 0.0, 0.5, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                ShaderProperty("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_paint1_enveffsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DamageSampler"),
                ShaderProperty("Image", "SnowSampler0"),
                ShaderProperty("Image", "SnowSampler1"),
                ShaderProperty("Image", "DirtSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                ShaderProperty("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Specular2Color_DirLerp", 0.0, 0.5, 0.0, 0.0),
                ShaderProperty("Value", "SpecTexTileUV", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                ShaderProperty("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_paint2sps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DamageSampler"),
                ShaderProperty("Image", "DirtSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                ShaderProperty("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Specular2Color_DirLerp", 0.0, 0.5, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                ShaderProperty("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_paint2_enveffsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DamageSampler"),
                ShaderProperty("Image", "SnowSampler0"),
                ShaderProperty("Image", "SnowSampler1"),
                ShaderProperty("Image", "DirtSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                ShaderProperty("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Specular2Color_DirLerp", 0.0, 0.5, 0.0, 0.0),
                ShaderProperty("Value", "SpecTexTileUV", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                ShaderProperty("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_paint3sps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DamageSampler"),
                ShaderProperty("Image", "DiffuseSampler2"),
                ShaderProperty("Image", "DirtSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                ShaderProperty("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Diffuse2SpecMod", 0.8, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Specular2Color_DirLerp", 0.0, 0.5, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                ShaderProperty("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "matDiffuseColor2", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Layout", PBBNCTT)]

vehicle_paint3_enveffsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DamageSampler"),
                ShaderProperty("Image", "SnowSampler0"),
                ShaderProperty("Image", "SnowSampler1"),
                ShaderProperty("Image", "DiffuseSampler2"),
                ShaderProperty("Image", "DirtSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                ShaderProperty("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Diffuse2SpecMod", 0.8, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Specular2Color_DirLerp", 0.0, 0.5, 0.0, 0.0),
                ShaderProperty("Value", "SpecTexTileUV", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                ShaderProperty("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "matDiffuseColor2", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_paint3_lvrsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DamageSampler"),
                ShaderProperty("Image", "DiffuseSampler3"),
                ShaderProperty("Image", "DirtSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                ShaderProperty("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Diffuse3SpecMod", 0.8, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Specular2Color_DirLerp", 0.0, 0.5, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                ShaderProperty("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "matDiffuseColor2", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_paint4sps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DamageSampler"),
                ShaderProperty("Image", "DiffuseSampler2"),
                ShaderProperty("Image", "DirtSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                ShaderProperty("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Diffuse2SpecMod", 0.8, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Specular2Color_DirLerp", 0.0, 0.5, 0.0, 0.0),
                ShaderProperty("Value", "Specular2ColorIntensity", 1.7, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Specular2Factor", 40.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecTexTileUV", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                ShaderProperty("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "matDiffuseColor2", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "DiffuseTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_paint4_emissivesps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DamageSampler"),
                ShaderProperty("Image", "DiffuseSampler2"),
                ShaderProperty("Image", "DirtSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                ShaderProperty("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Diffuse2SpecMod", 0.8, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Specular2Color_DirLerp", 0.0, 0.5, 0.0, 0.0),
                ShaderProperty("Value", "Specular2ColorIntensity", 1.7, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Specular2Factor", 40.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecTexTileUV", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                ShaderProperty("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "EmissiveMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "matDiffuseColor2", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "DiffuseTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_paint4_enveffsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DamageSampler"),
                ShaderProperty("Image", "SnowSampler0"),
                ShaderProperty("Image", "SnowSampler1"),
                ShaderProperty("Image", "DiffuseSampler2"),
                ShaderProperty("Image", "DirtSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                ShaderProperty("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Diffuse2SpecMod", 0.8, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Specular2Color_DirLerp", 0.0, 0.5, 0.0, 0.0),
                ShaderProperty("Value", "Specular2ColorIntensity", 1.7, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Specular2Factor", 40.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecTexTileUV", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                ShaderProperty("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "matDiffuseColor2", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "DiffuseTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_paint5_enveffsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DamageSampler"),
                ShaderProperty("Image", "SnowSampler0"),
                ShaderProperty("Image", "SnowSampler1"),
                ShaderProperty("Image", "DiffuseSampler2"),
                ShaderProperty("Image", "DirtSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                ShaderProperty("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Diffuse2SpecMod", 0.8, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Specular2Color_DirLerp", 0.0, 0.5, 0.0, 0.0),
                ShaderProperty("Value", "Specular2ColorIntensity", 1.7, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Specular2Factor", 40.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecTexTileUV", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                ShaderProperty("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "matDiffuseColor2", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "DiffuseTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_paint6sps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DamageSampler"),
                ShaderProperty("Image", "DiffuseSampler2"),
                ShaderProperty("Image", "DirtSampler"),
                ShaderProperty("Image", "BumpSampler2"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                ShaderProperty("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Diffuse2SpecMod", 0.8, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Specular2Color_DirLerp", 0.0, 0.5, 0.0, 0.0),
                ShaderProperty("Value", "Specular2ColorIntensity", 1.7, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Specular2Factor", 40.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecTexTileUV", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                ShaderProperty("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "matDiffuseColor2", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "DiffuseTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_paint6_enveffsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DamageSampler"),
                ShaderProperty("Image", "SnowSampler0"),
                ShaderProperty("Image", "SnowSampler1"),
                ShaderProperty("Image", "DiffuseSampler2"),
                ShaderProperty("Image", "DirtSampler"),
                ShaderProperty("Image", "BumpSampler2"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                ShaderProperty("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Diffuse2SpecMod", 0.8, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Specular2Color_DirLerp", 0.0, 0.5, 0.0, 0.0),
                ShaderProperty("Value", "Specular2ColorIntensity", 1.7, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Specular2Factor", 40.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecTexTileUV", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                ShaderProperty("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "matDiffuseColor2", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "DiffuseTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_paint7sps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DamageSampler"),
                ShaderProperty("Image", "DiffuseSampler2"),
                ShaderProperty("Image", "DirtSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                ShaderProperty("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Diffuse2SpecMod", 0.8, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Specular2Color_DirLerp", 0.0, 0.5, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                ShaderProperty("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "matDiffuseColor2", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "DiffuseTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_paint7_enveffsps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DamageSampler"),
                ShaderProperty("Image", "SnowSampler0"),
                ShaderProperty("Image", "SnowSampler1"),
                ShaderProperty("Image", "DiffuseSampler2"),
                ShaderProperty("Image", "DirtSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                ShaderProperty("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Diffuse2SpecMod", 0.8, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Specular2Color_DirLerp", 0.0, 0.5, 0.0, 0.0),
                ShaderProperty("Value", "SpecTexTileUV", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                ShaderProperty("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "matDiffuseColor2", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "DiffuseTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_paint8sps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DamageSampler"),
                ShaderProperty("Image", "SnowSampler0"),
                ShaderProperty("Image", "SnowSampler1"),
                ShaderProperty("Image", "DiffuseSampler2"),
                ShaderProperty("Image", "DirtSampler"),
                ShaderProperty("Image", "DirtBumpSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                ShaderProperty("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Diffuse2SpecMod", 0.8, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Specular2Color_DirLerp", 0.0, 0.5, 0.0, 0.0),
                ShaderProperty("Value", "Specular2ColorIntensity", 1.7, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Specular2Factor", 40.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecTexTileUV", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                ShaderProperty("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "matDiffuseColor2", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "DiffuseTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_paint9sps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DamageSampler"),
                ShaderProperty("Image", "SnowSampler0"),
                ShaderProperty("Image", "SnowSampler1"),
                ShaderProperty("Image", "DiffuseSampler2"),
                ShaderProperty("Image", "DirtSampler"),
                ShaderProperty("Image", "DirtBumpSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                ShaderProperty("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Diffuse2SpecMod", 0.8, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Specular2Color_DirLerp", 0.0, 0.5, 0.0, 0.0),
                ShaderProperty("Value", "Specular2ColorIntensity", 1.7, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Specular2Factor", 40.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecTexTileUV", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                ShaderProperty("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "matDiffuseColor2", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "DiffuseTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_shutssps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DamageSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                ShaderProperty("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_tiresps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DirtSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                ShaderProperty("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Specular2Color_DirLerp", 0.0, 0.5, 0.0, 0.0),
                ShaderProperty("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                ShaderProperty("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "matWheelWorldViewProj", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "matWheelWorld", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "TyreDeformParams2", 0.262, 1495.05, 0.0, 0.0),
                ShaderProperty("Value", "TyreDeformParams", 0.0, 0.0, 0.0, 1.0),
                ShaderProperty("Layout", PNCTTX)]

vehicle_tire_emissivesps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DirtSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                ShaderProperty("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Specular2Color_DirLerp", 0.0, 0.5, 0.0, 0.0),
                ShaderProperty("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                ShaderProperty("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "EmissiveMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "matWheelWorldViewProj", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "matWheelWorld", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "TyreDeformParams2", 0.262, 1495.05, 0.0, 0.0),
                ShaderProperty("Value", "TyreDeformParams", 0.0, 0.0, 0.0, 1.0)]

vehicle_tracksps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DirtSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                ShaderProperty("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                ShaderProperty("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "TrackAnimUV", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0)]

vehicle_track2sps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DirtSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                ShaderProperty("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                ShaderProperty("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "Track2AnimUV", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0)]

vehicle_track2_emissivesps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DirtSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                ShaderProperty("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                ShaderProperty("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "Track2AnimUV", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "EmissiveMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0)]

vehicle_track_ammosps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DirtSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                ShaderProperty("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                ShaderProperty("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "TrackAmmoAnimUV", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0)]

vehicle_track_emissivesps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DirtSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                ShaderProperty("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                ShaderProperty("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "TrackAnimUV", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "EmissiveMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0)]

vehicle_lightssps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DamageSampler"),
                ShaderProperty("Image", "DirtSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                ShaderProperty("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                ShaderProperty("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_vehglasssps = [
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DamageSampler"),
                ShaderProperty("Image", "DirtSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                ShaderProperty("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                ShaderProperty("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Layout", PBBNCTTT)]

vehicle_vehglass_innersps = [
                ShaderProperty("Layout", PBBNCTT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DamageSampler"),
                ShaderProperty("Image", "DirtSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                ShaderProperty("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                ShaderProperty("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                ShaderProperty("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

water_fountainsps = [
                ShaderProperty("Layout", PT),
                ShaderProperty("Value", "FogColor", 0.416, 0.6, 0.631, 0.055),
                ShaderProperty("Value", "SpecularFalloff", 1118.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensity", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "RippleScale", 0.04, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "RippleBumpiness", 0.356, 0.0, 0.0, 0.0)]

water_poolenvsps = [
                ShaderProperty("Layout", PT),
                ShaderProperty("Value", "FogColor", 0.416, 0.6, 0.631, 0.055),
                ShaderProperty("Value", "SpecularFalloff", 1118.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensity", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "RippleScale", 0.04, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "RippleBumpiness", 0.356, 0.0, 0.0, 0.0)]

water_riversps = [
                ShaderProperty("Image", "FlowSampler"),
                ShaderProperty("Image", "FogSampler"),
                ShaderProperty("Value", "SpecularFalloff", 1118.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensity", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "RippleScale", 0.04, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "RippleSpeed", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "RippleBumpiness", 0.356, 0.0, 0.0, 0.0)]

water_riverfoamsps = [
                ShaderProperty("Layout", PNCTX),
                ShaderProperty("Image", "FoamSampler"),
                ShaderProperty("Value", "RippleSpeed", 0.0, 0.0, 0.0, 0.0)]

water_riverlodsps = [
                ShaderProperty("Layout", PNCT),
                ShaderProperty("Image", "FlowSampler"),
                ShaderProperty("Image", "FogSampler"),
                ShaderProperty("Value", "SpecularFalloff", 1118.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensity", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "RippleScale", 0.04, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "RippleSpeed", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "RippleBumpiness", 0.356, 0.0, 0.0, 0.0)]

water_riveroceansps = [
                ShaderProperty("Image", "FogSampler"),
                ShaderProperty("Value", "SpecularFalloff", 1118.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensity", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "RippleScale", 0.04, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "RippleBumpiness", 0.356, 0.0, 0.0, 0.0)]

water_rivershallowsps = [
                ShaderProperty("Image", "FlowSampler"),
                ShaderProperty("Image", "FogSampler"),
                ShaderProperty("Value", "SpecularFalloff", 1118.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensity", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "RippleScale", 0.04, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "RippleSpeed", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "RippleBumpiness", 0.356, 0.0, 0.0, 0.0)]

water_shallowsps = [
                ShaderProperty("Image", "FlowSampler"),
                ShaderProperty("Image", "FogSampler"),
                ShaderProperty("Value", "SpecularFalloff", 1118.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensity", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "RippleScale", 0.04, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "RippleSpeed", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "RippleBumpiness", 0.356, 0.0, 0.0, 0.0)]

water_terrainfoamsps = [
                ShaderProperty("Image", "FoamSampler"),
                ShaderProperty("Value", "HeightOpacity", 10.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WaveMovement", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WaterHeight", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WaveOffset", 0.25, 0.0, 0.0, 0.0)]

weapon_emissivestrong_alphasps = [
                ShaderProperty("Layout", PBBNCT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "EmissiveMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                ShaderProperty("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

weapon_emissive_tntsps = [
                ShaderProperty("Layout", PBBNCT),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "TintPaletteSampler"),
                ShaderProperty("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "EmissiveMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

weapon_normal_spec_alphasps = [
                ShaderProperty("Layout", PBBNCTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

weapon_normal_spec_cutout_palettesps = [
                ShaderProperty("Layout", PBBNCTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DiffuseExtraSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Image", "TextureSamplerDiffPal"),
                ShaderProperty("Value", "PaletteSelector", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Specular2Color", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "Specular2ColorIntensity", 4.7, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Specular2Factor", 40.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

weapon_normal_spec_detail_palettesps = [
                ShaderProperty("Layout", PBBNCTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DetailSampler"),
                ShaderProperty("Image", "DiffuseExtraSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Image", "TextureSamplerDiffPal"),
                ShaderProperty("Value", "DetailSettings", 0.0, 0.0, 24.0, 24.0),
                ShaderProperty("Value", "PaletteSelector", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Specular2Color", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "Specular2ColorIntensity", 4.7, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Specular2Factor", 40.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

weapon_normal_spec_detail_tntsps = [
                ShaderProperty("Layout", PBBNCTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "TintPaletteSampler"),
                ShaderProperty("Image", "DetailSampler"),
                ShaderProperty("Image", "DiffuseExtraSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "DetailSettings", 0.0, 0.0, 24.0, 24.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Specular2Color", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "Specular2ColorIntensity", 4.7, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Specular2Factor", 40.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

weapon_normal_spec_palettesps = [
                ShaderProperty("Layout", PBBNCTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "DiffuseExtraSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Image", "TextureSamplerDiffPal"),
                ShaderProperty("Value", "PaletteSelector", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Specular2Color", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "Specular2ColorIntensity", 4.7, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Specular2Factor", 40.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

weapon_normal_spec_tntsps = [
                ShaderProperty("Layout", PBBNCTX),
                ShaderProperty("Image", "DiffuseSampler"),
                ShaderProperty("Image", "TintPaletteSampler"),
                ShaderProperty("Image", "DiffuseExtraSampler"),
                ShaderProperty("Image", "BumpSampler"),
                ShaderProperty("Image", "SpecSampler"),
                ShaderProperty("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Specular2Color", 1.0, 1.0, 1.0, 0.0),
                ShaderProperty("Value", "Specular2ColorIntensity", 4.7, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "Specular2Factor", 40.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                ShaderProperty("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

shaders = {
                "blend_2lyr.sps" : blend_2lyrsps, 
                "cable.sps" : cablesps, 
                "cloth_default.sps" : cloth_defaultsps, 
                "cloth_normal_spec.sps" : cloth_normal_specsps, 
                "cloth_normal_spec_alpha.sps" : cloth_normal_spec_alphasps, 
                "cloth_normal_spec_cutout.sps" : cloth_normal_spec_cutoutsps, 
                "cloth_normal_spec_tnt.sps" : cloth_normal_spec_tntsps, 
                "cloth_spec_alpha.sps" : cloth_spec_alphasps, 
                "cloth_spec_cutout.sps" : cloth_spec_cutoutsps, 
                "clouds_altitude.sps" : clouds_altitudesps, 
                "clouds_anim.sps" : clouds_animsps, 
                "clouds_animsoft.sps" : clouds_animsoftsps, 
                "clouds_fast.sps" : clouds_fastsps, 
                "clouds_fog.sps" : clouds_fogsps, 
                "clouds_soft.sps" : clouds_softsps, 
                "cpv_only.sps" : cpv_onlysps, 
                "cutout_fence.sps" : cutout_fencesps, 
                "cutout_fence_normal.sps" : cutout_fence_normalsps, 
                "cutout_hard.sps" : cutout_hardsps, 
                "decal.sps" : decalsps, 
                "decal_amb_only.sps" : decal_amb_onlysps, 
                "decal_diff_only_um.sps" : decal_diff_only_umsps, 
                "decal_dirt.sps" : decal_dirtsps, 
                "decal_emissivenight_only.sps" : decal_emissivenight_onlysps, 
                "decal_emissive_only.sps" : decal_emissive_onlysps, 
                "decal_glue.sps" : decal_gluesps, 
                "decal_normal_only.sps" : decal_normal_onlysps, 
                "decal_shadow_only.sps" : decal_shadow_onlysps, 
                "decal_spec_only.sps" : decal_spec_onlysps, 
                "decal_tnt.sps" : decal_tntsps, 
                "custom_default.sps" : custom_defaultsps, 
                "default.sps" : defaultsps, 
                "default_noedge.sps" : default_noedgesps, 
                "gta_default.sps" : gta_defaultsps, 
                "alpha.sps" : alphasps, 
                "cutout.sps" : cutoutsps, 
                "default_detail.sps" : default_detailsps, 
                "default_spec.sps" : default_specsps, 
                "spec_const.sps" : spec_constsps, 
                "default_terrain_wet.sps" : default_terrain_wetsps, 
                "default_tnt.sps" : default_tntsps, 
                "cutout_tnt.sps" : cutout_tntsps, 
                "default_um.sps" : default_umsps, 
                "cutout_um.sps" : cutout_umsps, 
                "distance_map.sps" : distance_mapsps, 
                "emissive.sps" : emissivesps, 
                "emissive_alpha.sps" : emissive_alphasps, 
                "emissivenight.sps" : emissivenightsps, 
                "emissivenight_alpha.sps" : emissivenight_alphasps, 
                "emissivenight_geomnightonly.sps" : emissivenight_geomnightonlysps, 
                "emissivestrong.sps" : emissivestrongsps, 
                "emissivestrong_alpha.sps" : emissivestrong_alphasps, 
                "emissive_additive_alpha.sps" : emissive_additive_alphasps, 
                "emissive_additive_uv_alpha.sps" : emissive_additive_uv_alphasps, 
                "emissive_clip.sps" : emissive_clipsps, 
                "emissive_speclum.sps" : emissive_speclumsps, 
                "emissive_tnt.sps" : emissive_tntsps, 
                "emissive_alpha_tnt.sps" : emissive_alpha_tntsps, 
                "glass.sps" : glasssps, 
                "glass_breakable.sps" : glass_breakablesps, 
                "glass_breakable_screendooralpha.sps" : glass_breakable_screendooralphasps, 
                "glass_displacement.sps" : glass_displacementsps, 
                "glass_emissive.sps" : glass_emissivesps, 
                "glass_emissive_alpha.sps" : glass_emissive_alphasps, 
                "glass_emissivenight.sps" : glass_emissivenightsps, 
                "glass_emissivenight_alpha.sps" : glass_emissivenight_alphasps, 
                "glass_env.sps" : glass_envsps, 
                "glass_normal_spec_reflect.sps" : glass_normal_spec_reflectsps, 
                "glass_pv.sps" : glass_pvsps, 
                "glass_pv_env.sps" : glass_pv_envsps, 
                "glass_reflect.sps" : glass_reflectsps, 
                "glass_spec.sps" : glass_specsps, 
                "grass.sps" : grasssps, 
                "grass_batch.sps" : grass_batchsps, 
                "grass_fur.sps" : grass_fursps, 
                "grass_fur_mask.sps" : grass_fur_masksps, 
                "minimap.sps" : minimapsps, 
                "mirror_crack.sps" : mirror_cracksps, 
                "mirror_decal.sps" : mirror_decalsps, 
                "mirror_default.sps" : mirror_defaultsps, 
                "gta_normal.sps" : gta_normalsps, 
                "normal.sps" : normalsps, 
                "normal_alpha.sps" : normal_alphasps, 
                "water_decal.sps" : water_decalsps, 
                "normal_cutout.sps" : normal_cutoutsps, 
                "normal_screendooralpha.sps" : normal_screendooralphasps, 
                "normal_cubemap_reflect.sps" : normal_cubemap_reflectsps, 
                "normal_decal.sps" : normal_decalsps, 
                "normal_decal_pxm.sps" : normal_decal_pxmsps, 
                "normal_decal_pxm_tnt.sps" : normal_decal_pxm_tntsps, 
                "normal_decal_tnt.sps" : normal_decal_tntsps, 
                "normal_detail.sps" : normal_detailsps, 
                "normal_detail_dpm.sps" : normal_detail_dpmsps, 
                "normal_diffspec.sps" : normal_diffspecsps, 
                "normal_diffspec_detail.sps" : normal_diffspec_detailsps, 
                "normal_diffspec_detail_dpm.sps" : normal_diffspec_detail_dpmsps, 
                "normal_diffspec_detail_dpm_tnt.sps" : normal_diffspec_detail_dpm_tntsps, 
                "normal_diffspec_detail_tnt.sps" : normal_diffspec_detail_tntsps, 
                "normal_diffspec_tnt.sps" : normal_diffspec_tntsps, 
                "normal_pxm.sps" : normal_pxmsps, 
                "normal_pxm_tnt.sps" : normal_pxm_tntsps, 
                "normal_tnt_pxm.sps" : normal_tnt_pxmsps, 
                "normal_reflect.sps" : normal_reflectsps, 
                "normal_reflect_alpha.sps" : normal_reflect_alphasps, 
                "normal_reflect_screendooralpha.sps" : normal_reflect_screendooralphasps, 
                "normal_reflect_decal.sps" : normal_reflect_decalsps, 
                "normal_spec.sps" : normal_specsps, 
                "normal_spec_alpha.sps" : normal_spec_alphasps, 
                "normal_spec_cutout.sps" : normal_spec_cutoutsps, 
                "normal_spec_screendooralpha.sps" : normal_spec_screendooralphasps, 
                "normal_spec_batch.sps" : normal_spec_batchsps, 
                "normal_spec_cubemap_reflect.sps" : normal_spec_cubemap_reflectsps, 
                "normal_spec_decal.sps" : normal_spec_decalsps, 
                "normal_spec_decal_detail.sps" : normal_spec_decal_detailsps, 
                "normal_spec_decal_nopuddle.sps" : normal_spec_decal_nopuddlesps, 
                "normal_spec_decal_pxm.sps" : normal_spec_decal_pxmsps, 
                "normal_spec_decal_tnt.sps" : normal_spec_decal_tntsps, 
                "normal_spec_detail.sps" : normal_spec_detailsps, 
                "normal_spec_detail_dpm.sps" : normal_spec_detail_dpmsps, 
                "normal_spec_detail_dpm_tnt.sps" : normal_spec_detail_dpm_tntsps, 
                "normal_spec_detail_dpm_vertdecal_tnt.sps" : normal_spec_detail_dpm_vertdecal_tntsps, 
                "normal_spec_detail_tnt.sps" : normal_spec_detail_tntsps, 
                "normal_spec_dpm.sps" : normal_spec_dpmsps, 
                "normal_spec_emissive.sps" : normal_spec_emissivesps, 
                "normal_spec_pxm.sps" : normal_spec_pxmsps, 
                "normal_spec_pxm_tnt.sps" : normal_spec_pxm_tntsps, 
                "normal_spec_tnt_pxm.sps" : normal_spec_tnt_pxmsps, 
                "normal_spec_reflect.sps" : normal_spec_reflectsps, 
                "normal_spec_reflect_alpha.sps" : normal_spec_reflect_alphasps, 
                "normal_spec_reflect_decal.sps" : normal_spec_reflect_decalsps, 
                "normal_spec_reflect_emissivenight.sps" : normal_spec_reflect_emissivenightsps, 
                "normal_spec_reflect_emissivenight_alpha.sps" : normal_spec_reflect_emissivenight_alphasps, 
                "normal_spec_tnt.sps" : normal_spec_tntsps, 
                "normal_spec_cutout_tnt.sps" : normal_spec_cutout_tntsps, 
                "normal_spec_um.sps" : normal_spec_umsps, 
                "normal_spec_wrinkle.sps" : normal_spec_wrinklesps, 
                "normal_terrain_wet.sps" : normal_terrain_wetsps, 
                "normal_tnt.sps" : normal_tntsps, 
                "normal_tnt_alpha.sps" : normal_tnt_alphasps, 
                "normal_cutout_tnt.sps" : normal_cutout_tntsps, 
                "normal_um.sps" : normal_umsps, 
                "normal_cutout_um.sps" : normal_cutout_umsps, 
                "normal_um_tnt.sps" : normal_um_tntsps, 
                "parallax.sps" : parallaxsps, 
                "parallax_specmap.sps" : parallax_specmapsps, 
                "ped.sps" : pedsps, 
                "ped_alpha.sps" : ped_alphasps, 
                "ped_cloth.sps" : ped_clothsps, 
                "ped_cloth_enveff.sps" : ped_cloth_enveffsps, 
                "ped_decal.sps" : ped_decalsps, 
                "ped_decal_decoration.sps" : ped_decal_decorationsps, 
                "ped_decal_expensive.sps" : ped_decal_expensivesps, 
                "ped_decal_nodiff.sps" : ped_decal_nodiffsps, 
                "ped_default.sps" : ped_defaultsps, 
                "ped_default_cutout.sps" : ped_default_cutoutsps, 
                "ped_default_cloth.sps" : ped_default_clothsps, 
                "ped_default_enveff.sps" : ped_default_enveffsps, 
                "ped_default_mp.sps" : ped_default_mpsps, 
                "ped_default_palette.sps" : ped_default_palettesps, 
                "ped_emissive.sps" : ped_emissivesps, 
                "ped_enveff.sps" : ped_enveffsps, 
                "ped_fur.sps" : ped_fursps, 
                "ped_hair_cutout_alpha.sps" : ped_hair_cutout_alphasps, 
                "ped_hair_spiked.sps" : ped_hair_spikedsps, 
                "ped_nopeddamagedecals.sps" : ped_nopeddamagedecalssps, 
                "ped_palette.sps" : ped_palettesps, 
                "ped_wrinkle.sps" : ped_wrinklesps, 
                "ped_wrinkle_cloth.sps" : ped_wrinkle_clothsps, 
                "ped_wrinkle_cloth_enveff.sps" : ped_wrinkle_cloth_enveffsps, 
                "ped_wrinkle_cs.sps" : ped_wrinkle_cssps, 
                "ped_wrinkle_enveff.sps" : ped_wrinkle_enveffsps, 
                "ptfx_model.sps" : ptfx_modelsps, 
                "gta_radar.sps" : gta_radarsps, 
                "radar.sps" : radarsps, 
                "reflect.sps" : reflectsps, 
                "gta_reflect_alpha.sps" : gta_reflect_alphasps, 
                "reflect_alpha.sps" : reflect_alphasps, 
                "reflect_decal.sps" : reflect_decalsps, 
                "sky_system.sps" : sky_systemsps, 
                "gta_spec.sps" : gta_specsps, 
                "spec.sps" : specsps, 
                "spec_alpha.sps" : spec_alphasps, 
                "spec_screendooralpha.sps" : spec_screendooralphasps, 
                "spec_decal.sps" : spec_decalsps, 
                "spec_reflect.sps" : spec_reflectsps, 
                "spec_reflect_alpha.sps" : spec_reflect_alphasps, 
                "spec_reflect_decal.sps" : spec_reflect_decalsps, 
                "spec_tnt.sps" : spec_tntsps, 
                "cutout_spec_tnt.sps" : cutout_spec_tntsps, 
                "spec_twiddle_tnt.sps" : spec_twiddle_tntsps, 
                "terrain_cb_4lyr.sps" : terrain_cb_4lyrsps, 
                "terrain_cb_4lyr_2tex.sps" : terrain_cb_4lyr_2texsps, 
                "terrain_cb_w_4lyr.sps" : terrain_cb_w_4lyrsps, 
                "terrain_cb_w_4lyr_2tex.sps" : terrain_cb_w_4lyr_2texsps, 
                "terrain_cb_w_4lyr_2tex_blend.sps" : terrain_cb_w_4lyr_2tex_blendsps, 
                "terrain_cb_w_4lyr_2tex_blend_lod.sps" : terrain_cb_w_4lyr_2tex_blend_lodsps, 
                "terrain_cb_w_4lyr_2tex_blend_pxm.sps" : terrain_cb_w_4lyr_2tex_blend_pxmsps, 
                "terrain_cb_w_4lyr_2tex_blend_pxm_spm.sps" : terrain_cb_w_4lyr_2tex_blend_pxm_spmsps, 
                "terrain_cb_w_4lyr_2tex_pxm.sps" : terrain_cb_w_4lyr_2tex_pxmsps, 
                "terrain_cb_w_4lyr_cm.sps" : terrain_cb_w_4lyr_cmsps, 
                "terrain_cb_w_4lyr_cm_pxm.sps" : terrain_cb_w_4lyr_cm_pxmsps, 
                "terrain_cb_w_4lyr_cm_pxm_tnt.sps" : terrain_cb_w_4lyr_cm_pxm_tntsps, 
                "terrain_cb_w_4lyr_cm_tnt.sps" : terrain_cb_w_4lyr_cm_tntsps, 
                "terrain_cb_w_4lyr_lod.sps" : terrain_cb_w_4lyr_lodsps, 
                "terrain_cb_w_4lyr_pxm.sps" : terrain_cb_w_4lyr_pxmsps, 
                "terrain_cb_w_4lyr_pxm_spm.sps" : terrain_cb_w_4lyr_pxm_spmsps, 
                "terrain_cb_w_4lyr_spec.sps" : terrain_cb_w_4lyr_specsps, 
                "terrain_cb_w_4lyr_spec_int.sps" : terrain_cb_w_4lyr_spec_intsps, 
                "terrain_cb_w_4lyr_spec_int_pxm.sps" : terrain_cb_w_4lyr_spec_int_pxmsps, 
                "terrain_cb_w_4lyr_spec_pxm.sps" : terrain_cb_w_4lyr_spec_pxmsps, 
                "trees.sps" : treessps, 
                "trees_lod.sps" : trees_lodsps, 
                "trees_lod2.sps" : trees_lod2sps, 
                "trees_lod_tnt.sps" : trees_lod_tntsps, 
                "trees_normal.sps" : trees_normalsps, 
                "trees_normal_diffspec.sps" : trees_normal_diffspecsps, 
                "trees_normal_diffspec_tnt.sps" : trees_normal_diffspec_tntsps, 
                "trees_normal_spec.sps" : trees_normal_specsps, 
                "trees_normal_spec_tnt.sps" : trees_normal_spec_tntsps, 
                "trees_shadow_proxy.sps" : trees_shadow_proxysps, 
                "trees_tnt.sps" : trees_tntsps, 
                "vehicle_badges.sps" : vehicle_badgessps, 
                "vehicle_basic.sps" : vehicle_basicsps, 
                "vehicle_blurredrotor.sps" : vehicle_blurredrotorsps, 
                "vehicle_blurredrotor_emissive.sps" : vehicle_blurredrotor_emissivesps, 
                "vehicle_cloth.sps" : vehicle_clothsps, 
                "vehicle_cloth2.sps" : vehicle_cloth2sps, 
                "vehicle_cutout.sps" : vehicle_cutoutsps, 
                "vehicle_dash_emissive.sps" : vehicle_dash_emissivesps, 
                "vehicle_dash_emissive_opaque.sps" : vehicle_dash_emissive_opaquesps, 
                "vehicle_decal.sps" : vehicle_decalsps, 
                "vehicle_decal2.sps" : vehicle_decal2sps, 
                "vehicle_detail.sps" : vehicle_detailsps, 
                "vehicle_detail2.sps" : vehicle_detail2sps, 
                "vehicle_emissive_alpha.sps" : vehicle_emissive_alphasps, 
                "vehicle_emissive_opaque.sps" : vehicle_emissive_opaquesps, 
                "vehicle_generic.sps" : vehicle_genericsps, 
                "vehicle_interior.sps" : vehicle_interiorsps, 
                "vehicle_interior2.sps" : vehicle_interior2sps, 
                "vehicle_licenseplate.sps" : vehicle_licenseplatesps, 
                "vehicle_lightsemissive.sps" : vehicle_lightsemissivesps, 
                "vehicle_mesh.sps" : vehicle_meshsps, 
                "vehicle_mesh2_enveff.sps" : vehicle_mesh2_enveffsps, 
                "vehicle_mesh_enveff.sps" : vehicle_mesh_enveffsps, 
                "vehicle_paint1.sps" : vehicle_paint1sps, 
                "vehicle_nosplash.sps" : vehicle_nosplashsps, 
                "vehicle_nowater.sps" : vehicle_nowatersps, 
                "vehicle_paint1_enveff.sps" : vehicle_paint1_enveffsps, 
                "vehicle_paint2.sps" : vehicle_paint2sps, 
                "vehicle_paint2_enveff.sps" : vehicle_paint2_enveffsps, 
                "vehicle_paint3.sps" : vehicle_paint3sps, 
                "vehicle_paint3_enveff.sps" : vehicle_paint3_enveffsps, 
                "vehicle_paint3_lvr.sps" : vehicle_paint3_lvrsps, 
                "vehicle_paint4.sps" : vehicle_paint4sps, 
                "vehicle_paint4_emissive.sps" : vehicle_paint4_emissivesps, 
                "vehicle_paint4_enveff.sps" : vehicle_paint4_enveffsps, 
                "vehicle_paint5_enveff.sps" : vehicle_paint5_enveffsps, 
                "vehicle_paint6.sps" : vehicle_paint6sps, 
                "vehicle_paint6_enveff.sps" : vehicle_paint6_enveffsps, 
                "vehicle_paint7.sps" : vehicle_paint7sps, 
                "vehicle_paint7_enveff.sps" : vehicle_paint7_enveffsps, 
                "vehicle_paint8.sps" : vehicle_paint8sps, 
                "vehicle_paint9.sps" : vehicle_paint9sps, 
                "vehicle_shuts.sps" : vehicle_shutssps, 
                "vehicle_tire.sps" : vehicle_tiresps, 
                "vehicle_tire_emissive.sps" : vehicle_tire_emissivesps, 
                "vehicle_track.sps" : vehicle_tracksps, 
                "vehicle_track2.sps" : vehicle_track2sps, 
                "vehicle_track2_emissive.sps" : vehicle_track2_emissivesps, 
                "vehicle_track_ammo.sps" : vehicle_track_ammosps, 
                "vehicle_track_emissive.sps" : vehicle_track_emissivesps, 
                "vehicle_lights.sps" : vehicle_lightssps, 
                "vehicle_vehglass.sps" : vehicle_vehglasssps, 
                "vehicle_vehglass_inner.sps" : vehicle_vehglass_innersps, 
                "water_fountain.sps" : water_fountainsps, 
                "water_poolenv.sps" : water_poolenvsps, 
                "water_river.sps" : water_riversps, 
                "water_riverfoam.sps" : water_riverfoamsps, 
                "water_riverlod.sps" : water_riverlodsps, 
                "water_riverocean.sps" : water_riveroceansps, 
                "water_rivershallow.sps" : water_rivershallowsps, 
                "water_shallow.sps" : water_shallowsps, 
                "water_terrainfoam.sps" : water_terrainfoamsps, 
                "weapon_emissivestrong_alpha.sps" : weapon_emissivestrong_alphasps, 
                "weapon_emissive_tnt.sps" : weapon_emissive_tntsps, 
                "weapon_normal_spec_alpha.sps" : weapon_normal_spec_alphasps, 
                "weapon_normal_spec_cutout_palette.sps" : weapon_normal_spec_cutout_palettesps, 
                "weapon_normal_spec_detail_palette.sps" : weapon_normal_spec_detail_palettesps, 
                "weapon_normal_spec_detail_tnt.sps" : weapon_normal_spec_detail_tntsps, 
                "weapon_normal_spec_palette.sps" : weapon_normal_spec_palettesps, 
                "weapon_normal_spec_tnt.sps" : weapon_normal_spec_tntsps }

shaders_hash = {}

for k,v in shaders.items():
    h = JenkHash.Generate(k)
    name = 'hash_{:X}'.format(h)
    shaders_hash[name] = v

shaders.update(shaders_hash)

def get_child_node(node):
    
    if(node == None): 
        return None
    
    for output in node.outputs:
        if(len(output.links) == 1):
            return output.links[0].to_node

def get_list_of_child_nodes(node):
    
    all_nodes = []
    all_nodes.append(node)
    
    searching = True 
    child = get_child_node(node)
    
    while(searching):        
        
        
        if(isinstance(child, bpy.types.ShaderNodeBsdfPrincipled)):
            pass
        elif(isinstance(child, bpy.types.ShaderNodeOutputMaterial)):
            pass
        else:
            all_nodes.append(child)
        
        child = get_child_node(child)
        
        if(child == None):
            searching = False
            
        
        
    return all_nodes

def check_if_node_has_child(node):
    
    haschild = False    
    for output in node.outputs:
        if(len(output.links) > 0):
                    haschild = True
    return haschild

def organize_node_tree(node_tree):
    
    level = 0
    singles_x = 0

    grid_x = 600
    grid_y = -300
    row_count = 0
    
    for n in node_tree.nodes:
        
        if(isinstance(n, bpy.types.ShaderNodeValue)):
            n.location.x = grid_x
            n.location.y = grid_y
            grid_x += 150
            row_count += 1
            if(row_count == 4):
                grid_y -= 100
                row_count = 0
                grid_x = 600
                
        if(isinstance(n, bpy.types.ShaderNodeBsdfPrincipled)):
            n.location.x = 0 
            n.location.y = -300
        if(isinstance(n, bpy.types.ShaderNodeOutputMaterial)):
            n.location.y = -300 
            n.location.x = 300
        
        if(isinstance(n, bpy.types.ShaderNodeTexImage)):
            
            haschild = check_if_node_has_child(n)
            if(haschild):
                level -= 250
                all_nodes = get_list_of_child_nodes(n)
                
                idx = 0
                for n in all_nodes:
                    try:
                        x = -300 * (len(all_nodes) - idx)
                        
                        n.location.x = x
                        n.location.y = level 
                        
                        idx += 1
                    except: 
                        print("error")
            else:
                n.location.x = singles_x
                n.location.y = 100
                singles_x += 300

def create_image_node(node_tree, param):
    
    imgnode = node_tree.nodes.new("ShaderNodeTexImage")
    imgnode.name = param.Name
    #imgnode.img = param.DefaultValue
    bsdf = node_tree.nodes["Principled BSDF"]
    links = node_tree.links

    if("Diffuse" in param.Name):    
        links.new(imgnode.outputs["Color"], bsdf.inputs["Base Color"])
        links.new(imgnode.outputs["Alpha"], bsdf.inputs["Alpha"])
    elif("Bump" in param.Name):    
        normalmap = node_tree.nodes.new("ShaderNodeNormalMap")
        links.new(imgnode.outputs["Color"], normalmap.inputs["Color"])
        links.new(normalmap.outputs["Normal"], bsdf.inputs["Normal"])
    elif("Spec" in param.Name):    
        links.new(imgnode.outputs["Color"], bsdf.inputs["Specular"])

def create_value_node(node_tree, param):
    
    vnodex = node_tree.nodes.new("ShaderNodeValue")
    vnodex.name = param.Name + "_x"
    vnodex.outputs[0].default_value = param.X
    
    vnodey = node_tree.nodes.new("ShaderNodeValue")
    vnodey.name = param.Name + "_y"
    vnodey.outputs[0].default_value = param.Y
    
    vnodez = node_tree.nodes.new("ShaderNodeValue")
    vnodez.name = param.Name + "_z"
    vnodez.outputs[0].default_value = param.Z
    
    vnodew = node_tree.nodes.new("ShaderNodeValue")
    vnodew.name = param.Name + "_w"
    vnodew.outputs[0].default_value = param.W

def link_terrain_shader(node_tree):
    
    links = node_tree.links
    vcnode = node_tree.nodes.new("ShaderNodeAttribute")
    vcnode.attribute_name = "Vertex illumiation"
    seprgbnode = node_tree.nodes.new("ShaderNodeSeparateRGB")
    links.new(vcnode.outputs[0], seprgbnode.inputs["Image"])
    
    #tex0
    lt1 = node_tree.nodes.new("ShaderNodeMath")
    lt1.operation = "LESS_THAN"
    links.new(seprgbnode.outputs["G"], lt1.inputs["Value"])
    lt2 = node_tree.nodes.new("ShaderNodeMath")
    lt2.operation = "LESS_THAN"
    links.new(seprgbnode.outputs["B"], lt2.inputs["Value"])
    m1 = node_tree.nodes.new("ShaderNodeMath")
    m1.operation = "MULTIPLY"
    links.new(lt1.outputs["Value"], m1.inputs[0])
    links.new(lt2.outputs["Value"], m1.inputs[1])
        
    #tex1
    lt3 = node_tree.nodes.new("ShaderNodeMath")
    lt3.operation = "GREATER_THAN"
    links.new(seprgbnode.outputs["B"], lt3.inputs["Value"])
    lt4 = node_tree.nodes.new("ShaderNodeMath")
    lt4.operation = "LESS_THAN"
    links.new(seprgbnode.outputs["G"], lt4.inputs["Value"])
    m2 = node_tree.nodes.new("ShaderNodeMath")
    m2.operation = "MULTIPLY"
    links.new(lt3.outputs["Value"], m2.inputs[0])
    links.new(lt4.outputs["Value"], m2.inputs[1])
    
    #tex2
    lt5 = node_tree.nodes.new("ShaderNodeMath")
    lt5.operation = "GREATER_THAN"
    links.new(seprgbnode.outputs["G"], lt5.inputs["Value"])
    lt6 = node_tree.nodes.new("ShaderNodeMath")
    lt6.operation = "LESS_THAN"
    links.new(seprgbnode.outputs["B"], lt6.inputs["Value"])
    m3 = node_tree.nodes.new("ShaderNodeMath")
    m3.operation = "MULTIPLY"
    links.new(lt5.outputs["Value"], m3.inputs[0])
    links.new(lt6.outputs["Value"], m3.inputs[1])
    
    ts1 = node_tree.nodes["TextureSampler_layer0"]
    ts2 = node_tree.nodes["TextureSampler_layer1"]
    ts3 = node_tree.nodes["TextureSampler_layer2"]
    ts4 = node_tree.nodes["TextureSampler_layer3"]
    
    mix1 = node_tree.nodes.new("ShaderNodeMixRGB")
    mix2 = node_tree.nodes.new("ShaderNodeMixRGB")
    mix3 = node_tree.nodes.new("ShaderNodeMixRGB")
    
    links.new(ts1.outputs["Color"], mix1.inputs["Color1"])
    links.new(ts2.outputs["Color"], mix1.inputs["Color2"])
    links.new(mix1.outputs["Color"], mix2.inputs["Color1"])
    links.new(ts3.outputs["Color"], mix2.inputs["Color2"])
    links.new(mix2.outputs["Color"], mix3.inputs["Color1"])
    links.new(ts4.outputs["Color"], mix3.inputs["Color2"])
    
    links.new(m1.outputs["Value"], mix1.inputs["Fac"])
    links.new(m2.outputs["Value"], mix2.inputs["Fac"])
    links.new(m3.outputs["Value"], mix3.inputs["Fac"])
    
    links.new(mix3.outputs["Color"], node_tree.nodes["Material Output"].inputs["Surface"])

def create(shadername, context):
    
    if(shadername in shaders):
        
        mat = bpy.data.materials.new(shadername)
        mat.use_nodes = True
        
        parameter_set = shaders[shadername]
        node_tree = mat.node_tree
                
        for p in parameter_set:
            if(p.Type == "Image"):
                create_image_node(node_tree, p)
            elif(p.Type == "Value"):
                create_value_node(node_tree, p)
        
        #temporary also find a better way to do this... even though it kinda works
        if("terrain" in shadername.lower()):
            link_terrain_shader(mat.node_tree)
        
        #organize nodes for now just spread them apart :P
        #location = Vector((0, 0))
        #for node in mat.node_tree.nodes:
            #node.location = location
            #location.x += 180   
        
        organize_node_tree(node_tree)
        
        mat.sollumtype = "GTA"
        bpy.context.scene.last_created_material = mat
        
class SOLLUM_OT_createvshader(bpy.types.Operator):
    """Creates a vshader"""
    bl_idname = "sollum.createvshader"
    bl_label = "Create Shader"
    shadername : bpy.props.StringProperty(default = "default.sps")

    def execute(self, context):
        create(self.shadername, context)
        return {'FINISHED'}

def convert(self, context):
    obj = context.active_object 
    mat = obj.active_material 
    
    #if(mat.sollumtype == "GTA"):
    #   print("ALREADY A GTA MATERIAL SHADER")
    
    o_nodes = mat.node_tree.nodes 
    bsdf_node = None 
    
    for node in o_nodes:
        if(node.name == "Principled BSDF"):
            bsdf_node = node 
    
    if(bsdf_node == None):
        self.report({'ERROR'}, "No BSDF node located please adjust material for conversion")
        return 
    
    bsdf_ls = bsdf_node.inputs["Base Color"].links
    
    o_img_node = None
    if(len(bsdf_ls) > 0):
        o_img_node = bsdf_ls[0].from_node 
        
    if(o_img_node == None):
        self.report({"ERROR"}, "No image node connected to base color bsdf")
        return
        
    bpy.ops.sollum.createvshader()
    
    
    n_mat = obj.material_slots[len(obj.material_slots) - 1].material #gets last appended materials to a object
    bpy.ops.object.material_slot_remove() #call this to remove the old material
    
    n_nodes = n_mat.node_tree.nodes
    
    for node in n_nodes:
        if(node.name == "DiffuseSampler"):
            node.image = o_img_node.image 
    
    if(obj != None):
        obj.active_material = n_mat
    
class ConvertToVShader(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "sollum.converttov"
    bl_label = "Convert To GTA Shader"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        convert(self, context)
        return {'FINISHED'}

def register():
    bpy.utils.register_class(SOLLUM_OT_createvshader)
    bpy.utils.register_class(ConvertToVShader)
def unregister():
    bpy.utils.unregister_class(SOLLUM_OT_createvshader)
    bpy.utils.unregister_class(ConvertToVShader)
