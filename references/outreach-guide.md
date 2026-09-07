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
3. **Proof (1 sentence)** - one matching anonymized proof point (vertical + country
   only).
4. **CTA (1 sentence)** + sign-off + signature.

## LinkedIn DM variant

For every High-fit lead also write a DM: 250-400 characters, same language rules, soft
CTA, no signature, no links unless natural. DMs are ALWAYS sent manually by the user -
never automate LinkedIn (no bots, no Selenium: ToS and account-ban risk).

## Channel decision per lead

- **Verified deliverable email** (`deliverable=yes` from Hunter) -> full email; create
  a Gmail draft if Gmail delivery is enabled in `preferences.md`.
- **Risky email** (catch-all domain) -> LinkedIn-first; include the email in the report
  flagged "risky", draft it only if the user opts in.
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

Plain text only - never `--body-html` and never a send command. Gmail auto-links bare
URLs on send. Drafts are never auto-sent: Federico reviews and sends every one. Do
NOT use the Gmail MCP `create_draft` tool: the connected MCP mailbox is a different
account.

## Never send twice

Before drafting anything, re-check the dedupe set (SKILL.md Step 0): `lead-history.md`
rows marked Drafted/Contacted, recent Gmail drafts to the same domain, and prior
manifests in `~/.revenue-engine-imparatta/outreach/`. Only draft companies that appear in none.

## Output

Collect every draft into one manifest `~/.revenue-engine-imparatta/outreach/<DATE>-batch.md` and
archive a per-lead copy to `~/.revenue-engine-imparatta/leads/<slug>-<DATE>/outreach.md`. Each
entry: a header line (To: name, title · email + deliverability · offer · language),
the email (subject + body), and the LinkedIn DM.
