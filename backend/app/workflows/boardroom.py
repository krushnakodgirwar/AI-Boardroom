


from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from backend.app.agents.ceo import CEOAgent
from backend.app.agents.hybrid_selector import HybridAgentSelector
from backend.app.agents.registry import create_selected_agents

from backend.app.rag.document_loader import DocumentLoader
from backend.app.rag.retriever import DocumentRetriever


class BoardroomWorkflow:
    """
    Complete AI Boardroom decision workflow.

    Supports three input modes:

    1. question_only
       User provides only a business question.

    2. question_with_document
       User provides a business question and a document.

    3. document_only
       User provides only a document.
       The Boardroom automatically creates a general
       document-analysis question.

    Existing Boardroom stages remain unchanged:

    Stage 1:
        Hybrid selector chooses relevant executives.

    Stage 2:
        Executives participate in evidence-grounded debate.

    Stage 3:
        CEO produces the final company-level decision.

    Stage 4:
        CEO decision is validated.

    Response Modes:
        - short
        - executive_summary
        - detailed
    """

    # =====================================================
    # SUPPORTED MODES
    # =====================================================

    VALID_MODES = {
        "question_only",
        "question_with_document",
        "document_only",
    }

    # =====================================================
    # SUPPORTED DOCUMENT TYPES
    # =====================================================

    SUPPORTED_DOCUMENT_EXTENSIONS = {
        ".pdf",
        ".docx",
        ".pptx",
        ".txt",
    }

    # =====================================================
    # DOCUMENT-ONLY QUESTION
    # =====================================================

    DOCUMENT_ONLY_QUESTION = """
Analyze the provided document as an AI Boardroom.

Identify the most important business considerations
supported by the document.

Evaluate only information that is actually supported
by the document.

Consider relevant areas such as:

- financial considerations
- product considerations
- technical considerations
- operational considerations
- legal or regulatory considerations
- people and organizational considerations
- revenue or commercial considerations
- enterprise risks

Do not invent facts that are not present in the document.

The Boardroom executives should determine which areas
are relevant based on the evidence available.

Provide a company-level assessment based only on the
document evidence.
""".strip()

    # =====================================================
    # RESPONSE MODE TOKEN BUDGETS
    # =====================================================

    RESPONSE_TOKEN_BUDGETS = {

        "short": {
            "agent": 300,
            "debate": 300,
            "ceo": 500,
        },

        "executive_summary": {
            "agent": 500,
            "debate": 900,
            "ceo": 900,
        },

        "detailed": {
            "agent": 600,
            "debate": 600,
            "ceo": 800,
        },
    }

    # =====================================================
    # EXECUTION MODES
    # =====================================================

    # Accurate mode preserves the existing Boardroom behavior.
    # Fast mode changes only execution settings. CEO reasoning
    # prompts and decision rules remain unchanged.
    EXECUTION_MODES = {
        "accurate": {
            "max_agents": None,
            "agent_multiplier": 1.0,
            "debate_multiplier": 1.0,
            "ceo_multiplier": 1.0,
        },
        "fast": {
            "max_agents": 3,
            "agent_multiplier": 0.67,
            "debate_multiplier": 0.67,
            "ceo_multiplier": 0.60,
        },
    }

    # =====================================================
    # CONSTRUCTOR
    # =====================================================

    def __init__(
        self,
        agents=None,
        llm=None
    ):
        """
        Initialize the Boardroom workflow.

        `agents` is kept for backward compatibility.

        Agent selection is performed dynamically by
        HybridAgentSelector for every business question.
        """

        self.agents = agents or {}

        self.llm = llm

        if llm is None:
            raise ValueError(
                "A shared LLM instance is required."
            )

        # -------------------------------------------------
        # HYBRID SELECTOR
        # -------------------------------------------------

        self.selector = HybridAgentSelector(
            llm
        )

        # -------------------------------------------------
        # CEO
        # -------------------------------------------------

        self.ceo = CEOAgent(
            llm
        )

        # -------------------------------------------------
        # RAG COMPONENTS
        # -------------------------------------------------

        self.document_loader = DocumentLoader()

        self.document_retriever = DocumentRetriever()

    # =====================================================
    # DOCUMENT / RAG SUPPORT
    # =====================================================

    def _validate_document_path(
        self,
        document_path
    ):
        """
        Validate document path and extension.
        """

        if not document_path:
            return None

        path = Path(
            document_path
        )

        if not path.exists():

            raise FileNotFoundError(
                f"Document not found: {path}"
            )

        if not path.is_file():

            raise ValueError(
                f"Document path is not a file: {path}"
            )

        extension = (
            path.suffix.lower()
        )

        if extension not in (
            self.SUPPORTED_DOCUMENT_EXTENSIONS
        ):

            raise ValueError(
                f"Unsupported document type: "
                f"{extension}. "
                f"Supported types: "
                f"{sorted(self.SUPPORTED_DOCUMENT_EXTENSIONS)}"
            )

        return path

    # =====================================================

    def _build_document_context(
        self,
        document_path,
        retrieval_question
    ):
        """
        Load, index and retrieve evidence from a document.

        Pipeline:

            Document
                ↓
            DocumentLoader
                ↓
            Chunks
                ↓
            Embeddings
                ↓
            ChromaDB
                ↓
            Semantic Retrieval
                ↓
            Evidence Context
        """

        path = self._validate_document_path(
            document_path
        )

        if path is None:
            return {
                "context": "",
                "chunks": [],
                "document_name": None,
                "retrieved_count": 0,
            }

        document_name = path.name

        print(
            "\n" + "=" * 60
        )

        print(
            "DOCUMENT / RAG PROCESSING"
        )

        print(
            "=" * 60
        )

        print(
            f"Document: {document_name}"
        )

        # =================================================
        # STEP 1
        # LOAD DOCUMENT
        # =================================================

        print(
            "\nLoading document..."
        )

        chunks = (
            self.document_loader.load(
                str(path)
            )
        )

        if not chunks:

            raise ValueError(
                "Document was loaded but produced "
                "no text chunks."
            )

        print(
            f"Document chunks loaded: "
            f"{len(chunks)}"
        )

        # =================================================
        # STEP 2
        # INDEX DOCUMENT
        # =================================================

        print(
            "\nIndexing document in ChromaDB..."
        )

        # DocumentRetriever owns the vector store
        # and embedding model in the current RAG design.
        #
        # We intentionally use the existing components
        # instead of creating another embedding/vector
        # implementation here.

        try:

            vector_store = (
                self.document_retriever.vector_store
            )

            embedding_model = (
                self.document_retriever.embedding_model
            )

        except AttributeError:

            # Compatibility fallback if the implementation
            # exposes the objects under different names.
            vector_store = getattr(
                self.document_retriever,
                "store",
                None
            )

            embedding_model = getattr(
                self.document_retriever,
                "embeddings",
                None
            )

        if vector_store is not None:

            try:
                vector_store.delete_source(
                    document_name
                )
            except Exception:
                pass

        texts = [
            chunk.get(
                "text",
                ""
            )
            for chunk in chunks
        ]

        texts = [
            text
            for text in texts
            if text and text.strip()
        ]

        if not texts:

            raise ValueError(
                "The document contains no usable text."
            )

        # =================================================
        # ADD DOCUMENT TO EXISTING VECTOR STORE
        # =================================================

        if (
            vector_store is not None
            and embedding_model is not None
        ):

            embeddings = (
                embedding_model.embed_texts(
                    texts
                )
            )

            vector_store.add_documents(
                chunks,
                embeddings
            )

            print(
                f"Indexed {len(chunks)} "
                f"document chunks."
            )

        else:

            print(
                "Warning: Could not access the "
                "underlying vector store directly."
            )

        # =================================================
        # STEP 3
        # SEMANTIC RETRIEVAL
        # =================================================

        print(
            "\nRetrieving relevant document evidence..."
        )

        results = (
            self.document_retriever.retrieve(
                retrieval_question
            )
        )

        if results is None:
            results = []

        print(
            f"Retrieved chunks: "
            f"{len(results)}"
        )

        # =================================================
        # STEP 4
        # BUILD EVIDENCE CONTEXT
        # =================================================

        context_parts = []

        for index, result in enumerate(
            results,
            start=1
        ):

            text = str(
                result.get(
                    "text",
                    ""
                )
            ).strip()

            if not text:
                continue

            source = result.get(
                "source",
                document_name
            )

            page = result.get(
                "page"
            )

            if page is not None:

                source_label = (
                    f"{source}, page {page}"
                )

            else:

                source_label = (
                    str(source)
                )

            context_parts.append(
                f"""
--- DOCUMENT EVIDENCE {index} ---
SOURCE: {source_label}

{text}
""".strip()
            )

        document_context = (
            "\n\n".join(
                context_parts
            )
        )

        # =================================================
        # FALLBACK
        # =================================================

        # If semantic retrieval returns nothing, use the
        # loaded document chunks rather than silently
        # losing the uploaded document.

        if not document_context:

            fallback_parts = []

            for index, chunk in enumerate(
                chunks,
                start=1
            ):

                text = str(
                    chunk.get(
                        "text",
                        ""
                    )
                ).strip()

                if not text:
                    continue

                source = chunk.get(
                    "source",
                    document_name
                )

                page = chunk.get(
                    "page"
                )

                if page is not None:

                    source_label = (
                        f"{source}, page {page}"
                    )

                else:

                    source_label = (
                        str(source)
                    )

                fallback_parts.append(
                    f"""
--- DOCUMENT EVIDENCE {index} ---
SOURCE: {source_label}

{text}
""".strip()
                )

            document_context = (
                "\n\n".join(
                    fallback_parts
                )
            )

        print(
            "\nDocument evidence prepared."
        )

        return {
            "context": document_context,
            "chunks": results,
            "document_name": document_name,
            "retrieved_count": len(results),
        }

    # =====================================================
    # COMBINE CONTEXT
    # =====================================================

    @staticmethod
    def _combine_context(
        existing_context,
        document_context
    ):
        """
        Combine existing application context with
        retrieved document evidence.
        """

        existing_context = (
            str(existing_context).strip()
            if existing_context
            else ""
        )

        document_context = (
            str(document_context).strip()
            if document_context
            else ""
        )

        if (
            existing_context
            and document_context
        ):

            return (
                "EXISTING CONTEXT:\n\n"
                + existing_context
                + "\n\n"
                + "=" * 60
                + "\n\n"
                + "UPLOADED DOCUMENT EVIDENCE:\n\n"
                + document_context
            )

        if document_context:
            return (
                "UPLOADED DOCUMENT EVIDENCE:\n\n"
                + document_context
            )

        return existing_context

    # =====================================================
    # STAGE 2: EXECUTIVE DEBATE
    # =====================================================

    def run_debate(
        self,
        user_question,
        executive_analyses,
        max_new_tokens=500
    ):
        """
        Compare the actual executive reports.

        The debate moderator:

        - represents every selected executive
        - preserves their actual positions
        - identifies genuine agreements
        - identifies genuine disagreements
        - preserves uncertainty
        - does not invent information
        - does not make the final decision
        """

        reports_text = ""

        actual_executives = []

        for name, report in (
            executive_analyses.items()
        ):

            if name == "BOARDROOM_DEBATE":
                continue

            actual_executives.append(
                name.upper()
            )

            reports_text += (
                f"\n===== {name.upper()} REPORT =====\n"
            )

            reports_text += (
                str(report).strip()
            )

            reports_text += "\n"

        executive_list = ", ".join(
            actual_executives
        )

        system_prompt = """
You are the Executive Debate Moderator
of an AI Boardroom.

Your job is NOT to make the business decision.

Your job is to accurately compare the executive
reports provided to you.

==================================================
STRICT EVIDENCE RULES
==================================================

1. Every selected executive must be represented.

2. Only attribute a statement to an executive if
   that executive's report actually contains it.

3. Do not invent opinions for any executive.

4. Do not change the meaning of an executive's position.

5. Do not invent:
   - statistics
   - financial figures
   - market data
   - customer numbers
   - competitors
   - technical capabilities
   - regulations
   - business conditions
   - company capabilities

6. Missing information remains missing information.

7. If an executive says information is uncertain,
   preserve that uncertainty.

8. Do not treat missing information as evidence
   that something is positive or negative.


==================================================
DISAGREEMENT RULE
==================================================

A disagreement exists ONLY when two executives make
MATERIALLY CONFLICTING:

- claims
- conclusions
- recommendations
- priorities
- decisions

A disagreement requires an ACTUAL DIRECT CONFLICT.

==================================================
COMPATIBILITY RULE
==================================================

Different recommendations are NOT automatically
disagreements.

Before declaring a disagreement, compare the actual
recommendations.

Ask:

1. What does Executive A recommend?

2. What does Executive B recommend?

3. Can both recommendations be performed?

4. Does one recommendation explicitly oppose,
   prevent, reject, or contradict the other?

If both recommendations can be performed together:

THERE IS NO DISAGREEMENT.

For example:

CFO:
"Gather detailed financial information."

CTO:
"Conduct a technical feasibility review."

These recommendations are COMPATIBLE.

Both actions can happen together.

Therefore:

"No material disagreement identified."

Another example:

CFO:
"Proceed with caution and gather financial information."

CTO:
"Proceed with caution and conduct technical testing."

These are also COMPATIBLE.

They address different areas and can both be performed.

Therefore they are NOT a disagreement.

==================================================
REAL DISAGREEMENT EXAMPLE
==================================================

CFO:
"Proceed with the launch immediately."

CTO:
"Do not launch until the technical issue is resolved."

These recommendations directly conflict.

One supports launching.

The other opposes launching.

Therefore this IS a genuine disagreement.

==================================================
DO NOT CONFUSE DIFFERENCES WITH DISAGREEMENTS
==================================================

The following are NOT disagreements by themselves:

- Different areas of expertise
- Different missing information
- Different risks
- Different questions
- Different concerns
- Different levels of caution
- Different follow-up actions
- Different mitigation actions
- Different priorities that can coexist

Different responsibilities are NOT disagreements.

Different risks are NOT automatically disagreements.

Different follow-up actions are NOT disagreements
when they can be performed together.

When uncertain whether two positions conflict,
DO NOT report a disagreement.

==================================================
NO-DISAGREEMENT DEFAULT
==================================================

If there is no direct material conflict, write:

"No material disagreement identified."

==================================================
AGREEMENT RULE
==================================================

Only identify an agreement when multiple reports
actually support the same conclusion, concern,
recommendation, or position.

Do not manufacture agreement.

If there is no clear agreement, write:

"No material agreement identified."

==================================================
RISK RULE
==================================================

Only report risks explicitly identified
in the executive reports.

Do not create new risks.

Do not turn missing information into a risk.

Do not add generic business risks.

==================================================
FINAL DECISION RULE
==================================================

Do NOT make the final business decision.

Do NOT recommend:

- PROCEED
- DO NOT PROCEED
- PROCEED WITH CONDITIONS
- PILOT FIRST
- GATHER MORE INFORMATION

The CEO will make the final decision.

==================================================
COMMUNICATION
==================================================

Be concise.

Use only the provided executive reports.

Do not repeat the complete reports.

Summarize their important positions accurately.
"""

        user_prompt = f"""
BUSINESS QUESTION:

{user_question}

==================================================

SELECTED EXECUTIVES:

{executive_list}

==================================================

EXECUTIVE REPORTS:

{reports_text}

==================================================
TASK
==================================================

Analyze ONLY the executive reports above.

Do not use outside information.

Use exactly this structure:

EXECUTIVE POSITIONS:

{self._build_position_template(
    actual_executives
)}

AGREEMENTS:

List only agreements directly supported
by multiple executive reports.

If no clear agreement exists:

"No material agreement identified."



DISAGREEMENTS:

IMPORTANT: Do NOT list an executive pair as a
disagreement until you have first verified that
their positions directly conflict.

Step 1:
Identify the recommendations of the two executives.

Step 2:
Ask whether BOTH recommendations can be performed
together.

Step 3:
Ask whether one recommendation explicitly opposes,
prevents, rejects, or contradicts the other.

If BOTH recommendations can be performed together,
they are COMPATIBLE and MUST NOT be listed as a
disagreement.

For example:

CFO:
"Gather detailed financial information."

CTO:
"Conduct a technical feasibility review."

These actions can happen together.

Therefore:

No material disagreement identified.

Another example:

CFO:
"Proceed with the launch immediately."

CTO:
"Do not launch until the technical issue is resolved."

These positions directly conflict.

Therefore this IS a genuine disagreement.

IMPORTANT:
Different risks, concerns, missing information,
follow-up actions, mitigation actions, or areas of
expertise are NOT disagreements unless they directly
conflict.

When uncertain, DO NOT report a disagreement.

If no direct conflict exists, output EXACTLY:

No material disagreement identified.

Only for a genuine disagreement use:

- Issue:
- Executive A position:
- Executive B position:

Do NOT write a disagreement and then say that the
recommendations are compatible.


STRONGEST ARGUMENTS:

For EVERY selected executive, identify at least
one strongest argument from that executive's report.

Use this format:

EXECUTIVE_NAME:
- Strongest argument from the report.

Do not invent arguments.

If an executive's report contains no concrete
argument, write:

EXECUTIVE_NAME:
- No concrete argument established from the
  available information.


KEY RISKS:

List only risks explicitly identified
in the executive reports.

For each risk identify the executive
who raised it.

Do not create additional risks.

MISSING INFORMATION:

List information that the executive reports
explicitly identify as missing or uncertain.

Do not claim information is available when
the reports say it is unknown.

CEO QUESTIONS:

List 2-3 important questions the CEO should
consider based ONLY on the reports.

Questions must address actual uncertainty,
conflict, evidence, or missing information.

FINAL MODERATOR NOTE:

Do not make the business decision.

Do not recommend a final action.

The CEO will make the final decision.
"""

        return self.llm.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_new_tokens=max_new_tokens
        )

    # =====================================================
    # POSITION TEMPLATE
    # =====================================================

    @staticmethod
    def _build_position_template(
        executives
    ):
        """
        Dynamically creates only the positions for
        the executives that were actually selected.
        """

        template = ""

        for executive in executives:

            template += (
                f"\n{executive}:\n"
                f"- Main position:\n"
                f"- Recommendation:\n"
                f"- Main concern:\n"
            )

        return template

    # =====================================================
    # CEO DECISION VALIDATION
    # =====================================================

    @staticmethod
    def _normalize_ceo_decision(
        response
    ):
        """
        Validate and normalize the CEO decision.

        If the CEO selects PROCEED WITH CONDITIONS but
        clearly describes a pilot before full commercial
        launch, normalize the primary action to PILOT FIRST.
        """

        if not response:
            return response

        text = response.strip()

        upper_text = text.upper()

        current_decision = None

        marker = "FINAL DECISION"

        if marker in upper_text:

            start = upper_text.find(
                marker
            )

            remaining = text[
                start + len(marker):
            ]

            remaining = remaining.lstrip(
                "*# :\t"
            )

            for line in remaining.splitlines():

                candidate = line.strip()

                candidate = candidate.strip(
                    "*# :\t"
                )

                if candidate:

                    current_decision = (
                        candidate.upper()
                    )

                    break

        if current_decision is None:

            print(
                "Could not detect CEO decision. "
                "No normalization applied."
            )

            return response

        print(
            f"Detected CEO decision: "
            f"{current_decision}"
        )

        pilot_signals = [

            "PILOT FIRST",

            "LIMITED PILOT",

            "RUN A LIMITED PILOT",

            "RUNNING A LIMITED PILOT",

            "PILOT PHASE",

            "LIMITED NUMBER OF CUSTOMERS",

            "LIMITED CUSTOMERS BEFORE FULL",

            "BEFORE FULL COMMERCIAL LAUNCH",

            "BEFORE FULL LAUNCH",

            "BEFORE COMMERCIAL LAUNCH",

            "BEFORE COMMITTING TO A FULL LAUNCH",

            "BEFORE COMMITTING TO FULL LAUNCH",
        ]

        immediate_launch_signals = [

            "LAUNCH IMMEDIATELY",

            "LAUNCH THE PRODUCT IMMEDIATELY",

            "IMMEDIATE LAUNCH",

            "LAUNCH NOW",

            "PROCEED IMMEDIATELY",
        ]

        has_pilot = any(
            signal in upper_text
            for signal in pilot_signals
        )

        has_immediate_launch = any(
            signal in upper_text
            for signal in immediate_launch_signals
        )

        has_conditional_decision = (
            "PROCEED WITH CONDITIONS"
            in current_decision
        )

        print(
            f"Pilot detected: "
            f"{has_pilot}"
        )

        print(
            f"Immediate launch detected: "
            f"{has_immediate_launch}"
        )

        print(
            f"Conditional decision detected: "
            f"{has_conditional_decision}"
        )

        pilot_before_full_launch = any(
            phrase in upper_text
            for phrase in [

                "BEFORE FULL COMMERCIAL LAUNCH",

                "BEFORE FULL LAUNCH",

                "BEFORE COMMERCIAL LAUNCH",

                "BEFORE COMMITTING TO A FULL LAUNCH",

                "BEFORE COMMITTING TO FULL LAUNCH",
            ]
        )

        should_be_pilot_first = (
            has_conditional_decision
            and has_pilot
            and (
                not has_immediate_launch
                or pilot_before_full_launch
            )
        )

        if not should_be_pilot_first:

            print(
                "CEO decision passed consistency check."
            )

            return response

        print(
            "Decision consistency correction applied."
        )

        print(
            "Primary action normalized to: "
            "PILOT FIRST"
        )

        lines = text.splitlines()

        sections = {}

        current_section = None

        known_sections = {

            "RECOMMENDATION:":
                "RECOMMENDATION",

            "KEY REASONS:":
                "KEY REASONS",

            "EXECUTIVE POSITIONS:":
                "EXECUTIVE POSITIONS",

            "KEY TRADE-OFF:":
                "KEY TRADE-OFF",

            "MAJOR RISKS:":
                "MAJOR RISKS",

            "MISSING INFORMATION:":
                "MISSING INFORMATION",

            "CONDITIONS:":
                "CONDITIONS",

            "NEXT STEPS:":
                "NEXT STEPS",

            "CONFIDENCE:":
                "CONFIDENCE",

            "CONFIDENCE REASON:":
                "CONFIDENCE REASON",
        }

        for line in lines:

            clean_heading = (
                line
                .strip()
                .strip("*#")
                .strip()
                .upper()
            )

            if clean_heading in known_sections:

                current_section = (
                    known_sections[
                        clean_heading
                    ]
                )

                sections[
                    current_section
                ] = []

                continue

            if current_section is not None:

                sections[
                    current_section
                ].append(
                    line
                )

        result = [

            "**FINAL DECISION:**",

            "PILOT FIRST",

            "",

            "RECOMMENDATION:",

            (
                "Run a limited pilot before full commercial "
                "launch to validate the key assumptions "
                "identified by the executive reports."
            ),

            "",
        ]

        for section_name in [

            "KEY REASONS",

            "EXECUTIVE POSITIONS",

            "KEY TRADE-OFF",

            "MAJOR RISKS",

            "MISSING INFORMATION",
        ]:

            if section_name in sections:

                result.append(
                    f"{section_name}:"
                )

                for line in sections[
                    section_name
                ]:

                    if line.strip():

                        result.append(
                            line
                        )

                result.append("")

        result.extend([

            "CONDITIONS:",

            "Not applicable.",

            "",

            "NEXT STEPS:",
        ])

        if sections.get(
            "NEXT STEPS"
        ):

            for line in sections[
                "NEXT STEPS"
            ]:

                if line.strip():

                    result.append(
                        line
                    )

        else:

            result.extend([

                "1. Run the limited pilot.",

                (
                    "2. Validate the key technical and "
                    "business assumptions."
                ),

                (
                    "3. Review pilot results before full "
                    "commercial launch."
                ),
            ])

        result.append("")

        if sections.get(
            "CONFIDENCE"
        ):

            result.append(
                "CONFIDENCE:"
            )

            for line in sections[
                "CONFIDENCE"
            ]:

                if line.strip():

                    result.append(
                        line
                    )

            result.append("")

        if sections.get(
            "CONFIDENCE REASON"
        ):

            result.append(
                "CONFIDENCE REASON:"
            )

            for line in sections[
                "CONFIDENCE REASON"
            ]:

                if line.strip():

                    result.append(
                        line
                    )

        return "\n".join(
            result
        ).strip()

    # =====================================================
    # COMPLETE BOARDROOM WORKFLOW
    # =====================================================

    def run(
        self,
        user_question,
        context=None,
        data=None,
        response_mode="executive_summary",
        document_path=None,
        mode=None,
        selected_agents=None,
        execution_mode="accurate"
    ):
        """
        Execute the complete Boardroom process.

        Supported modes:

        question_only
            Normal Boardroom analysis.

        question_with_document
            Retrieve evidence from uploaded document
            and include it in Boardroom analysis.

        document_only
            Retrieve document evidence and automatically
            create a document-analysis task.

        Backward compatibility:

        Existing calls such as:

            workflow.run(
                user_question,
                context=context,
                data=data,
                response_mode="short"
            )

        continue to work.
        """

        # =================================================
        # DETERMINE MODE
        # =================================================

        if mode is None:

            if document_path and user_question:

                mode = (
                    "question_with_document"
                )

            elif document_path:

                mode = (
                    "document_only"
                )

            else:

                mode = (
                    "question_only"
                )

        mode = (
            str(mode)
            .lower()
            .strip()
        )

        if mode not in self.VALID_MODES:

            raise ValueError(
                f"Invalid Boardroom mode: {mode}. "
                f"Valid modes: "
                f"{sorted(self.VALID_MODES)}"
            )

        # =================================================
        # VALIDATE MODE INPUT
        # =================================================

        if mode == "question_only":

            if not user_question:

                raise ValueError(
                    "question_only mode requires "
                    "a user question."
                )

            if document_path:

                raise ValueError(
                    "question_only mode does not "
                    "accept a document."
                )

        elif mode == "question_with_document":

            if not user_question:

                raise ValueError(
                    "question_with_document mode "
                    "requires a question."
                )

            if not document_path:

                raise ValueError(
                    "question_with_document mode "
                    "requires a document."
                )

        elif mode == "document_only":

            if not document_path:

                raise ValueError(
                    "document_only mode requires "
                    "a document."
                )

        # =================================================
        # DOCUMENT PROCESSING
        # =================================================

        document_name = None

        retrieved_count = 0

        retrieved_chunks = []

        # -------------------------------------------------
        # DOCUMENT-ONLY MODE
        # -------------------------------------------------

        if mode == "document_only":

            print(
                "\n" + "=" * 60
            )

            print(
                "DOCUMENT-ONLY MODE"
            )

            print(
                "=" * 60
            )

            user_question = (
                self.DOCUMENT_ONLY_QUESTION
            )

        # -------------------------------------------------
        # DOCUMENT MODES
        # -------------------------------------------------

        if document_path:

            rag_result = (
                self._build_document_context(
                    document_path=document_path,
                    retrieval_question=user_question
                )
            )

            document_name = (
                rag_result[
                    "document_name"
                ]
            )

            retrieved_count = (
                rag_result[
                    "retrieved_count"
                ]
            )

            retrieved_chunks = (
                rag_result[
                    "chunks"
                ]
            )

            context = (
                self._combine_context(
                    existing_context=context,
                    document_context=(
                        rag_result[
                            "context"
                        ]
                    )
                )
            )

        # =================================================
        # EXECUTION MODE VALIDATION
        # =================================================

        execution_mode = str(execution_mode).lower().strip()

        if execution_mode not in self.EXECUTION_MODES:
            print(f"Invalid execution mode '{execution_mode}'. Using accurate.")
            execution_mode = "accurate"

        execution_config = self.EXECUTION_MODES[execution_mode]

        # =================================================
        # RESPONSE MODE VALIDATION
        # =================================================

        valid_modes = {

            "short",

            "executive_summary",

            "detailed",
        }

        if response_mode not in valid_modes:

            print(
                f"Invalid response mode "
                f"'{response_mode}'. "
                f"Using executive_summary."
            )

            response_mode = (
                "executive_summary"
            )

        # =================================================
        # SELECT TOKEN BUDGET
        # =================================================

        base_token_budget = self.RESPONSE_TOKEN_BUDGETS[response_mode]

        max_agent_tokens = base_token_budget["agent"]
        max_debate_tokens = base_token_budget["debate"]
        max_ceo_tokens = base_token_budget["ceo"]

        if execution_mode == "fast":
            max_agent_tokens = max(1, int(base_token_budget["agent"] * execution_config["agent_multiplier"]))
            max_debate_tokens = max(1, int(base_token_budget["debate"] * execution_config["debate_multiplier"]))
            max_ceo_tokens = max(1, int(base_token_budget["ceo"] * execution_config["ceo_multiplier"]))

        token_budget = {
            "agent": max_agent_tokens,
            "debate": max_debate_tokens,
            "ceo": max_ceo_tokens,
        }

        # =================================================
        # DISPLAY CONFIGURATION
        # =================================================

        print(
            "\n" + "=" * 60
        )

        print(
            f"RESPONSE MODE: "
            f"{response_mode.upper()}"
        )

        print(
            f"EXECUTION MODE: "
            f"{execution_mode.upper()}"
        )

        print(
            "=" * 60
        )

        print(
            f"BOARDROOM MODE: "
            f"{mode}"
        )

        print(
            f"Agent token budget: "
            f"{max_agent_tokens}"
        )

        print(
            f"Debate token budget: "
            f"{max_debate_tokens}"
        )

        print(
            f"CEO token budget: "
            f"{max_ceo_tokens}"
        )

        if document_name:

            print(
                f"Document: "
                f"{document_name}"
            )

            print(
                f"Retrieved chunks: "
                f"{retrieved_count}"
            )

        print(
            "=" * 60
        )

        # =================================================
        # STAGE 1
        # HYBRID EXECUTIVE SELECTION
        # =================================================

        print(
            "\n" + "=" * 60
        )

        print(
            "STAGE 1: EXECUTIVE SELECTION"
        )

        print(
            "=" * 60
        )

        # =================================================
        # EXECUTIVE SELECTION
        # =================================================

        # -------------------------------------------------
        # MANUAL OR AUTOMATIC SELECTION
        # -------------------------------------------------

        if selected_agents:

            # MANUAL SELECTION

            selected_names = [
                str(name).lower().strip()
                for name in selected_agents
                if str(name).lower().strip()
            ]

            selection_confidence = 1.0
            selection_method = "manual"

            print(
                "\nSelection mode: MANUAL"
            )

        else:

            # AUTOMATIC HYBRID SELECTION

            print(
                "\nSelection mode: AUTOMATIC"
            )

            selection = (
                self.selector.select_agents(
                    user_question
                )
            )

            if isinstance(
                selection,
                dict
            ):

                selected_names = (
                    selection.get(
                        "agents",
                        []
                    )
                )

                selection_confidence = (
                    selection.get(
                        "confidence"
                    )
                )

                selection_method = (
                    selection.get(
                        "method"
                    )
                )

            else:

                selected_names = selection

                selection_confidence = None

                selection_method = None

        # -------------------------------------------------
        # VALIDATE SELECTION
        # -------------------------------------------------

        if not selected_names:

            raise RuntimeError(
                "No Boardroom agents were selected."
            )

        selected_names = [
            str(name)
            .lower()
            .strip()
            for name in selected_names
            if str(name)
            .lower()
            .strip()
        ]

        # -------------------------------------------------
        # FAST MODE AGENT REDUCTION
        # -------------------------------------------------

        max_agents = execution_config["max_agents"]

        # Only reduce agents selected automatically.
        # Manual selection is always respected.
        if (
            execution_mode == "fast"
            and selection_method in ("automatic", "hybrid")
            and max_agents is not None
            and len(selected_names) > max_agents
        ):

            print(
                f"\nFAST MODE: reducing automatic agents "
                f"from {len(selected_names)} to {max_agents}."
            )

            # Preserve important cross-functional perspectives
            # when they were selected by the Hybrid Selector.
            priority_agents = [
                "cfo",
                "cto",
                "risk",
            ]

            prioritized = [
                agent
                for agent in priority_agents
                if agent in selected_names
            ]

            remaining = [
                agent
                for agent in selected_names
                if agent not in prioritized
            ]

            selected_names = (
                prioritized + remaining
            )[:max_agents]

            print(
                f"FAST MODE selected agents: "
                f"{selected_names}"
            )


        if not selected_names:
            raise RuntimeError(
                "No Boardroom agents remain after execution-mode filtering."
            )

        print(
            "\nSELECTED EXECUTIVES:"
        )

        print(
            selected_names
        )

        if selection_confidence is not None:

            print(
                f"Selection confidence: "
                f"{selection_confidence}"
            )

        if selection_method:

            print(
                f"Selection method: "
                f"{selection_method}"
            )

        # =================================================
        # CREATE ONLY SELECTED AGENTS
        # =================================================

        selected_agents = (

            create_selected_agents
            (
              selected_names,
              self.llm,
             execution_mode=execution_mode
           )
        )

        print(
            "\nCREATED EXECUTIVE AGENTS:"
        )

        print(
            list(
                selected_agents.keys()
            )
        )





        # =================================================
        # STAGE 1
        # EXECUTIVE ANALYSIS
        # =================================================

        print(
            "\n" + "=" * 60
        )

        print(
            "STAGE 1: EXECUTIVE ANALYSIS"
        )

        print(
            "=" * 60
        )

        executive_analyses = {}

        # =================================================
        # CONTROLLED PARALLEL EXECUTIVE ANALYSIS
        # =================================================

        MAX_WORKERS = 2

        print(
            f"\nRunning executive analyses "
            f"in parallel (max {MAX_WORKERS} at a time)..."
        )

        def run_executive(name, agent):
            print(
                f"\nStarting "
                f"{agent.role_name} analysis..."
            )

            agent_kwargs = {
                "user_question": user_question,
                "context": context,
                "data": data,
                "max_new_tokens": max_agent_tokens,
            }

            # Fast agents accept execution_mode.
            # Original Accurate agents keep their existing API.
            if execution_mode == "fast":
                agent_kwargs["execution_mode"] = execution_mode

            response = agent.analyze(**agent_kwargs)

            return name, response

        with ThreadPoolExecutor(
            max_workers=MAX_WORKERS
        ) as executor:

            futures = {
                executor.submit(
                    run_executive,
                    name,
                    agent
                ): name
                for name, agent in selected_agents.items()
            }

            for future in as_completed(futures):

                name, response = future.result()

                executive_analyses[name] = response

                print(
                    f"\nCompleted "
                    f"{name.upper()} analysis."
                )

        # =================================================
        # DISPLAY EXECUTIVE REPORTS
        # =================================================

        print(
            "\n" + "=" * 60
        )

        print(
            "EXECUTIVE REPORTS"
        )

        print(
            "=" * 60
        )

        for name, report in (
            executive_analyses.items()
        ):

            print("\n")

            print(
                f"========== "
                f"{name.upper()} "
                f"=========="
            )

            print(
                report
            )

        # =================================================
        # STAGE 2
        # EXECUTIVE DEBATE
        # =================================================

        print(
            "\n" + "=" * 60
        )

        print(
            "STAGE 2: EXECUTIVE DEBATE"
        )

        print(
            "=" * 60
        )

        if len(executive_analyses) <= 1:
            debate = (
                "EXECUTIVE DEBATE:\n\n"
                "Only one executive was selected. "
                "No cross-executive disagreement can be established. "
                "The CEO should make the final decision using the "
                "selected executive's analysis and the available evidence."
            )
            print(
                "\nOnly one executive selected; "
                "skipping redundant debate LLM generation."
            )
        else:
            debate = self.run_debate(
                user_question=user_question,
                executive_analyses=executive_analyses,
                max_new_tokens=max_debate_tokens
            )

        print(
            "\nEXECUTIVE DEBATE:"
        )

        print(
            debate
        )

        # =================================================
        # STAGE 3
        # CEO FINAL DECISION
        # =================================================

        print(
            "\n" + "=" * 60
        )

        print(
            "STAGE 3: CEO FINAL DECISION"
        )

        print(
            "=" * 60
        )

        ceo_input = {
            **executive_analyses,
            "BOARDROOM_DEBATE": debate
        }

        final_decision = (
            self.ceo.make_final_decision(

                user_question=user_question,

                executive_analyses=ceo_input,

                context=context,

                data=data,

                max_new_tokens=max_ceo_tokens,

                response_mode=response_mode
            )
        )

        # =================================================
        # STAGE 4
        # CEO DECISION VALIDATION
        # =================================================

        print(
            "\n" + "=" * 60
        )

        print(
            "STAGE 4: CEO DECISION VALIDATION"
        )

        print(
            "=" * 60
        )

        final_decision = (
            self._normalize_ceo_decision(
                final_decision
            )
        )

        print(
            "\nVALIDATED CEO DECISION:"
        )

        print(
            final_decision
        )

        # =================================================
        # RETURN COMPLETE RESULT
        # =================================================

        return {

            "response_mode":
                response_mode,

            "execution_mode":
                execution_mode,

            "mode":
                mode,

            "token_budget":
                token_budget,

            # ---------------------------------------------
            # DOCUMENT INFORMATION
            # ---------------------------------------------

            "document_name":
                document_name,

            "retrieved_chunks":
                retrieved_count,

            "evidence_used":
                bool(context),

            # ---------------------------------------------
            # DYNAMIC AGENT SELECTION
            # ---------------------------------------------

            "selected_agents":
                selected_names,

            "selection_confidence":
                selection_confidence,

            "selection_method":
                selection_method,

            # ---------------------------------------------
            # EXECUTIVE OUTPUT
            # ---------------------------------------------

            "executive_analyses":
                executive_analyses,

            # ---------------------------------------------
            # DEBATE
            # ---------------------------------------------

            "debate":
                debate,

            # ---------------------------------------------
            # CEO DECISION
            # ---------------------------------------------

            "final_decision":
                final_decision,
        }

