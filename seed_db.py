
import sqlite3
import os


# ---------------------------------------------------------
# DATABASE PATH
# ---------------------------------------------------------

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DATA_DIR = os.path.join(
    BASE_DIR,
    "data"
)

DB_PATH = os.path.join(
    DATA_DIR,
    "rfp_evaluation.db"
)


# ---------------------------------------------------------
# CREATE DATA DIRECTORY
# ---------------------------------------------------------

os.makedirs(
    DATA_DIR,
    exist_ok=True
)


# ---------------------------------------------------------
# CREATE DATABASE
# ---------------------------------------------------------

conn = sqlite3.connect(DB_PATH)

cursor = conn.cursor()


# ---------------------------------------------------------
# CREATE TABLES
# ---------------------------------------------------------

cursor.execute("""
CREATE TABLE IF NOT EXISTS evaluation_criteria (
    criterion_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    weight REAL NOT NULL,
    max_score REAL NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1
)
""")


cursor.execute("""
CREATE TABLE IF NOT EXISTS rfp_runs (
    rfp_run_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    status TEXT NOT NULL
)
""")


cursor.execute("""
CREATE TABLE IF NOT EXISTS supplier_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rfp_run_id TEXT NOT NULL,
    supplier_name TEXT NOT NULL,
    submission_date TEXT NOT NULL,
    experience_rating REAL NOT NULL,
    absolute_score REAL,
    ppi REAL,
    final_rank INTEGER,
    result_json TEXT,
    FOREIGN KEY (rfp_run_id)
        REFERENCES rfp_runs(rfp_run_id)
)
""")


# ---------------------------------------------------------
# EVALUATION CRITERIA
# ---------------------------------------------------------

criteria = [

    (
        1,
        "Technical Capability",
        "Architecture, integrations, scalability, reliability, and technical approach.",
        30.0,
        10.0,
        1
    ),

    (
        2,
        "Implementation Plan",
        "Implementation timeline, milestones, delivery approach, team structure, and risk management.",
        20.0,
        10.0,
        1
    ),

    (
        3,
        "Commercial Value",
        "Pricing, cost transparency, commercial assumptions, and overall value for money.",
        20.0,
        10.0,
        1
    ),

    (
        4,
        "Security & Compliance",
        "Security controls, compliance, testing, data protection, and relevant certifications.",
        20.0,
        10.0,
        1
    ),

    (
        5,
        "Support & Experience",
        "Support model, service levels, relevant experience, references, and customer support.",
        10.0,
        10.0,
        1
    )
]


# ---------------------------------------------------------
# INSERT / REPLACE CRITERIA
# ---------------------------------------------------------

cursor.executemany("""
INSERT OR REPLACE INTO evaluation_criteria
(
    criterion_id,
    name,
    description,
    weight,
    max_score,
    is_active
)
VALUES (?, ?, ?, ?, ?, ?)
""", criteria)


# ---------------------------------------------------------
# VALIDATE WEIGHTS
# ---------------------------------------------------------

cursor.execute("""
SELECT SUM(weight)
FROM evaluation_criteria
WHERE is_active = 1
""")

total_weight = cursor.fetchone()[0]


if total_weight != 100.0:

    conn.rollback()
    conn.close()

    raise ValueError(
        f"Active criterion weights must total 100%. "
        f"Current total: {total_weight}%"
    )


# ---------------------------------------------------------
# COMMIT
# ---------------------------------------------------------

conn.commit()

conn.close()


print("✅ Database created successfully.")
print(f"Database: {DB_PATH}")
print(f"Active criteria: {len(criteria)}")
print(f"Total weight: {total_weight}%")
