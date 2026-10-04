---
max_turns: 12
allowed_tools: [Read, Write, Glob, Grep, Bash, Skill]
---

Dedup this send list and tell me which rows to drop before I import it into Instantly:

```csv
first_name,last_name,email,company,title,linkedin_url,signal,signal_date
Sarah,Lee,sarah@acmecloud.com,Acme Cloud,VP Demand Gen,https://linkedin.com/in/sarahlee,Posted Senior Demand Gen Lead role,2026-09-30
Sarah,Lee,sarah@acmecloud.com,Acme Cloud,VP Demand Gen,https://linkedin.com/in/sarahlee,Posted Senior Demand Gen Lead role,2026-09-30
Mike,Ross,mike.ross@gmail.com,Beta Ops,COO,https://linkedin.com/in/mikeross,Announced Series B,2026-09-20
Info,Team,info@deltahq.io,Delta HQ,,,,
Priya,Shah,priya@gammasoft.com,GammaSoft,Head of Growth,https://linkedin.com/in/priyashah,Hiring 3 SDRs,2026-04-01
```
