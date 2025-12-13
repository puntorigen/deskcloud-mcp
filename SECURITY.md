# Security Policy

## Supported Versions

We provide security updates for the latest release line.

| Version | Supported |
| ------- | --------- |
| Latest  | ✅ |
| Older   | ❌ |

## Reporting a Vulnerability

If you discover a security vulnerability, please **do not** open a public GitHub issue.

Instead, please report it via one of the following methods:

- Email: `security@deskcloud.app` (preferred)

Include as much of the following as possible:

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested fix or mitigation

## Disclosure Process

- We will acknowledge receipt within **72 hours**.
- We will assess severity and prioritize a fix.
- We may request additional information to reproduce.
- We will coordinate a release and, when appropriate, a public disclosure.

## Self-Hosting Security Notes

If you self-host DeskCloud MCP:

- **Do not expose VNC ports publicly** (5900+). Prefer a reverse proxy with authentication.
- **Use HTTPS** for any public deployment.
- **Treat your Anthropic API key as a secret** and do not put it in client-side code.
- **Restrict CORS** to trusted origins.
- **Run with least privilege** and keep Docker/host packages updated.
