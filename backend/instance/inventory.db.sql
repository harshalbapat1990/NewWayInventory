BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "challan" (
	"id"	INTEGER NOT NULL,
	"challan_code"	VARCHAR(100) NOT NULL,
	"date"	DATE NOT NULL,
	"customer_id"	INTEGER NOT NULL,
	"special_instructions"	TEXT,
	"printed"	BOOLEAN DEFAULT 0,
	UNIQUE("challan_code"),
	PRIMARY KEY("id"),
	FOREIGN KEY("customer_id") REFERENCES "customer"("id")
);
CREATE TABLE IF NOT EXISTS "customer" (
	"id"	INTEGER NOT NULL,
	"company_name"	VARCHAR(100) NOT NULL,
	"contact_person"	VARCHAR(100) NOT NULL,
	"address"	VARCHAR(200) NOT NULL,
	"phone"	VARCHAR(20) NOT NULL,
	"mobile"	VARCHAR(20) NOT NULL,
	"email"	VARCHAR(100) NOT NULL,
	"gstin"	VARCHAR(15),
	"state"	VARCHAR(50) DEFAULT 'Maharashtra',
	"code"	VARCHAR(10) DEFAULT '27',
	UNIQUE("company_name"),
	PRIMARY KEY("id")
);
CREATE TABLE IF NOT EXISTS "customer_rate" (
	"id"	INTEGER NOT NULL,
	"customer_id"	INTEGER NOT NULL,
	"plate_size_id"	INTEGER NOT NULL,
	"plate_rate"	FLOAT NOT NULL,
	"baking_rate"	FLOAT NOT NULL DEFAULT 0.0,
	CONSTRAINT "unique_customer_plate_size" UNIQUE("customer_id","plate_size_id"),
	PRIMARY KEY("id"),
	FOREIGN KEY("customer_id") REFERENCES "customer"("id"),
	FOREIGN KEY("plate_size_id") REFERENCES "plate_size"("id")
);
CREATE TABLE IF NOT EXISTS "invoice" (
	"id"	INTEGER NOT NULL,
	"invoice_number"	VARCHAR(50) NOT NULL,
	"financial_year"	VARCHAR(4) NOT NULL,
	"invoice_sequence"	INTEGER NOT NULL,
	"invoice_date"	DATE NOT NULL,
	"due_date"	DATE NOT NULL,
	"customer_id"	INTEGER NOT NULL,
	"total_amount"	FLOAT NOT NULL,
	"cgst_amount"	FLOAT NOT NULL,
	"sgst_amount"	FLOAT NOT NULL,
	"igst_amount"	FLOAT NOT NULL,
	"grand_total"	FLOAT NOT NULL,
	"challan_references"	VARCHAR(200),
	"status"	VARCHAR(20),
	"payment_date"	DATE,
	"created_at"	DATETIME,
	PRIMARY KEY("id"),
	UNIQUE("invoice_number"),
	FOREIGN KEY("customer_id") REFERENCES "customer"("id")
);
CREATE TABLE IF NOT EXISTS "invoice_item" (
	"id"	INTEGER NOT NULL,
	"invoice_id"	INTEGER NOT NULL,
	"plate_size_id"	INTEGER NOT NULL,
	"description"	VARCHAR(200) NOT NULL,
	"colours"	VARCHAR(50) NOT NULL,
	"quantity"	INTEGER NOT NULL,
	"rate"	FLOAT NOT NULL,
	"amount"	FLOAT NOT NULL,
	"job_ids"	VARCHAR(500),
	PRIMARY KEY("id"),
	FOREIGN KEY("invoice_id") REFERENCES "invoice"("id"),
	FOREIGN KEY("plate_size_id") REFERENCES "plate_size"("id")
);
CREATE TABLE IF NOT EXISTS "item" (
	"id"	INTEGER NOT NULL,
	"name"	VARCHAR(100) NOT NULL,
	"quantity"	INTEGER NOT NULL,
	"price"	FLOAT NOT NULL,
	PRIMARY KEY("id")
);
CREATE TABLE IF NOT EXISTS "job" (
	"id"	INTEGER NOT NULL,
	"job_name"	VARCHAR(100) NOT NULL,
	"challan_id"	INTEGER NOT NULL,
	"plate_size_id"	INTEGER NOT NULL,
	"colour"	INTEGER NOT NULL,
	"job_id"	VARCHAR(100) NOT NULL,
	"quantity"	INTEGER NOT NULL,
	"plates"	INTEGER NOT NULL,
	"remark"	VARCHAR(200),
	PRIMARY KEY("id"),
	FOREIGN KEY("challan_id") REFERENCES "challan"("id"),
	FOREIGN KEY("plate_size_id") REFERENCES "plate_size"("id")
);
CREATE TABLE IF NOT EXISTS "plate" (
	"id"	INTEGER NOT NULL,
	"name"	VARCHAR(100) NOT NULL,
	"quantity"	INTEGER NOT NULL,
	PRIMARY KEY("id")
);
CREATE TABLE IF NOT EXISTS "plate_size" (
	"id"	INTEGER NOT NULL,
	"length"	FLOAT NOT NULL,
	"width"	FLOAT NOT NULL,
	"min_quantity"	INTEGER,
	"is_dl"	BOOLEAN NOT NULL DEFAULT 0,
	PRIMARY KEY("id")
);
CREATE TABLE IF NOT EXISTS "purchase" (
	"id"	INTEGER NOT NULL,
	"date"	DATE NOT NULL,
	"size_id"	INTEGER NOT NULL,
	"quantity"	INTEGER NOT NULL,
	PRIMARY KEY("id"),
	FOREIGN KEY("size_id") REFERENCES "plate_size"("id")
);
CREATE TABLE IF NOT EXISTS "used_plate" (
	"id"	INTEGER NOT NULL,
	"plate_id"	INTEGER NOT NULL,
	"quantity"	INTEGER NOT NULL,
	PRIMARY KEY("id"),
	FOREIGN KEY("plate_id") REFERENCES "plate"("id")
);
CREATE TABLE IF NOT EXISTS "user" (
	"id"	INTEGER NOT NULL,
	"username"	VARCHAR(80) NOT NULL,
	"password"	VARCHAR(120) NOT NULL,
	"first_name"	VARCHAR(50) NOT NULL,
	"last_name"	VARCHAR(50) NOT NULL,
	"role"	VARCHAR(10) NOT NULL,
	PRIMARY KEY("id"),
	UNIQUE("username")
);
CREATE TABLE IF NOT EXISTS "waste_plate" (
	"id"	INTEGER NOT NULL,
	"size_id"	INTEGER NOT NULL,
	"quantity_wasted"	INTEGER NOT NULL,
	"waste_date"	DATE NOT NULL,
	PRIMARY KEY("id"),
	FOREIGN KEY("size_id") REFERENCES "plate_size"("id")
);
CREATE VIEW customer_summary_view AS
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
                JobSummary j ON ps.id = j.plate_size_id;
CREATE VIEW stock_summary_view AS
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
COMMIT;
