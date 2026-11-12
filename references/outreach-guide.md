# Cold Outreach Framework

Write one short cold email (and a short LinkedIn DM) per High-fit lead. Inputs: the
lead's record, `~/.revenue-engine-imparatta/services.md` (offers + proof + credibility),
`~/.revenue-engine-imparatta/identity.md` (sender, signature, language policy, CTA), and
`~/.revenue-engine-imparatta/icp.md`.

## Hard rules (non-negotiable)

- **Language**: follow the language policy in `identity.md` exactly (fixed language, or
  by prospect country with the configured fallback). Localize idiomatically: translate
  the message, not word for word. Correct grammar in every language, with a natural
  sign-off per language. Casing follows the brand rules in `identity.md` - for this
  practice that means the whole email is lowercase except other companies' and
  people's proper names.
- **One offer per email** - the strongest fit from the offer mapping. Link that offer's
  landing URL from `services.md` inline where it reads naturally. If no offer cleanly
  fits, pitch the company's general services with the main site URL; a genuine general
  pitch beats a forced specific one.
- **90-150 words** in the body. Cold emails are short.
- **Hyphens only, never em dashes. No emojis.**
- **Proof points exactly as written in `services.md`, nothing beyond them.** The
  proof points there are public on imparatta.com and may be named. Any client or
  engagement NOT in that list is never named - the exclude list in `exclude.md` is
  never referenced in outreach at all.
- **No fabrication.** Only proof points and credibility levers that exist in
  `services.md`. Never inflate numbers, never invent a case.
- **Subject: catchy, never provocative.** Short, specific, tied to their trigger or the
  outcome. No fake urgency, no "Re:"/"Fwd:" tricks, no all-caps, no fear, no insults.
- **CTA**: the meeting link (or ask) from `identity.md`, one sentence.
- **Signature**: the exact signature block from `identity.md`, including any brand
  casing rules. Plain text, no logo, no images.

## Structure

1. **Hook (1-2 sentences)** - name the lead's specific trigger (their funding round,
   the role they are hiring, the operational pain you spotted). Shows homework.
2. **Offer (2-3 sentences)** - the one best-fit offer, framed as solving that trigger,
   with the landing URL linked inline. Use the offer's own key differentiators from
   `services.md`.
3. **Proof (1 sentence)** - one matching proof point from `services.md`, exactly as
   written there.
4. **CTA (1 sentence)** + sign-off + signature.

## LinkedIn DM variant

For every High-fit lead also write a DM: 250-400 characters, same language rules, soft
CTA, no signature, no links unless natural. DMs are ALWAYS sent manually by the user -
never automate LinkedIn (no bots, no Selenium: ToS and account-ban risk).

## Channel decision per lead

- **Verified deliverable email** (`deliverable=yes` from Hunter, numeric
  `finder_score >= 80`, and a confirmed current title) -> full email; create
  a Gmail draft if Gmail delivery is enabled in `preferences.md`.
- **Risky email** (catch-all domain) -> no Gmail draft; LinkedIn-only, with the email listed
  in the report flagged "risky".
- **No verified email but a confirmed LinkedIn profile** -> LinkedIn-only: the DM goes
  in the report and the manifest for manual sending. No Gmail draft.
- **No email and no confirmed profile** -> drop the lead from outreach (it stays in the
  report as research).

## Gmail drafts (gog only)

Write the body to a temp file and create the draft in the imparatta.com mailbox:

```bash
gog gmail drafts create -a federico@imparatta.com \
  --to "<email>" --subject "<subject>" --body-file "<tempfile>"
```

Plain text only - never `--body-html`, never send and never reply. Gmail auto-links bare
URLs on send. Drafts are never auto-sent: Federico reviews and sends every one. Do
NOT use the Gmail MCP `create_draft` tool: the connected MCP mailbox is a different
account.

## Never send twice

Before drafting anything, re-check the dedupe set (SKILL.md Step 0): `lead-history.md`
rows marked Drafted/Contacted, recent Gmail drafts to the same domain, and prior
manifests in `~/.revenue-engine-imparatta/outreach/`. Only draft companies that appear in none.

Dedupe by normalized registrable website AND email domain, not company name alone.
Re-run client exclusion for both domains; no warm-path exceptions. Re-check hire
postings immediately before drafting. Only a saved `HIGH` gate plus the contact
checks qualifies. Honor 3/night and 8/week ceilings, counting prior attempts.

## Output

Collect every draft into one manifest `~/.revenue-engine-imparatta/outreach/<DATE>-batch.md` and
archive a per-lead copy to `~/.revenue-engine-imparatta/leads/<slug>-<DATE>/outreach.md`. Each
entry starts with a machine-readable header, followed by subject/body and LinkedIn DM:

```markdown
### <Company> - <person>

- source: launch agent
- strategy/signal: stuck leadership hire
- domain: acme.com
- source_url: https://boards.greenhouse.io/acme/jobs/123
- source_date: YYYY-MM-DD
- high_gate: HIGH
- gate_record: <saved JSON path>
- offer: <offer name>
- language: english
- hunter_score: 91
- deliverable: yes
- title: Head of Product
- title_confirmed: yes
- title_source_url: <current primary source or LinkedIn profile>
- title_checked_at: <ISO timestamp>
- job_url: https://boards.greenhouse.io/acme/jobs/123
- job_status: OPEN
- job_age_days: 47
- job_checked_at: <ISO timestamp immediately before drafting>
- to: Jane Doe, Head of Product <jane@acme.com>
- draft_id: <actual gog response ID; n/a for report-only DM>
- drafted_at: <ISO timestamp with offset; n/a when no Gmail draft>
```

`source` is always `launch agent` for this engine, including interactive runs.
`strategy/signal` is exactly `stuck leadership hire` or `fresh raise`; retired
signals never enter the draft set. For raises use `n/a` for job fields. Record
actual current title and finder score, not placeholders. Keep these fields out of
the email body. The tracker should copy source and strategy/signal from the matching
manifest entry. A dry run still writes a manifest saying no drafts and why.
