from backend.app.agents.base_agent import BaseAgent
from backend.app.core.prompts import CMO_PROMPT


class CMOAgent(BaseAgent):
    """
    Chief Marketing Officer agent.

    Responsible for analyzing business decisions from
    a market, customer, and competitive perspective.
    """

    def __init__(self, llm):
        super().__init__(
            role_name="CMO",
            role_prompt=CMO_PROMPT,
            llm=llm
        )