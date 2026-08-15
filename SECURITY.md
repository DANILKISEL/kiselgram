# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| Current | :white_check_mark: |

## Reporting a Vulnerability

Kiselgram takes security seriously. If you discover a security vulnerability, please report it privately instead of opening a public issue.

**How to report:**

- Use **GitHub Security Advisories**: open a private advisory in the repository at
  `Security > Advisories > New draft security advisory`, or
- Open an issue through the GitHub **private vulnerability reporting** flow on the repo homepage.

Please include in the report:

- Affected component and screen/endpoint (if applicable)
- Steps to reproduce
- Impact and potential exploitation scenario
- Version or commit where you observed it

You should receive a response within **72 hours**. We ask you to keep the report confidential until a fix has been released.

## Security Model

- **Authentication** — Bearer tokens (`UserSession.session_token`) with Flask-signed HTTP-only session cookies for the SPA; email + password (hashed), email OTP, QR login and Google OAuth.
- **Message privacy** — message content is encrypted at rest via Fernet (AES-256-GCM) with `MESSAGE_ENCRYPTION_KEY`; ciphertext in the DB is decrypted in memory only when served.
- **Hardening** — security headers (CSP, `X-Frame-Options`, `nosniff`, Referrer-Policy), CSRF protection, rate limiting on auth endpoints, upload size limits and filename sanitization.
- **Access control** — message history is returned only to chat members/subscribers; delete-for-everyone requires membership; the admin panel has its own login and is the most sensitive surface.

> **Important**: encryption at rest protects database files and backups. It does **not** provide end-to-end encryption between users — the server can decrypt messages. Always terminate TLS in production.

## Security Best Practices for Operators

1. Set unique, random `SECRET_KEY` and `MESSAGE_ENCRYPTION_KEY` via a secret manager.
2. Set `DATABASE_URL`; force production mode (`DEBUG=False`, secure cookies, TLS enforcement).
3. Terminate TLS at the reverse proxy; never serve plaintext in production.
4. Do not expose the video/mail services publicly — bind them to internal networks.
5. Protect backups at rest with disk encryption.
6. Pin and regularly update dependencies; run `pip-audit`.
7. Run the app as a non-root user.

See full documentation at `docs.kiselgram.ru/security/`.