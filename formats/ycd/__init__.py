if "bpy" in locals():
    import importlib
    importlib.reload(Animation)
    importlib.reload(AnimSequence)
    importlib.reload(Channel)
    importlib.reload(Clip)
    importlib.reload(ClipDictionary)
    importlib.reload(utils)
else:
    from . import Animation
    from . import AnimSequence
    from . import Channel
    from . import Clip
    from . import ClipDictionary
    from . import utils

import bpy