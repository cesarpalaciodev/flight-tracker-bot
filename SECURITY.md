# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 3.x     | :white_check_mark: |
| < 3.0   | :x:                |

## Reporting a Vulnerability

We take the security of this project seriously. If you discover a security vulnerability, please follow these steps:

### 1. Do NOT open a public issue

Please report vulnerabilities **privately** so they can be addressed before disclosure.

### 2. Contact

Send an email to the maintainer at the address listed in the project metadata, or open a **private advisory** on GitHub:

> https://github.com/cesarpalaciodev/flight-tracker-bot/security/advisories/new

### 3. Response timeline

- **Within 48 hours**: Acknowledgment of receipt
- **Within 7 days**: Initial assessment and severity classification
- **Within 30 days**: Fix released or detailed remediation plan

### 4. What to include

- Description of the vulnerability
- Steps to reproduce (PoC preferred)
- Affected versions
- Potential impact
- Suggested fix (optional)

### 5. Scope

The following are **in scope**:
- Authentication bypass (JWT, Telegram, Stripe webhooks)
- Data leakage between users (data isolation bypass)
- Remote code execution
- SQL / NoSQL injection
- Insecure direct object references

The following are **out of scope**:
- Rate limiting bypass (known limitation)
- Missing security headers on dashboard (low priority)
- Dependency vulnerabilities already tracked by Dependabot

## Responsible Disclosure

We believe in responsible disclosure. We will:

1. Acknowledge receipt within 48 hours
2. Investigate and classify the issue
3. Develop and test a fix
4. Release the fix and credit the reporter (with permission)

## Security Measures in Place

- **JWT authentication** for dashboard access
- **Data isolation**: all database queries scoped by `chat_id`
- **Rate limiting**: per-user request limits
- **Log sanitization**: API keys, tokens and passwords redacted from logs
- **CI/CD security scanning**: GitLeaks, Bandit, Trivy, Safety, Dependabot, CodeQL
- **Signed webhooks**: Stripe and Nequi signatures verified
- **Environment isolation**: `.env` excluded from version control