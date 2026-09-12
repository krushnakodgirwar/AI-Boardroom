from backend.app.agents.base_agent import BaseAgent
from backend.app.core.prompts import CSO_PROMPT


class CSOAgent(BaseAgent):
    """
    Chief Strategy Officer agent.

    Responsible for analyzing business decisions from
    a strategic and long-term business perspective.
    """

    def __init__(self, llm):
        super().__init__(
            role_name="CSO",
            role_prompt=CSO_PROMPT,
            llm=llm
        )