# Open Source Compliance Checklist

## A. Repository and Licensing

- [ ] Add an OSS license file (`LICENSE`)
- [ ] Confirm dependency license compatibility
- [ ] Remove proprietary keys, tokens, cookies, and local configs

## B. Legal and Policy Docs

- [ ] Review `compliance/DISCLAIMER.md`
- [ ] Review `compliance/LEGAL.md`
- [ ] Review `compliance/PRIVACY_NOTICE.md`
- [ ] Review `compliance/TAKEDOWN_POLICY.md`

## C. Data Safety

- [ ] No real user datasets committed
- [ ] Sample data is anonymized or synthetic
- [ ] Retention and deletion behavior documented

## D. Platform Risk Controls

- [ ] No instructions for bypassing anti-bot controls
- [ ] Default rate and pace is conservative and randomized
- [ ] Scope-limiting options enabled by default (time window, max volume)

## E. Security

- [ ] `.env` and secrets ignored by git
- [ ] Security contact documented (`SECURITY.md`, optional)
- [ ] Known-risk dependencies reviewed

## F. Release Notes

- [ ] Add "not legal advice" note in README
- [ ] Add "no affiliation" statement
- [ ] Add "user responsibility" section for ToS compliance

## G. Final Review

- [ ] Peer review completed
- [ ] Optional legal counsel review completed
- [ ] Tag and publish release
