# Open Source Compliance Checklist (Template)

## A. Repository and Licensing

- [ ] Choose and add OSS license (`LICENSE`)
- [ ] Ensure dependency licenses are compatible
- [ ] Remove proprietary keys, tokens, cookies, and local configs

## B. Legal and Policy Docs

- [ ] Fill `compliance/DISCLAIMER.md`
- [ ] Fill `compliance/LEGAL.md`
- [ ] Fill `compliance/PRIVACY_NOTICE.md`
- [ ] Fill `compliance/TAKEDOWN_POLICY.md`

## C. Data Safety

- [ ] No real user datasets committed
- [ ] Sample data is anonymized/synthetic
- [ ] Retention and deletion behavior documented

## D. Platform Risk Controls

- [ ] No instructions for bypassing anti-bot controls
- [ ] Default rate/pace is conservative and randomized
- [ ] Scope-limiting options enabled by default (time window, max volume)

## E. Security

- [ ] `.env` and secrets ignored by git
- [ ] Security contact documented (`SECURITY.md`, optional)
- [ ] Known-risk dependencies reviewed

## F. Release Notes

- [ ] Add "Not legal advice" note in README
- [ ] Add "No affiliation" statement
- [ ] Add "User responsibility" section for ToS compliance

## G. Final Review

- [ ] Peer review completed
- [ ] Optional legal counsel review completed
- [ ] Tag and publish release
