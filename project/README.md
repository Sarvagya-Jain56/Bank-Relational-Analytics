# Customer Engagement & Product Utilization Analytics for Retention Strategy

A behavioral analysis of 10,000 European retail bank customers, testing whether engagement, product depth, and account balance — not demographics alone — predict churn. Every finding is statistically validated (chi-square / Welch's t-tests, effect sizes) before being turned into a KPI or dashboard metric.

## Headline finding

Retention peaks at **2 products** (7.6% churn) and collapses at 3–4 products (83–100% churn) — a pattern more consistent with over-selling than loyalty. Balance does **not** protect against churn; engagement does. Full detail in `reports/Research_Paper.docx`.

## Project structure

```
.
├── app.py                      # Streamlit dashboard (5 tabs, live filters)
├── requirements.txt
├── Dockerfile
├── .github/workflows/ci.yml    # Runs the test suite on every push
├── data/
│   └── European_Bank.csv       # Source dataset (10,000 rows)
├── src/
│   ├── engagement_engine.py    # Feature engineering, segmentation, KPI math (single source of truth)
│   ├── statistical_tests.py    # Chi-square / Welch's t-test validation suite
│   └── clv_model.py            # Customer Lifetime Value & revenue-at-risk / ROI modeling
├── tests/
│   ├── test_engagement_engine.py   # 16 unit tests (pytest)
│   └── test_clv_model.py           # 18 unit tests (pytest)
├── scripts/
│   ├── make_charts.py          # Regenerates all report chart images
│   ├── build_paper.js          # Regenerates the research paper (.docx)
│   └── build_exec_summary.js   # Regenerates the executive summary (.docx)
├── assets/                     # Chart PNGs used in the reports
└── reports/
    ├── Research_Paper.docx     # 12-page paper: EDA, stats, KPIs, recommendations
    └── Executive_Summary.docx  # 1-page leadership summary
```

## Run the dashboard locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Run the tests

```bash
pip install pytest
pytest tests/ -v
```

## Run the statistical validation suite standalone

```bash
python src/statistical_tests.py
```

## Regenerate the reports (after changing analysis logic)

```bash
cd scripts
python make_charts.py          # regenerates assets/*.png
node build_paper.js            # regenerates reports/Research_Paper.docx
node build_exec_summary.js     # regenerates reports/Executive_Summary.docx
```

## Run with Docker

```bash
docker build -t retention-dashboard .
docker run -p 8501:8501 retention-dashboard
```

## Key definitions

- **High Balance / Premium**: top quartile of `Balance` (≥ $127,644)
- **Engagement Segments**: Active Engaged (active + 2+ products) / Active Low-Product (active + 1 product) / Inactive Disengaged (inactive + 1 product) / Inactive Multi-Product (inactive + 2+ products)
- **Relationship Strength Index (RSI)**: 0.5 × IsActiveMember + 0.5 × ProductDepthScore, tiered Weak (<0.40) / Moderate (0.40–0.75) / Strong (>0.75)
- **Statistical validation**: every predictor is tested with a chi-square test (categorical) or Welch's t-test (continuous), reported with an effect size (Cramer's V / Cohen's d) — a finding is only treated as actionable if it is both significant (p < 0.05) *and* at least small-to-medium effect size

## Roadmap

| Phase | Scope | Status |
|---|---|---|
| 1 | Data foundation — EDA, feature engineering, KPIs, dashboard, paper | Done |
| 2 | Statistical validation — hypothesis testing, effect sizes | Done |
| 3 | Production engineering — tests, CI, Docker, repo structure | Done |
| 4 | Business impact — Customer Lifetime Value, revenue-at-risk, ROI simulation | Done |
| 5 | Predictive modeling — churn classifier, explainability (SHAP) | Planned |
| 6 | Final polish — model card, architecture docs | Planned |
