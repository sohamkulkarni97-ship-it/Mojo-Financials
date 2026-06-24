"""
Mojo Financials carousel renderer — content-driven layouts in the Mojo brand
(teal / gold / cream), logo on every slide. The content engine picks the layout
(format) that fits each story; this just renders it.

Layouts: cover, bignum, table, list, feature (dark Tax Files/Busted), cta.

Usage:
    python render_mojo.py                 # renders sample_mojo.json
    python render_mojo.py path/post.json
"""
import json
import os
import sys

from PIL import Image, ImageDraw
import logo as L

W, H = 1080, 1350
M = 96
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output")

CREAM, INK, TEAL, TEAL_DEEP = L.CREAM, L.INK, L.TEAL, L.TEAL_DEEP
GOLD, MINT = L.GOLD, L.MINT
INK_SOFT = (40, 66, 59)
TINT = (233, 241, 236)
RULE_L = (221, 215, 200)
RULE_D = (40, 60, 54)

LOGO = os.path.join(HERE, "assets", "logo.png")
_logo_cache = {}


def _logo(dark):
    if dark in _logo_cache:
        return _logo_cache[dark]
    im = Image.open(LOGO).convert("RGBA")
    if dark:                            # recolor teal -> cream silhouette for dark slides
        alpha = im.split()[3]
        solid = Image.new("RGBA", im.size, CREAM + (255,))
        im = Image.composite(solid, Image.new("RGBA", im.size, (0, 0, 0, 0)), alpha)
    _logo_cache[dark] = im
    return im


def place_logo(img, dark=False, h=104, x=M, y=72):
    lg = _logo(dark)
    lg = lg.resize((int(lg.width * h / lg.height), h))
    img.paste(lg, (x, y), lg)


def paste_cover_photo(img, path):
    """Full-bleed cover-fit a realistic photo + a top/bottom dark gradient for text."""
    ph = Image.open(path).convert("RGB")
    sc = max(W / ph.width, H / ph.height)
    ph = ph.resize((int(ph.width * sc), int(ph.height * sc)))
    img.paste(ph, ((W - ph.width) // 2, (H - ph.height) // 2))
    col = Image.new("L", (1, H))
    cp = col.load()
    for y in range(H):
        top = max(0, (210 - y) / 210) * 135
        bot = max(0, (y - H * 0.46) / (H * 0.54)) * 240
        cp[0, y] = int(min(255, max(top, bot)))
    img.paste(Image.new("RGB", (W, H), INK), (0, 0), col.resize((W, H)))


def inter(s, w=700):
    return L._inter(s, w)


def tlen(d, t, f):
    return d.textlength(t, font=f)


def _wrap(d, words, f, maxw):
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if tlen(d, t, f) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def para(d, text, box, size=40, fill=INK, weight=500, leading=1.36, min_size=22, align="left"):
    bx, by, bw, bh = box
    words = (text or "").split()
    s = size
    while s > min_size:
        f = inter(s, weight)
        if len(_wrap(d, words, f, bw)) * int(s * leading) <= bh:
            break
        s -= 2
    f = inter(s, weight)
    lh = int(s * leading)
    y = by
    for ln in _wrap(d, words, f, bw):
        x = bx + (bw - tlen(d, ln, f)) / 2 if align == "center" else bx
        d.text((x, y), ln, font=f, fill=fill)
        y += lh
    return y


def headline(d, text, box, color, hi=None, hi_color=None, max_size=104, weight=800, valign="top"):
    bx, by, bw, bh = box
    words = text.split()
    hiset = set((hi or "").upper().split())
    size = max_size
    while size > 34:
        f = inter(size, weight)
        lines = _wrap(d, words, f, bw)
        if len(lines) * int(size * 1.06) <= bh and all(tlen(d, l, f) <= bw for l in lines):
            break
        size -= 3
    f = inter(size, weight)
    lh = int(size * 1.06)
    lines = _wrap(d, words, f, bw)
    y = by + (bh - len(lines) * lh) if valign == "bottom" else by
    sp = tlen(d, " ", f)
    for ln in lines:
        x = bx
        for word in ln.split():
            c = hi_color if word.upper().strip(",.:;") in hiset else color
            d.text((x, y), word, font=f, fill=c)
            x += tlen(d, word, f) + sp
        y += lh


def label(d, text, y, color, pill=False, pill_bg=None, pill_fg=None):
    text = text.upper()
    if pill:
        f = inter(28, 800)
        w = tlen(d, text, f)
        d.rounded_rectangle([M, y, M + w + 40, y + 56], radius=8, fill=pill_bg)
        d.text((M + 20, y + 13), text, font=f, fill=pill_fg)
    else:
        f = inter(26, 800)
        x = M
        for ch in text:                 # letter-spaced caps
            d.text((x, y), ch, font=f, fill=color)
            x += tlen(d, ch, f) + 6


def footer(d, ctx, dark=False, swipe=False):
    y = H - 150
    d.line([(M, y), (W - M, y)], fill=RULE_D if dark else RULE_L, width=2)
    d.text((M, y + 26), ctx["handle"], font=inter(30, 800), fill=CREAM if dark else INK)
    if swipe:
        right, rc = "SWIPE →", (MINT if dark else TEAL_DEEP)
    else:
        right, rc = "WhatsApp us", (MINT if dark else TEAL_DEEP)
    f = inter(26, 800)
    d.text((W - M - tlen(d, right, f), y + 30), right, font=f, fill=rc)


# ---- layouts ----------------------------------------------------------------
def s_cover(d, s, ctx):
    label(d, s.get("label", "MOJO"), 250, TEAL)
    headline(d, s["headline"], (M, 330, W - 2 * M, 560), INK,
             hi=s.get("highlight"), hi_color=TEAL_DEEP, max_size=104, valign="bottom")
    d.rectangle([M, 940, M + 70, 948], fill=GOLD)
    footer(d, ctx, swipe=True)


def s_bignum(d, s, ctx):
    label(d, s.get("label", "DID YOU KNOW"), 300, TEAL)
    big = inter(200, 800)
    d.text((M - 6, 430), s["value"], font=big, fill=GOLD)
    para(d, s.get("body", ""), (M, 720, W - 2 * M, 320), size=46, fill=INK, weight=600)
    footer(d, ctx)


def s_table(d, s, ctx):
    label(d, s.get("label", "THE MATH"), 250, TEAL)
    headline(d, s.get("title", ""), (M, 320, W - 2 * M, 200), INK, max_size=72)
    cols = s.get("cols", [])[:2]
    gap, top, ch = 24, 560, 260
    cw = (W - 2 * M - gap) // 2
    for i, col in enumerate(cols):
        x = M + i * (cw + gap)
        d.rounded_rectangle([x, top, x + cw, top + ch], radius=14, fill=TINT)
        d.text((x + 28, top + 30), col.get("head", "").upper(), font=inter(28, 800), fill=TEAL_DEEP)
        d.text((x + 28, top + 90), col.get("value", ""), font=inter(96, 800), fill=INK)
    if s.get("highlight"):
        hy = top + ch + 28
        d.rounded_rectangle([M, hy, W - M, hy + 90], radius=14, fill=GOLD)
        f = inter(40, 800)
        d.text((M + 28, hy + 22), s["highlight"], font=f, fill=(58, 42, 6))
    footer(d, ctx)


def s_list(d, s, ctx):
    label(d, s.get("label", "AVOID THIS"), 250, TEAL)
    headline(d, s.get("title", ""), (M, 320, W - 2 * M, 200), INK, max_size=66)
    pts = s.get("points", [])[:6]
    top, avail = 560, 540
    size = 38
    while size > 24:
        f = inter(size, 600)
        lh, gap, bsz = int(size * 1.25), int(size * 0.7), int(size * 1.5)
        wr = [_wrap(d, p.split(), f, W - 2 * M - bsz - 20) for p in pts]
        if sum(len(w) * lh + gap for w in wr) <= avail:
            break
        size -= 2
    f = inter(size, 600)
    lh, gap, bsz = int(size * 1.25), int(size * 0.7), int(size * 1.5)
    fb = inter(int(size * 0.85), 800)
    y = top
    for i, lines in enumerate(wr, 1):
        d.ellipse([M, y, M + bsz, y + bsz], fill=TEAL)
        nw = tlen(d, str(i), fb)
        d.text((M + bsz / 2 - nw / 2, y + bsz * 0.22), str(i), font=fb, fill=CREAM)
        yy = y
        for ln in lines:
            d.text((M + bsz + 20, yy), ln, font=f, fill=INK)
            yy += lh
        y = yy + gap
    footer(d, ctx)


def s_feature(d, s, ctx):
    label(d, s.get("label", "TAX FILES"), 320, GOLD)
    headline(d, s["headline"], (M, 430, W - 2 * M, 420), CREAM,
             hi=s.get("highlight"), hi_color=GOLD, max_size=104)
    if s.get("body"):
        para(d, s["body"], (M, 900, W - 2 * M, 150), size=34, fill=MINT, weight=600)
    footer(d, ctx, dark=True, swipe=True)


def s_cta(d, s, ctx):
    headline(d, s.get("headline", "Tax stress? Talk to us."),
             (M, 360, W - 2 * M, 360), CREAM, hi=s.get("highlight"), hi_color=GOLD,
             max_size=110, valign="center")
    para(d, s.get("body", "GST from ₹600 · ITR from ₹999 · 100% on-time filing"),
         (M, 780, W - 2 * M, 120), size=40, fill=MINT, weight=600)
    if s.get("cta"):
        f = inter(38, 800)
        w = tlen(d, s["cta"], f)
        d.rounded_rectangle([M, 940, M + w + 56, 1012], radius=36, fill=(37, 211, 102))
        d.text((M + 28, 958), s["cta"], font=f, fill=(255, 255, 255))
    footer(d, ctx, dark=True)


def s_explainer(d, s, ctx):
    label(d, s.get("label", "EXPLAINER"), 250, TEAL)
    headline(d, s.get("headline", ""), (M, 320, W - 2 * M, 280), INK,
             hi=s.get("highlight"), hi_color=TEAL_DEEP, max_size=78)
    para(d, s.get("body", ""), (M, 640, W - 2 * M, 470), size=42, fill=INK_SOFT, weight=500)
    footer(d, ctx)


def s_photocover(d, s, ctx):
    label(d, s.get("label", "TAX PLANNING"), 700, GOLD)
    headline(d, s["headline"], (M, 762, W - 2 * M, 330), CREAM,
             hi=s.get("highlight"), hi_color=GOLD, max_size=92, valign="top")
    footer(d, ctx, dark=True, swipe=True)


_R = {"cover": s_cover, "bignum": s_bignum, "table": s_table, "list": s_list,
      "feature": s_feature, "cta": s_cta, "photocover": s_photocover,
      "explainer": s_explainer}
_BG = {"feature": INK, "cta": TEAL_DEEP, "photocover": INK}


def render_post(post, out_dir=OUT):
    os.makedirs(out_dir, exist_ok=True)
    ctx = {"handle": post.get("handle", "@firm.mojo"), "total": len(post["slides"])}
    paths = []
    for i, s in enumerate(post["slides"], 1):
        s["index"] = i
        img = Image.new("RGB", (W, H), _BG.get(s.get("type"), CREAM))
        if s.get("type") == "photocover" and s.get("image"):
            paste_cover_photo(img, os.path.join(HERE, s["image"]))
        _R.get(s.get("type"), s_cover)(ImageDraw.Draw(img), s, ctx)
        place_logo(img, dark=s.get("type") in ("feature", "cta", "photocover"))
        p = os.path.join(out_dir, f"slide_{i:02d}.png")
        img.save(p)
        paths.append(p)
    sc = 0.26
    tw_, th_ = int(W * sc), int(H * sc)
    sheet = Image.new("RGB", (len(paths) * (tw_ + 16) + 16, th_ + 32), (24, 24, 24))
    for i, p in enumerate(paths):
        sheet.paste(Image.open(p).resize((tw_, th_)), (16 + i * (tw_ + 16), 16))
    sheet.save(os.path.join(out_dir, "_preview.png"))
    return paths


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "sample_mojo.json")
    with open(path, encoding="utf-8") as fh:
        post = json.load(fh)
    print(f"Rendered {len(render_post(post))} slides -> {OUT}")
