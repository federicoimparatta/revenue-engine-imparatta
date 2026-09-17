---
name: revenue-engine-imparatta
description: Federico's personal revenue engine - signal-driven leads and cold outreach selling imparatta.com (stalled products into production, AI to production, fractional product leadership). Use for "imparatta leads", "run the imparatta revenue engine", "sell my fractional services", or the nightly scheduled sweep.
argument-hint: "focus (vertical, region, keyword) - or 'scheduled' for the nightly run"
---

# Revenue Engine - imparatta.com

Signal-driven prospecting for Federico Imparatta's personal consulting practice. Each
run hunts companies showing real buying signals, scores them against the ICP, finds
and verifies decision-maker contacts, and drafts cold outreach ready to review and
send from federico@imparatta.com.

This is a configured personal derivative of the white-label `revenue-engine` skill.
Everything specific to the practice lives in the data directory
`~/.revenue-engine-imparatta/` (already seeded - there is no setup interview).

## Quick Start

- `/revenue-engine-imparatta` - sweep ALL target segments defined in the ICP
- `/revenue-engine-imparatta <focus>` - narrow to one vertical, region, or keyword
- `/revenue-engine-imparatta scheduled` - the nightly unattended run (see Scheduled
  mode below)

## Data Directory - `~/.revenue-engine-imparatta/`

| File | Purpose |
|---|---|
| `identity.md` | Sender identity, gog sending mailbox, language policy, CTA, signature, brand rules (lowercase style). |
| `services.md` | The three offers, proof points (public, may be named), credibility levers. |
| `icp.md` | Target verticals, geographies, stage, buyer titles, offer mapping. |
| `preferences.md` | Signal types, volume caps, dealbreakers, cross-engine dedupe, delivery channels. |
| `exclude.md` | NEVER pitch: clients, partners, past employers, competitors. |
| `lead-history.md` | Every lead ever surfaced, with status. The dedupe source. |
| `leads/<slug>-<date>/` | Per-lead research and outreach archive. |
| `outreach/` | Per-run outreach manifests. |
| `.secrets/hunter.env` | Hunter.io key. Gitignored, never committed. |
| `.secrets/typesafe.env` | TypeSafe (Jev) key. Optional - enables fast structured lead scoring (Step 3). Gitignored, never committed. |

## Deliverables (every run)

Write a user-facing bundle to `~/Downloads/revenue-engine-imparatta-<DATE>/`
(DATE = `YYYY-MM-DD`):

- `report.md` - all scored leads: High / Medium / Skipped. (`report.docx` too if
  python-docx is available: `python3 "<SKILL_DIR>/scripts/md_to_docx.py" in.md out.docx`
  - never block the run on the converter.)
- One outreach draft per High-fit lead, per `references/outreach-guide.md`.
- A Gmail draft per lead with a verified deliverable email, created with gog in
  federico@imparatta.com's drafts folder (never sent).
- A short run summary posted as a Slack DM to the channel id in `preferences.md`.

---

## Workflow

### Step 0: Load Context + Dedupe

1. Load ALL config files and `lead-history.md` from `~/.revenue-engine-imparatta/`.
   If `identity.md` or `icp.md` is missing, STOP and report it - this install ships
   pre-configured, so a missing file is breakage, not a setup request.
2. Extract the run focus from the arguments. `scheduled` (or no argument) sweeps all
   target verticals and geographies in `icp.md`; anything else narrows the run.
3. **Build the dedupe set** (never contact a company twice, from EITHER identity):
   - every company in `~/.revenue-engine-imparatta/lead-history.md`;
   - recent manifests in `~/.revenue-engine-imparatta/outreach/`;
   - recent drafts in the sending mailbox:
     `gog gmail drafts list -a federico@imparatta.com --max 100`;
   - **cross-engine**: every company in `~/.ataraxy-leads/lead-history.md` and every
     slug under `~/.ataraxy-leads/claims/`. Federico runs a second outreach identity
     (Ataraxy); a company must never hear from both. If the ataraxy files are absent
     on this machine, note it in the report and continue.
   Drop any company that appears anywhere above from the new results.

### Step 1: Hunt - fan out parallel research subagents

Dispatch research subagents in parallel, one per signal type enabled in
`preferences.md` (hiring, funding/expansion, pain, leadership-gap). Each subagent
uses web search/fetch, returns 6-10 verified companies, and is told to EXCLUDE
everything in `exclude.md` plus the dealbreakers in `preferences.md`. Each record
must carry: company, website domain, vertical + country, the signal + a real source
URL, the best-fit offer (from the mapping in `icp.md`), a decision-maker
(name/title/LinkedIn) if findable, and a one-line why-now.

Rules for every hunter: real source URL required - drop anything unverifiable;
respect the geography scope in `icp.md`; never return an agency, dev shop, or
staffing firm (that segment belongs to the ataraxy-leads engine).

### Step 2: Accounts to Contacts

For each fit company, identify 1-2 decision-makers (the buyer titles in `icp.md`).

**LinkedIn profile URLs must be real, never inferred.** Web-search
`"<name>" <company> LinkedIn` and confirm title + company on the result before
recording the URL. If search cannot confirm a real profile, record
`LinkedIn: not found - search "<name> <company>"` instead of a guessed URL. If only
a role is known, record the target title and the company LinkedIn people-search URL.

**Email resolution.** Resolve and verify with:

```bash
python3 "<SKILL_DIR>/scripts/hunter_lookup.py" enrich --domain <domain> --first <First> --last <Last>
```

Act on the result: `deliverable=yes` is emailable; `NOT_FOUND` or `deliverable=no`
means do NOT email (LinkedIn-only); `risky` (catch-all domain) means prefer LinkedIn
and email only as a flagged last resort. Never guess email patterns - guessed
addresses bounce and burn the imparatta.com domain.

### Step 3: Score and Exclude

Score each lead High/Medium/Low per `references/icp-scoring.md` (parallelize with
`scripts/evaluate-leads.md` for large batches). Apply `exclude.md` and the
dealbreakers BEFORE banding. When `TYPESAFE_API_KEY` is configured, the scoring
dimensions come from `scripts/typesafe_score.py` (TypeSafe's Jev model) instead of
being reasoned out freehand - see `scripts/evaluate-leads.md` for how the subagent
calls it and composes the band. No key: score by hand as before, same rubric. Then select the DRAFT SET: only High-fit leads, ONE
contact per company (the strongest), at most the cap in `preferences.md`. When more
High leads exist than the cap, draft the strongest and band the rest Medium with a
note. Nothing outside the draft set ever gets a Gmail draft - Medium leads and
second contacts go in the report only.

### Step 4: Save History

**Ordering: append history AFTER the Step 5 drafts are created**, then record each
row's real status (`Drafted` for created drafts, `New`/`Skipped` for the rest). A
lead recorded before it is pitched would be deduped out of every future sweep
without ever having been contacted; the opposite crash (drafts exist, history
missing) is recoverable because Federico reviews every draft by hand before
sending. The steps are numbered by what they produce, not their execution order.

Append ALL leads (including skips) to `~/.revenue-engine-imparatta/lead-history.md`:

```markdown
## [DATE] - Search: "[focus]"

| Company | Vertical · Country | Signal | Offer | Fit | Contact + LinkedIn | Status | Notes |
|---------|--------------------|--------|-------|-----|--------------------|--------|-------|
| ... | ... | ... | ... | ... | Name, Title - linkedin.com/in/... | New | ... |
```

**Always write the day heading, even on a run that surfaced zero leads** (add a
single line `No leads surfaced.` under it). The heading must contain `## [<DATE>]`
literally - square brackets included - because the scheduled runner greps for
exactly that: an absent heading means the run failed, never that the day was quiet.

Statuses: `New`, `Drafted`, `Contacted`, `Replied`, `Skipped`.

### Step 5: Write Deliverables (ALWAYS)

Create `~/Downloads/revenue-engine-imparatta-<DATE>/`. Write `report.md` (and
`report.docx` when the converter is available):

- Header: run focus, ICP filters applied, signals hunted, sources, caveats (risky
  emails, LinkedIn profiles marked "not found", ataraxy ledger unavailable, etc.).
- **HIGH FIT**: each lead with vertical + country, best-fit offer, why-now, signal +
  source URL, matching proof point, and a Contact block: LinkedIn URL, name + title,
  verified email + deliverability status, and the outreach language chosen.
- **MEDIUM FIT** table (worth-an-ask), with the LinkedIn column.
- **SKIPPED** table with the reason (excluded / duplicate / cross-engine / off-profile).

Then write the cold outreach per `references/outreach-guide.md` - the lowercase
style, language policy, structure, signature and channel rules all come from
`identity.md`. Collect all drafts into one manifest
`~/.revenue-engine-imparatta/outreach/<DATE>-batch.md` and archive per-lead copies
to `~/.revenue-engine-imparatta/leads/<slug>-<DATE>/`.

**Gmail drafts - gog only.** For every lead with a verified deliverable email, write
the body to a temp file and create the draft:

```bash
gog gmail drafts create -a federico@imparatta.com \
  --to "<email>" --subject "<subject>" --body-file "<tempfile>"
```

Plain text only, never `--body-html`, never send. LinkedIn-only leads get no draft -
they go in the report with a ready-to-paste DM for manual sending. Never automate
LinkedIn (no bots, no Selenium: ToS and account-ban risk). Do NOT use the Gmail MCP
tools: the connected MCP mailbox is a different account.

### Step 6: Present Results + Slack Summary

**Never publish these leads to Trello, or to any other shared workspace.** The
Ataraxy engine publishes its runs to a shared Trello board that other people read;
this engine does not, ever. The deliverables are the Downloads bundle, the ledger,
and Federico's DM - nothing else. The scheduled runner blocks the Trello and Gmail
MCP tools outright; on an interactive run, honor the same boundary yourself.


Show only NEW High/Medium leads (company, vertical, offer, signal, contact), point
to the Downloads bundle, and flag anything needing verification before send.

Then post the run summary as a **Slack DM to Federico** -
`mcp__claude_ai_Slack__slack_send_message` with the `channel_id` in
`preferences.md`. This is his personal pipeline: never post it to a shared channel,
whatever the ataraxy-leads engine does with its own runs. Contents: focus, net-new
company count, drafted leads grouped by offer, risky emails, LinkedIn-only leads,
and the bundle path. Use `HHhMM` for any times (Slack mobile renders `HH:MM` as an
emoji box).

**Prove the DM, do not assert it.** The 2026-09-08 run reported "Slack summary
delivered to your DM" when nothing had been posted. Take the `ts` from the
`slack_send_message` response and write it to `<RUN_DIR>/slack-receipt.txt` (the
runner passes `RUN_DIR`; on an interactive run write it into the Downloads bundle).
If the call errors or returns no `ts`, write `FAILED: <reason>` to that file instead
and say so in your final message. Never report a delivery you did not get a `ts`
back for.

### Step 7: Learn from Feedback

When Federico reacts ("not that vertical", "too big", "add X to exclude"), update
`preferences.md`, `icp.md`, or `exclude.md` immediately so the next run reflects it.
Confirm what changed in one line.

---

## Scheduled mode

The LaunchAgent `com.federico.imparatta-leads` runs
`scripts/run-imparatta-leads.sh` weekdays at 23:00 (America/Montevideo), which
invokes `/revenue-engine-imparatta scheduled <YYYY-MM-DD> <RUN_DIR>`. In this mode:

- The date after `scheduled` is the run date the runner stamped at launch. Use it as
  `<DATE>` for EVERY artifact (bundle folder, history heading, manifest name) even
  when the sweep finishes after midnight - the runner's assertions use that date.
- The path after the date is `RUN_DIR`. Write `slack-receipt.txt` there (Step 6);
  the runner reads it to tell a delivered DM from a claimed one.
- Never ask questions and never wait for input; make every call yourself.
- Never end the turn with work still in background tasks.
- Always produce the three artifacts the runner asserts on, in this order of
  importance: the day heading in `lead-history.md`, `report.md` in the Downloads
  bundle, the outreach manifest (write it even if empty, stating why).
- A dry night (zero leads after dedupe) is a valid outcome: write the heading, a
  short report saying so, an empty manifest, and the Slack summary.
- `risky` (catch-all) emails are NEVER drafted on a scheduled run - there is no user
  to opt in. They go in the report flagged risky, LinkedIn DM only.

## Response Format (interactive runs)

1. **Top Leads** - new High/Medium: company, vertical + country, offer, signal, contact.
2. **Saved to Downloads** - `~/Downloads/revenue-engine-imparatta-<DATE>/`.
3. **Next Steps** - what to verify before sending; offer to draft more or adjust the ICP.
