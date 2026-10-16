# Security Policy

## Reporting a vulnerability

Please open a [GitHub Security Advisory](https://github.com/dmminga1983/minga-clearmark/security/advisories/new)
(preferred — keeps the report private until a fix ships) or a regular
issue if the advisory flow isn't available to you. Include reproduction
steps and, if relevant, the file format/size that triggers the issue.

## Scope and known limitations

- The HTTP service (`clearmark.server`) has no built-in TLS, rate
  limiting, or request size validation beyond a flat body-size cap. It
  binds to `127.0.0.1` by default; only expose it on a trusted network,
  behind your own reverse proxy/TLS termination, and with
  `CLEARMARK_API_KEY` set.
- Cleaning is best-effort for the metadata channels listed in the README.
  It does not certify that a vendor's own detector will report "no AI
  involvement" — see the README's "what it deliberately doesn't do"
  section.
- Secrets handling: the server reads `CLEARMARK_API_KEY` from the
  environment only, never from a request body or CLI argument, and the
  repository's `.gitignore` excludes `.env`.
