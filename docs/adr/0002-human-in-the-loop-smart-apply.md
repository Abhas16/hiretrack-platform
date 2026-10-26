# ADR 0002: Smart Apply never submits applications

**Status:** accepted

## Context
It would be easy to "auto-apply". But job portals' terms forbid bots, automated applications
hurt the applicant, and storing portal credentials would be a serious security liability.

## Decision
- job-scout reads **only public, documented board APIs** (Greenhouse, Lever, Ashby), checks
  robots.txt, rate-limits per host and sends an honest User-Agent.
- match-scorer only scores and drafts a kit (cover note + bullets) for the user to edit.
- "Approve" creates an APPLIED application and opens the job URL. The user submits it.
- No browser automation, no scraping of HTML pages, no stored credentials.

## Consequences
- Fewer sources than a scraper would have, but every source is legal and stable.
- The product promise stays honest: HireTrack saves time, the human stays in charge.
