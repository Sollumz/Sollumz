from szio.gta5 import RenderBucket, RenderMask


RenderBucketEnumItems = tuple((enum.name, f"{label} ({enum.value})", desc, enum.value) for enum, label, desc in (
    (RenderBucket.OPAQUE, "Opaque", "Opaque object, without alpha"),
    (RenderBucket.ALPHA, "Alpha", "Alpha without shadows, commonly used on glass"),
    (RenderBucket.DECAL, "Decal", "Decal with alpha, no shadows"),
    (RenderBucket.CUTOUT, "Cutout", "Cutout with alpha and shadows, used on fences"),
    (RenderBucket.NO_SPLASH, "No Splash", "Used only with shader 'vehicle_nosplash'"),
    (RenderBucket.NO_WATER, "No Water", "Used only with shader 'vehicle_nowater'"),
    (RenderBucket.WATER, "Water", "Water shaders"),
    (RenderBucket.DISPLACEMENT_ALPHA, "Displacement Alpha",
     "Rendered last to apply displacement effect on all objects in the scene. "
     "Used only with shader 'glass_displacement'"),
))


RenderMaskEnumFlagItems = tuple((enum.name, label, desc, enum.value) for enum, label, desc in (
    (RenderMask.DEFAULT, "Default", "Rendered in the main view"),
    (RenderMask.SHADOW, "Shadow", "Casts shadows"),
    (RenderMask.REFLECTION, "Reflection", "Rendered in reflections"),
    (RenderMask.MIRROR, "Mirror", "Rendered in mirrors"),
    (RenderMask.WATER, "Water", "Rendered in water reflections"),
))
