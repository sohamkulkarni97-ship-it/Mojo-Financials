"""
Mojo image generator (OpenAI gpt-image-1) — now with VISUAL MODES so the page
stops looking the same every day. The content engine picks a mode per image:

  editorial : hyper-real premium photo — authentic human/business moments
  noir      : cinematic, moody, high-contrast — scams, fraud, court cases
  concept   : bold conceptual still-life / visual metaphor — modern & graphic
  bright    : optimistic, aspirational lifestyle — tax-saving wins, relief

All modes stay inside the Mojo world (deep-teal / gold / cream) but with very
different energy, lighting and subject — so a scam post and a savings post no
longer look like the same beige office photo.

Portrait 1024x1536 to fit the 4:5 canvas. Env: OPENAI_API_KEY.
"""
import base64
import os

from openai import OpenAI

MODEL = "gpt-image-1"

BASE = (
    "Vertical 4:5 portrait composition. Absolutely NO text, words, numbers, logos, "
    "watermarks or signage anywhere in the image. Keep one area (upper or lower third) "
    "calm and uncluttered so a headline can be overlaid later. Premium, intentional, "
    "scroll-stopping — never generic stock photography. "
)

MODES = {
    "editorial": (
        "Hyper-realistic premium editorial PHOTOGRAPH of an authentic Indian business or "
        "personal-finance moment. Cinematic soft natural light, shallow depth of field, "
        "sharp focus, real human emotion and storytelling detail. Warm modern tone that "
        "complements a deep-teal and gold brand. "
    ),
    "noir": (
        "Cinematic, moody, HIGH-CONTRAST film-noir style for a tense money story (a scam, "
        "fraud, or a courtroom/tax-case mood). Dramatic hard shadows, a single shaft of "
        "light, deep teal-black atmosphere with a gold rim-light accent, sense of suspense "
        "and consequence. Photoreal but stylized and dramatic. "
    ),
    "concept": (
        "Bold CONCEPTUAL still-life / visual metaphor on a clean modern studio backdrop. "
        "One striking hero object or simple symbolic arrangement, dramatic directional "
        "lighting, graphic and minimal, premium product-shot quality. Deep teal or warm "
        "cream background with a confident gold accent. Make the metaphor instantly readable. "
    ),
    "bright": (
        "Bright, optimistic, ASPIRATIONAL lifestyle photograph — a relieved or genuinely "
        "happy Indian person, or a clean modern success scene. Airy daylight, fresh and "
        "hopeful mood, premium and uplifting, subtle teal/gold accents in the scene. "
    ),
}


def generate(prompt, out_path, mode="editorial", quality="high", size="1024x1536"):
    client = OpenAI()
    style = MODES.get(mode, MODES["editorial"])
    res = client.images.generate(
        model=MODEL, prompt=BASE + style + "Scene: " + prompt,
        size=size, quality=quality, n=1,
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "wb") as fh:
        fh.write(base64.b64decode(res.data[0].b64_json))
    return out_path


if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "concept"
    p = sys.argv[2] if len(sys.argv) > 2 else (
        "a single matchstick shaped like a tiny burning rupee note, thin smoke curling up, "
        "dark dramatic background — money quietly going up in flames")
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "photo_test.png")
    generate(p, out, mode=mode)
    print("wrote", out, "mode:", mode)
