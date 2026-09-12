import re

from backend.app.agents.cfo import CFOAgent
from backend.app.core.prompts import CFO_PROMPT


class FastCFOAgent(CFOAgent):
    """
    Fast Mode CFO agent.

    IMPORTANT:
    - Reuses all deterministic CFO calculations from CFOAgent.
    - Reuses financial extraction.
    - Reuses authoritative financial facts.
    - Reuses deterministic benefits and risks.
    - Only the LLM interpretation prompt is made compact.
    - Accurate Mode CFOAgent remains unchanged.
    """

    def __init__(self, llm):

        super().__init__(llm)

    # =========================================================
    # FAST CFO ANALYSIS
    # =========================================================

    def analyze(
        self,
        user_question,
        context=None,
        data=None,
        agent_analyses=None,
        max_new_tokens=300,
        execution_mode=None
    ):
        """
        Run deterministic CFO processing and then use a
        compact Fast Mode interpretation prompt.
        """

        # =====================================================
        # STRUCTURED DATA
        # =====================================================

        if isinstance(data, dict):

            enhanced_data = {
                **data
            }

        elif data is None:

            enhanced_data = {}

        else:

            enhanced_data = {
                "original_data": str(data)
            }

        # =====================================================
        # EVIDENCE
        # =====================================================

        evidence_text = self._build_evidence_text(
            user_question=user_question,
            context=context,
            data=enhanced_data
        )

        # =====================================================
        # EXTRACTION
        # =====================================================

        print(
            "\nFast CFO: Extracting financial values..."
        )

        extracted = self.extract_financial_inputs(
            evidence_text
        )

        print(
            "Fast CFO: Extracted financial inputs:",
            extracted
        )

        # =====================================================
        # MERGE EXTRACTED VALUES
        # =====================================================

        for key, value in extracted.items():

            if key not in enhanced_data:

                enhanced_data[key] = value

        # =====================================================
        # DETERMINISTIC FINANCIAL CALCULATIONS
        # =====================================================

        metrics = self.calculate_financials(
            enhanced_data
        )

        print(
            "Fast CFO: Deterministic financial metrics:",
            metrics
        )

        # =====================================================
        # AUTHORITATIVE CFO CONTEXT
        # =====================================================

        financial_context = self.build_interpretation_context(
            enhanced_data,
            metrics
        )

        # =====================================================
        # COMPACT FAST SYSTEM PROMPT
        # =====================================================

        system_prompt = f"""
{CFO_PROMPT}

FAST MODE CFO RULES:

1. Python financial calculations are the source of truth.
2. Do NOT perform financial arithmetic.
3. Do NOT recalculate or change numbers.
4. Do NOT reverse financial comparisons.
5. Revenue minus development cost is NOT automatically profit.
6. Report profit only if Python calculated profit.
7. Report ROI only if Python calculated ROI.
8. Use only the authoritative financial benefits.
9. Use only the authoritative financial risks.
10. Do not move benefits into risks or risks into benefits.
11. Do not invent financial information.
12. Do not make the final company-wide decision.
13. Do not output STOP.

AUTHORITATIVE CFO DATA:

{financial_context}

Return a concise CFO analysis with:

FINANCIAL ASSESSMENT:
ATTRACTIVE / UNCERTAIN / RISKY

KEY FINANCIAL FACTORS:
Up to 3 points.

FINANCIAL BENEFITS:
Use only authoritative benefits.

FINANCIAL RISKS:
Use only authoritative risks.

MISSING FINANCIAL INFORMATION:
Use only genuinely missing information.

CFO RECOMMENDATION:
1-2 sentences.

CONFIDENCE:
HIGH / MEDIUM / LOW
"""

        # =====================================================
        # COMPACT USER PROMPT
        # =====================================================

        other_analyses = (
            str(agent_analyses)[:3000]
            if agent_analyses
            else "None available."
        )

        user_prompt = f"""
BUSINESS DECISION:

{user_question}

AUTHORITATIVE CFO DATA:

{financial_context}

OTHER EXECUTIVE ANALYSES:

{other_analyses}

TASK:

Interpret the authoritative CFO data.

Do not calculate.
Do not recalculate.
Do not reverse comparisons.
Do not contradict Python calculations.
Do not move benefits into risks.
Do not move risks into benefits.

Return only the concise CFO analysis.
"""

        # =====================================================
        # GENERATE
        # =====================================================

        response = self.llm.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_new_tokens=max_new_tokens
        )

        if response is None:
            response = ""

        response = response.strip()

        # =====================================================
        # REMOVE STOP
        # =====================================================

        response = re.sub(
            r"\s*STOP\.?\s*$",
            "",
            response,
            flags=re.IGNORECASE
        ).strip()

        # =====================================================
        # FINAL DETERMINISTIC FINANCIAL FACTS
        # =====================================================

        financial_facts = self.build_financial_facts(
            enhanced_data,
            metrics
        )

        # =====================================================
        # FINAL OUTPUT
        # =====================================================

        final_output = [
            "FINANCIAL FACTS",
            "==============="
        ]

        if financial_facts:

            for fact in financial_facts:

                final_output.append(
                    "- " + fact
                )

        else:

            final_output.append(
                "- No deterministic financial facts available."
            )

        final_output.append("")

        final_output.append(response)

        return "\n".join(
            final_output
        ).strip()