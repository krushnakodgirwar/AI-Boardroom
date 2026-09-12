"""
AI Boardroom API schemas.

Supports three analysis modes:

1. question_only
2. question_with_document
3. document_only
"""

from typing import Optional, Literal

from pydantic import BaseModel, Field


AnalysisMode = Literal[
    "question_only",
    "question_with_document",
    "document_only",
]


class BoardroomRequest(BaseModel):
    """
    Request for Boardroom analysis.

    For question_only:
        question is required
        document is not required

    For question_with_document:
        question is required
        document is required

    For document_only:
        question is optional
        document is required
    """

    question: Optional[str] = Field(
        default=None,
        description="Business question from the user.",
    )

    mode: Optional[AnalysisMode] = Field(
        default=None,
        description="Analysis mode.",
    )

    response_mode: str = Field(
        default="short",
        description="Response detail level.",
    )


class BoardroomResponse(BaseModel):
    """
    Standard Boardroom response.
    """

    selected_agents: list[str] = Field(
        default_factory=list
    )

    final_decision: str = ""

    confidence: Optional[float] = None

    selection_method: Optional[str] = None

    mode: Optional[str] = None

    document_name: Optional[str] = None

    retrieved_chunks: int = 0

    evidence_used: bool = False

    error: Optional[str] = None