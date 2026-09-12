from backend.app.agents.base_agent import BaseAgent
from backend.app.core.prompts import CPO_PROMPT


class CPOAgent(BaseAgent):
    """
    Chief Product Officer agent.

    Responsible for analyzing business decisions from
    a product, customer-value, and product-market-fit perspective.
    """

    def __init__(self, llm):
        super().__init__(
            role_name="CPO",
            role_prompt=CPO_PROMPT,
            llm=llm
        )