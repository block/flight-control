"""Parser for SKILL.md files following the agentskills.io specification."""

import re
from dataclasses import dataclass

import yaml

# Skill name: lowercase alphanumeric + hyphens, no double hyphens, 1-64 chars
SKILL_NAME_PATTERN = re.compile(r"^[a-z0-9]([a-z0-9-]{0,62}[a-z0-9])?$")
FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)", re.DOTALL)


@dataclass
class ParsedSkill:
    name: str
    description: str
    instructions: str
    license: str | None = None
    compatibility: str | None = None
    metadata: dict | None = None
    allowed_tools: str | None = None


def parse_skill_md(content: str) -> ParsedSkill:
    """Parse a SKILL.md file into structured data.

    Expects YAML frontmatter delimited by --- followed by markdown body.
    Raises ValueError on invalid input.
    """
    content = content.strip()
    if not content:
        raise ValueError("SKILL.md is empty")

    match = FRONTMATTER_PATTERN.match(content)
    if not match:
        raise ValueError("SKILL.md must start with YAML frontmatter delimited by ---")

    frontmatter_str = match.group(1)
    body = match.group(2).strip()

    try:
        frontmatter = yaml.safe_load(frontmatter_str)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML frontmatter: {e}")

    if not isinstance(frontmatter, dict):
        raise ValueError("YAML frontmatter must be a mapping")

    # Validate name
    name = frontmatter.get("name")
    if not name or not isinstance(name, str):
        raise ValueError("'name' is required in frontmatter")
    name = name.strip()
    if len(name) > 64:
        raise ValueError("'name' must be 64 characters or fewer")
    if not SKILL_NAME_PATTERN.match(name):
        raise ValueError(
            "'name' must be lowercase alphanumeric with hyphens, no double hyphens, "
            "and must start/end with alphanumeric"
        )
    if "--" in name:
        raise ValueError("'name' must not contain consecutive hyphens")

    # Validate description
    description = frontmatter.get("description")
    if not description or not isinstance(description, str):
        raise ValueError("'description' is required in frontmatter")
    description = description.strip()
    if len(description) > 1024:
        raise ValueError("'description' must be 1024 characters or fewer")

    # Optional fields
    license_val = frontmatter.get("license")
    if license_val is not None:
        license_val = str(license_val).strip()

    compatibility = frontmatter.get("compatibility")
    if compatibility is not None:
        compatibility = str(compatibility).strip()

    metadata = frontmatter.get("metadata")
    if metadata is not None and not isinstance(metadata, dict):
        raise ValueError("'metadata' must be a mapping if provided")

    allowed_tools = frontmatter.get("allowed-tools")
    if allowed_tools is not None:
        allowed_tools = str(allowed_tools).strip()

    return ParsedSkill(
        name=name,
        description=description,
        instructions=body,
        license=license_val,
        compatibility=compatibility,
        metadata=metadata,
        allowed_tools=allowed_tools,
    )
