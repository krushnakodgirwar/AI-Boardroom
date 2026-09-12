from backend.app.agents.base_agent import BaseAgent
from backend.app.core.prompts import CHRO_PROMPT


class CHROAgent(BaseAgent):
    """
    Chief Human Resources Officer agent.

    Responsible for analyzing business decisions from
    a people, workforce, and organizational perspective.
    """

    def __init__(self, llm):
        super().__init__(
            role_name="CHRO",
            role_prompt=CHRO_PROMPT,
            llm=llm
        )