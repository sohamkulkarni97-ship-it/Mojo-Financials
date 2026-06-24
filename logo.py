"""Mojo Financials logo — reproduced from the site's SVG mark, drawn in Pillow
so it can sit in the header of every post slide (color-adapts to light/dark)."""
import os
from PIL import ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
_INTER = os.path.join(HERE, "fonts", "Inter-Variable.ttf")

TEAL = (47, 122, 103)
TEAL_DEEP = (28, 79, 66)
INK = (12, 31, 27)
GOLD = (217, 164, 65)
MINT = (143, 227, 200)
CREAM = (246, 244, 238)


def _inter(size, weight=800):
    f = ImageFont.truetype(_INTER, size)
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f


def draw_logo(draw, x, y, h=58, mark=TEAL, text=INK, tagline=TEAL):
    """Draw the MOJO mark + wordmark with the top-left at (x, y). h = mark height."""
    s = h / 40.0
    w = max(int(6 * s), 3)

    def P(px, py):
        return (x + px * s, y + py * s)

    # M
    pts = [P(4, 36), P(4, 6), P(14, 20), P(24, 6), P(24, 36)]
    draw.line(pts, fill=mark, width=w, joint="curve")
    for p in pts:                      # round the joints/caps
        draw.ellipse([p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2], fill=mark)
    # O
    ocx, ocy = P(38, 21)
    r = 9 * s
    draw.ellipse([ocx - r, ocy - r, ocx + r, ocy + r], outline=mark, width=w)
    # J (third stroke — near-full ring with a small gap)
    jcx, jcy = P(47, 12)
    draw.arc([jcx - r, jcy - r, jcx + r, jcy + r], 110, 430, fill=mark, width=w)

    # wordmark + tagline
    tx = x + 64 * s + 16 * s
    fw = _inter(int(h * 0.82), 800)
    draw.text((tx, y - h * 0.04), "MOJO", font=fw, fill=text)
    ft = _inter(max(int(h * 0.2), 11), 700)
    cap = "MATH OF BUSINESS"
    draw.text((tx + 2, y + h * 0.82), " ".join(cap), font=ft, fill=tagline)
