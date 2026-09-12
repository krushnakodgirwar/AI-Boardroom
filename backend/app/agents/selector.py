"""
Rule-based Boardroom Agent Selector.

Uses weighted keyword evidence to select relevant executives.

Confidence is based on evidence quality and domain clarity,
not simply on the number of selected agents.
"""

import re


class AgentSelector:
    """
    Deterministic rule-based Boardroom agent selector.
    """

    # =========================================================
    # AGENT KEYWORDS
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

        "cpo": [
            "feature",
            "features",
            "user",
            "users",
            "user experience",
            "ux",
            "ui",
            "product-market fit",
            "product market fit",
            "mvp",
            "roadmap",
            "usability",
            "customer experience",
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
            "security risk",
            "operational risk",
            "financial risk",
            "technical risk",
            "mitigation",
            "contingency",
            "exposure",
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
    # BUSINESS DECISION TERMS
    # =========================================================

    CROSS_DOMAIN_TERMS = {
        "launch",
        "decision",
        "decide",
        "should we",
        "whether",
        "business decision",
    }

    # =========================================================
    # DEFAULT AGENTS
    # =========================================================

    DEFAULT_AGENTS = [
        "cfo",
        "cto",
        "risk",
    ]

    MAX_AGENTS = 6

    # =========================================================
    # NORMALIZE
    # =========================================================

    @staticmethod
    def _normalize(text):
        """
        Normalize text for reliable keyword matching.
        """

        text = str(text).lower()

        # Normalize hyphens.
        text = text.replace("-", " ")

        # Keep letters, numbers, currency symbol and spaces.
        text = re.sub(
            r"[^a-z0-9₹\s]",
            " ",
            text
        )

        # Collapse repeated spaces.
        text = re.sub(
            r"\s+",
            " ",
            text
        )

        return text.strip()

    # =========================================================
    # SCORE AGENT
    # =========================================================

    def _score_agent(
        self,
        question,
        keywords
    ):
        """
        Calculate relevance using word/phrase boundaries.

        Multi-word phrases receive stronger weight.

        Word boundaries prevent false matches such as:

            "ai" matching "training"
            "ml" matching unrelated words
        """

        score = 0
        matches = []

        for keyword in keywords:

            keyword = self._normalize(
                keyword
            )

            if not keyword:
                continue

            # -------------------------------------------------
            # Multi-word phrase
            # -------------------------------------------------

            if " " in keyword:

                pattern = (
                    r"\b"
                    + re.escape(keyword)
                    + r"\b"
                )

                if re.search(
                    pattern,
                    question
                ):

                    score += 2

                    matches.append(
                        keyword
                    )

            # -------------------------------------------------
            # Single word
            # -------------------------------------------------

            else:

                pattern = (
                    r"\b"
                    + re.escape(keyword)
                    + r"\b"
                )

                if re.search(
                    pattern,
                    question
                ):

                    score += 1

                    matches.append(
                        keyword
                    )

        return score, matches

    # =========================================================
    # SELECT AGENTS
    # =========================================================

    def select_agents(
        self,
        question
    ):
        """
        Select relevant executives.

        Returns:

            {
                "agents": [...],
                "confidence": float,
                "scores": {...},
                "matched_keywords": {...}
            }
        """

        # =====================================================
        # EMPTY QUESTION
        # =====================================================

        if not question:

            return {
                "agents": self.DEFAULT_AGENTS.copy(),
                "confidence": 0.0,
                "scores": {},
                "matched_keywords": {},
            }

        question = self._normalize(
            question
        )

        scores = {}
        matched_keywords = {}

        # =====================================================
        # SCORE ALL AGENTS
        # =====================================================

        for agent, keywords in (
            self.AGENT_KEYWORDS.items()
        ):

            score, matches = (
                self._score_agent(
                    question,
                    keywords
                )
            )

            scores[agent] = score

            matched_keywords[agent] = (
                matches
            )

        # =====================================================
        # DETECT BUSINESS DECISION
        #
        # IMPORTANT:
        # We DO NOT add points to Risk here.
        #
        # Risk can still be added to the final selection,
        # but it should not artificially increase confidence.
        # =====================================================

        has_decision_term = any(
            term in question
            for term in self.CROSS_DOMAIN_TERMS
        )

        # =====================================================
        # SELECT POSITIVE MATCHES
        # =====================================================

        selected = [
            agent
            for agent, score in scores.items()
            if score > 0
        ]

        # =====================================================
        # DEFAULT
        # =====================================================

        if not selected:

            selected = (
                self.DEFAULT_AGENTS.copy()
            )

        # =====================================================
        # SORT BY SCORE
        # =====================================================

        selected.sort(
            key=lambda agent: scores.get(
                agent,
                0
            ),
            reverse=True
        )

        # =====================================================
        # LIMIT AGENTS
        # =====================================================

        selected = selected[
            :self.MAX_AGENTS
        ]

        # =====================================================
        # ADD RISK FOR BUSINESS DECISIONS
        #
        # Risk is a supporting executive here.
        # It does NOT affect domain confidence.
        # =====================================================

        if (
            has_decision_term
            and "risk" not in selected
            and len(selected) < self.MAX_AGENTS
        ):

            selected.append(
                "risk"
            )

        # =====================================================
        # CONFIDENCE CALCULATION
        # =====================================================

        positive_scores = sorted(
            [
                score
                for score in scores.values()
                if score > 0
            ],
            reverse=True
        )

        if not positive_scores:

            confidence = 0.0

        else:

            strongest = (
                positive_scores[0]
            )

            second = (
                positive_scores[1]
                if len(positive_scores) > 1
                else 0
            )

            # -------------------------------------------------
            # STRONGEST DOMAIN
            # -------------------------------------------------

            strength_score = min(
                strongest / 4.0,
                1.0
            )

            # -------------------------------------------------
            # SEPARATION BETWEEN DOMAINS
            # -------------------------------------------------

            separation_score = min(
                max(
                    strongest - second,
                    0
                ) / 2.0,
                1.0
            )

            # -------------------------------------------------
            # DOMAIN COVERAGE
            # -------------------------------------------------

            matched_domain_count = len(
                [
                    score
                    for score in positive_scores
                    if score >= 2
                ]
            )

            coverage_score = min(
                matched_domain_count / 3.0,
                1.0
            )

            # -------------------------------------------------
            # BASE CONFIDENCE
            # -------------------------------------------------

            confidence = (
                0.50 * strength_score
                + 0.30 * separation_score
                + 0.20 * coverage_score
            )

            # -------------------------------------------------
            # BROAD SELECTION PENALTY
            # -------------------------------------------------

            if len(selected) >= 6:

                confidence *= 0.85

            # -------------------------------------------------
            # CLEAR SINGLE-DOMAIN CASE
            #
            # Example:
            #     GDPR -> Legal
            #
            # Risk may have been added because the question
            # contains "launch", but Risk should not reduce
            # confidence in Legal.
            # -------------------------------------------------

            if (
                strongest >= 1
                and strongest > second
                and len(
                    [
                        score
                        for score in positive_scores
                        if score > 0
                    ]
                ) == 1
            ):

                confidence = max(
                    confidence,
                    0.75
                )

            confidence = round(
                min(
                    max(
                        confidence,
                        0.0
                    ),
                    1.0
                ),
                2
            )

        # =====================================================
        # RETURN
        # =====================================================

        return {
            "agents": selected,
            "confidence": confidence,
            "scores": scores,
            "matched_keywords": matched_keywords,
        }