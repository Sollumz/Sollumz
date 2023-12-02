from enum import IntEnum


class RenderBucket(IntEnum):
    OPAQUE = 0
    ALPHA = 1
    DECAL = 2
    CUTOUT = 3
    NO_SPLASH = 4
    NO_WATER = 5
    WATER = 6
    DISPLACEMENT_ALPHA = 7


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
