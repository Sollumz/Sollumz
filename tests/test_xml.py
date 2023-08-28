import pytest
from ..cwxml.element import get_str_type

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
