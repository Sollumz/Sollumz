import pytest
from ..cwxml.element import get_str_type, ElementTree, ValueProperty


@pytest.mark.parametrize(
    "string, expected",
    (
        ("true", True),
        ("True", True),
        ("TrUE", True),
        ("false", False),
        ("False", False),
        ("FALsE", False),
    ),
)
def test_xml_bool(string, expected):
    assert get_str_type(string) == expected


@pytest.mark.parametrize(
    "bool_value, expected",
    (
        (True, "true"),
        (False, "false"),
    ),
)
def test_xml_bool_output(bool_value: bool, expected: str):
    class Data(ElementTree):
        tag_name = "Data"

        def __init__(self):
            self.v = ValueProperty("v")

    d = Data()
    d.v = bool_value
    xml = d.to_xml()
    assert xml.find("v").attrib["value"] == expected
