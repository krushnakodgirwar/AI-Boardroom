from backend.app.agents.base_agent import BaseAgent
from backend.app.core.prompts import RISK_PROMPT


class RiskAgent(BaseAgent):
    """
    Chief Risk Officer agent.

    Responsibilities:
    - Detect explicit risks from the user question.
    - Detect explicit risks from retrieved document evidence.
    - Never invent risks.
    - Never treat missing information as a risk.
    - Never allow the LLM to erase an explicitly stated risk.
    """

    # =========================================================
    # NO-RISK RESPONSE
    # =========================================================

    NO_RISK_RESPONSE = """RISK ASSESSMENT:
UNCERTAIN

KEY RISKS:
No specific risk can be established from the available information.

RISK EVIDENCE:
The available information is insufficient to establish specific enterprise risks.

MITIGATION:
No specific risk mitigation can be recommended because no specific risk has been established.

MISSING RISK INFORMATION:
Insufficient evidence to identify specific enterprise risks.

RISK RECOMMENDATION:
No specific risk-based recommendation can be made from the available evidence.

CONFIDENCE:
LOW"""

    # =========================================================
    # EXPLICIT RISK PATTERNS
    # =========================================================

    RISK_EVIDENCE_PATTERNS = {

        "performance": [
            "fails the response-time",
            "fails response-time",
            "fails the response time",
            "fails response time",
            "response-time target",
            "response time target",
            "slow response",
            "slow responses",
            "latency problem",
            "latency problems",
            "high latency",
            "performance failure",
            "performance problem",
            "performance problems",
            "poor performance",
            "performance degradation",
            "does not meet the response-time",
            "does not meet response-time",
            "does not meet the response time",
            "misses the response-time",
            "misses response-time",
            "misses the response time",
        ],

        "scalability": [
            "scalability problem",
            "scalability problems",
            "scalability issue",
            "scalability issues",
            "does not scale",
            "cannot scale",
            "fails under heavy usage",
            "fails under heavy load",
            "fails under high traffic",
            "scaling failure",
            "scaling problem",
            "scaling problems",
            "scalability failure",
            "scalability risk",
        ],

        "stability": [
            "system becomes unstable",
            "system is unstable",
            "system instability",
            "becomes unstable",
            "unstable under traffic",
            "unstable under load",
            "crashes under load",
            "crashes under heavy usage",
            "crashes under heavy load",
            "system crashes",
            "frequent crashes",
            "application crashes",
            "service crashes",
        ],

        "security": [
            "security vulnerability",
            "security vulnerabilities",
            "security breach",
            "data breach",
            "unauthorized access",
            "security failure",
            "authentication failure",
            "security incident",
            "data leak",
            "data leakage",
        ],

        "regulatory": [
            "regulatory violation",
            "regulatory violation notice",
            "violates gdpr",
            "gdpr violation",
            "compliance violation",
            "non-compliant",
            "not compliant",
            "failed compliance",
            "compliance failure",
            "regulatory failure",
        ],

        "financial": [
            "budget is insufficient",
            "insufficient budget",
            "budget is lower than",
            "cost exceeds budget",
            "cost is higher than budget",
            "cannot afford",
            "funding shortfall",
            "cash shortfall",
            "negative profit",
            "operating loss",
            "financial loss",
            "loss of revenue",
        ],

        "operational": [
            "supplier is unavailable",
            "supplier unavailable",
            "operational failure",
            "production failure",
            "capacity constraint",
            "insufficient capacity",
            "delivery failure",
            "cannot deliver",
            "operational problem",
            "operational problems",
        ],

        "customer": [
            "customers rejected",
            "customer rejection",
            "low customer adoption",
            "low adoption",
            "customers are not adopting",
            "customer churn",
            "high churn",
            "customer complaints",
            "customers are dissatisfied",
            "customer dissatisfaction",
        ],
    }

    # =========================================================
    # CONSTRUCTOR
    # =========================================================

    def __init__(self, llm):

        super().__init__(
            role_name="Risk Officer",
            role_prompt=RISK_PROMPT,
            llm=llm
        )

    # =========================================================
    # NORMALIZE TEXT
    # =========================================================

    @staticmethod
    def _normalize_text(text):
        """
        Normalize text for deterministic matching.
        """

        if text is None:
            return ""

        return " ".join(
            str(text)
            .lower()
            .split()
        )

    # =========================================================
    # BUILD COMPLETE EVIDENCE
    # =========================================================

    @staticmethod
    def _build_evidence_text(
        question=None,
        context=None
    ):
        """
        Combine:

        1. User question
        2. Retrieved document evidence

        Risk detection searches the complete evidence.
        """

        parts = []

        # -----------------------------------------------------
        # USER QUESTION
        # -----------------------------------------------------

        if question:

            parts.append(
                "USER QUESTION:\n"
                + str(question)
            )

        # -----------------------------------------------------
        # DOCUMENT / RAG CONTEXT
        # -----------------------------------------------------

        if context:

            if isinstance(
                context,
                (list, tuple)
            ):

                context_parts = []

                for item in context:

                    if isinstance(
                        item,
                        dict
                    ):

                        if item.get("text"):

                            context_parts.append(
                                str(
                                    item["text"]
                                )
                            )

                        elif item.get("evidence"):

                            context_parts.append(
                                str(
                                    item["evidence"]
                                )
                            )

                        else:

                            context_parts.append(
                                str(item)
                            )

                    else:

                        context_parts.append(
                            str(item)
                        )

                context_text = "\n".join(
                    context_parts
                )

            elif isinstance(
                context,
                dict
            ):

                if context.get("text"):

                    context_text = str(
                        context["text"]
                    )

                elif context.get("evidence"):

                    context_text = str(
                        context["evidence"]
                    )

                else:

                    context_text = "\n".join(
                        f"{key}: {value}"
                        for key, value
                        in context.items()
                    )

            else:

                context_text = str(
                    context
                )

            parts.append(
                "RETRIEVED DOCUMENT EVIDENCE:\n"
                + context_text
            )

        return "\n\n".join(
            parts
        )

    # =========================================================
    # DETECT EXPLICIT RISK EVIDENCE
    # =========================================================

    @classmethod
    def _detect_explicit_risk_evidence(
        cls,
        question
    ):
        """
        Detect only risks explicitly stated in the evidence.

        No risk is inferred from missing information.
        """

        text = cls._normalize_text(
            question
        )

        detected = []

        for category, patterns in (
            cls.RISK_EVIDENCE_PATTERNS.items()
        ):

            for pattern in patterns:

                if pattern in text:

                    detected.append(
                        {
                            "category": category,
                            "evidence": pattern
                        }
                    )

                    break

        return detected

    # =========================================================
    # BUILD DETERMINISTIC RISK RESPONSE
    # =========================================================

    @classmethod
    def _build_explicit_risk_response(
        cls,
        detected_risks
    ):
        """
        Build an evidence-grounded risk response.

        This is authoritative whenever explicit risk evidence
        exists.
        """

        risk_lines = []
        evidence_lines = []
        mitigation_lines = []

        seen_categories = set()

        for item in detected_risks:

            category = item[
                "category"
            ]

            evidence = item[
                "evidence"
            ]

            if category in seen_categories:
                continue

            seen_categories.add(
                category
            )

            # -------------------------------------------------
            # PERFORMANCE
            # -------------------------------------------------

            if category == "performance":

                risk_lines.append(
                    "Performance risk: the stated response-time "
                    "target is not being met."
                )

                evidence_lines.append(
                    "The available evidence explicitly states "
                    f"'{evidence}'."
                )

                mitigation_lines.append(
                    "Investigate and resolve the response-time "
                    "failure before relying on full-scale deployment."
                )

            # -------------------------------------------------
            # SCALABILITY
            # -------------------------------------------------

            elif category == "scalability":

                risk_lines.append(
                    "Scalability risk: the system has problems "
                    "under increased usage or load."
                )

                evidence_lines.append(
                    "The available evidence explicitly states "
                    f"'{evidence}'."
                )

                mitigation_lines.append(
                    "Validate scalability under the stated load "
                    "conditions before full deployment."
                )

            # -------------------------------------------------
            # STABILITY
            # -------------------------------------------------

            elif category == "stability":

                risk_lines.append(
                    "System stability risk: the system becomes "
                    "unstable under the stated conditions."
                )

                evidence_lines.append(
                    "The available evidence explicitly states "
                    f"'{evidence}'."
                )

                mitigation_lines.append(
                    "Identify and resolve the instability before "
                    "full deployment."
                )

            # -------------------------------------------------
            # SECURITY
            # -------------------------------------------------

            elif category == "security":

                risk_lines.append(
                    "Security risk: a concrete security problem "
                    "is explicitly identified."
                )

                evidence_lines.append(
                    "The available evidence explicitly states "
                    f"'{evidence}'."
                )

                mitigation_lines.append(
                    "Address the identified security issue before "
                    "deployment."
                )

            # -------------------------------------------------
            # REGULATORY
            # -------------------------------------------------

            elif category == "regulatory":

                risk_lines.append(
                    "Regulatory/compliance risk: the evidence "
                    "contains an explicit compliance problem."
                )

                evidence_lines.append(
                    "The available evidence explicitly states "
                    f"'{evidence}'."
                )

                mitigation_lines.append(
                    "Resolve the identified compliance issue "
                    "before proceeding."
                )

            # -------------------------------------------------
            # FINANCIAL
            # -------------------------------------------------

            elif category == "financial":

                risk_lines.append(
                    "Financial risk: the evidence explicitly "
                    "indicates a financial shortfall or loss."
                )

                evidence_lines.append(
                    "The available evidence explicitly states "
                    f"'{evidence}'."
                )

                mitigation_lines.append(
                    "Resolve the identified financial constraint "
                    "before proceeding."
                )

            # -------------------------------------------------
            # OPERATIONAL
            # -------------------------------------------------

            elif category == "operational":

                risk_lines.append(
                    "Operational risk: the evidence explicitly "
                    "identifies an operational failure or constraint."
                )

                evidence_lines.append(
                    "The available evidence explicitly states "
                    f"'{evidence}'."
                )

                mitigation_lines.append(
                    "Address the identified operational constraint "
                    "before proceeding."
                )

            # -------------------------------------------------
            # CUSTOMER
            # -------------------------------------------------

            elif category == "customer":

                risk_lines.append(
                    "Customer risk: the evidence explicitly "
                    "identifies a customer adoption or retention problem."
                )

                evidence_lines.append(
                    "The available evidence explicitly states "
                    f"'{evidence}'."
                )

                mitigation_lines.append(
                    "Address the identified customer issue before "
                    "full deployment."
                )

        # =====================================================
        # RETURN AUTHORITATIVE RESPONSE
        # =====================================================

        return (
            "RISK ASSESSMENT:\n"
            "HIGH\n\n"

            "KEY RISKS:\n"
            + "\n".join(
                f"{i + 1}. {risk}"
                for i, risk in enumerate(
                    risk_lines[:3]
                )
            )

            + "\n\n"

            "RISK EVIDENCE:\n"
            + "\n".join(
                f"{i + 1}. {evidence}"
                for i, evidence in enumerate(
                    evidence_lines[:3]
                )
            )

            + "\n\n"

            "MITIGATION:\n"
            + "\n".join(
                f"{i + 1}. {mitigation}"
                for i, mitigation in enumerate(
                    mitigation_lines[:3]
                )
            )

            + "\n\n"

            "MISSING RISK INFORMATION:\n"
            "No additional information is required to establish "
            "the explicitly identified risk.\n\n"

            "RISK RECOMMENDATION:\n"
            "Address the explicitly identified risk conditions "
            "before proceeding with full deployment.\n\n"

            "CONFIDENCE:\n"
            "HIGH"
        )

    # =========================================================
    # DETECT NO-RISK OUTPUT
    # =========================================================

    @staticmethod
    def _is_no_risk_output(
        response
    ):
        """
        Detect common LLM no-risk responses.
        """

        if not response:
            return False

        text = str(
            response
        ).lower()

        indicators = [

            "no specific risk can be established",

            "no specific risk can be identified",

            "no specific enterprise risk",

            "no specific risk evidence",

            "no specific risk has been established",

            "no specific risk was identified",

            "no material risk identified",

            "no concrete risk identified",

            "no material risk",

        ]

        return any(
            indicator in text
            for indicator in indicators
        )

    # =========================================================
    # ANALYZE
    # =========================================================

    def analyze(
        self,
        question=None,
        context=None,
        max_new_tokens=300,
        **kwargs
    ):
        """
        Complete Risk Agent analysis.

        IMPORTANT:

        If explicit risk evidence is detected, that evidence
        is authoritative.

        The LLM cannot downgrade an explicitly stated risk
        to "UNCERTAIN" or "NO RISK".
        """

        # =====================================================
        # RECOVER QUESTION
        # =====================================================

        if question is None:

            question = (
                kwargs.get(
                    "user_question"
                )
                or kwargs.get(
                    "query"
                )
                or kwargs.get(
                    "prompt"
                )
                or ""
            )

        # =====================================================
        # BUILD COMPLETE EVIDENCE
        # =====================================================

        evidence_text = (
            self._build_evidence_text(
                question=question,
                context=context
            )
        )

        print(
            "\nRiskAgent: Checking user question "
            "+ retrieved document evidence..."
        )

        # =====================================================
        # DETERMINISTIC RISK DETECTION
        # =====================================================

        detected_risks = (
            self._detect_explicit_risk_evidence(
                evidence_text
            )
        )

        print(
            "RiskAgent: Explicit risks detected: "
            f"{detected_risks}"
        )

        # =====================================================
        # ASK LLM FOR INTERPRETATION
        # =====================================================

        response = None

        try:

            response = super().analyze(
                evidence_text,
                context=context,
                max_new_tokens=max_new_tokens,
                **kwargs
            )

        except TypeError:

            try:

                response = super().analyze(
                    evidence_text,
                    max_new_tokens=max_new_tokens
                )

            except Exception as exc:

                print(
                    "RiskAgent BaseAgent analysis error:",
                    exc
                )

        except Exception as exc:

            print(
                "RiskAgent analysis error:",
                exc
            )

        # =====================================================
        # CRITICAL RULE
        # =====================================================
        #
        # If Python found explicit risk evidence,
        # ALWAYS use the deterministic evidence-grounded
        # response.
        #
        # This prevents Qwen from saying:
        #
        # "No material risk"
        #
        # when the document explicitly says:
        #
        # "prototype fails response-time target."
        #
        # =====================================================

        if detected_risks:

            print(
                "RiskAgent: Explicit risk evidence confirmed."
            )

            print(
                "RiskAgent: Deterministic risk evidence "
                "takes priority over LLM uncertainty."
            )

            return (
                self._build_explicit_risk_response(
                    detected_risks
                )
            )

        # =====================================================
        # NO EXPLICIT RISK
        # =====================================================

        if not response:

            print(
                "RiskAgent: No explicit risk detected "
                "and no usable LLM response."
            )

            return self.NO_RISK_RESPONSE

        response = str(
            response
        ).strip()

        # =====================================================
        # EMPTY LLM RESPONSE
        # =====================================================

        if not response:

            return self.NO_RISK_RESPONSE

        # =====================================================
        # LLM NO-RISK RESPONSE
        # =====================================================

        if self._is_no_risk_output(
            response
        ):

            print(
                "RiskAgent: No explicit risk detected."
            )

            return self.NO_RISK_RESPONSE

        # =====================================================
        # NORMAL LLM RESPONSE
        # =====================================================

        return response