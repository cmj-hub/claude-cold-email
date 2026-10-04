# Setup — the cold-email fields in brand-config.json and SOUL.md

First-run setup for this pack: merges `tone`, `infrastructure`, and `operations` into the shared `brand-config.json` and adds this pack's voice settings to `SOUL.md`. About 10 minutes.

## Contents

- When this runs
- Shared files contract
- Workflow
- Stress-test mode
- References

## When this runs

The main skill's preflight sends the operator here when `brand-config.json` or `SOUL.md` is missing, or lacks the cold-email fields. Also on demand: `/cold-email:cold-email setup`, "set up brand config", "configure my voice", "update brand-config".

Generic cold email is worse than none. The framework is generic; the operator's ICP, PSP, and voice are specific. Setup captures the parts this pack owns and reuses what the rest of the suite already wrote.

Output: the cold-email fields in `brand-config.json` and the cold-email sections of `SOUL.md`, at the project root.

## Shared files contract

Every pack in the GTM operator suite shares one `brand-config.json` and
one `SOUL.md` at the operator's project root.

- **Merge at the field level.** Read the existing file first. Add or
  update only the fields this pack owns, and leave every other key
  exactly as it was. Never rewrite the file from the example. Never
  delete another pack's keys. Show the diff and ask before changing a
  field that already has a value.
- **This pack owns** `tone`, `infrastructure`, and `operations`.
- **Shared, fill gaps only:** `operator` and `icp`.
- **Read, not owned:** `psp` (published by the psp pack) and `evp`
  (published by the evp pack). If a block is present, use it as is and
  do not re-ask. If it is missing, say which pack produces it and how to
  install it: `/plugin install psp@gtm-operator-skills` then `/psp:psp`,
  or `/plugin install evp@gtm-operator-skills` then `/evp:evp`. Do not
  invent the values. Only when the operator has no psp or evp pack and
  wants to continue, collect them in Steps 2 and 3 and write them in the
  published shapes below.
- **SOUL.md:** add or update only the sections in this pack's template
  (`../../../SOUL.md`). Voice sections other packs also use (`Who I am`,
  `Phrases I use a lot`, `Phrases I refuse`, `Stories I lean on`) are
  shared: merge bullets, keep what is there. Never rewrite another
  pack's section. If SOUL.md does not exist, start it from the template.

Published block shapes (write exactly these keys):

```json
"psp": { "signal_anchors": ["..."], "primary_pain": "...", "timing_trigger": "...", "felt_pain_role": "...", "vocabulary": ["..."] }
"evp": { "tier": 3, "primary": "...", "outcome": "...", "tradeoff": "...", "proof": "..." }
```

## Workflow

### Step 0 — Detect prior state

Read `brand-config.json` and `SOUL.md` if present. List which of `operator`, `icp`, `psp`, `evp`, `tone`, `infrastructure`, `operations` are filled and which are empty, and which SOUL.md sections are filled. Ask only for the empty ones this pack needs. Never offer to replace the files.

### Step 1 — Shared setup (operator, ICP, shared voice)

`operator`, `icp`, and the shared SOUL.md sections (`Who I am`, `Phrases I use a lot`, `Phrases I refuse`, `Stories I lean on`) belong to the whole suite. If any are missing, say:

> Run `/gtm:setup` once for the whole suite. It asks these questions one time and every pack reads the answers.

If the gtm plugin is not installed (`/plugin install gtm@gtm-operator-skills`) and the operator wants to continue now, ask only the missing shared fields, in one short batch:

```
1. Your name, title, company, and booking link?
2. Your ICP in one sentence (stage / size / motion / region), the 3 role titles you target, and 3 exclusions?
```

Write them to `operator` and `icp` (fill gaps only). If the ICP answer is vague, push back once: "A vague ICP produces vague cold email. Use a placeholder and we'll mark it for review after the first 100 sends?"

Then ask only this pack's questions below.

### Step 2 — Pain Signal Profile (PSP)

If `brand-config.psp` exists, show it back in one line and move on.
If only `psp_drafts.primary` exists, use it and suggest locking it with
`/psp:psp`. If neither exists, point to the psp pack first:

> No PSP yet. The psp pack builds it and publishes it here:
> `/plugin install psp@gtm-operator-skills`, then `/psp:psp`.

Only if the operator has no psp pack and wants to continue, ask:

```
The PSP is the bridge from a public signal to felt operational pain.

Tell me:
1. 3 public signals you anchor outreach on (job posts, funding, hires, launches, pricing changes)
2. The primary pain the signal implies — in YOUR buyer's vocabulary, not your category jargon
3. The 90-day trigger that makes it acute right now: new-exec / budget-cycle / obvious-failure
4. The role that FEELS the pain (often a layer below the buying authority)
5. 4-8 phrases your buyer uses about this pain (read their job posts, LinkedIn comments, conference talks)
```

Save to `brand-config.psp` in the published shape: answer 1 becomes
`signal_anchors`, then `primary_pain`, `timing_trigger`,
`felt_pain_role`, `vocabulary`. Leave a field empty rather than guess.

### Step 3 — EVP

If `brand-config.evp` exists, show `evp.primary` back and move on. If
it is missing, point to the evp pack first:

> No EVP yet. The evp pack writes it and publishes it here:
> `/plugin install evp@gtm-operator-skills`, then `/evp:evp`.

Only if the operator has no evp pack and wants to continue, ask:

```
Your EVP — the one-line value prop.

1. Which Schwartz awareness tier (1-5) is your primary outreach
   audience in? (Most B2B cold-email targets are Tier 2 or 3.)
2. Your 22-word EVP using the shape: "For {ICP}, in {pain}, we ship
   {specific outcome} without {specific tradeoff}."
3. The specific outcome (must include a number)
4. The specific tradeoff
5. Your strongest proof point (case study / metric / receipt)
```

Save to `brand-config.evp` in the published shape: `tier`, `primary`,
`outcome`, `tradeoff`, `proof`. Never invent the proof.

### Step 4 — Voice settings (SOUL.md)

The shared voice sections (`Who I am`, `Phrases I use a lot`, `Phrases I refuse`, `Stories I lean on`) come from `/gtm:setup` or another pack. Read them; ask for one only if it is empty. Then ask this pack's own questions:

```
1. How you talk in a cold email:
   - Formality: Casual / Professional / Direct
   - Sentence length: Short / Medium / Mixed
   - Confidence: High / Hedged / Calibrated
   - Humor: Dry / Never / Always
   - First-person: I / We / Both
2. Any topic you will not write about in outreach?
3. Any phrase to ban in cold email beyond the "Phrases I refuse" list?
```

Save answers to `## How I talk` and `## Topics I will NOT write about` in `SOUL.md` (markdown, since voice is descriptive). Every refused phrase, shared or new, also goes to `brand-config.tone.banned_phrases`.

### Step 5 — Infrastructure

```
Your sending setup:

1. Sending domain (e.g. outreach.acmecloud.com)
2. Inbox provider (smartlead / instantly / GSuite / O365 / custom)
3. Warm-up status (fresh / ramped / mature)
4. Last deliverability audit date
5. DMARC policy (none / quarantine / reject)
```

If the operator hasn't run deliverability, suggest:

> Want me to run a deliverability audit now? (15 DNS + reputation
> checks; no paid APIs. Takes ~30 seconds.) Or save this for later?

Save to `brand-config.infrastructure`.

### Step 6 — Operations

```
Your weekly cadence + reply routing.

Pick a weekly rhythm:
- Mon/Wed/Fri (default — most teams)
- Daily small batch
- Custom

Reply routing — when a reply comes in, what should happen?
- buy_signal → ?
- positive → ?
- neutral → ?
- not_interested → ?
```

Save to `brand-config.operations`.

### Step 7 — Write the files

Merge the captured data into `brand-config.json` + `SOUL.md` at the
project root, field by field, per the shared files contract above. If
`brand-config.json` is new, start it with the `"$schema"` line from
`brand-config.example.json` so editors validate it against
`brand-config.schema.json`. Leave a field empty rather than inventing a
value the operator did not give. Show the diff of every changed field,
ask before changing a field that already had a value, then show a
preview:

```
✓ brand-config.json (tone, infrastructure, operations merged; other keys untouched)
✓ SOUL.md (voice fingerprints + 5 stories merged in)

Try a quick test:
> Write a cold email to {name}, {role} at {company}. They just {signal}.

The output will now use:
- Your ICP precision
- Your EVP variant
- Your voice (phrases-you-use + phrases-banned)
- The JMC framework on top
```

### Step 8 — Re-onboarding cadence

```
Final note — brand profiles decay. Re-run setup when:
- Your ICP shifts (new segment / segment cull)
- Your EVP changes (especially after a 30-day reply-rate review)
- Your buyer's vocabulary evolves
- Quarterly minimum

Re-run with: /cold-email:cold-email setup refresh (asks field by
field; never replaces the file)
```

End the run with one line: `Next: /cold-email:cold-email status` (it names the next step: psp, evp, or deliverability).

## Stress-test mode

`/cold-email:cold-email setup stress-test`

Loads existing brand-config + SOUL and walks the operator through
edge cases:

- "Your ICP says <X>. Show me a real prospect that fits — does the
  signal-pain-EVP chain hold?"
- "Your EVP says <Y>. Read it out loud. Does it sound like something
  your buyer would say back? If not, refine."
- "Your banned-phrases list has 5 items. I'll generate a 'banned'
  email and see if you accept or reject. If you accept any, the list
  needs more items."

## References

- `../../../brand-config.example.json` — full template
- `../../../brand-config.schema.json` — field definitions and required keys
- `../../../SOUL.md` — voice template
- `../../../AGENTS.md` — behavior rules
- [status.md](status.md) — names the next step from these files
- [craft.md](craft.md) — drafts emails using brand + voice
- [audit.md](audit.md) — audits the program against brand + voice
