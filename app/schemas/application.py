from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    job_id: int
    status: str
    created_at: datetime


class ApplicationJobSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    company: str
    location: str


class ApplicationWithJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    created_at: datetime
    job: ApplicationJobSummary


class ApplicationCandidateSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: str


class ApplicationAdminJobSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    company: str


class ApplicationAdminResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    created_at: datetime
    candidate: ApplicationCandidateSummary
    job: ApplicationAdminJobSummary


class ApplicationStatusUpdate(BaseModel):
    status: Literal["pending", "accepted", "rejected"]
