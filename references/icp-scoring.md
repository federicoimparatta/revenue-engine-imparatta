# Lead Fit Scoring

Score every lead **High / Medium / Low** against the client's ICP. The source of truth
is `~/.revenue-engine-imparatta/icp.md` (targets, offer mapping, buyer titles) plus
`~/.revenue-engine-imparatta/preferences.md` (weights, dealbreakers); this file is the rubric.

When `TYPESAFE_API_KEY` is configured, `scripts/evaluate-leads.md` gets the first four
dimensions below as one TypeSafe (Jev) call via `scripts/typesafe_score.py`, then
composes the band itself using the weights here and in `preferences.md` - the model
answers the dimension, never the band. Without a key, score the same dimensions by
hand from this rubric; the definitions below are shared by both paths.

## Offer mapping

`icp.md` contains a table mapping signals to offers (built during setup):

| Signal on the lead | Best offer | Landing URL |
|---|---|---|
| (from icp.md) | (from services.md) | (from services.md) |

A lead can map to two offers. Lead with the single strongest in outreach; mention the
second only if it strengthens the pitch.

## Scoring dimensions

- **Vertical match** - is the company in a target industry from `icp.md`? In-vertical
  = full marks; adjacent = partial; unrelated = fail.
- **Signal strength** - a fresh, specific signal (recent raise, an open role that IS
  the pain, hard evidence of the problem) is STRONG; a generic posting or a stale
  signal (older than the recency window in `preferences.md`) is WEAK.
- **Geography** - inside the target geographies from `icp.md`. If outreach is
  localized per the language policy, near-miss geographies can still qualify when the
  signal is strong; hard-avoid regions never do.
- **Company stage and budget** - matches the stage/size range in `icp.md`. Companies
  plausibly able to pay = good; too early/no budget, or so large they solve this
  in-house with no visible gap = down-weight.
- **Offer fit** - does one offer in `services.md` cleanly solve a real, current need
  evidenced by the signal? A forced fit is a Low.

## Bands

- **High** - target vertical + clear current signal + in-geo + plausible budget + a
  clean single-offer fit. These get outreach drafts (respect the per-run cap in
  `preferences.md`; named contacts first).
- **Medium** - partial: right vertical but weak signal, or strong signal but edge
  geography/stage. "Worth-an-ask" speculatives.
- **Low / skip** - off-vertical, no budget, dealbreaker hit, no offer fit, or on the
  exclude list.

## Hard exclude (apply BEFORE banding)

Everything in `~/.revenue-engine-imparatta/exclude.md` is dropped entirely:

- **Clients** - never pitched AND never named anywhere in any output.
- **Partners** - never pitched.
- **Competitors** - never pitched; a candidate that turns out to sell what the client
  sells goes in the Skipped table with the reason, not a pitch.

Also drop, always: any company already in `lead-history.md` (duplicate), and any
lookalike reference company from `icp.md` unless the user explicitly asks to pitch it.
