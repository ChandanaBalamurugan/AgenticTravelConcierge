import os
import sqlite3
import uuid
from datetime import datetime, timezone



DATABASE = os.getenv(
    "DATABASE_PATH",
    os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "data",
        "APS-01.db"
    )
)


def get_connection():
    connection = sqlite3.connect(
        DATABASE,
        timeout=10
    )

    connection.row_factory = sqlite3.Row

    connection.execute("PRAGMA journal_mode=WAL;")
    connection.execute("PRAGMA busy_timeout=10000;")

    return connection


def create_itinerary(
    trip_id: str,
    name: str,
    total_cost: float,
    currency: str,
    total_duration_minutes: int = 0,
    total_carbon_kg: float = 0.0,
    generated_by: str = "agent",
    status: str = "active"
):
    itinerary_id = "itn_" + uuid.uuid4().hex[:8]

    now = datetime.now(timezone.utc).isoformat()

    connection = get_connection()
    cursor = connection.cursor()

    # --------------------------------------------------
    # Find current version for this trip
    # --------------------------------------------------

    cursor.execute(
        """
        SELECT COALESCE(MAX(version), 0) AS max_version
        FROM itineraries
        WHERE trip_id = ?
        """,
        (trip_id,)
    )

    row = cursor.fetchone()

    version = int(row["max_version"]) + 1

    # --------------------------------------------------
    # Deactivate previous itinerary
    # --------------------------------------------------

    cursor.execute(
        """
        UPDATE itineraries
        SET
            is_active = 0,
            status = 'inactive',
            updated_at = ?
        WHERE trip_id = ?
          AND is_active = 1
        """,
        (
            now,
            trip_id
        )
    )

    # --------------------------------------------------
    # Create new itinerary
    # --------------------------------------------------

    cursor.execute(
        """
        INSERT INTO itineraries (
            itinerary_id,
            trip_id,
            name,
            version,
            is_active,
            generated_by,
            total_cost,
            currency,
            total_duration_minutes,
            total_carbon_kg,
            optimizer_weights,
            status,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            itinerary_id,
            trip_id,
            name,
            version,
            1,
            generated_by,
            round(total_cost, 2),
            currency,
            total_duration_minutes,
            total_carbon_kg,
            None,
            status,
            now,
            now
        )
    )

    connection.commit()
    connection.close()

    return itinerary_id


def add_hotel_item(
    itinerary_id: str,
    hotel: dict,
    day_index: int = 1,
    sort_order: int = 1
):
    item_id = "itm_" + uuid.uuid4().hex[:8]

    now = datetime.now(timezone.utc).isoformat()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO itinerary_items (
            item_id,
            itinerary_id,
            day_index,
            sort_order,
            starts_at,
            ends_at,
            item_type,
            entity_type,
            entity_id,
            title,
            cost,
            currency,
            carbon_kg,
            duration_minutes,
            source,
            explanation,
            locked,
            status,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            item_id,
            itinerary_id,
            day_index,
            sort_order,
            None,
            None,
            "hotel",
            "hotel",
            hotel["hotel_id"],
            f'{hotel["hotel_name"]} - {hotel["room_type"]}',
            round(float(hotel["price"]), 2),
            hotel["currency"],
            0.0,
            0,
            "agent",
            "Recommended hotel from the travel planning agent.",
            0,
            "proposed",
            now,
            now
        )
    )

    connection.commit()
    connection.close()

    return item_id


def get_itinerary(itinerary_id: str):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM itineraries
        WHERE itinerary_id = ?
        """,
        (itinerary_id,)
    )

    row = cursor.fetchone()

    if row is None:
        connection.close()
        return None

    itinerary = dict(row)

    cursor.execute(
        """
        SELECT *
        FROM itinerary_items
        WHERE itinerary_id = ?
          AND status != 'removed'
        ORDER BY day_index, sort_order
        """,
        (itinerary_id,)
    )

    itinerary["items"] = [
        dict(item)
        for item in cursor.fetchall()
    ]

    connection.close()

    return itinerary


def get_active_itinerary_for_trip(trip_id: str):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM itineraries
        WHERE trip_id = ?
          AND is_active = 1
          AND status = 'active'
        ORDER BY version DESC
        LIMIT 1
        """,
        (trip_id,)
    )

    row = cursor.fetchone()

    if row is None:
        connection.close()
        return None

    itinerary = dict(row)

    cursor.execute(
        """
        SELECT *
        FROM itinerary_items
        WHERE itinerary_id = ?
          AND status != 'removed'
        ORDER BY day_index, sort_order
        """,
        (itinerary["itinerary_id"],)
    )

    itinerary["items"] = [
        dict(item)
        for item in cursor.fetchall()
    ]

    connection.close()

    return itinerary



def remove_active_hotel_items(itinerary_id: str):
    connection = get_connection()
    cursor = connection.cursor()

    now = datetime.now(timezone.utc).isoformat()

    cursor.execute(
        """
        UPDATE itinerary_items
        SET status = 'removed',
            updated_at = ?
        WHERE itinerary_id = ?
          AND item_type = 'hotel'
          AND entity_type = 'hotel'
          AND status != 'removed'
        """,
        (
            now,
            itinerary_id
        )
    )

    connection.commit()
    connection.close()