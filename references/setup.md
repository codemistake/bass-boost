# Setting up keys

Read this when a route reports a missing key, or when someone asks how to
install the skill. Walk the person through it; do not improvise a different
place to put a secret.

## Which key unlocks what

| Variable | Unlocks | Where to get one |
|---|---|---|
| `OPENROUTER_API_KEY` | research, opinion, video, audio, and economy on local files | <https://openrouter.ai/keys> |
| `FAL_AI_TOKEN` | image | <https://fal.ai/dashboard/keys> |
| `FIRECRAWL_API_KEY` | fetch-url, the fallback for pages the host cannot read | <https://www.firecrawl.dev/app/api-keys> |

None of them is required to install the skill. Each one turns on its own routes
and nothing else. A route whose key is absent reports that it is unavailable;
it never guesses at what it would have returned.

The OpenRouter MCP server is an alternative to `OPENROUTER_API_KEY` for research
and opinion only. It cannot carry a local file, so the key is still needed for
video, audio from disk, and economy. Both can be set up; the scripts use the key
and the tools use the MCP session.

## Where the key goes

`~/.claude/settings.json`, in the `env` block:

```json
{
  "env": {
    "FAL_AI_TOKEN": "..."
  }
}
```

That file is per user and applies to every project. Claude Code reloads settings
on save, so a new session picks the value up with no restart.

Use the bundled script rather than editing by hand. It merges into the existing
file instead of replacing it, backs the old one up, refuses to write over a file
it cannot parse, and never prints the value:

```bash
python scripts/save-key.py FAL_AI_TOKEN --from-file ~/key.txt
python scripts/save-key.py FAL_AI_TOKEN --stdin      # paste, then Ctrl-D
```

Then delete the file the key was pasted from.

## Where the key must never go

- **`.claude/settings.json` inside a project.** That file exists to be committed
  so teammates get the same settings. A key there is a key in the git history.
- **Anywhere in the repository**, including `.env` files, fixtures, and test
  data. A `.gitignore` entry is a promise, not a guarantee.
- **A command line.** `save-key.py KEY --value sk-...` would put the secret in
  shell history and in the transcript of whichever agent ran it, which is why
  the script has no such flag.
- **A cloud-synced folder**, such as Desktop under OneDrive, Dropbox, or iCloud
  Drive. Fine as a moment's transfer, but delete it afterwards.
- **The conversation.** Never ask to be shown a key, never echo one back, and
  never repeat one in a summary. Read it from the file inside the command that
  needs it.

## What the agent should do when a key is missing

1. Say which route is unavailable and which variable would enable it.
2. Give the sign-up link from the table above, and say what it costs. Firecrawl
   has a free tier of 1000 pages a month with no card; OpenRouter and fal are
   pay as you go.
3. Offer to run `save-key.py` once the person has the key in a file.
4. Do the rest of the task without that route, and say what was left out.

Do not stop the whole task over one missing key, and do not substitute a guess
for the route's output.

## Checking what is set

```bash
python -c "import os;[print(k, 'set' if os.environ.get(k) else 'MISSING') for k in ('OPENROUTER_API_KEY','FAL_AI_TOKEN','FIRECRAWL_API_KEY')]"
```

This prints presence only, never a value.
