import pytest

from orchestrator.services.skill_parser import parse_skill_md


VALID_SKILL_MD = """---
name: code-review
description: Performs thorough code reviews
license: MIT
compatibility: goose
metadata:
  author: acme
  version: "1.0"
allowed-tools: bash,read
---

# Code Review Instructions

Review the code for:
- Security issues
- Performance problems
- Style violations
"""

MINIMAL_SKILL_MD = """---
name: my-skill
description: A simple skill
---

Do the thing.
"""


def test_parse_valid_skill():
    parsed = parse_skill_md(VALID_SKILL_MD)
    assert parsed.name == "code-review"
    assert parsed.description == "Performs thorough code reviews"
    assert parsed.license == "MIT"
    assert parsed.compatibility == "goose"
    assert parsed.metadata == {"author": "acme", "version": "1.0"}
    assert parsed.allowed_tools == "bash,read"
    assert "Security issues" in parsed.instructions


def test_parse_minimal_skill():
    parsed = parse_skill_md(MINIMAL_SKILL_MD)
    assert parsed.name == "my-skill"
    assert parsed.description == "A simple skill"
    assert parsed.license is None
    assert parsed.compatibility is None
    assert parsed.metadata is None
    assert parsed.allowed_tools is None
    assert parsed.instructions == "Do the thing."


def test_empty_content():
    with pytest.raises(ValueError, match="empty"):
        parse_skill_md("")


def test_no_frontmatter():
    with pytest.raises(ValueError, match="frontmatter"):
        parse_skill_md("# Just markdown")


def test_missing_name():
    with pytest.raises(ValueError, match="name"):
        parse_skill_md("---\ndescription: test\n---\nBody")


def test_missing_description():
    with pytest.raises(ValueError, match="description"):
        parse_skill_md("---\nname: test\n---\nBody")


def test_invalid_name_uppercase():
    with pytest.raises(ValueError, match="name"):
        parse_skill_md("---\nname: MySkill\ndescription: test\n---\nBody")


def test_invalid_name_double_hyphen():
    with pytest.raises(ValueError, match="hyphen"):
        parse_skill_md("---\nname: my--skill\ndescription: test\n---\nBody")


def test_invalid_name_starts_with_hyphen():
    with pytest.raises(ValueError, match="name"):
        parse_skill_md("---\nname: -bad\ndescription: test\n---\nBody")


def test_name_too_long():
    long_name = "a" * 65
    with pytest.raises(ValueError, match="64"):
        parse_skill_md(f"---\nname: {long_name}\ndescription: test\n---\nBody")


def test_description_too_long():
    long_desc = "x" * 1025
    with pytest.raises(ValueError, match="1024"):
        parse_skill_md(f"---\nname: test\ndescription: {long_desc}\n---\nBody")


def test_invalid_yaml():
    with pytest.raises(ValueError, match="YAML"):
        parse_skill_md("---\n: [invalid yaml\n---\nBody")


def test_metadata_must_be_mapping():
    with pytest.raises(ValueError, match="metadata"):
        parse_skill_md("---\nname: test\ndescription: test\nmetadata: not-a-dict\n---\nBody")


def test_single_char_name():
    parsed = parse_skill_md("---\nname: a\ndescription: test\n---\nBody")
    assert parsed.name == "a"


def test_max_length_name():
    name = "a" + "b" * 62 + "c"  # 64 chars
    parsed = parse_skill_md(f"---\nname: {name}\ndescription: test\n---\nBody")
    assert parsed.name == name
