from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SalaryValidationMixin(BaseModel):
    salary_min: int | None = Field(default=None, ge=0)
    salary_max: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_salary_range(self):
        if (
            self.salary_min is not None
            and self.salary_max is not None
            and self.salary_max < self.salary_min
        ):
            raise ValueError("salary_max must be greater than or equal to salary_min")
        return self


class JobBase(SalaryValidationMixin):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=3, max_length=150)
    company: str = Field(min_length=1, max_length=150)
    location: str = Field(min_length=1, max_length=150)
    description: str = Field(min_length=1)
    category_id: int = Field(gt=0)


class JobCreate(JobBase):
    pass


class JobUpdate(SalaryValidationMixin):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str | None = Field(default=None, min_length=3, max_length=150)
    company: str | None = Field(default=None, min_length=1, max_length=150)
    location: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = Field(default=None, min_length=1)
    category_id: int | None = Field(default=None, gt=0)


class JobResponse(JobBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_name: str
    created_at: datetime
    updated_at: datetime
