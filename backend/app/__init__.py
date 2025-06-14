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
                -- Calculate total purchased for ALL size_ids
                SELECT
                    size_id,
                    SUM(quantity) AS total_purchased
                FROM purchase
                GROUP BY size_id -- Group by size_id to get sums for each
            ),
            WasteSummary AS (
                -- Calculate total wasted for ALL size_ids
                SELECT
                    size_id,
                    SUM(quantity_wasted) AS total_wasted
                FROM waste_plate
                GROUP BY size_id -- Group by size_id to get sums for each
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