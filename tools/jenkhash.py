
def GenerateData(bts: bytes, seed=0):
    h = seed

    for b in bts:
        h += b
        h &= 0xFFFFFFFF
        h += (h << 10) & 0xFFFFFFFF
        h &= 0xFFFFFFFF
        h ^= (h >> 6) & 0xFFFFFFFF
        h &= 0xFFFFFFFF

    h += (h << 3) & 0xFFFFFFFF
    h &= 0xFFFFFFFF
    h ^= (h >> 11) & 0xFFFFFFFF
    h &= 0xFFFFFFFF
    h += (h << 15) & 0xFFFFFFFF
    h &= 0xFFFFFFFF

    return h


def Generate(text, encoding="utf-8", seed=0):
    bts = text.lower().encode(encoding)
    return GenerateData(bts, seed)
