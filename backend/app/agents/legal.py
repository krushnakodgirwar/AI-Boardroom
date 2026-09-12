from backend.app.agents.base_agent import BaseAgent
from backend.app.core.prompts import LEGAL_PROMPT


class LegalAgent(BaseAgent):
    """
    Legal and Compliance Advisor agent.

    Responsible for analyzing business decisions from
    a legal, regulatory, and compliance perspective.
    """

    def __init__(self, llm):
        super().__init__(
            role_name="Legal Advisor",
            role_prompt=LEGAL_PROMPT,
            llm=llm
        )