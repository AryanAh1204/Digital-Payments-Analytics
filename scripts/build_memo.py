"""Builds memo.pdf: one-page business memo, findings grounded in outputs/*.csv."""
from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parent.parent
styles = getSampleStyleSheet()

title_style = ParagraphStyle("title", parent=styles["Title"], fontSize=15, spaceAfter=2)
subtitle_style = ParagraphStyle("subtitle", parent=styles["Normal"], fontSize=9, textColor=colors.grey, spaceAfter=12)
h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=11, spaceBefore=8, spaceAfter=4)
body = ParagraphStyle("body", parent=styles["Normal"], fontSize=9.5, leading=13)

doc = SimpleDocTemplate(
    str(ROOT / "memo.pdf"), pagesize=LETTER,
    topMargin=0.6 * inch, bottomMargin=0.6 * inch, leftMargin=0.7 * inch, rightMargin=0.7 * inch,
)

story = [
    Paragraph("Digital Payments Transaction Analytics", title_style),
    Paragraph(
        "Segmentation, fraud patterns, and volume forecasting on synthetic mobile payment "
        "transaction data, 6.36M transactions",
        subtitle_style,
    ),
    Paragraph("Findings", h2),
    Paragraph(
        "1. Fraud is concentrated in two transaction types. TRANSFER carries a 0.77% fraud "
        "rate and CASH_OUT 0.18%; CASH_IN, PAYMENT, and DEBIT show zero labeled fraud in "
        "this data. Fraud TRANSFERs almost always drain the account: 96% of them take the "
        "origin balance to about zero in a single transaction, a sharper signature than the "
        "type-level rate alone suggests.",
        body,
    ),
    Paragraph(
        "2. Account value is concentrated in half the base, split two ways rather than "
        "dominated by one tier. Quantile RFM segmentation splits accounts into 5 tiers; the "
        "two high-value tiers, frequent high spenders and high-value one-off senders, are "
        "50% of accounts by count and hold 94.3% of total transaction value between them, "
        "close to evenly. The other 50% of accounts (low-value-frequent, standard, and "
        "dormant) account for just 5.7% of value.",
        body,
    ),
    Spacer(1, 4),
    Paragraph("Interventions", h2),
    Paragraph(
        "1. Real-time flag on near-total balance drain. Rather than a type-level rate "
        "threshold, flag TRANSFER transactions that take the origin account's balance to "
        "within 1% of zero in one step. That's the verified pattern behind 96% of labeled "
        "fraud TRANSFERs, and it's rare in legitimate traffic.",
        body,
    ),
    Paragraph(
        "2. Tiered monitoring by RFM segment. Light-touch checks on high-frequency "
        "regulars, whose repeat behavior gives a stable baseline to compare against; "
        "tighter scrutiny on high-value transactions from accounts with little prior "
        "activity, which is the profile every labeled fraud CASH_OUT in this dataset "
        "matches (each is a single transaction from an account never seen before or "
        "since).",
        body,
    ),
]

story.append(Spacer(1, 6))
story.append(Paragraph("Method &amp; data notes", h2))
notes = [
    "Segmentation uses quantile RFM (4 tiers on recency, frequency, monetary), not k-means. Faster, interpretable, and doesn't need a training or scoring pipeline.",
    "The forecast is a 7-day linear trend fit on the most recent week, not ARIMA or Prophet. Full-history volume shows a level shift roughly two-thirds through the window (early days run 5-14x later days), so fitting on the recent regime instead of the full history avoids extrapolating the early high-volume trend into a negative forecast.",
    "Checked for a literal TRANSFER-to-CASH_OUT mule account chain, a shared account ID linking a fraud transfer to a later cash-out, and found it's structurally absent: 0 accounts do both, and only 3 of 8,213 fraud rows share any account link at all. The two fraud types present as independent single-hop events in this file, not a traceable chain. Reported here since it contradicts a common assumption about this dataset.",
    "Merchant accounts (nameOrig/nameDest starting \"M\") carry a zero-balance placeholder for oldbalanceDest/newbalanceDest, a known data artifact excluded from balance logic rather than treated as a signal.",
    "Balance reconciliation (oldbalanceOrg - amount vs newbalanceOrig) mismatches on 79.8% of all rows. That's a data-generation characteristic of this dataset, not a fraud indicator, noted here so it isn't mistaken for one downstream.",
]
for n in notes:
    story.append(Paragraph(f"• {n}", ParagraphStyle("note", parent=body, fontSize=8.5, leading=11, spaceAfter=3)))

doc.build(story)
print(f"wrote {ROOT / 'memo.pdf'}")
