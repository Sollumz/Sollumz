from szio.gta5 import jenkhash as iojenkhash


def GenerateData(bts: bytes, seed=0):
    return iojenkhash.hash_data(bts, seed)


def Generate(text, encoding="utf-8", seed=0):
    return iojenkhash.hash_string(text, encoding, seed)


def name_to_hash(name: str) -> int:
    return iojenkhash.name_to_hash(name)
