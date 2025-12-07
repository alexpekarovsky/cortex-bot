# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

The Palo Alto Networks Product Security Incident Response Team (PSIRT) is responsible for receiving, investigating, and responding to security vulnerability reports related to Palo Alto Networks products and services.

### How to Report

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please report security vulnerabilities through one of the following channels:

1. **Email**: Send vulnerability reports to [security@paloaltonetworks.com](mailto:security@paloaltonetworks.com)

2. **Palo Alto Networks Security Portal**: Submit reports through our official security portal at [https://security.paloaltonetworks.com](https://security.paloaltonetworks.com)

### What to Include

When reporting a vulnerability, please include:

- **Description**: A clear description of the vulnerability
- **Impact**: The potential security impact
- **Steps to Reproduce**: Detailed steps to reproduce the issue
- **Affected Versions**: Which versions are affected
- **Suggested Fix**: If you have a potential fix, please share it
- **Your Contact Information**: So we can follow up with you

### What to Expect

1. **Acknowledgment**: We will acknowledge receipt of your report within 3 business days

2. **Initial Assessment**: We will provide an initial assessment within 10 business days

3. **Regular Updates**: We will keep you informed of our progress

4. **Resolution**: Once resolved, we will notify you and coordinate disclosure

### Safe Harbor

We consider security research conducted in accordance with this policy to be:

- Authorized concerning any applicable anti-hacking laws
- Authorized concerning any relevant anti-circumvention laws
- Exempt from restrictions in our Terms of Service that would interfere with conducting security research

We will not pursue civil or criminal action against researchers who:

- Act in good faith
- Avoid privacy violations and data destruction
- Do not exploit vulnerabilities beyond proof of concept
- Report findings promptly

## Security Best Practices

When using this MCP server:

### API Credentials

- **Never commit credentials**: Do not commit `.env` files or API keys to version control
- **Use environment variables**: Always use environment variables for sensitive data
- **Rotate keys regularly**: Regularly rotate your Cortex XSIAM API keys
- **Minimum privileges**: Use API keys with only the required permissions

### Network Security

- **Use HTTPS**: Always use HTTPS for API communications
- **Firewall rules**: Restrict network access to the MCP server
- **VPN/Private networks**: Consider running within a VPN or private network

### Container Security

- **Non-root user**: The Docker container runs as a non-root user by default
- **Read-only filesystem**: Consider mounting volumes as read-only where possible
- **Resource limits**: Set appropriate CPU and memory limits

### Logging

- **Sensitive data**: The server may log API responses; ensure logs are protected
- **Log rotation**: Implement log rotation to prevent disk exhaustion
- **Audit trails**: Maintain audit trails for compliance requirements

## Vulnerability Disclosure Timeline

We follow a coordinated disclosure process:

1. **Day 0**: Vulnerability reported
2. **Day 1-3**: Acknowledgment sent
3. **Day 4-10**: Initial assessment completed
4. **Day 11-60**: Fix developed and tested
5. **Day 61-90**: Fix released, CVE assigned if applicable
6. **Day 90+**: Public disclosure (coordinated with reporter)

We aim to resolve critical vulnerabilities within 30 days and high-severity vulnerabilities within 60 days.

## Contact

For security concerns, contact:

- **Security Team**: [security@paloaltonetworks.com](mailto:security@paloaltonetworks.com)
- **PSIRT**: [https://security.paloaltonetworks.com](https://security.paloaltonetworks.com)

For general questions (non-security), please use:

- GitHub Issues: [https://github.com/PaloAltoNetworks/cortex-mcp/issues](https://github.com/PaloAltoNetworks/cortex-mcp/issues)
