#!/usr/bin/env python3
"""Generate a raster image with GPT Image 2.5 on fal.ai and save it to a file.

Standard library only. Needs FAL_AI_TOKEN.

  python gen-image.py "a red vinyl record on white" --out cover.png
  python gen-image.py "hero art" --quality high --size 1920x1080 --out hero.png --yes

Quality is the price. At 1024x1024 a low image costs $0.006 and a high one
costs $0.211, which is thirty-five times more for the same prompt. The default
is low on purpose: iterate there, and step up once, at the end.

A call that would cost more than --max-cost (default $0.01) refuses to run and
prints the price. Re-run it with --yes only after the person paying has said so.
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ENDPOINT = "https://fal.run/openai/gpt-image-2.5/{variant}/text-to-image"

# Published fal prices, US dollars per image. Only these six resolutions are
# priced, so only these are offered: a size we cannot price is a size we cannot
# guard. `auto`, `xhigh` and `max` quality are unpriced and deliberately absent.
PRICES = {
    (1024, 768):  {"low": 0.005, "medium": 0.037, "high": 0.145},
    (1024, 1024): {"low": 0.006, "medium": 0.053, "high": 0.211},
    (1024, 1536): {"low": 0.005, "medium": 0.042, "high": 0.165},
    (1920, 1080): {"low": 0.005, "medium": 0.040, "high": 0.158},
    (2560, 1440): {"low": 0.007, "medium": 0.056, "high": 0.222},
    (3840, 2160): {"low": 0.012, "medium": 0.101, "high": 0.401},
}
SIZES = {f"{w}x{h}": (w, h) for w, h in PRICES}


def die(msg, code=1):
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def post(url, body, token):
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(),
        headers={"Authorization": f"Key {token}",
                 "Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        die(f"HTTP {e.code}: {e.read().decode(errors='replace')[:1500]}")
    except urllib.error.URLError as e:
        die(f"Network error reaching fal: {e.reason}")


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("prompt")
    ap.add_argument("--out", required=True, help="path to write the image to")
    ap.add_argument("--quality", choices=["low", "medium", "high"], default="low")
    ap.add_argument("--size", choices=sorted(SIZES), default="1024x1024")
    ap.add_argument("--model", choices=["flare", "sunburst"], default="flare",
                    help="flare is the fast general one; sunburst is tuned for "
                         "precision. Same price.")
    ap.add_argument("--background", choices=["auto", "transparent", "opaque"],
                    default="auto", help="transparent suits icons and sprites")
    ap.add_argument("--max-cost", type=float, default=0.01, dest="max_cost",
                    help="refuse to spend more than this on one call")
    ap.add_argument("--yes", action="store_true",
                    help="confirm a call that costs more than --max-cost")
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    a = ap.parse_args()

    token = os.environ.get("FAL_AI_TOKEN")
    if not token:
        die("FAL_AI_TOKEN is not set. Get one at "
            "https://fal.ai/dashboard/keys, put it in a file, then store it with:\n"
            "  python scripts/save-key.py FAL_AI_TOKEN --from-file PATH\n"
            "Do not paste the key into a command line or a chat message.")

    out = Path(a.out)
    if out.exists():
        die(f"{out} already exists. Pick another name or delete it first.")
    if out.parent and not out.parent.exists():
        die(f"No such directory: {out.parent}")

    w, h = SIZES[a.size]
    cost = PRICES[(w, h)][a.quality]
    if cost > a.max_cost and not a.yes:
        cheaper = ", ".join(
            f"{q} ${PRICES[(w, h)][q]:.3f}"
            for q in ("low", "medium", "high") if PRICES[(w, h)][q] <= a.max_cost)
        die(f"This call costs ${cost:.3f} at {a.size} quality={a.quality}, over "
            f"the ${a.max_cost:.3f} limit. It was NOT sent.\n"
            f"Ask the person paying, then re-run with --yes.\n"
            + (f"Within the limit at this size: {cheaper}."
               if cheaper else "No quality at this size fits the limit."),
            code=2)

    d = post(ENDPOINT.format(variant=a.model),
             {"prompt": a.prompt,
              "image_size": {"width": w, "height": h},
              "quality": a.quality,
              "background": a.background,
              "output_format": "png"},
             token)

    imgs = d.get("images") or []
    if not imgs or not imgs[0].get("url"):
        die("No image in the fal response: " + json.dumps(d)[:1000])
    try:
        with urllib.request.urlopen(imgs[0]["url"], timeout=180) as r:
            data = r.read()
    except urllib.error.URLError as e:
        die(f"Could not download the generated image: {e.reason}")
    if not data.startswith(b"\x89PNG") and not data.startswith(b"\xff\xd8"):
        die(f"The response was not a PNG or JPEG ({len(data)} bytes). Not saved.")

    out.write_bytes(data)
    print(out)
    # This endpoint omits width and height; fall back to what was asked for.
    print(f"[{a.model} {a.quality} {imgs[0].get('width') or w}x"
          f"{imgs[0].get('height') or h} {len(data)} bytes ${cost:.3f}]",
          file=sys.stderr)


if __name__ == "__main__":
    main()
