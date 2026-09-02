"""
tests/test_engagement_engine.py

Unit tests for src/engagement_engine.py. Run with:
    pytest tests/ -v
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import pytest
from src.engagement_engine import engineer_features, compute_kpis, segment_summary


@pytest.fixture
def sample_df():
    """A small, hand-built dataset with known, predictable properties."""
    return pd.DataFrame({
        "CustomerId": [1, 2, 3, 4, 5, 6, 7, 8],
        "Surname": ["A", "B", "C", "D", "E", "F", "G", "H"],
        "CreditScore": [600, 650, 700, 750, 620, 680, 710, 590],
        "Geography": ["France", "Germany", "Spain", "France", "Germany", "Spain", "France", "Germany"],
        "Gender": ["Male", "Female", "Male", "Female", "Male", "Female", "Male", "Female"],
        "Age": [30, 40, 50, 35, 45, 55, 32, 60],
        "Tenure": [2, 5, 8, 1, 6, 9, 3, 4],
        # engineered to give clean quartiles: 0, 0, 0, 0, 100k, 150k, 200k, 300k
        "Balance": [0, 0, 0, 0, 100000, 150000, 200000, 300000],
        "NumOfProducts": [1, 2, 1, 2, 1, 2, 3, 4],
        "HasCrCard": [1, 0, 1, 0, 1, 0, 1, 0],
        "IsActiveMember": [1, 1, 0, 0, 1, 0, 1, 0],
        "EstimatedSalary": [40000, 50000, 60000, 70000, 80000, 90000, 100000, 110000],
        "Exited": [0, 0, 1, 1, 0, 1, 1, 1],
    })


class TestEngineerFeatures:
    def test_adds_expected_columns(self, sample_df):
        out = engineer_features(sample_df)
        for col in ["HighBalance", "EngagementSegment", "PremiumAtRisk", "ProductDepthScore", "RSI", "RSI_Tier"]:
            assert col in out.columns

    def test_high_balance_is_top_quartile(self, sample_df):
        out = engineer_features(sample_df)
        # Top quartile of [0,0,0,0,100k,150k,200k,300k] should flag the highest values
        assert out.loc[out.CustomerId == 8, "HighBalance"].iloc[0] == True  # noqa: E712
        assert out.loc[out.CustomerId == 1, "HighBalance"].iloc[0] == False  # noqa: E712

    def test_engagement_segment_classification(self, sample_df):
        out = engineer_features(sample_df)
        seg = out.set_index("CustomerId")["EngagementSegment"]
        assert seg[1] == "Active Low-Product"       # active, 1 product
        assert seg[2] == "Active Engaged"           # active, 2 products
        assert seg[3] == "Inactive Disengaged"      # inactive, 1 product
        assert seg[4] == "Inactive Multi-Product"   # inactive, 2 products

    def test_engagement_segment_never_null(self, sample_df):
        out = engineer_features(sample_df)
        assert out["EngagementSegment"].isnull().sum() == 0

    def test_premium_at_risk_requires_both_conditions(self, sample_df):
        out = engineer_features(sample_df)
        # CustomerId 8: inactive AND high balance -> should be flagged
        assert out.loc[out.CustomerId == 8, "PremiumAtRisk"].iloc[0] == True  # noqa: E712
        # CustomerId 5: active AND high balance -> should NOT be flagged
        assert out.loc[out.CustomerId == 5, "PremiumAtRisk"].iloc[0] == False  # noqa: E712

    def test_rsi_bounded_zero_to_one(self, sample_df):
        out = engineer_features(sample_df)
        assert out["RSI"].between(0, 1).all()

    def test_rsi_tier_labels_valid(self, sample_df):
        out = engineer_features(sample_df)
        assert set(out["RSI_Tier"].unique()).issubset({"Weak", "Moderate", "Strong"})

    def test_does_not_mutate_input(self, sample_df):
        original_cols = list(sample_df.columns)
        engineer_features(sample_df)
        assert list(sample_df.columns) == original_cols


class TestComputeKPIs:
    def test_returns_all_required_kpis(self, sample_df):
        df = engineer_features(sample_df)
        kpis = compute_kpis(df)
        for key in [
            "overall_churn_rate", "engagement_retention_ratio", "product_depth_index",
            "high_balance_disengagement_ratio", "cc_stickiness_score_pp",
            "rsi_churn_by_tier", "rsi_correlation",
        ]:
            assert key in kpis

    def test_overall_churn_rate_matches_manual_calc(self, sample_df):
        df = engineer_features(sample_df)
        kpis = compute_kpis(df)
        expected = sample_df["Exited"].mean()
        assert kpis["overall_churn_rate"] == pytest.approx(expected)

    def test_churn_rate_is_a_valid_probability(self, sample_df):
        df = engineer_features(sample_df)
        kpis = compute_kpis(df)
        assert 0 <= kpis["overall_churn_rate"] <= 1

    def test_product_depth_index_has_entry_per_product_count(self, sample_df):
        df = engineer_features(sample_df)
        kpis = compute_kpis(df)
        assert set(kpis["product_depth_index"].keys()) == set(sample_df["NumOfProducts"].unique())


class TestSegmentSummary:
    def test_segment_counts_sum_to_total(self, sample_df):
        df = engineer_features(sample_df)
        summary = segment_summary(df)
        assert summary["customers"].sum() == len(sample_df)

    def test_all_churn_rates_valid(self, sample_df):
        df = engineer_features(sample_df)
        summary = segment_summary(df)
        assert summary["churn_rate"].between(0, 1).all()


class TestEdgeCases:
    def test_all_active_no_error(self, sample_df):
        df = sample_df.copy()
        df["IsActiveMember"] = 1
        out = engineer_features(df)
        assert (out["EngagementSegment"].isin(["Active Engaged", "Active Low-Product"])).all()

    def test_single_row_does_not_crash(self, sample_df):
        out = engineer_features(sample_df.iloc[[0]])
        assert len(out) == 1
