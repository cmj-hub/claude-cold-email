# JMC Cold Email Framework

The framework underneath every output this skill produces. Load this
when a user asks "why this shape", "what's the framework", or before
explaining a recommendation.

## Contents

- The framework, in one diagram
- The four blocks
- Constraints (the shape)
- Banned patterns
- The signal-anchored opener prompt
- 3-touch sequence
- The "rewrite the weakest line" sub-prompt
- Free hosted version

## The framework, in one diagram

```
Signal  →  Pain  →  EVP  →  Ask
  ↓         ↓       ↓       ↓
 What     What     What     What
 they      that    you do   you want
 just     means    about    them to
 did                it       do next
```

Every line of a cold email exists to serve one of these four jobs. If
a line doesn't, cut it.

## The four blocks

### 1. Signal (the opener)

A signal is something the recipient (or their company) did **publicly,
recently, and verifiably**. It is not a guess about who they are; it is
a thing they did.

**Good signals:**

- Just posted a job for `<role>` on LinkedIn (4 days ago is fresh; 60
  days is stale)
- Just announced funding (Series A/B/C, within 30 days)
- Just shipped a feature, podcast appearance, or content piece
- Just hired or promoted a relevant exec
- Just changed pricing, packaging, or website positioning

**Not signals:**

- "I noticed you're a VP of Marketing at a SaaS company"
- "I saw your company is growing"
- "I came across your LinkedIn"

The opener line **names the signal in the source's words**. No
"impressive growth," no "great team." Quotation marks go only around
words the source really contains.

### 2. Pain (the implication)

The pain is what the signal **implies** about the recipient's
operational reality. A Pain Signal Profile (PSP) is the link from a
public signal to a felt pain.

**Examples:**

| Signal | Implied pain |
|---|---|
| Just posted Demand Gen Lead role | Pipeline gap; current motion isn't producing SQLs |
| Just announced Series B | Pressure to 3x revenue in 18 months; CAC must hold |
| Just shipped enterprise tier | Need new sales motion; legacy SDRs not built for $50k+ ACV |
| CRO just hired | Probably re-evaluating the GTM stack in next 90 days |

The pain line is **one sentence, in their language, not yours**.

### 3. EVP (your one-line value prop)

EVP = Early Value Proposition. It's not a feature list. It's the
single sentence that says: *"For people in this pain, we're the one
team that does <specific outcome> without <obvious tradeoff>."*

**Template:**

```
We help <ICP segment> hit <outcome> without <obvious tradeoff>.
```

**Examples:**

- "We help Series-B SaaS rebuild first-touch email around public signals without changing their sequencer."
- "We help PLG teams convert free users to enterprise without breaking
  the self-serve motion."

**EVP rules:**

- ≤22 words
- One specific outcome (no "improve" or "optimize")
- One specific tradeoff (no "and more")
- The recipient's ICP segment named explicitly

### 4. Ask (the binary CTA)

A binary CTA gives the recipient exactly two options: yes or no. Not
"let me know" (open-ended), not "would love to chat" (vague), not
"interested in learning more" (multi-step).

**Good binary CTAs:**

- "Worth a look?"
- "Is <their pain, in their words> on your list this quarter?"
- "Want me to send the case study?" (only if it exists)
- "Worth 15 minutes Thursday at 11am PT?" (only with the operator's real availability)

**Bad CTAs:**

- "Let me know if you'd like to learn more"
- "Happy to chat whenever works"
- "Interested?"
- "Let me know your thoughts"

## Constraints (the shape)

| Block | Length | Rule |
|---|---|---|
| Opener (Signal) | 1 sentence | Names the signal in the source's words |
| Pain | 1 sentence | In their language |
| EVP | 1 sentence | ≤22 words |
| Ask | 1 sentence | Binary; a day or time only from the operator |
| Total | <90 words | Strict |

## Banned patterns

The skill refuses to produce these; if user requests them, push back:

- "Hope you're well" / "Hope this finds you well" / "Hope your week is going well"
- "Just wanted to..." / "Just bumping this..."
- "Following up on my last email"
- "Did you get a chance to..."
- "Let me know your thoughts"
- "Happy to chat whenever"
- Multi-paragraph value-prop monologues
- Stacked questions ("Are you A? Or B? Or C?")
- Assumed first-name-basis ("Hey Sarah! How's it going?")
- "Quick question" (opener; almost always not quick)
- "Congratulations on..." (flattery opener, any touch)

## The signal-anchored opener prompt

This is the canonical first-touch template. The skill's `craft`
mode uses this:

```
Write a cold email to {firstName}, {role} at {company}. The signal
you're opening on: {signal}. The pain that signal implies: {pain}.
Your one-line EVP: {evp}.

Constraints:
- <90 words total
- Quote the signal verbatim in line 1
- One sentence per block (signal / pain / EVP / ask)
- One yes/no question; no invented day, time or asset
- No "Hope you're well", no "Just wanted to"
- Sign as {senderName}
```

## 3-touch sequence

When the first touch gets no reply, the JMC sequence is:

| Day | Touch | Shape |
|---|---|---|
| 0 | T1 — Signal-anchored opener (above) | Full framework |
| 3 | T2 — 1-line case study | "<peer company> hit <outcome> in <timeframe>. Worth comparing to how you run it today?" |
| 7 | T3 — Different angle on the same PSP | Same pain, different framing (cost / risk / opportunity-cost) |
| 14 | T4 — Binary close | "If <pain> isn't on the roadmap right now, should I close the loop?" |

Each touch <70 words. No "just bumping this" anywhere.

## The "rewrite the weakest line" sub-prompt

A surgical critique mode the skill offers as a final-pass quality
check. Identifies the single weakest line in a draft and rewrites it
in the same voice, with a one-sentence rationale.

This is the canonical "ship-or-cut" decision aid before sending.

## Free hosted version

The same job runs in a browser, no install and no key:
[Cold Email Linter](https://jaymountconsulting.com/tools/cold-email-linter)
