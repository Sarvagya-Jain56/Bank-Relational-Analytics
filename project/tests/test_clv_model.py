"""
tests/test_clv_model.py

Unit tests for src/clv_model.py. Run with:
    pytest tests/ -v
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import pytest
from src.engagement_engine import engineer_features
from src.clv_model import (
    compute_annual_margin, compute_clv_by_group, revenue_at_risk_summary,
    simulate_intervention_roi, _expected_lifetime, MAX_EXPECTED_LIFETIME_YEARS,
)


@pytest.fixture
def sample_df():
    raw = pd.DataFrame({
        "CustomerId": [1, 2, 3, 4, 5, 6, 7, 8],
        "Surname": ["A", "B", "C", "D", "E", "F", "G", "H"],
        "CreditScore": [600, 650, 700, 750, 620, 680, 710, 590],
        "Geography": ["France", "Germany", "Spain", "France", "Germany", "Spain", "France", "Germany"],
        "Gender": ["Male", "Female", "Male", "Female", "Male", "Female", "Male", "Female"],
        "Age": [30, 40, 50, 35, 45, 55, 32, 60],
        "Tenure": [2, 5, 8, 1, 6, 9, 3, 4],
        "Balance": [0, 0, 0, 0, 100000, 150000, 200000, 300000],
        "NumOfProducts": [1, 2, 1, 2, 1, 2, 3, 4],
        "HasCrCard": [1, 0, 1, 0, 1, 0, 1, 0],
        "IsActiveMember": [1, 1, 0, 0, 1, 0, 1, 0],
        "EstimatedSalary": [40000, 50000, 60000, 70000, 80000, 90000, 100000, 110000],
        "Exited": [0, 0, 1, 1, 0, 1, 1, 1],
    })
    return engineer_features(raw)


class TestExpectedLifetime:
    def test_zero_churn_returns_cap(self):
        assert _expected_lifetime(0.0) == MAX_EXPECTED_LIFETIME_YEARS

    def test_full_churn_returns_one_year(self):
        assert _expected_lifetime(1.0) == pytest.approx(1.0)

    def test_low_churn_capped_at_max(self):
        # 1% churn -> 100 years uncapped, should be capped
        assert _expected_lifetime(0.01) == MAX_EXPECTED_LIFETIME_YEARS

    def test_never_negative_or_infinite(self):
        for c in [0.0, 0.001, 0.05, 0.2, 0.5, 1.0]:
            val = _expected_lifetime(c)
            assert val > 0
            assert val <= MAX_EXPECTED_LIFETIME_YEARS


class TestAnnualMargin:
    def test_adds_column(self, sample_df):
        out = compute_annual_margin(sample_df)
        assert "AnnualMargin" in out.columns

    def test_margin_is_nonnegative(self, sample_df):
        out = compute_annual_margin(sample_df)
        assert (out["AnnualMargin"] >= 0).all()

    def test_zero_balance_customer_still_has_product_fee_margin(self, sample_df):
        out = compute_annual_margin(sample_df)
        # CustomerId 1 has 0 balance but 1 product -> margin should equal the product fee, not zero
        row = out[out.CustomerId == 1].iloc[0]
        assert row["AnnualMargin"] > 0

    def test_does_not_mutate_input(self, sample_df):
        cols_before = list(sample_df.columns)
        compute_annual_margin(sample_df)
        assert list(sample_df.columns) == cols_before


class TestCLVByGroup:
    def test_returns_row_per_group(self, sample_df):
        result = compute_clv_by_group(sample_df, "EngagementSegment")
        assert set(result.index) <= {"Active Engaged", "Active Low-Product", "Inactive Disengaged", "Inactive Multi-Product"}

    def test_clv_is_positive(self, sample_df):
        result = compute_clv_by_group(sample_df, "EngagementSegment")
        assert (result["clv_per_customer"] > 0).all()

    def test_segment_total_equals_per_customer_times_count(self, sample_df):
        result = compute_clv_by_group(sample_df, "EngagementSegment")
        expected = result["clv_per_customer"] * result["customers"]
        pd.testing.assert_series_equal(result["segment_total_clv"], expected, check_names=False)


class TestRevenueAtRisk:
    def test_returns_all_keys(self, sample_df):
        summary = revenue_at_risk_summary(sample_df)
        for key in ["total_annual_margin", "overall_churn_rate", "expected_annual_revenue_loss",
                    "premium_at_risk_customers", "premium_at_risk_clv_per_customer", "premium_at_risk_total_clv"]:
            assert key in summary

    def test_revenue_loss_bounded_by_total_margin(self, sample_df):
        summary = revenue_at_risk_summary(sample_df)
        assert 0 <= summary["expected_annual_revenue_loss"] <= summary["total_annual_margin"]

    def test_handles_zero_premium_at_risk_customers(self):
        # A dataset where nobody qualifies as PremiumAtRisk should not crash
        raw = pd.DataFrame({
            "CustomerId": [1, 2], "Surname": ["A", "B"], "CreditScore": [600, 650],
            "Geography": ["France", "France"], "Gender": ["Male", "Male"], "Age": [30, 40],
            "Tenure": [2, 5], "Balance": [0, 0], "NumOfProducts": [1, 1], "HasCrCard": [1, 1],
            "IsActiveMember": [1, 1], "EstimatedSalary": [40000, 50000], "Exited": [0, 0],
        })
        df = engineer_features(raw)
        summary = revenue_at_risk_summary(df)
        assert summary["premium_at_risk_customers"] == 0
        assert summary["premium_at_risk_total_clv"] == 0


class TestInterventionROI:
    def test_returns_all_keys(self, sample_df):
        roi = simulate_intervention_roi(sample_df, sample_df["PremiumAtRisk"], cost_per_customer=50, churn_reduction_pp=0.05)
        for key in ["customers_targeted", "baseline_churn_rate", "clv_per_customer", "campaign_cost",
                    "expected_customers_retained", "expected_value_saved", "net_value", "roi_ratio"]:
            assert key in roi

    def test_campaign_cost_matches_targeted_count(self, sample_df):
        mask = sample_df["IsActiveMember"] == 1
        roi = simulate_intervention_roi(sample_df, mask, cost_per_customer=10, churn_reduction_pp=0.05)
        assert roi["campaign_cost"] == pytest.approx(roi["customers_targeted"] * 10)

    def test_empty_target_raises(self, sample_df):
        mask = sample_df["CustomerId"] > 9999  # matches nobody
        with pytest.raises(ValueError):
            simulate_intervention_roi(sample_df, mask, cost_per_customer=10, churn_reduction_pp=0.05)

    def test_zero_churn_reduction_means_zero_value_saved(self, sample_df):
        roi = simulate_intervention_roi(sample_df, sample_df["IsActiveMember"] == 1, cost_per_customer=10, churn_reduction_pp=0.0)
        assert roi["expected_value_saved"] == 0
        assert roi["net_value"] == -roi["campaign_cost"]
