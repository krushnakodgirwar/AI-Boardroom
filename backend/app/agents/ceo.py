import re

from backend.app.agents.base_agent import BaseAgent
from backend.app.core.prompts import CEO_PROMPT


class CEOAgent(BaseAgent):
    """
    Chief Executive Officer agent.

    The CEO acts as the final decision-maker of the AI Boardroom.

    The CEO receives:
        - Original business question
        - Executive analyses
        - Boardroom debate
        - Optional RAG context
        - Optional structured data

    The CEO can produce the final answer in three formats:

        short
        executive_summary
        detailed
    """

    def __init__(self, llm):

        super().__init__(
            role_name="CEO",
            role_prompt=CEO_PROMPT,
            llm=llm
        )

    # =====================================================
    # RESPONSE STYLE INSTRUCTIONS
    # =====================================================

    @staticmethod
    def _get_response_style(response_mode):

        styles = {

            "short": """
==================================================
RESPONSE STYLE: SHORT
==================================================

Produce a concise CEO decision.

Use exactly this structure:

FINAL DECISION:
<one clear decision>

WHY:
- Most important reason
- Second important reason
- Third important reason if necessary

NEXT STEP:
<one concise recommended next action>

Do not add an OUTPUT section.

The FINAL DECISION and NEXT STEP must describe
the same primary action.

Keep the response highly concise.

Do not repeat the complete executive reports.

Target approximately 150-220 words.
""",

            "executive_summary": """
==================================================
RESPONSE STYLE: EXECUTIVE SUMMARY
==================================================

Produce a professional board-level executive summary.

Use exactly this structure:

FINAL DECISION:
<one clear decision>

RECOMMENDATION:
<concise explanation of the recommended action>

KEY REASONS:
1. <most important reason>
2. <second important reason>
3. <third important reason if supported>

KEY RISKS:
- <important risk>
- <important risk>

MISSING INFORMATION:
- <important unknown>
- <important unknown>

NEXT STEPS:
1. <action>
2. <action>
3. <action>

CONFIDENCE:
HIGH / MEDIUM / LOW

Do NOT add an OUTPUT section.

The FINAL DECISION, RECOMMENDATION, and NEXT STEPS
must describe the same primary action.

Keep the response concise but sufficiently informative
for a senior decision-maker.

Target approximately 250-350 words.
""",

            "detailed": """
==================================================
RESPONSE STYLE: DETAILED
==================================================

Produce a detailed Boardroom decision.

Use exactly this structure:

FINAL DECISION:
<one clear decision>

RECOMMENDATION:
<detailed explanation>

EXECUTIVE POSITIONS:
<accurate summary of the selected executives' positions>

KEY REASONS:
1. <reason>
2. <reason>
3. <reason>

KEY TRADE-OFF:
<important trade-off identified from the evidence>

MAJOR RISKS:
1. <risk>
2. <risk>
3. <risk>

MISSING INFORMATION:
1. <missing information>
2. <missing information>
3. <missing information>

CONDITIONS:
<conditions required for the decision, if applicable>

NEXT STEPS:
1. <action>
2. <action>
3. <action>

CONFIDENCE:
HIGH / MEDIUM / LOW

CONFIDENCE REASON:
<brief explanation>

Do NOT add an OUTPUT section.

The FINAL DECISION, RECOMMENDATION, CONDITIONS,
and NEXT STEPS must describe the same primary action.

Use only information contained in the executive
analyses, debate, context, and structured data.

Do not invent facts, numbers, market information,
technical capabilities, or probabilities.

Target approximately 400-550 words.
"""
        }

        return styles.get(
            response_mode,
            styles["executive_summary"]
        )

    # =====================================================
    # FINANCIAL EVIDENCE RULES
    # =====================================================

    @staticmethod
    def _get_financial_rules():

        return """
==================================================
STRICT FINANCIAL EVIDENCE RULES
==================================================

The CEO must use financially accurate terminology.

1. DISTINGUISH REVENUE, COST, PROFIT, SURPLUS,
   MARGIN, INVESTMENT, AND ROI.

2. If:

   Revenue = ₹30 lakh
   Development Cost = ₹8 lakh

   then:

   ₹30 lakh - ₹8 lakh = ₹22 lakh

   This may be described as:

   - revenue exceeding development cost
   - positive difference between revenue and development cost
   - surplus relative to development cost
   - expected revenue exceeding stated development cost

   DO NOT automatically call ₹22 lakh "ROI".

3. ROI requires an explicit investment/capital basis.

4. If NO explicit investment amount is provided:

   DO NOT calculate ROI.

   DO NOT claim positive ROI.

   DO NOT claim ROI is 275%.

5. Development cost and investment are NOT
   automatically interchangeable.

6. If investment is unavailable, say:

   "ROI cannot be determined from the available information."

7. Expected revenue is a projection.

8. Expected revenue must NOT be presented as:
   - guaranteed revenue
   - realized revenue
   - achieved revenue
   - actual revenue

9. Do not invent:
   - operating costs
   - marketing costs
   - salaries
   - cloud costs
   - taxes
   - investment
   - profit
   - additional revenue

10. Financial attractiveness does not equal
    commercial success.

11. Technical readiness and financial attractiveness
    are separate considerations.

12. A favorable financial comparison does not cancel
    an explicitly identified technical risk.

==================================================
END FINANCIAL RULES
==================================================
"""

    # =====================================================
    # EVIDENCE PRIORITY RULES
    # =====================================================

    @staticmethod
    def _get_evidence_rules():

        return """
==================================================
EVIDENCE PRIORITY RULES
==================================================

1. Base the final decision only on:

   - User question
   - Retrieved document evidence
   - Structured data
   - Executive analyses
   - Boardroom debate

2. Do not invent missing facts.

3. Do not convert uncertainty into certainty.

4. Explicit evidence has priority over unsupported
   executive claims.

5. Deterministic calculations must not be changed.

6. If an executive incorrectly interprets a number,
   use the underlying evidence.

7. Missing information must remain missing.

8. Do not treat absence of evidence as evidence
   of safety.

9. Do not treat projected numbers as guaranteed.

10. Do not claim commercial success unless
    explicitly supported.

11. The CEO is the final decision-maker, but must
    remain evidence-grounded.

12. FINAL FACTUAL CONSISTENCY CHECK:

    Before producing the final answer, cross-check
    every important factual claim against the
    original evidence.

13. If an executive statement conflicts with the
    original business question, structured data,
    retrieved evidence, or explicit evidence from
    the Boardroom, trust the original evidence.

14. Never state that a requirement, target, milestone,
    condition, risk, or capability is satisfied
    unless the evidence explicitly confirms it.

15. Never reverse the meaning of an explicitly stated
    failure, limitation, unmet target, or unresolved risk.

16. If the evidence says that a target is NOT met,
    do not describe that target as met.

17. If the evidence says that a risk is unresolved,
    do not describe that risk as resolved.

18. If evidence is conflicting, explicitly acknowledge
    the conflict instead of selecting the more favorable
    interpretation without support.

19. Before finalizing the decision, verify that:

    FINAL DECISION
    RECOMMENDATION
    KEY REASONS
    KEY RISKS
    CONDITIONS
    NEXT STEPS

    do not contain factual claims that contradict
    the strongest available evidence.

==================================================
END EVIDENCE RULES
==================================================
"""

    # =====================================================
    # DECISION QUALITY RULES
    # =====================================================

    @staticmethod
    def _get_decision_rules():

        return """
==================================================
CEO DECISION QUALITY RULES
==================================================

1. Separate financial attractiveness from
   technical readiness.

2. A favorable financial projection does not
   automatically mean that the product is ready
   for full launch.

3. If an explicitly identified technical risk
   exists, include it in the decision reasoning.

4. If the evidence supports proceeding only
   with conditions, clearly state those conditions.

5. If a pilot or controlled rollout is recommended,
   explain what evidence should be validated before
   full launch.

6. Do not invent conditions unrelated to the evidence.

7. Do not claim that a risk has been resolved unless
   the evidence explicitly states that it has been resolved.

8. If a key financial input is missing, identify it
   as missing rather than estimating it.

9. If ROI cannot be calculated, this must not prevent
   discussion of other evidence-based financial
   comparisons.

10. The final decision must reflect the strongest
    evidence available from the Boardroom.

11. THERE MUST BE ONLY ONE PRIMARY ACTION.

12. The following sections must remain consistent:

    FINAL DECISION
    RECOMMENDATION
    CONDITIONS
    NEXT STEPS

13. Do NOT produce an additional OUTPUT section.

14. Never say "postpone the launch" or
    "delay the launch" if FINAL DECISION is
    PROCEED WITH CONDITIONS, unless the final
    decision itself explicitly states that postponement
    is the chosen action.

15. Never say "launch immediately" if the final
    decision is PROCEED WITH CONDITIONS.

==================================================
END CEO DECISION QUALITY RULES
==================================================
"""

    # =====================================================
    # PRIMARY DECISION EXTRACTION
    # =====================================================

    @staticmethod
    def _extract_final_decision(response):

        if not response:
            return None

        text = str(response)

        match = re.search(
            r"FINAL\s+DECISION\s*:?\s*(?:\*+)?\s*"
            r"([^\n]+)",
            text,
            flags=re.IGNORECASE
        )

        if not match:
            return None

        decision = match.group(1).strip()

        decision = decision.strip(
            "*# :"
        )

        return decision.upper()

    # =====================================================
    # REMOVE CONTRADICTORY OUTPUT SECTION
    # =====================================================

    @classmethod
    def _remove_output_section(cls, response):

        if not response:
            return response

        text = str(response).strip()

        # -------------------------------------------------
        # Remove everything starting from an OUTPUT heading.
        #
        # Qwen sometimes adds:
        #
        # OUTPUT:
        # ...
        #
        # after producing the requested response.
        # -------------------------------------------------

        cleaned = re.split(
            r"\n\s*(?:\*\*|#+\s*)?OUTPUT\s*:?\s*",
            text,
            maxsplit=1,
            flags=re.IGNORECASE
        )[0]

        return cleaned.strip()

    # =====================================================
    # DECISION CONSISTENCY CLEANUP
    # =====================================================

    @classmethod
    def _clean_decision_consistency(cls, response):

        if not response:
            return response

        text = str(response).strip()

        decision = cls._extract_final_decision(
            text
        )

        if not decision:
            return text

        # -------------------------------------------------
        # First remove any unwanted OUTPUT section.
        # -------------------------------------------------

        text = cls._remove_output_section(
            text
        )

        # -------------------------------------------------
        # Normalize whitespace.
        # -------------------------------------------------

        text = re.sub(
            r"\n{3,}",
            "\n\n",
            text
        ).strip()

        # -------------------------------------------------
        # The final decision itself remains authoritative.
        #
        # We do NOT rewrite the CEO's reasoning.
        # We only remove contradictory trailing OUTPUT
        # content and protect the single-primary-action rule.
        # -------------------------------------------------

        return text

    # =====================================================
    # FINAL CEO DECISION
    # =====================================================

    def make_final_decision(
        self,
        user_question,
        executive_analyses,
        context=None,
        data=None,
        max_new_tokens=300,
        response_mode="executive_summary"
    ):
        """
        Synthesize the analyses from the selected executives
        and produce the final Boardroom recommendation.
        """

        # =================================================
        # VALIDATE RESPONSE MODE
        # =================================================

        valid_modes = {
            "short",
            "executive_summary",
            "detailed"
        }

        if response_mode not in valid_modes:

            response_mode = "executive_summary"

        # =================================================
        # SAVE ORIGINAL ROLE PROMPT
        # =================================================

        original_role_prompt = self.role_prompt

        # =================================================
        # BUILD CEO INSTRUCTIONS
        # =================================================

        style_instruction = (
            self._get_response_style(
                response_mode
            )
        )

        financial_rules = (
            self._get_financial_rules()
        )

        evidence_rules = (
            self._get_evidence_rules()
        )

        decision_rules = (
            self._get_decision_rules()
        )

        # =================================================
        # COMBINE INSTRUCTIONS
        # =================================================

        self.role_prompt = (
            original_role_prompt
            + "\n\n"
            + evidence_rules
            + "\n\n"
            + financial_rules
            + "\n\n"
            + decision_rules
            + "\n\n"
            + style_instruction
        )

        # =================================================
        # GENERATE FINAL DECISION
        # =================================================

        try:

            response = self.analyze(
                user_question=user_question,
                context=context,
                data=data,
                agent_analyses=executive_analyses,
                max_new_tokens=max_new_tokens
            )

        finally:

            # Restore the original prompt so repeated
            # Boardroom runs do not accumulate instructions.

            self.role_prompt = (
                original_role_prompt
            )

        # =================================================
        # CLEAN RESPONSE
        # =================================================

        if response is None:

            return ""

        cleaned_response = (
            self._clean_decision_consistency(
                response
            )
        )

        return cleaned_response.strip()