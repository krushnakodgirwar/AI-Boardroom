"""
Deterministic financial calculation utilities for the AI Boardroom CFO.

This module provides the CFO-facing financial calculation API.

All numerical calculations are delegated to the reusable
MathEngine so that financial arithmetic remains:

    - deterministic
    - reproducible
    - high precision
    - independent of the LLM

The calculator NEVER invents missing values.

The LLM must only interpret the results.
"""

from typing import Optional, Dict, Any

from backend.app.tools.math_engine import MathEngine


# ============================================================
# BASIC FINANCIAL CALCULATIONS
# ============================================================

def calculate_profit(
    revenue: float,
    total_cost: float
):
    """
    Calculate profit.

    Formula:

        Profit = Revenue - Total Cost
    """

    return MathEngine.profit(
        revenue,
        total_cost
    )


def calculate_profit_margin(
    revenue: float,
    profit: float
) -> Optional[float]:
    """
    Calculate profit margin as a percentage.

    Formula:

        Profit Margin = (Profit / Revenue) × 100
    """

    return MathEngine.profit_margin(
        revenue,
        profit=profit
    )


def calculate_roi(
    investment: float,
    profit: float
) -> Optional[float]:
    """
    Calculate ROI as a percentage.

    Formula:

        ROI = (Profit / Investment) × 100
    """

    return MathEngine.roi(
        profit,
        investment
    )


def calculate_break_even_units(
    fixed_cost: float,
    selling_price_per_unit: float,
    variable_cost_per_unit: float
) -> Optional[float]:
    """
    Calculate break-even units.

    Formula:

        Break-even Units =
            Fixed Cost /
            (Selling Price - Variable Cost)
    """

    return MathEngine.break_even_units(
        fixed_cost,
        selling_price_per_unit,
        variable_cost_per_unit
    )


def calculate_break_even_revenue(
    fixed_cost: float,
    contribution_margin: float
) -> Optional[float]:
    """
    Calculate break-even revenue.

    contribution_margin must be supplied as a decimal.

    Example:

        40% -> 0.40
    """

    return MathEngine.break_even_revenue(
        fixed_cost,
        contribution_margin
    )


def calculate_payback_period(
    investment: float,
    annual_cash_flow: float
) -> Optional[float]:
    """
    Calculate payback period in years.

    Formula:

        Payback Period =
            Investment / Annual Cash Flow
    """

    return MathEngine.payback_period(
        investment,
        annual_cash_flow
    )


# ============================================================
# COMPLETE FINANCIAL ANALYSIS
# ============================================================

def calculate_financial_metrics(
    revenue: Optional[float] = None,
    total_cost: Optional[float] = None,
    investment: Optional[float] = None,
    fixed_cost: Optional[float] = None,
    selling_price_per_unit: Optional[float] = None,
    variable_cost_per_unit: Optional[float] = None,
    annual_cash_flow: Optional[float] = None,
    contribution_margin: Optional[float] = None
) -> Dict[str, Any]:
    """
    Calculate every financial metric for which sufficient
    input data is available.

    Missing inputs are NOT guessed.

    MathEngine performs the actual arithmetic.
    """

    return MathEngine.financial_analysis(
        revenue=revenue,
        total_cost=total_cost,
        investment=investment,
        fixed_cost=fixed_cost,
        selling_price_per_unit=selling_price_per_unit,
        variable_cost_per_unit=variable_cost_per_unit,
        annual_cash_flow=annual_cash_flow,
        contribution_margin=contribution_margin
    )


# ============================================================
# FINANCIAL COMPARISON
# ============================================================

def compare_financial_values(
    first_value,
    second_value
):
    """
    Compare two financial values deterministically.

    Returns:

        "greater"
        "equal"
        "lower"

    Returns None if either value is invalid.
    """

    return MathEngine.compare(
        first_value,
        second_value
    )


# ============================================================
# FORMAT FINANCIAL METRICS
# ============================================================

def format_financial_metrics(
    metrics: Dict[str, Any]
) -> str:
    """
    Convert deterministic financial metrics into readable text.

    Formatting is performed outside the LLM.
    """

    if not metrics:

        return (
            "No financial calculations could be performed "
            "because the required financial inputs were "
            "not provided."
        )

    lines = [
        "DETERMINISTIC FINANCIAL CALCULATIONS:",
        ""
    ]

    # --------------------------------------------------------
    # PROFIT
    # --------------------------------------------------------

    if "profit" in metrics:

        lines.append(
            "- Profit: "
            + MathEngine.format_decimal(
                metrics["profit"]
            )
        )

    # --------------------------------------------------------
    # PROFIT MARGIN
    # --------------------------------------------------------

    if "profit_margin_percent" in metrics:

        lines.append(
            "- Profit Margin: "
            + MathEngine.format_decimal(
                metrics["profit_margin_percent"]
            )
            + "%"
        )

    # --------------------------------------------------------
    # ROI
    # --------------------------------------------------------

    if "roi_percent" in metrics:

        lines.append(
            "- ROI: "
            + MathEngine.format_decimal(
                metrics["roi_percent"]
            )
            + "%"
        )

    # --------------------------------------------------------
    # BREAK-EVEN UNITS
    # --------------------------------------------------------

    if "break_even_units" in metrics:

        lines.append(
            "- Break-even Units: "
            + MathEngine.format_decimal(
                metrics["break_even_units"]
            )
        )

    # --------------------------------------------------------
    # BREAK-EVEN REVENUE
    # --------------------------------------------------------

    if "break_even_revenue" in metrics:

        lines.append(
            "- Break-even Revenue: "
            + MathEngine.format_decimal(
                metrics["break_even_revenue"]
            )
        )

    # --------------------------------------------------------
    # PAYBACK PERIOD
    # --------------------------------------------------------

    if "payback_period_years" in metrics:

        lines.append(
            "- Payback Period: "
            + MathEngine.format_decimal(
                metrics["payback_period_years"]
            )
            + " years"
        )

    # --------------------------------------------------------
    # DETERMINISTIC WARNING
    # --------------------------------------------------------

    lines.extend([
        "",
        "IMPORTANT:",
        "These values were calculated deterministically",
        "by the Boardroom Math Engine.",
        "Do not recalculate them or invent additional "
        "financial values."
    ])

    return "\n".join(lines)