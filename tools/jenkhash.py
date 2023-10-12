
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


def name_to_hash(name: str) -> int:
    """Gets a hash from a string. If it starts with `hash_`, it parses the hexadecimal number afterwards;
    otherwise, it calculates the JOAAT hash of the string.
    """

    if name.startswith("hash_"):
        return int(name[5:], 16) & 0xFFFFFFFF
    else:
        return Generate(name)
