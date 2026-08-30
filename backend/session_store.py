import json
import os
import sqlite3
from datetime import datetime, timezone


DATABASE = os.getenv(
    "DATABASE_PATH",
    os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "data",
        "APS-01.db"
    )
)


# ==========================================================
# DATABASE CONNECTION
# ==========================================================

def get_connection():
    connection = sqlite3.connect(
        DATABASE,
        timeout=10
    )

    connection.row_factory = sqlite3.Row

    # Allow reads while another connection is writing.
    connection.execute("PRAGMA journal_mode=WAL;")

    # Wait briefly instead of failing immediately when locked.
    connection.execute("PRAGMA busy_timeout=10000;")

    return connection


# ==========================================================
# SAVE NEW AGENT SESSION
# ==========================================================

def save_agent_session(
    session_id: str,
    goal_text: str,
    constraints: dict,
    plan_steps: list,
    current_step: int,
    spend_cap: float,
    spend_committed: float,
    currency: str,
    requires_confirmation: bool,
    status: str,
    user_id: str = "usr_demo",
    trip_id: str | None = None,
    confirmed_at: str | None = None,
    replan_count: int = 0,
    last_error_code: str | None = None,
    goal_language: str = "en-IN"
):
    now = datetime.now(timezone.utc).isoformat()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO agent_sessions (
            session_id,
            user_id,
            trip_id,
            goal_text,
            goal_language,
            constraints_json,
            plan_steps_json,
            current_step,
            spend_cap,
            spend_committed,
            currency,
            requires_confirmation,
            confirmed_at,
            replan_count,
            last_error_code,
            status,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            session_id,
            user_id,
            trip_id,
            goal_text,
            goal_language,
            json.dumps(constraints),
            json.dumps(plan_steps),
            current_step,
            spend_cap,
            spend_committed,
            currency,
            int(requires_confirmation),
            confirmed_at,
            replan_count,
            last_error_code,
            status,
            now,
            now
        )
    )

    connection.commit()
    connection.close()


# ==========================================================
# LOAD AGENT SESSION
# ==========================================================

def load_agent_session(session_id: str):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM agent_sessions
        WHERE session_id = ?
        """,
        (session_id,)
    )

    row = cursor.fetchone()

    connection.close()

    if row is None:
        return None

    session = dict(row)

    # ------------------------------------------------------
    # Decode JSON fields
    # ------------------------------------------------------

    try:
        session["constraints"] = json.loads(
            session["constraints_json"]
        )
    except (
        TypeError,
        json.JSONDecodeError
    ):
        session["constraints"] = {}

    try:
        session["plan_steps"] = json.loads(
            session["plan_steps_json"]
        )
    except (
        TypeError,
        json.JSONDecodeError
    ):
        session["plan_steps"] = []

    return session


# ==========================================================
# UPDATE AGENT SESSION
# ==========================================================

def update_agent_session(
    session_id: str,
    current_step: int | None = None,
    spend_committed: float | None = None,
    requires_confirmation: bool | None = None,
    confirmed_at: str | None = None,
    replan_count: int | None = None,
    last_error_code: str | None = None,
    status: str | None = None,
    constraints: dict | None = None,
    plan_steps: list | None = None
):
    updates = []
    values = []

    # ------------------------------------------------------
    # Current step
    # ------------------------------------------------------

    if current_step is not None:
        updates.append("current_step = ?")
        values.append(current_step)

    # ------------------------------------------------------
    # Spend committed
    # ------------------------------------------------------

    if spend_committed is not None:
        updates.append("spend_committed = ?")
        values.append(spend_committed)

    # ------------------------------------------------------
    # Confirmation flag
    # ------------------------------------------------------

    if requires_confirmation is not None:
        updates.append("requires_confirmation = ?")
        values.append(
            int(requires_confirmation)
        )

    # ------------------------------------------------------
    # Confirmed timestamp
    # ------------------------------------------------------

    if confirmed_at is not None:
        updates.append("confirmed_at = ?")
        values.append(confirmed_at)

    # ------------------------------------------------------
    # Re-plan count
    # ------------------------------------------------------

    if replan_count is not None:
        updates.append("replan_count = ?")
        values.append(replan_count)

    # ------------------------------------------------------
    # Error code
    # ------------------------------------------------------

    if last_error_code is not None:
        updates.append("last_error_code = ?")
        values.append(last_error_code)

    # ------------------------------------------------------
    # Status
    # ------------------------------------------------------

    if status is not None:
        updates.append("status = ?")
        values.append(status)

    # ------------------------------------------------------
    # Constraints
    # ------------------------------------------------------

    if constraints is not None:
        updates.append("constraints_json = ?")
        values.append(
            json.dumps(constraints)
        )

    # ------------------------------------------------------
    # Plan steps
    # ------------------------------------------------------

    if plan_steps is not None:
        updates.append("plan_steps_json = ?")
        values.append(
            json.dumps(plan_steps)
        )

    # Nothing to update
    if not updates:
        return

    # ------------------------------------------------------
    # Updated timestamp
    # ------------------------------------------------------

    updates.append("updated_at = ?")

    values.append(
        datetime.now(timezone.utc).isoformat()
    )

    # Session ID for WHERE clause
    values.append(session_id)

    connection = get_connection()
    cursor = connection.cursor()

    query = f"""
        UPDATE agent_sessions
        SET {", ".join(updates)}
        WHERE session_id = ?
    """

    cursor.execute(
        query,
        values
    )

    connection.commit()
    connection.close()