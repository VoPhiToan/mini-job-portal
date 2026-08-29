from pydantic import BaseModel

from app.schemas.job import JobResponse


class JobPaginatedResponse(BaseModel):
    items: list[JobResponse]
    total: int
    skip: int
    limit: int
