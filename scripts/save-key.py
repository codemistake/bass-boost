#!/usr/bin/env python3
"""Store an API key in the user's Claude Code settings, without it appearing
anywhere it can be read back later.

Standard library only.

  python save-key.py FIRECRAWL_API_KEY --from-file /path/to/key.txt
  python save-key.py OPENROUTER_API_KEY --stdin      # then paste, then Ctrl-D

The value is read from a file or from stdin, never from the command line,
because a command line lands in shell history and in the transcript of whatever
agent ran it. Nothing here prints the value back.

It writes only to ~/.claude/settings.json, the per-user file. It will not touch
a project's .claude/settings.json, which is meant to be committed and is the
usual way a key ends up in a git repository.
"""
import argparse
import json
import re
import shutil
import sys
from pathlib import Path

SETTINGS = Path.home() / ".claude" / "settings.json"
NAME_RE = re.compile(r"^[A-Z][A-Z0-9_]{2,63}$")


def die(msg):
    print(msg, file=sys.stderr)
    raise SystemExit(1)


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("name", help="environment variable name, e.g. FAL_AI_TOKEN")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--from-file", help="file holding the key and nothing else")
    src.add_argument("--stdin", action="store_true", help="read the key from stdin")
    ap.add_argument("--force", action="store_true",
                    help="overwrite a value that is already stored")
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    a = ap.parse_args()

    if not NAME_RE.match(a.name):
        die(f"{a.name!r} is not a plausible environment variable name. "
            "Use upper case letters, digits and underscores.")

    if a.stdin:
        value = sys.stdin.read().strip()
    else:
        p = Path(a.from_file)
        if not p.is_file():
            die(f"No such file: {p}")
        value = p.read_text(encoding="utf-8-sig").strip()

    if len(value.splitlines()) > 1:
        die("The source holds more than one line. Give a file containing only "
            "the key, or pipe only the key.")
    if len(value) < 8:
        die(f"That value is {len(value)} characters, too short to be a key. "
            "Nothing was written.")

    SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    if SETTINGS.exists():
        try:
            data = json.loads(SETTINGS.read_text(encoding="utf-8-sig") or "{}")
        except json.JSONDecodeError as e:
            die(f"{SETTINGS} is not valid JSON ({e}). Fix it by hand first; "
                "this script will not overwrite a file it cannot parse.")
        if not isinstance(data, dict):
            die(f"{SETTINGS} does not hold a JSON object. Nothing was written.")
        backup = SETTINGS.with_suffix(".json.bak")
        shutil.copy2(SETTINGS, backup)
    else:
        data, backup = {}, None

    env = data.setdefault("env", {})
    if not isinstance(env, dict):
        die('The "env" key in settings is not an object. Nothing was written.')
    if a.name in env and not a.force:
        die(f"{a.name} is already stored in {SETTINGS}. Re-run with --force to "
            "replace it.")

    env[a.name] = value
    SETTINGS.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")

    print(f"{a.name} stored in {SETTINGS} ({len(value)} characters, "
          f"starts {value[:4]}...)")
    if backup:
        print(f"previous settings backed up to {backup}")
    print("Claude Code reloads settings on save, so a new session picks it up. "
          "Delete the file you pasted the key from.")


if __name__ == "__main__":
    main()
