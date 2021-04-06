if "bpy" in locals():
    import importlib
    importlib.reload(xml)
    importlib.reload(cats)
    importlib.reload(meshgen)
    importlib.reload(jenkhash)
else:
    from . import xml
    from . import cats
    from . import meshgen
    from . import cats
    from . import jenkhash

import bpy