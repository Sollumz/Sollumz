import textwrap

from ..dependencies import (
    Dependency,
    generate_requirements_file_contents,
)

TEST_DEPS = (
    Dependency(
        "a",
        "A",
        True,
        True,
        "",
        "Test dep A.",
        True,
        "",
        "1.2.3",
        ("123abc",),
    ),
    Dependency(
        "b",
        "B",
        False,
        True,
        "",
        "Test dep B.",
        False,
        "https://example.org/whl/",
        "0.1.2",
        ("abcdef", "deadbeef", "123456"),
    ),
    Dependency(
        "c",
        "C",
        False,
        True,
        "",
        "Test dep C.",
        False,
        "https://example.org/other/whl/",
        "0.0.1",
        ("def456",),
    ),
)


def test_deps_generate_requirements_file_contents():
    expected_contents = textwrap.dedent("""\
        --extra-index-url https://example.org/whl/
        --extra-index-url https://example.org/other/whl/
        a==1.2.3 --hash=sha256:123abc
        b==0.1.2 --hash=sha256:abcdef --hash=sha256:deadbeef --hash=sha256:123456
        c==0.0.1 --hash=sha256:def456
    """)
    contents = generate_requirements_file_contents(TEST_DEPS, None)

    assert expected_contents == contents


def test_deps_generate_requirements_file_contents_with_offline_index():
    expected_contents = textwrap.dedent("""\
        --no-index
        --find-links some/dir/my_offline_index/
        a==1.2.3 --hash=sha256:123abc
        b==0.1.2 --hash=sha256:abcdef --hash=sha256:deadbeef --hash=sha256:123456
        c==0.0.1 --hash=sha256:def456
    """)
    contents = generate_requirements_file_contents(TEST_DEPS, "some/dir/my_offline_index/")

    assert expected_contents == contents
