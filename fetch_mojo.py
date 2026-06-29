"""
Mojo — source fetcher. Three streams feed the content engine:
  1. TIMELY   — tax/finance/legal news (RSS)
  2. CALENDAR — "Due this week" compliance deadlines (date-driven, no feed)
  3. EVERGREEN — a story bank of cases / scams / concepts for slow days

Returns a deduped candidate list (skips anything in posted.json).
"""
import datetime as dt
import json
import os
import re

import feedparser

HERE = os.path.dirname(os.path.abspath(__file__))
POSTED_LOG = os.path.join(HERE, "posted.json")
MAX_AGE_HOURS = 60
PER_FEED = 8

FEEDS = {
    "tax": [
        "https://taxguru.in/feed/",
        "https://economictimes.indiatimes.com/wealth/rssfeeds/837555174.cms",
        "https://www.livemint.com/rss/money",
        "https://www.moneycontrol.com/rss/personal-finance.xml",
    ],
    "business": [
        "https://economictimes.indiatimes.com/small-biz/rssfeeds/5575607.cms",
        "https://www.business-standard.com/rss/finance-103.rss",
    ],
}

# Monthly-recurring compliance dates (day-of-month -> what's due)
MONTHLY = {
    7: "TDS / TCS payment for the previous month",
    11: "GSTR-1 for monthly filers",
    13: "GSTR-1 / IFF for QRMP filers",
    15: "PF & ESI payment; advance-tax installment (quarter-end months)",
    20: "GSTR-3B for monthly filers",
    25: "GST PMT-06 challan for QRMP filers",
}
# Annual fixed dates (month, day) -> what's due
ANNUAL = {
    (6, 15): "First advance-tax installment (15%)",
    (7, 31): "Income Tax Return filing (non-audit cases)",
    (9, 15): "Second advance-tax installment (45%)",
    (9, 30): "Tax audit report (Form 3CD)",
    (10, 31): "ITR filing for audit cases",
    (12, 15): "Third advance-tax installment (75%)",
    (3, 15): "Final advance-tax installment (100%)",
    (3, 31): "End of financial year — last day for tax-saving investments",
}

EVERGREEN = [
    ("Vodafone vs India — the ₹22,000 crore retrospective tax case", "2007 Vodafone-Hutchison offshore deal; India's capital-gains demand; Supreme Court ruled for Vodafone in 2012; govt's retrospective amendment; India lost the 2020 international arbitration; the retro tax law was scrapped in 2021."),
    ("Old vs New tax regime — which actually saves you more", "New regime: lower slabs, almost no deductions. Old regime: higher slabs but 80C/80D/HRA etc. Breakeven depends on how many deductions you claim."),
    ("How the fake-GST-invoice (fake ITC) racket works", "Shell firms raise invoices without any real supply; buyers fraudulently claim input tax credit; detected via e-way-bill and GSTR-1 vs 3B mismatches; heavy penalties and arrest provisions."),
    ("ESOP taxation in India, explained", "Taxed twice — as a perquisite at exercise and as capital gains at sale; eligible startups get a tax-deferment on the perquisite."),
    ("Pvt Ltd vs LLP vs Proprietorship — what to choose", "Trade-offs in liability protection, compliance cost, tax rate, and ability to raise funds."),
    ("McDowell case — tax planning vs tax avoidance vs evasion", "Landmark 1985 Supreme Court case on the line between legitimate planning and unacceptable avoidance; led toward GAAR."),
    ("Section 80C — the ₹1.5 lakh deduction most people underuse", "ELSS, PPF, EPF, life insurance premium, home-loan principal, children's tuition all qualify under one ₹1.5L cap."),
    ("HRA exemption and the fake-rent-receipt trap", "How HRA exemption is calculated; bogus receipts (often to relatives) are a common scam; the department now cross-checks the landlord's PAN and AIS."),
    ("Presumptive taxation (44AD / 44ADA) for small businesses & professionals", "Declare a flat 6–8% of turnover (44AD) or 50% of receipts (44ADA), skip detailed books, within turnover limits."),
    ("Advance tax — the 234B/234C interest trap", "If your tax liability exceeds ₹10,000, you must pay in installments; shortfalls attract monthly interest."),
    ("How big companies legally cut their tax bill", "Holding-company structures, IP licensing, SEZ benefits and timing — legal planning, distinct from evasion."),
    ("Capital gains on stocks & mutual funds — STCG vs LTCG", "Holding periods decide the rate; equity LTCG up to ₹1.25 lakh a year is exempt."),
    ("Common ITR mistakes that trigger a notice", "Income not matching AIS/26AS, unreported savings interest, picking the wrong ITR form."),
    ("Gifts and tax under Section 56", "Gifts above ₹50,000 a year are taxable — but gifts from specified relatives and on marriage are exempt."),
    ("NPS — the extra ₹50,000 deduction under 80CCD(1B)", "Over and above the ₹1.5 lakh 80C limit."),
    # --- Relatable PERSONAL money "gotchas" (the format that performs best) ---
    ("Clubbing of income — why putting investments in your spouse's name doesn't save tax", "Under Section 64, income from assets you gift to your spouse or minor child is added back to YOUR income and taxed in your hands — a common 'save tax in the family' move that quietly backfires."),
    ("Your minor child's income gets clubbed too", "Interest and earnings on investments held in a minor's name are added to the higher-earning parent's income under Section 64(1A), with only a small ₹1,500-per-child exemption."),
    ("Joint home loan — who really gets the tax deduction", "Both co-borrowers can claim interest (up to ₹2L each) and principal (80C) — but only on their share of ownership AND the EMI they actually pay; adding a non-paying spouse to the loan doesn't multiply the benefit."),
    ("How much gold can you keep at home without trouble", "A CBDT instruction sets quantities (e.g. ~500g for a married woman) that won't be seized in a search — but that's about seizure, NOT a tax exemption; unexplained gold can still be taxed."),
    ("The ₹2 lakh cash limit most people don't know — Section 269ST", "Accepting ₹2,00,000 or more in cash in a single transaction, day or event can attract a penalty equal to the amount received — it quietly hits weddings, property deals and big cash purchases."),
    ("Tax on your savings & FD interest — the AIS mismatch trap", "Bank interest is pre-filled in your AIS; assuming 'TDS was deducted so I'm done' and leaving it out is a top reason ordinary taxpayers get a notice. 80TTA/80TTB give a small deduction."),
    ("Selling inherited property or ancestral gold — how it's actually taxed", "Inheritance itself is tax-free, but when you SELL, capital gains apply using the original owner's cost and holding period — many heirs are caught off guard by the bill."),
    ("PF withdrawal before 5 years can be taxable", "Withdraw your EPF before 5 years of continuous service and the employer's contribution, interest and earlier 80C benefit can all become taxable, often with TDS."),
    ("Wedding gifts and family gifts — what's actually tax-free", "Gifts received on your marriage are fully exempt and gifts from specified relatives (parents, siblings, spouse) are exempt — but a ₹60,000 gift from a friend is taxable as income."),
    ("Gifting cash to your wife to invest — the gift is free, the income isn't", "A gift to your spouse isn't taxed in her hands, BUT any income she earns from investing it is clubbed back to you under Section 64 — so the tax-saving plan quietly fails."),
    ("Paying rent to your own parents for HRA — legal, if you do it right", "You CAN claim HRA on rent paid to parents who own the home — but it must be real (actual transfer, they declare the rent as income); fake arrangements get caught via PAN and AIS."),
    ("Buying a flat over ₹50 lakh? The BUYER must deduct 1% TDS", "Section 194-IA makes the buyer responsible for deducting and depositing 1% TDS on property above ₹50L — miss it and the penalty and interest fall on the buyer, not the seller."),
    ("Buying property from an NRI — the TDS trap that costs lakhs", "Buying from a resident is 1% TDS; buying from an NRI means deducting much higher TDS (20%+ on gains/value) — the buyer is liable, and getting it wrong is an expensive mistake."),
    ("Paying rent above ₹50,000 a month? You must deduct TDS", "Section 194-IB requires a tenant paying over ₹50,000/month to deduct 5% TDS once a year — a rule most individual tenants have never heard of."),
    ("Switching mutual funds is a SALE — and it's taxable", "Moving money between schemes (even within the same fund house, or regular-to-direct) counts as a redemption, triggering capital gains tax — 'switching' is not tax-free."),
    ("Dividends used to be tax-free — not anymore", "Since FY 2020-21 dividends are fully taxable in your hands at your slab rate, and companies deduct 10% TDS above ₹5,000 a year — a surprise for many long-term investors."),
    ("Made money on crypto? 30% flat. Lost money? You still can't offset it", "Virtual digital assets are taxed at a flat 30% with 1% TDS on transfers, and losses can't be set off against other income or even other crypto gains — one of the harshest regimes in the Act."),
    ("Won a game show, lottery or online game? You keep about 70%", "Winnings are taxed at a flat 30% (plus cess) with TDS deducted upfront, and NO deductions or basic-exemption benefit apply — Section 115BB / 194B."),
]


def _clean(t):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", t or "")).strip()


def _key(t):
    return re.sub(r"[^a-z0-9]+", "", (t or "").lower())[:60]


def _load_posted():
    if os.path.exists(POSTED_LOG):
        with open(POSTED_LOG, encoding="utf-8") as fh:
            return {e["key"] for e in json.load(fh)}
    return set()


def _due_this_week(posted, seen):
    out, today = [], dt.date.today()
    for delta in range(0, 7):
        day = today + dt.timedelta(days=delta)
        hits = []
        if day.day in MONTHLY:
            hits.append(MONTHLY[day.day])
        if (day.month, day.day) in ANNUAL:
            hits.append(ANNUAL[(day.month, day.day)])
        for what in hits:
            when = "today" if delta == 0 else ("tomorrow" if delta == 1 else day.strftime("%d %b"))
            title = f"Due {when}: {what}"
            k = _key(title)
            if k in seen or k in posted:
                continue
            seen.add(k)
            out.append({"key": k, "lane": "compliance", "title": title,
                        "summary": f"{what} is due on {day.strftime('%d %B %Y')}. Late filing/payment attracts interest and penalties.",
                        "source": "Compliance calendar", "link": ""})
    return out


def fetch_candidates():
    posted, seen, out = _load_posted(), set(), []
    now = dt.datetime.now(dt.timezone.utc)
    for lane, urls in FEEDS.items():
        for url in urls:
            try:
                feed = feedparser.parse(url)
            except Exception:
                continue
            for e in feed.entries[:PER_FEED]:
                title = _clean(e.get("title"))
                k = _key(title)
                if not title or k in seen or k in posted:
                    continue
                pub = e.get("published_parsed") or e.get("updated_parsed")
                if pub and (now - dt.datetime(*pub[:6], tzinfo=dt.timezone.utc)) > dt.timedelta(hours=MAX_AGE_HOURS):
                    continue
                seen.add(k)
                body = ""
                if e.get("content"):
                    body = e["content"][0].get("value", "")
                body = body or e.get("summary", "")
                out.append({"key": k, "lane": lane, "title": title,
                            "summary": _clean(body)[:1500],
                            "source": feed.feed.get("title") or url.split("/")[2],
                            "link": e.get("link", "")})
    out.extend(_due_this_week(posted, seen))
    for title, summary in EVERGREEN:                 # always available as fallback
        k = _key(title)
        if k in seen or k in posted:
            continue
        seen.add(k)
        out.append({"key": k, "lane": "evergreen", "title": title,
                    "summary": summary, "source": "Mojo explainer", "link": ""})
    return out


if __name__ == "__main__":
    items = fetch_candidates()
    by = {}
    for it in items:
        by.setdefault(it["lane"], []).append(it)
    print(f"{len(items)} candidates across {len(by)} streams\n")
    for lane, lst in by.items():
        print(f"=== {lane.upper()} ({len(lst)}) ===")
        for it in lst[:4]:
            print("  -", it["title"][:80])
        print()
