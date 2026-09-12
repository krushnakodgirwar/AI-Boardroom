"""
Deterministic mathematics engine for the AI Boardroom.

This module provides reusable mathematical and financial
calculations.

IMPORTANT:

    - No LLM is used for calculations.
    - Decimal arithmetic is used for financial values.
    - Results are deterministic and reproducible.
    - Missing values are never invented.
    - Revenue minus development cost is NOT automatically
      treated as accounting profit.
"""

from decimal import (
    Decimal,
    InvalidOperation,
    getcontext
)

from typing import Optional, Dict, Any

import sympy as sp


# ============================================================
# HIGH-PRECISION DECIMAL CONFIGURATION
# ============================================================

getcontext().prec = 28


class MathEngine:
    """
    Reusable deterministic mathematics engine for AI Boardroom.

    Responsibilities:

        - Exact decimal arithmetic
        - Financial calculations
        - Percentage calculations
        - Ratios
        - Comparisons
        - Basic equation solving through SymPy

    IMPORTANT:

        This class does NOT use an LLM.

        Numerical results are deterministic and reproducible.
    """

    # ========================================================
    # DECIMAL CONVERSION
    # ========================================================

    @staticmethod
    def decimal(
        value
    ) -> Optional[Decimal]:
        """
        Safely convert a value to Decimal.

        Returns None when conversion is impossible.
        """

        if value is None:
            return None

        try:
            return Decimal(str(value))

        except (
            InvalidOperation,
            ValueError,
            TypeError
        ):
            return None

    # ========================================================
    # BASIC ARITHMETIC
    # ========================================================

    @staticmethod
    def add(
        a,
        b
    ):

        a = MathEngine.decimal(a)
        b = MathEngine.decimal(b)

        if a is None or b is None:
            return None

        return a + b

    # --------------------------------------------------------

    @staticmethod
    def subtract(
        a,
        b
    ):

        a = MathEngine.decimal(a)
        b = MathEngine.decimal(b)

        if a is None or b is None:
            return None

        return a - b

    # --------------------------------------------------------

    @staticmethod
    def multiply(
        a,
        b
    ):

        a = MathEngine.decimal(a)
        b = MathEngine.decimal(b)

        if a is None or b is None:
            return None

        return a * b

    # --------------------------------------------------------

    @staticmethod
    def divide(
        a,
        b
    ):

        a = MathEngine.decimal(a)
        b = MathEngine.decimal(b)

        if a is None or b is None:
            return None

        if b == 0:
            return None

        return a / b

    # ========================================================
    # PERCENTAGE
    # ========================================================

    @staticmethod
    def percentage(
        value,
        total
    ):
        """
        Calculate:

            value / total * 100
        """

        value = MathEngine.decimal(value)
        total = MathEngine.decimal(total)

        if value is None or total is None:
            return None

        if total == 0:
            return None

        return (
            value / total
        ) * Decimal("100")

    # ========================================================
    # PROFIT
    # ========================================================

    @staticmethod
    def profit(
        revenue,
        total_cost
    ):
        """
        Calculate profit when the caller has explicitly
        established that total_cost represents the complete
        applicable cost basis.

        Formula:

            Profit = Revenue - Total Cost
        """

        return MathEngine.subtract(
            revenue,
            total_cost
        )

    # ========================================================
    # PROFIT MARGIN
    # ========================================================

    @staticmethod
    def profit_margin(
        revenue,
        profit=None,
        total_cost=None
    ):
        """
        Calculate profit margin.

        Formula:

            Profit Margin =
                Profit / Revenue × 100

        If profit is not supplied, total_cost may be used
        only when the caller explicitly intends total_cost
        to represent the complete profit cost basis.
        """

        revenue = MathEngine.decimal(revenue)

        if revenue is None or revenue == 0:
            return None

        if profit is None:

            if total_cost is None:
                return None

            profit = MathEngine.profit(
                revenue,
                total_cost
            )

        return MathEngine.percentage(
            profit,
            revenue
        )

    # ========================================================
    # ROI
    # ========================================================

    @staticmethod
    def roi(
        profit,
        investment
    ):
        """
        ROI = Profit / Investment × 100
        """

        return MathEngine.percentage(
            profit,
            investment
        )

    # ========================================================
    # BREAK-EVEN UNITS
    # ========================================================

    @staticmethod
    def break_even_units(
        fixed_cost,
        selling_price_per_unit,
        variable_cost_per_unit
    ):
        """
        Break-even Units =

            Fixed Cost /
            (Selling Price - Variable Cost)
        """

        contribution = MathEngine.subtract(
            selling_price_per_unit,
            variable_cost_per_unit
        )

        if contribution is None:
            return None

        if contribution <= 0:
            return None

        return MathEngine.divide(
            fixed_cost,
            contribution
        )

    # ========================================================
    # BREAK-EVEN REVENUE
    # ========================================================

    @staticmethod
    def break_even_revenue(
        fixed_cost,
        contribution_margin
    ):
        """
        Break-even Revenue =

            Fixed Cost / Contribution Margin

        contribution_margin must be supplied as a decimal.

        Example:

            40% -> 0.40
        """

        fixed_cost = MathEngine.decimal(
            fixed_cost
        )

        contribution_margin = MathEngine.decimal(
            contribution_margin
        )

        if (
            fixed_cost is None
            or contribution_margin is None
        ):
            return None

        if contribution_margin <= 0:
            return None

        return (
            fixed_cost /
            contribution_margin
        )

    # ========================================================
    # PAYBACK PERIOD
    # ========================================================

    @staticmethod
    def payback_period(
        investment,
        annual_cash_flow
    ):
        """
        Payback Period =

            Investment / Annual Cash Flow
        """

        investment = MathEngine.decimal(
            investment
        )

        annual_cash_flow = MathEngine.decimal(
            annual_cash_flow
        )

        if (
            investment is None
            or annual_cash_flow is None
        ):
            return None

        if annual_cash_flow <= 0:
            return None

        return (
            investment /
            annual_cash_flow
        )

    # ========================================================
    # COMPARISONS
    # ========================================================

    @staticmethod
    def compare(
        a,
        b
    ):
        """
        Deterministically compare two numbers.

        Returns:

            greater
            equal
            lower

        Returns None when either value is invalid.
        """

        a = MathEngine.decimal(a)
        b = MathEngine.decimal(b)

        if a is None or b is None:
            return None

        if a > b:
            return "greater"

        if a < b:
            return "lower"

        return "equal"

    # ========================================================
    # FINANCIAL ANALYSIS
    # ========================================================

    @staticmethod
    def financial_analysis(
        revenue=None,
        total_cost=None,
        investment=None,
        fixed_cost=None,
        selling_price_per_unit=None,
        variable_cost_per_unit=None,
        annual_cash_flow=None,
        contribution_margin=None
    ) -> Dict[str, Any]:
        """
        Perform deterministic financial calculations.

        IMPORTANT:

        Revenue - development cost is NOT automatically
        accounting profit.

        Therefore:

            revenue - total_cost

        is returned as:

            revenue_cost_difference

        and NOT as:

            profit

        Actual profit is calculated only when a sufficiently
        complete explicit cost basis is available.
        """

        results = {}

        # ====================================================
        # DECIMAL CONVERSION
        # ====================================================

        revenue = MathEngine.decimal(
            revenue
        )

        total_cost = MathEngine.decimal(
            total_cost
        )

        investment = MathEngine.decimal(
            investment
        )

        fixed_cost = MathEngine.decimal(
            fixed_cost
        )

        selling_price_per_unit = (
            MathEngine.decimal(
                selling_price_per_unit
            )
        )

        variable_cost_per_unit = (
            MathEngine.decimal(
                variable_cost_per_unit
            )
        )

        annual_cash_flow = (
            MathEngine.decimal(
                annual_cash_flow
            )
        )

        contribution_margin = (
            MathEngine.decimal(
                contribution_margin
            )
        )

        # ====================================================
        # REVENUE - DEVELOPMENT COST
        # ====================================================

        if (
            revenue is not None
            and total_cost is not None
        ):

            revenue_cost_difference = (
                MathEngine.subtract(
                    revenue,
                    total_cost
                )
            )

            results[
                "revenue_cost_difference"
            ] = revenue_cost_difference

            # ------------------------------------------------
            # DOES REVENUE COVER COST?
            # ------------------------------------------------

            results[
                "revenue_covers_cost"
            ] = (
                revenue >= total_cost
            )

        # ====================================================
        # ACTUAL PROFIT
        # ====================================================
        #
        # DO NOT calculate:
        #
        #     revenue - development_cost
        #
        # as accounting profit.
        #
        # We only calculate profit when there is an explicit
        # complete cost model:
        #
        #     Revenue
        #       - Fixed Cost
        #       - Variable Cost
        #
        # ====================================================

        profit = None

        if (
            revenue is not None
            and fixed_cost is not None
            and variable_cost_per_unit is not None
        ):

            profit = (
                revenue
                - fixed_cost
                - variable_cost_per_unit
            )

            results[
                "profit"
            ] = profit

        # ====================================================
        # ANNUAL CASH FLOW
        # ====================================================

        if annual_cash_flow is not None:

            results[
                "annual_cash_flow"
            ] = annual_cash_flow

        # ====================================================
        # PROFIT MARGIN
        # ====================================================

        if (
            revenue is not None
            and revenue != 0
            and profit is not None
        ):

            margin = (
                MathEngine.profit_margin(
                    revenue,
                    profit=profit
                )
            )

            if margin is not None:

                results[
                    "profit_margin_percent"
                ] = margin

        # ====================================================
        # ROI
        # ====================================================

        if (
            investment is not None
            and profit is not None
        ):

            roi = (
                MathEngine.roi(
                    profit,
                    investment
                )
            )

            if roi is not None:

                results[
                    "roi_percent"
                ] = roi

        # ====================================================
        # BREAK-EVEN UNITS
        # ====================================================

        if (
            fixed_cost is not None
            and selling_price_per_unit is not None
            and variable_cost_per_unit is not None
        ):

            units = (
                MathEngine.break_even_units(
                    fixed_cost,
                    selling_price_per_unit,
                    variable_cost_per_unit
                )
            )

            if units is not None:

                results[
                    "break_even_units"
                ] = units

        # ====================================================
        # BREAK-EVEN REVENUE
        # ====================================================

        if (
            fixed_cost is not None
            and contribution_margin is not None
        ):

            break_even_revenue = (
                MathEngine.break_even_revenue(
                    fixed_cost,
                    contribution_margin
                )
            )

            if break_even_revenue is not None:

                results[
                    "break_even_revenue"
                ] = break_even_revenue

        # ====================================================
        # PAYBACK PERIOD
        # ====================================================

        if (
            investment is not None
            and annual_cash_flow is not None
        ):

            payback = (
                MathEngine.payback_period(
                    investment,
                    annual_cash_flow
                )
            )

            if payback is not None:

                results[
                    "payback_period_years"
                ] = payback

        return results

    # ========================================================
    # SYMPY EQUATION SOLVER
    # ========================================================

    @staticmethod
    def solve_equation(
        equation,
        variable="x"
    ):
        """
        Solve a mathematical equation using SymPy.

        Example:

            MathEngine.solve_equation(
                "2*x + 10 = 30",
                "x"
            )

        Returns:

            [10]
        """

        try:

            symbol = sp.Symbol(
                variable
            )

            left, right = (
                equation.split("=")
            )

            expression = (
                sp.sympify(left)
                - sp.sympify(right)
            )

            solution = sp.solve(
                expression,
                symbol
            )

            return solution

        except Exception:

            return []

    # ========================================================
    # FORMAT DECIMAL
    # ========================================================

    @staticmethod
    def format_decimal(
        value,
        decimal_places=2
    ):
        """
        Format Decimal safely.
        """

        value = MathEngine.decimal(
            value
        )

        if value is None:
            return "N/A"

        return (
            f"{value:,.{decimal_places}f}"
        )