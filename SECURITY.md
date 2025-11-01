# Security policy

## Supported versions

| Branch            | Supported | Notes                                    |
| ----------------- | --------- | ---------------------------------------- |
| `main`            | ✅        | Nightly integration branch; security fixes land here first. |
| `release/1.x`     | ✅        | Maintained LTS branch for production deployments. |
| `legacy/0.x`      | ⚠️        | Security fixes only if severity is Critical or High. |

## Reporting a vulnerability

- Email [security@hotpass.example](mailto:security@hotpass.example) with proof-of-concept details, affected version/branch, and reproduction steps.
- Include SBOM/provenance artefacts if available to accelerate triage.
- Optionally encrypt your report with our PGP key (`SECURITY-KEYS.md`).
- Expected response: acknowledgement within **2 business days**, initial triage outcome within **5 business days**.

## Security response process

1. Acknowledge report and create private tracker entry.
2. Assess severity, assign ownership (Security + relevant squad).
3. Develop fix, run full QA + supply-chain suite.
4. Publish advisory and update roadmap/remediation backlog.

### Coordinated disclosure timeline

- **Day 0:** Reporter submits vulnerability. Security team acknowledges within 48 hours.
- **Day 5:** Initial triage complete. Reporter receives severity, affected surface, and planned remediation window.
- **Day 10:** Fix ready for review; quality + supply-chain workflows executed (`Security & Supply Chain` GitHub Action).
- **Day 14:** Coordinated release to supported branches; advisory shared with reporter and published to the security mailing list.
- Timelines may be accelerated for critical issues; we keep reporters informed if additional time is required.

## Disclosure policy

- Responsible disclosure preferred; coordinate release date with reporter.
- Credits provided in advisory unless reporter opts out.
- Non-sensitive fixes batched into monthly security release notes.
