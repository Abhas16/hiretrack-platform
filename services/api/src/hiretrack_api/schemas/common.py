from pydantic import BaseModel, ConfigDict


class ReadModel(BaseModel):
    """Base for response DTOs; can be built straight from ORM objects."""

    model_config = ConfigDict(from_attributes=True)


class WriteModel(BaseModel):
    """Base for request DTOs; unknown fields are rejected with 422 instead of ignored."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Page[T](BaseModel):
    items: list[T]
    total: int
    page: int
    page_size: int
