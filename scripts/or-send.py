#!/usr/bin/env python3
"""Ask an OpenRouter model a question about a local file, without the file
passing through the calling agent's context window.

Standard library only. Needs OPENROUTER_API_KEY in the environment.

  python or-send.py FILE --ask "question" [--model SLUG] [--max-tokens N]

The route is chosen by extension:
  audio (.wav .mp3 .flac .m4a .ogg .webm .aac) -> /audio/transcriptions
  video (.mp4 .webm .mov .mkv)                 -> /chat/completions, video_url
  anything else                                -> /chat/completions, as text

Only the answer reaches stdout. Cost and token counts go to stderr.
"""
import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

API = "https://openrouter.ai/api/v1"
TEXT_MODEL = "~google/gemini-flash-latest"
AUDIO_MODEL = "nvidia/parakeet-tdt-0.6b-v3"

AUDIO_FMT = {".wav": "wav", ".mp3": "mp3", ".flac": "flac", ".m4a": "m4a",
             ".ogg": "ogg", ".webm": "webm", ".aac": "aac"}
VIDEO_MIME = {".mp4": "video/mp4", ".mov": "video/quicktime",
              ".mkv": "video/x-matroska", ".webm": "video/webm"}
# .webm is both; treat it as audio only when the caller says so.
VIDEO_LIMIT = 20 * 1024 * 1024
TEXT_LIMIT = 400_000  # characters, roughly 100k tokens

DEFAULT_ASK = ("Summarize what this contains and what matters in it. "
               "Quote exact lines for anything you claim.")
DEFAULT_VIDEO_ASK = (
    "Describe what happens in this recording, step by step. Note where "
    "something goes wrong, with timestamps, and quote on-screen text exactly.")


def die(msg):
    print(msg, file=sys.stderr)
    raise SystemExit(1)


def post(path, body):
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        die("OPENROUTER_API_KEY is not set. Get one at "
            "https://openrouter.ai/keys. Ask for it in a file, take the path,\n"
            "and store it yourself. Do not hand this command to the user:\n"
            "  python scripts/save-key.py OPENROUTER_API_KEY --from-file PATH\n"
            "A key must never reach a command line or a chat message.")
    req = urllib.request.Request(
        f"{API}{path}",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {key}",
                 "Content-Type": "application/json",
                 "HTTP-Referer": "https://github.com/codemistake/bass-boost",
                 "X-Title": "bass-boost"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=900) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")[:2000]
        if "<!DOCTYPE html>" in body:
            die(f"HTTP {e.code}: blocked by OpenRouter's WAF. Too many calls "
                "from this IP. Wait a few minutes; retrying in a loop extends "
                "the block.")
        die(f"HTTP {e.code}: {body}")
    except urllib.error.URLError as e:
        die(f"Network error: {e.reason}")


def report(d, extra=""):
    u = d.get("usage") or {}
    bits = [f"{k}={u[k]}" for k in ("prompt_tokens", "completion_tokens", "cost")
            if k in u]
    if d.get("id"):
        bits.append(f"id={d['id']}")
    if extra:
        bits.insert(0, extra)
    if bits:
        print("[" + " ".join(bits) + "]", file=sys.stderr)


def chat(model, parts, max_tokens):
    d = post("/chat/completions", {
        "model": model,
        "reasoning": {"effort": "low"},
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": parts}],
    })
    try:
        return d["choices"][0]["message"]["content"], d
    except (KeyError, IndexError):
        die("Unexpected response: " + json.dumps(d)[:2000])


def run_audio(p, a):
    fmt = AUDIO_FMT[p.suffix.lower()]
    body = {"model": a.model or AUDIO_MODEL,
            "input_audio": {"data": base64.b64encode(p.read_bytes()).decode(),
                            "format": fmt}}
    if a.lang:
        body["language"] = a.lang
    d = post("/audio/transcriptions", body)
    text = d.get("text")
    if text is None:
        die("No transcript in response: " + json.dumps(d)[:2000])
    print(text)
    report(d, f"seconds={d.get('seconds')}" if d.get("seconds") else "")


def run_video(p, a):
    size = p.stat().st_size
    if size > VIDEO_LIMIT:
        die(f"{p.name} is {size / 1e6:.1f} MB. Base64 adds a third on top and "
            f"requests above about {VIDEO_LIMIT / 1e6:.0f} MB are rejected. Shrink it:\n"
            f"  ffmpeg -i {p.name} -vf scale=-2:720 -r 10 -an -crf 32 out.mp4")
    mime = VIDEO_MIME.get(p.suffix.lower(), "video/mp4")
    url = f"data:{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"
    out, d = chat(a.model or TEXT_MODEL,
                  [{"type": "text", "text": a.ask or DEFAULT_VIDEO_ASK},
                   {"type": "video_url", "video_url": {"url": url}}],
                  a.max_tokens)
    print(out)
    report(d)


def run_text(p, a):
    try:
        text = p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        die(f"{p.name} is not UTF-8 text. If it is media, use a recognized "
            "extension so the right route is chosen.")
    if len(text) > TEXT_LIMIT and not a.force:
        die(f"{p.name} is {len(text)} characters, over the {TEXT_LIMIT} "
            "guard. Narrow it first with grep or sed, or pass --force to send "
            "it whole and pay for every token.")
    prompt = (f"{a.ask or DEFAULT_ASK}\n\n"
              f"--- begin {p.name} ---\n{text}\n--- end {p.name} ---")
    out, d = chat(a.model or TEXT_MODEL,
                  [{"type": "text", "text": prompt}], a.max_tokens)
    print(out)
    report(d, f"chars={len(text)}")


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--ask", help="the question to answer about the file")
    ap.add_argument("--model", help="override the model slug")
    ap.add_argument("--lang", help='audio only: ISO-639-1 hint, e.g. "ru"')
    ap.add_argument("--max-tokens", type=int, default=3000, dest="max_tokens")
    ap.add_argument("--audio", action="store_true",
                    help="force the audio route (for .webm and other "
                         "ambiguous containers)")
    ap.add_argument("--force", action="store_true",
                    help="send an oversized text file anyway")
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    a = ap.parse_args()

    p = Path(a.file)
    if not p.is_file():
        die(f"No such file: {p}")
    ext = p.suffix.lower()
    if a.audio or (ext in AUDIO_FMT and ext not in VIDEO_MIME):
        run_audio(p, a)
    elif ext in VIDEO_MIME:
        run_video(p, a)
    else:
        run_text(p, a)


if __name__ == "__main__":
    main()
