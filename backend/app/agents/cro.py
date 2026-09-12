from backend.app.agents.base_agent import BaseAgent
from backend.app.core.prompts import CRO_PROMPT


class CROAgent(BaseAgent):
    """
    Chief Revenue Officer agent.

    Responsible for analyzing business decisions from
    a revenue, sales, and customer-acquisition perspective.
    """

    def __init__(self, llm):
        super().__init__(
            role_name="CRO",
            role_prompt=CRO_PROMPT,
            llm=llm
        )