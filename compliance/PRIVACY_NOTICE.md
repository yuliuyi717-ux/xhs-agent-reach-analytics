# Privacy Notice

## 1. Controller Information

- Project: XHS Agent-Reach Analytics
- Maintainer/Controller: Feiyang Yu
- Contact: open a GitHub issue with a `privacy` or `compliance` label.

## 2. Data Categories

Depending on configuration, the project may process:

- Account/session artifacts (for example cookies and auth state)
- Public content metadata (title, URL, timestamps, engagement metrics)
- Content text fields (if enabled)
- Operational logs and error traces

## 3. Processing Purposes

- Keyword monitoring and trend analytics
- Operational quality checks and debugging
- Internal research and reporting

## 4. Legal Basis

- The deployer/operator must determine and document the lawful basis before use in each jurisdiction.
- Typical bases include legitimate interest, consent, or contractual necessity, depending on scenario and law.

## 5. Data Minimization and Defaults

- Only collect fields required for stated purposes.
- Disable optional content fields if not needed.
- Avoid collecting special categories of personal data.

## 6. Retention and Deletion

- Default retention window: 30 days (recommended baseline).
- Deletion method: remove date-partitioned files under `data/raw`, `data/by_keyword`, `data/by_date`, `data/reports`, and `data/runlog`.
- User/request handling SLA: 15 business days.

## 7. Sharing and Transfers

- Third-party sharing: none by default.
- Cross-border transfer: none by default; if enabled by operator, appropriate safeguards and notices are required.

## 8. Security Controls

- Access control for output files
- Encryption at rest and in transit where applicable
- Audit logging for sensitive operations

## 9. Data Subject Rights

Where applicable, users may request:

- Access, correction, deletion
- Restriction or objection to processing
- Data portability

Contact: open a GitHub issue with a `privacy` label.

## 10. Changes

This notice may be updated as the project evolves.
