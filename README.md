# Inventory App

## Development setup

- Python 3.9 or higher
- Node.js 18 or higher

For local development, run `setup_dev.bat` once. Then start the backend with `start_backend.bat`; in a second terminal run `npm run dev` from `frontend`. The dev API uses `http://localhost:5000/api`.

Create a local administrator with `flask --app run:create_app create-admin` from the `backend` directory. Public account registration is disabled. The supported LAN deployment is one Windows host behind an HTTPS reverse proxy; Flask listens only on loopback. Production requires strong `SECRET_KEY`, `JWT_SECRET_KEY`, `SMTP_CREDENTIAL_ENCRYPTION_KEY`, HTTPS `CORS_ORIGINS`, and shared Redis rate-limit storage. SQLite lives in persistent `C:\ProgramData\NewWayInventory` (configurable through `INVENTORY_DATA_DIR`), outside release files. First executable launch copies a legacy `inventory.db` beside the executable to that data directory; retain a separate verified backup before upgrading.

Generate the SMTP encryption key with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`. Store it in the server environment/secret store and back it up securely. Accountants and admins can replace SMTP username/password under Administration; the app tests credentials before saving. SMTP server, sender, port, and TLS remain deployment settings.

Back up the live database before upgrades with `python backend/backup_restore.py backup` while `INVENTORY_DATA_DIR` points at the live data folder. Restore into a new empty data directory with `INVENTORY_DATA_DIR=<new-folder> python backend/backup_restore.py restore <backup-file>`; the helper refuses to overwrite an existing database and checks SQLite integrity.

Invoice and challan numbers are reserved when a user opens the creation flow. If a draft is cancelled or abandoned, its number may remain unused; include reserved sequence ranges in routine numbering reconciliation.

Build from `frontend` with `npm ci` and `npm run build`. Run backend checks from `backend` with `python -m pytest tests` after installing `requirements-dev.txt`.
