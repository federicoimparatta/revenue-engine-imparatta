# revenue-engine-imparatta

Federico Imparatta's personal revenue engine: a nightly, signal-driven prospecting
run that sells [imparatta.com](https://imparatta.com) - stalled products into
production, AI demo to production, and fractional product & delivery leadership.

A configured personal derivative of the white-label `revenue-engine` skill
(ataraxy-digital/revenue-engine). The white-label version keeps all business config
in a data directory seeded by a setup interview; this version ships the strategy
baked in for one practice and swaps Gmail MCP drafting for the gog CLI so it can run
headless from launchd.

## What a run does

1. Dedupe against its own ledger AND the ataraxy-leads ledger (two outreach
   identities, one inbox rule: a company never hears from both).
2. Hunt four signal seams in parallel: stuck senior product-leadership hires,
   fresh raises with product/AI build-out promises, public shipping stalls, and
   leadership departures with no successor.
3. Verify contacts (real LinkedIn profiles only, Hunter.io-verified emails only).
4. Score against the ICP, cap at 6 drafts a night to protect the sending domain.
5. Draft lowercase, plain-text cold emails into federico@imparatta.com via
   `gog gmail drafts create` - drafts only, every send is manual.
6. Write the report bundle to `~/Downloads/revenue-engine-imparatta-<date>/`,
   append the ledger, post a Slack summary.

## Install (new machine)

```bash
git clone git@github.com:federicoimparatta/revenue-engine-imparatta.git \
  ~/.claude/skills/revenue-engine-imparatta
mkdir -p ~/.revenue-engine-imparatta/.secrets
# seed identity.md services.md icp.md preferences.md exclude.md lead-history.md
# (copy from the machine that has them - they are not in this repo)
# put the Hunter.io key in ~/.revenue-engine-imparatta/.secrets/hunter.env
gog auth add   # federico@imparatta.com, gmail scope
cp launchd/com.federico.imparatta-leads.plist ~/Library/LaunchAgents/
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.federico.imparatta-leads.plist
bash scripts/check-setup.sh
```

Requires: `claude` CLI, `gog` (with the federico@imparatta.com account authorized),
Homebrew bash 5 at `/opt/homebrew/bin/bash`, coreutils (`gtimeout`), and
`~/.local/bin/launchagent-alert-wrap.sh` (failure paging; lives outside this repo).

## Schedule

Weekdays 23:00 America/Montevideo via `launchd/com.federico.imparatta-leads.plist`
-> `launchagent-alert-wrap.sh` (caffeinate + failure paging) ->
`scripts/run-imparatta-leads.sh` -> `claude -p "/revenue-engine-imparatta scheduled
<date>"`. The runner asserts on artifacts (report, ledger heading, outreach
manifest), never on claude's exit code.

**Model is pinned to Opus** (`MODEL` at the top of the runner), never inherited.
Interactive work runs on Fable, so a nightly job on the default model competes for
the same quota and dies as "broken research". Opus is a separate pool, fresh at
23:00, and the tier the scoring and outreach writing deserve. For a cheaper night,
run the script directly with `IMPARATTA_LEADS_MODEL=claude-sonnet-5` (launchctl
does not pass env through).

Kick a run manually:

```bash
launchctl kickstart gui/$(id -u)/com.federico.imparatta-leads
```

Or run interactively inside Claude Code: `/revenue-engine-imparatta`.

## Layout

| Path | What |
|---|---|
| `SKILL.md` | The workflow the agent follows. |
| `references/` | Scoring rubric and outreach framework. |
| `scripts/run-imparatta-leads.sh` | The launchd runner (lock, deadline, artifact assertions). |
| `scripts/hunter_lookup.py` | Hunter.io email find + verify. |
| `scripts/check-setup.sh` | Install sanity check. |
| `launchd/` | The LaunchAgent plist. |
| `~/.revenue-engine-imparatta/` | Data: config, ledger, per-lead archives, secrets. Never in this repo. |
