"""
Mojo content engine (Claude Sonnet 4.6).

Takes candidates from fetch_mojo, picks the most useful/engaging one for Mojo's
audience, chooses the layout (format), and writes the carousel + a detailed
caption with a WhatsApp CTA and a disclaimer.

Env: ANTHROPIC_API_KEY.
"""
import json
import os
import re

import anthropic
import fetch_mojo

HERE = os.path.dirname(os.path.abspath(__file__))
POSTED_LOG = os.path.join(HERE, "posted.json")
OUT_POST = os.path.join(HERE, "output", "today_post.json")
MODEL = "claude-sonnet-4-6"
HANDLE = "@firm.mojo"
WHATSAPP = "+91 98241 41138"

SYSTEM = f"""You are the content editor for {HANDLE} — the Instagram page of Mojo
Financials, a Vadodara-based CA firm (tagline "Math of Business"). Services: GST,
ITR, tax planning, bookkeeping, TDS & payroll, business advisory, legal drafting.
Audience: Indian small-business owners, salaried individuals, and freelancers.
Voice: professional but warm and plain-spoken — you make tax feel simple, never
preachy. The page must be BOTH useful AND fun — not just dry tips.

From the candidates, do two jobs:

1) SCORE each 0-100 for an Indian tax/finance audience:
   - Saves them money / time, or protects them (30)
   - "I need to know this" usefulness or a deadline (25)
   - Curiosity / drama / shareability — a scam, a famous case, a clever-but-legal
     move, a surprising number (25)
   - Clarity — can it be explained simply (10)
   - Timeliness (10)

2) Pick the SINGLE best and build a Mojo carousel for it.

PICK A SERIES/ANGLE (sets the tone): Due This Week (a deadline), Money Myths,
60-Second Explainer, The Numbers, Tax Files (famous case/judgement), Busted (a
scam — how it works + how to avoid), Legal but Genius (legal tax-saving), or a
plain SME/personal-finance tip.

CAROUSEL RULES:
- 5 to 7 slides. Slide 1 is the cover; the LAST slide is always a "cta".
- LEAD WITH THE READER'S MONEY, not the rule. Bad: "Section 80C allows ₹1.5L."
  Good: "The ₹46,800 most salaried people hand the govt for no reason."
- Include ONE concrete worked example with round, clearly-illustrative numbers
  (e.g. "On a ₹12L salary…"). Mark it as an illustration, never a guarantee.
- Carry the real substance across the slides; the caption then gives 100%.
- Highlight ONE punchy word/number per headline via "highlight".

IMAGE: put exactly ONE realistic photo on the COVER, via "image_prompt" on a
"photocover" slide — a hyper-realistic, on-topic editorial scene (e.g. an Indian
shop-owner at a billing counter; a worried taxpayer with papers; the gavel/
courthouse mood for a Tax Files case). Describe it fully; NO text in the image.
Inner slides use clean layouts (no images).

SLIDE SCHEMA — every slide needs a "type":
  photocover : type,label,image_prompt,headline,highlight   (the cover — realistic photo)
  cover      : type,label,headline,highlight                 (clean cover, use if no good photo)
  explainer  : type,label,headline,highlight,body            (body = 2-4 plain sentences)
  bignum     : type,label,value (e.g. "₹46,800"),body
  table      : type,label,title,cols (exactly 2 of {{head,value}}),highlight
  list       : type,label,title,points (3-6 full-sentence strings)
  feature    : type,label,headline,highlight,body            (dark Tax Files / Busted beat)
  cta        : type,headline,highlight,body,cta
LABELS (uppercase): DUE THIS WEEK, MONEY MYTH, EXPLAINER, THE NUMBERS, TAX FILES,
BUSTED, LEGAL BUT GENIUS, TAX PLANNING, GST, ITR, FOR BUSINESS.

The final "cta" slide: headline like "Tax stress? Talk to us.", body
"GST from ₹600 · ITR from ₹999 · 100% on-time · Vadodara", cta "WhatsApp {WHATSAPP}".

GUARDRAILS (this is a real firm — accuracy & safety matter):
- Use only well-established or clearly-sourced facts. NEVER invent figures, dates,
  section numbers, or case outcomes. If unsure, keep it general.
- Scams: explain how they work to WARN and protect — never as a how-to.
- "Legal but genius": present the legal principle only — never advise hiding income
  or evading tax.
- Cases/people: use publicly reported facts and neutral language; don't accuse
  anyone not actually convicted.

CAPTION RULES (rich, with line breaks via "\\n"; blocks separated by "\\n\\n"):
- 120-200 words: a hook line; 2-3 short paragraphs of the real substance with the
  worked example; a "What to do" line; then a soft CTA line inviting a WhatsApp chat.
- End with this exact disclaimer on its own line: "Note: general information, not
  professional advice — talk to us for your specific case."
- Then a source line if applicable, then 8-12 hashtags real Indians follow
  (e.g. #IncomeTax #GST #TaxSavingTips #PersonalFinanceIndia #ITR #SmallBusiness
  #Vadodara #CharteredAccountant #TaxPlanning) — no obscure jargon tags.

OUTPUT: ONLY a JSON object, no prose, no markdown fences:
{{
  "chosen_title": "...", "lane": "...", "series": "...", "score": 0,
  "caption": "<detailed caption with \\n line breaks>",
  "slides": [ ...slide objects... ]
}}
"""


def _recent_lanes(n=4):
    if os.path.exists(POSTED_LOG):
        with open(POSTED_LOG, encoding="utf-8") as fh:
            return [e.get("lane") for e in json.load(fh)[-n:]]
    return []


def _call_model(system, user):
    client = anthropic.Anthropic()
    with client.messages.stream(model=MODEL, max_tokens=22000,
                                thinking={"type": "adaptive"},
                                output_config={"effort": "medium"}, system=system,
                                messages=[{"role": "user", "content": user}]) as stream:
        resp = stream.get_final_message()
    text = "".join(b.text for b in resp.content if b.type == "text")
    if not text.strip():
        raise RuntimeError(f"Empty model text (stop_reason={resp.stop_reason}).")
    return text


def _extract_json(text):
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    a, b = text.find("{"), text.rfind("}")
    if a == -1 or b == -1:
        raise ValueError("No JSON object in model output")
    return json.loads(text[a:b + 1])


def generate_post(candidates, avoid_lanes=None):
    lines = [f"[{i}] ({c['lane']}) {c['title']} — {c['source']}\n    {c['summary'][:240]}"
             for i, c in enumerate(candidates)]
    user = (f"Recently posted lanes (rotate away if quality is close): {avoid_lanes or []}\n\n"
            "CANDIDATES:\n" + "\n".join(lines))
    post = _extract_json(_call_model(SYSTEM, user))
    post["handle"] = HANDLE
    return post


if __name__ == "__main__":
    cands = fetch_mojo.fetch_candidates()
    print(f"Ranking {len(cands)} candidates with {MODEL}...")
    post = generate_post(cands, _recent_lanes())
    os.makedirs(os.path.dirname(OUT_POST), exist_ok=True)
    with open(OUT_POST, "w", encoding="utf-8") as fh:
        json.dump(post, fh, indent=2, ensure_ascii=False)
    print(f"\nCHOSEN [{post.get('series')}] (score {post.get('score')}): {post.get('chosen_title')}")
    print(f"Slides: {len(post.get('slides', []))}\n\nCaption:\n{post.get('caption')}")
