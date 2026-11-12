"""tests/test_goal_plan.py — Tests for goal_plan, debt_schedule, savings_schedule."""
import math
import pytest
from tools.core.finance import goal_plan, debt_schedule, savings_schedule


# ── goal_plan ─────────────────────────────────────────────────────────────────

def test_goal_plan_returns_all_keys():
    r = goal_plan(5000, 12, 0, 500)
    assert {"required_monthly","feasible","shortfall_per_month",
            "months_needed_at_current_headroom","projected_at_headroom","summary"} == set(r.keys())

def test_goal_plan_feasible_exact():
    # Need $5000 in 10 months, have $0 saved, headroom $500 → exactly $500/mo needed
    r = goal_plan(5000, 10, 0, 500)
    assert r["required_monthly"] == pytest.approx(500.0)
    assert r["feasible"] is True
    assert r["shortfall_per_month"] == 0.0

def test_goal_plan_feasible_with_existing_savings():
    # Need $5000, already have $2000, only $3000 more in 10 months = $300/mo
    r = goal_plan(5000, 10, 2000, 400)
    assert r["required_monthly"] == pytest.approx(300.0)
    assert r["feasible"] is True

def test_goal_plan_infeasible():
    r = goal_plan(5000, 10, 0, 200)
    assert r["required_monthly"] == pytest.approx(500.0)
    assert r["feasible"] is False
    assert r["shortfall_per_month"] == pytest.approx(300.0)

def test_goal_plan_months_at_headroom():
    # $5000 target, $0 saved, $200/mo headroom → ceiling(25) = 25 months
    r = goal_plan(5000, 12, 0, 200)
    assert r["months_needed_at_current_headroom"] == 25

def test_goal_plan_already_reached():
    # current_saved >= target → required_monthly = 0
    r = goal_plan(5000, 12, 6000, 500)
    assert r["required_monthly"] == 0.0
    assert r["feasible"] is True

def test_goal_plan_zero_headroom():
    r = goal_plan(5000, 12, 0, 0)
    assert r["months_needed_at_current_headroom"] is None
    assert r["feasible"] is False

def test_goal_plan_with_rate():
    # With 5% annual rate, required monthly should be less than without rate
    r_no_rate  = goal_plan(12000, 24, 0, 1000)
    r_with_rate = goal_plan(12000, 24, 0, 1000, annual_rate=0.05)
    assert r_with_rate["required_monthly"] < r_no_rate["required_monthly"]

def test_goal_plan_summary_feasible():
    r = goal_plan(5000, 10, 0, 600)
    assert "FEASIBLE" in r["summary"]
    assert "to spare" in r["summary"]

def test_goal_plan_summary_infeasible():
    r = goal_plan(5000, 10, 0, 200)
    assert "shortfall" in r["summary"]

def test_goal_plan_validation_target_zero():
    with pytest.raises(ValueError, match="target_amount must be > 0"):
        goal_plan(0, 12, 0, 500)

def test_goal_plan_validation_months_zero():
    with pytest.raises(ValueError, match="months_to_goal must be > 0"):
        goal_plan(5000, 0, 0, 500)

def test_goal_plan_validation_negative_saved():
    with pytest.raises(ValueError, match="current_saved must be >= 0"):
        goal_plan(5000, 12, -100, 500)

def test_goal_plan_validation_negative_headroom():
    with pytest.raises(ValueError, match="monthly_headroom must be >= 0"):
        goal_plan(5000, 12, 0, -1)


# ── debt_schedule ─────────────────────────────────────────────────────────────

def test_debt_schedule_length():
    s = debt_schedule(10000, 300, 0.06, months=24)
    assert len(s) == 24

def test_debt_schedule_zero_rate():
    # 1200 balance, $400/mo, 0% → paid off in 3 months
    s = debt_schedule(1200, 400, 0.0, months=6)
    assert s[2] == 0.0
    assert all(v == 0.0 for v in s[3:])

def test_debt_schedule_decreasing():
    s = debt_schedule(10000, 500, 0.06, months=12)
    non_zero = [v for v in s if v > 0]
    assert non_zero == sorted(non_zero, reverse=True)

def test_debt_schedule_stays_zero_after_payoff():
    s = debt_schedule(1000, 600, 0.0, months=10)
    # paid off in 2 months, rest should be 0
    assert s[1] == 0.0 or s[2] == 0.0
    assert s[-1] == 0.0

def test_debt_schedule_with_interest():
    s = debt_schedule(10000, 300, 0.12, months=36)
    # first month: interest = 10000 * 0.01 = 100, balance = 10100 - 300 = 9800
    assert s[0] == pytest.approx(9800.0, abs=1)

def test_debt_schedule_validation():
    with pytest.raises(ValueError): debt_schedule(-1, 300, 0.06)
    with pytest.raises(ValueError): debt_schedule(1000, -1, 0.06)
    with pytest.raises(ValueError): debt_schedule(1000, 300, -0.01)
    with pytest.raises(ValueError): debt_schedule(1000, 300, 0.06, months=0)


# ── savings_schedule ──────────────────────────────────────────────────────────

def test_savings_schedule_length():
    s = savings_schedule(1000, 200, 0.05, months=12)
    assert len(s) == 12

def test_savings_schedule_zero_rate():
    s = savings_schedule(1000, 200, 0.0, months=5)
    assert s[0] == pytest.approx(1200.0)
    assert s[4] == pytest.approx(2000.0)

def test_savings_schedule_increasing():
    s = savings_schedule(0, 500, 0.06, months=12)
    assert s == sorted(s)

def test_savings_schedule_compounding():
    # With rate, end balance > start + n * contribution
    s = savings_schedule(0, 500, 0.06, months=12)
    simple = 500 * 12
    assert s[-1] > simple

def test_savings_schedule_no_contribution():
    # Just compounding on existing balance
    s = savings_schedule(1000, 0, 0.12, months=1)
    assert s[0] == pytest.approx(1000 * (1 + 0.12/12), rel=1e-4)

def test_savings_schedule_validation():
    with pytest.raises(ValueError): savings_schedule(-1, 200, 0.05)
    with pytest.raises(ValueError): savings_schedule(1000, -1, 0.05)
    with pytest.raises(ValueError): savings_schedule(1000, 200, -0.01)
    with pytest.raises(ValueError): savings_schedule(1000, 200, 0.05, months=0)
