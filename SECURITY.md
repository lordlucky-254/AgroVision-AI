# Security policy

## Supported use

This repository is a local/private prototype. It is not configured for multi-user public hosting. Do not expose it directly to the internet: authentication, request rate limiting, and per-user authorization are not implemented.

## Data handling

- The application does not persist uploaded photographs or filenames. The multipart framework may temporarily spool larger uploads to the host's temporary directory and removes them after request handling.
- The browser stores up to 20 scan summaries in local storage. Use **Clear history** on shared devices.
- Do not upload images containing people, private property details, or other sensitive information.
- Keep model checkpoints and datasets outside Git unless their provenance and license have been reviewed.

## Reporting

Do not include farm photos or personal data in a public issue. Report security issues privately to the repository owner.
