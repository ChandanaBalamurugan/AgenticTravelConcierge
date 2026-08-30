import os
import sqlite3
import uuid
from datetime import datetime, timezone


DATABASE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data",
    "APS-01.db"
)


def get_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def find_city_id(city_name: str):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT city_id
        FROM cities
        WHERE LOWER(name) = LOWER(?)
          AND status = 'active'
        LIMIT 1
        """,
        (city_name,)
    )

    row = cursor.fetchone()

    connection.close()

    if row is None:
        return None

    return row["city_id"]


def create_trip(
    owner_user_id: str,
    title: str,
    origin: str,
    destination: str,
    start_date: str,
    end_date: str,
    party_size: int,
    adults: int,
    children: int,
    trip_type: str,
    home_currency: str,
    notes: str | None = None
):
    origin_city_id = find_city_id(origin)
    destination_city_id = find_city_id(destination)

    if origin_city_id is None:
        raise ValueError(
            f"Origin city not found: {origin}"
        )

    if destination_city_id is None:
        raise ValueError(
            f"Destination city not found: {destination}"
        )

    trip_id = "trp_" + uuid.uuid4().hex[:8]

    now = datetime.now(timezone.utc).isoformat()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO trips (
            trip_id,
            owner_user_id,
            title,
            origin_city_id,
            destination_city_id,
            start_date,
            end_date,
            party_size,
            adults,
            children,
            trip_type,
            is_group_trip,
            status,
            home_currency,
            notes,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            trip_id,
            owner_user_id,
            title,
            origin_city_id,
            destination_city_id,
            start_date,
            end_date,
            party_size,
            adults,
            children,
            trip_type,
            int(party_size > 1),
            "planning",
            home_currency,
            notes,
            now,
            now
        )
    )

    connection.commit()
    connection.close()

    return trip_id


def get_trip(trip_id: str):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM trips
        WHERE trip_id = ?
        """,
        (trip_id,)
    )

    row = cursor.fetchone()

    connection.close()

    if row is None:
        return None

    return dict(row)