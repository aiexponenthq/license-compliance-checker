# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of License Compliance Checker seriously. If you believe you have found a security vulnerability, please report it responsibly.

**Please do NOT report security vulnerabilities through public GitHub issues.**

### How to Report

1. Email your findings to **security@lcc.dev**
2. Include a detailed description of the vulnerability
3. Provide steps to reproduce the issue if possible
4. Include the version of LCC you are using

### What to Expect

- **Acknowledgment**: We will acknowledge receipt of your report within 48 hours.
- **Assessment**: We will investigate and validate the vulnerability within 5 business days.
- **Resolution**: We aim to release a fix within 30 days for critical vulnerabilities.
- **Disclosure**: We will coordinate with you on public disclosure timing.

### Scope

The following are in scope for security reports:

- Authentication and authorization bypasses
- Injection vulnerabilities (SQL, command, etc.)
- Sensitive data exposure (secrets, credentials, PII)
- Cryptographic weaknesses
- Dependency vulnerabilities

### Out of Scope

- Denial of service attacks
- Social engineering
- Issues in third-party dependencies (report these upstream)

## Security Best Practices for Deployment

- Always set `LCC_SECRET_KEY` to a cryptographically random value
- Never use default passwords in production
- Use environment variables or a secrets manager for all credentials
- Enable TLS/HTTPS for all API endpoints
- Restrict database and Redis access to internal networks
- Regularly rotate API keys and tokens
