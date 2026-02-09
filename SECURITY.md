# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 1.0.x   | Yes                |
| < 1.0   | No                 |

## Reporting a Vulnerability

If you discover a security vulnerability in llm-integration-starter, please report it responsibly.

### Contact

Email: **chunkytortoise@proton.me**

Include the following in your report:
- Description of the vulnerability
- Steps to reproduce
- Potential impact assessment
- Suggested fix (if any)

### Response Timeline

| Severity | Initial Response | Fix Target |
|----------|-----------------|------------|
| Critical | 48 hours        | 7 days     |
| High     | 48 hours        | 14 days    |
| Medium   | 5 business days  | 30 days    |
| Low      | 5 business days  | 90 days    |

### Process

1. **Acknowledgment** -- You will receive an initial response within 48 hours confirming receipt
2. **Assessment** -- We will evaluate the severity and impact within 5 business days
3. **Fix Development** -- A patch will be developed according to the severity timeline above
4. **Disclosure** -- We will coordinate public disclosure with you after the fix is released

### Scope

The following are in scope:
- API key exposure or leakage vectors
- Prompt injection that bypasses guardrails
- Circuit breaker or rate limiter bypass
- Unauthorized access to provider credentials
- Denial of service through resource exhaustion

The following are out of scope:
- Vulnerabilities in upstream LLM provider APIs
- Social engineering attacks
- Issues requiring physical access

### Recognition

We appreciate security researchers who help keep llm-integration-starter secure. With your permission, we will acknowledge your contribution in the release notes.

## Security Best Practices for Users

- **Never commit API keys** -- Use `.env` files and ensure `.env` is in `.gitignore`
- **Use the guardrails engine** -- Enable content filtering and PII redaction in production
- **Set rate limits** -- Configure per-provider rate limits to prevent cost overruns
- **Pin provider models** -- Avoid using `latest` model aliases in production
