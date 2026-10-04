# Bulk-sender rules (Google, Yahoo, Microsoft)

What the large mailbox providers require from senders, and what that
means for cold outreach. Rules change; check the provider pages linked
at the bottom before treating this as current.

## Who counts as a bulk sender

- **Google**: roughly 5,000+ messages in a day to personal Gmail
  accounts (`@gmail.com`, `@googlemail.com`), counted across the
  primary domain. Once classified, the status does not expire.
- **Yahoo**: "significant volume" to Yahoo / AOL consumer mailboxes;
  same requirements as Google in practice.
- **Microsoft**: 5,000+ messages a day to Outlook.com consumer
  addresses (`outlook.com`, `hotmail.com`, `live.com`), enforced from
  May 2025.

These rules target **consumer** mailboxes. Most B2B cold email lands in
Google Workspace or Microsoft 365 business tenants, which apply their
own filtering. Meet the bulk rules anyway: business filters reward the
same signals, and one consumer-domain row on a list makes them apply.

## Requirements for every sender (Google)

- SPF **or** DKIM passing for the sending domain
- Valid forward and reverse DNS (PTR) for sending IPs
- TLS for transmission
- Spam-complaint rate in Google Postmaster Tools below **0.3%**
  (aim under 0.1%)
- Messages formatted per RFC 5322; don't impersonate Gmail in `From:`

## Additional requirements for bulk senders

| Requirement | Google / Yahoo (Feb 2024) | Microsoft (May 2025) |
|---|---|---|
| SPF passing | Required | Required |
| DKIM passing | Required | Required |
| DMARC record published | Required — `p=none` is the minimum | Required — `p=none` is the minimum |
| DMARC alignment | `From:` domain aligns with SPF or DKIM domain | Same |
| One-click unsubscribe | Required for marketing / subscribed mail (RFC 8058 `List-Unsubscribe-Post`), honoured within 2 days | Functional unsubscribe link expected |
| Spam rate | Below 0.3% | Not stated as a number; complaints still count |

**Common misreading:** the rules do *not* require `p=quarantine` or
`p=reject`. They require a DMARC record. Moving to `quarantine` once
your aggregate (`rua=`) reports are clean is best practice, and the
deliverability checker scores it as an "important" check, not a
"critical" one.

## What this means for cold outreach

- **Send from a dedicated subdomain or secondary domain**
  (`outreach.example.com`), each with its own SPF, DKIM, and DMARC.
  Reputation damage stays off the primary domain.
- **Authenticate before warm-up**, not after. A mailbox that warmed up
  unauthenticated starts over.
- **Keep complaint rate low by keeping the list tight.** One signal-
  anchored email to 50 right people beats 500 to a scraped list.
  Run `cold-email-list-quality` first.
- **Never fake threading.** A `Re:` / `Fwd:` subject without a prior
  thread is a deceptive subject line — a spam signal to filters and a
  CAN-SPAM problem in the US.
- **Give an opt-out.** Cold email is not "subscribed" mail, so the
  one-click header is not strictly required for it, but a plain
  "reply 'no' and I won't follow up" line is cheap and keeps complaints
  down.

## Law is separate from deliverability

Provider rules decide inbox placement. Law decides what you may send.
In brief (not legal advice):

- **US — CAN-SPAM**: accurate headers, no deceptive subject lines, a
  valid postal address, a working opt-out honoured within 10 business
  days.
- **EU / UK — GDPR, PECR**: B2B cold email usually relies on legitimate
  interest; document it, keep the email relevant to the person's role,
  and honour objections immediately. Rules differ by country.
- **Canada — CASL**: stricter consent rules; check before sending.

The operator owns compliance. The pack drafts; it does not send.

## Sources

- Google: Email sender guidelines — support.google.com/a/answer/81126
- Yahoo: Sender best practices — senders.yahooinc.com/best-practices
- Microsoft: Outlook.com high-volume sender requirements (Microsoft
  Defender for Office 365 blog, April 2025)
- RFC 7208 (SPF), RFC 6376 (DKIM), RFC 7489 (DMARC), RFC 8058
  (one-click unsubscribe)
