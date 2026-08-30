import sqlite3
import os


DATABASE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data",
    "APS-01.db"
)


def search_flights(
    origin: str,
    destination: str,
    travel_date: str,
    max_budget: float | None = None
):
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    query = """
        SELECT
            f.flight_id,
            f.flight_number,

            al.iata AS airline_iata,
            al.name AS airline_name,

            origin_airport.iata AS origin_iata,
            origin_airport.name AS origin_airport_name,

            destination_airport.iata AS destination_iata,
            destination_airport.name AS destination_airport_name,

            f.departs_at,
            f.arrives_at,
            f.duration_minutes,
            f.stops,

            ff.fare_id,
            ff.cabin_class,
            ff.fare_class,

            CAST(ff.base_fare AS REAL) AS base_fare,
            CAST(ff.taxes AS REAL) AS taxes,

            ff.currency,
            ff.baggage_kg,
            ff.cabin_baggage_kg

        FROM flights f

        JOIN airlines al
            ON f.airline_id = al.airline_id

        JOIN airports origin_airport
            ON f.origin_airport_id = origin_airport.airport_id

        JOIN airports destination_airport
            ON f.dest_airport_id = destination_airport.airport_id

        JOIN cities origin_city
            ON origin_airport.city_id = origin_city.city_id

        JOIN cities destination_city
            ON destination_airport.city_id = destination_city.city_id

        JOIN flight_fares ff
            ON f.flight_id = ff.flight_id

        WHERE
            LOWER(origin_city.name) = LOWER(?)

            AND LOWER(destination_city.name) = LOWER(?)

            AND DATE(f.departs_at) = DATE(?)

            AND ff.status = 'active'

            AND f.status = 'active'
    """

    parameters = [
        origin,
        destination,
        travel_date
    ]

    if max_budget is not None:

        query += """
            AND (
                CAST(ff.base_fare AS REAL)
                +
                CAST(ff.taxes AS REAL)
            ) <= ?
        """

        parameters.append(max_budget)

    query += """
        ORDER BY
            (
                CAST(ff.base_fare AS REAL)
                +
                CAST(ff.taxes AS REAL)
            ) ASC
    """

    cursor.execute(query, parameters)

    results = [dict(row) for row in cursor.fetchall()]

    connection.close()

    return results