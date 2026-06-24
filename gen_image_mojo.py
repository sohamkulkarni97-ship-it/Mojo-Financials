"""
Mojo image generator — HYPER-REALISTIC editorial photography (OpenAI gpt-image-1).
Used for photo covers / feature slides. Portrait 1024x1536 to fit the 4:5 canvas.

Env: OPENAI_API_KEY (same key as DECODE).
"""
import base64
import os

from openai import OpenAI

MODEL = "gpt-image-1"

STYLE = (
    "Hyper-realistic, photorealistic premium editorial photograph. Professional, clean and "
    "sophisticated, cinematic soft natural lighting, shallow depth of field, sharp focus, "
    "fine detail, high dynamic range. Indian business and finance context. Tasteful, modern, "
    "muted warm tones that sit well with a deep-teal and gold brand. Absolutely no text, "
    "words, numbers, logos, or watermarks anywhere in the image. Scene: "
)


def generate(prompt, out_path, quality="high", size="1024x1536"):
    client = OpenAI()
    res = client.images.generate(
        model=MODEL, prompt=STYLE + prompt, size=size, quality=quality, n=1,
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "wb") as fh:
        fh.write(base64.b64decode(res.data[0].b64_json))
    return out_path


if __name__ == "__main__":
    import sys
    p = sys.argv[1] if len(sys.argv) > 1 else (
        "an Indian chartered accountant at a modern office desk reviewing financial "
        "statements, a calculator, a laptop and neat stacks of Indian rupee notes, warm "
        "window light, shallow depth of field, professional and trustworthy mood")
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "photo_test.png")
    generate(p, out)
    print("wrote", out)
