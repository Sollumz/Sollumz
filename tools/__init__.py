if "bpy" in locals():
    import importlib
    importlib.reload(cats)
    importlib.reload(jenkhash)
else:
    from . import cats
    from . import jenkhash