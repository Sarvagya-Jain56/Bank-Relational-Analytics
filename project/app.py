"""
Customer Engagement & Product Utilization Analytics Dashboard
---------------------------------------------------------------
Run locally with:
    pip install -r requirements.txt
    streamlit run app.py

Expects: data/European_Bank.csv, src/engagement_engine.py, src/statistical_tests.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.engagement_engine import load_and_engineer, compute_kpis, segment_summary
from src.statistical_tests import run_full_report, format_p

# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Engagement & Retention Analytics", page_icon="\U0001F3E6", layout="wide")

PRIMARY = "#2563EB"
DANGER = "#DC2626"
WARN = "#D97706"
GOOD = "#16A34A"
MUTED = "#6B7280"

st.markdown("<style>[data-testid='stMetricValue']{font-size:1.7rem;} .block-container{padding-top:1.5rem;}</style>", unsafe_allow_html=True)

import os base_dir = os.path.dirname(os.path.abspath(__file__)) DATA_PATH = os.path.join(BASE_DIR, "data", "European_Bank.csv") @st.cache_data def get_data(): return load_and_engineer(DATA_PATH)


@st.cache_data
def get_stats_report(_df):
    return run_full_report(_df)


df_full = get_data()

# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------
st.sidebar.title("Filters")
engagement_options = ["All"] + sorted(df_full["EngagementSegment"].unique().tolist())
engagement_choice = st.sidebar.selectbox("Engagement segment", engagement_options)
product_range = st.sidebar.slider("Number of products", int(df_full.NumOfProducts.min()), int(df_full.NumOfProducts.max()),
                                   (int(df_full.NumOfProducts.min()), int(df_full.NumOfProducts.max())))
balance_range = st.sidebar.slider("Balance range ($)", float(df_full.Balance.min()), float(df_full.Balance.max()),
                                   (float(df_full.Balance.min()), float(df_full.Balance.max())), step=1000.0, format="%.0f")
salary_range = st.sidebar.slider("Estimated salary range ($)", float(df_full.EstimatedSalary.min()), float(df_full.EstimatedSalary.max()),
                                  (float(df_full.EstimatedSalary.min()), float(df_full.EstimatedSalary.max())), step=1000.0, format="%.0f")
geo_options = ["All"] + sorted(df_full["Geography"].unique().tolist())
geo_choice = st.sidebar.selectbox("Geography", geo_options)

df = df_full.copy()
if engagement_choice != "All":
    df = df[df.EngagementSegment == engagement_choice]
if geo_choice != "All":
    df = df[df.Geography == geo_choice]
df = df[df.NumOfProducts.between(*product_range) & df.Balance.between(*balance_range) & df.EstimatedSalary.between(*salary_range)]
st.sidebar.markdown(f"**{len(df):,}** customers match filters")

if len(df) == 0:
    st.warning("No customers match the current filters. Widen your ranges in the sidebar.")
    st.stop()

kpis = compute_kpis(df)

# ---------------------------------------------------------------------------
# Header + KPI row
# ---------------------------------------------------------------------------
st.title("Customer Engagement & Product Utilization Analytics")
st.caption("Retention strategy analysis \u2014 behavior and relationship depth, not just demographics")

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Churn Rate (filtered)", f"{kpis['overall_churn_rate']:.1%}")
k2.metric("Engagement Retention Ratio", f"{kpis['engagement_retention_ratio']:.2f}x")
k3.metric("High-Balance Disengagement Ratio", f"{kpis['high_balance_disengagement_ratio']:.2f}x")
k4.metric("CC Stickiness Score", f"{kpis['cc_stickiness_score_pp']:+.1f} pp")
best_product = max(kpis["product_depth_index"], key=kpis["product_depth_index"].get)
k5.metric("Best-Retention Product Count", f"{best_product} products")

st.divider()

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Engagement vs Churn Overview", "Product Utilization Impact",
    "High-Value Disengaged Detector", "Retention Strength Scoring",
    "Statistical Validation",
])

with tab1:
    col1, col2 = st.columns([3, 2])
    with col1:
        seg = segment_summary(df).reset_index()
        fig = px.bar(seg, x="EngagementSegment", y="churn_rate", color="churn_rate",
                     color_continuous_scale=[GOOD, WARN, DANGER], text=seg["churn_rate"].map(lambda v: f"{v:.1%}"),
                     labels={"churn_rate": "Churn Rate", "EngagementSegment": "Segment"}, title="Churn Rate by Engagement Segment")
        fig.update_traces(textposition="outside")
        fig.update_layout(yaxis_tickformat=".0%", coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        active_churn = df.loc[df.IsActiveMember == 1, "Exited"].mean()
        inactive_churn = df.loc[df.IsActiveMember == 0, "Exited"].mean()
        fig2 = go.Figure(go.Bar(x=["Active", "Inactive"], y=[active_churn, inactive_churn], marker_color=[GOOD, DANGER],
                                 text=[f"{active_churn:.1%}", f"{inactive_churn:.1%}"], textposition="outside"))
        fig2.update_layout(title="Churn: Active vs Inactive", yaxis_tickformat=".0%")
        st.plotly_chart(fig2, use_container_width=True)
    st.subheader("Segment detail")
    display_seg = segment_summary(df).reset_index()
    display_seg["churn_rate"] = display_seg["churn_rate"].map(lambda v: f"{v:.1%}")
    display_seg["share_of_base"] = display_seg["share_of_base"].map(lambda v: f"{v:.1%}")
    display_seg["avg_balance"] = display_seg["avg_balance"].map(lambda v: f"${v:,.0f}")
    display_seg["avg_salary"] = display_seg["avg_salary"].map(lambda v: f"${v:,.0f}")
    st.dataframe(display_seg, use_container_width=True, hide_index=True)

with tab2:
    prod_churn = df.groupby("NumOfProducts")["Exited"].agg(["count", "mean"]).reset_index()
    prod_churn.columns = ["NumOfProducts", "Customers", "ChurnRate"]
    fig3 = px.bar(prod_churn, x="NumOfProducts", y="ChurnRate", text=prod_churn["ChurnRate"].map(lambda v: f"{v:.1%}"),
                  color="ChurnRate", color_continuous_scale=[GOOD, WARN, DANGER],
                  title="Churn Rate by Number of Products (the 'sweet spot' effect)",
                  labels={"ChurnRate": "Churn Rate", "NumOfProducts": "Products Held"})
    fig3.update_traces(textposition="outside")
    fig3.update_layout(yaxis_tickformat=".0%", coloraxis_showscale=False)
    st.plotly_chart(fig3, use_container_width=True)
    st.info("2 products is the retention sweet spot. 3-4 products correlates with dramatically higher churn \u2014 "
            "consistent with over-selling or bundling customers into products they didn't want, rather than genuine loyalty.")
    col3, col4 = st.columns(2)
    with col3:
        st.metric("Customers with 3-4 products", f"{(df.NumOfProducts>=3).sum():,}")
    with col4:
        risky = df[df.NumOfProducts >= 3]
        st.metric("Their churn rate", f"{(risky['Exited'].mean() if len(risky) else 0):.1%}")
    st.subheader("Single vs multi-product retention")
    single_vs_multi = df.assign(Bucket=df.NumOfProducts.map(lambda n: "1 product" if n == 1 else "2+ products")).groupby("Bucket")["Exited"].mean().reset_index()
    fig4 = px.bar(single_vs_multi, x="Bucket", y="Exited", text=single_vs_multi["Exited"].map(lambda v: f"{v:.1%}"))
    fig4.update_traces(textposition="outside", marker_color=PRIMARY)
    fig4.update_layout(yaxis_tickformat=".0%", yaxis_title="Churn Rate")
    st.plotly_chart(fig4, use_container_width=True)

with tab3:
    st.subheader("At-risk premium customers: inactive + high balance")
    at_risk = df[df.PremiumAtRisk].sort_values("Balance", ascending=False)
    c1, c2, c3 = st.columns(3)
    c1.metric("At-risk premium customers", f"{len(at_risk):,}")
    c2.metric("Their churn rate", f"{at_risk['Exited'].mean():.1%}" if len(at_risk) else "n/a")
    c3.metric("Total balance at risk", f"${at_risk['Balance'].sum():,.0f}")
    st.dataframe(at_risk[["CustomerId", "Surname", "Geography", "Age", "Balance", "EstimatedSalary", "NumOfProducts", "Tenure", "Exited"]]
                 .rename(columns={"Exited": "AlreadyChurned"}), use_container_width=True, hide_index=True, height=350)
    fig5 = px.scatter(df, x="Balance", y="EstimatedSalary", color="EngagementSegment", symbol="Exited", opacity=0.6,
                       title="Balance vs Salary, colored by engagement segment", labels={"Exited": "Churned"})
    st.plotly_chart(fig5, use_container_width=True)

with tab4:
    st.subheader("Relationship Strength Index (RSI)")
    st.caption("RSI = 0.5 x Active-membership + 0.5 x Product-Depth-Score (0-1 scale)")
    rsi_churn = df.groupby("RSI_Tier")["Exited"].agg(["count", "mean"]).reindex(["Weak", "Moderate", "Strong"]).reset_index()
    rsi_churn.columns = ["Tier", "Customers", "ChurnRate"]
    fig6 = px.bar(rsi_churn, x="Tier", y="ChurnRate", text=rsi_churn["ChurnRate"].map(lambda v: f"{v:.1%}"),
                  color="Tier", color_discrete_map={"Weak": DANGER, "Moderate": WARN, "Strong": GOOD},
                  title="Churn Rate by Relationship Strength Tier")
    fig6.update_traces(textposition="outside")
    fig6.update_layout(yaxis_tickformat=".0%", showlegend=False)
    st.plotly_chart(fig6, use_container_width=True)
    fig7 = px.histogram(df, x="RSI", nbins=30, color="RSI_Tier",
                         color_discrete_map={"Weak": DANGER, "Moderate": WARN, "Strong": GOOD},
                         title="Distribution of Relationship Strength Index")
    st.plotly_chart(fig7, use_container_width=True)
    st.subheader("Look up a customer")
    cust_id = st.selectbox("CustomerId", df["CustomerId"].tolist())
    row = df[df.CustomerId == cust_id].iloc[0]
    lc1, lc2, lc3, lc4 = st.columns(4)
    lc1.metric("Engagement Segment", row.EngagementSegment)
    lc2.metric("RSI Score", f"{row.RSI:.2f}")
    lc3.metric("RSI Tier", row.RSI_Tier)
    lc4.metric("Churned?", "Yes" if row.Exited == 1 else "No")

with tab5:
    st.subheader("Formal statistical validation")
    st.caption("Every driver above is tested for statistical significance, not just eyeballed from percentages. "
               "Computed on the full 10,000-row dataset (filters do not apply here \u2014 significance testing needs the full sample).")

    report = get_stats_report(df_full)

    st.markdown("**Categorical predictors** \u2014 Chi-square test of independence")
    cat_rows = []
    for r in report["categorical"]:
        cat_rows.append({
            "Predictor": r["predictor"], "\u03c7\u00b2": r["statistic"], "p-value": format_p(r["p_value"]),
            "Effect size (Cramer's V)": r["effect_size"], "Effect": r["effect_label"],
            "Significant (\u03b1=0.05)": "Yes" if r["significant_at_0.05"] else "No",
        })
    st.dataframe(pd.DataFrame(cat_rows), use_container_width=True, hide_index=True)

    st.markdown("**Continuous predictors** \u2014 Welch's t-test (churned vs retained)")
    cont_rows = []
    for r in report["continuous"]:
        cont_rows.append({
            "Predictor": r["predictor"], "Mean (churned)": r["mean_churned"], "Mean (retained)": r["mean_retained"],
            "t-statistic": r["statistic"], "p-value": format_p(r["p_value"]),
            "Effect size (Cohen's d)": r["effect_size"], "Effect": r["effect_label"],
            "Significant (\u03b1=0.05)": "Yes" if r["significant_at_0.05"] else "No",
        })
    st.dataframe(pd.DataFrame(cont_rows), use_container_width=True, hide_index=True)

    st.info(
        "**Reading this table**: statistical significance (p < 0.05) tells you a relationship is real and not "
        "due to chance. Effect size tells you if it's *big enough to act on*. CreditScore, for example, is "
        "statistically significant here purely because the sample is large (10,000 rows) \u2014 but its effect size "
        "is negligible, so it isn't a useful lever for retention strategy. NumOfProducts has both significance "
        "and the largest effect size of any categorical driver \u2014 that's why it's the headline finding."
    )
