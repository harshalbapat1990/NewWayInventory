# filepath: backend/app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_migrate import Migrate
from flask_mail import Mail
from sqlalchemy import text
from .config import Config  # Import the Config class

db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()
mail = Mail()


def create_app():
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(Config)

    # Disable SMTP debug output
    import logging
    logging.getLogger('mail.log').setLevel(logging.ERROR)

    # Initialize mail with SSL instead of TLS
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 465
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USE_SSL'] = True
    app.config['MAIL_USERNAME'] = 'newwayaccounts@gmail.com'
    app.config['MAIL_PASSWORD'] = 'gbrwmcfqnwequheu'
    app.config['MAIL_DEFAULT_SENDER'] = 'New Way Typesetters <newwayaccounts@gmail.com>'
    # app.config['MAIL_USERNAME'] = 'harshalbapat1990@gmail.com'
    # app.config['MAIL_PASSWORD'] = 'uiojnavqzeabtyyw'
    # app.config['MAIL_DEFAULT_SENDER'] = 'New Way Typesetters <harshalbapat1990@gmail.com>'
    app.config['MAIL_DEBUG'] = False  # Changed from True to False
    app.config['MAIL_SUPPRESS_SEND'] = False

    mail.init_app(app)

    db.init_app(app)
    jwt.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": app.config['CORS_ORIGINS']}})
    migrate.init_app(app, db)

    with app.app_context():
        from . import routes
        routes.register_routes(app)
        from .models import User, Item, Customer, PlateSize, WastePlate, Job, Plate, UsedPlate
        db.create_all()
        run_migrations(db)
        User.create_default_users()
        create_views()

    return app


def create_views():
    view_queries = [
        text("""
            DROP VIEW IF EXISTS "main"."stock_summary_view";
        """),
        text("""
        CREATE VIEW IF NOT EXISTS stock_summary_view AS
        SELECT
            p.name AS product_name,
            SUM(p.quantity) AS total_purchased,
            SUM(u.quantity) AS total_used,
            SUM(w.quantity_wasted) AS total_wasted,
            (SUM(p.quantity) - SUM(u.quantity) - SUM(w.quantity_wasted)) AS current_stock
        FROM
            plate p
        LEFT JOIN
            used_plate u ON p.id = u.plate_id
        LEFT JOIN
            waste_plate w ON p.id = w.plate_id
        GROUP BY
            p.name;
        """),
        text("""
            DROP VIEW IF EXISTS "main"."customer_summary_view";
        """),
        text("""
        CREATE VIEW IF NOT EXISTS customer_summary_view AS
        SELECT
            c.company_name AS customer_name,
            COUNT(j.id) AS total_jobs,
            SUM(j.quantity) AS total_plates
        FROM
            customer c
        LEFT JOIN
            job j ON c.id = j.customer_id
        GROUP BY
            c.company_name;
        """),
        text("""
            DROP VIEW IF EXISTS "main"."plate_summary_view";
        """),
        text("""
            CREATE VIEW plate_summary_view AS
            WITH PurchaseSummary AS (
                -- Calculate total purchased for ALL size_ids (all FYs, stock is perpetual/cumulative)
                SELECT
                    size_id,
                    SUM(quantity) AS total_purchased
                FROM purchase
                GROUP BY size_id
            ),
            WasteSummary AS (
                -- Calculate total wasted for ALL size_ids (all FYs, stock is perpetual/cumulative)
                SELECT
                    size_id,
                    SUM(quantity_wasted) AS total_wasted
                FROM waste_plate
                GROUP BY size_id
            ),
            JobSummary AS (
                -- Calculate total used in jobs for ALL plate_size_ids
                SELECT
                    plate_size_id,
                    SUM(quantity * colour) AS total_used -- Ensure this calculation logic is correct
                FROM job
                GROUP BY plate_size_id -- Group by plate_size_id to get sums for each
            )
            -- The SELECT statement that defines the view's structure and data
            SELECT
                ps.id AS size_id,
                ps.length,
                ps.width,
                ps.min_quantity,
                ps.is_dl,
                ps.prefix,
                ps.suffix,
                (COALESCE(p.total_purchased, 0)  -- Get total purchased from PurchaseSummary CTE
                - COALESCE(wp.total_wasted, 0)   -- Get total wasted from WasteSummary CTE
                - COALESCE(j.total_used, 0)      -- Get total used from JobSummary CTE
                ) AS available_quantity
            FROM
                plate_size ps -- Start with all plate sizes from the base table
            LEFT JOIN
                PurchaseSummary p ON ps.id = p.size_id -- Join with aggregated purchase totals
            LEFT JOIN
                WasteSummary wp ON ps.id = wp.size_id -- Join with aggregated waste totals
            LEFT JOIN
                JobSummary j ON ps.id = j.plate_size_id; -- Join with aggregated job totals
            -- Note: ORDER BY is removed from the view definition.
            -- Apply ORDER BY when querying the view, e.g., SELECT * FROM plate_summary_view ORDER BY size_id;
        """)
    ]

    for query in view_queries:
        db.session.execute(query)
    db.session.commit()


def run_migrations(db):
    """Add new columns to existing tables if they don't already exist, then backfill data."""
    from sqlalchemy import inspect, text as sa_text
    inspector = inspect(db.engine)

    def column_exists(table, col):
        return any(c['name'] == col for c in inspector.get_columns(table))

    migrations = []

    # challan table
    if not column_exists('challan', 'financial_year'):
        migrations.append("ALTER TABLE challan ADD COLUMN financial_year VARCHAR(4)")
    if not column_exists('challan', 'challan_sequence'):
        migrations.append("ALTER TABLE challan ADD COLUMN challan_sequence INTEGER")
    if not column_exists('challan', 'is_archived'):
        migrations.append("ALTER TABLE challan ADD COLUMN is_archived BOOLEAN NOT NULL DEFAULT 0")

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
