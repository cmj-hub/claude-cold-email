# PSP anchors — signal → pain → EVP

A Pain Signal Profile (PSP) is the chain that lets a stranger's email
make sense: something they **did** in public, the operational pain that
action implies, and the one line of value that answers that pain. This
file is how to derive each link without guessing.

The fields map one-to-one to `brand-config.json → psp` and `evp`.

## 1. Signal — something they did, in public, recently

A signal passes all four tests. If it fails one, it is not a signal.

| Test | Pass | Fail |
|---|---|---|
| **Action** — did they *do* it? | "Posted a Senior Demand Gen Lead role" | "VP Marketing at a Series B" (who they are) |
| **Public** — can the operator link to it? | Job post, press release, LinkedIn post, changelog, podcast | "I heard they're struggling" |
| **Recent** — ≤30 days, ideally ≤14 | Posted 4 days ago | Raised a Series B 11 months ago |
| **Quotable** — can line 1 quote it verbatim? | "'Own pipeline from MQL to SQL' — from your Demand Gen Lead post" | "Saw you're hiring" |

Store recurring signal types in `psp.signal_anchors` with their age
limit ("Posted Demand Gen / Growth Lead role ≤14 days").

## 2. Pain — what the signal implies, in their words

Ask: *what would have to be true inside the company for them to take
this action?* That answer is the pain. Then rewrite it in the buyer's
vocabulary, never your category's.

| Signal | Implied pain (operational) | Buyer's words (`psp.vocabulary`) |
|---|---|---|
| Hiring a Demand Gen / Growth lead | Pipeline below plan; current motion isn't producing | "pipeline gap", "not enough SQLs" |
| Hiring 3+ SDRs at once | Top-of-funnel is a headcount bet; ramp time is the risk | "SDR ramp", "quota coverage" |
| Raised a round | Board-set growth target with a deadline | "the plan", "hitting the number" |
| New CRO / VP Sales (≤90 days) | 90-day mandate to show change | "first 90 days", "new playbook" |
| Launched an enterprise tier | Sales motion built for SMB now needs to sell up-market | "longer cycles", "procurement" |
| Pricing page changed | Conversion or expansion is under pressure | "packaging", "upgrade path" |
| Posted about a failed launch / churn | Visible failure with an owner | "what went wrong", "retention" |

Rules:

- One pain per email. Two pains reads as a guess.
- Write it so the reader could have said it. If it contains "optimize",
  "leverage", "synergy", or your product category, rewrite it.
- Name the **felt-pain role** (`psp.felt_pain_role`) — often a layer
  below the budget owner. Write to the person who feels it.
- Name the **timing trigger** (`psp.timing_trigger`): `new-exec`,
  `budget-cycle`, or `obvious-failure`. No trigger means no urgency;
  say so instead of inventing one.

If you cannot connect the signal to a pain without speculation, tell
the operator the chain is weak and ask what they know. Do not paper
over it (`AGENTS.md` rule 10).

## 3. EVP — one line that answers that pain

Shape: **For `<ICP>`, in `<pain>`, we ship `<specific outcome>` without
`<specific tradeoff>`.** ≤22 words.

| Part | Must have | Fails when |
|---|---|---|
| ICP | The segment, not "companies" | "For businesses like yours" |
| Pain | The same pain as line 2 | A different pain than the email set up |
| Outcome | A number and a unit of time | "better pipeline", "more growth" |
| Tradeoff | The cost they expected to pay and won't | Missing — then it's a claim, not a value prop |
| Proof | A real case the operator gave you (`evp.proof`) | Anything you made up |

Example: "For Series-B SaaS in a pipeline gap, we ship 14+ SQLs/month
without hiring 2 more SDRs." (17 words)

## 4. Ask — the binary that follows

The ask should be the smallest next step that tests whether the pain
is real *for them*: a 15-minute call on a named day, or "should I send
the case study?". See `binary-ctas.md`.

## Chain check (run before drafting)

- [ ] Line 1 quotes the signal; the operator can link to it
- [ ] Line 2's pain follows from line 1 without a leap
- [ ] Line 3's outcome answers line 2's pain, not a different one
- [ ] Line 4 asks one yes / no question
- [ ] Every number traces to the operator's own data

Deeper PSP and EVP construction lives in the companion packs
`cmj-hub/claude-psp` and `cmj-hub/claude-evp`.
