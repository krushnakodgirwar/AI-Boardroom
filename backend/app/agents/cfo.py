"""
CFO Agent for the AI Boardroom.

Architecture:

    User Question
          ↓
    Financial Extraction
          ↓
    Deterministic MathEngine
          ↓
    Verified Financial Facts
          ↓
    Deterministic Benefits / Risks
          ↓
    Qwen LLM Interpretation
          ↓
    CFO Analysis

IMPORTANT:

    The LLM must NOT perform financial arithmetic.

    Python/MathEngine is the numerical source of truth.

    Financial benefits and risks are also determined
    deterministically wherever possible.
"""

import re

from backend.app.agents.base_agent import BaseAgent
from backend.app.core.prompts import CFO_PROMPT

from backend.app.tools.financial_calculator import (
    calculate_financial_metrics,
)


class CFOAgent(BaseAgent):
    """
    Chief Financial Officer agent.

    Financial arithmetic is performed deterministically
    outside the LLM.

    The LLM is responsible for interpretation and
    recommendation only.
    """

    # =========================================================
    # CONSTRUCTOR
    # =========================================================

    def __init__(self, llm):

        super().__init__(
            role_name="CFO",
            role_prompt=CFO_PROMPT,
            llm=llm
        )

    # =========================================================
    # MONEY PARSING
    # =========================================================

    @staticmethod
    def _parse_indian_amount(
        value_text
    ):
        """
        Convert Indian financial notation to rupees.

        Examples:

            ₹10 lakh  -> 1000000
            ₹18 lakh  -> 1800000
            ₹2 crore  -> 20000000
            ₹5 million -> 5000000
        """

        if not value_text:
            return None

        text = (
            str(value_text)
            .lower()
            .strip()
        )

        text = text.replace(
            ",",
            ""
        )

        text = text.replace(
            "₹",
            ""
        )

        text = text.replace(
            "rs.",
            ""
        )

        text = text.replace(
            "rs",
            ""
        )

        match = re.search(
            r"(\d+(?:\.\d+)?)\s*"
            r"(crore|crores|cr|"
            r"lakh|lakhs|lac|lacs|"
            r"million|mn|"
            r"thousand|k)?",
            text
        )

        if not match:
            return None

        try:

            number = float(
                match.group(1)
            )

        except (
            ValueError,
            TypeError
        ):

            return None

        unit = match.group(2)

        if unit in (
            "crore",
            "crores",
            "cr"
        ):

            return (
                number *
                10_000_000
            )

        if unit in (
            "lakh",
            "lakhs",
            "lac",
            "lacs"
        ):

            return (
                number *
                100_000
            )

        if unit in (
            "million",
            "mn"
        ):

            return (
                number *
                1_000_000
            )

        if unit in (
            "thousand",
            "k"
        ):

            return (
                number *
                1_000
            )

        return number

    # =========================================================
    # EVIDENCE TEXT
    # =========================================================

    @staticmethod
    def _build_evidence_text(
        user_question,
        context=None,
        data=None
    ):
        """
        Combine all available evidence into a single
        extraction string.
        """

        parts = []

        # -----------------------------------------------------
        # USER QUESTION
        # -----------------------------------------------------

        if user_question:

            parts.append(
                "USER QUESTION:\n"
                + str(user_question)
            )

        # -----------------------------------------------------
        # CONTEXT
        # -----------------------------------------------------

        if context:

            if isinstance(
                context,
                (list, tuple)
            ):

                context_text = "\n".join(
                    str(item)
                    for item in context
                )

            elif isinstance(
                context,
                dict
            ):

                context_text = "\n".join(
                    f"{key}: {value}"
                    for key, value
                    in context.items()
                )

            else:

                context_text = str(
                    context
                )

            parts.append(
                "RETRIEVED DOCUMENT EVIDENCE:\n"
                + context_text
            )

        # -----------------------------------------------------
        # STRUCTURED DATA
        # -----------------------------------------------------

        if data:

            if isinstance(
                data,
                dict
            ):

                data_text = "\n".join(
                    f"{key}: {value}"
                    for key, value
                    in data.items()
                )

            else:

                data_text = str(
                    data
                )

            parts.append(
                "STRUCTURED DATA:\n"
                + data_text
            )

        return "\n\n".join(
            parts
        )

    # =========================================================
    # FINANCIAL INPUT EXTRACTION
    # =========================================================

    @classmethod
    def extract_financial_inputs(
        cls,
        user_question
    ):
        """
        Extract explicit financial values from text.

        No values are invented.
        """

        if not user_question:
            return {}

        text = str(
            user_question
        )

        extracted = {}

        # =====================================================
        # DEVELOPMENT COST
        # =====================================================

        development_patterns = [

            r"(?:development\s+cost)"
            r"(?:\s+is|\s+of)?\s*[:\-]?\s*"
            r"(₹?\s*[\d,.]+\s*"
            r"(?:lakh|lakhs|lac|lacs|"
            r"crore|crores|cr|"
            r"million|mn|thousand|k)?)"
        ]

        for pattern in development_patterns:

            match = re.search(
                pattern,
                text,
                flags=re.IGNORECASE
            )

            if match:

                value = (
                    cls._parse_indian_amount(
                        match.group(1)
                    )
                )

                if value is not None:

                    extracted[
                        "total_cost"
                    ] = value

                break

        # =====================================================
        # EXPECTED REVENUE
        # =====================================================

        revenue_patterns = [

            r"(?:expected\s+first[-\s]?year\s+revenue)"
            r"(?:\s+is|\s+of)?\s*[:\-]?\s*"
            r"(₹?\s*[\d,.]+\s*"
            r"(?:lakh|lakhs|lac|lacs|"
            r"crore|crores|cr|"
            r"million|mn|thousand|k)?)",

            r"(?:expected\s+revenue)"
            r"(?:\s+is|\s+of)?\s*[:\-]?\s*"
            r"(₹?\s*[\d,.]+\s*"
            r"(?:lakh|lakhs|lac|lacs|"
            r"crore|crores|cr|"
            r"million|mn|thousand|k)?)",

            r"(?:first[-\s]?year\s+revenue)"
            r"(?:\s+is|\s+of)?\s*[:\-]?\s*"
            r"(₹?\s*[\d,.]+\s*"
            r"(?:lakh|lakhs|lac|lacs|"
            r"crore|crores|cr|"
            r"million|mn|thousand|k)?)",

            r"(?:revenue)"
            r"(?:\s+is|\s+of)?\s*[:\-]?\s*"
            r"(₹?\s*[\d,.]+\s*"
            r"(?:lakh|lakhs|lac|lacs|"
            r"crore|crores|cr|"
            r"million|mn|thousand|k)?)"
        ]

        for pattern in revenue_patterns:

            match = re.search(
                pattern,
                text,
                flags=re.IGNORECASE
            )

            if match:

                value = (
                    cls._parse_indian_amount(
                        match.group(1)
                    )
                )

                if value is not None:

                    extracted[
                        "revenue"
                    ] = value

                break

        # =====================================================
        # INVESTMENT
        # =====================================================

        investment_patterns = [

            r"(?:initial\s+investment)"
            r"(?:\s+is|\s+of)?\s*[:\-]?\s*"
            r"(₹?\s*[\d,.]+\s*"
            r"(?:lakh|lakhs|lac|lacs|"
            r"crore|crores|cr|"
            r"million|mn|thousand|k)?)",

            r"(?:investment)"
            r"(?:\s+is|\s+of)?\s*[:\-]?\s*"
            r"(₹?\s*[\d,.]+\s*"
            r"(?:lakh|lakhs|lac|lacs|"
            r"crore|crores|cr|"
            r"million|mn|thousand|k)?)"
        ]

        for pattern in investment_patterns:

            match = re.search(
                pattern,
                text,
                flags=re.IGNORECASE
            )

            if match:

                value = (
                    cls._parse_indian_amount(
                        match.group(1)
                    )
                )

                if value is not None:

                    extracted[
                        "investment"
                    ] = value

                break

        # =====================================================
        # AVAILABLE BUDGET
        # =====================================================

        budget_patterns = [

            r"(?:available\s+budget)"
            r"(?:\s+is|\s+of)?\s*[:\-]?\s*"
            r"(₹?\s*[\d,.]+\s*"
            r"(?:lakh|lakhs|lac|lacs|"
            r"crore|crores|cr|"
            r"million|mn|thousand|k)?)",

            r"(?:budget)"
            r"(?:\s+is|\s+of)?\s*[:\-]?\s*"
            r"(₹?\s*[\d,.]+\s*"
            r"(?:lakh|lakhs|lac|lacs|"
            r"crore|crores|cr|"
            r"million|mn|thousand|k)?)"
        ]

        for pattern in budget_patterns:

            match = re.search(
                pattern,
                text,
                flags=re.IGNORECASE
            )

            if match:

                value = (
                    cls._parse_indian_amount(
                        match.group(1)
                    )
                )

                if value is not None:

                    extracted[
                        "available_budget"
                    ] = value

                break

        return extracted

    # =========================================================
    # FINANCIAL CALCULATIONS
    # =========================================================

    @staticmethod
    def calculate_financials(
        data=None
    ):
        """
        Delegate all numerical calculations to MathEngine
        through financial_calculator.py.
        """

        if not isinstance(
            data,
            dict
        ):

            return {}

        return calculate_financial_metrics(

            revenue=data.get(
                "revenue"
            ),

            total_cost=data.get(
                "total_cost"
            ),

            investment=data.get(
                "investment"
            ),

            fixed_cost=data.get(
                "fixed_cost"
            ),

            selling_price_per_unit=data.get(
                "selling_price_per_unit"
            ),

            variable_cost_per_unit=data.get(
                "variable_cost_per_unit"
            ),

            annual_cash_flow=data.get(
                "annual_cash_flow"
            ),

            contribution_margin=data.get(
                "contribution_margin"
            )
        )

    # =========================================================
    # MONEY FORMAT
    # =========================================================

    @staticmethod
    def _format_money(
        value
    ):
        """
        Format rupee values for readable CFO output.
        """

        if value is None:
            return "Not available"

        try:

            value = float(
                value
            )

        except (
            ValueError,
            TypeError
        ):

            return "Not available"

        # -----------------------------------------------------
        # CRORE
        # -----------------------------------------------------

        if abs(value) >= 10_000_000:

            crore = (
                value /
                10_000_000
            )

            if crore.is_integer():

                return (
                    f"₹{int(crore)} crore"
                )

            return (
                f"₹{crore:.2f} crore"
            )

        # -----------------------------------------------------
        # LAKH
        # -----------------------------------------------------

        if abs(value) >= 100_000:

            lakh = (
                value /
                100_000
            )

            if lakh.is_integer():

                return (
                    f"₹{int(lakh)} lakh"
                )

            return (
                f"₹{lakh:.2f} lakh"
            )

        # -----------------------------------------------------
        # NORMAL RUPEES
        # -----------------------------------------------------

        return (
            f"₹{value:,.2f}"
        )

    # =========================================================
    # FINANCIAL FACTS
    # =========================================================

    @classmethod
    def build_financial_facts(
        cls,
        inputs,
        metrics
    ):
        """
        Build authoritative financial facts.
        """

        facts = []

        budget = inputs.get(
            "available_budget"
        )

        revenue = inputs.get(
            "revenue"
        )

        cost = inputs.get(
            "total_cost"
        )

        investment = inputs.get(
            "investment"
        )

        # -----------------------------------------------------
        # BASIC INPUTS
        # -----------------------------------------------------

        if budget is not None:

            facts.append(
                "Available Budget: "
                + cls._format_money(
                    budget
                )
            )

        if cost is not None:

            facts.append(
                "Development Cost: "
                + cls._format_money(
                    cost
                )
            )

        if revenue is not None:

            facts.append(
                "Expected Revenue: "
                + cls._format_money(
                    revenue
                )
            )

        if investment is not None:

            facts.append(
                "Investment: "
                + cls._format_money(
                    investment
                )
            )

        # -----------------------------------------------------
        # REVENUE-COST DIFFERENCE
        # -----------------------------------------------------

        if (
            "revenue_cost_difference"
            in metrics
        ):

            difference = metrics[
                "revenue_cost_difference"
            ]

            facts.append(
                "Revenue-Cost Difference: "
                + cls._format_money(
                    difference
                )
            )

        # -----------------------------------------------------
        # BUDGET-COST DIFFERENCE
        # -----------------------------------------------------

        if (
            budget is not None
            and cost is not None
        ):

            difference = (
                budget -
                cost
            )

            facts.append(
                "Available Budget Difference: "
                + cls._format_money(
                    difference
                )
            )

        # -----------------------------------------------------
        # ACTUAL PROFIT
        # -----------------------------------------------------

        if "profit" in metrics:

            facts.append(
                "Calculated Profit: "
                + cls._format_money(
                    metrics[
                        "profit"
                    ]
                )
            )

        else:

            facts.append(
                "Actual Profit: "
                "Not established from the available information."
            )

        # -----------------------------------------------------
        # PROFIT MARGIN
        # -----------------------------------------------------

        if (
            "profit_margin_percent"
            in metrics
        ):

            facts.append(
                "Profit Margin: "
                + f"{float(metrics['profit_margin_percent']):.2f}%"
            )

        else:

            facts.append(
                "Profit Margin: "
                "Not established from the available information."
            )

        # -----------------------------------------------------
        # ROI
        # -----------------------------------------------------

        if "roi_percent" in metrics:

            facts.append(
                "ROI: "
                + f"{float(metrics['roi_percent']):.2f}%"
            )

        else:

            facts.append(
                "ROI: "
                "Not calculable because an explicit investment "
                "and complete profit basis are unavailable."
            )

        # -----------------------------------------------------
        # BREAK-EVEN UNITS
        # -----------------------------------------------------

        if "break_even_units" in metrics:

            facts.append(
                "Break-even Units: "
                + f"{float(metrics['break_even_units']):.2f}"
            )

        # -----------------------------------------------------
        # BREAK-EVEN REVENUE
        # -----------------------------------------------------

        if "break_even_revenue" in metrics:

            facts.append(
                "Break-even Revenue: "
                + cls._format_money(
                    metrics[
                        "break_even_revenue"
                    ]
                )
            )

        # -----------------------------------------------------
        # PAYBACK PERIOD
        # -----------------------------------------------------

        if (
            "payback_period_years"
            in metrics
        ):

            facts.append(
                "Payback Period: "
                + f"{float(metrics['payback_period_years']):.2f} years"
            )

        return facts

    # =========================================================
    # DETERMINISTIC RELATIONSHIPS
    # =========================================================

    @staticmethod
    def determine_relationships(
        inputs,
        metrics
    ):
        """
        Determine all important financial relationships
        deterministically.
        """

        relationships = []

        revenue = inputs.get(
            "revenue"
        )

        cost = inputs.get(
            "total_cost"
        )

        budget = inputs.get(
            "available_budget"
        )

        # =====================================================
        # REVENUE VS COST
        # =====================================================

        if (
            revenue is not None
            and cost is not None
        ):

            difference = (
                revenue -
                cost
            )

            if revenue > cost:

                relationships.append(
                    "Expected revenue is ABOVE development "
                    "cost by "
                    + CFOAgent._format_money(
                        difference
                    )
                    + "."
                )

            elif revenue == cost:

                relationships.append(
                    "Expected revenue is EQUAL TO development "
                    "cost."
                )

            else:

                relationships.append(
                    "Expected revenue is BELOW development "
                    "cost by "
                    + CFOAgent._format_money(
                        abs(difference)
                    )
                    + "."
                )

        # =====================================================
        # BUDGET VS COST
        # =====================================================

        if (
            budget is not None
            and cost is not None
        ):

            difference = (
                budget -
                cost
            )

            if budget > cost:

                relationships.append(
                    "Available budget is ABOVE development "
                    "cost by "
                    + CFOAgent._format_money(
                        difference
                    )
                    + "."
                )

            elif budget == cost:

                relationships.append(
                    "Available budget is EQUAL TO development "
                    "cost."
                )

            else:

                relationships.append(
                    "Available budget is BELOW development "
                    "cost by "
                    + CFOAgent._format_money(
                        abs(difference)
                    )
                    + "."
                )

        # =====================================================
        # PROFIT
        # =====================================================

        if "profit" in metrics:

            profit = metrics[
                "profit"
            ]

            if profit > 0:

                relationships.append(
                    "Calculated profit is positive based on "
                    "the explicitly provided complete cost basis."
                )

            elif profit == 0:

                relationships.append(
                    "Calculated profit is zero based on "
                    "the explicitly provided complete cost basis."
                )

            else:

                relationships.append(
                    "Calculated profit is negative based on "
                    "the explicitly provided complete cost basis."
                )

        else:

            relationships.append(
                "Actual profit cannot be established because "
                "a complete profit cost basis is unavailable."
            )

        # =====================================================
        # ROI
        # =====================================================

        if "roi_percent" in metrics:

            relationships.append(
                "ROI is calculable from the explicitly "
                "provided investment and profit basis."
            )

        else:

            relationships.append(
                "ROI cannot be calculated because an explicit "
                "investment and complete profit basis are unavailable."
            )

        return relationships

    # =========================================================
    # DETERMINISTIC BENEFITS AND RISKS
    # =========================================================

    @classmethod
    def determine_benefits_and_risks(
        cls,
        inputs,
        metrics
    ):
        """
        Determine benefits and risks without using the LLM.

        This prevents Qwen from placing negative financial
        conditions under FINANCIAL BENEFITS.
        """

        benefits = []

        risks = []

        revenue = inputs.get(
            "revenue"
        )

        cost = inputs.get(
            "total_cost"
        )

        budget = inputs.get(
            "available_budget"
        )

        # =====================================================
        # REVENUE VS COST
        # =====================================================

        if (
            revenue is not None
            and cost is not None
        ):

            if revenue > cost:

                benefits.append(
                    "Expected revenue is above development "
                    "cost by "
                    + cls._format_money(
                        revenue - cost
                    )
                    + "."
                )

            elif revenue < cost:

                risks.append(
                    "Expected revenue is below development "
                    "cost by "
                    + cls._format_money(
                        cost - revenue
                    )
                    + "."
                )

        # =====================================================
        # BUDGET VS COST
        # =====================================================

        if (
            budget is not None
            and cost is not None
        ):

            if budget > cost:

                benefits.append(
                    "Available budget exceeds development "
                    "cost by "
                    + cls._format_money(
                        budget - cost
                    )
                    + "."
                )

            elif budget < cost:

                risks.append(
                    "Available budget is below development "
                    "cost by "
                    + cls._format_money(
                        cost - budget
                    )
                    + "."
                )

        # =====================================================
        # ACTUAL PROFIT
        # =====================================================

        if "profit" in metrics:

            profit = metrics[
                "profit"
            ]

            if profit > 0:

                benefits.append(
                    "The explicitly calculated profit is positive."
                )

            elif profit == 0:

                risks.append(
                    "The explicitly calculated profit is zero."
                )

            else:

                risks.append(
                    "The explicitly calculated profit is negative."
                )

        else:

            risks.append(
                "Actual profit cannot be established because "
                "a complete profit cost basis is unavailable."
            )

        # =====================================================
        # ROI
        # =====================================================

        if "roi_percent" in metrics:

            roi = metrics[
                "roi_percent"
            ]

            if roi > 0:

                benefits.append(
                    "The calculated ROI is positive."
                )

            elif roi == 0:

                risks.append(
                    "The calculated ROI is zero."
                )

            else:

                risks.append(
                    "The calculated ROI is negative."
                )

        return (
            benefits,
            risks
        )

    # =========================================================
    # MISSING INFORMATION
    # =========================================================

    @staticmethod
    def determine_missing_information(
        inputs
    ):
        """
        Identify genuinely missing information.

        Derived metrics such as profit margin are NOT
        treated as missing inputs.
        """

        missing = []

        if "investment" not in inputs:

            missing.append(
                "Investment amount is not provided, "
                "so ROI cannot be calculated."
            )

        if "revenue" not in inputs:

            missing.append(
                "Expected revenue is not provided."
            )

        if "total_cost" not in inputs:

            missing.append(
                "Development or total cost is not provided."
            )

        if "available_budget" not in inputs:

            missing.append(
                "Available budget is not provided."
            )

        # Operating costs are useful for a complete
        # profitability assessment.

        missing.append(
            "Ongoing operating costs are not provided."
        )

        return missing

    # =========================================================
    # BUILD INTERPRETATION CONTEXT
    # =========================================================

    @classmethod
    def build_interpretation_context(
        cls,
        inputs,
        metrics
    ):
        """
        Build authoritative CFO context.

        Python determines:

            - Facts
            - Relationships
            - Benefits
            - Risks
            - Missing information

        Qwen only interprets them.
        """

        relationships = (
            cls.determine_relationships(
                inputs,
                metrics
            )
        )

        benefits, risks = (
            cls.determine_benefits_and_risks(
                inputs,
                metrics
            )
        )

        missing = (
            cls.determine_missing_information(
                inputs
            )
        )

        facts = (
            cls.build_financial_facts(
                inputs,
                metrics
            )
        )

        lines = [

            "CFO DETERMINISTIC ANALYSIS",

            "==========================",

            "",

            "Python has performed all financial arithmetic.",

            "The following information is authoritative.",

            "The LLM must interpret it without recalculating it.",

            "",

            "AUTHORITATIVE FINANCIAL FACTS:",
        ]

        # =====================================================
        # FACTS
        # =====================================================

        if facts:

            for fact in facts:

                lines.append(
                    "- " + fact
                )

        else:

            lines.append(
                "- No financial facts could be calculated."
            )

        # =====================================================
        # RELATIONSHIPS
        # =====================================================

        lines.extend([

            "",

            "AUTHORITATIVE FINANCIAL RELATIONSHIPS:",
        ])

        if relationships:

            for relationship in relationships:

                lines.append(
                    "- " + relationship
                )

        else:

            lines.append(
                "- No financial relationships available."
            )

        # =====================================================
        # BENEFITS
        # =====================================================

        lines.extend([

            "",

            "AUTHORITATIVE FINANCIAL BENEFITS:",
        ])

        if benefits:

            for benefit in benefits:

                lines.append(
                    "- " + benefit
                )

        else:

            lines.append(
                "- No material financial benefits established."
            )

        # =====================================================
        # RISKS
        # =====================================================

        lines.extend([

            "",

            "AUTHORITATIVE FINANCIAL RISKS:",
        ])

        if risks:

            for risk in risks:

                lines.append(
                    "- " + risk
                )

        else:

            lines.append(
                "- No material financial risks established."
            )

        # =====================================================
        # MISSING INFORMATION
        # =====================================================

        lines.extend([

            "",

            "GENUINELY MISSING INFORMATION:",
        ])

        if missing:

            for item in missing:

                lines.append(
                    "- " + item
                )

        else:

            lines.append(
                "- No additional financial information identified as missing."
            )

        # =====================================================
        # STRICT RULES
        # =====================================================

        lines.extend([

            "",

            "============================================================",

            "STRICT CFO RULES",

            "============================================================",

            "",

            "1. Python is the numerical source of truth.",

            "",

            "2. Do not perform financial arithmetic.",

            "",

            "3. Do not recalculate or change any Python value.",

            "",

            "4. Do not reverse any comparison.",

            "",

            "5. Revenue minus development cost is NOT automatically",

            "   accounting profit.",

            "",

            "6. Do not report profit margin unless Python calculated it.",

            "",

            "7. Do not report ROI unless Python calculated it.",

            "",

            "8. Do not invent financial information.",

            "",

            "9. Do not describe a risk as a financial benefit.",

            "",

            "10. Do not describe a financial benefit as a risk.",

            "",

            "11. Use AUTHORITATIVE FINANCIAL BENEFITS exactly.",

            "",

            "12. Use AUTHORITATIVE FINANCIAL RISKS exactly.",

            "",

            "13. Do not move information between Benefits and Risks.",

            "",

            "14. Do not report a negative financial condition as a benefit.",

            "",

            "15. Do not report a positive financial condition as a risk.",

            "",

            "16. Do not output STOP.",

            "",

            "============================================================",

            "END OF AUTHORITATIVE CFO DATA",

            "============================================================",
        ])

        return "\n".join(
            lines
        )

    # =========================================================
    # ANALYZE
    # =========================================================

    def analyze(
        self,
        user_question,
        context=None,
        data=None,
        agent_analyses=None,
        max_new_tokens=400
    ):
        """
        Execute complete CFO analysis.
        """

        # =====================================================
        # STRUCTURED DATA
        # =====================================================

        if isinstance(
            data,
            dict
        ):

            enhanced_data = {
                **data
            }

        elif data is None:

            enhanced_data = {}

        else:

            enhanced_data = {
                "original_data":
                str(data)
            }

        # =====================================================
        # EVIDENCE
        # =====================================================

        evidence_text = (
            self._build_evidence_text(
                user_question=user_question,
                context=context,
                data=enhanced_data
            )
        )

        # =====================================================
        # EXTRACTION
        # =====================================================

        print(
            "\nCFO: Extracting financial values from "
            "question + document evidence..."
        )

        extracted = (
            self.extract_financial_inputs(
                evidence_text
            )
        )

        print(
            "CFO: Extracted financial inputs: "
            f"{extracted}"
        )

        # =====================================================
        # MERGE EXTRACTED VALUES
        # =====================================================

        for key, value in extracted.items():

            if key not in enhanced_data:

                enhanced_data[
                    key
                ] = value

        # =====================================================
        # DETERMINISTIC CALCULATIONS
        # =====================================================

        metrics = (
            self.calculate_financials(
                enhanced_data
            )
        )

        print(
            "CFO: Deterministic financial metrics:"
        )

        print(
            metrics
        )

        # =====================================================
        # DETERMINISTIC CONTEXT
        # =====================================================

        financial_context = (
            self.build_interpretation_context(
                enhanced_data,
                metrics
            )
        )

        # =====================================================
        # SYSTEM PROMPT
        # =====================================================

        system_prompt = f"""
{CFO_PROMPT}

============================================================
AUTHORITATIVE CFO FINANCIAL DATA
============================================================

{financial_context}

============================================================
CRITICAL INSTRUCTIONS
============================================================

The AUTHORITATIVE CFO FINANCIAL DATA above is generated by
Python and is the numerical source of truth.

You are NOT allowed to perform financial arithmetic.

You are NOT allowed to reverse, reinterpret, or recalculate
the numerical relationships.

If Python says:

"Expected revenue is BELOW development cost by ₹6 lakh."

you MUST NOT say:

"Expected revenue exceeds development cost by ₹6 lakh."

If Python says:

"Available budget is BELOW development cost by ₹8 lakh."

you MUST preserve that direction.

============================================================
PROFIT RULE
============================================================

Revenue minus development cost is NOT automatically accounting
profit.

Do not call the revenue-cost difference "profit".

Only discuss calculated profit when Python explicitly provides
a calculated profit.

============================================================
ROI RULE
============================================================

Do not calculate ROI yourself.

Only report ROI when Python explicitly calculated it.

============================================================
BENEFITS RULE
============================================================

Use ONLY the items listed under:

AUTHORITATIVE FINANCIAL BENEFITS

Do not invent additional benefits.

Do not move risks into the Benefits section.

============================================================
RISKS RULE
============================================================

Use ONLY the items listed under:

AUTHORITATIVE FINANCIAL RISKS

Do not invent additional risks.

Do not move benefits into the Risks section.

============================================================
MISSING INFORMATION RULE
============================================================

Only identify information that is genuinely unavailable.

Do not list derived metrics such as profit margin as missing
inputs.

============================================================
ROLE
============================================================

You are the CFO.

Provide financial analysis.

Do not make the final company-wide decision.

Do not output STOP.

============================================================
OUTPUT FORMAT
============================================================

FINANCIAL ASSESSMENT:

Choose exactly one:

ATTRACTIVE
UNCERTAIN
RISKY

KEY FINANCIAL FACTORS:

Provide up to 3 concise points.

Use authoritative facts and relationships.

FINANCIAL BENEFITS:

Use ONLY authoritative financial benefits.

If none exist, say:

"No material financial benefits established."

FINANCIAL RISKS:

Use ONLY authoritative financial risks.

If none exist, say:

"No material financial risks established."

MISSING FINANCIAL INFORMATION:

Use only genuinely missing information.

CFO RECOMMENDATION:

Provide 1-2 complete sentences.

CONFIDENCE:

Choose exactly one:

HIGH
MEDIUM
LOW

Complete every section.
"""

        # =====================================================
        # USER PROMPT
        # =====================================================

        user_prompt = f"""
BUSINESS DECISION:

{user_question}

============================================================
AUTHORITATIVE CFO DATA
============================================================

{financial_context}

============================================================
OTHER EXECUTIVE ANALYSES
============================================================

{
    str(agent_analyses)[:5000]
    if agent_analyses
    else "None available."
}

============================================================
TASK
============================================================

Interpret the AUTHORITATIVE CFO DATA.

Do not perform arithmetic.

Do not recalculate any number.

Do not reverse any comparison.

Do not contradict authoritative relationships.

Do not move benefits into risks.

Do not move risks into benefits.

The authoritative Python calculations have priority over
any numerical claim made by another executive.

Return only the CFO analysis.
"""

        # =====================================================
        # GENERATE
        # =====================================================

        response = self.llm.generate(

            system_prompt=system_prompt,

            user_prompt=user_prompt,

            max_new_tokens=max_new_tokens
        )

        response = (
            response
            .strip()
        )

        # =====================================================
        # REMOVE STOP
        # =====================================================

        response = re.sub(
            r"\s*STOP\.?\s*$",
            "",
            response,
            flags=re.IGNORECASE
        ).strip()

        # =====================================================
        # FINAL DETERMINISTIC FACTS
        # =====================================================

        financial_facts = (
            self.build_financial_facts(
                enhanced_data,
                metrics
            )
        )

        # =====================================================
        # FINAL OUTPUT
        # =====================================================

        final_output = [

            "FINANCIAL FACTS",

            "===============",
        ]

        if financial_facts:

            for fact in financial_facts:

                final_output.append(
                    "- " + fact
                )

        else:

            final_output.append(
                "- No deterministic financial facts available."
            )

        final_output.append("")

        final_output.append(
            response
        )

        return "\n".join(
            final_output
        ).strip()