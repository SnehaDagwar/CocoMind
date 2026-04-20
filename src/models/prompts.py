"""Prompt template models for versioned prompt management."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class PromptVersion(BaseModel):
    """Tracks a specific version of a prompt template."""

    version: str = Field(description="e.g. 'v1.0'")
    template_path: str = Field(description="e.g. 'value_extractor/v1.0.jinja'")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    description: str = ""
    git_sha: str = ""


class PromptTemplate(BaseModel):
    """A named prompt template with version history."""

    name: str = Field(description="e.g. 'criterion_extractor' or 'value_extractor'")
    current_version: PromptVersion
    versions: list[PromptVersion] = []
