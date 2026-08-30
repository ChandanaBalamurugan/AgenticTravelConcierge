import os
import sqlite3


DATABASE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data",
    "APS-01.db"
)


def get_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def get_flight_with_fare(
    flight_id: str,
    fare_id: str
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            f.flight_id,
            f.flight_number,
            f.departs_at,
            f.arrives_at,
            f.duration_minutes,
            f.stops,
            f.status AS flight_status,

            fa.fare_id,
            fa.cabin_class,
            fa.fare_class,
            fa.base_fare,
            fa.taxes,
            fa.currency,
            fa.baggage_kg,
            fa.cabin_baggage_kg,
            fa.status AS fare_status,

            a1.iata AS origin_iata,
            a1.name AS origin_airport_name,

            a2.iata AS destination_iata,
            a2.name AS destination_airport_name,

            al.iata AS airline_iata,
            al.name AS airline_name

        FROM flights f

        JOIN flight_fares fa
            ON fa.flight_id = f.flight_id

        JOIN airports a1
            ON a1.airport_id = f.origin_airport_id

        JOIN airports a2
            ON a2.airport_id = f.dest_airport_id

        JOIN airlines al
            ON al.airline_id = f.airline_id

        WHERE
            f.flight_id = ?
            AND fa.fare_id = ?

        LIMIT 1
        """,
        (
            flight_id,
            fare_id
        )
    )

    row = cursor.fetchone()

    connection.close()

    if row is None:
        return None

    flight = dict(row)

    flight["base_fare"] = float(
        flight["base_fare"]
    )

    flight["taxes"] = float(
        flight["taxes"]
    )

    flight["baggage_kg"] = int(
        flight["baggage_kg"]
    )

    flight["cabin_baggage_kg"] = int(
        flight["cabin_baggage_kg"]
    )

    flight["duration_minutes"] = int(
        flight["duration_minutes"]
    )

    flight["stops"] = int(
        flight["stops"]
    )

    return flight