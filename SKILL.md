---
name: bass-boost
description: "Use when the main model should hand work to a different model through OpenRouter: a page or search the built-in web tools cannot read, a video or screen recording that needs analyzing, an audio file or voice note that needs transcribing, an independent second opinion on a non-code decision, or when the user says their subscription limits are running low and wants heavy reading moved off the main model. Also use when the user asks which outside model to pick for a task or what a call would cost."
license: MIT
compatibility: "Requires an OpenRouter account with credit, and either the OpenRouter MCP server or OPENROUTER_API_KEY in the environment. Economy mode assumes a subscription-metered host such as Claude Code."
metadata:
  version: "1.0.0"
  author: codemistake
  repository: https://github.com/codemistake/bass-boost
---

# Bass Boost

The main model is the tweeter. It is precise, expensive, and it makes the
decisions. The models behind OpenRouter are the subwoofer: cheap watts for the
heavy low end, which is bulk reading, media, and long-horizon research. This
skill moves the low end off the tweeter.

**The main model decides and writes. Every time.** Nothing that comes back from
OpenRouter edits a file, runs a command, or gets believed without a check. A
returned claim is a lead to verify, not a result.

**Every call spends the user's own money.** Always set `max_tokens`. Prefer the
cheapest model that can do the job. Say what a step will cost before an
expensive one.

## Setup

Preferred, no key handling:

```bash
claude mcp add --transport http openrouter https://mcp.openrouter.ai/mcp
claude mcp login openrouter
```

That gives the tools `send-message`, `transcribe-audio`, `list-models`,
`get-model`, and `get-generation`.

Local files need a key instead, because base64 through a tool call burns the
main model's context. Ask the user to create one at
<https://openrouter.ai/keys> and export `OPENROUTER_API_KEY`. Never ask for the
key itself and never write it into a file.

## Modes

| Mode | Reach for it when | How |
|---|---|---|
| research | built-in fetch is blocked, or the answer needs several pages | `send-message`, a `:online` model |
| video | a screen recording or clip has to be understood | `scripts/or-media.py video` |
| audio | speech has to become text | `transcribe-audio`, or `scripts/or-media.py audio` |
| opinion | a non-code decision needs a dissenting reader | `send-message`, a model from another lab |
| economy | the user's subscription limits are running out | see below |

Model slugs move. Before pinning one in a new workflow, confirm it with
`get-model`, or find a current one with `list-models` (it sorts by price,
context, coding index, and modality). The `~vendor/family-latest` aliases, such
as `~google/gemini-flash-latest`, always resolve to the newest model in that
family and are the safer default.

### research

`send-message` with a `:online` model, `reasoning_effort: low`,
`max_tokens: 4000`. The `:online` suffix adds web search to any model that
supports it.

Ask for facts with source links, dates, and version numbers, and say no prose.
Then re-read the important links with the local fetch tool. A grounded model
still paraphrases, and the paraphrase is what gets a fact wrong.

### video

```bash
python scripts/or-media.py video FILE --prompt "what to look for"
```

Name the target in the prompt: the moment of failure, the exact on-screen text,
the order the user clicked things. Files above about 20 MB are rejected, and the
script prints the `ffmpeg` command that shrinks one.

### audio

A file already on public HTTPS goes through `transcribe-audio` with an
`audio_url`. A local file goes through the script:

```bash
python scripts/or-media.py audio FILE --lang ru
```

`nvidia/parakeet-tdt-0.6b-v3` is a cheap multilingual default. Never pass
`audio_base64` to the MCP tool; the encoded audio would pass through the main
model's context.

The transcript is raw text with no structure. Reading the task out of it is the
main model's job.

### opinion

`send-message` with a frontier model from a **different lab** than the main
model, `max_tokens: 3000`. The value is a different training run with different
blind spots, not a higher benchmark score, so picking the cheapest capable
outsider beats picking the most expensive one.

Send a brief, not a repository: context in five to fifteen lines, the options,
and the question. Ask it to argue against the plan and to name what would have
to be true for the plan to fail.

Use it for architecture, product, and wording calls. For code review, the host's
own review tooling sees the actual diff and does better.

### economy

Turn on when the user says they are low on limits, or asks for economy mode.
Confirm in one line, then hold it until they say stop or the session ends.

While it is on:

- Files over roughly 300 lines, logs, and long diffs are not read directly.
  Send them to a cheap flash-tier model with a specific question,
  `reasoning_effort: low`, `max_tokens: 3000`, and keep the summary.
- Long first drafts, such as a README or a report, are drafted outside and
  edited by the main model.
- Subagents stay off. They bill the same subscription that is running out.
- The main model keeps edits, commands, short reads, decisions, and the final
  check.

What does not change in economy mode: verify before acting, ask before anything
destructive, and never let an outside model write to the repository.

## Cost and privacy

Whatever gets sent leaves the machine. Source code, logs, and recordings all
reach a third-party inference provider that the router picks. Before sending
anything from a private repository, say so and get agreement. For a file the
user has called sensitive, do not send it at all.

Spending is metered per call against the user's balance. After a large or
unfamiliar call, `get-generation` with the returned id reports what it actually
cost.

## Common mistakes

| Mistake | What to do instead |
|---|---|
| Delegating a task the main model would finish faster | Delegate for reach, context relief, or an outside view. Nothing else. |
| Pasting a whole file into an opinion call | Send a brief. Frontier models are billed per token in both directions. |
| Treating a grounded answer as verified | Follow the links. Grounding narrows hallucination, it does not remove it. |
| Pinning a model slug found in a blog post | Confirm it with `get-model` first. Slugs are retired without notice. |
| Sending base64 media through a tool call | Use the script. The tool result would land in the main model's context. |
| Leaving `max_tokens` unset on a reasoning model | A stuck reasoning loop bills to the user until it stops. |
