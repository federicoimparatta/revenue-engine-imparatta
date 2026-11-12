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
| `clients-exclude.json` | Machine-readable hard exclusions by name and website/email domain; never warm paths. |
| `lead-history.md` | Every lead ever surfaced, with status. The dedupe source. |
| `leads/<slug>-<date>/` | Per-lead research and outreach archive. |
| `outreach/` | Per-run outreach manifests. |
| `.secrets/hunter.env` | Hunter.io key. Gitignored, never committed. |

## Deliverables (every run)

Write a user-facing bundle to `~/Downloads/revenue-engine-imparatta-<DATE>/`
(DATE = `YYYY-MM-DD`):

- `report.md` - all scored leads: High / Medium / Skipped. (`report.docx` too if
  python-docx is available: `python3 "<SKILL_DIR>/scripts/md_to_docx.py" in.md out.docx`
  - never block the run on the converter.)
- One outreach draft per High-fit lead, per `references/outreach-guide.md`.
- A Gmail draft per draft-set lead (Step 3) with a verified deliverable email,
  created with gog in federico@imparatta.com's drafts folder (never sent).
- A short run summary posted as a Slack DM to the channel id in `preferences.md`.

---

## Workflow

### Step 0: Load Context + Dedupe

1. Load ALL config files and `lead-history.md` from `~/.revenue-engine-imparatta/`.
   If `identity.md` or `icp.md` is missing, STOP and report it - this install ships
   pre-configured, so a missing file is breakage, not a setup request.
2. Extract the run focus from the arguments. `scheduled` (or no argument) sweeps all
   target verticals and geographies in `icp.md`; anything else narrows the run.
3. **Build the dedupe set by registrable website domain**, with email domains as
   a backstop. Collect website/email domains from this engine's `lead-history.md`,
   ALL prior outreach manifests, and recent mailbox drafts:
   `gog gmail drafts list -a federico@imparatta.com --max 100` (paginate if needed;
   fetch draft details when recipients are not in the list output).
   Also read `~/.ataraxy-leads/lead-history.md` and `~/.ataraxy-leads/claims/`.
   Resolve claim slugs and old name-only history rows through their saved research
   or manifests; a slug is not a domain. If a legacy company cannot be resolved,
   retain its name as an additional block, never fabricate a domain. Note missing
   Ataraxy files in the report.

   Normalize every URL, host and email with:
   `python3 "<SKILL_DIR>/scripts/domain_util.py" normalize "<value>"`.
   Save normalized domains one per line in the run's `seen-domains.txt` and check
   each candidate with `domain_util.py in-set --domain <domain> --set-file <file>`.
   Drop a lead if EITHER its website domain or contact email domain is seen.
   Unknown website domain means no draft. Company-name matching is a backstop,
   never the primary key. Reserve selected domains separately by lead record so
   one run cannot select two aliases/contacts at the same company. A lead may
   retain its own reservation during the final check. Add its domains to the
   seen set immediately after successful draft creation.
4. **Hard client exclusion before research or scoring**. Require a readable,
   nonempty `clients-exclude.json` (missing/invalid means STOP drafting). Run:

   ```bash
   python3 "<SKILL_DIR>/scripts/domain_util.py" check-exclude \
     --company "<name>" --domain "<website domain>" --email "<email or empty>" \
     --exclude-file ~/.revenue-engine-imparatta/clients-exclude.json
   ```

   `EXCLUDE` means hard skip: no draft, no prospect or warm-path recommendation,
   no evaluator/High-gate call. Honor `exclude.md` and all dealbreakers too.
   An error is not clearance; stop drafting until the check succeeds. Re-check
   after discovering the email, because either domain can independently exclude.

### Step 1: Hunt - structured sources only

Use only these two buying-intent lanes; no open-ended four-signal web-search hunt.
Search may locate structured pages, but snippets are never evidence. Do not hunt
shipping stalls, changelog gaps, coming-soon pages, social silence or leadership
departures. No result-count target: zero qualifying leads is a valid outcome.

1. **Stuck leadership hires**: CPO / Chief Product Officer, Head of Product,
   Head of Delivery, Head of AI or Head of Data (including combined titles).
   Use Greenhouse, Ashby, Lever, Wellfound and the fractional boards explicitly
   enabled in `preferences.md` (currently fractionals.work). The role must still
   be open and its **first-posted date** must be at least 30 days ago; a last-updated
   date or repost alone does not prove age. Prefer the board's posting/API URL:
   `boards.greenhouse.io`, `job-boards.greenhouse.io`, `boards-api.greenhouse.io`,
   `jobs.ashbyhq.com`, `api.ashbyhq.com/posting-api`, `jobs.lever.co`,
   `api.lever.co/v0/postings`, `wellfound.com`, `fractionals.work`.
   Fetch the specific posting today and run:

   ```bash
   python3 "<SKILL_DIR>/scripts/validate_job_posting.py" --url "<job URL>"
   ```

   Only `OPEN` plus integer `age_days >= 30` qualifies. `CLOSED` is dropped;
   `UNKNOWN` or unknown age is report-only, never guessed. The validator accepts
   structured individual-job evidence, not generic pages or search snippets.
   For Greenhouse pages without structured job data, use the individual public
   API URL `https://boards-api.greenhouse.io/v1/boards/<board>/jobs/<job_id>`
   (not the full-board list). Do not substitute `updated_at` for `first_published`.
   Save the source response and validator output. Re-check immediately before
   drafting; a newly closed or unverified role is dropped from the draft set.
2. **Fresh raises**: dated seed / seed extension / pre-A or Series A announcements
   from the **last 60 days**, explicitly funding a product or AI build-out.
   Use company announcements, official press releases, TechCrunch funding desks
   or Crunchbase News; verify the visible announcement date and build-out text
   on the source page. No date, future date, outside 60 days, Series B+ raise,
   or generic expansion without product/AI intent means no qualifying signal.

Each record must carry company, normalized website domain, vertical + country,
remote/geography evidence, stage + source, signal type (`stuck leadership hire`
or `fresh raise`), real source URL, first-posted/announcement date, job title +
liveness/age (for hires), best-fit offer, current decision-maker name/title/source
if findable, and a one-line why-now. Apply exclusions and dedupe before enrichment.
Never return agencies, dev shops or staffing firms. Do not launch research subagents
unless the user explicitly requests delegation for that run.

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

A Gmail draft is allowed only with `deliverable=yes`, a **numeric
`finder_score >= 80`**, and a primary source or current LinkedIn profile confirming
that this person **currently holds that title at this company**. Record `title`,
`title_source_url` and `title_checked_at` in the lead and manifest. If the person
has left or the title cannot be confirmed, no email. A search snippet or Hunter's
stored title alone is insufficient current-title evidence.

`NOT_FOUND`, missing/non-numeric/under-80 scores, `deliverable=no/unknown`, and
`risky` catch-all emails get no Gmail draft (LinkedIn-only at most, with a confirmed
current profile). Never guess email patterns. `hunter_lookup.py` reports the score
floor and email eligibility; it does not confirm titles or qualify the account.

After resolving an email, repeat both domain dedupe and client exclusion on its
domain. For stuck-hire leads, repeat `validate_job_posting.py` immediately before
Step 5; only still-OPEN, age-verified postings remain eligible.

### Step 3: Score and Exclude

Apply `clients-exclude.json`, `exclude.md`, domain dedupe and dealbreakers BEFORE
banding. For every survivor, use `references/icp-scoring.md` and
`scripts/evaluate-leads.md`: save a gate JSON record with evidence for each field,
then run `python3 "<SKILL_DIR>/scripts/high_gate.py" --record <gate.json>`.
Only the script's literal `HIGH` verdict can enter the DRAFT SET, with Step 2's
contact checks also passed. A failed/error gate is never High.

ONE contact per normalized website domain, **max 3 Gmail drafts per night and 8
per Monday-Sunday week** (America/Montevideo). Count already-created drafts in
manifests/mailbox for the same night/week, including earlier attempts; if totals
cannot be reconciled, create no additional drafts. Caps are ceilings, not quotas.
When more qualify, choose the strongest and report the rest as High, deferred by
cap. If fewer qualify, draft fewer. Medium/Low leads never receive Gmail drafts.
Shipping stalls and leadership departures cannot qualify, regardless of fit.

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

| Company | Domain | Vertical · Country | Signal | Source | Offer | Fit | Contact + LinkedIn | Status | Notes |
|---------|--------|--------------------|--------|--------|-------|-----|--------------------|--------|-------|
| ... | acme.com | ... | stuck leadership hire | launch agent | ... | High | Name, confirmed Title - linkedin.com/in/... | Drafted | hunter_score=91; job_age_days=47 |
```

**Always write the day heading, even on a run that surfaced zero leads** (add a
single line `No leads surfaced.` under it). The heading must contain `## [<DATE>]`
literally - square brackets included - because the scheduled runner greps for
exactly that: an absent heading means the run failed, never that the day was quiet.

Source is `launch agent` on every new row, and Signal uses the exact allowed signal
type. Domain is the normalized registrable website domain; preserve existing history.

Statuses: `New`, `Drafted`, `Contacted`, `Replied`, `Skipped`.

### Step 5: Write Deliverables (ALWAYS)

Create `~/Downloads/revenue-engine-imparatta-<DATE>/`. Write `report.md` (and
`report.docx` when the converter is available):

- Header: run focus, ICP filters applied, signals hunted, sources, caveats (risky
  emails, LinkedIn profiles marked "not found", ataraxy ledger unavailable, etc.).
- **HIGH FIT**: each lead with vertical + country, best-fit offer, why-now, signal +
  source URL, matching proof point, and a Contact block: LinkedIn URL, name + confirmed current title/source,
  finder score, verified email + deliverability status, and the outreach language.
  Include the source date, posting check and saved High-gate verdict/record.
- **MEDIUM FIT** table (worth-an-ask), with the LinkedIn column.
- **SKIPPED** table with the reason (excluded / duplicate / cross-engine / off-profile).

Then write the cold outreach per `references/outreach-guide.md` - the lowercase
style, language policy, structure, signature and channel rules all come from
`identity.md`. Collect all drafts into one manifest
`~/.revenue-engine-imparatta/outreach/<DATE>-batch.md` and archive per-lead copies
to `~/.revenue-engine-imparatta/leads/<slug>-<DATE>/`. Each manifest entry must use
the machine-readable fields in `references/outreach-guide.md`, including
`source: launch agent`, `strategy/signal`, confirmed title and High-gate evidence.
Do not put tracker/source metadata into recipient-visible email text. Record the
actual Gmail draft ID immediately after creation, before proceeding to another lead.
Re-check the cap, domain dedupe, exclusions, title and (for hires) posting liveness
immediately before each draft; update the gate record if evidence changed.

**Gmail drafts - gog only.** For every draft-set lead (Step 3) with a verified
deliverable email, write the body to a temp file and create the draft:

```bash
gog gmail drafts create -a federico@imparatta.com \
  --to "<email>" --subject "<subject>" --body-file "<tempfile>"
```

Plain text only, never `--body-html`, **never send or reply**. LinkedIn-only leads get no draft -
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

**Prove the DM, do not assert it.** The runner counts the summary as delivered only
when `slack-receipt.txt` holds the message `ts`. Take the `ts` from the
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
