import re

from backend.app.agents.fast_base_agent import FastBaseAgent
from backend.app.core.prompts import CPO_PROMPT


class FastCPOAgent(FastBaseAgent):
    """
    Fast Mode CPO agent.

    Accurate Mode CPOAgent remains unchanged.
    """

    def __init__(self, llm):

        super().__init__(
            role_name="CPO",
            role_prompt=CPO_PROMPT,
            llm=llm
        )

    @staticmethod
    def _clean_output(response):

        if not response:
            return response

        text = response.strip()

        text = re.sub(
            r"\s*\bSTOP\b\s*\.?\s*$",
            "",
            text,
            flags=re.IGNORECASE
        )

        return text.strip()

    def analyze(
        self,
        user_question,
        context=None,
        data=None,
        agent_analyses=None,
        max_new_tokens=500,
        execution_mode=None
    ):
        """
        Generate compact CPO analysis.

        execution_mode is accepted for BoardroomWorkflow
        compatibility but is handled by the registry/workflow.
        """

        response = super().analyze(
            user_question=user_question,
            context=context,
            data=data,
            agent_analyses=agent_analyses,
            max_new_tokens=max_new_tokens
        )

        return self._clean_output(response)