"""
tests/test_finance.py
---------------------
Unit tests for tools/core/finance.py.

Run with:  pytest tests/ -v --tb=short
"""

from __future__ import annotations

import math
import sys
import os

import pytest

# Make tools/core importable without installing the package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tools.core.finance import (
    DEFAULT_ANNUAL_RATE,
    MAX_SCENARIOS,
    compare_scenarios,
    emergency_fund_months,
    monthly_cash_flow,
    project_savings_growth,
)


# ═══════════════════════════════════════════════════════════════════════════════
# emergency_fund_months
# ═══════════════════════════════════════════════════════════════════════════════


class TestEmergencyFundMonths:
    def test_typical_three_months(self):
        assert emergency_fund_months(6000, 2000) == 3.0

    def test_fractional_months(self):
        assert emergency_fund_months(5000, 2000) == 2.5

    def test_zero_savings(self):
        assert emergency_fund_months(0, 2000) == 0.0

    def test_result_rounded_to_two_decimals(self):
        result = emergency_fund_months(1000, 3000)
        assert result == round(1000 / 3000, 2)

    def test_large_savings(self):
        assert emergency_fund_months(120_000, 4_000) == 30.0

    def test_negative_savings_raises(self):
        with pytest.raises(ValueError, match="savings must be >= 0"):
            emergency_fund_months(-100, 2000)

    def test_zero_expenses_raises(self):
        with pytest.raises(ValueError, match="monthly_expenses must be > 0"):
            emergency_fund_months(5000, 0)

    def test_negative_expenses_raises(self):
        with pytest.raises(ValueError, match="monthly_expenses must be > 0"):
            emergency_fund_months(5000, -500)


# ═══════════════════════════════════════════════════════════════════════════════
# monthly_cash_flow
# ═══════════════════════════════════════════════════════════════════════════════


class TestMonthlyCashFlow:
    def test_positive_surplus(self):
        # 5000 - 2000 - 500 - 300 = 2200
        assert monthly_cash_flow(5000, 2000, 500, 300) == 2200.0

    def test_exactly_zero_surplus(self):
        assert monthly_cash_flow(3000, 2000, 500, 500) == 0.0

    def test_negative_surplus_infeasible(self):
        assert monthly_cash_flow(3000, 2000, 500, 700) == -200.0

    def test_no_debt_no_savings(self):
        assert monthly_cash_flow(4000, 3500, 0, 0) == 500.0

    def test_result_rounded(self):
        result = monthly_cash_flow(3333.33, 1111.11, 222.22, 333.33)
        expected = round(3333.33 - 1111.11 - 222.22 - 333.33, 2)
        assert result == expected

    def test_zero_income_raises(self):
        with pytest.raises(ValueError, match="income must be > 0"):
            monthly_cash_flow(0, 2000, 500, 300)

    def test_negative_income_raises(self):
        with pytest.raises(ValueError, match="income must be > 0"):
            monthly_cash_flow(-100, 2000, 500, 300)

    def test_negative_expenses_raises(self):
        with pytest.raises(ValueError, match="expenses must be >= 0"):
            monthly_cash_flow(5000, -200, 500, 300)

    def test_negative_debt_payments_raises(self):
        with pytest.raises(ValueError, match="debt_payments must be >= 0"):
            monthly_cash_flow(5000, 2000, -100, 300)

    def test_negative_savings_contribution_raises(self):
        with pytest.raises(ValueError, match="savings_contribution must be >= 0"):
            monthly_cash_flow(5000, 2000, 500, -50)


# ═══════════════════════════════════════════════════════════════════════════════
# project_savings_growth
# ═══════════════════════════════════════════════════════════════════════════════


class TestProjectSavingsGrowth:
    def test_zero_rate_no_contribution(self):
        # Only principal, no growth
        assert project_savings_growth(10_000, 0, annual_rate=0, months=12) == 10_000.0

    def test_zero_rate_with_contribution(self):
        # 1000 + 200 * 12 = 3400
        assert project_savings_growth(1000, 200, annual_rate=0, months=12) == 3400.0

    def test_default_rate_applied(self):
        # Ensure DEFAULT_ANNUAL_RATE is used when not specified
        r = DEFAULT_ANNUAL_RATE / 12
        n = 12
        growth = math.pow(1 + r, n)
        expected = round(10_000 * growth + 500 * (growth - 1) / r, 2)
        assert project_savings_growth(10_000, 500, months=n) == expected

    def test_explicit_rate(self):
        r = 0.06 / 12
        n = 24
        growth = math.pow(1 + r, n)
        expected = round(5_000 * growth + 300 * (growth - 1) / r, 2)
        assert project_savings_growth(5_000, 300, annual_rate=0.06, months=n) == expected

    def test_zero_principal_with_contribution(self):
        result = project_savings_growth(0, 200, annual_rate=0, months=6)
        assert result == 1200.0

    def test_result_rounded_to_two_decimals(self):
        result = project_savings_growth(1000, 100, annual_rate=0.05, months=3)
        # Verify it's exactly two decimal places
        assert result == round(result, 2)

    def test_negative_principal_raises(self):
        with pytest.raises(ValueError, match="principal must be >= 0"):
            project_savings_growth(-100, 200, months=12)

    def test_negative_contribution_raises(self):
        with pytest.raises(ValueError, match="monthly_contribution must be >= 0"):
            project_savings_growth(1000, -50, months=12)

    def test_negative_rate_raises(self):
        with pytest.raises(ValueError, match="annual_rate must be >= 0"):
            project_savings_growth(1000, 200, annual_rate=-0.01, months=12)

    def test_zero_months_raises(self):
        with pytest.raises(ValueError, match="months must be > 0"):
            project_savings_growth(1000, 200, months=0)

    def test_negative_months_raises(self):
        with pytest.raises(ValueError, match="months must be > 0"):
            project_savings_growth(1000, 200, months=-1)


# ═══════════════════════════════════════════════════════════════════════════════
# compare_scenarios
# ═══════════════════════════════════════════════════════════════════════════════

# Reusable base scenario
_BASE = {
    "label": "Current",
    "income": 5000.0,
    "expenses": 2500.0,
    "debt_payments": 400.0,
    "savings_contribution": 300.0,
    "current_savings": 6000.0,
    "annual_rate": 0.05,
    "months": 12,
}


class TestCompareScenarios:
    def test_single_scenario_returns_one_result(self):
        results = compare_scenarios([_BASE])
        assert len(results) == 1

    def test_result_keys_present(self):
        results = compare_scenarios([_BASE])
        r = results[0]
        for key in [
            "label", "cash_flow", "emergency_fund_months",
            "projected_savings", "feasible",
            "assumed_annual_rate", "assumed_months",
        ]:
            assert key in r, f"Missing key: {key}"

    def test_cash_flow_correct(self):
        results = compare_scenarios([_BASE])
        expected_cf = monthly_cash_flow(5000, 2500, 400, 300)
        assert results[0]["cash_flow"] == expected_cf

    def test_emergency_fund_correct(self):
        results = compare_scenarios([_BASE])
        expected_ef = emergency_fund_months(6000, 2500)
        assert results[0]["emergency_fund_months"] == expected_ef

    def test_projected_savings_correct(self):
        results = compare_scenarios([_BASE])
        expected_ps = project_savings_growth(6000, 300, 0.05, 12)
        assert results[0]["projected_savings"] == expected_ps

    def test_feasible_true_when_surplus(self):
        results = compare_scenarios([_BASE])
        assert results[0]["feasible"] is True

    def test_feasible_false_when_deficit(self):
        infeasible = {**_BASE, "label": "Infeasible", "savings_contribution": 5000.0}
        results = compare_scenarios([infeasible])
        assert results[0]["feasible"] is False

    def test_three_scenarios(self):
        s1 = {**_BASE, "label": "Current"}
        s2 = {**_BASE, "label": "+200", "savings_contribution": 500.0}
        s3 = {**_BASE, "label": "+400", "savings_contribution": 700.0}
        results = compare_scenarios([s1, s2, s3])
        assert len(results) == 3
        assert results[1]["savings_contribution"] == 500.0
        assert results[2]["savings_contribution"] == 700.0

    def test_defaults_applied_when_optional_keys_absent(self):
        minimal = {k: _BASE[k] for k in _REQUIRED_SCENARIO_KEYS}
        results = compare_scenarios([minimal])
        assert results[0]["assumed_annual_rate"] == DEFAULT_ANNUAL_RATE
        assert results[0]["assumed_months"] == 12
        assert results[0]["current_savings"] == 0.0

    def test_empty_list_raises(self):
        with pytest.raises(ValueError, match="at least one entry"):
            compare_scenarios([])

    def test_too_many_scenarios_raises(self):
        too_many = [{**_BASE, "label": f"s{i}"} for i in range(MAX_SCENARIOS + 1)]
        with pytest.raises(ValueError, match=f"at most {MAX_SCENARIOS}"):
            compare_scenarios(too_many)

    def test_missing_required_key_raises(self):
        bad = {k: v for k, v in _BASE.items() if k != "income"}
        with pytest.raises(ValueError, match="missing required keys"):
            compare_scenarios([bad])

    def test_labels_preserved_in_order(self):
        s1 = {**_BASE, "label": "Alpha"}
        s2 = {**_BASE, "label": "Beta", "savings_contribution": 500.0}
        results = compare_scenarios([s1, s2])
        assert results[0]["label"] == "Alpha"
        assert results[1]["label"] == "Beta"


# Expose required keys for the defaults test above
_REQUIRED_SCENARIO_KEYS = {"label", "income", "expenses", "debt_payments", "savings_contribution"}
