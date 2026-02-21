from datetime import datetime

from pydantic import BaseModel


class CredentialCreate(BaseModel):
    name: str
    env_var: str
    value: str
    description: str | None = None


class CredentialUpdate(BaseModel):
    name: str | None = None
    env_var: str | None = None
    value: str | None = None
    description: str | None = None


class CredentialResponse(BaseModel):
    id: str
    name: str
    env_var: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
