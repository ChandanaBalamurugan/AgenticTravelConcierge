import sqlite3
import os
from datetime import date, timedelta


DATABASE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data",
    "APS-01.db"
)


def _get_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def _get_nights(check_in: str, check_out: str):
    start = date.fromisoformat(check_in)
    end = date.fromisoformat(check_out)

    if end <= start:
        raise ValueError(
            "check_out must be later than check_in."
        )

    nights = []

    current = start

    while current < end:
        nights.append(current.isoformat())
        current += timedelta(days=1)

    return nights


def search_hotels(
    city: str,
    check_in: str,
    check_out: str,
    guests: int,
    max_budget: float | None = None
):
    """
    Search bookable hotel rooms for the complete stay.

    Example:

        check_in  = 2026-09-01
        check_out = 2026-09-03

    means two nights:

        2026-09-01
        2026-09-02

    The returned `price` is the TOTAL price for the
    complete stay, not just one night.
    """

    if guests < 1:
        raise ValueError(
            "guests must be at least 1."
        )

    nights = _get_nights(
        check_in,
        check_out
    )

    connection = _get_connection()
    cursor = connection.cursor()

    # --------------------------------------------------
    # FIND HOTEL ROOMS IN THE REQUESTED CITY
    # --------------------------------------------------

    cursor.execute(
        """
        SELECT
            h.hotel_id,
            h.name AS hotel_name,
            h.property_type,
            h.star_rating,
            h.guest_score,
            h.review_count,
            h.address_line,
            h.distance_to_centre_km,

            c.name AS city,

            rt.room_type_id,
            rt.name AS room_type,
            rt.max_occupancy,
            rt.max_adults,
            rt.max_children

        FROM hotels h

        JOIN hotel_room_types rt
            ON h.hotel_id = rt.hotel_id

        JOIN cities c
            ON h.city_id = c.city_id

        WHERE
            LOWER(c.name) = LOWER(?)
            AND h.status = 'active'
            AND rt.status = 'active'
            AND rt.max_occupancy >= ?
        """,
        (
            city,
            guests
        )
    )

    room_candidates = cursor.fetchall()

    results = []

    # --------------------------------------------------
    # CHECK INVENTORY FOR EVERY NIGHT
    # --------------------------------------------------

    for room in room_candidates:

        nightly_prices = []
        nightly_details = []

        valid_room = True

        for night in nights:

            cursor.execute(
                """
                SELECT
                    total_units,
                    booked_units,
                    held_units,
                    price,
                    currency,
                    min_stay_nights,
                    closed_to_arrival

                FROM inventory_calendar

                WHERE
                    entity_type = 'room_type'
                    AND entity_id = ?
                    AND DATE(for_date) = DATE(?)
                LIMIT 1
                """,
                (
                    room["room_type_id"],
                    night
                )
            )

            inventory = cursor.fetchone()

            # No inventory row for this date.
            if inventory is None:
                valid_room = False
                break

            available_units = (
                inventory["total_units"]
                - inventory["booked_units"]
                - inventory["held_units"]
            )

            # No rooms available.
            if available_units <= 0:
                valid_room = False
                break

            # Prevent check-in when the property is closed
            # to arrival on the first night.
            if (
                night == check_in
                and inventory["closed_to_arrival"] == 1
            ):
                valid_room = False
                break

            # Ensure the room supports the requested stay
            # length.
            if (
                inventory["min_stay_nights"] > len(nights)
            ):
                valid_room = False
                break

            price = float(inventory["price"])

            nightly_prices.append(price)

            nightly_details.append(
                {
                    "date": night,
                    "price": round(price, 2),
                    "currency": inventory["currency"],
                    "available_units": available_units
                }
            )

        if not valid_room:
            continue

        # --------------------------------------------------
        # CALCULATE COMPLETE STAY COST
        # --------------------------------------------------

        total_price = round(
            sum(nightly_prices),
            2
        )

        currency = nightly_details[0]["currency"]

        # --------------------------------------------------
        # APPLY TOTAL-STAY BUDGET FILTER
        # --------------------------------------------------

        if (
            max_budget is not None
            and total_price > float(max_budget)
        ):
            continue

        result = {
            "hotel_id": room["hotel_id"],
            "hotel_name": room["hotel_name"],
            "property_type": room["property_type"],
            "star_rating": room["star_rating"],
            "guest_score": room["guest_score"],
            "review_count": room["review_count"],
            "address_line": room["address_line"],
            "distance_to_centre_km": room[
                "distance_to_centre_km"
            ],

            "city": room["city"],

            "room_type_id": room["room_type_id"],
            "room_type": room["room_type"],
            "max_occupancy": room["max_occupancy"],
            "max_adults": room["max_adults"],
            "max_children": room["max_children"],

            "check_in": check_in,
            "check_out": check_out,
            "nights": len(nights),

            "nightly_prices": nightly_details,

            # Keep `price` for compatibility with the
            # existing comparison and budget code.
            "price": total_price,

            "total_price": total_price,

            "currency": currency
        }

        results.append(result)

    connection.close()

    # --------------------------------------------------
    # CHEAPEST COMPLETE STAY FIRST
    # --------------------------------------------------

    results.sort(
        key=lambda hotel: hotel["price"]
    )

    return results