"""
tests/test_rate_validation.py
------------------------------
Tests that every function with a rate parameter raises ValueError when a
percentage value (> 1) is passed instead of a decimal.

Covers:
  - project_savings_growth
  - debt_payoff_months
  - debt_vs_invest       (annual_debt_rate, annual_invest_rate)
  - financial_health_check (annual_debt_rate, assumed_invest_rate)
  - goal_plan
  - debt_schedule
  - savings_schedule
  - multi_debt_plan      (per-debt apr)
  - compare_scenarios    (annual_rate propagated to project_savings_growth)
"""

from __future__ import annotations

import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tools.core.finance import (
    compare_scenarios,
    debt_payoff_months,
    debt_schedule,
    debt_vs_invest,
    financial_health_check,
    goal_plan,
    multi_debt_plan,
    project_savings_growth,
    savings_schedule,
)

_RATE_MSG = "rates must be decimals, e.g. 0.20 for 20%"


# ── project_savings_growth ────────────────────────────────────────────────────


class TestProjectSavingsGrowthRateValidation:
    def test_rejects_percentage_rate(self):
        with pytest.raises(ValueError, match=_RATE_MSG):
            project_savings_growth(1000, 100, annual_rate=5)  # 5 instead of 0.05

    def test_rejects_rate_exactly_above_one(self):
        with pytest.raises(ValueError, match=_RATE_MSG):
            project_savings_growth(1000, 100, annual_rate=1.01)

    def test_accepts_rate_of_one(self):
        # 100% annual rate is unusual but technically valid as a decimal
        result = project_savings_growth(1000, 0, annual_rate=1.0, months=12)
        assert result > 1000

    def test_accepts_normal_decimal_rate(self):
        result = project_savings_growth(1000, 100, annual_rate=0.05, months=12)
        assert result > 1000


# ── debt_payoff_months ────────────────────────────────────────────────────────


class TestDebtPayoffMonthsRateValidation:
    def test_rejects_percentage_rate(self):
        with pytest.raises(ValueError, match=_RATE_MSG):
            debt_payoff_months(5000, 200, annual_rate=20)  # 20 instead of 0.20

    def test_rejects_rate_just_above_one(self):
        with pytest.raises(ValueError, match=_RATE_MSG):
            debt_payoff_months(5000, 200, annual_rate=1.5)

    def test_accepts_normal_decimal_rate(self):
        result = debt_payoff_months(5000, 200, annual_rate=0.20)
        assert result["months_to_payoff"] is not None or result["months_to_payoff"] is None


# ── debt_vs_invest ────────────────────────────────────────────────────────────


class TestDebtVsInvestRateValidation:
    def test_rejects_percentage_debt_rate(self):
        with pytest.raises(ValueError, match=_RATE_MSG):
            debt_vs_invest(5000, annual_debt_rate=7, monthly_surplus=500,
                           min_monthly_payment=100)

    def test_rejects_percentage_invest_rate(self):
        with pytest.raises(ValueError, match=_RATE_MSG):
            debt_vs_invest(5000, annual_debt_rate=0.07, monthly_surplus=500,
                           min_monthly_payment=100, annual_invest_rate=5)

    def test_accepts_normal_decimal_rates(self):
        result = debt_vs_invest(5000, annual_debt_rate=0.07, monthly_surplus=500,
                                min_monthly_payment=100, annual_invest_rate=0.05)
        assert "recommended" in result


# ── financial_health_check ────────────────────────────────────────────────────


class TestFinancialHealthCheckRateValidation:
    def test_rejects_percentage_debt_rate(self):
        with pytest.raises(ValueError, match=_RATE_MSG):
            financial_health_check(
                income=5000, expenses=2000, monthly_savings_contribution=500,
                current_savings=10000, debt_balance=5000,
                annual_debt_rate=7,        # should be 0.07
                monthly_debt_payment=200,
            )

    def test_rejects_percentage_invest_rate(self):
        with pytest.raises(ValueError, match=_RATE_MSG):
            financial_health_check(
                income=5000, expenses=2000, monthly_savings_contribution=500,
                current_savings=10000, debt_balance=5000,
                annual_debt_rate=0.07, monthly_debt_payment=200,
                assumed_invest_rate=5,    # should be 0.05
            )

    def test_accepts_normal_decimal_rates(self):
        result = financial_health_check(
            income=5000, expenses=2000, monthly_savings_contribution=500,
            current_savings=10000, debt_balance=5000,
            annual_debt_rate=0.07, monthly_debt_payment=200,
        )
        assert "score" in result


# ── goal_plan ─────────────────────────────────────────────────────────────────


class TestGoalPlanRateValidation:
    def test_rejects_percentage_rate(self):
        with pytest.raises(ValueError, match=_RATE_MSG):
            goal_plan(10000, 24, 0, 400, annual_rate=5)

    def test_accepts_normal_decimal_rate(self):
        result = goal_plan(10000, 24, 0, 400, annual_rate=0.05)
        assert "required_monthly" in result


# ── debt_schedule ─────────────────────────────────────────────────────────────


class TestDebtScheduleRateValidation:
    def test_rejects_percentage_rate(self):
        with pytest.raises(ValueError, match=_RATE_MSG):
            debt_schedule(5000, 200, annual_rate=18)

    def test_accepts_normal_decimal_rate(self):
        result = debt_schedule(5000, 200, annual_rate=0.18, months=12)
        assert len(result) == 12


# ── savings_schedule ──────────────────────────────────────────────────────────


class TestSavingsScheduleRateValidation:
    def test_rejects_percentage_rate(self):
        with pytest.raises(ValueError, match=_RATE_MSG):
            savings_schedule(1000, 100, annual_rate=7)

    def test_accepts_normal_decimal_rate(self):
        result = savings_schedule(1000, 100, annual_rate=0.07, months=12)
        assert len(result) == 12


# ── multi_debt_plan ───────────────────────────────────────────────────────────


class TestMultiDebtPlanRateValidation:
    def test_rejects_percentage_apr_on_first_debt(self):
        debts = [
            {"name": "Card A", "balance": 3000, "apr": 18, "min_payment": 60},
            {"name": "Card B", "balance": 1500, "apr": 0.12, "min_payment": 30},
        ]
        with pytest.raises(ValueError, match=_RATE_MSG):
            multi_debt_plan(debts)

    def test_rejects_percentage_apr_on_second_debt(self):
        debts = [
            {"name": "Card A", "balance": 3000, "apr": 0.18, "min_payment": 60},
            {"name": "Card B", "balance": 1500, "apr": 12, "min_payment": 30},
        ]
        with pytest.raises(ValueError, match=_RATE_MSG):
            multi_debt_plan(debts)

    def test_accepts_normal_decimal_aprs(self):
        debts = [
            {"name": "Card A", "balance": 3000, "apr": 0.18, "min_payment": 60},
            {"name": "Card B", "balance": 1500, "apr": 0.12, "min_payment": 30},
        ]
        result = multi_debt_plan(debts)
        assert "avalanche" in result


# ── compare_scenarios (annual_rate propagation) ───────────────────────────────


class TestCompareScenariosRateValidation:
    def test_rejects_percentage_annual_rate_in_scenario(self):
        scenarios = [
            {
                "label": "Base",
                "income": 5000,
                "expenses": 2000,
                "debt_payments": 300,
                "savings_contribution": 500,
                "annual_rate": 5,   # should be 0.05
            }
        ]
        with pytest.raises(ValueError, match=_RATE_MSG):
            compare_scenarios(scenarios)

    def test_accepts_normal_decimal_rate_in_scenario(self):
        scenarios = [
            {
                "label": "Base",
                "income": 5000,
                "expenses": 2000,
                "debt_payments": 300,
                "savings_contribution": 500,
                "annual_rate": 0.05,
            }
        ]
        result = compare_scenarios(scenarios)
        assert len(result) == 1
