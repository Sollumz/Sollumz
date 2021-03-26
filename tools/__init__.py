if "bpy" in locals():
    import importlib
    importlib.reload(cats)
    importlib.reload(meshgen)
else:
    from . import cats
    from . import meshgen