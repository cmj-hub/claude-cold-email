---
name: cold-email-onboarding
description: "First-run setup for the cold-email pack. Merges the fields this pack owns (tone, infrastructure, operations) into the shared brand-config.json and adds its own section to SOUL.md, reading the psp and evp blocks other packs publish. Takes about 10 minutes and does not let the operator skip the inputs that make output specific. Use when brand-config.json or SOUL.md is missing or lacks the cold-email fields; loaded by the main cold-email skill."
user-invocable: false
allowed-tools: Read Write Grep
license: MIT
models: ""

---

# Cold Email Onboarding — first-run setup

Walks the operator through 10 minutes of setup that makes every
downstream output 10x more useful than generic framework prose.

## Activation

Loaded automatically by `cold-email` (the orchestrator) on first
invocation when `brand-config.json` and/or `SOUL.md` are missing from
the project root.

Also user-invocable on demand:
- "Set up brand config"
- "Configure my voice"
- "Re-run cold-email onboarding"
- "Update brand-config"

## Why this exists

Generic cold-email output is worse than no output. The framework is
generic — your ICP + PSP + voice are specific. Without those, the
skill produces vibes-emails that look like every other AI-generated
cold email.

This onboarding sub-skill captures the operator's:

1. **ICP precision** (specific segment, exclusion criteria)
2. **PSP** (signal anchors → felt pain → vocabulary)
3. **EVP** (Schwartz tier + the 22-word line + proof)
4. **Voice** (phrases used + phrases banned + tone settings)
5. **Stories** (case-study reservoir to pull from)
6. **Infrastructure** (domain, inbox provider, deliverability state)
7. **Operations** (weekly cadence, reply routing, experiment log)

Output: the cold-email fields in `brand-config.json` and the
cold-email section of `SOUL.md`, at the project root.

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
  wants to continue, collect them in Steps 3 and 4 and write them in the
  published shapes below.
- **SOUL.md:** add or update only the sections in this pack's template
  (`../../SOUL.md`). Voice sections other packs also use (`Who I am`,
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

```python
# Pseudo-code logic
exists_brand = file_exists("brand-config.json")
exists_soul = file_exists("SOUL.md")

if exists_brand:
    read it; list which of operator, icp, psp, evp, tone,
    infrastructure, operations are present and which are empty
    ask only for the empty ones this pack needs
if exists_soul:
    read it; list which template sections are present and which are empty
if not exists_brand and not exists_soul:
    "Welcome. ~10 minute setup. Ready?"
```

Skip any step whose fields are already filled. Never offer to replace
the files.

### Step 1 — Operator + company

Ask in one batch:

```
First, the basics:

1. Your name (for the sign-off line)?
2. Your title?
3. Your company?
4. Your calendar / booking link?
```

Save to `brand-config.operator`. Fill gaps only; keep any value
another pack already wrote.

### Step 2 — ICP precision check

```
Now your ICP. Be specific. "B2B SaaS" is too broad.

Tell me:
1. The 1-sentence segment (with stage / size / motion / region)
2. The 3 role-titles you target most
3. The 3 exclusion criteria (who you DON'T sell to)

If you're unsure on any of these, that's a signal you need to
sharpen ICP before launching outreach. Let me know if you want to
talk through it, or use a placeholder for now.
```

Save to `brand-config.icp`. Fill gaps only.

If the operator says "I don't know yet" — push back ONCE:

> A vague ICP produces vague cold email. Want to use placeholders
> like "Tech companies, role: VP+, exclusion: pre-PMF" — and we'll
> mark this for review after the first 100 sends?

### Step 3 — Pain Signal Profile (PSP)

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

### Step 4 — EVP

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

### Step 5 — Voice fingerprints (SOUL.md)

```
Now your voice. This is what makes the output sound like YOU,
not Jay Mount or ChatGPT.

1. 5-10 phrases you use a lot in your writing (look at your last 10
   emails / posts — what shows up repeatedly?)
2. 5-10 phrases you would NEVER write (your hard nos)
3. Tone settings:
   - Formality: Casual / Professional / Direct
   - Sentence length: Short / Medium / Mixed
   - Confidence: High / Hedged / Calibrated
   - Humor: Dry / Never / Always
   - First-person: I / We / Both
4. 3-5 stories or receipts you reference often (these become the case-study reservoir)
5. Any topic you absolutely will not write about (boundaries)
```

Save to the matching sections of `SOUL.md` (markdown, not JSON,
since voice is descriptive). If SOUL.md already has voice sections from
another pack, read them and ask only for what is missing. Phrases-banned
also go to `brand-config.tone.banned_phrases`.

### Step 6 — Infrastructure

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

### Step 7 — Operations

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

### Step 8 — Write the files

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

### Step 9 — Re-onboarding cadence

```
Final note — brand profiles decay. Re-run this onboarding when:
- Your ICP shifts (new segment / segment cull)
- Your EVP changes (especially after a 30-day reply-rate review)
- Your buyer's vocabulary evolves
- Quarterly minimum

Re-run with: `/cold-email onboarding refresh` (asks field by field;
never replaces the file)
```

## Stress-test mode

User-invocable: `/cold-email onboarding stress-test`

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

- `../../brand-config.example.json` — full template
- `../../brand-config.schema.json` — field definitions and required keys
- `../../SOUL.md` — voice template
- `../../AGENTS.md` — behavior rules
- Sister skills:
  - `cold-email-kickoff` — adaptive router that uses these files
  - `cold-email-craft` — drafts emails using brand + voice
  - `cold-email-audit` — audits programs against brand + voice
