"""
engagement_engine.py

Single source of truth for the Customer Engagement & Product Utilization
Analytics project. All feature engineering, customer segmentation, and KPI
calculations live here so the Streamlit dashboard, the research paper, and
the executive summary always report identical numbers.

Usage:
    from engagement_engine import load_and_engineer, compute_kpis
    df = load_and_engineer("European_Bank.csv")
    kpis = compute_kpis(df)
"""

import pandas as pd
import numpy as np


def _safe_ratio(numerator: float, denominator: float) -> float:
    """Returns numerator/denominator, or NaN (never raises/warns) if denominator is 0."""
    if denominator == 0 or pd.isna(denominator):
        return float("nan")
    return numerator / denominator


# ---------------------------------------------------------------------------
# Data loading + feature engineering
# ---------------------------------------------------------------------------

def load_and_engineer(csv_path: str) -> pd.DataFrame:
    """Load the raw dataset and attach every derived field used downstream."""
    df = pd.read_csv(csv_path)
    df = engineer_features(df)
    return df


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # --- High balance flag: top quartile of Balance ("premium" customers) ---
    balance_q75 = df["Balance"].quantile(0.75)
    df["HighBalance"] = df["Balance"] >= balance_q75

    # --- Engagement classification (per project brief) ---
    def classify_engagement(row):
        active = row["IsActiveMember"] == 1
        multi_product = row["NumOfProducts"] >= 2
        if active and multi_product:
            return "Active Engaged"
        if active and not multi_product:
            return "Active Low-Product"
        if not active and not multi_product:
            return "Inactive Disengaged"
        return "Inactive Multi-Product"  # not active, 2+ products

    df["EngagementSegment"] = df.apply(classify_engagement, axis=1)

    # Cross-cutting premium-risk flag (used alongside, not instead of, the
    # four core segments above)
    df["PremiumAtRisk"] = (df["IsActiveMember"] == 0) & (df["HighBalance"])

    # --- Product Depth Score: retention rate by product count, min-max
    # normalized so 2-products (empirically the best) = 1.0 ---
    retention_by_products = 1 - df.groupby("NumOfProducts")["Exited"].transform("mean")
    df["_ret_by_prod_raw"] = retention_by_products
    pmin, pmax = df["_ret_by_prod_raw"].min(), df["_ret_by_prod_raw"].max()
    df["ProductDepthScore"] = (df["_ret_by_prod_raw"] - pmin) / (pmax - pmin)
    df.drop(columns=["_ret_by_prod_raw"], inplace=True)

    # --- Relationship Strength Index (RSI): composite of engagement +
    # product depth, equally weighted, scaled 0-1 ---
    df["RSI"] = 0.5 * df["IsActiveMember"] + 0.5 * df["ProductDepthScore"]

    def rsi_tier(x):
        if x < 0.40:
            return "Weak"
        elif x < 0.75:
            return "Moderate"
        return "Strong"

    df["RSI_Tier"] = df["RSI"].apply(rsi_tier)

    return df


# ---------------------------------------------------------------------------
# KPI calculations
# ---------------------------------------------------------------------------

def compute_kpis(df: pd.DataFrame) -> dict:
    """Returns the 5 required KPIs plus supporting breakdowns, all as plain
    Python values/DataFrames ready to display."""

    overall_churn = df["Exited"].mean()

    # 1. Engagement Retention Ratio
    active_retention = 1 - df.loc[df.IsActiveMember == 1, "Exited"].mean()
    inactive_retention = 1 - df.loc[df.IsActiveMember == 0, "Exited"].mean()
    engagement_retention_ratio = _safe_ratio(active_retention, inactive_retention)

    # 2. Product Depth Index (retention rate by product count)
    product_depth_index = (1 - df.groupby("NumOfProducts")["Exited"].mean()).to_dict()

    # 3. High-Balance Disengagement Ratio
    premium_at_risk_churn = df.loc[df.PremiumAtRisk, "Exited"].mean()
    high_balance_disengagement_ratio = _safe_ratio(premium_at_risk_churn, overall_churn)

    # 4. Credit Card Stickiness Score (percentage-point retention difference)
    cc_retention = 1 - df.loc[df.HasCrCard == 1, "Exited"].mean()
    no_cc_retention = 1 - df.loc[df.HasCrCard == 0, "Exited"].mean()
    cc_stickiness_score_pp = (cc_retention - no_cc_retention) * 100

    # 5. Relationship Strength Index (tiered churn + correlation)
    rsi_churn_by_tier = df.groupby("RSI_Tier")["Exited"].mean().reindex(
        ["Weak", "Moderate", "Strong"]
    ).to_dict()
    rsi_correlation = df["RSI"].corr(df["Exited"])

    return {
        "overall_churn_rate": overall_churn,
        "engagement_retention_ratio": engagement_retention_ratio,
        "product_depth_index": product_depth_index,
        "high_balance_disengagement_ratio": high_balance_disengagement_ratio,
        "cc_stickiness_score_pp": cc_stickiness_score_pp,
        "rsi_churn_by_tier": rsi_churn_by_tier,
        "rsi_correlation": rsi_correlation,
    }


def segment_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Count, churn rate, avg balance, avg salary per EngagementSegment."""
    g = df.groupby("EngagementSegment").agg(
        customers=("CustomerId", "count"),
        churn_rate=("Exited", "mean"),
        avg_balance=("Balance", "mean"),
        avg_salary=("EstimatedSalary", "mean"),
    )
    g["share_of_base"] = g["customers"] / len(df)
    return g.sort_values("churn_rate", ascending=False)


if __name__ == "__main__":
    import os
    csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "European_Bank.csv")
    df = load_and_engineer(csv_path)
    kpis = compute_kpis(df)
    print("Overall churn:", round(kpis["overall_churn_rate"], 4))
    print("Engagement Retention Ratio:", round(kpis["engagement_retention_ratio"], 3))
    print("Product Depth Index:", {k: round(v, 3) for k, v in kpis["product_depth_index"].items()})
    print("High-Balance Disengagement Ratio:", round(kpis["high_balance_disengagement_ratio"], 3))
    print("CC Stickiness Score (pp):", round(kpis["cc_stickiness_score_pp"], 2))
    print("RSI churn by tier:", {k: round(v, 3) for k, v in kpis["rsi_churn_by_tier"].items()})
    print("RSI correlation:", round(kpis["rsi_correlation"], 3))
    print()
    print(segment_summary(df))
