const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell,
  WidthType, ShadingType, AlignmentType, Header, Footer, PageNumber,
  VerticalAlign, LevelFormat,
} = require("docx");

const NAVY = "1E3A5F";
const ACCENT = "2563EB";
const GREY = "6B7280";
const LIGHT = "EEF2F7";
const RED = "DC2626";
const GREEN = "16A34A";
const FONT = "Calibri";

function h1(text) {
  return new Paragraph({ text, heading: HeadingLevel.HEADING_1, spacing: { before: 220, after: 110 } });
}
function p(text, opts = {}) {
  return new Paragraph({ spacing: { after: 120, line: 264 }, children: [new TextRun({ text, font: FONT, size: 21, ...opts })] });
}
function bullet(text, opts = {}) {
  return new Paragraph({
    numbering: { reference: "bullet-list", level: 0 },
    spacing: { after: 70, line: 260 },
    children: [new TextRun({ text, font: FONT, size: 21, ...opts })],
  });
}

function statCell(label, value, color, width) {
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    shading: { type: ShadingType.CLEAR, fill: LIGHT },
    verticalAlign: VerticalAlign.CENTER,
    margins: { top: 110, bottom: 110, left: 100, right: 100 },
    children: [
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 30 },
        children: [new TextRun({ text: value, bold: true, size: 32, color, font: FONT })] }),
      new Paragraph({ alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: label, size: 17, color: GREY, font: FONT })] }),
    ],
  });
}

function cell(text, { bold = false, color = "000000", shade = null, width = 1000 } = {}) {
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    shading: shade ? { type: ShadingType.CLEAR, fill: shade } : undefined,
    verticalAlign: VerticalAlign.CENTER,
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    children: [new Paragraph({ children: [new TextRun({ text: String(text), bold, color, font: FONT, size: 20 })] })],
  });
}
function dataTable(headers, rows, widths) {
  const total = widths.reduce((a, b) => a + b, 0);
  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths: widths,
    rows: [
      new TableRow({ tableHeader: true, children: headers.map((hd, i) => cell(hd, { bold: true, color: "FFFFFF", shade: NAVY, width: widths[i] })) }),
      ...rows.map((r, ri) => new TableRow({ children: r.map((val, i) => cell(val, { width: widths[i], shade: ri % 2 === 1 ? LIGHT : null })) })),
    ],
  });
}

const children = [];

children.push(
  new Paragraph({ children: [new TextRun({ text: "EXECUTIVE SUMMARY", color: ACCENT, bold: true, size: 20, font: FONT })] }),
  new Paragraph({
    spacing: { before: 100, after: 70 },
    children: [new TextRun({ text: "Customer Engagement & Product Utilization Analytics for Retention Strategy", bold: true, size: 32, color: NAVY, font: FONT })],
  }),
  new Paragraph({
    spacing: { after: 180 },
    children: [new TextRun({ text: "Prepared for bank leadership and retention strategy stakeholders  \u2022  Sarvagya, Data Analyst Intern  \u2022  September 2026", italics: true, size: 18, color: GREY, font: FONT })],
  }),

  p("This analysis of 10,000 customer records (France, Germany, Spain) tested three assumptions used to guide retention strategy: that more products signal loyalty, that a high balance signals safety, and that card ownership builds stickiness. All three are contradicted by the data and confirmed with formal significance testing (chi-square / t-tests, p < 0.05) \u2014 the strongest validated predictor of retention is engagement (activity status + moderate product count), not account value.", { bold: false }),

  new Table({
    width: { size: 9350, type: WidthType.DXA },
    columnWidths: [1870, 1870, 1870, 1870, 1870],
    rows: [new TableRow({ children: [
      statCell("Overall Churn Rate", "20.4%", RED, 1870),
      statCell("Best-Retention Segment", "9.7%", GREEN, 1870),
      statCell("Annual Revenue at Risk", "$4.36M", RED, 1870),
      statCell("Premium Customers At Risk", "1,247", ACCENT, 1870),
      statCell("Premium CLV Exposure", "$16.1M", ACCENT, 1870),
    ]})],
  }),

  h1("Key Findings"),
  bullet("Product depth has a sweet spot, not a straight line. Retention peaks at 2 products (92.4%); 3\u20134 products correlates with 83\u2013100% churn \u2014 a strong signal of over-selling, not loyalty, affecting 326 customers."),
  bullet("Balance does not protect against churn. Top-quartile-balance customers churn more (23.7%) than the rest of the base (19.3%). Loyalty must be read from behavior, not account value."),
  bullet("Inactivity is the real risk \u2014 especially paired with high balance. 1,247 customers are both inactive and high-balance; they churn at 30.5% and represent an estimated $16.1M in lifetime value exposure."),
  bullet("Credit card ownership has no measurable retention effect (+0.6 percentage points) \u2014 it should not be treated as a retention lever."),
  bullet("A simple composite score \u2014 the Relationship Strength Index, built from activity and product depth \u2014 separates customers into risk tiers with a more than 3x churn spread (Weak 40.3% vs. Strong 12.4%), and a 2.7x lifetime-value spread ($6,453 vs. $17,111 per customer)."),
  bullet("Illustrative ROI modeling shows both proposed campaigns below (Premium At-Risk outreach, Inactive Disengaged re-engagement) pay back 12\u201318x their cost even under conservative assumptions \u2014 full detail in the research paper, Section 10."),

  h1("Recommendations"),
  dataTable(
    ["Priority", "Action", "Why"],
    [
      ["1", "Pause 3rd/4th-product cross-sell; investigate root cause", "82.7\u2013100% churn in this segment, likely mis-selling"],
      ["2", "Launch proactive outreach to the 1,247 Premium At-Risk customers", "Highest financial exposure: $16.1M in estimated lifetime value"],
      ["3", "Re-engagement campaign for Inactive Disengaged segment", "Highest churn rate of any segment: 36.7%"],
      ["4", "Redirect card-issuance retention budget elsewhere", "No measurable retention effect"],
      ["5", "Adopt RSI as a live CRM/dashboard metric", "Cheap to compute, updates in real time, 3x+ churn spread"],
    ],
    [1100, 4500, 3750],
  ),

  h1("Supporting Deliverables"),
  bullet("Full research paper \u2014 detailed methodology, EDA, and KPI derivations"),
  bullet("Interactive Streamlit dashboard \u2014 live filtering by engagement, product count, balance, and salary, with a built-in high-value disengaged customer detector"),
);

const doc = new Document({
  creator: "Sarvagya",
  title: "Executive Summary — Customer Engagement & Retention Analytics",
  numbering: {
    config: [{ reference: "bullet-list", levels: [
      { level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720, hanging: 360 } } } },
    ]}],
  },
  styles: {
    default: {
      document: { run: { font: FONT, size: 22 } },
      heading1: { run: { font: FONT, size: 26, bold: true, color: NAVY }, paragraph: { spacing: { before: 300, after: 140 } } },
    },
  },
  sections: [{
    properties: { page: { margin: { top: 760, bottom: 760, left: 1080, right: 1080 } } },
    footers: {
      default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: "Page ", size: 16, color: GREY, font: FONT }),
                    new TextRun({ children: [PageNumber.CURRENT], size: 16, color: GREY, font: FONT }),
                    new TextRun({ text: " of ", size: 16, color: GREY, font: FONT }),
                    new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 16, color: GREY, font: FONT })] })] }),
    },
    children,
  }],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync("../reports/Executive_Summary.docx", buf);
  console.log("Executive_Summary.docx written,", buf.length, "bytes");
});
