# agentfield-trigger-demo

Live demo repository for [AgentField](https://github.com/Agent-Field/agentfield)'s
inbound trigger system. The webhook on this repo is wired to a local
AgentField control plane via a Cloudflare tunnel; when issues, pull
requests, or pushes happen here, an AgentField agent receives the event
and runs a reasoner against it.

## What runs

Three reasoners on the local agent listen for events from this repo:

| Event | Reasoner | What it does |
|---|---|---|
| `issues` (opened, edited, reopened) | `summarize_issue` | Calls Claude Haiku via OpenRouter, writes a 2-3 sentence summary to per-agent memory |
| `pull_request` | `handle_pr` | Captures action, number, title, repo into a deterministic memory record |
| `push` | (logged at trigger layer) | Confirms signature verification end-to-end |

The webhook delivery is signed with `X-Hub-Signature-256` (HMAC SHA-256
over the raw body). The control plane verifies the signature using a
secret stored as an env var on the host; the secret value never enters
the agent process or this repo.

## Architecture

```
GitHub.com (this repo)
  │
  │ POST /sources/<trigger-id>      (JSON body, signed)
  │ X-Hub-Signature-256: sha256=…
  │
  ▼
Cloudflare quick tunnel
  │
  ▼
AgentField control plane (localhost:8080)
  │  verifies signature, stamps trigger event VC,
  │  dispatches to the matching agent reasoner
  │
  ▼
Agent (triggers-demo-agent)
  │  summarize_issue / handle_pr / handle_push
  │  writes structured records to per-agent memory
  ▼
Operator UI (/triggers, /integrations)
```

## How to use

This repo is intentionally lightweight — the value is the AgentField
demo behind it, not the repo content. To exercise the pipeline:

- **Open an issue** with a real bug body — the agent will summarize it via Claude Haiku.
- **Open a pull request** — the agent records the PR action.
- **Push a commit** — the trigger event is captured with valid signature.

Inspect what landed inside the AgentField UI at `localhost:8080/ui/triggers`
on the demo machine.

## Repository discoverability

This is a demo target, not production code. The actual agent code,
control plane, and SDKs are at:
[Agent-Field/agentfield](https://github.com/Agent-Field/agentfield).
