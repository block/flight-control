import hashlib
import logging
import mimetypes
import shutil
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from orchestrator.config import settings
from orchestrator.models.skill import Skill
from orchestrator.models.skill_file import SkillFile
from orchestrator.schemas.skills import SkillUpdate
from orchestrator.services.skill_parser import ParsedSkill

logger = logging.getLogger(__name__)


def _skill_dir(workspace_id: str, skill_name: str) -> Path:
    return Path(settings.skill_storage_path) / workspace_id / skill_name


def _ensure_skill_dir(workspace_id: str, skill_name: str) -> Path:
    d = _skill_dir(workspace_id, skill_name)
    d.mkdir(parents=True, exist_ok=True)
    return d


async def list_skills(db: AsyncSession, workspace_id: str) -> list[Skill]:
    result = await db.execute(
        select(Skill)
        .where(Skill.workspace_id == workspace_id)
        .order_by(Skill.name)
    )
    return list(result.scalars().all())


async def get_skill(db: AsyncSession, skill_id: str, workspace_id: str | None = None) -> Skill | None:
    query = select(Skill).where(Skill.id == skill_id)
    if workspace_id:
        query = query.where(Skill.workspace_id == workspace_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_skill_by_name(db: AsyncSession, name: str, workspace_id: str) -> Skill | None:
    result = await db.execute(
        select(Skill).where(Skill.workspace_id == workspace_id, Skill.name == name)
    )
    return result.scalar_one_or_none()


async def get_skill_files(db: AsyncSession, skill_id: str) -> list[SkillFile]:
    result = await db.execute(
        select(SkillFile)
        .where(SkillFile.skill_id == skill_id)
        .order_by(SkillFile.file_path)
    )
    return list(result.scalars().all())


async def create_skill(
    db: AsyncSession,
    parsed: ParsedSkill,
    workspace_id: str,
    files: dict[str, bytes] | None = None,
) -> Skill:
    """Create a skill from parsed SKILL.md data and optional extra files.

    Args:
        db: Database session.
        parsed: Parsed SKILL.md frontmatter and body.
        workspace_id: Workspace scope.
        files: Dict of {relative_path: file_bytes} for additional files.
    """
    skill = Skill(
        workspace_id=workspace_id,
        name=parsed.name,
        description=parsed.description,
        license=parsed.license,
        compatibility=parsed.compatibility,
        metadata_kv=parsed.metadata,
        allowed_tools=parsed.allowed_tools,
        instructions=parsed.instructions,
    )
    db.add(skill)
    await db.flush()  # get skill.id

    skill_dir = _ensure_skill_dir(workspace_id, parsed.name)

    # Always store the SKILL.md itself
    all_files: dict[str, bytes] = {"SKILL.md": _rebuild_skill_md(parsed).encode()}
    if files:
        all_files.update(files)

    total_size = 0
    file_count = 0

    for file_path, data in all_files.items():
        # Write to disk
        dest = skill_dir / file_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)

        checksum = hashlib.sha256(data).hexdigest()
        content_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"

        sf = SkillFile(
            skill_id=skill.id,
            file_path=file_path,
            size_bytes=len(data),
            checksum_sha256=checksum,
            content_type=content_type,
        )
        db.add(sf)
        total_size += len(data)
        file_count += 1

    skill.total_size_bytes = total_size
    skill.file_count = file_count

    await db.commit()
    await db.refresh(skill)
    return skill


async def update_skill(
    db: AsyncSession, skill_id: str, data: SkillUpdate, workspace_id: str
) -> Skill | None:
    skill = await get_skill(db, skill_id, workspace_id)
    if not skill:
        return None
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(skill, field, value)
    await db.commit()
    await db.refresh(skill)
    return skill


async def delete_skill(db: AsyncSession, skill_id: str, workspace_id: str) -> bool:
    skill = await get_skill(db, skill_id, workspace_id)
    if not skill:
        return False

    # Delete files from disk
    skill_dir = _skill_dir(workspace_id, skill.name)
    if skill_dir.exists():
        shutil.rmtree(skill_dir)

    # Delete skill_files records
    files = await get_skill_files(db, skill_id)
    for f in files:
        await db.delete(f)

    await db.delete(skill)
    await db.commit()
    return True


def get_skill_file_path(workspace_id: str, skill_name: str, file_path: str) -> Path:
    """Return the absolute path to a skill file on disk."""
    return _skill_dir(workspace_id, skill_name) / file_path


def _rebuild_skill_md(parsed: ParsedSkill) -> str:
    """Rebuild SKILL.md content from parsed data."""
    frontmatter: dict = {
        "name": parsed.name,
        "description": parsed.description,
    }
    if parsed.license:
        frontmatter["license"] = parsed.license
    if parsed.compatibility:
        frontmatter["compatibility"] = parsed.compatibility
    if parsed.metadata:
        frontmatter["metadata"] = parsed.metadata
    if parsed.allowed_tools:
        frontmatter["allowed-tools"] = parsed.allowed_tools

    import yaml
    fm_str = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False).strip()
    return f"---\n{fm_str}\n---\n\n{parsed.instructions}\n"
