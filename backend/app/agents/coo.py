from backend.app.agents.base_agent import BaseAgent
from backend.app.core.prompts import COO_PROMPT


class COOAgent(BaseAgent):
    """
    Chief Operating Officer agent.

    Responsible for analyzing business decisions from
    an operations and execution perspective.
    """

    def __init__(self, llm):
        super().__init__(
            role_name="COO",
            role_prompt=COO_PROMPT,
            llm=llm
        )