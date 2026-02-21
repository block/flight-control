import io
import zipfile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from orchestrator.auth import AuthContext, require_auth
from orchestrator.database import get_db
from orchestrator.schemas.skills import (
    SkillDetailResponse,
    SkillFileResponse,
    SkillSummaryResponse,
    SkillUpdate,
)
from orchestrator.services import skill_service
from orchestrator.services.skill_parser import parse_skill_md

router = APIRouter(prefix="/skills", tags=["skills"])

MAX_ZIP_EXTRACTED_SIZE = 50 * 1024 * 1024  # 50 MB
MAX_ZIP_FILE_COUNT = 500


@router.get("", response_model=list[SkillSummaryResponse])
async def list_skills(
    auth: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    return await skill_service.list_skills(db, auth.workspace_id)


@router.get("/{skill_id}", response_model=SkillDetailResponse)
async def get_skill(
    skill_id: str,
    auth: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    skill = await skill_service.get_skill(db, skill_id, auth.workspace_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    files = await skill_service.get_skill_files(db, skill_id)
    return SkillDetailResponse(
        id=skill.id,
        workspace_id=skill.workspace_id,
        name=skill.name,
        description=skill.description,
        license=skill.license,
        compatibility=skill.compatibility,
        metadata_kv=skill.metadata_kv,
        allowed_tools=skill.allowed_tools,
        instructions=skill.instructions,
        total_size_bytes=skill.total_size_bytes,
        file_count=skill.file_count,
        created_at=skill.created_at,
        updated_at=skill.updated_at,
        files=[SkillFileResponse.model_validate(f) for f in files],
    )


@router.post("", response_model=SkillSummaryResponse, status_code=201)
async def upload_skill(
    skill_md: UploadFile = File(..., description="SKILL.md file"),
    files: list[UploadFile] = File(default=[], description="Additional skill files"),
    zip_file: UploadFile | None = File(default=None, description="Zip archive of skill"),
    auth: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    # Read and parse SKILL.md
    skill_md_content = (await skill_md.read()).decode("utf-8")
    try:
        parsed = parse_skill_md(skill_md_content)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Check for duplicate name
    existing = await skill_service.get_skill_by_name(db, parsed.name, auth.workspace_id)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Skill '{parsed.name}' already exists in this workspace",
        )

    extra_files: dict[str, bytes] = {}

    if zip_file:
        zip_data = await zip_file.read()
        try:
            extra_files = _extract_zip(zip_data)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
    elif files:
        for f in files:
            data = await f.read()
            if f.filename:
                extra_files[f.filename] = data

    skill = await skill_service.create_skill(db, parsed, auth.workspace_id, extra_files or None)
    return skill


@router.put("/{skill_id}", response_model=SkillSummaryResponse)
async def update_skill(
    skill_id: str,
    data: SkillUpdate,
    auth: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    skill = await skill_service.update_skill(db, skill_id, data, auth.workspace_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


@router.delete("/{skill_id}", status_code=204)
async def delete_skill(
    skill_id: str,
    auth: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    if not await skill_service.delete_skill(db, skill_id, auth.workspace_id):
        raise HTTPException(status_code=404, detail="Skill not found")


@router.get("/{skill_id}/files/{file_path:path}")
async def download_skill_file(
    skill_id: str,
    file_path: str,
    auth: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    skill = await skill_service.get_skill(db, skill_id, auth.workspace_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    abs_path = skill_service.get_skill_file_path(auth.workspace_id, skill.name, file_path)
    if not abs_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(path=str(abs_path), filename=abs_path.name)


def _extract_zip(data: bytes) -> dict[str, bytes]:
    """Extract files from a zip archive with safety checks."""
    result: dict[str, bytes] = {}
    total_size = 0

    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        entries = [i for i in zf.infolist() if not i.is_dir()]
        if len(entries) > MAX_ZIP_FILE_COUNT:
            raise ValueError(f"Zip contains too many files (max {MAX_ZIP_FILE_COUNT})")

        for info in entries:
            if ".." in info.filename or info.filename.startswith("/"):
                raise ValueError(f"Unsafe path in zip: {info.filename}")

            file_data = zf.read(info)
            total_size += len(file_data)
            if total_size > MAX_ZIP_EXTRACTED_SIZE:
                raise ValueError(f"Zip extracted size exceeds limit ({MAX_ZIP_EXTRACTED_SIZE // (1024*1024)}MB)")

            # Skip SKILL.md from zip — we use the explicitly uploaded one
            if info.filename == "SKILL.md":
                continue

            result[info.filename] = file_data

    return result
