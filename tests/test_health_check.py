"""
tests/test_health_check.py
--------------------------
Tests for financial_health_check in tools/core/finance.py.
No ADK imports — pure function tests only.
"""

from __future__ import annotations

import pytest

from tools.core.finance import financial_health_check


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _check(income, expenses, contrib, savings, debt_bal, debt_rate, debt_pmt,
           invest_rate=0.05):
    """Thin wrapper so tests stay readable."""
    return financial_health_check(
        income=income,
        expenses=expenses,
        monthly_savings_contribution=contrib,
        current_savings=savings,
        debt_balance=debt_bal,
        annual_debt_rate=debt_rate,
        monthly_debt_payment=debt_pmt,
        assumed_invest_rate=invest_rate,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Return structure
# ─────────────────────────────────────────────────────────────────────────────

REQUIRED_KEYS = {
    "score", "cash_flow_score", "emergency_fund_score",
    "debt_burden_score", "savings_rate_score",
    "cash_flow", "emergency_fund_months", "debt_to_income_ratio",
    "savings_rate", "priorities", "summary",
}

def test_returns_all_keys():
    result = _check(5000, 3000, 500, 6000, 10000, 0.06, 300)
    assert REQUIRED_KEYS == set(result.keys())

def test_score_is_int_in_range():
    result = _check(5000, 3000, 500, 6000, 10000, 0.06, 300)
    assert isinstance(result["score"], int)
    assert 0 <= result["score"] <= 100

def test_sub_scores_sum_to_total():
    result = _check(5000, 3000, 500, 6000, 10000, 0.06, 300)
    sub_sum = (result["cash_flow_score"] + result["emergency_fund_score"] +
               result["debt_burden_score"] + result["savings_rate_score"])
    assert result["score"] == sub_sum

def test_priorities_is_nonempty_list():
    result = _check(5000, 3000, 500, 6000, 10000, 0.06, 300)
    assert isinstance(result["priorities"], list)
    assert 1 <= len(result["priorities"]) <= 3

def test_summary_is_nonempty_string():
    result = _check(5000, 3000, 500, 6000, 10000, 0.06, 300)
    assert isinstance(result["summary"], str)
    assert len(result["summary"]) > 20


# ─────────────────────────────────────────────────────────────────────────────
# Cash-flow sub-score
# ─────────────────────────────────────────────────────────────────────────────

def test_cf_score_25_when_surplus():
    # income=5000, expenses=3000, debt=300, contrib=500 → cf=1200
    result = _check(5000, 3000, 500, 6000, 10000, 0.06, 300)
    assert result["cash_flow"] == pytest.approx(1200.0)
    assert result["cash_flow_score"] == 25

def test_cf_score_15_mild_deficit():
    # income=5000, mild deficit < 5% of 5000 = 250 → deficit of 100
    # expenses=3000, debt=800, contrib=1300 → cf=-100
    result = _check(5000, 3000, 1300, 6000, 10000, 0.06, 800)
    assert result["cash_flow"] == pytest.approx(-100.0)
    assert result["cash_flow_score"] == 15

def test_cf_score_0_large_deficit():
    # deficit > 5% of income (>250): expenses=4000, debt=500, contrib=1000 → cf=-500
    result = _check(5000, 4000, 1000, 6000, 10000, 0.06, 500)
    assert result["cash_flow"] == pytest.approx(-500.0)
    assert result["cash_flow_score"] == 0


# ─────────────────────────────────────────────────────────────────────────────
# Emergency-fund sub-score
# ─────────────────────────────────────────────────────────────────────────────

def test_ef_score_25_six_months():
    # savings=18000, expenses=3000 → 6 months exactly
    result = _check(5000, 3000, 500, 18000, 0, 0.0, 0)
    assert result["emergency_fund_months"] == pytest.approx(6.0)
    assert result["emergency_fund_score"] == 25

def test_ef_score_20_three_months():
    # savings=9000, expenses=3000 → 3 months
    result = _check(5000, 3000, 500, 9000, 0, 0.0, 0)
    assert result["emergency_fund_months"] == pytest.approx(3.0)
    assert result["emergency_fund_score"] == 20

def test_ef_score_10_one_month():
    # savings=3000, expenses=3000 → 1 month
    result = _check(5000, 3000, 500, 3000, 0, 0.0, 0)
    assert result["emergency_fund_months"] == pytest.approx(1.0)
    assert result["emergency_fund_score"] == 10

def test_ef_score_0_under_one_month():
    # savings=1500, expenses=3000 → 0.5 months
    result = _check(5000, 3000, 500, 1500, 0, 0.0, 0)
    assert result["emergency_fund_months"] == pytest.approx(0.5)
    assert result["emergency_fund_score"] == 0


# ─────────────────────────────────────────────────────────────────────────────
# Debt-burden sub-score
# ─────────────────────────────────────────────────────────────────────────────

def test_db_score_25_no_debt():
    result = _check(5000, 3000, 500, 6000, 0, 0.0, 0)
    assert result["debt_to_income_ratio"] == pytest.approx(0.0)
    assert result["debt_burden_score"] == 25

def test_db_score_22_low_dti():
    # 300/5000 = 0.06 ≤ 0.15
    result = _check(5000, 3000, 500, 6000, 10000, 0.06, 300)
    assert result["debt_to_income_ratio"] == pytest.approx(0.06)
    assert result["debt_burden_score"] == 22

def test_db_score_15_moderate_dti():
    # 900/5000 = 0.18, 0.15 < 0.18 ≤ 0.28
    result = _check(5000, 2000, 500, 6000, 20000, 0.06, 900)
    assert result["debt_to_income_ratio"] == pytest.approx(0.18)
    assert result["debt_burden_score"] == 15

def test_db_score_8_high_dti():
    # 1600/5000 = 0.32, 0.28 < 0.32 ≤ 0.36
    result = _check(5000, 2000, 200, 6000, 30000, 0.06, 1600)
    assert result["debt_to_income_ratio"] == pytest.approx(0.32)
    assert result["debt_burden_score"] == 8

def test_db_score_0_extreme_dti():
    # 2000/5000 = 0.40 > 0.36
    result = _check(5000, 1500, 200, 6000, 40000, 0.06, 2000)
    assert result["debt_to_income_ratio"] == pytest.approx(0.40)
    assert result["debt_burden_score"] == 0


# ─────────────────────────────────────────────────────────────────────────────
# Savings-rate sub-score
# ─────────────────────────────────────────────────────────────────────────────

def test_sr_score_25_high_rate():
    # 1200/5000 = 0.24 ≥ 0.20
    result = _check(5000, 3000, 1200, 6000, 0, 0.0, 0)
    assert result["savings_rate"] == pytest.approx(0.24)
    assert result["savings_rate_score"] == 25

def test_sr_score_18_ten_pct():
    # 500/5000 = 0.10 ≥ 0.10
    result = _check(5000, 3000, 500, 6000, 0, 0.0, 0)
    assert result["savings_rate"] == pytest.approx(0.10)
    assert result["savings_rate_score"] == 18

def test_sr_score_10_five_pct():
    # 250/5000 = 0.05 ≥ 0.05
    result = _check(5000, 3000, 250, 6000, 0, 0.0, 0)
    assert result["savings_rate"] == pytest.approx(0.05)
    assert result["savings_rate_score"] == 10

def test_sr_score_5_small_positive():
    # 100/5000 = 0.02 > 0
    result = _check(5000, 3000, 100, 6000, 0, 0.0, 0)
    assert result["savings_rate"] == pytest.approx(0.02)
    assert result["savings_rate_score"] == 5

def test_sr_score_0_no_savings():
    result = _check(5000, 3000, 0, 6000, 0, 0.0, 0)
    assert result["savings_rate"] == pytest.approx(0.0)
    assert result["savings_rate_score"] == 0


# ─────────────────────────────────────────────────────────────────────────────
# Priority rules (deterministic, first-match)
# ─────────────────────────────────────────────────────────────────────────────

def test_priority_1_negative_cash_flow():
    # Large expenses → cash flow < 0; this must be first priority
    result = _check(5000, 4500, 500, 1500, 10000, 0.06, 300)
    assert result["priorities"][0] == "Cut expenses or raise income first"

def test_priority_2_no_emergency_fund():
    # savings=100, expenses=3000 → 0.03 months < 1; but cash flow is positive
    result = _check(5000, 3000, 200, 100, 0, 0.0, 0)
    # cash flow = 5000-3000-0-200 = 1800 ≥ 0, skip rule 1
    assert result["priorities"][0] == "Build a 1-month starter emergency fund"

def test_priority_3_high_rate_debt():
    # debt_rate (9%) > invest_rate (5%), EF >= 1 month, cash flow positive
    result = _check(5000, 3000, 200, 4000, 18000, 0.09, 300)
    # ef = 4000/3000 = 1.33 months ≥ 1, skip rule 2
    # cash flow = 5000-3000-300-200 = 1500 ≥ 0, skip rule 1
    assert result["priorities"][0] == "Put extra cash toward high-interest debt"

def test_priority_4_low_emergency_fund():
    # EF 1-3 months, debt rate ≤ invest rate, cash flow positive
    result = _check(5000, 3000, 200, 4000, 5000, 0.03, 200, invest_rate=0.05)
    # ef = 4000/3000 = 1.33 months (1-3 range), debt rate < invest rate
    # cash flow = 5000-3000-200-200 = 1600 ≥ 0
    assert result["priorities"][0] == "Grow emergency fund to 3 months"

def test_priority_5_default_invest():
    # Perfect position: cash flow +, EF ≥ 3 mo, debt rate ≤ invest rate
    result = _check(5000, 2000, 500, 10000, 5000, 0.03, 200, invest_rate=0.05)
    # ef = 10000/2000 = 5 months ≥ 3, debt rate < invest rate
    # cash flow = 5000-2000-200-500 = 2300 ≥ 0
    assert result["priorities"][0] == "Start investing the surplus"

def test_priorities_max_three():
    result = _check(5000, 4500, 500, 100, 10000, 0.09, 300)
    assert len(result["priorities"]) <= 3


# ─────────────────────────────────────────────────────────────────────────────
# Score boundaries — perfect and zero
# ─────────────────────────────────────────────────────────────────────────────

def test_perfect_score():
    # Positive CF, 6+ months EF, zero debt, 20%+ savings
    result = _check(10000, 4000, 2500, 30000, 0, 0.0, 0)
    # cf = 10000-4000-0-2500 = 3500 → cf_score=25
    # ef = 30000/4000 = 7.5 → ef_score=25
    # dti = 0 → db_score=25
    # srate = 2500/10000 = 0.25 → sr_score=25
    assert result["score"] == 100

def test_zero_score():
    # Huge deficit, no savings, huge debt payment
    result = _check(5000, 5000, 0, 0, 50000, 0.20, 3000)
    # cf = 5000-5000-3000-0 = -3000 (> 5% of 5000=250) → cf_score=0
    # ef = 0 → ef_score=0
    # dti = 3000/5000 = 0.60 > 0.36 → db_score=0
    # sr = 0 → sr_score=0
    assert result["score"] == 0


# ─────────────────────────────────────────────────────────────────────────────
# Edge cases
# ─────────────────────────────────────────────────────────────────────────────

def test_recent_graduate_profile():
    # income=3200, expenses=2400, contrib=200, savings=1500,
    # debt=8000, rate=7%, pmt=250
    result = _check(3200, 2400, 200, 1500, 8000, 0.07, 250)
    # cf = 3200-2400-250-200 = 350 ≥ 0 → cf_score=25
    # ef = 1500/2400 = 0.625 < 1 → ef_score=0
    # dti = 250/3200 = 0.078 ≤ 0.15 → db_score=22
    # sr = 200/3200 = 0.0625 ≥ 0.05 → sr_score=10
    assert result["cash_flow"] == pytest.approx(350.0)
    assert result["cash_flow_score"] == 25
    assert result["emergency_fund_score"] == 0
    assert result["debt_burden_score"] == 22
    assert result["savings_rate_score"] == 10
    assert result["score"] == 57
    # EF < 1 month triggers priority 2 (EF check before debt rate check)
    assert result["priorities"][0] == "Build a 1-month starter emergency fund"

def test_input_validation_income_zero():
    with pytest.raises(ValueError, match="income must be > 0"):
        _check(0, 3000, 500, 6000, 0, 0.0, 0)

def test_input_validation_negative_expenses():
    with pytest.raises(ValueError, match="expenses must be >= 0"):
        _check(5000, -100, 500, 6000, 0, 0.0, 0)

def test_input_validation_negative_savings():
    with pytest.raises(ValueError, match="current_savings must be >= 0"):
        _check(5000, 3000, 500, -1, 0, 0.0, 0)

def test_input_validation_negative_rate():
    with pytest.raises(ValueError, match="annual_debt_rate must be >= 0"):
        _check(5000, 3000, 500, 6000, 10000, -0.01, 300)
