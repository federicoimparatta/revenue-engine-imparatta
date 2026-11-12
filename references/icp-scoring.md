# Lead Fit Scoring

Score every lead **High / Medium / Low** against the client's ICP. The source of truth
is `~/.revenue-engine-imparatta/icp.md` (targets, offer mapping, buyer titles) plus
`~/.revenue-engine-imparatta/preferences.md` (weights, dealbreakers); this file is the rubric.

## Offer mapping

`icp.md` contains a table mapping signals to offers (built during setup):

| Signal on the lead | Best offer | Landing URL |
|---|---|---|
| (from icp.md) | (from services.md) | (from services.md) |

A lead can map to two offers. Lead with the single strongest in outreach; mention the
second only if it strengthens the pitch.

## High is a pass/fail gate

Apply the hard exclusions first. For every surviving lead, save a JSON gate record
and run `python3 "<SKILL_DIR>/scripts/high_gate.py" --record <gate.json>`.
See the script docstring for the input schema. Save the record, source evidence and
literal verdict with the lead; hand/optional model scores cannot override it.
Every condition must pass:

- Direct target vertical (`vertical_match: in_vertical`), not merely adjacent.
- In-geo per `icp.md`, or verified remote compatibility with Federico's location
  (`geography_fit: in_geo` or `remote`). A generic remote label restricted to an
  incompatible country does not count.
- Verified seed through Series B, within the ICP size/budget bounds (`stage` plus
  `stage_ok: true`). Bootstrapped, later-stage or unknown-stage companies cannot be High.
- Real source URL and a non-future source date. For hires: a permitted structured
  board, target leadership title, still OPEN and first posted >=30 days ago;
  `job_age_days` must match `source_date` and `job_date_kind: first_posted`.
  This is a 30-days-or-older live-posting window, with no maximum age while open.
  For raises: the dated announcement is 0-60 days old, seed/seed extension/pre-A
  or Series A, explicitly funding product or AI build-out. A Series B company can
  qualify through a stuck hire, but a Series B raise is not a qualifying signal.
- A clean single-offer fit from `services.md` (`offer_fit`), with evidence.
- Buying intent is exactly `stuck leadership hire` or `fresh raise` as above.
- Explicitly cleared exclusions, duplicate domains and dealbreakers (all false).
  Missing checks fail closed.

Shipping stalls, changelog gaps, coming-soon pages, social silence and leadership
departures **cannot be High**. Retire those hunts; on scheduled runs, skip them.

## Bands and draft eligibility

- **High**: script prints `HIGH`. Gmail drafting additionally requires Hunter
  `finder_score >= 80`, `deliverable=yes`, and a confirmed current title. Re-check
  stuck-hire liveness immediately before drafting.
- **Medium**: partial fit or unverifiable age/date; report only, no Gmail draft.
- **Low / skip**: off-profile, closed role, no intent/offer/budget, excluded,
  duplicate, or dealbreaker. Never pitch excluded clients, including warm paths.

The cap is a ceiling: at most 3 drafts per night and 8 per Monday-Sunday week.
Count prior same-night attempts too. Draft fewer when fewer pass; never promote
Medium to fill volume. Highs beyond the cap remain High, deferred by cap.

## Hard exclude (apply BEFORE banding)

Run `scripts/domain_util.py check-exclude --company "<company>" --domain "<website>"
--email "<email>" --exclude-file ~/.revenue-engine-imparatta/clients-exclude.json`
(on one line). `EXCLUDE` is a hard skip before evaluation; errors block drafting.
Check BOTH website and email domains independently. Also honor `exclude.md`, all
`preferences.md` dealbreakers, reference lookalikes, and both engines' ledgers.
Use normalized registrable website/email domains for dedupe, not company names;
retain name matching only as an additional backstop for unresolved legacy rows.
