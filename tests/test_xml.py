import pytest
from ..cwxml.element import get_str_type, ElementTree, ValueProperty
from ..cwxml.ymap import HexColorProperty


@pytest.mark.parametrize("string, expected", (
    ("true", True),
    ("True", True),
    ("TrUE", True),
    ("false", False),
    ("False", False),
    ("FALsE", False),
))
def test_xml_bool(string, expected):
    assert get_str_type(string) == expected


@pytest.mark.parametrize("bool_value, expected", (
    (True, "true"),
    (False, "false"),
))
def test_xml_bool_output(bool_value: bool, expected: str):
    class Data(ElementTree):
        tag_name = "Data"

        def __init__(self):
            self.v = ValueProperty("v")

    d = Data()
    d.v = bool_value
    xml = d.to_xml()
    assert xml.find("v").attrib["value"] == expected


@pytest.mark.parametrize("argb_hex, expected_rgba", (
    ("0x00FF0000", (1.0, 0.0, 0.0, 0.0)),
    ("0x0000FF00", (0.0, 1.0, 0.0, 0.0)),
    ("0x000000FF", (0.0, 0.0, 1.0, 0.0)),
    ("0xFF000000", (0.0, 0.0, 0.0, 1.0)),
    ("0x90909090", (0x90 / 0xFF,) * 4),
))
def test_argb_hex_to_rgba(argb_hex, expected_rgba):
    assert HexColorProperty.argb_hex_to_rgba(argb_hex) == expected_rgba


@pytest.mark.parametrize("rgba, expected_argb_hex", (
    ((1.0, 0.0, 0.0, 0.0), "0x00FF0000"),
    ((0.0, 1.0, 0.0, 0.0), "0x0000FF00"),
    ((0.0, 0.0, 1.0, 0.0), "0x000000FF"),
    ((0.0, 0.0, 0.0, 1.0), "0xFF000000"),
    ((0x90 / 0xFF,) * 4, "0x90909090"),
))
def test_rgba_to_argb_hex(rgba, expected_argb_hex):
    assert HexColorProperty.rgba_to_argb_hex(rgba) == expected_argb_hex
