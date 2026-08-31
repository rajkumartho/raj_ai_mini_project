
import sqlite3
import os
from datetime import datetime


# ---------------------------------------------------------
# DATABASE PATH
# ---------------------------------------------------------

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DB_PATH = os.path.join(
    BASE_DIR,
    "data",
    "rfp_evaluation.db"
)


# ---------------------------------------------------------
# CONNECTION
# ---------------------------------------------------------

def get_connection():

    return sqlite3.connect(
        DB_PATH
    )


# ---------------------------------------------------------
# ACTIVE CRITERIA
# ---------------------------------------------------------

def get_active_criteria():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            criterion_id,
            name,
            description,
            weight,
            max_score
        FROM evaluation_criteria
        WHERE is_active = 1
        ORDER BY criterion_id
    """)

    rows = cursor.fetchall()

    conn.close()

    criteria = []

    for row in rows:

        criteria.append({

            "criterion_id":
                row[0],

            "name":
                row[1],

            "description":
                row[2],

            "weight":
                row[3],

            "max_score":
                row[4]
        })

    return criteria


# ---------------------------------------------------------
# VALIDATE CRITERIA WEIGHTS
# ---------------------------------------------------------

def validate_criteria_weights():

    criteria = get_active_criteria()

    total_weight = sum(
        c["weight"]
        for c in criteria
    )

    return total_weight


# ---------------------------------------------------------
# CREATE RFP RUN
# ---------------------------------------------------------

def create_rfp_run(
    rfp_run_id
):

    conn = get_connection()
    cursor = conn.cursor()

    created_at = (
        datetime.now()
        .isoformat()
    )

    cursor.execute("""
        INSERT INTO rfp_runs
        (
            rfp_run_id,
            created_at,
            status
        )
        VALUES (?, ?, ?)
    """, (
        rfp_run_id,
        created_at,
        "RUNNING"
    ))

    conn.commit()
    conn.close()


# ---------------------------------------------------------
# SAVE SUPPLIER RESULT
# ---------------------------------------------------------

def save_supplier_result(
    rfp_run_id,
    supplier_name,
    submission_date,
    experience_rating,
    absolute_score,
    ppi,
    final_rank,
    result_json
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO supplier_results
        (
            rfp_run_id,
            supplier_name,
            submission_date,
            experience_rating,
            absolute_score,
            ppi,
            final_rank,
            result_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        rfp_run_id,
        supplier_name,
        submission_date,
        experience_rating,
        absolute_score,
        ppi,
        final_rank,
        result_json
    ))

    conn.commit()
    conn.close()


# ---------------------------------------------------------
# COMPLETE RFP RUN
# ---------------------------------------------------------

def complete_rfp_run(
    rfp_run_id
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE rfp_runs
        SET status = ?
        WHERE rfp_run_id = ?
    """, (
        "COMPLETED",
        rfp_run_id
    ))

    conn.commit()
    conn.close()


# ---------------------------------------------------------
# GET RESULTS FOR A RUN
# ---------------------------------------------------------

def get_run_results(
    rfp_run_id
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            supplier_name,
            submission_date,
            experience_rating,
            absolute_score,
            ppi,
            final_rank,
            result_json
        FROM supplier_results
        WHERE rfp_run_id = ?
        ORDER BY final_rank
    """, (
        rfp_run_id,
    ))

    rows = cursor.fetchall()

    conn.close()

    return rows
