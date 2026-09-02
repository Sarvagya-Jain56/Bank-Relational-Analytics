"""
statistical_tests.py

Formal hypothesis testing for every driver identified in the EDA.
Categorical predictors -> Chi-square test of independence + Cramer's V (effect size)
Continuous predictors  -> Welch's t-test (unequal variance) + Cohen's d (effect size)

Run directly to print a full significance report:
    python src/statistical_tests.py
"""
import json
import numpy as np
import pandas as pd
from scipy import stats

CATEGORICAL_PREDICTORS = ["Geography", "Gender", "HasCrCard", "IsActiveMember", "NumOfProducts"]
CONTINUOUS_PREDICTORS = ["CreditScore", "Age", "Tenure", "Balance", "EstimatedSalary"]


def cramers_v(confusion_matrix: np.ndarray) -> float:
    chi2 = stats.chi2_contingency(confusion_matrix)[0]
    n = confusion_matrix.sum()
    r, k = confusion_matrix.shape
    return float(np.sqrt((chi2 / n) / (min(r - 1, k - 1) or 1)))


def cohens_d(a: pd.Series, b: pd.Series) -> float:
    n1, n2 = len(a), len(b)
    pooled_std = np.sqrt(((n1 - 1) * a.std() ** 2 + (n2 - 1) * b.std() ** 2) / (n1 + n2 - 2))
    return float((a.mean() - b.mean()) / pooled_std) if pooled_std else 0.0


def effect_label(kind: str, value: float) -> str:
    value = abs(value)
    if kind == "cramers_v":
        if value < 0.10: return "negligible"
        if value < 0.20: return "small"
        if value < 0.40: return "moderate"
        return "large"
    if kind == "cohens_d":
        if value < 0.20: return "negligible"
        if value < 0.50: return "small"
        if value < 0.80: return "medium"
        return "large"
    return "n/a"


def run_categorical_tests(df: pd.DataFrame) -> list:
    results = []
    for col in CATEGORICAL_PREDICTORS:
        ct = pd.crosstab(df[col], df["Exited"])
        chi2, p, dof, _ = stats.chi2_contingency(ct)
        v = cramers_v(ct.values)
        results.append({
            "predictor": col, "test": "Chi-square test of independence",
            "statistic": round(float(chi2), 3), "dof": int(dof), "p_value": p,
            "effect_size_metric": "Cramer's V", "effect_size": round(v, 3),
            "effect_label": effect_label("cramers_v", v),
            "significant_at_0.05": bool(p < 0.05),
        })
    return results


def run_continuous_tests(df: pd.DataFrame) -> list:
    results = []
    churned = df[df.Exited == 1]
    retained = df[df.Exited == 0]
    for col in CONTINUOUS_PREDICTORS:
        stat, p = stats.ttest_ind(churned[col], retained[col], equal_var=False)  # Welch's t-test
        d = cohens_d(churned[col], retained[col])
        results.append({
            "predictor": col, "test": "Welch's t-test (unequal variance)",
            "statistic": round(float(stat), 3), "p_value": p,
            "mean_churned": round(float(churned[col].mean()), 2),
            "mean_retained": round(float(retained[col].mean()), 2),
            "effect_size_metric": "Cohen's d", "effect_size": round(d, 3),
            "effect_label": effect_label("cohens_d", d),
            "significant_at_0.05": bool(p < 0.05),
        })
    return results


def format_p(p: float) -> str:
    return "<0.001" if p < 0.001 else f"{p:.4f}"


def run_full_report(df: pd.DataFrame) -> dict:
    cat = run_categorical_tests(df)
    cont = run_continuous_tests(df)
    return {"categorical": cat, "continuous": cont}


if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from src.engagement_engine import load_and_engineer

    df = load_and_engineer(os.path.join(os.path.dirname(__file__), "..", "data", "European_Bank.csv"))
    report = run_full_report(df)

    print("=" * 78)
    print("CATEGORICAL PREDICTORS vs CHURN  (Chi-square test of independence)")
    print("=" * 78)
    for r in report["categorical"]:
        sig = "***SIGNIFICANT***" if r["significant_at_0.05"] else "not significant"
        print(f"{r['predictor']:<18} chi2={r['statistic']:>9.2f}  p={format_p(r['p_value']):<9} "
              f"Cramer's V={r['effect_size']:.3f} ({r['effect_label']:<11}) {sig}")

    print()
    print("=" * 78)
    print("CONTINUOUS PREDICTORS vs CHURN  (Welch's t-test)")
    print("=" * 78)
    for r in report["continuous"]:
        sig = "***SIGNIFICANT***" if r["significant_at_0.05"] else "not significant"
        print(f"{r['predictor']:<15} churned_mean={r['mean_churned']:>10.1f}  retained_mean={r['mean_retained']:>10.1f}  "
              f"t={r['statistic']:>8.2f}  p={format_p(r['p_value']):<9} d={r['effect_size']:.3f} ({r['effect_label']:<11}) {sig}")

    out_path = os.path.join(os.path.dirname(__file__), "..", "models", "statistical_test_results.json")
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nSaved full report to {out_path}")
