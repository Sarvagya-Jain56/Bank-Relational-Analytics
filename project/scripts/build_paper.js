const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell,
  WidthType, BorderStyle, ShadingType, ImageRun, AlignmentType, PageBreak,
  LevelFormat, Header, Footer, PageNumber, NumberFormat,
  VerticalAlign, convertInchesToTwip, PositionalTab, PositionalTabAlignment,
  PositionalTabLeader, PositionalTabRelativeTo,
} = require("docx");

const NAVY = "1E3A5F";
const ACCENT = "2563EB";
const GREY = "6B7280";
const LIGHT = "EEF2F7";
const RED = "DC2626";
const GREEN = "16A34A";

const FONT = "Calibri";

function h1(text) {
  return new Paragraph({
    text, heading: HeadingLevel.HEADING_1,
    spacing: { before: 400, after: 200 },
  });
}
function h2(text) {
  return new Paragraph({
    text, heading: HeadingLevel.HEADING_2,
    spacing: { before: 300, after: 150 },
  });
}
function p(text, opts = {}) {
  return new Paragraph({
    spacing: { after: 180, line: 276 },
    children: [new TextRun({ text, font: FONT, size: 22, ...opts })],
  });
}
function bullet(text, opts = {}) {
  return new Paragraph({
    numbering: { reference: "bullet-list", level: 0 },
    spacing: { after: 90 },
    children: [new TextRun({ text, font: FONT, size: 22, ...opts })],
  });
}
function caption(text) {
  return new Paragraph({
    spacing: { before: 80, after: 260 },
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text, italics: true, color: GREY, size: 19, font: FONT })],
  });
}
function image(path, width, height) {
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 200, after: 60 },
    children: [new ImageRun({ type: "png", data: fs.readFileSync(path), transformation: { width, height } })],
  });
}

function cell(text, { bold = false, color = "000000", shade = null, width = 1000, align = AlignmentType.LEFT } = {}) {
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    shading: shade ? { type: ShadingType.CLEAR, fill: shade } : undefined,
    verticalAlign: VerticalAlign.CENTER,
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    children: [new Paragraph({
      alignment: align,
      children: [new TextRun({ text: String(text), bold, color, font: FONT, size: 20 })],
    })],
  });
}

function dataTable(headers, rows, widths) {
  const total = widths.reduce((a, b) => a + b, 0);
  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths: widths,
    rows: [
      new TableRow({
        tableHeader: true,
        children: headers.map((hd, i) => cell(hd, { bold: true, color: "FFFFFF", shade: NAVY, width: widths[i] })),
      }),
      ...rows.map((r, ri) => new TableRow({
        children: r.map((val, i) => cell(val, { width: widths[i], shade: ri % 2 === 1 ? LIGHT : null })),
      })),
    ],
  });
}

function tocEntry(text, page) {
  return new Paragraph({
    spacing: { after: 130 },
    children: [
      new TextRun({ text, font: FONT, size: 22 }),
      new TextRun({
        children: [
          new PositionalTab({
            alignment: PositionalTabAlignment.RIGHT,
            relativeTo: PositionalTabRelativeTo.MARGIN,
            leader: PositionalTabLeader.DOT,
          }),
        ],
      }),
      new TextRun({ text: String(page), font: FONT, size: 22 }),
    ],
  });
}

function hr() {
  return new Paragraph({
    border: { bottom: { color: "D1D5DB", space: 1, style: BorderStyle.SINGLE, size: 6 } },
    spacing: { after: 240 },
  });
}

const children = [];

// ---------------------------------------------------------------------
// COVER PAGE
// ---------------------------------------------------------------------
children.push(
  new Paragraph({ spacing: { before: 1600 }, children: [] }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "TECHNICAL RESEARCH PAPER", color: ACCENT, bold: true, size: 22, font: FONT })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 300, after: 300 },
    children: [new TextRun({
      text: "Customer Engagement & Product Utilization Analytics for Retention Strategy",
      bold: true, size: 44, color: NAVY, font: FONT,
    })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 800 },
    children: [new TextRun({
      text: "A behavioral analysis of customer engagement, product depth, and financial commitment as drivers of retention",
      italics: true, size: 26, color: GREY, font: FONT,
    })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 80 },
    children: [new TextRun({ text: "Prepared by: Sarvagya", size: 24, font: FONT, bold: true })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 80 },
    children: [new TextRun({ text: "Role: Data Analyst Intern", size: 22, font: FONT, color: GREY })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 80 },
    children: [new TextRun({ text: "Dataset: European_Bank.csv \u2014 10,000 customer records", size: 22, font: FONT, color: GREY })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "September 2026", size: 22, font: FONT, color: GREY })],
  }),
  new Paragraph({ children: [new PageBreak()] }),
);

// ---------------------------------------------------------------------
// TABLE OF CONTENTS
// ---------------------------------------------------------------------
children.push(
  h1("Table of Contents"),
  tocEntry("Abstract", 3),
  tocEntry("1. Background and Context", 3),
  tocEntry("2. Problem Statement", 3),
  tocEntry("3. Objectives", 4),
  tocEntry("4. Dataset Description", 4),
  tocEntry("5. Analytical Methodology", 5),
  tocEntry("6. Exploratory Data Analysis & Key Findings", 5),
  tocEntry("7. Statistical Validation of Findings", 8),
  tocEntry("8. Key Performance Indicators", 10),
  tocEntry("9. Customer Segmentation Summary", 11),
  tocEntry("10. Recommendations", 11),
  tocEntry("11. Limitations", 12),
  tocEntry("12. Conclusion", 12),
  new Paragraph({ children: [new PageBreak()] }),
);

// ---------------------------------------------------------------------
// ABSTRACT
// ---------------------------------------------------------------------
children.push(
  h1("Abstract"),
  p("Retail banks routinely equate a customer's balance sheet strength with their loyalty, and their product count with their satisfaction. This paper tests both assumptions against 10,000 customer records from a European retail bank (France, Germany, Spain) with a 20.37% observed churn rate. Using engagement status (IsActiveMember), product count, and account balance as the primary behavioral signals, we built a four-segment engagement classification, five retention KPIs, and a composite Relationship Strength Index (RSI), then validated each against actual churn outcomes."),
  p("The results overturn both assumptions, and every driver reported here was confirmed with formal hypothesis testing (chi-square tests for categorical predictors, Welch's t-tests for continuous ones, both paired with effect sizes) rather than read off raw percentages alone. Balance is not protective: customers in the top balance quartile churn at a higher rate (23.7%) than the rest of the base (19.3%). Product count is not linear: retention peaks at exactly two products (92.4% retained) and collapses for three or more (17.3% and 0% retained respectively), a pattern consistent with over-selling rather than genuine cross-sell success \u2014 and formally, NumOfProducts carries the largest categorical effect size in the dataset (Cramer's V = 0.388). Engagement status is the most reliable actionable lever available \u2014 active members retain at 1.17x the rate of inactive members \u2014 and the RSI, built purely from engagement and product depth, separates customers into churn-risk tiers with a fourfold spread (Weak tier: 40.3% churn vs. Strong tier: 12.4%)."),
  p("We conclude that retention strategy should be re-anchored around behavior \u2014 activity and product depth \u2014 rather than account value, and we flag the 3\u20134 product segment (326 customers, 85.9% churn) as an operational priority requiring root-cause investigation rather than further cross-selling."),
);

// ---------------------------------------------------------------------
// 1. BACKGROUND AND CONTEXT
// ---------------------------------------------------------------------
children.push(
  h1("1. Background and Context"),
  p("Banks increasingly recognize that customer behavior and engagement \u2014 not just demographics \u2014 determine long-term retention. Customers can appear financially strong, carrying a high balance or salary, and still churn because of low engagement, limited product adoption, or a weak overall relationship with the bank."),
  p("Understanding how customers actually use banking products and services is essential to designing effective cross-sell strategies, loyalty programs, and engagement-driven retention initiatives. This project evaluates retention through the lens of customer behavior and relationship strength, rather than through demographic or account-value proxies alone."),
);

// ---------------------------------------------------------------------
// 2. PROBLEM STATEMENT
// ---------------------------------------------------------------------
children.push(
  h1("2. Problem Statement"),
  p("Despite holding data on customer engagement and product usage, banks often lack:"),
  bullet("Quantitative insight into which behaviors actually drive retention"),
  bullet("Clarity on whether product depth (number of products held) reduces churn"),
  bullet("Evidence on whether high balances alone are sufficient to ensure loyalty"),
  p("As a result, retention strategies are frequently generic and misaligned with actual customer behavior. This paper addresses each of these three gaps directly and empirically."),
);

// ---------------------------------------------------------------------
// 3. OBJECTIVES
// ---------------------------------------------------------------------
children.push(
  h1("3. Objectives"),
  h2("3.1 Primary Objectives"),
  bullet("Evaluate the relationship between engagement and churn"),
  bullet("Measure the retention impact of product count and product mix"),
  bullet("Identify disengaged yet high-value customers"),
  h2("3.2 Secondary Objectives"),
  bullet("Support engagement-driven retention strategies"),
  bullet("Improve product bundling decisions"),
  bullet("Reduce silent churn among premium customers"),
);

// ---------------------------------------------------------------------
// 4. DATASET DESCRIPTION
// ---------------------------------------------------------------------
children.push(
  h1("4. Dataset Description"),
  p("The dataset contains 10,000 customer records with 13 fields and no missing values or duplicate rows. Geography is limited to three markets: France (5,014 customers), Germany (2,509), and Spain (2,477)."),
  dataTable(
    ["Column", "Description"],
    [
      ["CustomerId", "Unique customer identifier"],
      ["Surname", "Customer surname"],
      ["CreditScore", "Customer creditworthiness (350\u2013850)"],
      ["Geography", "France, Germany, or Spain"],
      ["Gender", "Male / Female"],
      ["Age", "Customer age in years"],
      ["Tenure", "Years with the bank (0\u201310)"],
      ["Balance", "Account balance"],
      ["NumOfProducts", "Number of bank products held (1\u20134)"],
      ["HasCrCard", "Credit card ownership (binary)"],
      ["IsActiveMember", "Activity indicator (binary)"],
      ["EstimatedSalary", "Estimated annual salary"],
      ["Exited", "Churn indicator \u2014 target variable (1 = churned)"],
    ],
    [2800, 6200],
  ),
  caption("Table 1. Dataset field descriptions"),
  p("Overall churn rate: 20.37% (2,037 churned of 10,000). This is a moderately imbalanced target, which was accounted for by using rate-based and ratio-based KPIs rather than raw counts throughout the analysis."),
);

// ---------------------------------------------------------------------
// 5. METHODOLOGY
// ---------------------------------------------------------------------
children.push(
  h1("5. Analytical Methodology"),
  h2("5.1 Data Ingestion & Validation"),
  p("The dataset was loaded and checked for missing values, duplicate records, and consistency of binary fields (HasCrCard, IsActiveMember, Exited). No cleaning was required \u2014 the data was complete and well-formed."),
  h2("5.2 Engagement Classification"),
  p("Each customer was assigned to one of four engagement segments, based on activity status and product depth:"),
  bullet("Active Engaged \u2014 active member holding 2 or more products"),
  bullet("Active Low-Product \u2014 active member holding exactly 1 product"),
  bullet("Inactive Disengaged \u2014 inactive member holding exactly 1 product"),
  bullet("Inactive Multi-Product \u2014 inactive member holding 2 or more products"),
  h2("5.3 Product Utilization Analysis"),
  p("Churn rate was computed for each product count (1\u20134) to test whether product depth is protective, and single-product customers were compared against multi-product customers as a group."),
  h2("5.4 Financial Commitment vs. Engagement Analysis"),
  p("Customers were flagged as \u201cHigh Balance\u201d if their balance fell in the top quartile of the dataset (\u2265 $127,644). This flag was cross-tabulated against activity status to test whether balance offsets the risk of inactivity, and to identify \u201cat-risk premium customers\u201d \u2014 defined as inactive customers who are also high-balance."),
  h2("5.5 Retention Strength Assessment"),
  p("A composite Relationship Strength Index (RSI) was constructed from activity status and a normalized product-depth score, then partitioned into Weak / Moderate / Strong tiers to test whether a single combined score predicts churn better than any individual variable."),
  h2("5.6 Statistical Validation"),
  p("Every predictor examined in the EDA was re-tested formally rather than left as a raw percentage comparison: chi-square tests of independence for categorical predictors, Welch's t-tests for continuous predictors, both reported alongside an effect size (Cramer's V and Cohen's d respectively) so that statistical significance is never confused with practical importance. Full results are in Section 7."),
);

// ---------------------------------------------------------------------
// 6. EDA & FINDINGS
// ---------------------------------------------------------------------
children.push(
  h1("6. Exploratory Data Analysis & Key Findings"),

  h2("6.1 Finding 1 \u2014 Product Depth Has a Sweet Spot, Not a Straight Line"),
  p("Churn rate by product count is sharply non-monotonic. Customers with 2 products churn least of any group (7.6%); customers with 3 or 4 products churn at 82.7% and 100% respectively \u2014 a near-certainty. This affects 326 customers (3.3% of the base) and represents the single most severe risk concentration in the dataset."),
  image("../assets/chart_products.png", 480, 288),
  caption("Figure 1. Churn rate by number of products held"),
  p("This pattern is inconsistent with a simple \u201cmore products = more loyalty\u201d cross-sell model. It is far more consistent with over-selling or forced bundling: customers pushed into a third or fourth product they didn't want or need, who then leave at the first opportunity. We treat this as an operational red flag rather than a cross-sell success story."),

  h2("6.2 Finding 2 \u2014 Engagement Segments Show a Clean, Usable Gradient"),
  image("../assets/chart_segments.png", 500, 280),
  caption("Figure 2. Churn rate by engagement segment"),
  p("The four engagement segments separate cleanly: Active Engaged customers churn at just 9.7%, while Inactive Disengaged customers churn at 36.7% \u2014 nearly four times higher. Active Low-Product and Inactive Multi-Product sit in between, showing that both activity and product depth matter, but neither alone is sufficient \u2014 it is the combination that predicts retention best."),

  h2("6.3 Finding 3 \u2014 Balance Does Not Protect Against Churn"),
  image("../assets/chart_balance_quartile.png", 480, 288),
  caption("Figure 3. Churn rate by balance quartile"),
  p("Directly testing the assumption that high balances ensure loyalty: they do not. Top-quartile-balance customers churn at 23.7%, higher than the base rate of 20.4% and higher than lower-balance customers (19.3%). Balance alone is not a retention signal \u2014 it must be read alongside engagement."),
  image("../assets/chart_interaction.png", 500, 280),
  caption("Figure 4. Churn by balance tier and activity status combined"),
  p("The interaction is the important part: inactive customers churn more regardless of balance tier, and being high-balance does not close that gap. Inactive + high-balance customers churn at 30.5%, the highest risk combination identified in this analysis, and this segment alone represents an estimated $185.6 million in balances at risk (1,247 customers)."),

  h2("6.4 Finding 4 \u2014 Credit Card Ownership Is Not a Retention Lever"),
  p("A common assumption is that product ownership \u2014 particularly a credit card, which creates recurring engagement touchpoints \u2014 improves stickiness. The data does not support this: retention among cardholders (79.8%) is statistically indistinguishable from non-cardholders (79.2%), a gap of only 0.6 percentage points. We recommend against treating credit card issuance as a retention initiative on its own."),

  h2("6.5 Secondary Factors"),
  p("Two demographic patterns are notable but sit outside this project's primary engagement/product-depth scope, so we flag them for awareness rather than build KPIs around them:"),
  image("../assets/chart_geography.png", 460, 275),
  caption("Figure 5. Churn rate by geography"),
  bullet("Germany churns at 32.4%, roughly double France (16.2%) and Spain (16.7%) \u2014 worth a market-specific review."),
  bullet("Churned customers skew older on average (44.8 years) than retained customers (37.4 years); credit score and tenure show negligible difference between churned and retained groups and were not predictive on their own."),
);

// ---------------------------------------------------------------------
// 7. STATISTICAL VALIDATION
// ---------------------------------------------------------------------
children.push(
  h1("7. Statistical Validation of Findings"),
  p("Percentages alone can be misleading \u2014 a gap between two groups can look meaningful and still be noise, especially in subgroups with few customers. Every driver discussed in Section 6 was therefore re-tested formally: categorical predictors with a chi-square test of independence, and continuous predictors with Welch's t-test (which does not assume equal variance between the churned and retained groups). Effect size \u2014 Cramer's V for categorical predictors, Cohen's d for continuous ones \u2014 was computed alongside each p-value, because with 10,000 rows even a trivial difference can register as statistically significant. A finding is only treated as actionable in this paper if it is both significant and at least small-to-medium in effect size."),

  h2("7.1 Categorical Predictors"),
  dataTable(
    ["Predictor", "\u03c7\u00b2", "p-value", "Cramer's V", "Effect", "Significant?"],
    [
      ["Geography", "301.25", "<0.001", "0.174", "Small", "Yes"],
      ["Gender", "112.92", "<0.001", "0.106", "Small", "Yes"],
      ["HasCrCard", "0.47", "0.4924", "0.007", "Negligible", "No"],
      ["IsActiveMember", "242.99", "<0.001", "0.156", "Small", "Yes"],
      ["NumOfProducts", "1503.63", "<0.001", "0.388", "Moderate", "Yes"],
    ],
    [2000, 1400, 1400, 1400, 1500, 1600],
  ),
  caption("Table 4. Chi-square test of independence, categorical predictors vs. churn"),
  p("NumOfProducts has both the largest chi-square statistic and the largest effect size of any categorical predictor \u2014 formal confirmation that product depth is the strongest lever available. HasCrCard is the only categorical predictor that fails significance entirely (p = 0.49), which statistically confirms Finding 4: card ownership has no relationship with churn, not even a small one."),

  h2("7.2 Continuous Predictors"),
  dataTable(
    ["Predictor", "Mean (churned)", "Mean (retained)", "t-stat", "p-value", "Cohen's d", "Effect", "Sig.?"],
    [
      ["CreditScore", "645.4", "651.9", "-2.63", "0.0085", "-0.067", "Negligible", "Yes*"],
      ["Age", "44.8", "37.4", "30.42", "<0.001", "0.739", "Medium", "Yes"],
      ["Tenure", "4.9", "5.0", "-1.38", "0.1664", "-0.035", "Negligible", "No"],
      ["Balance", "91,108.5", "72,745.3", "12.47", "<0.001", "0.296", "Small", "Yes"],
      ["EstimatedSalary", "101,465.7", "99,738.4", "1.20", "0.2289", "0.030", "Negligible", "No"],
    ],
    [1750, 1550, 1550, 1000, 1050, 1150, 1200, 1000],
  ),
  caption("Table 5. Welch's t-test, continuous predictors vs. churn"),
  p("*CreditScore is statistically significant (p = 0.0085) purely because of sample size \u2014 its effect size (d = -0.067) is negligible, meaning it has no practical use as a retention lever despite the low p-value. This is a useful reminder that significance and importance are not the same thing, and the KPIs in Section 8 are deliberately built only from predictors that clear both bars."),

  image("../assets/chart_effect_sizes.png", 480, 320),
  caption("Figure 7. Effect size by predictor, ranked (significant predictors in blue). Cramer's V and Cohen's d are different metrics shown on a shared axis for ranking convenience \u2014 both are conventionally read on comparable small/medium/large scales, but they are not mathematically equivalent."),
  p("The single largest effect size in the entire dataset belongs to Age (d = 0.739, medium) \u2014 larger than NumOfProducts' Cramer's V. This did not surface as a headline finding in the raw EDA because age differences are less visually dramatic than the product-count churn cliff, but formal testing puts it ahead of geography, gender, and activity status individually. It is not built into a dedicated KPI in this version of the project because age is not an actionable lever in the way engagement and product depth are \u2014 a bank cannot change a customer's age \u2014 but it is a strong candidate input for a future predictive model (Phase 2 of this project) and for age-segmented retention messaging."),
);

// ---------------------------------------------------------------------
// 8. KPIs
// ---------------------------------------------------------------------
children.push(
  h1("8. Key Performance Indicators"),
  p("Five KPIs were defined to operationalize the findings above into metrics that can be tracked over time."),
  dataTable(
    ["KPI", "Formula", "Value", "Interpretation"],
    [
      ["Engagement Retention Ratio", "Retention(active) \u00f7 Retention(inactive)", "1.17x", "Active members retain 17% better than inactive members"],
      ["Product Depth Index", "Retention rate indexed by product count", "1: 0.78 \u2192 2: 1.00 \u2192 3: 0.19 \u2192 4: 0.00", "Retention peaks at 2 products, collapses beyond it"],
      ["High-Balance Disengagement Ratio", "Churn(inactive+high-bal) \u00f7 overall churn", "1.50x", "Inactive premium customers churn 50% above the base rate"],
      ["Credit Card Stickiness Score", "Retention(has CC) \u2212 Retention(no CC)", "+0.6 pp", "Negligible \u2014 not a meaningful retention lever"],
      ["Relationship Strength Index (RSI)", "0.5\u00d7Active + 0.5\u00d7ProductDepthScore, tiered", "Weak 40.3% \u2192 Moderate 14.3% \u2192 Strong 12.4% churn", "Best single composite predictor (r = \u22120.27 with churn)"],
    ],
    [2400, 2600, 1900, 2100],
  ),
  caption("Table 2. Key Performance Indicators, formulas, and computed values"),
  image("../assets/chart_rsi.png", 440, 280),
  caption("Figure 6. Churn rate by Relationship Strength Index tier"),
);

// ---------------------------------------------------------------------
// 8. SEGMENTATION SUMMARY
// ---------------------------------------------------------------------
children.push(
  h1("9. Customer Segmentation Summary"),
  dataTable(
    ["Segment", "Customers", "Share", "Churn Rate", "Avg. Balance"],
    [
      ["Active Engaged", "2,588", "25.9%", "9.7%", "$53,071"],
      ["Active Low-Product", "2,563", "25.6%", "18.9%", "$98,902"],
      ["Inactive Multi-Product", "2,328", "23.3%", "16.2%", "$54,327"],
      ["Inactive Disengaged", "2,521", "25.2%", "36.7%", "$98,196"],
    ],
    [2600, 1700, 1400, 1600, 1700],
  ),
  caption("Table 3. Engagement segment summary"),
  h2("9.1 High-Value Disengaged Customer Detection"),
  p("Cross-referencing inactivity with high balance identifies 1,247 \u201cpremium at-risk\u201d customers (12.5% of the base). This group churns at 30.5% \u2014 the highest rate of any segment defined in this study \u2014 and collectively holds an estimated $185.6 million in balances. This is the group with the highest financial exposure per churned customer and should be the first target for proactive relationship-manager outreach, ahead of broad-based campaigns."),
);

// ---------------------------------------------------------------------
// 9. RECOMMENDATIONS
// ---------------------------------------------------------------------
children.push(
  h1("10. Recommendations"),
  h2("10.1 Investigate, don't expand, the 3\u20134 product segment"),
  p("Pause cross-sell pushes toward a 3rd or 4th product until the root cause of the 82.7\u2013100% churn rate is understood. Recommend a targeted satisfaction survey or complaint-log review for the 326 affected customers before any further bundling campaigns."),
  h2("10.2 Prioritize the Inactive Disengaged and Premium At-Risk segments"),
  p("These two segments carry the highest churn rates (36.7% and 30.5%) and the clearest intervention logic: re-engagement campaigns (app nudges, relationship-manager check-ins) for Inactive Disengaged customers, and white-glove retention outreach for the 1,247 Premium At-Risk customers given their $185.6M balance exposure."),
  h2("10.3 Stop treating credit card issuance as a retention initiative"),
  p("Redirect budget currently aimed at credit card cross-sell-for-retention purposes toward the engagement-first initiatives above, since card ownership shows no measurable retention effect in this data."),
  h2("10.4 Adopt the Relationship Strength Index as an ongoing CRM metric"),
  p("RSI is cheap to compute (built from two fields already captured at account level), updates in real time, and shows a 3\u20134x churn spread between tiers. Recommend surfacing RSI directly in the relationship-manager dashboard delivered alongside this paper."),
  h2("10.5 Open a market-specific review for Germany"),
  p("Germany's churn rate (32.4%) is roughly double the other two markets and falls outside this project's core engagement/product scope \u2014 recommend a follow-up study isolating whether this is a product-fit, pricing, or competitive issue specific to that market."),
);

// ---------------------------------------------------------------------
// 10. LIMITATIONS
// ---------------------------------------------------------------------
children.push(
  h1("11. Limitations"),
  bullet("Single time snapshot: the dataset reflects one point in time (2025), so trend and seasonality cannot be assessed."),
  bullet("No explicit churn reason is captured; the 3\u20134-product \u201cover-selling\u201d explanation is the most consistent read of the pattern but is inferred, not directly evidenced, and should be confirmed with qualitative data (complaints, surveys, exit interviews)."),
  bullet("All relationships reported are correlational. Engagement, product depth, and balance are associated with churn; this analysis does not establish causal direction."),
  bullet("IsActiveMember is a binary flag with no definition of the underlying activity threshold provided in the source data, so its precise meaning should be confirmed with the data owner before operational use."),
);

// ---------------------------------------------------------------------
// 11. CONCLUSION
// ---------------------------------------------------------------------
children.push(
  h1("12. Conclusion"),
  p("This project reframes customer churn from a behavioral and relationship-strength perspective rather than a demographic or account-value one. Three assumptions commonly used to guide retention strategy \u2014 that more products signal more loyalty, that a high balance signals safety, and that card ownership builds stickiness \u2014 are each contradicted by this data. What does predict retention reliably is engagement, measured simply as activity status, combined with a moderate (not maximal) product depth. The Relationship Strength Index operationalizes this into a single, trackable score, and the accompanying Streamlit dashboard puts all of the above into the hands of relationship managers for day-to-day use."),
);

// ---------------------------------------------------------------------
// BUILD DOCUMENT
// ---------------------------------------------------------------------
const doc = new Document({
  creator: "Sarvagya",
  title: "Customer Engagement & Product Utilization Analytics for Retention Strategy",
  numbering: {
    config: [
      {
        reference: "bullet-list",
        levels: [
          { level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 720, hanging: 360 } } } },
        ],
      },
    ],
  },
  styles: {
    default: {
      document: { run: { font: FONT, size: 22 } },
      heading1: { run: { font: FONT, size: 30, bold: true, color: NAVY }, paragraph: { spacing: { before: 400, after: 200 } } },
      heading2: { run: { font: FONT, size: 25, bold: true, color: ACCENT }, paragraph: { spacing: { before: 280, after: 140 } } },
    },
  },
  sections: [
    {
      properties: {
        page: { margin: { top: 1440, bottom: 1440, left: 1350, right: 1350 } },
      },
      headers: {
        default: new Header({
          children: [new Paragraph({
            alignment: AlignmentType.RIGHT,
            children: [new TextRun({ text: "Customer Engagement & Retention Analytics", size: 16, color: GREY, font: FONT })],
          })],
        }),
      },
      footers: {
        default: new Footer({
          children: [new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [
              new TextRun({ text: "Page ", size: 16, color: GREY, font: FONT }),
              new TextRun({ children: [PageNumber.CURRENT], size: 16, color: GREY, font: FONT }),
              new TextRun({ text: " of ", size: 16, color: GREY, font: FONT }),
              new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 16, color: GREY, font: FONT }),
            ],
          })],
        }),
      },
      children,
    },
  ],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync("../reports/Research_Paper.docx", buf);
  console.log("Research_Paper.docx written,", buf.length, "bytes");
});
