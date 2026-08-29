from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DashboardSummary(BaseModel):
    total_users: int
    total_candidates: int
    total_admins: int
    total_jobs: int
    total_categories: int
    total_applications: int
    pending_applications: int
    accepted_applications: int
    rejected_applications: int


class RecentApplicationResponse(BaseModel):
    id: int
    status: str
    created_at: datetime
    candidate_id: int
    candidate_full_name: str
    candidate_email: str
    job_id: int
    job_title: str
    company: str


class RecentJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    company: str
    location: str
    category_name: str
    created_at: datetime
