if "bpy" in locals():
    import importlib
    importlib.reload(ycd)
else:
    from . import ycd

import bpy