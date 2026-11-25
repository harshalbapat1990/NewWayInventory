# Security deployment

## Required before deployment

1. Rotate the SMTP app credential that was previously committed. Remove it from the provider and issue a new credential. This repository change cannot revoke the old credential or rewrite shared Git history.
2. Generate distinct random `SECRET_KEY` and `JWT_SECRET_KEY` values (at least 32 characters each). Rotating `JWT_SECRET_KEY` invalidates all issued tokens.
3. Run the backend only on loopback. Publish it through a maintained HTTPS reverse proxy. The frontend production build uses the same-origin `/api` path.
4. Configure `APP_ENV=production`, both signing keys, a persistent `SMTP_CREDENTIAL_ENCRYPTION_KEY` (Fernet key), `RATELIMIT_STORAGE_URI=rediss://...` (shared Redis), and `CORS_ORIGINS` as a comma-separated allowlist of HTTPS origins if cross-origin access is necessary. SMTP host, sender, port, and TLS remain environment-managed.
5. Set `INVENTORY_DATA_DIR` to a persistent, access-restricted Windows data directory. The default for the packaged executable is `C:\ProgramData\NewWayInventory`; it is outside the release folder. Keep verified database backups and secrets outside release artifacts.
6. Bootstrap the first admin once with `python -m flask --app run:create_app create-admin` from `backend` (or `flask --app run:create_app create-admin`). Re-run it to reset the specified admin account; do not reuse old seeded passwords.

Production startup fails when signing keys are absent/short, SMTP encryption key is missing, or rate limiting has no shared Redis store. HTTPS is enforced for auth cookies in production. Do not expose port 5000 directly to the LAN. Back up the SQLite database before upgrades and verify the backup with SQLite `PRAGMA integrity_check` before relying on it.

## Development

Set `APP_ENV=development` before starting Flask. Development may use generated process-local signing keys and the in-memory rate-limit store. Existing seeded default credentials are disabled on startup if their known passwords are still present. Create a local admin using the CLI command above.

## Operations

Review SMTP activity and user/account changes after credential rotation. Accountants and admins can replace SMTP usernames/passwords in Administration; proposed credentials are tested before encrypted storage, and the password is never returned by the API. Preserve the Fernet key across restarts and database restores. Run Python dependency scanning (`pip-audit`) and `npm audit` in CI, review and update advisories, then deploy from the committed frontend lockfile. Repository-history cleanup requires coordination because it rewrites shared history.
