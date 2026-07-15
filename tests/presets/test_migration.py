"""Tests for the legacy XML -> JSON migration."""

import pytest

from ...shared.presets import migration, store
from ...ybn.gta5.presets.flag import FLAG_PRESET_CATEGORY
from ...ydr.gta5.presets.light import LIGHT_PRESET_CATEGORY
from ...ydr.gta5.presets.shader import SHADER_PRESET_CATEGORY


_FLAG_XML = """<?xml version='1.0' encoding='UTF-8'?>
<FlagPresetsFile>
  <Presets>
    <Item name="My Flags">
      <Flags1>map_animal, map_cover</Flags1>
      <Flags2>ped, glass</Flags2>
    </Item>
  </Presets>
</FlagPresetsFile>
"""

_LIGHT_XML = """<?xml version='1.0' encoding='UTF-8'?>
<LightPresetsFile>
  <LightPresets>
    <Item name="My Light">
      <Color x="1.0" y="0.5" z="0.0" />
      <Energy value="100" />
      <TimeFlags value="5" />
      <Flags value="3" />
      <Flashiness>CONSTANT</Flashiness>
    </Item>
  </LightPresets>
</LightPresetsFile>
"""

_SHADER_XML = """<?xml version='1.0' encoding='UTF-8'?>
<ShaderPresetsFile>
  <ShaderPresets>
    <ShaderPreset name="My Shader">
      <Param name="Diffuse" x="1.0" y="2.0" z="3.0" w="4.0" />
      <Param name="DiffuseTex" texture="my_tex" />
    </ShaderPreset>
  </ShaderPresets>
</ShaderPresetsFile>
"""


def _check_flag(presets):
    assert len(presets) == 1
    assert presets[0]["name"] == "My Flags"
    assert presets[0]["data"]["composite_flags1"] == {"map_animal": True, "map_cover": True}
    assert presets[0]["data"]["composite_flags2"] == {"ped": True, "glass": True}


def _check_light(presets):
    assert len(presets) == 1
    data = presets[0]["data"]
    assert presets[0]["name"] == "My Light"
    assert data["light"]["color"] == [1.0, 0.5, 0.0]
    assert data["light"]["energy"] == 100.0
    assert data["time_flags"] == "5"
    assert data["light_flags"] == "3"
    assert data["light_properties"]["flashiness"] == "CONSTANT"


def _check_shader(presets):
    assert len(presets) == 1
    assert presets[0]["name"] == "My Shader"
    assert presets[0]["data"]["params"] == [
        {"name": "Diffuse", "x": 1.0, "y": 2.0, "z": 3.0, "w": 4.0},
        {"name": "DiffuseTex", "texture": "my_tex"},
    ]


@pytest.mark.parametrize(
    "category, xml_text, check",
    [
        (FLAG_PRESET_CATEGORY, _FLAG_XML, _check_flag),
        (LIGHT_PRESET_CATEGORY, _LIGHT_XML, _check_light),
        (SHADER_PRESET_CATEGORY, _SHADER_XML, _check_shader),
    ],
    ids=["flag", "light", "shader"],
)
def test_migration(preset_config_dir, category, xml_text, check):
    xml_path = preset_config_dir / "{}_presets.xml".format(category.id)
    xml_path.write_text(xml_text, encoding="utf-8")

    result = migration.migrate_if_needed(category)

    assert result == store.user_preset_path(category)
    assert not xml_path.exists()
    assert xml_path.with_suffix(xml_path.suffix + ".bak").is_file()

    store.invalidate(category)
    check(store.load_presets(category))
