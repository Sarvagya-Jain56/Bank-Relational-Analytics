import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.engagement_engine import load_and_engineer, compute_kpis, segment_summary

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.edgecolor": "#D1D5DB",
    "axes.linewidth": 0.8,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
})

GREEN, AMBER, RED, BLUE, MUTED = "#16A34A", "#D97706", "#DC2626", "#2563EB", "#6B7280"

df = load_and_engineer(os.path.join(os.path.dirname(__file__), "..", "data", "European_Bank.csv"))
kpis = compute_kpis(df)

def style_ax(ax, title):
    ax.set_title(title, fontsize=13, fontweight="bold", pad=12)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=1, decimals=0))
    ax.grid(axis="y", color="#E5E7EB", linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)

def bar_labels(ax, bars, fmt="{:.1%}"):
    for b in bars:
        h = b.get_height()
        ax.text(b.get_x()+b.get_width()/2, h+0.01, fmt.format(h),
                 ha="center", va="bottom", fontsize=10, fontweight="bold")

# 1. Churn by product count
fig, ax = plt.subplots(figsize=(7, 4.2))
prod = df.groupby("NumOfProducts")["Exited"].mean()
colors = [GREEN if v == prod.min() else (RED if v > 0.5 else AMBER) for v in prod.values]
bars = ax.bar(prod.index.astype(str), prod.values, color=colors, width=0.6, zorder=3)
style_ax(ax, "Churn Rate by Number of Products Held")
ax.set_xlabel("Products held")
bar_labels(ax, bars)
ax.set_ylim(0, 1.15)
plt.tight_layout()
plt.savefig("../assets/chart_products.png", dpi=170)
plt.close()

# 2. Churn by engagement segment
fig, ax = plt.subplots(figsize=(7.5, 4.2))
seg = segment_summary(df)["churn_rate"].sort_values(ascending=False)
colors = [RED, AMBER, AMBER, GREEN]
bars = ax.bar(seg.index, seg.values, color=colors[:len(seg)], zorder=3)
style_ax(ax, "Churn Rate by Engagement Segment")
plt.xticks(rotation=12, ha="right", fontsize=9.5)
bar_labels(ax, bars)
ax.set_ylim(0, max(seg.values)*1.25)
plt.tight_layout()
plt.savefig("../assets/chart_segments.png", dpi=170)
plt.close()

# 3. Churn by RSI tier
fig, ax = plt.subplots(figsize=(6.5, 4.2))
rsi = df.groupby("RSI_Tier")["Exited"].mean().reindex(["Weak", "Moderate", "Strong"])
bars = ax.bar(rsi.index, rsi.values, color=[RED, AMBER, GREEN], width=0.55, zorder=3)
style_ax(ax, "Churn Rate by Relationship Strength Tier")
bar_labels(ax, bars)
ax.set_ylim(0, max(rsi.values)*1.3)
plt.tight_layout()
plt.savefig("../assets/chart_rsi.png", dpi=170)
plt.close()

# 4. High balance myth-busting: churn by balance quartile
fig, ax = plt.subplots(figsize=(7, 4.2))
df["BalanceQuartile"] = pd.qcut(df["Balance"].rank(method="first"), 4, labels=["Q1 (lowest)", "Q2", "Q3", "Q4 (highest)"])
bq = df.groupby("BalanceQuartile", observed=True)["Exited"].mean()
bars = ax.bar(bq.index.astype(str), bq.values, color=BLUE, zorder=3)
style_ax(ax, "Churn Rate by Balance Quartile (Higher Balance \u2260 Safer)")
bar_labels(ax, bars)
ax.set_ylim(0, max(bq.values)*1.3)
plt.tight_layout()
plt.savefig("../assets/chart_balance_quartile.png", dpi=170)
plt.close()

# 5. Interaction: balance x activity
fig, ax = plt.subplots(figsize=(7.5, 4.2))
inter = df.groupby(["HighBalance", "IsActiveMember"])["Exited"].mean().unstack()
inter.index = ["Standard Balance", "High Balance (top 25%)"]
inter.columns = ["Inactive", "Active"]
x = range(len(inter))
w = 0.35
bars1 = ax.bar([i - w/2 for i in x], inter["Inactive"], width=w, label="Inactive", color=RED, zorder=3)
bars2 = ax.bar([i + w/2 for i in x], inter["Active"], width=w, label="Active", color=GREEN, zorder=3)
ax.set_xticks(list(x)); ax.set_xticklabels(inter.index)
style_ax(ax, "Churn: Balance Tier \u00d7 Activity Status")
bar_labels(ax, bars1); bar_labels(ax, bars2)
ax.legend(frameon=False)
ax.set_ylim(0, 0.42)
plt.tight_layout()
plt.savefig("../assets/chart_interaction.png", dpi=170)
plt.close()

# 6. Geography churn (secondary finding)
fig, ax = plt.subplots(figsize=(6.5, 4.2))
geo = df.groupby("Geography")["Exited"].mean().sort_values(ascending=False)
bars = ax.bar(geo.index, geo.values, color=[RED, AMBER, AMBER], zorder=3)
style_ax(ax, "Churn Rate by Geography")
bar_labels(ax, bars)
ax.set_ylim(0, max(geo.values)*1.3)
plt.tight_layout()
plt.savefig("../assets/chart_geography.png", dpi=170)
plt.close()

print("All charts generated.")

# 7. Effect size ranking (statistical validation)
from src.statistical_tests import run_full_report
report = run_full_report(df)
eff_rows = []
for r in report["categorical"]:
    eff_rows.append((r["predictor"], r["effect_size"], r["significant_at_0.05"], "Cramer's V"))
for r in report["continuous"]:
    eff_rows.append((r["predictor"], abs(r["effect_size"]), r["significant_at_0.05"], "Cohen's d"))
eff_df = pd.DataFrame(eff_rows, columns=["predictor", "effect", "sig", "metric"]).sort_values("effect", ascending=True)

fig, ax = plt.subplots(figsize=(7.5, 5))
colors = [BLUE if sig else MUTED for sig in eff_df["sig"]]
bars = ax.barh(eff_df["predictor"], eff_df["effect"], color=colors, zorder=3)
ax.set_title("Effect Size by Predictor (statistically significant in blue)", fontsize=13, fontweight="bold", pad=12)
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
ax.grid(axis="x", color="#E5E7EB", linewidth=0.8, zorder=0)
ax.set_axisbelow(True)
ax.set_xlabel("Effect size (Cramer's V for categorical, |Cohen's d| for continuous)")
for b, v in zip(bars, eff_df["effect"]):
    ax.text(v + 0.008, b.get_y()+b.get_height()/2, f"{v:.3f}", va="center", fontsize=9.5, fontweight="bold")
plt.tight_layout()
plt.savefig("../assets/chart_effect_sizes.png", dpi=170)
plt.close()
print("Effect size chart generated.")

# 8. CLV by engagement segment (Phase 4 - Business Impact)
from src.clv_model import compute_clv_by_group, revenue_at_risk_summary, simulate_intervention_roi

clv_seg = compute_clv_by_group(df, "EngagementSegment").sort_values("clv_per_customer", ascending=True)
fig, ax = plt.subplots(figsize=(7.5, 4.5))
bars = ax.barh(clv_seg.index, clv_seg["clv_per_customer"], color=BLUE, zorder=3)
ax.set_title("Customer Lifetime Value by Engagement Segment", fontsize=13, fontweight="bold", pad=12)
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
ax.grid(axis="x", color="#E5E7EB", linewidth=0.8, zorder=0); ax.set_axisbelow(True)
ax.set_xlabel("Estimated CLV per customer ($)")
for b, v in zip(bars, clv_seg["clv_per_customer"]):
    ax.text(v + 200, b.get_y()+b.get_height()/2, f"${v:,.0f}", va="center", fontsize=9.5, fontweight="bold")
ax.set_xlim(0, clv_seg["clv_per_customer"].max()*1.22)
plt.tight_layout()
plt.savefig("../assets/chart_clv_segment.png", dpi=170)
plt.close()

# 9. CLV by RSI tier
clv_rsi = compute_clv_by_group(df, "RSI_Tier").reindex(["Weak", "Moderate", "Strong"])
fig, ax = plt.subplots(figsize=(6.5, 4.2))
bars = ax.bar(clv_rsi.index, clv_rsi["clv_per_customer"], color=[RED, AMBER, GREEN], zorder=3)
ax.set_title("Customer Lifetime Value by Relationship Strength Tier", fontsize=13, fontweight="bold", pad=12)
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
ax.grid(axis="y", color="#E5E7EB", linewidth=0.8, zorder=0); ax.set_axisbelow(True)
ax.set_ylabel("Estimated CLV per customer ($)")
for b, v in zip(bars, clv_rsi["clv_per_customer"]):
    ax.text(b.get_x()+b.get_width()/2, v+300, f"${v:,.0f}", ha="center", fontsize=10, fontweight="bold")
ax.set_ylim(0, clv_rsi["clv_per_customer"].max()*1.2)
plt.tight_layout()
plt.savefig("../assets/chart_clv_rsi.png", dpi=170)
plt.close()

# 10. ROI simulation comparison (two illustrative campaigns)
roi1 = simulate_intervention_roi(df, df["PremiumAtRisk"], cost_per_customer=50, churn_reduction_pp=0.05)
roi2 = simulate_intervention_roi(df, df["EngagementSegment"]=="Inactive Disengaged", cost_per_customer=30, churn_reduction_pp=0.08)
labels = ["Premium At-Risk\noutreach ($50/cust,\n5pp reduction)", "Inactive Disengaged\nre-engagement ($30/cust,\n8pp reduction)"]
costs = [roi1["campaign_cost"], roi2["campaign_cost"]]
values = [roi1["expected_value_saved"], roi2["expected_value_saved"]]
fig, ax = plt.subplots(figsize=(7.5, 4.5))
x = range(len(labels)); w = 0.35
b1 = ax.bar([i-w/2 for i in x], costs, width=w, label="Campaign cost", color=MUTED, zorder=3)
b2 = ax.bar([i+w/2 for i in x], values, width=w, label="Expected value saved", color=GREEN, zorder=3)
ax.set_xticks(list(x)); ax.set_xticklabels(labels, fontsize=9)
ax.set_title("Illustrative Campaign ROI: Cost vs. Expected Value Saved", fontsize=13, fontweight="bold", pad=12)
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
ax.grid(axis="y", color="#E5E7EB", linewidth=0.8, zorder=0); ax.set_axisbelow(True)
ax.legend(frameon=False)
for b in list(b1)+list(b2):
    h = b.get_height()
    ax.text(b.get_x()+b.get_width()/2, h+15000, f"${h:,.0f}", ha="center", fontsize=8.5, fontweight="bold")
ax.set_ylim(0, max(values)*1.25)
plt.tight_layout()
plt.savefig("../assets/chart_roi_simulation.png", dpi=170)
plt.close()

print("CLV/ROI charts generated.")
print(f"revenue_at_risk_summary: {revenue_at_risk_summary(df)}")
