import hashlib

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from orchestrator.models.artifact import Artifact
from orchestrator.storage import get_storage


async def save_artifact(
    db: AsyncSession,
    run_id: str,
    filename: str,
    data: bytes,
    content_type: str,
    workspace_id: str = "default",
) -> Artifact:
    checksum = hashlib.sha256(data).hexdigest()
    storage_path = f"{run_id}/{filename}"

    storage = get_storage()
    await storage.save(storage_path, data)

    artifact = Artifact(
        workspace_id=workspace_id,
        run_id=run_id,
        filename=filename,
        content_type=content_type,
        size_bytes=len(data),
        checksum_sha256=checksum,
        storage_path=storage_path,
    )
    db.add(artifact)
    await db.commit()
    await db.refresh(artifact)
    return artifact


async def list_artifacts(db: AsyncSession, run_id: str) -> list[Artifact]:
    result = await db.execute(
        select(Artifact)
        .where(Artifact.run_id == run_id)
        .order_by(Artifact.created_at.asc())
    )
    return list(result.scalars().all())


async def get_artifact(db: AsyncSession, artifact_id: str) -> Artifact | None:
    result = await db.execute(
        select(Artifact).where(Artifact.id == artifact_id)
    )
    return result.scalar_one_or_none()


async def read_artifact_data(artifact: Artifact) -> bytes:
    storage = get_storage()
    return await storage.read(artifact.storage_path)
