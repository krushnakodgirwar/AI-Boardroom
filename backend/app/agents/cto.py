import re

from backend.app.agents.base_agent import BaseAgent
from backend.app.core.prompts import CTO_PROMPT


class CTOAgent(BaseAgent):
    """
    Chief Technology Officer agent.

    Responsible for analyzing business decisions from
    a technology and technical feasibility perspective.

    The CTO:
        - evaluates technical feasibility
        - identifies technical risks
        - identifies missing technical information
        - provides a technical recommendation

    The CTO does NOT make the final company-wide decision.
    """

    def __init__(self, llm):

        super().__init__(
            role_name="CTO",
            role_prompt=CTO_PROMPT,
            llm=llm
        )

    # =====================================================
    # REMOVE UNWANTED TERMINATION TOKENS
    # =====================================================

    @staticmethod
    def _clean_output(response):
        """
        Remove accidental termination tokens such as
        STOP from the end of the LLM response.

        The CTO should return a complete executive report,
        not a termination command.
        """

        if not response:
            return response

        text = response.strip()

        # -------------------------------------------------
        # Remove STOP if it appears as a standalone token
        # at the end of the response.
        # -------------------------------------------------

        text = re.sub(
            r"\s*\bSTOP\b\s*\.?\s*$",
            "",
            text,
            flags=re.IGNORECASE
        )

        return text.strip()

    # =====================================================
    # CTO ANALYSIS
    # =====================================================

    def analyze(
        self,
        user_question,
        context=None,
        data=None,
        agent_analyses=None,
        max_new_tokens=500
    ):
        """
        Generate the CTO technical assessment.

        The CTO analyzes only technical considerations
        supported by the available evidence.
        """

        response = super().analyze(
            user_question=user_question,
            context=context,
            data=data,
            agent_analyses=agent_analyses,
            max_new_tokens=max_new_tokens
        )

        return self._clean_output(
            response
        )