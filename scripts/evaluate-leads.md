# Lead Evaluation

Evaluate the account against `references/icp-scoring.md`, `icp.md`, `services.md`
and `preferences.md`. Do not delegate unless the user requests it for this run.
An optional model may score dimensions; only `high_gate.py` decides High.

First run `scripts/domain_util.py check-exclude --company "<name>" --domain
"<website>" --email "<email>" --exclude-file
~/.revenue-engine-imparatta/clients-exclude.json` (one line). Excluded leads are
skipped, never evaluated or proposed as warm paths. Errors block drafting.
Apply `exclude.md`, dealbreakers and domain dedupe against both engines too.

For each survivor, when `TYPESAFE_API_KEY` is configured in the environment or
`~/.revenue-engine-imparatta/.secrets/typesafe.env`, get advisory dimensions with:

```bash
python3 "<SKILL_DIR>/scripts/typesafe_score.py" score --record <lead.json>
```

The scorer input is a JSON object containing `company`, `vertical`, `country`,
`signal` (the verified buying intent), `source_url`, `icp_verticals` (array),
`icp_geographies` (array), `icp_stage` (string), and `offers` (array of objects
with `name` and `what`). Read ICP/offer context from the local config files.
It returns `vertical_match`, `signal_strength`, `geography_fit`,
`stage_budget_fit` and `offer_fit`, with confidence/probability. Missing key,
API failure or confidence below 0.5 means assess the affected dimensions from
evidence by hand. Do not treat model confidence as dated evidence, verified
stage, job age, current title or liveness. Never send excluded records to the
scorer. Either scoring path must still run the gate below; neither can choose
or override the High band.

For each survivor, build an evidence-backed JSON record following the docstring
in `scripts/high_gate.py` and run:

```bash
python3 "<SKILL_DIR>/scripts/high_gate.py" --record <gate.json>
```

Only `HIGH` can be High. `NOT_HIGH` or an error never gets a Gmail draft. No
hand/model override; no promotion to fill the nightly ceiling. Shipping stalls
and leadership departures are skipped on scheduled runs. Save the input/verdict.

Return this structured verdict with the report:

```yaml
company: <name>
domain: <normalized registrable website domain>
country: <country>
language: <identity policy>
stage: <verified stage>
vertical_match: <in_vertical/adjacent/off_vertical>
geography_fit: <in_geo/remote/out_of_scope>
exclude: <yes/no, checked names and both domains>
duplicate_domain: <true/false>
signal_type: <stuck leadership hire/fresh raise>
source_url: <real source>
source_date: <YYYY-MM-DD>
job_title: <target role, or n/a>
job_status: <OPEN/CLOSED/UNKNOWN/n/a>
job_age_days: <integer or null>
job_date_kind: <first_posted or unknown>
high_gate: <literal HIGH or NOT_HIGH with reasons>
gate_record: <saved JSON path>
fit: <High/Medium/Low>
offer: <one services.md offer>
reason: <evidence of vertical, geography, stage, signal, offer>
contact: <confirmed person>
title: <current title, never blank for a draft>
title_source_url: <current LinkedIn/primary source>
title_checked_at: <ISO timestamp>
linkedin: <real confirmed profile or not found>
email: <Hunter-resolved address or unavailable>
hunter_score: <numeric finder score or null>
deliverable: <yes/risky/no/unknown>
source: launch agent
```

Only `deliverable=yes` with numeric `finder_score >=80` AND a confirmed current
title is emailable. Missing/low scores, risky or unknown results mean no Gmail
draft. A current LinkedIn profile permits a report-only manual DM. Never guess
addresses or profile URLs. Re-check client/email-domain exclusion after enrichment
and re-fetch stuck-hire postings immediately before drafting. Maximum 3 drafts per
night and 8 per Monday-Sunday week, including earlier same-night attempts.
