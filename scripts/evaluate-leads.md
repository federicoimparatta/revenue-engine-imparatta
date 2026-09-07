# Lead Evaluation Subagent

Use this to score raw leads in parallel (one subagent per batch of records, or per
record for borderline ones).

## Input given to the subagent

- A raw lead record: company, website domain, vertical + country, the signal + source
  URL, candidate offer fit, decision-maker (if found), why-now.
- The rubric in `references/icp-scoring.md`, the client's `~/.revenue-engine-imparatta/icp.md`
  and `services.md`, and the exclude list in `~/.revenue-engine-imparatta/exclude.md`.

## Task

For each record, return a structured verdict:

```
- company: <name>
  domain: <domain>
  country: <HQ country>
  language: <outreach language per the policy in identity.md>
  exclude: <yes/no - and which list if yes>
  fit: <High | Medium | Low>
  offer: <best-fit offer name from services.md - or "general">
  reason: <one line: vertical + signal strength + stage + offer fit>
  linkedin: <real linkedin.com/in/... URL - or "not found: search '<name> <company>'">
  contact: <name, title - or "role to target: <title>" if no person>
  email: <Hunter-resolved address + status: yes | risky | unconfirmed | skipped (no key)>
```

Resolve `email` with `scripts/hunter_lookup.py enrich` when a Hunter key is configured;
never guess a pattern. Only status **yes** is emailable; **risky** or **unconfirmed**
means LinkedIn-only.

## Rules

- Apply the **hard exclude first**. If excluded, set `fit: Low`, `exclude: yes`, no
  outreach - it goes in the Skipped table.
- A company already in `~/.revenue-engine-imparatta/lead-history.md` is a duplicate - flag it so
  the workflow drops it from new results.
- LinkedIn URLs must be confirmed by search, never inferred from the name.
- Be skeptical of giant enterprises that solve this problem in-house - cap at Medium
  ("worth-an-ask") unless there is a clear, specific gap.
- Down-check anything hitting a dealbreaker in `preferences.md`.
