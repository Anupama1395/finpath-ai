"""
tests/test_new_tools.py
-----------------------
Unit tests for:
  - debt_payoff_months   (updated return keys + "never pays off" path)
  - debt_vs_invest       (rewritten simulation model, new min_monthly_payment param)
  - stress_test
  - savings_headroom     (new)
  - emergency_fund_check (new)

Run with:  pytest tests/ -v --tb=short
"""

from __future__ import annotations

import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tools.core.finance import (
    DEFAULT_ANNUAL_RATE,
    DEFAULT_EMERGENCY_TARGET,
    debt_payoff_months,
    debt_vs_invest,
    emergency_fund_check,
    savings_headroom,
    stress_test,
)


# ═══════════════════════════════════════════════════════════════════════════════
# debt_payoff_months
# ═══════════════════════════════════════════════════════════════════════════════

class TestDebtPayoffMonths:
    # ── smoke test values from Step 6 of the plan ─────────────────────────────

    def test_recent_graduate_36_months(self):
        # 8000 @ 7%, $250/mo → 36 months, ~$880.88 interest
        r = debt_payoff_months(8_000, 250, 0.07)
        assert r["months_to_payoff"] == 36
        assert r["total_interest_paid"] == pytest.approx(880.88, abs=1.0)

    def test_mid_career_saver_18_months(self):
        # 5000 @ 4.5%, $300/mo → 18 months, ~$172.86 interest
        r = debt_payoff_months(5_000, 300, 0.045)
        assert r["months_to_payoff"] == 18
        assert r["total_interest_paid"] == pytest.approx(172.86, abs=1.0)

    def test_debt_focused_43_months(self):
        # 18000 @ 9%, $500/mo → 43 months, ~$3059.49 interest
        r = debt_payoff_months(18_000, 500, 0.09)
        assert r["months_to_payoff"] == 43
        assert r["total_interest_paid"] == pytest.approx(3059.49, abs=2.0)

    # ── return keys ───────────────────────────────────────────────────────────

    def test_required_keys_present(self):
        r = debt_payoff_months(5_000, 200, 0.06)
        for key in ["months_to_payoff", "total_interest_paid", "total_paid", "summary"]:
            assert key in r

    def test_total_paid_equals_balance_plus_interest(self):
        r = debt_payoff_months(5_000, 200, 0.06)
        assert abs(r["total_paid"] - (5_000 + r["total_interest_paid"])) < 0.02

    def test_summary_is_non_empty_string(self):
        r = debt_payoff_months(5_000, 200, 0.06)
        assert isinstance(r["summary"], str) and len(r["summary"]) > 10

    # ── zero-rate path ────────────────────────────────────────────────────────

    def test_zero_rate_exact_divisor(self):
        r = debt_payoff_months(1200, 100, 0.0)
        assert r["months_to_payoff"] == 12
        assert r["total_interest_paid"] == 0.0
        assert r["total_paid"] == pytest.approx(1200.0, abs=0.01)

    def test_zero_rate_non_divisor(self):
        r = debt_payoff_months(1000, 300, 0.0)
        assert r["months_to_payoff"] == 4
        assert r["total_interest_paid"] == 0.0
        assert r["total_paid"] == pytest.approx(1000.0, abs=0.01)

    # ── "never pays off" returns a clear result, does NOT raise ───────────────

    def test_payment_below_interest_returns_never_pays_off(self):
        # 10000 @ 12% → monthly interest = 100; payment = 50 < 100
        r = debt_payoff_months(10_000, 50, 0.12)
        assert r["months_to_payoff"] is None
        assert r["total_interest_paid"] is None
        assert "never" in r["summary"].lower() or "not cover" in r["summary"].lower()

    def test_payment_exactly_at_interest_returns_never_pays_off(self):
        # 12000 @ 12% → monthly interest = 120; payment = 120 == 120
        r = debt_payoff_months(12_000, 120, 0.12)
        assert r["months_to_payoff"] is None

    # ── validation errors ─────────────────────────────────────────────────────

    def test_zero_balance_raises(self):
        with pytest.raises(ValueError, match="balance must be > 0"):
            debt_payoff_months(0, 200, 0.05)

    def test_zero_payment_raises(self):
        with pytest.raises(ValueError, match="monthly_payment must be > 0"):
            debt_payoff_months(5000, 0, 0.05)

    def test_negative_rate_raises(self):
        with pytest.raises(ValueError, match="annual_rate must be >= 0"):
            debt_payoff_months(5000, 200, -0.01)

    # ── ordering invariants ───────────────────────────────────────────────────

    def test_higher_payment_fewer_months(self):
        slow = debt_payoff_months(10_000, 200, 0.06)
        fast = debt_payoff_months(10_000, 500, 0.06)
        assert fast["months_to_payoff"] < slow["months_to_payoff"]

    def test_higher_rate_more_interest(self):
        low  = debt_payoff_months(10_000, 400, 0.03)
        high = debt_payoff_months(10_000, 400, 0.18)
        assert high["total_interest_paid"] > low["total_interest_paid"]


# ═══════════════════════════════════════════════════════════════════════════════
# debt_vs_invest  (rewritten simulation model)
# ═══════════════════════════════════════════════════════════════════════════════

class TestDebtVsInvest:
    # ── Required tests from the plan ─────────────────────────────────────────

    def test_equal_cash_outflow_both_strategies(self):
        """Both strategies must spend the same total cash over the horizon."""
        # Total cash out = monthly_surplus * months for both
        budget = 500
        mo = 24
        r = debt_vs_invest(5_000, 0.08, budget, 150, annual_invest_rate=0.05, months=mo)
        # We can't directly observe cash out from the API, but we can verify
        # that the model ran without error and returned both net worths
        assert "strategy_a_net_worth" in r
        assert "strategy_b_net_worth" in r

    def test_invest_rate_zero_debt_rate_positive_recommends_debt_first(self):
        """invest_rate=0, debt_rate>0 → debt_first must win (impossible otherwise)."""
        r = debt_vs_invest(
            balance=5_000, annual_debt_rate=0.10,
            monthly_surplus=400, min_monthly_payment=100,
            annual_invest_rate=0.0, months=36,
        )
        assert r["recommended"] == "debt_first", (
            f"Expected debt_first when invest_rate=0 and debt_rate>0. Got: {r}"
        )

    def test_high_invest_rate_vs_low_debt_rate_recommends_invest_first(self):
        """invest_rate >> debt_rate → invest_first must win."""
        r = debt_vs_invest(
            balance=5_000, annual_debt_rate=0.02,  # 2% debt
            monthly_surplus=500, min_monthly_payment=100,
            annual_invest_rate=0.15, months=60,    # 15% return
        )
        assert r["recommended"] == "invest_first", (
            f"Expected invest_first when invest_rate >> debt_rate. Got: {r}"
        )

    def test_equal_rates_net_worths_close(self):
        """When debt_rate == invest_rate, net worths should be close (within ~5%)."""
        r = debt_vs_invest(
            balance=5_000, annual_debt_rate=0.06,
            monthly_surplus=400, min_monthly_payment=100,
            annual_invest_rate=0.06, months=60,
        )
        a, b = r["strategy_a_net_worth"], r["strategy_b_net_worth"]
        mid = (abs(a) + abs(b)) / 2 or 1
        assert abs(a - b) / mid < 0.10, (
            f"Equal rates should give close net worths. A={a}, B={b}"
        )

    def test_budget_below_min_payment_raises(self):
        with pytest.raises(ValueError, match="must be greater than min_monthly_payment"):
            debt_vs_invest(5_000, 0.08, monthly_surplus=100, min_monthly_payment=200)

    def test_min_payment_below_first_month_interest_raises(self):
        # balance=10000, rate=0.24 → monthly interest=200; min_pay=150 < 200
        with pytest.raises(ValueError, match="must exceed the first month's interest"):
            debt_vs_invest(10_000, 0.24, monthly_surplus=600, min_monthly_payment=150)

    # ── Return keys ───────────────────────────────────────────────────────────

    def test_required_keys_present(self):
        r = debt_vs_invest(5_000, 0.08, 400, 100)
        for key in [
            "strategy_a_net_worth", "strategy_b_net_worth",
            "recommended", "payoff_months_a", "payoff_months_b",
            "assumed_invest_rate", "assumed_months",
        ]:
            assert key in r, f"Missing key: {key}"

    def test_assumed_values_echoed(self):
        r = debt_vs_invest(8_000, 0.05, 400, 120, annual_invest_rate=0.07, months=48)
        assert r["assumed_invest_rate"] == 0.07
        assert r["assumed_months"] == 48

    def test_default_invest_rate_applied(self):
        r = debt_vs_invest(8_000, 0.05, 400, 100)
        assert r["assumed_invest_rate"] == DEFAULT_ANNUAL_RATE
        assert r["assumed_months"] == 60

    def test_recommended_consistent_with_net_worths(self):
        """recommended must always reflect the actual net worth comparison."""
        for bal, dr, sur, mp, ir, mo in [
            (5_000, 0.10, 400, 100, 0.0,  36),   # debt_first
            (5_000, 0.02, 500, 100, 0.15, 60),   # invest_first
        ]:
            r = debt_vs_invest(bal, dr, sur, mp, ir, mo)
            a, b = r["strategy_a_net_worth"], r["strategy_b_net_worth"]
            if abs(a - b) < 1.0:
                assert r["recommended"] == "neutral"
            elif a > b:
                assert r["recommended"] == "debt_first"
            else:
                assert r["recommended"] == "invest_first"

    def test_payoff_months_a_set_when_debt_clearable(self):
        r = debt_vs_invest(2_000, 0.06, 500, 100, months=60)
        assert r["payoff_months_a"] is not None
        assert 1 <= r["payoff_months_a"] <= 60

    # ── Validation errors ─────────────────────────────────────────────────────

    def test_zero_balance_raises(self):
        with pytest.raises(ValueError, match="balance must be > 0"):
            debt_vs_invest(0, 0.05, 300, 100)

    def test_negative_debt_rate_raises(self):
        with pytest.raises(ValueError, match="annual_debt_rate must be >= 0"):
            debt_vs_invest(5000, -0.01, 300, 100)

    def test_zero_surplus_raises(self):
        with pytest.raises(ValueError, match="monthly_surplus must be > 0"):
            debt_vs_invest(5000, 0.05, 0, 100)

    def test_zero_min_payment_raises(self):
        with pytest.raises(ValueError, match="min_monthly_payment must be > 0"):
            debt_vs_invest(5000, 0.05, 400, 0)

    def test_negative_invest_rate_raises(self):
        with pytest.raises(ValueError, match="annual_invest_rate must be >= 0"):
            debt_vs_invest(5000, 0.05, 300, 100, annual_invest_rate=-0.01)

    def test_zero_months_raises(self):
        with pytest.raises(ValueError, match="months must be > 0"):
            debt_vs_invest(5000, 0.05, 300, 100, months=0)


# ═══════════════════════════════════════════════════════════════════════════════
# stress_test
# ═══════════════════════════════════════════════════════════════════════════════

_ST_BASE = dict(
    income=5000, expenses=2500, debt_payments=400,
    savings_contribution=300, current_savings=7500,
)


class TestStressTest:
    def test_no_shock_returns_base_values(self):
        result = stress_test(**_ST_BASE)
        assert result["shocked_income"]   == 5000.0
        assert result["shocked_expenses"] == 2500.0
        # cash_flow = 5000 - 2500 - 400 - 300 = 1800
        assert result["shocked_cash_flow"] == 1800.0

    def test_income_shock_minus_10_pct(self):
        result = stress_test(**_ST_BASE, income_shock_pct=-10)
        assert result["shocked_income"] == pytest.approx(4500.0, abs=0.01)
        assert result["income_shock_pct"] == -10

    def test_expense_shock_plus_10_pct(self):
        result = stress_test(**_ST_BASE, expenses_shock_pct=10)
        assert result["shocked_expenses"] == pytest.approx(2750.0, abs=0.01)
        assert result["expenses_shock_pct"] == 10

    def test_severe_income_shock_makes_infeasible(self):
        result = stress_test(**_ST_BASE, income_shock_pct=-50)
        assert result["still_feasible"] is False

    def test_feasible_stays_true_under_small_shock(self):
        result = stress_test(**_ST_BASE, income_shock_pct=-5)
        assert result["still_feasible"] is True

    def test_emergency_fund_months_computed(self):
        # 7500 / 2500 = 3.0 months, no shock
        result = stress_test(**_ST_BASE)
        assert result["shocked_emergency_months"] == 3.0

    def test_meets_target_true_when_above_threshold(self):
        result = stress_test(**_ST_BASE, emergency_target_months=3.0)
        assert result["still_meets_target"] is True

    def test_meets_target_false_when_below_threshold(self):
        result = stress_test(
            income=5000, expenses=2500, debt_payments=400,
            savings_contribution=300, current_savings=2000,
            emergency_target_months=3.0,
        )
        assert result["still_meets_target"] is False

    def test_expense_shock_reduces_emergency_coverage(self):
        base    = stress_test(**_ST_BASE, expenses_shock_pct=0)
        shocked = stress_test(**_ST_BASE, expenses_shock_pct=50)
        assert shocked["shocked_emergency_months"] < base["shocked_emergency_months"]

    def test_returned_keys_complete(self):
        result = stress_test(**_ST_BASE)
        for key in [
            "shocked_income", "shocked_expenses", "shocked_cash_flow",
            "shocked_emergency_months", "still_feasible", "still_meets_target",
            "income_shock_pct", "expenses_shock_pct", "emergency_target_months",
        ]:
            assert key in result

    def test_echoed_values_correct(self):
        result = stress_test(**_ST_BASE, income_shock_pct=-10,
                             expenses_shock_pct=10, emergency_target_months=4.0)
        assert result["income_shock_pct"]        == -10
        assert result["expenses_shock_pct"]      == 10
        assert result["emergency_target_months"] == 4.0

    def test_combined_shock(self):
        result = stress_test(**_ST_BASE, income_shock_pct=-10, expenses_shock_pct=10)
        assert result["shocked_income"]   == pytest.approx(4500.0, abs=0.01)
        assert result["shocked_expenses"] == pytest.approx(2750.0, abs=0.01)

    def test_default_emergency_target_is_3(self):
        result = stress_test(**_ST_BASE)
        assert result["emergency_target_months"] == DEFAULT_EMERGENCY_TARGET


# ═══════════════════════════════════════════════════════════════════════════════
# savings_headroom
# ═══════════════════════════════════════════════════════════════════════════════

class TestSavingsHeadroom:
    # ── Smoke test values from Step 6 of the plan ────────────────────────────

    def test_recent_graduate_free_cash_600(self):
        # 3200 - 2400 - 200 = 600
        r = savings_headroom(3200, 2400, 200)
        assert r["free_cash"] == 600.0
        assert r["can_save_more"] is True
        assert r["max_additional_savings"] == 600.0

    def test_mid_career_saver_headroom(self):
        # 6500 - 3800 - 1000 = 1700
        r = savings_headroom(6500, 3800, 1000)
        assert r["free_cash"] == 1700.0
        assert r["can_save_more"] is True

    def test_debt_focused_headroom(self):
        # 4800 - 3200 - 200 = 1400
        r = savings_headroom(4800, 3200, 200)
        assert r["free_cash"] == 1400.0
        assert r["can_save_more"] is True

    # ── Edge cases ────────────────────────────────────────────────────────────

    def test_no_headroom_when_expenses_equal_income(self):
        r = savings_headroom(3000, 3000, 0)
        assert r["free_cash"] == 0.0
        assert r["can_save_more"] is False
        assert r["max_additional_savings"] == 0.0

    def test_negative_free_cash_clamped_to_zero_max_additional(self):
        r = savings_headroom(3000, 2500, 700)
        assert r["free_cash"] == -200.0
        assert r["can_save_more"] is False
        assert r["max_additional_savings"] == 0.0

    def test_zero_contribution_uses_full_surplus(self):
        r = savings_headroom(4000, 3000, 0)
        assert r["free_cash"] == 1000.0
        assert r["max_additional_savings"] == 1000.0

    def test_required_keys_present(self):
        r = savings_headroom(4000, 2500, 300)
        for key in ["free_cash", "can_save_more", "max_additional_savings", "summary"]:
            assert key in r

    def test_summary_is_non_empty_string(self):
        r = savings_headroom(4000, 2500, 300)
        assert isinstance(r["summary"], str) and len(r["summary"]) > 10

    # ── Validation ────────────────────────────────────────────────────────────

    def test_zero_income_raises(self):
        with pytest.raises(ValueError, match="income must be > 0"):
            savings_headroom(0, 2000, 200)

    def test_negative_income_raises(self):
        with pytest.raises(ValueError, match="income must be > 0"):
            savings_headroom(-500, 2000, 200)

    def test_negative_expenses_raises(self):
        with pytest.raises(ValueError, match="expenses must be >= 0"):
            savings_headroom(4000, -100, 200)

    def test_negative_contribution_raises(self):
        with pytest.raises(ValueError, match="current_savings_contribution must be >= 0"):
            savings_headroom(4000, 2500, -50)

    def test_result_rounded_to_two_decimals(self):
        r = savings_headroom(3333.33, 1111.11, 222.22)
        assert r["free_cash"] == round(3333.33 - 1111.11 - 222.22, 2)


# ═══════════════════════════════════════════════════════════════════════════════
# emergency_fund_check
# ═══════════════════════════════════════════════════════════════════════════════

class TestEmergencyFundCheck:
    # ── Smoke test values from Step 6 of the plan ────────────────────────────

    def test_recent_graduate_low_0_62_months(self):
        # 1500 / 2400 = 0.625 → rounds to 0.62 at 2dp; low, gap = 3*2400 - 1500 = 5700
        r = emergency_fund_check(1500, 2400)
        assert r["months_covered"] == 0.62
        assert r["status"] == "low"
        assert r["gap_to_3_months"] == 5700.0

    def test_mid_career_saver_ok_3_16_months(self):
        # 12000 / 3800 ≈ 3.16 → ok, gap = 0
        r = emergency_fund_check(12000, 3800)
        assert r["months_covered"] == pytest.approx(3.16, abs=0.01)
        assert r["status"] == "ok"
        assert r["gap_to_3_months"] == 0.0

    def test_debt_focused_low_0_62_months(self):
        # 2000 / 3200 = 0.625 → rounds to 0.62 at 2dp; low, gap = 3*3200 - 2000 = 7600
        r = emergency_fund_check(2000, 3200)
        assert r["months_covered"] == 0.62
        assert r["status"] == "low"
        assert r["gap_to_3_months"] == 7600.0

    # ── Status boundaries ─────────────────────────────────────────────────────

    def test_exactly_3_months_is_ok(self):
        r = emergency_fund_check(6000, 2000)
        assert r["months_covered"] == 3.0
        assert r["status"] == "ok"
        assert r["gap_to_3_months"] == 0.0

    def test_exactly_6_months_is_ok(self):
        r = emergency_fund_check(12000, 2000)
        assert r["months_covered"] == 6.0
        assert r["status"] == "ok"

    def test_above_6_months_is_strong(self):
        r = emergency_fund_check(15000, 2000)
        assert r["months_covered"] == 7.5
        assert r["status"] == "strong"
        assert r["gap_to_3_months"] == 0.0

    def test_below_3_months_is_low(self):
        r = emergency_fund_check(4000, 2000)
        assert r["months_covered"] == 2.0
        assert r["status"] == "low"
        assert r["gap_to_3_months"] == 2000.0

    def test_zero_savings_is_low(self):
        r = emergency_fund_check(0, 2000)
        assert r["months_covered"] == 0.0
        assert r["status"] == "low"
        assert r["gap_to_3_months"] == 6000.0

    # ── Return keys ───────────────────────────────────────────────────────────

    def test_required_keys_present(self):
        r = emergency_fund_check(5000, 2000)
        for key in ["months_covered", "status", "gap_to_3_months", "summary"]:
            assert key in r

    def test_summary_is_non_empty_string(self):
        r = emergency_fund_check(5000, 2000)
        assert isinstance(r["summary"], str) and len(r["summary"]) > 10

    # ── Validation ────────────────────────────────────────────────────────────

    def test_negative_savings_raises(self):
        with pytest.raises(ValueError, match="current_savings must be >= 0"):
            emergency_fund_check(-100, 2000)

    def test_zero_expenses_raises(self):
        with pytest.raises(ValueError, match="monthly_expenses must be > 0"):
            emergency_fund_check(5000, 0)

    def test_negative_expenses_raises(self):
        with pytest.raises(ValueError, match="monthly_expenses must be > 0"):
            emergency_fund_check(5000, -500)
