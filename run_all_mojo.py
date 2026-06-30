"""
Mojo content build (no publishing).
fetch -> Sonnet pick+write -> realistic cover photo -> render.
Produces output/today_post.json and output/slide_XX.png.
"""
import json
import os

import fetch_mojo
import pick_and_write_mojo as pw
import render_mojo

HERE = pw.HERE
IMG_QUALITY = os.environ.get("MOJO_IMG_QUALITY", "high")   # "high" or "medium"


def _fallback(s):
    """If an image can't be generated, swap the photo slide for a clean text layout."""
    if s.get("type") == "photocover":
        s["type"] = "cover"
    elif s.get("type") == "photofeature":
        s["type"] = "feature"                 # dark text beat
        s.setdefault("body", s.get("caption", ""))


def _add_photos(post):
    if not os.environ.get("OPENAI_API_KEY"):
        print("[note] OPENAI_API_KEY not set — image slides use clean layouts.")
        for s in post["slides"]:
            _fallback(s)
        return
    import gen_image_mojo
    for i, s in enumerate(post["slides"]):
        prompt = s.get("image_prompt")
        if not prompt:
            continue
        mode = s.get("image_mode", "editorial")
        rel = os.path.join("assets", f"gen_{i:02d}.png")
        try:
            gen_image_mojo.generate(prompt, os.path.join(HERE, rel), mode=mode,
                                    quality=IMG_QUALITY)
            s["image"] = rel
            print(f"  photo [{mode}] -> {rel}  ({prompt[:46]}...)")
        except Exception as e:
            print(f"  [warn] photo gen failed ({e}); slide falls back to clean layout.")
            _fallback(s)


def main():
    cands = fetch_mojo.fetch_candidates()
    if not cands:
        raise SystemExit("No candidates.")
    print(f"Fetched {len(cands)} candidates.")
    post = pw.generate_post(cands, pw._recent_lanes(), pw._recent_titles())
    print(f"Chosen [{post.get('series')}] (score {post.get('score')}): {post.get('chosen_title')}")
    _add_photos(post)
    out = os.path.join(HERE, "output", "today_post.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(post, fh, indent=2, ensure_ascii=False)
    print(f"Rendered {len(render_mojo.render_post(post))} slides.")


if __name__ == "__main__":
    main()
