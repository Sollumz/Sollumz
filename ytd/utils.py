from .properties import TextureDictionary, TextureSlot


def get_selected_txd(context) -> TextureDictionary | None:
    coll = context.scene.sz_txds.texture_dictionaries
    if len(coll) == 0:
        return None
    return coll.active_item


def get_selected_txd_texture(context) -> TextureSlot | None:
    txd = get_selected_txd(context)
    if txd is None or len(txd.textures) == 0:
        return None
    return txd.textures.active_item
