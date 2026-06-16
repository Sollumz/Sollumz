"""Unit tests for the three legacy preset XML converters (flag/light/shader)."""

from ...ybn.gta5.presets.flag import _convert_legacy_xml as convert_flag
from ...ydr.gta5.presets.light import _convert_legacy_xml as convert_light
from ...ydr.gta5.presets.shader import _convert_legacy_xml as convert_shader


def _write(tmp_path, text):
    path = tmp_path / "legacy.xml"
    path.write_text(text, encoding="utf-8")
    return path


def test_flag_basic(tmp_path):
    xml = """<?xml version='1.0' encoding='UTF-8'?>
<FlagPresetsFile>
  <Presets>
    <Item name="A">
      <Flags1>map_animal, map_cover, map_dynamic</Flags1>
      <Flags2>ped</Flags2>
    </Item>
  </Presets>
</FlagPresetsFile>
"""
    presets = convert_flag(_write(tmp_path, xml))
    assert presets == [
        {
            "name": "A",
            "data": {
                "composite_flags1": {"map_animal": True, "map_cover": True, "map_dynamic": True},
                "composite_flags2": {"ped": True},
            },
        }
    ]


def test_flag_whitespace_trimmed_and_missing_group(tmp_path):
    xml = """<FlagPresetsFile><Presets>
      <Item name="A"><Flags1>  map_animal ,map_cover ,  map_dynamic  </Flags1></Item>
    </Presets></FlagPresetsFile>"""
    presets = convert_flag(_write(tmp_path, xml))
    assert presets[0]["data"]["composite_flags1"] == {
        "map_animal": True,
        "map_cover": True,
        "map_dynamic": True,
    }
    # Missing <Flags2> -> empty dict.
    assert presets[0]["data"]["composite_flags2"] == {}


def test_flag_empty_flags_element(tmp_path):
    xml = """<FlagPresetsFile><Presets>
      <Item name="A"><Flags1>   </Flags1><Flags2></Flags2></Item>
    </Presets></FlagPresetsFile>"""
    presets = convert_flag(_write(tmp_path, xml))
    assert presets[0]["data"]["composite_flags1"] == {}
    assert presets[0]["data"]["composite_flags2"] == {}


def test_flag_missing_name_skipped(tmp_path):
    xml = """<FlagPresetsFile><Presets>
      <Item><Flags1>map_animal</Flags1></Item>
      <Item name="B"><Flags1>map_cover</Flags1></Item>
    </Presets></FlagPresetsFile>"""
    presets = convert_flag(_write(tmp_path, xml))
    assert [p["name"] for p in presets] == ["B"]


def test_flag_multiple_items_keep_order(tmp_path):
    xml = """<FlagPresetsFile><Presets>
      <Item name="First"><Flags1>map_animal</Flags1></Item>
      <Item name="Second"><Flags1>map_cover</Flags1></Item>
      <Item name="Third"><Flags1>map_dynamic</Flags1></Item>
    </Presets></FlagPresetsFile>"""
    presets = convert_flag(_write(tmp_path, xml))
    assert [p["name"] for p in presets] == ["First", "Second", "Third"]


def test_light_full(tmp_path):
    xml = """<?xml version='1.0' encoding='UTF-8'?>
<LightPresetsFile>
  <LightPresets>
    <Item name="L">
      <Color x="1.0" y="0.5" z="0.25" />
      <Energy value="120" />
      <CutoffDistance value="40" />
      <SpotSize value="2.0" />
      <SpotBlend value="0.5" />
      <TimeFlags value="7" />
      <Flags value="2" />
      <Flashiness>CONSTANT</Flashiness>
      <ProjectedTextureHash>some_hash</ProjectedTextureHash>
      <VolumeSizeScale value="1.5" />
      <Extent x="2.0" y="2.0" z="2.0" />
    </Item>
  </LightPresets>
</LightPresetsFile>
"""
    presets = convert_light(_write(tmp_path, xml))
    assert len(presets) == 1
    assert presets[0]["name"] == "L"
    data = presets[0]["data"]
    assert data["light"]["color"] == [1.0, 0.5, 0.25]
    assert data["light"]["energy"] == 120.0
    assert data["light"]["cutoff_distance"] == 40.0
    assert data["light"]["spot_size"] == 2.0
    assert data["light"]["spot_blend"] == 0.5
    assert data["time_flags"] == "7"
    assert data["light_flags"] == "2"
    assert data["light_properties"]["flashiness"] == "CONSTANT"
    assert data["light_properties"]["projected_texture_hash"] == "some_hash"
    assert data["light_properties"]["volume_size_scale"] == 1.5
    assert data["light_properties"]["extent"] == [2.0, 2.0, 2.0]


def test_light_missing_color_and_energy_defaults(tmp_path):
    xml = """<LightPresetsFile><LightPresets>
      <Item name="L"><Flashiness>CONSTANT</Flashiness></Item>
    </LightPresets></LightPresetsFile>"""
    presets = convert_light(_write(tmp_path, xml))
    data = presets[0]["data"]
    assert data["light"]["color"] == [0.0, 0.0, 0.0]
    assert data["light"]["energy"] == 0.0
    assert data["time_flags"] == "0"
    assert data["light_flags"] == "0"


def test_light_flag_values_coerced_to_int_string(tmp_path):
    # Floats in the legacy XML are normalised to integer strings.
    xml = """<LightPresetsFile><LightPresets>
      <Item name="L"><TimeFlags value="5.0" /><Flags value="8.9" /></Item>
    </LightPresets></LightPresetsFile>"""
    presets = convert_light(_write(tmp_path, xml))
    data = presets[0]["data"]
    assert data["time_flags"] == "5"
    assert data["light_flags"] == "8"


def test_light_non_numeric_energy_defaults(tmp_path):
    xml = """<LightPresetsFile><LightPresets>
      <Item name="L"><Energy value="not-a-number" /></Item>
    </LightPresets></LightPresetsFile>"""
    presets = convert_light(_write(tmp_path, xml))
    assert presets[0]["data"]["light"]["energy"] == 0.0


def test_light_missing_name_skipped(tmp_path):
    xml = """<LightPresetsFile><LightPresets>
      <Item><Energy value="1" /></Item>
      <Item name="Keep"><Energy value="2" /></Item>
    </LightPresets></LightPresetsFile>"""
    presets = convert_light(_write(tmp_path, xml))
    assert [p["name"] for p in presets] == ["Keep"]


def test_shader_basic(tmp_path):
    xml = """<?xml version='1.0' encoding='UTF-8'?>
<ShaderPresetsFile>
  <ShaderPresets>
    <ShaderPreset name="S">
      <Param name="Diffuse" x="1.0" y="2.0" z="3.0" w="4.0" />
      <Param name="DiffuseTex" texture="my_tex" />
    </ShaderPreset>
  </ShaderPresets>
</ShaderPresetsFile>
"""
    presets = convert_shader(_write(tmp_path, xml))
    assert presets == [
        {
            "name": "S",
            "data": {
                "params": [
                    {"name": "Diffuse", "x": 1.0, "y": 2.0, "z": 3.0, "w": 4.0},
                    {"name": "DiffuseTex", "texture": "my_tex"},
                ]
            },
        }
    ]


def test_shader_partial_components(tmp_path):
    xml = """<ShaderPresetsFile><ShaderPresets>
      <ShaderPreset name="S"><Param name="P" x="0.5" /></ShaderPreset>
    </ShaderPresets></ShaderPresetsFile>"""
    presets = convert_shader(_write(tmp_path, xml))
    assert presets[0]["data"]["params"] == [{"name": "P", "x": 0.5}]


def test_shader_bad_float_skipped(tmp_path):
    xml = """<ShaderPresetsFile><ShaderPresets>
      <ShaderPreset name="S"><Param name="P" x="abc" y="2.0" /></ShaderPreset>
    </ShaderPresets></ShaderPresetsFile>"""
    presets = convert_shader(_write(tmp_path, xml))
    # The unparseable x is skipped; the valid y is kept.
    assert presets[0]["data"]["params"] == [{"name": "P", "y": 2.0}]


def test_shader_missing_name_skipped(tmp_path):
    xml = """<ShaderPresetsFile><ShaderPresets>
      <ShaderPreset><Param name="P" x="1.0" /></ShaderPreset>
      <ShaderPreset name="Keep"><Param name="P" x="1.0" /></ShaderPreset>
    </ShaderPresets></ShaderPresetsFile>"""
    presets = convert_shader(_write(tmp_path, xml))
    assert [p["name"] for p in presets] == ["Keep"]


def test_shader_empty_preset(tmp_path):
    xml = """<ShaderPresetsFile><ShaderPresets>
      <ShaderPreset name="S"></ShaderPreset>
    </ShaderPresets></ShaderPresetsFile>"""
    presets = convert_shader(_write(tmp_path, xml))
    assert presets == [{"name": "S", "data": {"params": []}}]
