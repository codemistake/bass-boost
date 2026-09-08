#!/usr/bin/env python3
"""Send a local audio or video file to OpenRouter and print the result.

Standard library only. Needs OPENROUTER_API_KEY in the environment.

  python or-media.py audio  FILE [--lang ru] [--model SLUG]
  python or-media.py video  FILE [--prompt TEXT] [--model SLUG]

Audio goes to /audio/transcriptions, video goes to /chat/completions as a
base64 data URL. Both bill the OpenRouter account that owns the key.
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
AUDIO_MODEL = "nvidia/parakeet-tdt-0.6b-v3"
VIDEO_MODEL = "~google/gemini-flash-latest"

# Formats the transcription endpoint accepts. Provider support varies.
AUDIO_FMT = {".wav": "wav", ".mp3": "mp3", ".flac": "flac", ".m4a": "m4a",
             ".ogg": "ogg", ".webm": "webm", ".aac": "aac"}
VIDEO_MIME = {".mp4": "video/mp4", ".webm": "video/webm",
              ".mov": "video/quicktime", ".mkv": "video/x-matroska"}
VIDEO_SOFT_LIMIT = 20 * 1024 * 1024

DEFAULT_VIDEO_PROMPT = (
    "Describe what happens in this recording, step by step. Note the moments "
    "where something goes wrong, with timestamps, and quote any on-screen text "
    "or error messages exactly."
)


def die(msg):
    print(msg, file=sys.stderr)
    raise SystemExit(1)


def post(path, body):
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        die("OPENROUTER_API_KEY is not set. Create a key at "
            "https://openrouter.ai/keys and export it.")
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
        # OpenRouter puts the useful part in the body, not the status line.
        die(f"HTTP {e.code}: {e.read().decode(errors='replace')[:2000]}")
    except urllib.error.URLError as e:
        die(f"Network error: {e.reason}")


def b64(path):
    return base64.b64encode(path.read_bytes()).decode()


def report_usage(d):
    u = d.get("usage") or {}
    bits = [f"{k}={u[k]}" for k in ("prompt_tokens", "completion_tokens", "cost")
            if k in u]
    if d.get("id"):
        bits.append(f"id={d['id']}")
    if bits:
        print("[" + " ".join(bits) + "]", file=sys.stderr)


def cmd_audio(a):
    p = Path(a.file)
    if not p.is_file():
        die(f"No such file: {p}")
    fmt = AUDIO_FMT.get(p.suffix.lower())
    if not fmt:
        die(f"Unsupported audio format {p.suffix}. Convert to one of: "
            + ", ".join(sorted(AUDIO_FMT.values())))
    body = {"model": a.model, "input_audio": {"data": b64(p), "format": fmt}}
    if a.lang:
        body["language"] = a.lang
    d = post("/audio/transcriptions", body)
    text = d.get("text")
    if text is None:
        die("No transcript in response: " + json.dumps(d)[:2000])
    print(text)
    report_usage(d)


def cmd_video(a):
    p = Path(a.file)
    if not p.is_file():
        die(f"No such file: {p}")
    size = p.stat().st_size
    if size > VIDEO_SOFT_LIMIT:
        die(f"{p.name} is {size / 1e6:.1f} MB. Base64 inflates it by a third and "
            f"the request will likely be rejected above ~{VIDEO_SOFT_LIMIT / 1e6:.0f} MB. "
            "Shrink or trim it first, for example:\n"
            f"  ffmpeg -i {p.name} -vf scale=-2:720 -r 10 -an -crf 32 out.mp4")
    mime = VIDEO_MIME.get(p.suffix.lower(), "video/mp4")
    body = {
        "model": a.model,
        "reasoning": {"effort": "low"},
        "max_tokens": a.max_tokens,
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": a.prompt},
            {"type": "video_url",
             "video_url": {"url": f"data:{mime};base64,{b64(p)}"}},
        ]}],
    }
    d = post("/chat/completions", body)
    try:
        print(d["choices"][0]["message"]["content"])
    except (KeyError, IndexError):
        die("Unexpected response: " + json.dumps(d)[:2000])
    report_usage(d)


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("audio", help="transcribe a local audio file")
    s.add_argument("file")
    s.add_argument("--lang", help='ISO-639-1 hint, e.g. "ru". Auto-detected if omitted.')
    s.add_argument("--model", default=AUDIO_MODEL)
    s.set_defaults(fn=cmd_audio)

    s = sub.add_parser("video", help="analyze a local video file")
    s.add_argument("file")
    s.add_argument("--prompt", default=DEFAULT_VIDEO_PROMPT)
    s.add_argument("--model", default=VIDEO_MODEL)
    s.add_argument("--max-tokens", type=int, default=4000, dest="max_tokens")
    s.set_defaults(fn=cmd_video)

    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
