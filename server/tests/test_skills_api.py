import pytest
import pytest_asyncio

from orchestrator.services import skill_service
from orchestrator.services.skill_parser import ParsedSkill


@pytest_asyncio.fixture
async def skill_storage(tmp_path, monkeypatch):
    monkeypatch.setattr("orchestrator.services.skill_service.settings.skill_storage_path", str(tmp_path))
    return tmp_path


@pytest.mark.asyncio
async def test_create_and_list_skills(db, skill_storage):
    parsed = ParsedSkill(
        name="code-review",
        description="Reviews code",
        instructions="Check for bugs.",
    )
    skill = await skill_service.create_skill(db, parsed, "default")
    assert skill.name == "code-review"
    assert skill.description == "Reviews code"
    assert skill.instructions == "Check for bugs."
    assert skill.workspace_id == "default"
    assert skill.file_count == 1  # SKILL.md
    assert skill.total_size_bytes > 0

    skills = await skill_service.list_skills(db, "default")
    assert len(skills) == 1
    assert skills[0].name == "code-review"


@pytest.mark.asyncio
async def test_create_skill_with_files(db, skill_storage):
    parsed = ParsedSkill(
        name="deploy-helper",
        description="Helps with deploys",
        instructions="Run the deploy script.",
    )
    extra_files = {
        "scripts/deploy.sh": b"#!/bin/bash\necho deploy",
        "references/guide.md": b"# Deploy guide\nStep 1...",
    }
    skill = await skill_service.create_skill(db, parsed, "default", extra_files)
    assert skill.file_count == 3  # SKILL.md + 2 extra files

    files = await skill_service.get_skill_files(db, skill.id)
    paths = {f.file_path for f in files}
    assert "SKILL.md" in paths
    assert "scripts/deploy.sh" in paths
    assert "references/guide.md" in paths

    # Verify files on disk
    assert (skill_storage / "default" / "deploy-helper" / "scripts" / "deploy.sh").exists()
    assert (skill_storage / "default" / "deploy-helper" / "references" / "guide.md").exists()


@pytest.mark.asyncio
async def test_get_skill(db, skill_storage):
    parsed = ParsedSkill(name="my-skill", description="Test", instructions="Do stuff.")
    skill = await skill_service.create_skill(db, parsed, "default")

    found = await skill_service.get_skill(db, skill.id, "default")
    assert found is not None
    assert found.name == "my-skill"

    # Wrong workspace returns None
    not_found = await skill_service.get_skill(db, skill.id, "other-workspace")
    assert not_found is None


@pytest.mark.asyncio
async def test_get_skill_by_name(db, skill_storage):
    parsed = ParsedSkill(name="by-name", description="Test", instructions="Body.")
    await skill_service.create_skill(db, parsed, "default")

    found = await skill_service.get_skill_by_name(db, "by-name", "default")
    assert found is not None
    assert found.name == "by-name"

    not_found = await skill_service.get_skill_by_name(db, "by-name", "other")
    assert not_found is None


@pytest.mark.asyncio
async def test_update_skill(db, skill_storage):
    parsed = ParsedSkill(name="updatable", description="Old desc", instructions="Old.")
    skill = await skill_service.create_skill(db, parsed, "default")

    from orchestrator.schemas.skills import SkillUpdate
    updated = await skill_service.update_skill(
        db, skill.id, SkillUpdate(description="New desc"), "default"
    )
    assert updated is not None
    assert updated.description == "New desc"
    assert updated.instructions == "Old."  # unchanged


@pytest.mark.asyncio
async def test_delete_skill(db, skill_storage):
    parsed = ParsedSkill(name="delete-me", description="Test", instructions="Body.")
    skill = await skill_service.create_skill(db, parsed, "default")

    assert (skill_storage / "default" / "delete-me").exists()

    result = await skill_service.delete_skill(db, skill.id, "default")
    assert result is True

    # Disk cleaned up
    assert not (skill_storage / "default" / "delete-me").exists()

    # DB cleaned up
    assert await skill_service.get_skill(db, skill.id) is None
    assert await skill_service.get_skill_files(db, skill.id) == []


@pytest.mark.asyncio
async def test_delete_skill_not_found(db, skill_storage):
    result = await skill_service.delete_skill(db, "nonexistent", "default")
    assert result is False


@pytest.mark.asyncio
async def test_workspace_isolation(db, skill_storage):
    parsed1 = ParsedSkill(name="shared-name", description="WS1", instructions="Body 1.")
    await skill_service.create_skill(db, parsed1, "default")

    # Same name in different workspace should work
    parsed2 = ParsedSkill(name="shared-name", description="WS2", instructions="Body 2.")

    # Create the workspace for the test
    from orchestrator.models.workspace import Workspace
    from orchestrator.models.workspace_member import WorkspaceMember
    db.add(Workspace(id="ws2", name="Workspace 2", slug="ws2"))
    db.add(WorkspaceMember(id="admin-ws2", workspace_id="ws2", user_id="admin", role="owner"))
    await db.commit()

    await skill_service.create_skill(db, parsed2, "ws2")

    ws1_skills = await skill_service.list_skills(db, "default")
    ws2_skills = await skill_service.list_skills(db, "ws2")
    assert len(ws1_skills) == 1
    assert len(ws2_skills) == 1
    assert ws1_skills[0].description == "WS1"
    assert ws2_skills[0].description == "WS2"
