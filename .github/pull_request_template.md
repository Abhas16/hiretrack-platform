## What and why

<!-- One or two sentences: what changes, and the reason. -->

## How it was tested

- [ ] `make test` / `make web-check` pass locally
- [ ] For deploy changes: `helm lint` + `helm template` render cleanly

## Risk

- [ ] Database migration included, and it is backwards compatible (old pods keep running during the rollout)
- [ ] New env var / secret: added to `.env.example`, chart values and deploy/README.md
- [ ] New alert: has a runbook in docs/runbooks
