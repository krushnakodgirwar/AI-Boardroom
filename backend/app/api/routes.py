"""
AI Boardroom API routes.

Supports:

1. Question only
2. Question + document
3. Document only
4. Automatic agent selection
5. Manual agent selection
"""

import json
from pathlib import Path
from typing import Optional

from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    UploadFile,
)

from backend.app.core.llm import QwenLLM
from backend.app.workflows.boardroom import BoardroomWorkflow
from backend.app.agents.registry import get_available_agents


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/boardroom",
    tags=["Boardroom"],
)


# ============================================================
# CONFIGURATION
# ============================================================

UPLOAD_DIR = Path("./data/uploads")

SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".pptx",
    ".txt",
}

VALID_MODES = {
    "question_only",
    "question_with_document",
    "document_only",
}


# ============================================================
# SHARED LLM + BOARDROOM
# ============================================================

print("Initializing shared Boardroom LLM...")

llm = QwenLLM()

print("Creating shared Boardroom workflow...")

boardroom = BoardroomWorkflow(
    llm=llm
)

print("AI Boardroom API ready.")


# ============================================================
# AVAILABLE AGENTS
# ============================================================

@router.get("/agents")
def get_boardroom_agents():

    return {
        "agents": get_available_agents()
    }


# ============================================================
# BOARDROOM ANALYZE ENDPOINT
# ============================================================

@router.post("/analyze")
async def analyze_boardroom(
    question: Optional[str] = Form(default=None),

    mode: str = Form(
        default="question_only"
    ),

    response_mode: str = Form(
        default="short"
    ),

    execution_mode: str = Form(
        default="accurate"
    ),

    selected_agents: Optional[str] = Form(
        default=None
    ),

    document: Optional[UploadFile] = File(
        default=None
    ),
):
    """
    Execute the complete AI Boardroom workflow.

    Modes:

    question_only
        Question without a document.

    question_with_document
        Question + uploaded document.

    document_only
        Uploaded document without a question.

    Agent selection:

    If selected_agents is not provided:
        HybridAgentSelector automatically selects agents.

    If selected_agents is provided:
        Only the selected executive agents are used.
    """

    # ========================================================
    # NORMALIZE INPUT
    # ========================================================

    mode = (
        str(mode)
        .lower()
        .strip()
    )

    response_mode = (
        str(response_mode)
        .lower()
        .strip()
    )

    execution_mode = (
        str(execution_mode)
        .lower()
        .strip()
    )

    question = (
        question.strip()
        if question
        else None
    )

    # ========================================================
    # PARSE MANUAL AGENT SELECTION
    # ========================================================

    manual_agents = None

    if selected_agents:

        try:

            manual_agents = json.loads(
                selected_agents
            )

        except json.JSONDecodeError:

            # Also accept Swagger's comma-separated format:
            # cfo,cto
            if "," in selected_agents:

                manual_agents = [
                    agent.strip().lower()
                    for agent in selected_agents.split(",")
                    if agent.strip()
                ]

            else:

                raise HTTPException(
                    status_code=400,
                    detail=(
                        "selected_agents must be "
                        "a valid JSON list or "
                        "comma-separated list."
                    ),
                )

        if not isinstance(
            manual_agents,
            list
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    "selected_agents must be "
                    "a list."
                ),
            )

        manual_agents = [
            str(agent)
            .lower()
            .strip()
            for agent in manual_agents
            if str(agent)
            .lower()
            .strip()
        ]

        if not manual_agents:

            raise HTTPException(
                status_code=400,
                detail=(
                    "At least one agent must "
                    "be selected."
                ),
            )

    # ========================================================
    # VALIDATE MODE
    # ========================================================

    if mode not in VALID_MODES:

        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid Boardroom mode.",
                "received": mode,
                "valid_modes": sorted(
                    VALID_MODES
                ),
            },
        )

    # ========================================================
    # VALIDATE RESPONSE MODE
    # ========================================================

    valid_response_modes = {
        "short",
        "executive_summary",
        "detailed",
    }

    if response_mode not in valid_response_modes:

        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid response mode.",
                "received": response_mode,
                "valid_response_modes": sorted(
                    valid_response_modes
                ),
            },
        )

    # ========================================================
    # VALIDATE EXECUTION MODE
    # ========================================================

    valid_execution_modes = {
        "accurate",
        "fast",
    }

    if execution_mode not in valid_execution_modes:

        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid execution mode.",
                "received": execution_mode,
                "valid_execution_modes": sorted(
                    valid_execution_modes
                ),
            },
        )

    # ========================================================
    # QUESTION-ONLY VALIDATION
    # ========================================================

    if mode == "question_only":

        if not question:

            raise HTTPException(
                status_code=400,
                detail=(
                    "A question is required "
                    "for question_only mode."
                ),
            )

        if document is not None:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Do not upload a document "
                    "in question_only mode."
                ),
            )

    # ========================================================
    # QUESTION + DOCUMENT VALIDATION
    # ========================================================

    elif mode == "question_with_document":

        if not question:

            raise HTTPException(
                status_code=400,
                detail=(
                    "A question is required "
                    "for question_with_document mode."
                ),
            )

        if document is None:

            raise HTTPException(
                status_code=400,
                detail=(
                    "A document is required "
                    "for question_with_document mode."
                ),
            )

    # ========================================================
    # DOCUMENT-ONLY VALIDATION
    # ========================================================

    elif mode == "document_only":

        if document is None:

            raise HTTPException(
                status_code=400,
                detail=(
                    "A document is required "
                    "for document_only mode."
                ),
            )

    # ========================================================
    # DOCUMENT HANDLING
    # ========================================================

    document_path = None
    document_name = None

    if document is not None:

        document_name = (
            document.filename or ""
        )

        extension = Path(
            document_name
        ).suffix.lower()

        # ----------------------------------------------------
        # EXTENSION CHECK
        # ----------------------------------------------------

        if extension not in SUPPORTED_EXTENSIONS:

            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Unsupported document type.",
                    "extension": extension,
                    "supported_extensions": sorted(
                        SUPPORTED_EXTENSIONS
                    ),
                },
            )

        # ----------------------------------------------------
        # CREATE UPLOAD DIRECTORY
        # ----------------------------------------------------

        UPLOAD_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        # ----------------------------------------------------
        # SAFE FILENAME
        # ----------------------------------------------------

        safe_name = Path(
            document_name
        ).name

        if not safe_name:

            raise HTTPException(
                status_code=400,
                detail="Invalid document filename.",
            )

        document_path = (
            UPLOAD_DIR / safe_name
        )

        # ----------------------------------------------------
        # READ FILE
        # ----------------------------------------------------

        contents = await document.read()

        if not contents:

            raise HTTPException(
                status_code=400,
                detail="Uploaded document is empty.",
            )

        # ----------------------------------------------------
        # SAVE FILE
        # ----------------------------------------------------

        document_path.write_bytes(
            contents
        )

    # ========================================================
    # EXECUTE BOARDROOM
    # ========================================================

    try:

        print(
            "\n"
            + "=" * 60
        )

        print(
            "API: Starting AI Boardroom analysis"
        )

        print(
            f"API: Mode = {mode}"
        )

        print(
            f"API: Response mode = {response_mode}"
        )

        # ----------------------------------------------------
        # AGENT SELECTION LOG
        # ----------------------------------------------------

        if manual_agents:

            print(
                "API: Agent selection = MANUAL"
            )

            print(
                f"API: Selected agents = "
                f"{manual_agents}"
            )

        else:

            print(
                "API: Agent selection = AUTOMATIC"
            )

        if question:

            print(
                f"API: Question = {question}"
            )

        if document_path:

            print(
                f"API: Document = {document_path}"
            )

        print(
            "=" * 60
        )

        # ----------------------------------------------------
        # RUN EXISTING BOARDROOM
        # ----------------------------------------------------

        result = boardroom.run(
            user_question=question,

            response_mode=response_mode,

            document_path=(
                str(document_path)
                if document_path
                else None
            ),

            mode=mode,

            selected_agents=manual_agents,

            execution_mode=execution_mode,
        )

        # ----------------------------------------------------
        # RETURN COMPLETE RESULT
        # ----------------------------------------------------

        return {
            "status": "success",

            "mode": mode,

            "response_mode": response_mode,

            "execution_mode": execution_mode,

            "question": question,

            "document_name": document_name,

            "selected_agents": (
                manual_agents
                if manual_agents
                else None
            ),

            "result": result,

            "final_decision": (
                result.get(
                    "final_decision"
                )
                if isinstance(
                    result,
                    dict
                )
                else None
            ),
        }

    except Exception as exc:

        print(
            "\nAI Boardroom API ERROR:"
        )

        print(
            repr(exc)
        )

        raise HTTPException(
            status_code=500,
            detail={
                "error": "Boardroom analysis failed.",
                "message": str(exc),
            },
        ) from exc