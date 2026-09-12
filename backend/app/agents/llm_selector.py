"""
LLM-based Boardroom Agent Selector.

Qwen is used when deterministic selection is uncertain.

Pipeline:

    Question
        ↓
    Qwen selection
        ↓
    Parse
        ↓
    Validate
        ↓
    Rule-based recovery if necessary
        ↓
    Final agent list
"""

import re

from backend.app.agents.selector import AgentSelector


class LLMAgentSelector:
    """
    Uses the shared LLM to select relevant Boardroom executives.
    """

    # =========================================================
    # AVAILABLE AGENTS
    # =========================================================

    AVAILABLE_AGENTS = {
        "cfo":
            "Finance, costs, revenue, profitability, ROI, investments",

        "cmo":
            "Market analysis, customers, competition, branding, marketing strategy",

        "cto":
            "Technology feasibility, architecture, engineering, security, scalability",

        "coo":
            "Operations, execution, resources, processes, delivery",

        "cso":
            "Business strategy, long-term direction, partnerships, growth strategy",

        "cpo":
            "Product strategy, product-market fit, features, user experience",

        "cro":
            "Revenue growth, sales strategy, customer acquisition",

        "legal":
            "Legal risks, regulations, compliance, contracts, policies",

        "risk":
            "Business risks, operational risks, security risks, uncertainty",

        "chro":
            "People, hiring, workforce, organizational impact",
    }

    # =========================================================
    # COMMON LLM TYPO ALIASES
    # =========================================================

    AGENT_ALIASES = {
        "fco": "cfo",
        "rpo": "cpo",
        "cfo": "cfo",
        "cmo": "cmo",
        "cto": "cto",
        "coo": "coo",
        "cso": "cso",
        "cpo": "cpo",
        "cro": "cro",
        "legal": "legal",
        "risk": "risk",
        "chro": "chro",
    }

    # =========================================================
    # DOMAIN KEYWORDS
    # =========================================================

    AGENT_KEYWORDS = {

        "cfo": [
            "finance",
            "financial",
            "cost",
            "costs",
            "budget",
            "profit",
            "profitability",
            "revenue",
            "investment",
            "roi",
            "cash flow",
            "cashflow",
            "funding",
            "expense",
            "expenses",
            "margin",
            "break even",
            "break-even",
            "payback",
        ],

        "cmo": [
            "market",
            "marketing",
            "customer",
            "customers",
            "competition",
            "competitor",
            "competitors",
            "brand",
            "branding",
            "advertising",
            "campaign",
            "positioning",
            "awareness",
            "demand",
            "market share",
        ],

        "cto": [
            "technology",
            "technical",
            "software",
            "system",
            "architecture",
            "engineering",
            "developer",
            "developers",
            "ai",
            "model",
            "machine learning",
            "ml",
            "api",
            "backend",
            "frontend",
            "cloud",
            "infrastructure",
            "latency",
            "response time",
            "performance",
            "scalability",
            "scale",
            "security",
            "cybersecurity",
            "deployment",
            "prototype",
        ],

        "coo": [
            "operation",
            "operations",
            "process",
            "processes",
            "execution",
            "delivery",
            "resource",
            "resources",
            "capacity",
            "workflow",
            "supply",
            "logistics",
            "implementation",
            "implementation plan",
        ],

        "cso": [
            "strategy",
            "strategic",
            "long term",
            "long-term",
            "growth strategy",
            "growth plan",
            "partnership",
            "partnerships",
            "expansion",
            "enterprise strategy",
            "business strategy",
            "competitive strategy",
        ],

        "cpo": [
            # Do NOT add generic "product" here.
            # Generic product references should not dominate
            # financial/technical/legal decisions.
            "feature",
            "features",
            "user experience",
            "ux",
            "ui",
            "product-market fit",
            "product market fit",
            "mvp",
            "roadmap",
            "usability",
            "customer experience",
            "requirements",
            "product strategy",
            "product design",
        ],

        "cro": [
            "sales",
            "selling",
            "revenue growth",
            "customer acquisition",
            "acquisition",
            "pipeline",
            "deal",
            "deals",
            "conversion",
            "sales growth",
            "retention",
            "upsell",
            "cross sell",
            "cross-sell",
        ],

        "legal": [
            "legal",
            "law",
            "laws",
            "regulation",
            "regulations",
            "regulatory",
            "compliance",
            "contract",
            "contracts",
            "license",
            "licensing",
            "privacy",
            "gdpr",
            "policy",
            "policies",
            "intellectual property",
            "patent",
        ],

        "risk": [
            "risk",
            "risks",
            "uncertainty",
            "uncertain",
            "threat",
            "threats",
            "failure",
            "fail",
            "fails",
            "failed",
            "failing",
            "problem",
            "problems",
            "issue",
            "issues",
            "severe",
            "critical",
            "vulnerability",
            "vulnerabilities",
            "security risk",
            "operational risk",
            "financial risk",
            "technical risk",
            "mitigation",
            "contingency",
            "exposure",
            "performance risk",
            "scalability risk",
        ],

        "chro": [
            "employee",
            "employees",
            "people",
            "workforce",
            "hiring",
            "hire",
            "staff",
            "staffing",
            "team",
            "teams",
            "skills",
            "training",
            "culture",
            "organization",
            "organizational",
            "hr",
            "human resources",
        ],
    }

    # =========================================================
    # FALLBACK
    # =========================================================

    FALLBACK_AGENTS = [
        "cfo",
        "cto",
        "risk",
    ]

    MAX_AGENTS = 6
    MIN_AGENTS = 2

    # =========================================================
    # CONSTRUCTOR
    # =========================================================

    def __init__(self, llm):

        self.llm = llm
        self.rule_selector = AgentSelector()

    # =========================================================
    # NORMALIZE TEXT
    # =========================================================

    @staticmethod
    def _normalize(text):

        text = str(text).lower()

        text = text.replace("-", " ")

        text = re.sub(
            r"[^a-z0-9\s]",
            " ",
            text
        )

        text = re.sub(
            r"\s+",
            " ",
            text
        )

        return text.strip()

    # =========================================================
    # BUILD PROMPT
    # =========================================================

    def _build_prompt(self, question):

        available = "\n".join(
            [
                f"- {name}: {description}"
                for name, description
                in self.AVAILABLE_AGENTS.items()
            ]
        )

        return f"""
You are the AI Boardroom Executive Selection System.

Select ONLY executives whose expertise is directly necessary
to answer the business question.

AVAILABLE EXECUTIVES:

{available}

BUSINESS QUESTION:

{question}

==================================================
SELECTION RULES
==================================================

1. Select only executives with a direct and material
   connection to the question.

2. Do not select executives merely because their domain
   could theoretically be useful.

3. Do not select an executive simply because this is
   a business decision.

4. Select Risk when there is meaningful:
   - risk
   - uncertainty
   - failure
   - security exposure
   - financial exposure
   - operational exposure
   - significant downside
   - severe problems

5. CTO is for:
   technology, software, AI, engineering, architecture,
   performance, scalability, infrastructure, APIs,
   and technical feasibility.

6. CPO is for:
   product strategy, features, roadmap, UX, usability,
   product-market fit, product requirements, and product design.

7. CHRO is for:
   employees, hiring, staffing, workforce, training,
   organizational development, and workplace culture.

8. CFO is for:
   costs, budget, revenue, profit, ROI, investment,
   funding, and expenses.

9. Legal is for:
   GDPR, compliance, regulations, contracts, privacy,
   licensing, and intellectual property.

10. CMO is for:
    market, marketing, competition, branding, and demand.

11. CRO is for:
    sales, customer acquisition, sales growth,
    conversion, and revenue growth.

12. COO is for:
    operations, execution, resources, processes,
    and delivery.

13. CSO is for:
    business strategy, long-term direction,
    partnerships, expansion, and strategic growth.

14. Select the smallest useful set.

15. Normally select 2 to 4 executives.

16. Never select more than 6.

==================================================
OUTPUT
==================================================

Return ONLY lowercase agent identifiers separated by commas.

Example:

cto,risk

Do not return explanations, reasoning, markdown,
confidence scores, or sentences.
"""

    # =========================================================
    # NORMALIZE RESPONSE
    # =========================================================

    def _normalize_response(self, response):

        if response is None:
            return ""

        return str(
            response
        ).lower().strip()

    # =========================================================
    # PARSE RESPONSE
    # =========================================================

    def _parse_agents(self, response):

        response = self._normalize_response(
            response
        )

        if not response:
            return []

        normalized = re.sub(
            r"[\[\]\(\)\{\}\"'`]",
            " ",
            response
        )

        normalized = normalized.replace(",", " ")
        normalized = normalized.replace("\n", " ")
        normalized = normalized.replace(";", " ")
        normalized = normalized.replace("|", " ")

        tokens = normalized.split()

        selected_agents = []

        for token in tokens:

            token = token.strip(
                ".,:;()[]{}\"'"
            )

            # Apply safe alias mapping.
            agent = self.AGENT_ALIASES.get(
                token
            )

            if agent is None:
                continue

            if agent not in selected_agents:

                selected_agents.append(
                    agent
                )

        return selected_agents[
            :self.MAX_AGENTS
        ]

    # =========================================================
    # QUESTION DOMAIN SCORES
    # =========================================================

    def _question_domain_scores(self, question):

        question = self._normalize(
            question
        )

        scores = {}

        for agent, keywords in (
            self.AGENT_KEYWORDS.items()
        ):

            score = 0

            for keyword in keywords:

                keyword = self._normalize(
                    keyword
                )

                if not keyword:
                    continue

                pattern = (
                    r"\b"
                    + re.escape(keyword)
                    + r"\b"
                )

                if re.search(
                    pattern,
                    question
                ):

                    if " " in keyword:
                        score += 2
                    else:
                        score += 1

            scores[agent] = score

        return scores

    # =========================================================
    # VALIDATE LLM SELECTION
    # =========================================================

    def _validate_selection(
        self,
        question,
        selected_agents
    ):

        if not selected_agents:
            return []

        normalized_question = self._normalize(
            question
        )

        scores = (
            self._question_domain_scores(
                question
            )
        )

        strongest_score = max(
            scores.values(),
            default=0
        )

        # If deterministic evidence is unavailable,
        # trust the parsed LLM result.
        if strongest_score == 0:

            return selected_agents[
                :self.MAX_AGENTS
            ]

        validated = []

        for agent in selected_agents:

            agent_score = scores.get(
                agent,
                0
            )

            # Direct domain evidence.
            if agent_score > 0:

                validated.append(
                    agent
                )

                continue

            # Risk has broader decision-level coverage.
            if agent == "risk":

                risk_signals = [
                    "risk",
                    "risks",
                    "uncertain",
                    "uncertainty",
                    "fail",
                    "fails",
                    "failed",
                    "failure",
                    "failing",
                    "problem",
                    "problems",
                    "issue",
                    "issues",
                    "severe",
                    "critical",
                    "security",
                    "exposure",
                    "threat",
                    "threats",
                    "vulnerability",
                    "vulnerabilities",
                    "performance",
                    "scalability",
                    "latency",
                    "response time",
                    "launch",
                    "decision",
                    "should we",
                ]

                if any(
                    signal in normalized_question
                    for signal in risk_signals
                ):

                    validated.append(
                        agent
                    )

        return list(
            dict.fromkeys(
                validated
            )
        )[:self.MAX_AGENTS]

    # =========================================================
    # RULE-BASED RECOVERY
    # =========================================================

    def _rule_recovery(self, question):

        print(
            "Running deterministic rule-based recovery..."
        )

        try:

            rule_result = (
                self.rule_selector.select_agents(
                    question
                )
            )

        except Exception as exc:

            print(
                "Rule recovery failed:",
                exc
            )

            return self.FALLBACK_AGENTS.copy()

        rule_agents = (
            rule_result.get(
                "agents",
                []
            )
        )

        rule_agents = [
            agent
            for agent in rule_agents
            if agent in self.AVAILABLE_AGENTS
        ]

        rule_agents = list(
            dict.fromkeys(
                rule_agents
            )
        )

        if len(rule_agents) >= self.MIN_AGENTS:

            print(
                "Rule recovery agents:",
                rule_agents
            )

            return rule_agents[
                :self.MAX_AGENTS
            ]

        if len(rule_agents) == 1:

            normalized_question = (
                self._normalize(
                    question
                )
            )

            risk_signals = [
                "risk",
                "uncertain",
                "uncertainty",
                "failure",
                "fail",
                "fails",
                "failed",
                "problem",
                "problems",
                "issue",
                "issues",
                "severe",
                "critical",
                "launch",
                "decision",
                "should",
            ]

            if any(
                signal in normalized_question
                for signal in risk_signals
            ):

                if "risk" not in rule_agents:

                    rule_agents.append(
                        "risk"
                    )

            if len(rule_agents) >= self.MIN_AGENTS:

                return rule_agents[
                    :self.MAX_AGENTS
                ]

        return self.FALLBACK_AGENTS.copy()

    # =========================================================
    # SELECT AGENTS
    # =========================================================

    def select_agents(self, question):

        if not question:

            return self.FALLBACK_AGENTS.copy()

        prompt = self._build_prompt(
            question
        )

        try:

            response = self.llm.generate(
                system_prompt=(
                    "You are a strict AI Boardroom "
                    "executive-selection system. "
                    "Return only valid lowercase "
                    "agent identifiers."
                ),
                user_prompt=prompt,
                max_new_tokens=80
            )

        except Exception as exc:

            print(
                "LLM Agent Selector error:",
                exc
            )

            return self._rule_recovery(
                question
            )

        print(
            "\nLLM Selector Response:"
        )

        print(
            response
        )

        selected_agents = (
            self._parse_agents(
                response
            )
        )

        print(
            "Parsed LLM Agents:",
            selected_agents
        )

        selected_agents = (
            self._validate_selection(
                question,
                selected_agents
            )
        )

        print(
            "Validated LLM Agents:",
            selected_agents
        )

        if len(selected_agents) < self.MIN_AGENTS:

            print(
                "LLM selection insufficient "
                "after validation."
            )

            selected_agents = (
                self._rule_recovery(
                    question
                )
            )

            print(
                "Recovered Agents:",
                selected_agents
            )

        selected_agents = [
            agent
            for agent in selected_agents
            if agent in self.AVAILABLE_AGENTS
        ]

        selected_agents = list(
            dict.fromkeys(
                selected_agents
            )
        )

        if not selected_agents:

            return self.FALLBACK_AGENTS.copy()

        return selected_agents[
            :self.MAX_AGENTS
        ]