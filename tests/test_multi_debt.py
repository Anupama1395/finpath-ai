"""tests/test_multi_debt.py — Tests for multi_debt_plan."""
import pytest
from tools.core.finance import multi_debt_plan

# Helpers
DEBTS_2 = [
    {"name": "Credit Card", "balance": 3000, "apr": 0.20, "min_payment": 60},
    {"name": "Student Loan", "balance": 8000, "apr": 0.06, "min_payment": 150},
]
DEBTS_3 = [
    {"name": "Card A", "balance": 2000, "apr": 0.22, "min_payment": 40},
    {"name": "Car Loan",  "balance": 5000, "apr": 0.08, "min_payment": 120},
    {"name": "Medical",   "balance": 1500, "apr": 0.00, "min_payment": 75},
]

# ── Structure ─────────────────────────────────────────────────────────────────

def test_returns_all_keys():
    r = multi_debt_plan(DEBTS_2)
    assert {"avalanche","snowball","better_strategy","interest_saved","summary"} == set(r.keys())

def test_avalanche_keys():
    r = multi_debt_plan(DEBTS_2)
    assert {"payoff_order","months","total_interest"} == set(r["avalanche"].keys())

def test_summary_is_string():
    r = multi_debt_plan(DEBTS_2)
    assert isinstance(r["summary"], str) and len(r["summary"]) > 20

# ── Correctness ───────────────────────────────────────────────────────────────

def test_avalanche_pays_high_apr_first():
    # Credit Card (20% APR) should be paid first in avalanche
    r = multi_debt_plan(DEBTS_2, extra_monthly=200)
    assert r["avalanche"]["payoff_order"][0] == "Credit Card"

def test_snowball_pays_small_balance_first():
    # Medical ($1500) is smallest — paid first in snowball
    r = multi_debt_plan(DEBTS_3, extra_monthly=200)
    assert r["snowball"]["payoff_order"][0] == "Medical"

def test_avalanche_saves_more_interest_than_snowball():
    # With high-APR debt, avalanche generally saves more interest
    r = multi_debt_plan(DEBTS_2, extra_monthly=200)
    assert r["avalanche"]["total_interest"] <= r["snowball"]["total_interest"]

def test_better_strategy_matches_interest():
    r = multi_debt_plan(DEBTS_2, extra_monthly=200)
    av = r["avalanche"]["total_interest"]
    sn = r["snowball"]["total_interest"]
    if av < sn:
        assert r["better_strategy"] == "avalanche"
    elif sn < av:
        assert r["better_strategy"] == "snowball"
    else:
        assert r["better_strategy"] == "tie"

def test_interest_saved_nonnegative():
    r = multi_debt_plan(DEBTS_2, extra_monthly=100)
    assert r["interest_saved"] >= 0

def test_single_debt():
    single = [{"name": "Only debt", "balance": 5000, "apr": 0.10, "min_payment": 200}]
    r = multi_debt_plan(single, extra_monthly=0)
    # Avalanche and snowball identical with one debt
    assert r["avalanche"]["months"] == r["snowball"]["months"]
    assert r["better_strategy"] == "tie"

def test_no_extra_payment():
    r = multi_debt_plan(DEBTS_2, extra_monthly=0)
    assert r["avalanche"]["months"] > 0
    assert r["snowball"]["months"] > 0

def test_large_extra_payment_faster():
    r_small = multi_debt_plan(DEBTS_2, extra_monthly=0)
    r_large = multi_debt_plan(DEBTS_2, extra_monthly=500)
    assert r_large["avalanche"]["months"] < r_small["avalanche"]["months"]

def test_zero_apr_debt():
    debts = [
        {"name": "0% card",   "balance": 2000, "apr": 0.00, "min_payment": 100},
        {"name": "High card", "balance": 2000, "apr": 0.20, "min_payment": 100},
    ]
    r = multi_debt_plan(debts, extra_monthly=200)
    # Avalanche: high card first. Snowball: tie (same balance) — first listed wins
    assert r["avalanche"]["payoff_order"][0] == "High card"

def test_three_debts_all_paid():
    r = multi_debt_plan(DEBTS_3, extra_monthly=300)
    assert len(r["avalanche"]["payoff_order"]) == 3
    assert len(r["snowball"]["payoff_order"]) == 3

# ── Validation ────────────────────────────────────────────────────────────────

def test_empty_debts():
    with pytest.raises(ValueError, match="must not be empty"):
        multi_debt_plan([])

def test_too_many_debts():
    debts = [{"name": f"D{i}", "balance": 1000, "apr": 0.1, "min_payment": 50}
             for i in range(11)]
    with pytest.raises(ValueError, match="maximum 10"):
        multi_debt_plan(debts)

def test_negative_extra():
    with pytest.raises(ValueError, match="extra_monthly must be >= 0"):
        multi_debt_plan(DEBTS_2, extra_monthly=-1)

def test_missing_key():
    with pytest.raises(ValueError, match="missing required key"):
        multi_debt_plan([{"name": "X", "balance": 1000, "apr": 0.1}])

def test_negative_balance():
    with pytest.raises(ValueError, match="balance must be >= 0"):
        multi_debt_plan([{"name": "X", "balance": -1, "apr": 0.1, "min_payment": 50}])

def test_zero_min_payment():
    with pytest.raises(ValueError, match="min_payment must be > 0"):
        multi_debt_plan([{"name": "X", "balance": 1000, "apr": 0.1, "min_payment": 0}])
