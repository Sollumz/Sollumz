from .shared import load_blend_data


def test_versioning_archetype_uuids():
    data = load_blend_data("v260_archetype_uuids.blend")

    UUID_LENGTH = 36
    all_uuids = set()

    def _check_uuid(uuid: str, who):
        assert len(uuid) == UUID_LENGTH, f"UUID of '{who}' is invalid: {uuid}"
        assert uuid not in all_uuids, f"UUID of '{who}' already in use: {uuid}"
        all_uuids.add(uuid)

    for scene in data.scenes:
        for ytyp in scene.ytyps:
            for arch in ytyp.get("archetypes", []):
                arch_uuid = arch["uuid"]
                _check_uuid(arch_uuid, arch)
                for e in arch.get("entities", []):
                    _check_uuid(e["uuid"], e)
                    assert e["mlo_archetype_uuid"] == arch_uuid
                for s in arch.get("entity_sets", []):
                    _check_uuid(s["uuid"], s)
                    assert s["mlo_archetype_uuid"] == arch_uuid
                for p in arch.get("portals", []):
                    _check_uuid(p["uuid"], p)
                    assert p["mlo_archetype_uuid"] == arch_uuid
                for r in arch.get("rooms", []):
                    _check_uuid(r["uuid"], r)
                    assert r["mlo_archetype_uuid"] == arch_uuid
                for tcm in arch.get("timecycle_modifiers", []):
                    assert tcm["mlo_archetype_uuid"] == arch_uuid
