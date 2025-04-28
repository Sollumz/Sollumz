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
            for arch in ytyp.get("archetypes_", []):
                arch_uuid = arch["uuid"]
                _check_uuid(arch_uuid, arch)
                for e in arch.get("entities_", []):
                    _check_uuid(e["uuid"], e)
                    assert e["mlo_archetype_uuid"] == arch_uuid
                for s in arch.get("entity_sets_", []):
                    _check_uuid(s["uuid"], s)
                    assert s["mlo_archetype_uuid"] == arch_uuid
                for p in arch.get("portals_", []):
                    _check_uuid(p["uuid"], p)
                    assert p["mlo_archetype_uuid"] == arch_uuid
                for r in arch.get("rooms_", []):
                    _check_uuid(r["uuid"], r)
                    assert r["mlo_archetype_uuid"] == arch_uuid
                for tcm in arch.get("timecycle_modifiers_", []):
                    assert tcm["mlo_archetype_uuid"] == arch_uuid


def test_versioning_archetype_multiselect_collections():
    data = load_blend_data("v260_archetype_multiselect_collections.blend")

    UUID_LENGTH = 36
    all_uuids = set()

    def _check_uuid(uuid: str, who):
        assert len(uuid) == UUID_LENGTH, f"UUID of '{who}' is invalid: {uuid}"
        assert uuid not in all_uuids, f"UUID of '{who}' already in use: {uuid}"
        all_uuids.add(uuid)

    for scene in data.scenes:
        for ytyp in scene.ytyps:
            assert "archetypes_" in ytyp
            archetypes = ytyp["archetypes_"]
            assert len(archetypes) == 3
            assert archetypes[0]["name"] == "test_mlo"
            assert archetypes[1]["name"] == "test_prop_01"
            assert archetypes[2]["name"] == "test_prop_02"

            mlo = archetypes[0]

            assert "rooms_" in mlo
            rooms = mlo["rooms_"]
            assert len(rooms) == 2
            assert rooms[0]["name"] == "room01"
            assert rooms[1]["name"] == "room02"

            assert "portals_" in mlo
            portals = mlo["portals_"]
            assert len(portals) == 2
            assert portals[0]["room_from_id"] == rooms[1]["id"]
            assert portals[1]["room_from_id"] == rooms[0]["id"]

            assert "entities_" in mlo
            entities = mlo["entities_"]
            assert len(entities) == 3
            assert entities[0]["archetype_name"] == "entity01"
            assert entities[1]["archetype_name"] == "entity02"
            assert entities[2]["archetype_name"] == "entity03"

            assert "timecycle_modifiers_" in mlo
            tcms = mlo["timecycle_modifiers_"]
            assert len(tcms) == 2
            assert tcms[0]["name"] == "tcm01"
            assert tcms[1]["name"] == "tcm02"

            assert "entity_sets_" in mlo
            entity_sets = mlo["entity_sets_"]
            assert len(entity_sets) == 2
            assert entity_sets[0]["name"] == "set01"
            assert entity_sets[1]["name"] == "set02"
