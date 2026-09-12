"""
Hybrid Boardroom Agent Selector.

Combines deterministic rule-based selection with the LLM
selector only when the deterministic result is insufficient
or genuinely ambiguous.

Important design principle:

    The LLM supplements deterministic evidence.

    It must NOT blindly add unrelated agents to a strong
    rule-based selection.
"""

from backend.app.agents.selector import AgentSelector
from backend.app.agents.llm_selector import LLMAgentSelector


class HybridAgentSelector:
    """
    Hybrid Boardroom Agent Selection System.
    """

    # =========================================================
    # CONFIDENCE THRESHOLDS
    # =========================================================

    HIGH_CONFIDENCE = 0.75
    MEDIUM_CONFIDENCE = 0.45

    # =========================================================
    # AGENT LIMITS
    # =========================================================

    MIN_AGENTS = 2
    MAX_AGENTS = 6

    # =========================================================
    # CONSTRUCTOR
    # =========================================================

    def __init__(self, llm):

        self.rule_selector = AgentSelector()

        self.llm_selector = LLMAgentSelector(
            llm
        )

    # =========================================================
    # CLEAN AGENTS
    # =========================================================

    @staticmethod
    def _clean_agents(
        agents
    ):
        """
        Normalize and deduplicate agent names.
        """

        if not agents:
            return []

        cleaned = []

        for agent in agents:

            if not isinstance(
                agent,
                str
            ):
                continue

            agent = (
                agent
                .lower()
                .strip()
            )

            if agent and agent not in cleaned:

                cleaned.append(
                    agent
                )

        return cleaned

    # =========================================================
    # SELECT
    # =========================================================

    def select_agents(
        self,
        question
    ):
        """
        Select Boardroom executives.

        Strategy:

        1. High-confidence rule selection
           -> use rules directly.

        2. Medium-confidence rule selection with enough
           relevant agents
           -> use rules directly.

        3. Medium-confidence selection with too few agents
           -> consult LLM for supplementary expertise.

        4. Low-confidence selection
           -> consult LLM.

        The LLM is never blindly merged into a sufficiently
        strong deterministic selection.
        """

        # =====================================================
        # EMPTY QUESTION
        # =====================================================

        if not question:

            return {
                "agents": [
                    "cfo",
                    "cto",
                    "risk"
                ],
                "confidence": 0.0,
                "method": "fallback"
            }

        # =====================================================
        # RULE SELECTION
        # =====================================================

        print(
            "\nRunning Rule-Based Selector..."
        )

        rule_result = (
            self.rule_selector.select_agents(
                question
            )
        )

        rule_agents = self._clean_agents(
            rule_result.get(
                "agents",
                []
            )
        )

        rule_confidence = float(
            rule_result.get(
                "confidence",
                0.0
            )
        )

        print(
            "Rule Agents:",
            rule_agents
        )

        print(
            "Rule Confidence:",
            rule_confidence
        )

        # =====================================================
        # CASE 1
        # HIGH CONFIDENCE
        # =====================================================

        if (
            rule_confidence
            >= self.HIGH_CONFIDENCE
        ):

            print(
                "Using Rule-Based Selection"
            )

            return {
                "agents": rule_agents[
                    :self.MAX_AGENTS
                ],
                "confidence": rule_confidence,
                "method": "rule"
            }

        # =====================================================
        # CASE 2
        # MEDIUM CONFIDENCE + SUFFICIENT AGENTS
        #
        # Example:
        #
        # Employee training
        #     ↓
        # CHRO + CPO + Risk
        #
        # Three relevant agents already exist.
        # No need to let a small LLM hallucination add CTO.
        # =====================================================

        if (
            rule_confidence
            >= self.MEDIUM_CONFIDENCE
            and len(rule_agents) >= 3
        ):

            print(
                "Rule selection has sufficient "
                "domain coverage."
            )

            print(
                "Using Rule-Based Selection "
                "without LLM expansion."
            )

            return {
                "agents": rule_agents[
                    :self.MAX_AGENTS
                ],
                "confidence": rule_confidence,
                "method": "rule"
            }

        # =====================================================
        # CASE 3 / 4
        # LLM NEEDED
        # =====================================================

        print(
            "Rule confidence is insufficient "
            "for standalone selection."
        )

        print(
            "Using LLM Selector..."
        )

        try:

            llm_agents = (
                self.llm_selector.select_agents(
                    question
                )
            )

        except Exception as exc:

            print(
                "LLM Selector failed:",
                exc
            )

            llm_agents = []

        llm_agents = self._clean_agents(
            llm_agents
        )

        print(
            "LLM Agents:",
            llm_agents
        )

        # =====================================================
        # BUILD FINAL SELECTION
        # =====================================================

        final_agents = []

        # -----------------------------------------------------
        # Rule evidence always comes first.
        # -----------------------------------------------------

        for agent in rule_agents:

            if agent not in final_agents:

                final_agents.append(
                    agent
                )

        # -----------------------------------------------------
        # Add LLM agents only when rule selection is weak.
        #
        # This prevents the LLM from replacing strong
        # deterministic evidence.
        # -----------------------------------------------------

        for agent in llm_agents:

            if agent not in final_agents:

                final_agents.append(
                    agent
                )

            if len(final_agents) >= self.MAX_AGENTS:

                break

        # =====================================================
        # FALLBACK
        # =====================================================

        if len(final_agents) < self.MIN_AGENTS:

            final_agents = [
                "cfo",
                "cto",
                "risk"
            ]

            method = "fallback"

            effective_confidence = 0.0

        else:

            method = "hybrid"

            # -------------------------------------------------
            # Effective confidence
            # -------------------------------------------------

            if (
                rule_confidence
                >= self.MEDIUM_CONFIDENCE
            ):

                effective_confidence = round(
                    min(
                        rule_confidence + 0.05,
                        0.74
                    ),
                    2
                )

            else:

                effective_confidence = round(
                    min(
                        rule_confidence,
                        0.44
                    ),
                    2
                )

        # =====================================================
        # FINAL LIMIT
        # =====================================================

        final_agents = final_agents[
            :self.MAX_AGENTS
        ]

        # =====================================================
        # OUTPUT
        # =====================================================

        print(
            "Final Hybrid Agents:",
            final_agents
        )

        print(
            "Selection Method:",
            method
        )

        print(
            "Effective Confidence:",
            effective_confidence
        )

        return {
            "agents": final_agents,
            "confidence": effective_confidence,
            "method": method
        }