from ..ydr.shader_materials import shadermats
from ..ybn.collision_materials import collisionmats

SOLLUMZ_SHADERS = list(map(lambda s: s.value, shadermats))
SOLLUMZ_COLLISION_MATERIALS = list(collisionmats)
BLENDER_LANGUAGES = ("en_US", "es")  # bpy.app.translations.locales
