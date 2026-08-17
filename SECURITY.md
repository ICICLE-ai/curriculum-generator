# Security Policy

## Supported Releases

Security fixes are evaluated for the most recent tagged release (currently `v1.0.0`) and the default `main` branch.

| Version | Supported          |
| ------- | ------------------ |
| v1.x    | :white_check_mark: |
| < v1.0  | :x:                |

## Reporting a Vulnerability

**Do not open a public issue for a suspected vulnerability or exposure of credentials, restricted datasets, or sensitive configuration.**

Report concerns privately to the project maintainers:

- **Hari Subramoni**: `subramoni.1@osu.edu`
- **Jason Seh**: `seh.1@osu.edu` / `jassehxia@gmail.com`
- **Backup Channel**: [GitHub Private Security Advisory](https://github.com/OSU-SAI-Lab/curriculum_generator/security/advisories/new)

When submitting a report, please include:
- A concise description of the potential vulnerability.
- Affected component, configuration, or commit SHA.
- Reproduction steps or proof-of-concept when safe to provide.
- Potential impact on cluster environments, container isolation, or student data.
- Any proposed remediations.

## Maintainer Response

Maintainers will acknowledge receipt, evaluate severity and scope, coordinate remediation, and determine whether a security advisory, patch release, configuration update, or documentation notice is required.

## Contributor Security Expectations

Contributors must never commit secrets, API keys, private certificates, proprietary data, restricted datasets, or malicious code. Contributions that add dependencies, data interfaces, workflow execution paths, or cluster deployment configurations must identify any new dependency, trust boundary, or required permissions.
