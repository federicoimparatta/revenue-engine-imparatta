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

1. Dedupe normalized registrable website/email domains across both engines, saved
   manifests and mailbox drafts. Hard-skip clients by name and both domains.
2. Hunt structured leadership postings on Greenhouse, Ashby, Lever, Wellfound and
   fractionals.work, still open and first posted >=30 days ago; or seed/Series A
   raises from the last 60 days explicitly funding a product or AI build-out.
   Shipping stalls and leadership departures are retired signals.
3. Confirm current titles and require Hunter finder_score >=80 plus deliverable=yes.
   Re-check job liveness immediately before drafting.
4. Score dimensions via optional TypeSafe/Jev or by hand, then apply the fail-closed High gate. Cap at 3 drafts a night and 8 per Monday-Sunday
   week, including previous same-night attempts. Ceilings, never quotas.
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
# copy the live clients-exclude.json from the configured machine (never commit it)
# (copy from the machine that has them - they are not in this repo)
# put the Hunter.io key in ~/.revenue-engine-imparatta/.secrets/hunter.env
# put the TypeSafe key in ~/.revenue-engine-imparatta/.secrets/typesafe.env
#   (optional - format: TYPESAFE_API_KEY=<key>, no quotes, no "export")
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

**Model is pinned to Sonnet** (`MODEL` at the top of the runner), never inherited -
as is every other scheduled job on this machine. Interactive work runs on Fable, so
a nightly job on the default model competes for the same quota and dies as "broken
research". For a heavier night on Opus, run the script directly with
`IMPARATTA_LEADS_MODEL=opus` (launchctl does not pass env through).

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
| `scripts/typesafe_score.py` | TypeSafe (Jev) lead-fit scoring - optional, see `references/icp-scoring.md`. |
| `scripts/check-setup.sh` | Install sanity check. |
| `scripts/high_gate.py` | Deterministic pass/fail High gate. |
| `scripts/validate_job_posting.py` | Live structured posting and first-posted age check. |
| `scripts/domain_util.py` | Registrable-domain dedupe and client exclusion. |
| `scripts/public_suffix_list.dat` | Bundled Mozilla Public Suffix List; offline domain normalization. |
| `scripts/test_quality_gates.py` | Offline smoke/regression checks; no sends or drafts. |
| `launchd/` | The LaunchAgent plist. |
| `~/.revenue-engine-imparatta/` | Data: config, ledger, per-lead archives, secrets. Never in this repo. |

## Validate changes

```bash
bash scripts/check-setup.sh
python3 scripts/test_quality_gates.py
python3 scripts/domain_util.py normalize https://www.nike.com/careers
python3 scripts/domain_util.py check-exclude --company Nike --domain nike.com \
  --exclude-file ~/.revenue-engine-imparatta/clients-exclude.json
# EXCLUDE exits 1 intentionally.
```

A scheduled sweep remains drafts-only via gog to federico@imparatta.com, never
send/reply. Check its report/manifest for 0-3 drafts, HIGH evidence, confirmed title,
finder score >=80, live age-verified role (for hires), source: launch agent and
strategy/signal. Do not commit the live data directory or secrets.

The domain helper uses the bundled [Public Suffix List](https://publicsuffix.org/list/)
(including private suffixes) to normalize subdomains and country-code domains
without runtime network access. The list retains its Mozilla Public License notice.
