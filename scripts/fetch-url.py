#!/usr/bin/env python3
"""Fetch one web page as clean markdown, through Firecrawl.

Standard library only. Needs FIRECRAWL_API_KEY.

  python fetch-url.py URL [--out FILE] [--full] [--timeout MS]

This is the fallback for pages the host's own fetch tool cannot read: ones
behind Cloudflare, ones that block datacenter traffic, and ones that render
their content with JavaScript. Firecrawl requests from its own infrastructure,
so an IP block on this machine does not apply.

Try the built-in fetch tool first. It is free and it handles most pages.
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

API = "https://api.firecrawl.dev/v2/scrape"


def die(msg):
    print(msg, file=sys.stderr)
    raise SystemExit(1)


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url")
    ap.add_argument("--out", help="write the markdown here instead of stdout")
    ap.add_argument("--full", action="store_true",
                    help="keep nav, header and footer instead of main content only")
    ap.add_argument("--timeout", type=int, default=60000,
                    help="milliseconds, 1000 to 300000")
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    a = ap.parse_args()

    key = os.environ.get("FIRECRAWL_API_KEY")
    if not key:
        die("FIRECRAWL_API_KEY is not set. The free plan gives 1000 pages a "
            "month with no card: https://www.firecrawl.dev/app/api-keys\n"
            "Ask for it in a file, take the path, and store it yourself. Do not\n"
            "hand this command to the user:\n"
            "  python scripts/save-key.py FIRECRAWL_API_KEY --from-file PATH\n"
            "A key must never reach a command line or a chat message.")
    if not a.url.startswith(("http://", "https://")):
        die(f"Not a URL: {a.url}")
    if a.out and Path(a.out).exists():
        die(f"{a.out} already exists. Pick another name or delete it first.")

    req = urllib.request.Request(
        API,
        data=json.dumps({"url": a.url, "formats": ["markdown"],
                         "onlyMainContent": not a.full,
                         "timeout": a.timeout}).encode(),
        headers={"Authorization": f"Bearer {key}",
                 "Content-Type": "application/json"},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=a.timeout / 1000 + 30) as r:
            d = json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")[:1200]
        if e.code == 402:
            die("HTTP 402: out of Firecrawl credits for this billing period.")
        die(f"HTTP {e.code}: {body}")
    except urllib.error.URLError as e:
        die(f"Network error reaching Firecrawl: {e.reason}")

    data = d.get("data") or {}
    md = data.get("markdown")
    if not md:
        die("No markdown in the response. The page may have been empty or "
            "blocked at the source:\n" + json.dumps(d)[:1000])

    meta = data.get("metadata") or {}
    note = f"chars={len(md)} status={meta.get('statusCode')}"
    if meta.get("title"):
        note += f" title={meta['title'][:60]!r}"

    if a.out:
        Path(a.out).write_text(md, encoding="utf-8")
        print(a.out)
    else:
        print(md)
    print(f"[{note}]", file=sys.stderr)


if __name__ == "__main__":
    main()
