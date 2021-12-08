import uuid
from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel, validator, AnyHttpUrl, UUID4, Field

from app.core.config import settings


class ProjectBase(BaseModel):
    name: str
    domain_name: AnyHttpUrl
    enabled_currency: Optional[List[str]]
    webhook_url: Optional[AnyHttpUrl]

    @validator("enabled_currency", each_item=True)
    def validate_enabled_currency(cls, v: Optional[List[str]]):
        if v not in settings.ALLOWED_CURRENCY_NAME:
            raise ValueError(f'{v} is not a valid allowed currency')
        return v

    class Config:
        min_anystr_length = 1


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(ProjectBase):
    pass


class ProjectDB(ProjectBase):
    owner_id: UUID4
    api_key_hashed: str
    payment_signature_secret: str
    id: UUID4 = Field(default_factory=uuid.uuid4)

    class Config:
        orm_mode = True


class Project(BaseModel):
    id: UUID4
    name: str
    enabled_currency: Optional[List[str]]
    date_created: Optional[datetime]
    domain_name: Optional[AnyHttpUrl]
    webhook_url: Optional[AnyHttpUrl]


class ProjectCreateResponse(Project):
    api_key: str
    payment_signature_secret: str


class ProjectStats(BaseModel):
    total_project: int
    verified_domain: int
    active_project: int
