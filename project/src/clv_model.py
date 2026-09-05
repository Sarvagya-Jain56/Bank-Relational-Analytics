"""
clv_model.py

Customer Lifetime Value (CLV) and revenue-at-risk modeling.

IMPORTANT / HONESTY NOTE:
This dataset does not include actual revenue, margin, or cost figures — banks
don't disclose per-customer profitability in a public dataset. Every dollar
figure this module produces is built from clearly labeled, adjustable
assumptions (a net-interest-margin rate and a flat per-product fee), not real
bank financials. Treat every number here as illustrative and directional --
useful for comparing segments against each other -- not as an audited figure.
All assumptions are centralized below so they can be changed in one place.

CLV formula used (standard "margin / churn rate" approach from marketing
analytics): a segment's expected customer lifetime, in years, is
1 / annual_churn_rate. Multiply by that segment's average annual margin to
get CLV. This is a simplification (assumes constant churn rate over the
customer's lifetime, no discounting for the time value of money) but is a
widely used, defensible baseline when a full survival model isn't available.
"""

import pandas as pd

# ---- Assumptions (override these to match real bank economics if available) ----
DEFAULT_ANNUAL_NIM_RATE = 0.025        # 2.5% net interest margin on balance (typical retail bank range: 2-4%)
DEFAULT_ANNUAL_FEE_PER_PRODUCT = 150   # illustrative average annual fee/margin per product held
MAX_EXPECTED_LIFETIME_YEARS = 20       # cap for near-zero-churn segments, avoids unrealistic near-infinite CLV


def compute_annual_margin(df: pd.DataFrame, nim_rate: float = DEFAULT_ANNUAL_NIM_RATE,
                           fee_per_product: float = DEFAULT_ANNUAL_FEE_PER_PRODUCT) -> pd.DataFrame:
    """Adds an AnnualMargin column: estimated annual contribution margin per customer."""
    df = df.copy()
    df["AnnualMargin"] = df["Balance"] * nim_rate + df["NumOfProducts"] * fee_per_product
    return df


def _expected_lifetime(churn_rate: float) -> float:
    if churn_rate <= 0:
        return float(MAX_EXPECTED_LIFETIME_YEARS)
    return float(min(1.0 / churn_rate, MAX_EXPECTED_LIFETIME_YEARS))


def compute_clv_by_group(df: pd.DataFrame, group_col: str, nim_rate: float = DEFAULT_ANNUAL_NIM_RATE,
                          fee_per_product: float = DEFAULT_ANNUAL_FEE_PER_PRODUCT) -> pd.DataFrame:
    """CLV, aggregated by any grouping column (e.g. EngagementSegment, RSI_Tier, Geography)."""
    df = compute_annual_margin(df, nim_rate, fee_per_product)
    g = df.groupby(group_col).agg(
        customers=("CustomerId", "count"),
        churn_rate=("Exited", "mean"),
        avg_annual_margin=("AnnualMargin", "mean"),
    )
    g["expected_lifetime_years"] = g["churn_rate"].apply(_expected_lifetime)
    g["clv_per_customer"] = g["avg_annual_margin"] * g["expected_lifetime_years"]
    g["segment_total_clv"] = g["clv_per_customer"] * g["customers"]
    return g.sort_values("clv_per_customer", ascending=False)


def revenue_at_risk_summary(df: pd.DataFrame, nim_rate: float = DEFAULT_ANNUAL_NIM_RATE,
                             fee_per_product: float = DEFAULT_ANNUAL_FEE_PER_PRODUCT) -> dict:
    """Portfolio-level revenue exposure: what churn is costing annually, and what's at stake
    in the highest-risk segment (inactive + high balance, defined in engagement_engine.py)."""
    df = compute_annual_margin(df, nim_rate, fee_per_product)
    total_annual_margin = df["AnnualMargin"].sum()
    overall_churn = df["Exited"].mean()
    expected_annual_revenue_loss = total_annual_margin * overall_churn

    premium_at_risk = df[df["PremiumAtRisk"]]
    premium_churn = premium_at_risk["Exited"].mean() if len(premium_at_risk) else 0.0
    premium_lifetime = _expected_lifetime(premium_churn)
    premium_avg_margin = premium_at_risk["AnnualMargin"].mean() if len(premium_at_risk) else 0.0
    premium_clv_per_customer = premium_avg_margin * premium_lifetime
    premium_total_clv = premium_clv_per_customer * len(premium_at_risk)

    return {
        "total_annual_margin": float(total_annual_margin),
        "overall_churn_rate": float(overall_churn),
        "expected_annual_revenue_loss": float(expected_annual_revenue_loss),
        "premium_at_risk_customers": int(len(premium_at_risk)),
        "premium_at_risk_clv_per_customer": float(premium_clv_per_customer),
        "premium_at_risk_total_clv": float(premium_total_clv),
    }


def simulate_intervention_roi(df: pd.DataFrame, target_mask: pd.Series, cost_per_customer: float,
                               churn_reduction_pp: float, nim_rate: float = DEFAULT_ANNUAL_NIM_RATE,
                               fee_per_product: float = DEFAULT_ANNUAL_FEE_PER_PRODUCT) -> dict:
    """
    Estimates the ROI of a hypothetical retention campaign.

    target_mask: boolean mask selecting the customers the campaign is aimed at
    cost_per_customer: $ cost to run the campaign per targeted customer (outreach, incentive, etc.)
    churn_reduction_pp: assumed reduction in churn probability for targeted customers,
                         expressed as a fraction (e.g. 0.05 = 5 percentage points)

    This is a what-if calculator, not a forecast: churn_reduction_pp must be supplied
    as an assumption (from a pilot test, industry benchmark, or judgment call) --
    the model has no way to know how effective an untested campaign will be.
    """
    df = compute_annual_margin(df, nim_rate, fee_per_product)
    targeted = df[target_mask]
    n_targeted = len(targeted)
    if n_targeted == 0:
        raise ValueError("target_mask selects zero customers")

    churn_rate = targeted["Exited"].mean()
    lifetime = _expected_lifetime(churn_rate)
    avg_margin = targeted["AnnualMargin"].mean()
    clv_per_customer = avg_margin * lifetime

    campaign_cost = n_targeted * cost_per_customer
    expected_customers_retained = n_targeted * churn_reduction_pp
    expected_value_saved = expected_customers_retained * clv_per_customer
    net_value = expected_value_saved - campaign_cost
    roi_ratio = (net_value / campaign_cost) if campaign_cost > 0 else float("nan")

    return {
        "customers_targeted": int(n_targeted),
        "baseline_churn_rate": float(churn_rate),
        "clv_per_customer": float(clv_per_customer),
        "campaign_cost": float(campaign_cost),
        "expected_customers_retained": float(expected_customers_retained),
        "expected_value_saved": float(expected_value_saved),
        "net_value": float(net_value),
        "roi_ratio": float(roi_ratio),
    }


if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from src.engagement_engine import load_and_engineer

    csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "European_Bank.csv")
    df = load_and_engineer(csv_path)

    print("=" * 78)
    print("REVENUE AT RISK SUMMARY (illustrative assumptions: 2.5% NIM, $150/product/yr)")
    print("=" * 78)
    summary = revenue_at_risk_summary(df)
    for k, v in summary.items():
        print(f"{k:<38} {v:,.4f}" if isinstance(v, float) else f"{k:<38} {v}")

    print()
    print("=" * 78)
    print("CLV BY ENGAGEMENT SEGMENT")
    print("=" * 78)
    print(compute_clv_by_group(df, "EngagementSegment").round(2).to_string())

    print()
    print("=" * 78)
    print("CLV BY RSI TIER")
    print("=" * 78)
    print(compute_clv_by_group(df, "RSI_Tier").round(2).to_string())

    print()
    print("=" * 78)
    print("ROI SIMULATION: outreach to Premium At-Risk customers")
    print("Assumption: $50/customer campaign cost, 5pp churn reduction")
    print("=" * 78)
    roi = simulate_intervention_roi(df, df["PremiumAtRisk"], cost_per_customer=50, churn_reduction_pp=0.05)
    for k, v in roi.items():
        print(f"{k:<32} {v:,.2f}" if isinstance(v, float) else f"{k:<32} {v}")

    print()
    print("=" * 78)
    print("ROI SIMULATION: re-engagement campaign for Inactive Disengaged segment")
    print("Assumption: $30/customer campaign cost, 8pp churn reduction")
    print("=" * 78)
    mask = df["EngagementSegment"] == "Inactive Disengaged"
    roi2 = simulate_intervention_roi(df, mask, cost_per_customer=30, churn_reduction_pp=0.08)
    for k, v in roi2.items():
        print(f"{k:<32} {v:,.2f}" if isinstance(v, float) else f"{k:<32} {v}")
