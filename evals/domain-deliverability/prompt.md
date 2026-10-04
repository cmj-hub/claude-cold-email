---
max_turns: 12
allowed_tools: [Read, Write, Glob, Grep, Bash, Skill]
---

Is outreach.acmecloud.com ready to send cold email? Here is what dig returned this morning:

```
$ dig +short TXT outreach.acmecloud.com
"v=spf1 include:_spf.google.com ?all"
$ dig +short TXT google._domainkey.outreach.acmecloud.com
"v=DKIM1; k=rsa; p=MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA0w"
$ dig +short TXT _dmarc.outreach.acmecloud.com
$ dig +short TXT _dmarc.acmecloud.com
"v=DMARC1; p=none; rua=mailto:dmarc@acmecloud.com"
$ dig +short MX outreach.acmecloud.com
1 smtp.google.com.
```

Check SPF, DKIM and DMARC and tell me what to fix before we launch Monday.
