import bpy
from mathutils import Vector
from .tools import jenkhash as JenkHash

class shader_parameter:
    
    def __init__(self, type, name, x = None, y = None, z = None, w = None):
        self.Type = type
        self.Name = name    
        self.X = x
        self.Y = y
        self.Z = z
        self.W = w

blend_2lyrsps = [
                shader_parameter("Image", "TextureSampler_layer0"),
                shader_parameter("Image", "BumpSampler_layer0"),
                shader_parameter("Image", "TextureSampler_layer1"),
                shader_parameter("Image", "BumpSampler_layer1"),
                shader_parameter("Image", "LookupSampler"),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 32.0, 0.0, 0.0, 0.0)]

cablesps = [
                shader_parameter("Value", "TextureSamp"),
                shader_parameter("Value", "AlphaTestValue", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gCableParams", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gViewProj", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Shader_cableEmissive", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Shader_cableAmbient", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Shader_cableDiffuse2", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Shader_cableDiffuse", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Shader_windAmount", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Shader_fadeExponent", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Shader_radiusScale", 1.0, 0.0, 0.0, 0.0)]

cloth_defaultsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0)]

cloth_normal_specsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

cloth_normal_spec_alphasps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

cloth_normal_spec_cutoutsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

cloth_normal_spec_tntsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "TintPaletteSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

cloth_spec_alphasps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

cloth_spec_cutoutsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

clouds_altitudesps = [
                shader_parameter("Image", "DensitySampler"),
                shader_parameter("Image", "NormalSampler"),
                shader_parameter("Image", "DetailDensitySampler"),
                shader_parameter("Image", "DetailNormalSampler"),
                shader_parameter("Image", "DetailDensity2Sampler"),
                shader_parameter("Image", "DetailNormal2Sampler"),
                shader_parameter("Image", "DepthMapTexSampler"),
                shader_parameter("Value", "CloudLayerAnimScale3", 1.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "CloudLayerAnimScale2", 1.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "CloudLayerAnimScale1", 1.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "gSoftParticleRange", 175.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gRescaleUV3", 1.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "gRescaleUV2", 1.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "gRescaleUV1", 1.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "gUVOffset3", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gUVOffset2", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gUVOffset1", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gCameraPos", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gCloudViewProj", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gUVOffset", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gAnimBlendWeights", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gAnimSculpt", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gAnimCombine", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "gNearFarQMult", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gWrapLighting_MSAARef", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "gScaleDiffuseFillAmbient", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "gPiercingLightPower_Strength_NormalStrength_Thickness", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "gScatterG_GSquared_PhaseMult_Scale", -0.75, 0.5625, 2.1, 1.0),
                shader_parameter("Value", "gDensityShiftScale", 0.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "gBounceColor", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gAmbientColor", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gCloudColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "gSunColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "gSunDirection", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gWestColor", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gEastMinusWestColor", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gSkyColor", 0.0, 0.0, 0.0, 0.0)]

clouds_animsps = [
                shader_parameter("Image", "DensitySampler"),
                shader_parameter("Image", "NormalSampler"),
                shader_parameter("Image", "DetailDensitySampler"),
                shader_parameter("Image", "DetailNormalSampler"),
                shader_parameter("Image", "DetailDensity2Sampler"),
                shader_parameter("Image", "DetailNormal2Sampler"),
                shader_parameter("Image", "DepthMapTexSampler"),
                shader_parameter("Value", "CloudLayerAnimScale3", 1.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "CloudLayerAnimScale2", 1.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "CloudLayerAnimScale1", 1.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "gSoftParticleRange", 175.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gRescaleUV3", 1.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "gRescaleUV2", 1.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "gRescaleUV1", 1.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "gUVOffset3", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gUVOffset2", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gUVOffset1", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gCameraPos", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gCloudViewProj", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gUVOffset", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gAnimBlendWeights", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gAnimSculpt", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gAnimCombine", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "gNearFarQMult", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gWrapLighting_MSAARef", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "gScaleDiffuseFillAmbient", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "gPiercingLightPower_Strength_NormalStrength_Thickness", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "gScatterG_GSquared_PhaseMult_Scale", -0.75, 0.5625, 2.1, 1.0),
                shader_parameter("Value", "gDensityShiftScale", 0.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "gBounceColor", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gAmbientColor", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gCloudColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "gSunColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "gSunDirection", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gWestColor", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gEastMinusWestColor", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gSkyColor", 0.0, 0.0, 0.0, 0.0)]

clouds_animsoftsps = [
                shader_parameter("Image", "DensitySampler"),
                shader_parameter("Image", "NormalSampler"),
                shader_parameter("Image", "DetailDensitySampler"),
                shader_parameter("Image", "DetailNormalSampler"),
                shader_parameter("Image", "DetailDensity2Sampler"),
                shader_parameter("Image", "DetailNormal2Sampler"),
                shader_parameter("Image", "DepthMapTexSampler"),
                shader_parameter("Value", "CloudLayerAnimScale3", 1.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "CloudLayerAnimScale2", 1.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "CloudLayerAnimScale1", 1.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "gSoftParticleRange", 175.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gRescaleUV3", 1.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "gRescaleUV2", 1.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "gRescaleUV1", 1.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "gUVOffset3", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gUVOffset2", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gUVOffset1", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gCameraPos", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gCloudViewProj", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gUVOffset", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gAnimBlendWeights", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gAnimSculpt", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gAnimCombine", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "gNearFarQMult", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gWrapLighting_MSAARef", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "gScaleDiffuseFillAmbient", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "gPiercingLightPower_Strength_NormalStrength_Thickness", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "gScatterG_GSquared_PhaseMult_Scale", -0.75, 0.5625, 2.1, 1.0),
                shader_parameter("Value", "gDensityShiftScale", 0.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "gBounceColor", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gAmbientColor", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gCloudColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "gSunColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "gSunDirection", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gWestColor", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gEastMinusWestColor", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gSkyColor", 0.0, 0.0, 0.0, 0.0)]

clouds_fastsps = [
                shader_parameter("Image", "DensitySampler"),
                shader_parameter("Image", "NormalSampler"),
                shader_parameter("Value", "CloudLayerAnimScale3", 1.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "CloudLayerAnimScale2", 1.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "CloudLayerAnimScale1", 1.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "gRescaleUV3", 1.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "gRescaleUV2", 1.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "gRescaleUV1", 1.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "gUVOffset3", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gUVOffset2", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gUVOffset1", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gCameraPos", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gCloudViewProj", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gUVOffset", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gWrapLighting_MSAARef", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "gScaleDiffuseFillAmbient", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "gPiercingLightPower_Strength_NormalStrength_Thickness", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "gScatterG_GSquared_PhaseMult_Scale", -0.75, 0.5625, 2.1, 1.0),
                shader_parameter("Value", "gDensityShiftScale", 0.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "gBounceColor", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gAmbientColor", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gCloudColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "gSunColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "gSunDirection", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gWestColor", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gEastMinusWestColor", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gSkyColor", 0.0, 0.0, 0.0, 0.0)]

clouds_fogsps = [
                shader_parameter("Image", "DensitySampler"),
                shader_parameter("Image", "NormalSampler"),
                shader_parameter("Image", "DepthMapTexSampler"),
                shader_parameter("Value", "CloudLayerAnimScale3", 1.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "CloudLayerAnimScale2", 1.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "CloudLayerAnimScale1", 1.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "gSoftParticleRange", 175.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gRescaleUV3", 1.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "gRescaleUV2", 1.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "gRescaleUV1", 1.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "gUVOffset3", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gUVOffset2", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gUVOffset1", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gCameraPos", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gCloudViewProj", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gUVOffset", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gNearFarQMult", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gWrapLighting_MSAARef", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "gScaleDiffuseFillAmbient", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "gPiercingLightPower_Strength_NormalStrength_Thickness", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "gDensityShiftScale", 0.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "gBounceColor", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gAmbientColor", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gCloudColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "gSunColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "gSunDirection", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gWestColor", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gEastMinusWestColor", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gSkyColor", 0.0, 0.0, 0.0, 0.0)]

clouds_softsps = [
                shader_parameter("Image", "DensitySampler"),
                shader_parameter("Image", "NormalSampler"),
                shader_parameter("Image", "DepthMapTexSampler"),
                shader_parameter("Value", "CloudLayerAnimScale3", 1.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "CloudLayerAnimScale2", 1.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "CloudLayerAnimScale1", 1.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "gSoftParticleRange", 175.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gRescaleUV3", 1.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "gRescaleUV2", 1.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "gRescaleUV1", 1.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "gUVOffset3", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gUVOffset2", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gUVOffset1", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gCameraPos", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gCloudViewProj", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gUVOffset", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gNearFarQMult", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gWrapLighting_MSAARef", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "gScaleDiffuseFillAmbient", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "gPiercingLightPower_Strength_NormalStrength_Thickness", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "gScatterG_GSquared_PhaseMult_Scale", -0.75, 0.5625, 2.1, 1.0),
                shader_parameter("Value", "gDensityShiftScale", 0.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "gBounceColor", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gAmbientColor", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gCloudColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "gSunColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "gSunDirection", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gWestColor", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gEastMinusWestColor", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gSkyColor", 0.0, 0.0, 0.0, 0.0)]

cpv_onlysps = [
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0)]

cutout_fencesps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0)]

cutout_fence_normalsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

cutout_hardsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0)]

decalsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

decal_amb_onlysps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "AmbientDecalMask", 1.0, 0.0, 0.0, 0.0)]

decal_diff_only_umsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "umGlobalOverrideParams", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "umGlobalParams", 0.025, 0.025, 1.0, 1.0)]

decal_dirtsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DirtDecalMask", 1.0, 0.0, 0.0, 0.0)]

decal_emissivenight_onlysps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "EmissiveMultiplier", 1.0, 0.0, 0.0, 0.0)]

decal_emissive_onlysps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "EmissiveMultiplier", 1.0, 0.0, 0.0, 0.0)]

decal_gluesps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

decal_normal_onlysps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

decal_shadow_onlysps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0)]

decal_spec_onlysps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

decal_tntsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "TintPaletteSampler"),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

custom_defaultsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

defaultsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

default_noedgesps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

gta_defaultsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

alphasps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

cutoutsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

default_detailsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DetailSampler"),
                shader_parameter("Value", "DetailSettings", 0.0, 0.0, 24.0, 24.0),
                shader_parameter("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0)]

default_specsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

spec_constsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

default_terrain_wetsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

default_tntsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "TintPaletteSampler"),
                shader_parameter("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

cutout_tntsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "TintPaletteSampler"),
                shader_parameter("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

default_umsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "umGlobalOverrideParams", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "umGlobalParams", 0.025, 0.025, 1.0, 1.0)]

cutout_umsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "umGlobalOverrideParams", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "umGlobalParams", 0.025, 0.025, 1.0, 1.0)]

distance_mapsps = [
                shader_parameter("Image", "DistanceMapSampler"),
                shader_parameter("Value", "FillColor", 0.0, 0.0, 1.0, 0.0)]

emissivesps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "EmissiveMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

emissive_alphasps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "EmissiveMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

emissivenightsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "EmissiveMultiplier", 1.0, 0.0, 0.0, 0.0)]

emissivenight_alphasps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "EmissiveMultiplier", 1.0, 0.0, 0.0, 0.0)]

emissivenight_geomnightonlysps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "EmissiveMultiplier", 1.0, 0.0, 0.0, 0.0)]

emissivestrongsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "EmissiveMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

emissivestrong_alphasps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "EmissiveMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

emissive_additive_alphasps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "EmissiveMultiplier", 1.0, 0.0, 0.0, 0.0)]

emissive_additive_uv_alphasps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "EmissiveMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

emissive_clipsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "EmissiveMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

emissive_speclumsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "EmissiveMultiplier", 1.0, 0.0, 0.0, 0.0)]

emissive_tntsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "TintPaletteSampler"),
                shader_parameter("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "EmissiveMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

emissive_alpha_tntsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "TintPaletteSampler"),
                shader_parameter("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "EmissiveMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

glasssps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "EnvironmentSampler"),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

glass_breakablesps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "DecalTint", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "CrackDecalBumpAlphaThreshold", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "CrackDecalBumpAmount", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "CrackEdgeBumpAmount", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "CrackDecalBumpTileScale", 1.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "CrackEdgeBumpTileScale", 1.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "BrokenSpecularColor", 0.46, 0.6117647, 0.6117647, 1.0),
                shader_parameter("Value", "BrokenDiffuseColor", 0.46, 0.6117647, 0.6117647, 0.5686275),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

glass_breakable_screendooralphasps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "DecalTint", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "CrackDecalBumpAlphaThreshold", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "CrackDecalBumpAmount", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "CrackEdgeBumpAmount", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "CrackDecalBumpTileScale", 1.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "CrackEdgeBumpTileScale", 1.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "BrokenSpecularColor", 0.46, 0.6117647, 0.6117647, 1.0),
                shader_parameter("Value", "BrokenDiffuseColor", 0.46, 0.6117647, 0.6117647, 0.5686275),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

glass_displacementsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Image", "EnvironmentSampler"),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "displParams", 16.0, 16.0, 15.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

glass_emissivesps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "EnvironmentSampler"),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "EmissiveMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

glass_emissive_alphasps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "EnvironmentSampler"),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "EmissiveMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

glass_emissivenightsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "EnvironmentSampler"),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "EmissiveMultiplier", 1.0, 0.0, 0.0, 0.0)]

glass_emissivenight_alphasps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "EnvironmentSampler"),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "EmissiveMultiplier", 1.0, 0.0, 0.0, 0.0)]

glass_envsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

glass_normal_spec_reflectsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Image", "EnvironmentSampler"),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

glass_pvsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Value", "DecalTint", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "CrackDecalBumpAlphaThreshold", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "CrackDecalBumpAmount", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "CrackEdgeBumpAmount", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "CrackDecalBumpTileScale", 1.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "CrackEdgeBumpTileScale", 1.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "BrokenSpecularColor", 0.46, 0.6117647, 0.6117647, 1.0),
                shader_parameter("Value", "BrokenDiffuseColor", 0.46, 0.6117647, 0.6117647, 0.5686275),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

glass_pv_envsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Value", "DecalTint", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "CrackDecalBumpAlphaThreshold", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "CrackDecalBumpAmount", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "CrackEdgeBumpAmount", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "CrackDecalBumpTileScale", 1.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "CrackEdgeBumpTileScale", 1.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "BrokenSpecularColor", 0.46, 0.6117647, 0.6117647, 1.0),
                shader_parameter("Value", "BrokenDiffuseColor", 0.46, 0.6117647, 0.6117647, 0.5686275),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

glass_reflectsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "EnvironmentSampler"),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

glass_specsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

grasssps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "TextureGrassSampler"),
                shader_parameter("Value", "gAlphaToCoverageScale", 1.3, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ShadowFalloff", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "AlphaTest", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "AlphaScale", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "_fakedGrassNormal", 0.0, 0.0, 1.0, 1.0),
                shader_parameter("Value", "uMovementParams", 0.05, 0.05, 0.2125, 0.2125),
                shader_parameter("Value", "FadeAlphaLOD2DistFar0", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "FadeAlphaLOD2Dist", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "FadeAlphaLOD1Dist", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "FadeAlphaDistUmTimer", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "_vecVehColl3R", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "_vecVehColl3M", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "_vecVehColl3B", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "_vecVehColl2R", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "_vecVehColl2M", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "_vecVehColl2B", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "_vecVehColl1R", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "_vecVehColl1M", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "_vecVehColl1B", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "_vecVehColl0R", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "_vecVehColl0M", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "_vecVehColl0B", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "_vecCollParams", 0.5625, 1.777778, 0.0, 0.0),
                shader_parameter("Value", "_dimensionLOD2", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "vecPlayerPos", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "vecCameraPos", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "GroundColor"),
                shader_parameter("Value", "PlantColor", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "matGrassTransform", 0.0, 0.0, 0.0, 0.0)]

grass_batchsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Value", "gLodFadeTileScale", 1.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "gLodFadePower", 1.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "gLodFadeRange", 0.05, 0.05, 0.0, 0.0),
                shader_parameter("Value", "gLodFadeStartDist", -1.0, -1.0, 0.0, 0.0),
                shader_parameter("Value", "gAlphaToCoverageScale", 1.3, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gAlphaTest", 0.25, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gWindBendScaleVar", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gWindBendingGlobals", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gScaleRange", 1.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "_fakedGrassNormal", 0.0, 0.0, 1.0, 1.0),
                shader_parameter("Value", "uMovementParams", 0.05, 0.05, 0.2125, 0.2125),
                shader_parameter("Value", "FadeAlphaDistUmTimer", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "_vecVehColl3R", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "_vecVehColl3M", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "_vecVehColl3B", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "_vecVehColl2R", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "_vecVehColl2M", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "_vecVehColl2B", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "_vecVehColl1R", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "_vecVehColl1M", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "_vecVehColl1B", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "_vecVehColl0R", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "_vecVehColl0M", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "_vecVehColl0B", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "_vecCollParams", 0.5625, 1.777778, 0.0, 0.0),
                shader_parameter("Value", "vecPlayerPos", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "vecBatchAabbDelta", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "vecBatchAabbMin", 0.0, 0.0, 0.0, 0.0)]

grass_fursps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Image", "ComboHeightSamplerFur01"),
                shader_parameter("Image", "ComboHeightSamplerFur23"),
                shader_parameter("Image", "ComboHeightSamplerFur45"),
                shader_parameter("Image", "ComboHeightSamplerFur67"),
                shader_parameter("Image", "StippleSampler"),
                shader_parameter("Value", "FurShadow47", 0.7843137, 0.8627451, 0.9333333, 1.0),
                shader_parameter("Value", "FurShadow03", 0.3529412, 0.4627451, 0.5803922, 0.6588235),
                shader_parameter("Value", "FurAlphaClip47", 0.07843138, 0.09803922, 0.1176471, 0.1333333),
                shader_parameter("Value", "FurAlphaClip03", 0.0, 0.03921569, 0.03921569, 0.05882353),
                shader_parameter("Value", "FurAlphaDistance", 10.0, 25.0, 0.0, 0.0),
                shader_parameter("Value", "FurUvScales", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "FurLayerParams", 0.008, 0.0, 0.0, 1.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

grass_fur_masksps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Image", "ComboHeightSamplerFur01"),
                shader_parameter("Image", "ComboHeightSamplerFur23"),
                shader_parameter("Image", "ComboHeightSamplerFur45"),
                shader_parameter("Image", "ComboHeightSamplerFur67"),
                shader_parameter("Image", "FurMaskSampler"),
                shader_parameter("Image", "DiffuseHfSampler"),
                shader_parameter("Image", "StippleSampler"),
                shader_parameter("Value", "FurShadow47", 0.7843137, 0.8627451, 0.9333333, 1.0),
                shader_parameter("Value", "FurShadow03", 0.3529412, 0.4627451, 0.5803922, 0.6588235),
                shader_parameter("Value", "FurAlphaClip47", 0.07843138, 0.09803922, 0.1176471, 0.1333333),
                shader_parameter("Value", "FurAlphaClip03", 0.0, 0.03921569, 0.03921569, 0.05882353),
                shader_parameter("Value", "FurAlphaDistance", 10.0, 25.0, 0.0, 0.0),
                shader_parameter("Value", "FurUvScales", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "FurLayerParams", 0.008, 0.0, 0.0, 1.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

minimapsps = [
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0)]

mirror_cracksps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "gMirrorCrackSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "gMirrorBounds", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gMirrorCrackAmount", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0)]

mirror_decalsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Value", "gMirrorBounds", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "gMirrorDistortionAmount", 32.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

mirror_defaultsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "gMirrorBounds", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0)]

gta_normalsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

normalsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

normal_alphasps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

water_decalsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

normal_cutoutsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

normal_screendooralphasps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

normal_cubemap_reflectsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "EnvironmentSampler"),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0)]

normal_decalsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

normal_decal_pxmsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "HeightSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ParallaxSelfShadowAmount", 0.95, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightBias", 0.015, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightScale", 0.03, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

normal_decal_pxm_tntsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "TintPaletteSampler"),
                shader_parameter("Image", "HeightSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ParallaxSelfShadowAmount", 0.95, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightBias", 0.015, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightScale", 0.03, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

normal_decal_tntsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "TintPaletteSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

normal_detailsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DetailSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Value", "DetailSettings", 0.0, 0.0, 24.0, 24.0),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

normal_detail_dpmsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DetailSampler"),
                shader_parameter("Image", "HeightSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Value", "DetailSettings", 0.0, 0.0, 24.0, 24.0),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightBias", -0.5, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightScale", 0.4, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "TessellationMultiplier", 1.0, 0.0, 0.0, 0.0)]

normal_diffspecsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecDesaturateExponent", 0.3, 0.6, 0.1, 0.0625),
                shader_parameter("Value", "SpecDesaturateIntensity", 0.3, 0.6, 0.1, 0.0625),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

normal_diffspec_detailsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DetailSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Value", "DetailSettings", 0.0, 0.0, 24.0, 24.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecDesaturateExponent", 0.3, 0.6, 0.1, 0.0625),
                shader_parameter("Value", "SpecDesaturateIntensity", 0.3, 0.6, 0.1, 0.0625),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

normal_diffspec_detail_dpmsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DetailSampler"),
                shader_parameter("Image", "HeightSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Value", "DetailSettings", 0.0, 0.0, 24.0, 24.0),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightBias", -0.5, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightScale", 0.4, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecDesaturateExponent", 0.3, 0.6, 0.1, 0.0625),
                shader_parameter("Value", "SpecDesaturateIntensity", 0.3, 0.6, 0.1, 0.0625),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "TessellationMultiplier", 1.0, 0.0, 0.0, 0.0)]

normal_diffspec_detail_dpm_tntsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "TintPaletteSampler"),
                shader_parameter("Image", "DetailSampler"),
                shader_parameter("Image", "HeightSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Value", "DetailSettings", 0.0, 0.0, 24.0, 24.0),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightBias", -0.5, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightScale", 0.4, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecDesaturateExponent", 0.3, 0.6, 0.1, 0.0625),
                shader_parameter("Value", "SpecDesaturateIntensity", 0.3, 0.6, 0.1, 0.0625),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "TessellationMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

normal_diffspec_detail_tntsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "TintPaletteSampler"),
                shader_parameter("Image", "DetailSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Value", "DetailSettings", 0.0, 0.0, 24.0, 24.0),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecDesaturateExponent", 0.3, 0.6, 0.1, 0.0625),
                shader_parameter("Value", "SpecDesaturateIntensity", 0.3, 0.6, 0.1, 0.0625),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

normal_diffspec_tntsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "TintPaletteSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecDesaturateExponent", 0.3, 0.6, 0.1, 0.0625),
                shader_parameter("Value", "SpecDesaturateIntensity", 0.3, 0.6, 0.1, 0.0625),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

normal_pxmsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "HeightSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ParallaxSelfShadowAmount", 0.95, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightBias", 0.015, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightScale", 0.03, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

normal_pxm_tntsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "TintPaletteSampler"),
                shader_parameter("Image", "HeightSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ParallaxSelfShadowAmount", 0.95, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightBias", 0.015, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightScale", 0.03, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

normal_tnt_pxmsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "TintPaletteSampler"),
                shader_parameter("Image", "HeightSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ParallaxSelfShadowAmount", 0.95, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightBias", 0.015, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightScale", 0.03, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

normal_reflectsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "EnvironmentSampler"),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0)]

normal_reflect_alphasps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "EnvironmentSampler"),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0)]

normal_reflect_screendooralphasps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "EnvironmentSampler"),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0)]

normal_reflect_decalsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "EnvironmentSampler"),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0)]

normal_specsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

normal_spec_alphasps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

normal_spec_cutoutsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

normal_spec_screendooralphasps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

normal_spec_batchsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "gLodFadeTileScale", 1.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "gLodFadePower", 1.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "gLodFadeRange", 0.05, 0.05, 0.0, 0.0),
                shader_parameter("Value", "gLodFadeStartDist", -1.0, -1.0, 0.0, 0.0),
                shader_parameter("Value", "vecBatchAabbMin", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

normal_spec_cubemap_reflectsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Image", "EnvironmentSampler"),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

normal_spec_decalsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

normal_spec_decal_detailsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DetailSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "DetailSettings", 0.0, 0.0, 24.0, 24.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

normal_spec_decal_nopuddlesps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

normal_spec_decal_pxmsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "HeightSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ParallaxSelfShadowAmount", 0.95, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightBias", 0.015, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightScale", 0.03, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

normal_spec_decal_tntsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "TintPaletteSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

normal_spec_detailsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DetailSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "DetailSettings", 0.0, 0.0, 24.0, 24.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

normal_spec_detail_dpmsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DetailSampler"),
                shader_parameter("Image", "HeightSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "DetailSettings", 0.0, 0.0, 24.0, 24.0),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightBias", -0.5, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightScale", 0.4, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "TessellationMultiplier", 1.0, 0.0, 0.0, 0.0)]

normal_spec_detail_dpm_tntsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "TintPaletteSampler"),
                shader_parameter("Image", "DetailSampler"),
                shader_parameter("Image", "HeightSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "DetailSettings", 0.0, 0.0, 24.0, 24.0),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightBias", -0.5, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightScale", 0.4, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "TessellationMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

normal_spec_detail_dpm_vertdecal_tntsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "TintPaletteSampler"),
                shader_parameter("Image", "DetailSampler"),
                shader_parameter("Image", "HeightSampler"),
                shader_parameter("Image", "DiffuseSampler2"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "DetailSettings", 0.0, 0.0, 24.0, 24.0),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightBias", -0.5, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightScale", 0.4, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "TessellationMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

normal_spec_detail_tntsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "TintPaletteSampler"),
                shader_parameter("Image", "DetailSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "DetailSettings", 0.0, 0.0, 24.0, 24.0),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

normal_spec_dpmsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "HeightSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightBias", -0.5, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightScale", 0.4, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "TessellationMultiplier", 1.0, 0.0, 0.0, 0.0)]

normal_spec_emissivesps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "EmissiveMultiplier", 1.0, 0.0, 0.0, 0.0)]

normal_spec_pxmsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "HeightSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ParallaxSelfShadowAmount", 0.95, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightBias", 0.015, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightScale", 0.03, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

normal_spec_pxm_tntsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "TintPaletteSampler"),
                shader_parameter("Image", "HeightSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ParallaxSelfShadowAmount", 0.95, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightBias", 0.015, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightScale", 0.03, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

normal_spec_tnt_pxmsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "TintPaletteSampler"),
                shader_parameter("Image", "HeightSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ParallaxSelfShadowAmount", 0.95, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightBias", 0.015, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightScale", 0.03, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

normal_spec_reflectsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Image", "EnvironmentSampler"),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

normal_spec_reflect_alphasps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Image", "EnvironmentSampler"),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

normal_spec_reflect_decalsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Image", "EnvironmentSampler"),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

normal_spec_reflect_emissivenightsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "EmissiveMultiplier", 1.0, 0.0, 0.0, 0.0)]

normal_spec_reflect_emissivenight_alphasps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "EmissiveMultiplier", 1.0, 0.0, 0.0, 0.0)]

normal_spec_tntsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "TintPaletteSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

normal_spec_cutout_tntsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "TintPaletteSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

normal_spec_umsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "umGlobalOverrideParams", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "umGlobalParams", 0.025, 0.025, 1.0, 1.0)]

normal_spec_wrinklesps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "WrinkleMaskSampler_0"),
                shader_parameter("Image", "WrinkleMaskSampler_1"),
                shader_parameter("Image", "WrinkleMaskSampler_2"),
                shader_parameter("Image", "WrinkleMaskSampler_3"),
                shader_parameter("Image", "WrinkleSampler_A"),
                shader_parameter("Image", "WrinkleSampler_B"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WrinkleMaskStrengths3", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WrinkleMaskStrengths2", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WrinkleMaskStrengths1", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WrinkleMaskStrengths0", 0.0, 0.0, 0.0, 0.0)]

normal_terrain_wetsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

normal_tntsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "TintPaletteSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

normal_tnt_alphasps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "TintPaletteSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

normal_cutout_tntsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "TintPaletteSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

normal_umsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "umGlobalOverrideParams", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "umGlobalParams", 0.025, 0.025, 1.0, 1.0)]

normal_cutout_umsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "umGlobalOverrideParams", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "umGlobalParams", 0.025, 0.025, 1.0, 1.0)]

normal_um_tntsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "TintPaletteSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "umGlobalOverrideParams", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "umGlobalParams", 0.025, 0.025, 1.0, 1.0)]

parallaxsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ParallaxScaleBias", 0.03, 0.0, 0.0, 0.0)]

parallax_specmapsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ParallaxScaleBias", 0.03, 0.0, 0.0, 0.0)]

pedsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "VolumeSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "umGlobalParams", 0.0025, 0.0025, 7.0, 7.0),
                shader_parameter("Value", "envEffFatThickness", 25.0, 25.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DetailSettings", 0.0, 0.0, 24.0, 0.0),
                shader_parameter("Value", "StubbleControl", 2.0, 0.6, 0.0, 0.0)]

ped_alphasps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffFatThickness", 25.0, 25.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DetailSettings", 0.0, 0.0, 24.0, 0.0),
                shader_parameter("Value", "StubbleControl", 2.0, 0.6, 0.0, 0.0)]

ped_clothsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "VolumeSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "umGlobalParams", 0.0025, 0.0025, 7.0, 7.0),
                shader_parameter("Value", "envEffFatThickness", 25.0, 25.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DetailSettings", 0.0, 0.0, 24.0, 0.0),
                shader_parameter("Value", "StubbleControl", 2.0, 0.6, 0.0, 0.0)]

ped_cloth_enveffsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "VolumeSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Image", "SnowSampler"),
                shader_parameter("Value", "umGlobalParams", 0.0025, 0.0025, 7.0, 7.0),
                shader_parameter("Value", "envEffFatThickness", 25.0, 25.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DetailSettings", 0.0, 0.0, 24.0, 0.0),
                shader_parameter("Value", "StubbleControl", 2.0, 0.6, 0.0, 0.0)]

ped_decalsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "VolumeSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffFatThickness", 25.0, 25.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DetailSettings", 0.0, 0.0, 24.0, 0.0),
                shader_parameter("Value", "StubbleControl", 2.0, 0.6, 0.0, 0.0)]

ped_decal_decorationsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "VolumeSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "umGlobalParams", 0.0025, 0.0025, 7.0, 7.0),
                shader_parameter("Value", "envEffFatThickness", 25.0, 25.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DetailSettings", 0.0, 0.0, 24.0, 0.0),
                shader_parameter("Value", "StubbleControl", 2.0, 0.6, 0.0, 0.0)]

ped_decal_expensivesps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "VolumeSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffFatThickness", 25.0, 25.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DetailSettings", 0.0, 0.0, 24.0, 0.0),
                shader_parameter("Value", "StubbleControl", 2.0, 0.6, 0.0, 0.0)]

ped_decal_nodiffsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "VolumeSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffFatThickness", 25.0, 25.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DetailSettings", 0.0, 0.0, 24.0, 0.0),
                shader_parameter("Value", "StubbleControl", 2.0, 0.6, 0.0, 0.0)]

ped_defaultsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "VolumeSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffFatThickness", 25.0, 25.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DetailSettings", 0.0, 0.0, 24.0, 0.0),
                shader_parameter("Value", "StubbleControl", 2.0, 0.6, 0.0, 0.0)]

ped_default_cutoutsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "VolumeSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffFatThickness", 25.0, 25.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DetailSettings", 0.0, 0.0, 24.0, 0.0),
                shader_parameter("Value", "StubbleControl", 2.0, 0.6, 0.0, 0.0)]

ped_default_clothsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "VolumeSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffFatThickness", 25.0, 25.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DetailSettings", 0.0, 0.0, 24.0, 0.0),
                shader_parameter("Value", "StubbleControl", 2.0, 0.6, 0.0, 0.0)]

ped_default_enveffsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "VolumeSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Image", "SnowSampler"),
                shader_parameter("Value", "envEffFatThickness", 25.0, 25.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DetailSettings", 0.0, 0.0, 24.0, 0.0),
                shader_parameter("Value", "StubbleControl", 2.0, 0.6, 0.0, 0.0)]

ped_default_mpsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "VolumeSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffFatThickness", 25.0, 25.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DetailSettings", 0.0, 0.0, 24.0, 0.0),
                shader_parameter("Value", "StubbleControl", 2.0, 0.6, 0.0, 0.0)]

ped_default_palettesps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "VolumeSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffFatThickness", 25.0, 25.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DetailSettings", 0.0, 0.0, 24.0, 0.0),
                shader_parameter("Value", "StubbleControl", 2.0, 0.6, 0.0, 0.0)]

ped_emissivesps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "VolumeSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "umGlobalParams", 0.0025, 0.0025, 7.0, 7.0),
                shader_parameter("Value", "envEffFatThickness", 25.0, 25.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "EmissiveMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DetailSettings", 0.0, 0.0, 24.0, 0.0),
                shader_parameter("Value", "StubbleControl", 2.0, 0.6, 0.0, 0.0)]

ped_enveffsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "VolumeSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Image", "SnowSampler"),
                shader_parameter("Value", "umGlobalParams", 0.0025, 0.0025, 7.0, 7.0),
                shader_parameter("Value", "envEffFatThickness", 25.0, 25.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DetailSettings", 0.0, 0.0, 24.0, 0.0),
                shader_parameter("Value", "StubbleControl", 2.0, 0.6, 0.0, 0.0)]

ped_fursps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "NoiseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffFatThickness", 25.0, 25.0, 0.0, 0.0),
                shader_parameter("Value", "FurBendParams", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "FurGlobalParams", 0.0, 0.0, 0.00392157, 0.0),
                shader_parameter("Value", "FurAttenCoef", 1.21, -0.22, 0.0, 0.0),
                shader_parameter("Value", "FurAOBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "FurStiffness", 0.75, 0.0, 0.0, 0.0),
                shader_parameter("Value", "FurSelfShadowMin", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "FurNoiseUVScale", 2.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "FurLength", 0.5, 0.0, 0.0, 0.0),
                shader_parameter("Value", "FurMaxLayers", 10.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "FurMinLayers", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "OrderNumber", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DetailSettings", 0.0, 0.0, 24.0, 0.0),
                shader_parameter("Value", "StubbleControl", 2.0, 0.6, 0.0, 0.0)]

ped_hair_cutout_alphasps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "anisoNoiseSpecSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "umGlobalParams", 0.0025, 0.0025, 7.0, 7.0),
                shader_parameter("Value", "AnisotropicAlphaBias", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffFatThickness", 25.0, 25.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularNoiseMapUVScaleFactor", 2.0, 1.0, 3.0, 1.0),
                shader_parameter("Value", "AnisotropicSpecularColour", 0.1, 0.1, 0.1, 1.0),
                shader_parameter("Value", "AnisotropicSpecularExponent", 16.0, 32.0, 0.0, 0.0),
                shader_parameter("Value", "AnisotropicSpecularIntensity", 0.1, 0.15, 0.0, 0.0),
                shader_parameter("Value", "DetailSettings", 0.0, 0.0, 24.0, 0.0),
                shader_parameter("Value", "StubbleControl", 2.0, 0.6, 0.0, 0.0)]

ped_hair_spikedsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "anisoNoiseSpecSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "umGlobalParams", 0.0025, 0.0025, 7.0, 7.0),
                shader_parameter("Value", "AnisotropicAlphaBias", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffFatThickness", 25.0, 25.0, 0.0, 0.0),
                shader_parameter("Value", "OrderNumber", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularNoiseMapUVScaleFactor", 2.0, 1.0, 3.0, 1.0),
                shader_parameter("Value", "AnisotropicSpecularColour", 0.1, 0.1, 0.1, 1.0),
                shader_parameter("Value", "AnisotropicSpecularExponent", 16.0, 32.0, 0.0, 0.0),
                shader_parameter("Value", "AnisotropicSpecularIntensity", 0.1, 0.15, 0.0, 0.0),
                shader_parameter("Value", "DetailSettings", 0.0, 0.0, 24.0, 0.0),
                shader_parameter("Value", "StubbleControl", 2.0, 0.6, 0.0, 0.0)]

ped_nopeddamagedecalssps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "VolumeSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "umGlobalParams", 0.0025, 0.0025, 7.0, 7.0),
                shader_parameter("Value", "envEffFatThickness", 25.0, 25.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DetailSettings", 0.0, 0.0, 24.0, 0.0),
                shader_parameter("Value", "StubbleControl", 2.0, 0.6, 0.0, 0.0)]

ped_palettesps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "VolumeSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "umGlobalParams", 0.0025, 0.0025, 7.0, 7.0),
                shader_parameter("Value", "envEffFatThickness", 25.0, 25.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DetailSettings", 0.0, 0.0, 24.0, 0.0),
                shader_parameter("Value", "StubbleControl", 2.0, 0.6, 0.0, 0.0)]

ped_wrinklesps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "VolumeSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Image", "WrinkleMaskSampler_0"),
                shader_parameter("Image", "WrinkleMaskSampler_1"),
                shader_parameter("Image", "WrinkleMaskSampler_2"),
                shader_parameter("Image", "WrinkleMaskSampler_3"),
                shader_parameter("Image", "WrinkleSampler_A"),
                shader_parameter("Image", "WrinkleSampler_B"),
                shader_parameter("Value", "umGlobalParams", 0.0025, 0.0025, 7.0, 7.0),
                shader_parameter("Value", "envEffFatThickness", 25.0, 25.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DetailSettings", 0.0, 0.0, 24.0, 0.0),
                shader_parameter("Value", "StubbleControl", 2.0, 0.6, 0.0, 0.0)]

ped_wrinkle_clothsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "VolumeSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Image", "WrinkleMaskSampler_0"),
                shader_parameter("Image", "WrinkleMaskSampler_1"),
                shader_parameter("Image", "WrinkleMaskSampler_2"),
                shader_parameter("Image", "WrinkleMaskSampler_3"),
                shader_parameter("Image", "WrinkleSampler_A"),
                shader_parameter("Image", "WrinkleSampler_B"),
                shader_parameter("Value", "umGlobalParams", 0.0025, 0.0025, 7.0, 7.0),
                shader_parameter("Value", "envEffFatThickness", 25.0, 25.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DetailSettings", 0.0, 0.0, 24.0, 0.0),
                shader_parameter("Value", "StubbleControl", 2.0, 0.6, 0.0, 0.0)]

ped_wrinkle_cloth_enveffsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "VolumeSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Image", "SnowSampler"),
                shader_parameter("Image", "WrinkleMaskSampler_0"),
                shader_parameter("Image", "WrinkleMaskSampler_1"),
                shader_parameter("Image", "WrinkleMaskSampler_2"),
                shader_parameter("Image", "WrinkleMaskSampler_3"),
                shader_parameter("Image", "WrinkleSampler_A"),
                shader_parameter("Image", "WrinkleSampler_B"),
                shader_parameter("Value", "umGlobalParams", 0.0025, 0.0025, 7.0, 7.0),
                shader_parameter("Value", "envEffFatThickness", 25.0, 25.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DetailSettings", 0.0, 0.0, 24.0, 0.0),
                shader_parameter("Value", "StubbleControl", 2.0, 0.6, 0.0, 0.0)]

ped_wrinkle_cssps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "VolumeSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Image", "WrinkleMaskSampler_0"),
                shader_parameter("Image", "WrinkleMaskSampler_1"),
                shader_parameter("Image", "WrinkleMaskSampler_2"),
                shader_parameter("Image", "WrinkleMaskSampler_3"),
                shader_parameter("Image", "WrinkleMaskSampler_4"),
                shader_parameter("Image", "WrinkleMaskSampler_5"),
                shader_parameter("Image", "WrinkleSampler_A"),
                shader_parameter("Image", "WrinkleSampler_B"),
                shader_parameter("Value", "umGlobalParams", 0.0025, 0.0025, 7.0, 7.0),
                shader_parameter("Value", "envEffFatThickness", 25.0, 25.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DetailSettings", 0.0, 0.0, 24.0, 0.0),
                shader_parameter("Value", "StubbleControl", 2.0, 0.6, 0.0, 0.0)]

ped_wrinkle_enveffsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "VolumeSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Image", "SnowSampler"),
                shader_parameter("Image", "WrinkleMaskSampler_0"),
                shader_parameter("Image", "WrinkleMaskSampler_1"),
                shader_parameter("Image", "WrinkleMaskSampler_2"),
                shader_parameter("Image", "WrinkleMaskSampler_3"),
                shader_parameter("Image", "WrinkleSampler_A"),
                shader_parameter("Image", "WrinkleSampler_B"),
                shader_parameter("Value", "umGlobalParams", 0.0025, 0.0025, 7.0, 7.0),
                shader_parameter("Value", "envEffFatThickness", 25.0, 25.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DetailSettings", 0.0, 0.0, 24.0, 0.0),
                shader_parameter("Value", "StubbleControl", 2.0, 0.6, 0.0, 0.0)]

ptfx_modelsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

gta_radarsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Value", "ClippingPlane", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DiffuseCol", 1.0, 1.0, 1.0, 1.0)]

radarsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Value", "ClippingPlane", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DiffuseCol", 1.0, 1.0, 1.0, 1.0)]

reflectsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "EnvironmentSampler"),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0)]

gta_reflect_alphasps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "EnvironmentSampler"),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0)]

reflect_alphasps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "EnvironmentSampler"),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0)]

reflect_decalsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "EnvironmentSampler"),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0)]

sky_systemsps = [
                shader_parameter("Image", "NoiseSampler"),
                shader_parameter("Image", "PerlinSampler"),
                shader_parameter("Image", "HighDetailSampler"),
                shader_parameter("Image", "StarFieldSampler"),
                shader_parameter("Image", "DitherSampler"),
                shader_parameter("Image", "MoonSampler"),
                shader_parameter("Value", "NoisePhase", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "NoiseDensityOffset", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "NoiseSoftness", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "NoiseThreshold", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "NoiseScale", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "NoiseFrequency", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "MoonColor", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "LunarCycle", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "MoonIntensity", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "MoonPosition", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "MoonDirection", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "StarfieldIntensity", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpeedConstants", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HorizonLevel", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "EffectsConstants", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SmallCloudColorHdr", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SmallCloudConstants", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "CloudConstants2", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "CloudConstants1", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "CloudDetailConstants", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "CloudShadowMinusBaseColourTimesShadowStrength", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "CloudMidColour", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "CloudBaseMinusMidColour", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SunPosition", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SunDirection", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SunConstants", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SunDiscColorHdr", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SunColorHdr", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SunColor", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HDRIntensity", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SkyPlaneParams", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SkyPlaneColor", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ZenithConstants", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ZenithTransitionColor", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ZenithColor", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "AzimuthTransitionPosition", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "AzimuthTransitionColor", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "AzimuthWestColor", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "AzimuthEastColor", 0.0, 0.0, 0.0, 0.0)]

gta_specsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

specsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

spec_alphasps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

spec_screendooralphasps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

spec_decalsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

spec_reflectsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Image", "EnvironmentSampler"),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

spec_reflect_alphasps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Image", "EnvironmentSampler"),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

spec_reflect_decalsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Image", "EnvironmentSampler"),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

spec_tntsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "TintPaletteSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

cutout_spec_tntsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "TintPaletteSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

spec_twiddle_tntsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "TintPaletteSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

terrain_cb_4lyrsps = [
                shader_parameter("Image", "TextureSampler_layer0"),
                shader_parameter("Image", "BumpSampler_layer0"),
                shader_parameter("Image", "TextureSampler_layer1"),
                shader_parameter("Image", "BumpSampler_layer1"),
                shader_parameter("Image", "TextureSampler_layer2"),
                shader_parameter("Image", "BumpSampler_layer2"),
                shader_parameter("Image", "TextureSampler_layer3"),
                shader_parameter("Image", "BumpSampler_layer3"),
                shader_parameter("Value", "WetnessMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BumpSelfShadowAmount", 0.3, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 48.0, 0.0, 0.0, 0.0)]

terrain_cb_4lyr_2texsps = [
                shader_parameter("Image", "TextureSampler_layer0"),
                shader_parameter("Image", "BumpSampler_layer0"),
                shader_parameter("Image", "TextureSampler_layer1"),
                shader_parameter("Image", "BumpSampler_layer1"),
                shader_parameter("Image", "TextureSampler_layer2"),
                shader_parameter("Image", "BumpSampler_layer2"),
                shader_parameter("Image", "TextureSampler_layer3"),
                shader_parameter("Image", "BumpSampler_layer3"),
                shader_parameter("Value", "WetnessMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BumpSelfShadowAmount", 0.3, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 48.0, 0.0, 0.0, 0.0)]

terrain_cb_w_4lyrsps = [
                shader_parameter("Image", "TextureSampler_layer0"),
                shader_parameter("Image", "BumpSampler_layer0"),
                shader_parameter("Image", "TextureSampler_layer1"),
                shader_parameter("Image", "BumpSampler_layer1"),
                shader_parameter("Image", "TextureSampler_layer2"),
                shader_parameter("Image", "BumpSampler_layer2"),
                shader_parameter("Image", "TextureSampler_layer3"),
                shader_parameter("Image", "BumpSampler_layer3"),
                shader_parameter("Value", "MaterialWetnessMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BumpSelfShadowAmount", 0.3, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 48.0, 0.0, 0.0, 0.0)]

terrain_cb_w_4lyr_2texsps = [
                shader_parameter("Image", "TextureSampler_layer0"),
                shader_parameter("Image", "BumpSampler_layer0"),
                shader_parameter("Image", "TextureSampler_layer1"),
                shader_parameter("Image", "BumpSampler_layer1"),
                shader_parameter("Image", "TextureSampler_layer2"),
                shader_parameter("Image", "BumpSampler_layer2"),
                shader_parameter("Image", "TextureSampler_layer3"),
                shader_parameter("Image", "BumpSampler_layer3"),
                shader_parameter("Value", "MaterialWetnessMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BumpSelfShadowAmount", 0.3, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 48.0, 0.0, 0.0, 0.0)]

terrain_cb_w_4lyr_2tex_blendsps = [
                shader_parameter("Image", "TextureSampler_layer0"),
                shader_parameter("Image", "BumpSampler_layer0"),
                shader_parameter("Image", "TextureSampler_layer1"),
                shader_parameter("Image", "BumpSampler_layer1"),
                shader_parameter("Image", "TextureSampler_layer2"),
                shader_parameter("Image", "BumpSampler_layer2"),
                shader_parameter("Image", "TextureSampler_layer3"),
                shader_parameter("Image", "BumpSampler_layer3"),
                shader_parameter("Image", "LookupSampler"),
                shader_parameter("Value", "MaterialWetnessMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BumpSelfShadowAmount", 0.3, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 48.0, 0.0, 0.0, 0.0)]

terrain_cb_w_4lyr_2tex_blend_lodsps = [
                shader_parameter("Image", "TextureSampler_layer0"),
                shader_parameter("Image", "TextureSampler_layer1"),
                shader_parameter("Image", "TextureSampler_layer2"),
                shader_parameter("Image", "TextureSampler_layer3"),
                shader_parameter("Image", "LookupSampler"),
                shader_parameter("Value", "MaterialWetnessMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BumpSelfShadowAmount", 0.3, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 48.0, 0.0, 0.0, 0.0)]

terrain_cb_w_4lyr_2tex_blend_pxmsps = [
                shader_parameter("Image", "TextureSampler_layer0"),
                shader_parameter("Image", "BumpSampler_layer0"),
                shader_parameter("Image", "HeightMapSamplerLayer0"),
                shader_parameter("Image", "TextureSampler_layer1"),
                shader_parameter("Image", "BumpSampler_layer1"),
                shader_parameter("Image", "HeightMapSamplerLayer1"),
                shader_parameter("Image", "TextureSampler_layer2"),
                shader_parameter("Image", "BumpSampler_layer2"),
                shader_parameter("Image", "HeightMapSamplerLayer2"),
                shader_parameter("Image", "TextureSampler_layer3"),
                shader_parameter("Image", "BumpSampler_layer3"),
                shader_parameter("Image", "HeightMapSamplerLayer3"),
                shader_parameter("Image", "LookupSampler"),
                shader_parameter("Value", "MaterialWetnessMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BumpSelfShadowAmount", 0.3, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightBias3", 0.015, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightScale3", 0.03, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightBias2", 0.015, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightScale2", 0.03, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightBias1", 0.015, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightScale1", 0.03, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightBias0", 0.015, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightScale0", 0.03, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ParallaxSelfShadowAmount", 0.95, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 48.0, 0.0, 0.0, 0.0)]

terrain_cb_w_4lyr_2tex_blend_pxm_spmsps = [
                shader_parameter("Image", "TextureSampler_layer0"),
                shader_parameter("Image", "BumpSampler_layer0"),
                shader_parameter("Image", "HeightMapSamplerLayer0"),
                shader_parameter("Image", "TextureSampler_layer1"),
                shader_parameter("Image", "BumpSampler_layer1"),
                shader_parameter("Image", "HeightMapSamplerLayer1"),
                shader_parameter("Image", "TextureSampler_layer2"),
                shader_parameter("Image", "BumpSampler_layer2"),
                shader_parameter("Image", "HeightMapSamplerLayer2"),
                shader_parameter("Image", "TextureSampler_layer3"),
                shader_parameter("Image", "BumpSampler_layer3"),
                shader_parameter("Image", "HeightMapSamplerLayer3"),
                shader_parameter("Image", "LookupSampler"),
                shader_parameter("Value", "MaterialWetnessMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BumpSelfShadowAmount", 0.3, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightBias3", 0.015, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightScale3", 0.03, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightBias2", 0.015, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightScale2", 0.03, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightBias1", 0.015, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightScale1", 0.03, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightBias0", 0.015, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightScale0", 0.03, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ParallaxSelfShadowAmount", 0.95, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecIntensityAdjust", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMultSpecMap", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecFalloffAdjust", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMultSpecMap", 48.0, 0.0, 0.0, 0.0)]

terrain_cb_w_4lyr_2tex_pxmsps = [
                shader_parameter("Image", "TextureSampler_layer0"),
                shader_parameter("Image", "BumpSampler_layer0"),
                shader_parameter("Image", "HeightMapSamplerLayer0"),
                shader_parameter("Image", "TextureSampler_layer1"),
                shader_parameter("Image", "BumpSampler_layer1"),
                shader_parameter("Image", "HeightMapSamplerLayer1"),
                shader_parameter("Image", "TextureSampler_layer2"),
                shader_parameter("Image", "BumpSampler_layer2"),
                shader_parameter("Image", "HeightMapSamplerLayer2"),
                shader_parameter("Image", "TextureSampler_layer3"),
                shader_parameter("Image", "BumpSampler_layer3"),
                shader_parameter("Image", "HeightMapSamplerLayer3"),
                shader_parameter("Value", "MaterialWetnessMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BumpSelfShadowAmount", 0.3, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightBias3", 0.015, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightScale3", 0.03, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightBias2", 0.015, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightScale2", 0.03, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightBias1", 0.015, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightScale1", 0.03, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightBias0", 0.015, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightScale0", 0.03, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ParallaxSelfShadowAmount", 0.95, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 48.0, 0.0, 0.0, 0.0)]

terrain_cb_w_4lyr_cmsps = [
                shader_parameter("Image", "TextureSampler_layer0"),
                shader_parameter("Image", "BumpSampler_layer0"),
                shader_parameter("Image", "TextureSampler_layer1"),
                shader_parameter("Image", "BumpSampler_layer1"),
                shader_parameter("Image", "TextureSampler_layer2"),
                shader_parameter("Image", "BumpSampler_layer2"),
                shader_parameter("Image", "TextureSampler_layer3"),
                shader_parameter("Image", "BumpSampler_layer3"),
                shader_parameter("Image", "LookupSampler"),
                shader_parameter("Value", "MaterialWetnessMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BumpSelfShadowAmount", 0.3, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 48.0, 0.0, 0.0, 0.0)]

terrain_cb_w_4lyr_cm_pxmsps = [
                shader_parameter("Image", "TextureSampler_layer0"),
                shader_parameter("Image", "BumpSampler_layer0"),
                shader_parameter("Image", "HeightMapSamplerLayer0"),
                shader_parameter("Image", "TextureSampler_layer1"),
                shader_parameter("Image", "BumpSampler_layer1"),
                shader_parameter("Image", "HeightMapSamplerLayer1"),
                shader_parameter("Image", "TextureSampler_layer2"),
                shader_parameter("Image", "BumpSampler_layer2"),
                shader_parameter("Image", "HeightMapSamplerLayer2"),
                shader_parameter("Image", "TextureSampler_layer3"),
                shader_parameter("Image", "BumpSampler_layer3"),
                shader_parameter("Image", "HeightMapSamplerLayer3"),
                shader_parameter("Image", "LookupSampler"),
                shader_parameter("Value", "MaterialWetnessMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BumpSelfShadowAmount", 0.3, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightBias3", 0.015, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightScale3", 0.03, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightBias2", 0.015, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightScale2", 0.03, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightBias1", 0.015, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightScale1", 0.03, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightBias0", 0.015, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightScale0", 0.03, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ParallaxSelfShadowAmount", 0.95, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 48.0, 0.0, 0.0, 0.0)]

terrain_cb_w_4lyr_cm_pxm_tntsps = [
                shader_parameter("Image", "TintPaletteSampler"),
                shader_parameter("Image", "TextureSampler_layer0"),
                shader_parameter("Image", "BumpSampler_layer0"),
                shader_parameter("Image", "HeightMapSamplerLayer0"),
                shader_parameter("Image", "TextureSampler_layer1"),
                shader_parameter("Image", "BumpSampler_layer1"),
                shader_parameter("Image", "HeightMapSamplerLayer1"),
                shader_parameter("Image", "TextureSampler_layer2"),
                shader_parameter("Image", "BumpSampler_layer2"),
                shader_parameter("Image", "HeightMapSamplerLayer2"),
                shader_parameter("Image", "TextureSampler_layer3"),
                shader_parameter("Image", "BumpSampler_layer3"),
                shader_parameter("Image", "HeightMapSamplerLayer3"),
                shader_parameter("Image", "LookupSampler"),
                shader_parameter("Value", "MaterialWetnessMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BumpSelfShadowAmount", 0.3, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightBias3", 0.015, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightScale3", 0.03, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightBias2", 0.015, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightScale2", 0.03, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightBias1", 0.015, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightScale1", 0.03, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightBias0", 0.015, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightScale0", 0.03, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ParallaxSelfShadowAmount", 0.95, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 48.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

terrain_cb_w_4lyr_cm_tntsps = [
                shader_parameter("Image", "TintPaletteSampler"),
                shader_parameter("Image", "TextureSampler_layer0"),
                shader_parameter("Image", "BumpSampler_layer0"),
                shader_parameter("Image", "TextureSampler_layer1"),
                shader_parameter("Image", "BumpSampler_layer1"),
                shader_parameter("Image", "TextureSampler_layer2"),
                shader_parameter("Image", "BumpSampler_layer2"),
                shader_parameter("Image", "TextureSampler_layer3"),
                shader_parameter("Image", "BumpSampler_layer3"),
                shader_parameter("Image", "LookupSampler"),
                shader_parameter("Value", "MaterialWetnessMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BumpSelfShadowAmount", 0.3, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 48.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

terrain_cb_w_4lyr_lodsps = [
                shader_parameter("Image", "TextureSampler_layer0"),
                shader_parameter("Image", "TextureSampler_layer1"),
                shader_parameter("Image", "TextureSampler_layer2"),
                shader_parameter("Image", "TextureSampler_layer3"),
                shader_parameter("Value", "MaterialWetnessMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BumpSelfShadowAmount", 0.3, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 48.0, 0.0, 0.0, 0.0)]

terrain_cb_w_4lyr_pxmsps = [
                shader_parameter("Image", "TextureSampler_layer0"),
                shader_parameter("Image", "BumpSampler_layer0"),
                shader_parameter("Image", "HeightMapSamplerLayer0"),
                shader_parameter("Image", "TextureSampler_layer1"),
                shader_parameter("Image", "BumpSampler_layer1"),
                shader_parameter("Image", "HeightMapSamplerLayer1"),
                shader_parameter("Image", "TextureSampler_layer2"),
                shader_parameter("Image", "BumpSampler_layer2"),
                shader_parameter("Image", "HeightMapSamplerLayer2"),
                shader_parameter("Image", "TextureSampler_layer3"),
                shader_parameter("Image", "BumpSampler_layer3"),
                shader_parameter("Image", "HeightMapSamplerLayer3"),
                shader_parameter("Value", "MaterialWetnessMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BumpSelfShadowAmount", 0.3, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightBias3", 0.015, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightScale3", 0.03, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightBias2", 0.015, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightScale2", 0.03, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightBias1", 0.015, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightScale1", 0.03, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightBias0", 0.015, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightScale0", 0.03, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ParallaxSelfShadowAmount", 0.95, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 48.0, 0.0, 0.0, 0.0)]

terrain_cb_w_4lyr_pxm_spmsps = [
                shader_parameter("Image", "TextureSampler_layer0"),
                shader_parameter("Image", "BumpSampler_layer0"),
                shader_parameter("Image", "HeightMapSamplerLayer0"),
                shader_parameter("Image", "TextureSampler_layer1"),
                shader_parameter("Image", "BumpSampler_layer1"),
                shader_parameter("Image", "HeightMapSamplerLayer1"),
                shader_parameter("Image", "TextureSampler_layer2"),
                shader_parameter("Image", "BumpSampler_layer2"),
                shader_parameter("Image", "HeightMapSamplerLayer2"),
                shader_parameter("Image", "TextureSampler_layer3"),
                shader_parameter("Image", "BumpSampler_layer3"),
                shader_parameter("Image", "HeightMapSamplerLayer3"),
                shader_parameter("Value", "MaterialWetnessMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BumpSelfShadowAmount", 0.3, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightBias3", 0.015, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightScale3", 0.03, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightBias2", 0.015, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightScale2", 0.03, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightBias1", 0.015, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightScale1", 0.03, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightBias0", 0.015, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightScale0", 0.03, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ParallaxSelfShadowAmount", 0.95, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecIntensityAdjust", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMultSpecMap", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecFalloffAdjust", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMultSpecMap", 48.0, 0.0, 0.0, 0.0)]

terrain_cb_w_4lyr_specsps = [
                shader_parameter("Image", "TextureSampler_layer0"),
                shader_parameter("Image", "BumpSampler_layer0"),
                shader_parameter("Image", "TextureSampler_layer1"),
                shader_parameter("Image", "BumpSampler_layer1"),
                shader_parameter("Image", "TextureSampler_layer2"),
                shader_parameter("Image", "BumpSampler_layer2"),
                shader_parameter("Image", "TextureSampler_layer3"),
                shader_parameter("Image", "BumpSampler_layer3"),
                shader_parameter("Value", "MaterialWetnessMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BumpSelfShadowAmount", 0.3, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 48.0, 0.0, 0.0, 0.0)]

terrain_cb_w_4lyr_spec_intsps = [
                shader_parameter("Image", "TextureSampler_layer0"),
                shader_parameter("Image", "BumpSampler_layer0"),
                shader_parameter("Image", "TextureSampler_layer1"),
                shader_parameter("Image", "BumpSampler_layer1"),
                shader_parameter("Image", "TextureSampler_layer2"),
                shader_parameter("Image", "BumpSampler_layer2"),
                shader_parameter("Image", "TextureSampler_layer3"),
                shader_parameter("Image", "BumpSampler_layer3"),
                shader_parameter("Value", "MaterialWetnessMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BumpSelfShadowAmount", 0.3, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 48.0, 0.0, 0.0, 0.0)]

terrain_cb_w_4lyr_spec_int_pxmsps = [
                shader_parameter("Image", "TextureSampler_layer0"),
                shader_parameter("Image", "BumpSampler_layer0"),
                shader_parameter("Image", "HeightMapSamplerLayer0"),
                shader_parameter("Image", "TextureSampler_layer1"),
                shader_parameter("Image", "BumpSampler_layer1"),
                shader_parameter("Image", "HeightMapSamplerLayer1"),
                shader_parameter("Image", "TextureSampler_layer2"),
                shader_parameter("Image", "BumpSampler_layer2"),
                shader_parameter("Image", "HeightMapSamplerLayer2"),
                shader_parameter("Image", "TextureSampler_layer3"),
                shader_parameter("Image", "BumpSampler_layer3"),
                shader_parameter("Image", "HeightMapSamplerLayer3"),
                shader_parameter("Value", "MaterialWetnessMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BumpSelfShadowAmount", 0.3, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightBias3", 0.015, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightScale3", 0.03, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightBias2", 0.015, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightScale2", 0.03, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightBias1", 0.015, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightScale1", 0.03, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightBias0", 0.015, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightScale0", 0.03, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ParallaxSelfShadowAmount", 0.95, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 48.0, 0.0, 0.0, 0.0)]

terrain_cb_w_4lyr_spec_pxmsps = [
                shader_parameter("Image", "TextureSampler_layer0"),
                shader_parameter("Image", "BumpSampler_layer0"),
                shader_parameter("Image", "HeightMapSamplerLayer0"),
                shader_parameter("Image", "TextureSampler_layer1"),
                shader_parameter("Image", "BumpSampler_layer1"),
                shader_parameter("Image", "HeightMapSamplerLayer1"),
                shader_parameter("Image", "TextureSampler_layer2"),
                shader_parameter("Image", "BumpSampler_layer2"),
                shader_parameter("Image", "HeightMapSamplerLayer2"),
                shader_parameter("Image", "TextureSampler_layer3"),
                shader_parameter("Image", "BumpSampler_layer3"),
                shader_parameter("Image", "HeightMapSamplerLayer3"),
                shader_parameter("Value", "MaterialWetnessMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BumpSelfShadowAmount", 0.3, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightBias3", 0.015, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightScale3", 0.03, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightBias2", 0.015, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightScale2", 0.03, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightBias1", 0.015, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightScale1", 0.03, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightBias0", 0.015, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HeightScale0", 0.03, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ParallaxSelfShadowAmount", 0.95, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 48.0, 0.0, 0.0, 0.0)]

treessps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Value", "ShadowFalloff", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "AlphaTest", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "AlphaScale", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SelfShadowing", 0.8, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTreeNormals", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WindGlobalParams", 1.0, 5.0, 5.0, 1.0),
                shader_parameter("Value", "umGlobalParams", 0.025, 0.02, 1.0, 0.5)]

trees_lodsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Value", "ShadowFalloff", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "AlphaTest", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "AlphaScale", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SelfShadowing", 0.8, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTreeNormals", 1.0, 0.0, 0.0, 0.0)]

trees_lod2sps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Value", "ShadowFalloff", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "AlphaTest", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "AlphaScale", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTreeNormals", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "TreeLod2Normal", 0.0, 0.0, 1.0, 0.0),
                shader_parameter("Value", "TreeLod2Params", 1.0, 1.0, 0.0, 0.0)]

trees_lod_tntsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "TintPaletteSampler"),
                shader_parameter("Value", "ShadowFalloff", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "AlphaTest", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "AlphaScale", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SelfShadowing", 0.8, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTreeNormals", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

trees_normalsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Value", "ShadowFalloff", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "AlphaTest", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "AlphaScale", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SelfShadowing", 0.8, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTreeNormals", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WindGlobalParams", 1.0, 5.0, 5.0, 1.0),
                shader_parameter("Value", "umGlobalParams", 0.025, 0.02, 1.0, 0.5),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0)]

trees_normal_diffspecsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Value", "ShadowFalloff", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "AlphaTest", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "AlphaScale", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SelfShadowing", 0.8, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTreeNormals", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WindGlobalParams", 1.0, 5.0, 5.0, 1.0),
                shader_parameter("Value", "umGlobalParams", 0.025, 0.02, 1.0, 0.5),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

trees_normal_diffspec_tntsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "TintPaletteSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Value", "ShadowFalloff", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "AlphaTest", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "AlphaScale", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SelfShadowing", 0.8, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTreeNormals", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WindGlobalParams", 1.0, 5.0, 5.0, 1.0),
                shader_parameter("Value", "umGlobalParams", 0.025, 0.02, 1.0, 0.5),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

trees_normal_specsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Value", "ShadowFalloff", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "AlphaTest", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "AlphaScale", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SelfShadowing", 0.8, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTreeNormals", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WindGlobalParams", 1.0, 5.0, 5.0, 1.0),
                shader_parameter("Value", "umGlobalParams", 0.025, 0.02, 1.0, 0.5),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

trees_normal_spec_tntsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "TintPaletteSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Value", "ShadowFalloff", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "AlphaTest", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "AlphaScale", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SelfShadowing", 0.8, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTreeNormals", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WindGlobalParams", 1.0, 5.0, 5.0, 1.0),
                shader_parameter("Value", "umGlobalParams", 0.025, 0.02, 1.0, 0.5),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

trees_shadow_proxysps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Value", "ShadowFalloff", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "AlphaTest", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "AlphaScale", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SelfShadowing", 0.8, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTreeNormals", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WindGlobalParams", 1.0, 5.0, 5.0, 1.0),
                shader_parameter("Value", "umGlobalParams", 0.025, 0.02, 1.0, 0.5)]

trees_tntsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "TintPaletteSampler"),
                shader_parameter("Value", "ShadowFalloff", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "AlphaTest", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "AlphaScale", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SelfShadowing", 0.8, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTreeNormals", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WindGlobalParams", 1.0, 5.0, 5.0, 1.0),
                shader_parameter("Value", "umGlobalParams", 0.025, 0.02, 1.0, 0.5),
                shader_parameter("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

vehicle_badgessps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DamageSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                shader_parameter("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_basicsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DamageSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                shader_parameter("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_blurredrotorsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                shader_parameter("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0)]

vehicle_blurredrotor_emissivesps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                shader_parameter("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "EmissiveMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0)]

vehicle_clothsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DamageSampler"),
                shader_parameter("Image", "DirtSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                shader_parameter("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                shader_parameter("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_cloth2sps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DamageSampler"),
                shader_parameter("Image", "DiffuseSampler2"),
                shader_parameter("Image", "DirtSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                shader_parameter("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Diffuse2SpecMod", 0.8, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                shader_parameter("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "matDiffuseColor2", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_cutoutsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DamageSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                shader_parameter("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_dash_emissivesps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DamageSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                shader_parameter("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DimmerSetPacked", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_dash_emissive_opaquesps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DamageSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                shader_parameter("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_decalsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DamageSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                shader_parameter("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_decal2sps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DamageSampler"),
                shader_parameter("Image", "DirtSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                shader_parameter("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                shader_parameter("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_detailsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DamageSampler"),
                shader_parameter("Image", "DetailSampler"),
                shader_parameter("Image", "DirtSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "DetailSettings", 0.0, 0.0, 24.0, 24.0),
                shader_parameter("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                shader_parameter("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                shader_parameter("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_detail2sps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DamageSampler"),
                shader_parameter("Image", "DetailSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "DetailSettings", 0.0, 0.0, 24.0, 24.0),
                shader_parameter("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                shader_parameter("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_emissive_alphasps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DamageSampler"),
                shader_parameter("Image", "DirtSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                shader_parameter("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                shader_parameter("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "EmissiveMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_emissive_opaquesps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DamageSampler"),
                shader_parameter("Image", "DirtSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                shader_parameter("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                shader_parameter("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "EmissiveMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_genericsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DamageSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                shader_parameter("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_interiorsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DamageSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                shader_parameter("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_interior2sps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DamageSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                shader_parameter("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_licenseplatesps = [
                shader_parameter("Image", "DamageSampler"),
                shader_parameter("Image", "DirtSampler"),
                shader_parameter("Image", "plateBgSampler"),
                shader_parameter("Image", "plateBgBumpSampler"),
                shader_parameter("Image", "FontSampler"),
                shader_parameter("Image", "FontNormalSampler"),
                shader_parameter("Value", "distEpsilonScaleMin", 10.0, 10.0, 0.0, 0.0),
                shader_parameter("Value", "distMapCenterVal", 0.5, 0.0, 0.0, 0.0),
                shader_parameter("Value", "FontNormalScale", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "LicensePlateFontTint", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "LicensePlateFontExtents", 0.043, 0.38, 0.945, 0.841),
                shader_parameter("Value", "numLetters", 16.0, 4.0, 0.0, 0.0),
                shader_parameter("Value", "LetterSize", 0.0625, 0.25, 0.0, 0.0),
                shader_parameter("Value", "LetterIndex2", 63.0, 63.0, 62.0, 0.0),
                shader_parameter("Value", "LetterIndex1", 10.0, 21.0, 10.0, 23.0),
                shader_parameter("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                shader_parameter("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                shader_parameter("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_lightsemissivesps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DamageSampler"),
                shader_parameter("Image", "DirtSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                shader_parameter("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                shader_parameter("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "DimmerSetPacked", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "EmissiveMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_meshsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DamageSampler"),
                shader_parameter("Image", "DirtSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                shader_parameter("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Specular2Color_DirLerp", 0.0, 0.5, 0.0, 0.0),
                shader_parameter("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                shader_parameter("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_mesh2_enveffsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DamageSampler"),
                shader_parameter("Image", "SnowSampler0"),
                shader_parameter("Image", "SnowSampler1"),
                shader_parameter("Image", "DirtSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                shader_parameter("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecTexTileUV", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                shader_parameter("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_mesh_enveffsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DamageSampler"),
                shader_parameter("Image", "SnowSampler0"),
                shader_parameter("Image", "SnowSampler1"),
                shader_parameter("Image", "DirtSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                shader_parameter("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecTexTileUV", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                shader_parameter("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_paint1sps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DamageSampler"),
                shader_parameter("Image", "DirtSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                shader_parameter("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Specular2Color_DirLerp", 0.0, 0.5, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                shader_parameter("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_nosplashsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DamageSampler"),
                shader_parameter("Image", "DirtSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                shader_parameter("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Specular2Color_DirLerp", 0.0, 0.5, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                shader_parameter("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_nowatersps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DamageSampler"),
                shader_parameter("Image", "DirtSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                shader_parameter("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Specular2Color_DirLerp", 0.0, 0.5, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                shader_parameter("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_paint1_enveffsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DamageSampler"),
                shader_parameter("Image", "SnowSampler0"),
                shader_parameter("Image", "SnowSampler1"),
                shader_parameter("Image", "DirtSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                shader_parameter("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Specular2Color_DirLerp", 0.0, 0.5, 0.0, 0.0),
                shader_parameter("Value", "SpecTexTileUV", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                shader_parameter("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_paint2sps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DamageSampler"),
                shader_parameter("Image", "DirtSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                shader_parameter("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Specular2Color_DirLerp", 0.0, 0.5, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                shader_parameter("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_paint2_enveffsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DamageSampler"),
                shader_parameter("Image", "SnowSampler0"),
                shader_parameter("Image", "SnowSampler1"),
                shader_parameter("Image", "DirtSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                shader_parameter("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Specular2Color_DirLerp", 0.0, 0.5, 0.0, 0.0),
                shader_parameter("Value", "SpecTexTileUV", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                shader_parameter("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_paint3sps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DamageSampler"),
                shader_parameter("Image", "DiffuseSampler2"),
                shader_parameter("Image", "DirtSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                shader_parameter("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Diffuse2SpecMod", 0.8, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Specular2Color_DirLerp", 0.0, 0.5, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                shader_parameter("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "matDiffuseColor2", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_paint3_enveffsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DamageSampler"),
                shader_parameter("Image", "SnowSampler0"),
                shader_parameter("Image", "SnowSampler1"),
                shader_parameter("Image", "DiffuseSampler2"),
                shader_parameter("Image", "DirtSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                shader_parameter("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Diffuse2SpecMod", 0.8, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Specular2Color_DirLerp", 0.0, 0.5, 0.0, 0.0),
                shader_parameter("Value", "SpecTexTileUV", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                shader_parameter("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "matDiffuseColor2", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_paint3_lvrsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DamageSampler"),
                shader_parameter("Image", "DiffuseSampler3"),
                shader_parameter("Image", "DirtSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                shader_parameter("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Diffuse3SpecMod", 0.8, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Specular2Color_DirLerp", 0.0, 0.5, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                shader_parameter("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "matDiffuseColor2", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_paint4sps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DamageSampler"),
                shader_parameter("Image", "DiffuseSampler2"),
                shader_parameter("Image", "DirtSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                shader_parameter("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Diffuse2SpecMod", 0.8, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Specular2Color_DirLerp", 0.0, 0.5, 0.0, 0.0),
                shader_parameter("Value", "Specular2ColorIntensity", 1.7, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Specular2Factor", 40.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecTexTileUV", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                shader_parameter("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "matDiffuseColor2", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "DiffuseTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_paint4_emissivesps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DamageSampler"),
                shader_parameter("Image", "DiffuseSampler2"),
                shader_parameter("Image", "DirtSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                shader_parameter("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Diffuse2SpecMod", 0.8, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Specular2Color_DirLerp", 0.0, 0.5, 0.0, 0.0),
                shader_parameter("Value", "Specular2ColorIntensity", 1.7, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Specular2Factor", 40.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecTexTileUV", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                shader_parameter("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "EmissiveMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "matDiffuseColor2", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "DiffuseTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_paint4_enveffsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DamageSampler"),
                shader_parameter("Image", "SnowSampler0"),
                shader_parameter("Image", "SnowSampler1"),
                shader_parameter("Image", "DiffuseSampler2"),
                shader_parameter("Image", "DirtSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                shader_parameter("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Diffuse2SpecMod", 0.8, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Specular2Color_DirLerp", 0.0, 0.5, 0.0, 0.0),
                shader_parameter("Value", "Specular2ColorIntensity", 1.7, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Specular2Factor", 40.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecTexTileUV", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                shader_parameter("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "matDiffuseColor2", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "DiffuseTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_paint5_enveffsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DamageSampler"),
                shader_parameter("Image", "SnowSampler0"),
                shader_parameter("Image", "SnowSampler1"),
                shader_parameter("Image", "DiffuseSampler2"),
                shader_parameter("Image", "DirtSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                shader_parameter("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Diffuse2SpecMod", 0.8, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Specular2Color_DirLerp", 0.0, 0.5, 0.0, 0.0),
                shader_parameter("Value", "Specular2ColorIntensity", 1.7, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Specular2Factor", 40.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecTexTileUV", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                shader_parameter("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "matDiffuseColor2", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "DiffuseTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_paint6sps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DamageSampler"),
                shader_parameter("Image", "DiffuseSampler2"),
                shader_parameter("Image", "DirtSampler"),
                shader_parameter("Image", "BumpSampler2"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                shader_parameter("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Diffuse2SpecMod", 0.8, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Specular2Color_DirLerp", 0.0, 0.5, 0.0, 0.0),
                shader_parameter("Value", "Specular2ColorIntensity", 1.7, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Specular2Factor", 40.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecTexTileUV", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                shader_parameter("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "matDiffuseColor2", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "DiffuseTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_paint6_enveffsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DamageSampler"),
                shader_parameter("Image", "SnowSampler0"),
                shader_parameter("Image", "SnowSampler1"),
                shader_parameter("Image", "DiffuseSampler2"),
                shader_parameter("Image", "DirtSampler"),
                shader_parameter("Image", "BumpSampler2"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                shader_parameter("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Diffuse2SpecMod", 0.8, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Specular2Color_DirLerp", 0.0, 0.5, 0.0, 0.0),
                shader_parameter("Value", "Specular2ColorIntensity", 1.7, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Specular2Factor", 40.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecTexTileUV", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                shader_parameter("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "matDiffuseColor2", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "DiffuseTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_paint7sps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DamageSampler"),
                shader_parameter("Image", "DiffuseSampler2"),
                shader_parameter("Image", "DirtSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                shader_parameter("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Diffuse2SpecMod", 0.8, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Specular2Color_DirLerp", 0.0, 0.5, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                shader_parameter("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "matDiffuseColor2", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "DiffuseTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_paint7_enveffsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DamageSampler"),
                shader_parameter("Image", "SnowSampler0"),
                shader_parameter("Image", "SnowSampler1"),
                shader_parameter("Image", "DiffuseSampler2"),
                shader_parameter("Image", "DirtSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                shader_parameter("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Diffuse2SpecMod", 0.8, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Specular2Color_DirLerp", 0.0, 0.5, 0.0, 0.0),
                shader_parameter("Value", "SpecTexTileUV", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                shader_parameter("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "matDiffuseColor2", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "DiffuseTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_paint8sps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DamageSampler"),
                shader_parameter("Image", "SnowSampler0"),
                shader_parameter("Image", "SnowSampler1"),
                shader_parameter("Image", "DiffuseSampler2"),
                shader_parameter("Image", "DirtSampler"),
                shader_parameter("Image", "DirtBumpSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                shader_parameter("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Diffuse2SpecMod", 0.8, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Specular2Color_DirLerp", 0.0, 0.5, 0.0, 0.0),
                shader_parameter("Value", "Specular2ColorIntensity", 1.7, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Specular2Factor", 40.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecTexTileUV", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                shader_parameter("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "matDiffuseColor2", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "DiffuseTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_paint9sps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DamageSampler"),
                shader_parameter("Image", "SnowSampler0"),
                shader_parameter("Image", "SnowSampler1"),
                shader_parameter("Image", "DiffuseSampler2"),
                shader_parameter("Image", "DirtSampler"),
                shader_parameter("Image", "DirtBumpSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                shader_parameter("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Diffuse2SpecMod", 0.8, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Specular2Color_DirLerp", 0.0, 0.5, 0.0, 0.0),
                shader_parameter("Value", "Specular2ColorIntensity", 1.7, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Specular2Factor", 40.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecTexTileUV", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                shader_parameter("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "matDiffuseColor2", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "DiffuseTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_shutssps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DamageSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                shader_parameter("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_tiresps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DirtSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                shader_parameter("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Specular2Color_DirLerp", 0.0, 0.5, 0.0, 0.0),
                shader_parameter("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                shader_parameter("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "matWheelWorldViewProj", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "matWheelWorld", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "TyreDeformParams2", 0.262, 1495.05, 0.0, 0.0),
                shader_parameter("Value", "TyreDeformParams", 0.0, 0.0, 0.0, 1.0)]

vehicle_tire_emissivesps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DirtSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                shader_parameter("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Specular2Color_DirLerp", 0.0, 0.5, 0.0, 0.0),
                shader_parameter("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                shader_parameter("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "EmissiveMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "matWheelWorldViewProj", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "matWheelWorld", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "TyreDeformParams2", 0.262, 1495.05, 0.0, 0.0),
                shader_parameter("Value", "TyreDeformParams", 0.0, 0.0, 0.0, 1.0)]

vehicle_tracksps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DirtSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                shader_parameter("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                shader_parameter("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "TrackAnimUV", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0)]

vehicle_track2sps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DirtSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                shader_parameter("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                shader_parameter("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "Track2AnimUV", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0)]

vehicle_track2_emissivesps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DirtSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                shader_parameter("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                shader_parameter("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "Track2AnimUV", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "EmissiveMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0)]

vehicle_track_ammosps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DirtSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                shader_parameter("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                shader_parameter("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "TrackAmmoAnimUV", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0)]

vehicle_track_emissivesps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DirtSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                shader_parameter("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.15, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 180.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                shader_parameter("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "TrackAnimUV", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "EmissiveMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0)]

vehicle_lightssps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DamageSampler"),
                shader_parameter("Image", "DirtSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                shader_parameter("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                shader_parameter("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_vehglasssps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DamageSampler"),
                shader_parameter("Image", "DirtSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                shader_parameter("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                shader_parameter("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

vehicle_vehglass_innersps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DamageSampler"),
                shader_parameter("Image", "DirtSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "envEffTexTileUV", 8.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "envEffScale", 1.0, 0.001, 0.0, 0.0),
                shader_parameter("Value", "envEffThickness", 25.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "ReflectivePower", 0.45, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DirtColor", 0.231372, 0.223529, 0.203921, 0.0),
                shader_parameter("Value", "DirtLevelMod", 1.0, 1.0, 1.0, 1.0),
                shader_parameter("Value", "matDiffuseColor", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "DamagedWheelOffsets", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageTextureOffset", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "DamageMultiplier", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "BoundRadius", 0.0, 0.0, 0.0, 0.0)]

water_fountainsps = [
                shader_parameter("Value", "FogColor", 0.416, 0.6, 0.631, 0.055),
                shader_parameter("Value", "SpecularFalloff", 1118.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensity", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "RippleScale", 0.04, 0.0, 0.0, 0.0),
                shader_parameter("Value", "RippleBumpiness", 0.356, 0.0, 0.0, 0.0)]

water_poolenvsps = [
                shader_parameter("Value", "FogColor", 0.416, 0.6, 0.631, 0.055),
                shader_parameter("Value", "SpecularFalloff", 1118.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensity", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "RippleScale", 0.04, 0.0, 0.0, 0.0),
                shader_parameter("Value", "RippleBumpiness", 0.356, 0.0, 0.0, 0.0)]

water_riversps = [
                shader_parameter("Image", "FlowSampler"),
                shader_parameter("Image", "FogSampler"),
                shader_parameter("Value", "SpecularFalloff", 1118.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensity", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "RippleScale", 0.04, 0.0, 0.0, 0.0),
                shader_parameter("Value", "RippleSpeed", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "RippleBumpiness", 0.356, 0.0, 0.0, 0.0)]

water_riverfoamsps = [
                shader_parameter("Image", "FoamSampler"),
                shader_parameter("Value", "RippleSpeed", 0.0, 0.0, 0.0, 0.0)]

water_riverlodsps = [
                shader_parameter("Image", "FlowSampler"),
                shader_parameter("Image", "FogSampler"),
                shader_parameter("Value", "SpecularFalloff", 1118.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensity", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "RippleScale", 0.04, 0.0, 0.0, 0.0),
                shader_parameter("Value", "RippleSpeed", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "RippleBumpiness", 0.356, 0.0, 0.0, 0.0)]

water_riveroceansps = [
                shader_parameter("Image", "FogSampler"),
                shader_parameter("Value", "SpecularFalloff", 1118.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensity", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "RippleScale", 0.04, 0.0, 0.0, 0.0),
                shader_parameter("Value", "RippleBumpiness", 0.356, 0.0, 0.0, 0.0)]

water_rivershallowsps = [
                shader_parameter("Image", "FlowSampler"),
                shader_parameter("Image", "FogSampler"),
                shader_parameter("Value", "SpecularFalloff", 1118.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensity", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "RippleScale", 0.04, 0.0, 0.0, 0.0),
                shader_parameter("Value", "RippleSpeed", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "RippleBumpiness", 0.356, 0.0, 0.0, 0.0)]

water_shallowsps = [
                shader_parameter("Image", "FlowSampler"),
                shader_parameter("Image", "FogSampler"),
                shader_parameter("Value", "SpecularFalloff", 1118.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensity", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "RippleScale", 0.04, 0.0, 0.0, 0.0),
                shader_parameter("Value", "RippleSpeed", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "RippleBumpiness", 0.356, 0.0, 0.0, 0.0)]

water_terrainfoamsps = [
                shader_parameter("Image", "FoamSampler"),
                shader_parameter("Value", "HeightOpacity", 10.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WaveMovement", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WaterHeight", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WaveOffset", 0.25, 0.0, 0.0, 0.0)]

weapon_emissivestrong_alphasps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "EmissiveMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV1", 0.0, 1.0, 0.0, 0.0),
                shader_parameter("Value", "GlobalAnimUV0", 1.0, 0.0, 0.0, 0.0)]

weapon_emissive_tntsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "TintPaletteSampler"),
                shader_parameter("Value", "matMaterialColorScale", 1.0, 0.0, 0.0, 1.0),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "EmissiveMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

weapon_normal_spec_alphasps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "WetnessMultiplier", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecMapIntMask", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

weapon_normal_spec_cutout_palettesps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DiffuseExtraSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Image", "TextureSamplerDiffPal"),
                shader_parameter("Value", "PaletteSelector", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Specular2Color", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "Specular2ColorIntensity", 4.7, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Specular2Factor", 40.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

weapon_normal_spec_detail_palettesps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DetailSampler"),
                shader_parameter("Image", "DiffuseExtraSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Image", "TextureSamplerDiffPal"),
                shader_parameter("Value", "DetailSettings", 0.0, 0.0, 24.0, 24.0),
                shader_parameter("Value", "PaletteSelector", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Specular2Color", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "Specular2ColorIntensity", 4.7, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Specular2Factor", 40.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

weapon_normal_spec_detail_tntsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "TintPaletteSampler"),
                shader_parameter("Image", "DetailSampler"),
                shader_parameter("Image", "DiffuseExtraSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "DetailSettings", 0.0, 0.0, 24.0, 24.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Specular2Color", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "Specular2ColorIntensity", 4.7, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Specular2Factor", 40.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

weapon_normal_spec_palettesps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "DiffuseExtraSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Image", "TextureSamplerDiffPal"),
                shader_parameter("Value", "PaletteSelector", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "HardAlphaBlend", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Specular2Color", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "Specular2ColorIntensity", 4.7, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Specular2Factor", 40.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0)]

weapon_normal_spec_tntsps = [
                shader_parameter("Image", "DiffuseSampler"),
                shader_parameter("Image", "TintPaletteSampler"),
                shader_parameter("Image", "DiffuseExtraSampler"),
                shader_parameter("Image", "BumpSampler"),
                shader_parameter("Image", "SpecSampler"),
                shader_parameter("Value", "UseTessellation", 0.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Bumpiness", 1.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Specular2Color", 1.0, 1.0, 1.0, 0.0),
                shader_parameter("Value", "Specular2ColorIntensity", 4.7, 0.0, 0.0, 0.0),
                shader_parameter("Value", "Specular2Factor", 40.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularIntensityMult", 0.125, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFalloffMult", 100.0, 0.0, 0.0, 0.0),
                shader_parameter("Value", "SpecularFresnel", 0.97, 0.0, 0.0, 0.0),
                shader_parameter("Value", "TintPaletteSelector", 0.0, 0.0, 0.0, 0.0)]

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
