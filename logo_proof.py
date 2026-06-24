"""Proof: the Mojo logo in the header of a light slide and a dark slide."""
import os
from PIL import Image, ImageDraw
import logo as L

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1080, 1350
M = 96


def footer(d, bg_dark=False):
    y = H - 150
    line = (40, 60, 54) if bg_dark else (221, 215, 200)
    d.line([(M, y), (W - M, y)], fill=line, width=2)
    d.text((M, y + 26), "@firm.mojo", font=L._inter(30, 800),
           fill=L.CREAM if bg_dark else L.INK)
    wa = "WhatsApp us"
    f = L._inter(26, 800)
    d.text((W - M - d.textlength(wa, font=f), y + 30), wa, font=f,
           fill=L.MINT if bg_dark else L.TEAL_DEEP)


def light_slide():
    img = Image.new("RGB", (W, H), L.CREAM)
    d = ImageDraw.Draw(img)
    L.draw_logo(d, M, 80, h=60, mark=L.TEAL_DEEP, text=L.INK, tagline=L.TEAL)
    d.text((M, 330), "D I D   Y O U   K N O W", font=L._inter(28, 800), fill=L.TEAL)
    d.text((M - 6, 470), "₹46,800", font=L._inter(220, 800), fill=L.GOLD)
    f = L._inter(46, 600)
    for i, ln in enumerate(["is the extra tax the average salaried",
                            "person pays — just by skipping",
                            "80C + 80D deductions."]):
        d.text((M, 760 + i * 60), ln, font=f, fill=L.INK)
    footer(d)
    return img


def dark_slide():
    img = Image.new("RGB", (W, H), L.INK)
    d = ImageDraw.Draw(img)
    L.draw_logo(d, M, 80, h=60, mark=L.GOLD, text=L.CREAM, tagline=L.MINT)
    d.text((M, 360), "T A X   F I L E S", font=L._inter(28, 800), fill=L.GOLD)
    f = L._inter(96, 800)
    for i, ln in enumerate(["The ₹22,000", "crore case that", "shook Indian tax"]):
        d.text((M, 480 + i * 104), ln, font=f, fill=L.CREAM)
    d.text((M, 820), "Vodafone vs India — explained simply",
           font=L._inter(34, 600), fill=L.MINT)
    footer(d, bg_dark=True)
    return img


if __name__ == "__main__":
    a, b = light_slide(), dark_slide()
    a.save(os.path.join(HERE, "output", "logo_light.png"))
    b.save(os.path.join(HERE, "output", "logo_dark.png"))
    sheet = Image.new("RGB", (int(W * 0.32) * 2 + 60, int(H * 0.32) + 40), (24, 24, 24))
    for i, im in enumerate([a, b]):
        sheet.paste(im.resize((int(W * 0.32), int(H * 0.32))), (20 + i * (int(W * 0.32) + 20), 20))
    sheet.save(os.path.join(HERE, "output", "_logo_preview.png"))
    print("wrote logo_light.png, logo_dark.png, _logo_preview.png")
