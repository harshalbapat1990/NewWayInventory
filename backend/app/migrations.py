"""Versioned SQLite schema migrations and stable reporting views."""
from sqlalchemy import text

from . import db

def create_views():
    """Keep report views stable and repair obsolete definitions only once."""
    view_queries = {
        'stock_summary_view': """
            CREATE VIEW stock_summary_view AS
            WITH purchases AS (SELECT size_id, SUM(quantity) AS total FROM purchase GROUP BY size_id),
                 waste AS (SELECT size_id, SUM(quantity_wasted) AS total FROM waste_plate GROUP BY size_id),
                 used AS (SELECT plate_size_id, SUM(quantity * colour) AS total FROM job GROUP BY plate_size_id)
            SELECT ps.id AS size_id, ps.length || 'x' || ps.width AS product_name,
                   COALESCE(p.total, 0) AS total_purchased, COALESCE(u.total, 0) AS total_used,
                   COALESCE(w.total, 0) AS total_wasted,
                   COALESCE(p.total, 0) - COALESCE(w.total, 0) - COALESCE(u.total, 0) AS current_stock
            FROM plate_size ps LEFT JOIN purchases p ON p.size_id = ps.id
            LEFT JOIN waste w ON w.size_id = ps.id LEFT JOIN used u ON u.plate_size_id = ps.id
        """,
        'customer_summary_view': """
            CREATE VIEW customer_summary_view AS
            SELECT c.company_name AS customer_name, COUNT(j.id) AS total_jobs,
                   COALESCE(SUM(j.quantity), 0) AS total_plates
            FROM customer c LEFT JOIN challan ch ON ch.customer_id = c.id
            LEFT JOIN job j ON j.challan_id = ch.id GROUP BY c.id
        """,
        'plate_summary_view': """
            CREATE VIEW plate_summary_view AS
            WITH purchases AS (SELECT size_id, SUM(quantity) AS total FROM purchase GROUP BY size_id),
                 waste AS (SELECT size_id, SUM(quantity_wasted) AS total FROM waste_plate GROUP BY size_id),
                 used AS (SELECT plate_size_id, SUM(quantity * colour) AS total FROM job GROUP BY plate_size_id)
            SELECT ps.id AS size_id, ps.length, ps.width, ps.min_quantity, ps.is_dl, ps.prefix, ps.suffix,
                   COALESCE(p.total, 0) - COALESCE(w.total, 0) - COALESCE(u.total, 0) AS available_quantity
            FROM plate_size ps LEFT JOIN purchases p ON p.size_id = ps.id
            LEFT JOIN waste w ON w.size_id = ps.id LEFT JOIN used u ON u.plate_size_id = ps.id
        """
    }
    connection = db.engine.connect()
    try:
        existing = {row[0]: row[1] for row in connection.execute(text("SELECT name, sql FROM sqlite_master WHERE type='view'"))}
        # Validate the actual join definitions so an older view with a stale
        # column relationship is repaired once and then left alone.
        expected_markers = {
            'stock_summary_view': 'p.size_id = ps.id',
            'customer_summary_view': 'ch.customer_id = c.id',
            'plate_summary_view': 'u.plate_size_id = ps.id',
        }
        for name, definition in view_queries.items():
            if name in existing and expected_markers[name] in (existing[name] or ''):
                continue
            if name in existing:
                connection.execute(text(f'DROP VIEW "{name}"'))
                connection.commit()
            connection.execute(text(definition))
            connection.commit()
    finally:
        connection.close()


def run_migrations(db):
    """Apply numbered, data-preserving schema migrations once per database."""
    from sqlalchemy import inspect

    with db.engine.begin() as connection:
        connection.execute(text('CREATE TABLE IF NOT EXISTS schema_migration (version VARCHAR(80) PRIMARY KEY, applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP)'))
    # Only a brand-new empty database uses model metadata for initial creation.
    # Existing databases are changed by the numbered steps below.
    if not inspect(db.engine).has_table('user'):
        db.create_all()
    if not _migration_applied(db, '0001_legacy_schema'):
        _apply_legacy_migration(db)
        _record_migration(db, '0001_legacy_schema')
    if not _migration_applied(db, '0002_invoice_item_challans'):
        from .models import invoice_item_challan
        invoice_item_challan.create(bind=db.engine, checkfirst=True)
        _backfill_invoice_item_challans(db)
        _record_migration(db, '0002_invoice_item_challans')
    if not _migration_applied(db, '0003_document_sequences'):
        from .models import DocumentSequence
        DocumentSequence.__table__.create(bind=db.engine, checkfirst=True)
        _record_migration(db, '0003_document_sequences')
    if not _migration_applied(db, '0004_money_minor_units'):
        _apply_money_migration(db)
        _record_migration(db, '0004_money_minor_units')
    if not _migration_applied(db, '0005_audit_log'):
        from .models import AuditLog
        AuditLog.__table__.create(bind=db.engine, checkfirst=True)
        _record_migration(db, '0005_audit_log')
    if not _migration_applied(db, '0006_auxiliary_tables'):
        from .models import AppSetting, RevokedToken, invoice_item_challan
        for table in (AppSetting.__table__, RevokedToken.__table__, invoice_item_challan):
            table.create(bind=db.engine, checkfirst=True)
        _record_migration(db, '0006_auxiliary_tables')


def _apply_money_migration(db):
    """Add exact minor-unit columns and backfill legacy floating point values."""
    from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
    from sqlalchemy import inspect, text as sa_text

    fields = {
        'customer_rate': ('plate_rate', 'baking_rate'),
        'invoice': ('total_amount', 'cgst_amount', 'sgst_amount', 'igst_amount', 'grand_total'),
        'invoice_item': ('rate', 'amount'),
    }
    inspector = inspect(db.engine)
    with db.engine.begin() as connection:
        for table, columns in fields.items():
            if table not in inspector.get_table_names():
                continue
            existing = {column['name'] for column in inspector.get_columns(table)}
            for column in columns:
                cents_column = f'{column}_cents'
                if cents_column not in existing:
                    connection.execute(sa_text(
                        f'ALTER TABLE "{table}" ADD COLUMN "{cents_column}" INTEGER'
                    ))
            selected_columns = ', '.join('"' + column + '"' for column in columns)
            for row in connection.execute(sa_text(
                f'SELECT id, {selected_columns} FROM "{table}"'
            )).mappings():
                updates = {}
                for column in columns:
                    try:
                        amount = Decimal(str(row[column] or 0)).quantize(
                            Decimal('0.01'), rounding=ROUND_HALF_UP
                        )
                        cents = int(amount * 100)
                    except (InvalidOperation, TypeError, ValueError):
                        cents = 0
                    updates[f'{column}_cents'] = cents
                    # Normalize the compatibility column to the same cent value.
                    updates[column] = cents / 100
                assignments = ', '.join(f'"{name}" = :{name}' for name in updates)
                connection.execute(sa_text(
                    f'UPDATE "{table}" SET {assignments} WHERE id = :id'
                ), {'id': row['id'], **updates})


def _migration_applied(db, version):
    with db.engine.connect() as connection:
        return connection.execute(text('SELECT 1 FROM schema_migration WHERE version = :version'), {'version': version}).first() is not None


def _record_migration(db, version):
    with db.engine.begin() as connection:
        connection.execute(text('INSERT OR IGNORE INTO schema_migration (version) VALUES (:version)'), {'version': version})


def _backfill_invoice_item_challans(database=None):
    """Link legacy challan sequence references when they resolve uniquely."""
    database = database or db
    from .models import Challan, InvoiceItem

    for item in InvoiceItem.query.all():
        if item.challans or not item.job_ids or not item.invoice:
            continue
        if not item.invoice.summary_start_date or not item.invoice.summary_end_date:
            continue
        sequences = set()
        for token in item.job_ids.split(','):
            try:
                sequences.add(int(token.strip()))
            except (TypeError, ValueError):
                continue
        for sequence in sequences:
            matches = Challan.query.filter_by(
                customer_id=item.invoice.customer_id,
                challan_sequence=sequence
            ).filter(Challan.date.between(item.invoice.summary_start_date, item.invoice.summary_end_date)).all()
            if len(matches) == 1:
                item.challans.append(matches[0])
    database.session.commit()


def _apply_legacy_migration(db):
    """Add new columns to existing tables if they don't already exist, then backfill data."""
    from sqlalchemy import inspect, text as sa_text
    inspector = inspect(db.engine)

    def column_exists(table, col):
        return any(c['name'] == col for c in inspector.get_columns(table))

    migrations = []

    if 'is_active' not in {c['name'] for c in inspector.get_columns('user')}:
        migrations.append('ALTER TABLE "user" ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT 1')
    if 'auth_version' not in {c['name'] for c in inspector.get_columns('user')}:
        migrations.append('ALTER TABLE "user" ADD COLUMN auth_version INTEGER NOT NULL DEFAULT 0')

    # challan table
    if not column_exists('challan', 'financial_year'):
        migrations.append("ALTER TABLE challan ADD COLUMN financial_year VARCHAR(4)")
    if not column_exists('challan', 'challan_sequence'):
        migrations.append("ALTER TABLE challan ADD COLUMN challan_sequence INTEGER")
    if not column_exists('challan', 'is_archived'):
        migrations.append("ALTER TABLE challan ADD COLUMN is_archived BOOLEAN NOT NULL DEFAULT 0")

    # customer table
    if not column_exists('customer', 'is_archived'):
        migrations.append("ALTER TABLE customer ADD COLUMN is_archived BOOLEAN NOT NULL DEFAULT 0")

    # invoice table
    if not column_exists('invoice', 'is_archived'):
        migrations.append("ALTER TABLE invoice ADD COLUMN is_archived BOOLEAN NOT NULL DEFAULT 0")

    # purchase table
    if not column_exists('purchase', 'is_archived'):
        migrations.append("ALTER TABLE purchase ADD COLUMN is_archived BOOLEAN NOT NULL DEFAULT 0")

    # waste_plate table
    if not column_exists('waste_plate', 'is_archived'):
        migrations.append("ALTER TABLE waste_plate ADD COLUMN is_archived BOOLEAN NOT NULL DEFAULT 0")

    for sql in migrations:
        db.session.execute(sa_text(sql))
    if migrations:
        db.session.commit()

    # Backfill challans that have no financial_year yet
    # Derive FY from challan date and sequence from the old "DC-<number>" code
    rows = db.session.execute(sa_text(
        "SELECT id, challan_code, date FROM challan WHERE financial_year IS NULL"
    )).fetchall()

    if rows:
        for row in rows:
            challan_id, code, date_str = row[0], row[1], row[2]
            # Parse date
            try:
                if isinstance(date_str, str):
                    from datetime import date as date_type
                    d = date_type.fromisoformat(date_str[:10])
                else:
                    d = date_str
                fy_start = d.year if d.month >= 4 else d.year - 1
                fy = f"{str(fy_start)[-2:]}{str(fy_start + 1)[-2:]}"
            except Exception:
                fy = "2526"

            # Parse sequence from "DC-<num>" or pure numeric
            try:
                if '-' in code:
                    seq = int(code.split('-')[-1])
                else:
                    seq = int(code)
            except (ValueError, IndexError):
                seq = 0

            # Rewrite challan_code to new format "<FY>/DC/<seq>"
            new_code = f"{fy}/DC/{seq}"
            # Handle duplicate new_code by appending id if needed
            existing = db.session.execute(
                sa_text("SELECT id FROM challan WHERE challan_code = :code AND id != :cid"),
                {"code": new_code, "cid": challan_id}
            ).fetchone()
            if existing:
                new_code = f"{fy}/DC/{seq}-{challan_id}"

            db.session.execute(
                sa_text("UPDATE challan SET financial_year=:fy, challan_sequence=:seq, challan_code=:code WHERE id=:cid"),
                {"fy": fy, "seq": seq, "code": new_code, "cid": challan_id}
            )
        db.session.commit()

    # Renumber challan sequences per FY so each FY starts from 1 (sorted by date, then id).
    # This fixes cases where old global DC-numbers were carried over as sequences during backfill.
    # Idempotent: skips any FY whose MIN(challan_sequence) is already 1.
    fy_mins = db.session.execute(sa_text(
        "SELECT financial_year, MIN(challan_sequence) FROM challan "
        "WHERE financial_year IS NOT NULL GROUP BY financial_year"
    )).fetchall()

    needs_renumber = [fy for fy, min_seq in fy_mins if min_seq is None or min_seq != 1]

    for fy in needs_renumber:
        challans = db.session.execute(sa_text(
            "SELECT id FROM challan WHERE financial_year = :fy ORDER BY date ASC, id ASC"
        ), {"fy": fy}).fetchall()

        for new_seq, (challan_id,) in enumerate(challans, start=1):
            new_code = f"{fy}/DC/{new_seq}"
            db.session.execute(sa_text(
                "UPDATE challan SET challan_sequence=:seq, challan_code=:code WHERE id=:cid"
            ), {"seq": new_seq, "code": new_code, "cid": challan_id})

    if needs_renumber:
        db.session.commit()
