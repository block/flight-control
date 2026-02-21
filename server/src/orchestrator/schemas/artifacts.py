from datetime import datetime

from pydantic import BaseModel


class ArtifactResponse(BaseModel):
    id: str
    run_id: str
    filename: str
    content_type: str
    size_bytes: int
    checksum_sha256: str
    created_at: datetime

    model_config = {"from_attributes": True}
