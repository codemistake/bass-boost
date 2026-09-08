#!/usr/bin/env python3
"""Generate a raster image from a text prompt and save it to a file.

Standard library only. Two routes, chosen with --route:

  draft    fal.ai z-image/turbo. Needs FAL_AI_TOKEN.
           Under a second per image, a small fraction of a cent.
           Use it for placeholders, layout stand-ins, and iterating on wording.

  quality  OpenRouter. Needs OPENROUTER_API_KEY. Slower and dearer.
           Use it once the prompt is settled and the image ships.

  python gen-image.py "a red vinyl record on white" --out cover.png
  python gen-image.py "shop background, pixel art" --route quality --out bg.png
  python gen-image.py "sword icon" --route quality --model openai/gpt-image-2 --out sword.png

Only the saved path reaches stdout. Timing and cost go to stderr.
"""
import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

FAL_URL = "https://fal.run/fal-ai/z-image/turbo"
OR_URL = "https://openrouter.ai/api/v1/chat/completions"
OR_DEFAULT = "google/gemini-3.1-flash-image"  # Nano Banana 2
# Named sizes accepted by the fal endpoint.
FAL_SIZES = ["square", "square_hd", "portrait_4_3", "portrait_16_9",
             "landscape_4_3", "landscape_16_9"]


def die(msg):
    print(msg, file=sys.stderr)
    raise SystemExit(1)


def request(url, body, headers, timeout=300):
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", **headers}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        text = e.read().decode(errors="replace")[:1500]
        if "<!DOCTYPE html>" in text:
            die(f"HTTP {e.code}: blocked by a WAF. Too many calls from this IP. "
                "Wait a few minutes rather than retrying in a loop.")
        die(f"HTTP {e.code}: {text}")
    except urllib.error.URLError as e:
        die(f"Network error reaching {url}: {e.reason}")


def fetch(url, timeout=120):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.read()
    except urllib.error.URLError as e:
        die(f"Could not download the generated image: {e.reason}")


def route_draft(a):
    token = os.environ.get("FAL_AI_TOKEN")
    if not token:
        die("FAL_AI_TOKEN is not set. Create a key at https://fal.ai/dashboard/keys "
            "and export it.")
    d = request(FAL_URL,
                {"prompt": a.prompt, "image_size": a.size, "num_images": 1,
                 **({"seed": a.seed} if a.seed is not None else {})},
                {"Authorization": f"Key {token}"})
    imgs = d.get("images") or []
    if not imgs or not imgs[0].get("url"):
        die("No image in the fal response: " + json.dumps(d)[:1000])
    img = imgs[0]
    data = fetch(img["url"])
    t = d.get("timings", {}).get("inference")
    note = f"{img.get('width')}x{img.get('height')} seed={d.get('seed')}"
    if t:
        note += f" inference={t:.2f}s"
    return data, note


def _find_image(payload):
    """OpenRouter returns images inside the assistant message. The exact key has
    moved before, so look in the documented place and the known alternatives
    rather than crashing on a rename."""
    try:
        msg = payload["choices"][0]["message"]
    except (KeyError, IndexError):
        return None
    for entry in msg.get("images") or []:
        if isinstance(entry, str):
            return entry
        url = (entry.get("image_url") or {}).get("url") if isinstance(entry, dict) else None
        if url:
            return url
    content = msg.get("content")
    if isinstance(content, list):
        for part in content:
            if isinstance(part, dict):
                url = (part.get("image_url") or {}).get("url")
                if url:
                    return url
    return None


def route_quality(a):
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        die("OPENROUTER_API_KEY is not set. Create a key at "
            "https://openrouter.ai/keys and export it.")
    d = request(OR_URL,
                {"model": a.model or OR_DEFAULT,
                 "modalities": ["image", "text"],
                 "messages": [{"role": "user", "content": a.prompt}]},
                {"Authorization": f"Bearer {key}",
                 "HTTP-Referer": "https://github.com/codemistake/bass-boost",
                 "X-Title": "bass-boost"})
    url = _find_image(d)
    if not url:
        die("No image in the OpenRouter response. Check that the model outputs "
            "images and that the response shape has not changed:\n"
            + json.dumps(d)[:1200])
    if url.startswith("data:"):
        data = base64.b64decode(url.split(",", 1)[1])
    else:
        data = fetch(url)
    u = d.get("usage") or {}
    note = " ".join(f"{k}={u[k]}" for k in ("prompt_tokens", "completion_tokens",
                                            "cost") if k in u)
    return data, (note or "ok")


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("prompt")
    ap.add_argument("--out", required=True, help="path to write the image to")
    ap.add_argument("--route", choices=["draft", "quality"], default="draft")
    ap.add_argument("--model", help="quality route: override the model slug")
    ap.add_argument("--size", default="square_hd", choices=FAL_SIZES,
                    help="draft route only")
    ap.add_argument("--seed", type=int, help="draft route only, for a reproducible image")
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    a = ap.parse_args()

    out = Path(a.out)
    if out.exists():
        die(f"{out} already exists. Pick another name or delete it first.")
    if out.parent and not out.parent.exists():
        die(f"No such directory: {out.parent}")

    data, note = (route_draft if a.route == "draft" else route_quality)(a)
    if not data.startswith(b"\x89PNG") and not data.startswith(b"\xff\xd8"):
        die(f"The response was not a PNG or JPEG ({len(data)} bytes). Not saved.")
    out.write_bytes(data)
    print(out)
    print(f"[{a.route} {len(data)} bytes {note}]", file=sys.stderr)


if __name__ == "__main__":
    main()
