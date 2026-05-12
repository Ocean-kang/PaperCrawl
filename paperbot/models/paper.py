from pydantic import BaseModel, Field


class Paper(BaseModel):
    title: str
    authors: list[str] = Field(default_factory=list)
    abstract: str | None = None
    pdf_url: str | None = None
    detail_url: str | None = None
    conference: str
    year: int
    source: str
    keywords: list[str] = Field(default_factory=list)
    decision: str | None = None
    withdrawn: bool = False
