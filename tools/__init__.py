if "bpy" in locals():
    import importlib
    importlib.reload(cats)
else:
    from . import cats