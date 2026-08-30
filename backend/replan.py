import os
import sqlite3
from datetime import date, timedelta


DATABASE = os.getenv(
    "DATABASE_PATH",
    os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "data",
        "APS-01.db"
    )
)


def get_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


# ==========================================================
# FIND CITY ID
# ==========================================================

def get_city_id(city_name: str):

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


# ==========================================================
# FIND CHEAPER HOTEL
# ==========================================================

def find_cheaper_hotel(
    city_id: str,
    check_in: str,
    check_out: str,
    guests: int,
    current_price: float
):
    """
    Find the cheapest available hotel room for all
    requested nights that is cheaper than current_price.
    """

    connection = get_connection()
    cursor = connection.cursor()

    # --------------------------------------------------
    # Get requested dates
    # --------------------------------------------------

    start_date = date.fromisoformat(check_in)
    end_date = date.fromisoformat(check_out)

    nights = (end_date - start_date).days

    if nights <= 0:
        connection.close()
        return None

    # --------------------------------------------------
    # Get Kolkata hotel rooms
    # --------------------------------------------------

    cursor.execute(
        """
        SELECT
            h.hotel_id,
            h.name AS hotel_name,

            rt.room_type_id,
            rt.name AS room_type,
            rt.max_occupancy,
            rt.max_adults,
            rt.max_children

        FROM hotels h

        JOIN hotel_room_types rt
            ON rt.hotel_id = h.hotel_id

        WHERE h.city_id = ?
          AND h.status = 'active'
          AND rt.status = 'active'
          AND rt.max_occupancy >= ?

        ORDER BY CAST(rt.base_rate AS REAL) ASC
        """,
        (
            city_id,
            guests
        )
    )

    rooms = cursor.fetchall()

    candidates = []

    # --------------------------------------------------
    # Check each room type
    # --------------------------------------------------

    for room in rooms:

        room_type_id = room["room_type_id"]

        nightly_prices = []
        total_price = 0.0

        valid = True

        current_date = start_date

        while current_date < end_date:

            date_string = current_date.isoformat()

            cursor.execute(
                """
                SELECT
                    price,
                    currency,
                    total_units,
                    booked_units,
                    held_units,
                    closed_to_arrival

                FROM inventory_calendar

                WHERE entity_type = 'room_type'
                  AND entity_id = ?
                  AND for_date = ?

                LIMIT 1
                """,
                (
                    room_type_id,
                    date_string
                )
            )

            inventory = cursor.fetchone()

            # Missing inventory for even one night
            # means this room cannot be selected.
            if inventory is None:
                valid = False
                break

            total_units = int(
                inventory["total_units"] or 0
            )

            booked_units = int(
                inventory["booked_units"] or 0
            )

            held_units = int(
                inventory["held_units"] or 0
            )

            available_units = (
                total_units
                - booked_units
                - held_units
            )

            # No room available
            if available_units <= 0:
                valid = False
                break

            # Closed arrival
            if int(
                inventory["closed_to_arrival"] or 0
            ) == 1:
                valid = False
                break

            price = float(
                inventory["price"]
            )

            total_price += price

            nightly_prices.append(
                {
                    "date": date_string,
                    "price": price,
                    "currency": inventory["currency"],
                    "available_units": available_units
                }
            )

            current_date += timedelta(days=1)

        if not valid:
            continue

        total_price = round(
            total_price,
            2
        )

        # --------------------------------------------------
        # CHEAPER THAN CURRENT HOTEL
        # --------------------------------------------------

        if total_price >= float(current_price):
            continue

        candidates.append(
            {
                "hotel_id": room["hotel_id"],
                "hotel_name": room["hotel_name"],

                "room_type_id": room[
                    "room_type_id"
                ],

                "room_type": room["room_type"],

                "max_occupancy": room[
                    "max_occupancy"
                ],

                "max_adults": room[
                    "max_adults"
                ],

                "max_children": room[
                    "max_children"
                ],

                "check_in": check_in,
                "check_out": check_out,
                "nights": nights,

                "nightly_prices": nightly_prices,

                "price": total_price,
                "total_price": total_price,

                "currency": nightly_prices[0][
                    "currency"
                ]
            }
        )

    connection.close()

    if not candidates:
        return None

    # Cheapest valid alternative
    candidates.sort(
        key=lambda hotel: hotel["total_price"]
    )

    return candidates[0]


# ==========================================================
# REPLAN HOTEL
# ==========================================================

def replan_hotel(
    city_id: str,
    check_in: str,
    check_out: str,
    guests: int,
    current_hotel: dict,
    itinerary_id: str,
    current_total: float,
    flight_cost: float
):

    current_hotel_price = float(
        current_hotel["price"]
    )

    new_hotel = find_cheaper_hotel(
        city_id=city_id,
        check_in=check_in,
        check_out=check_out,
        guests=guests,
        current_price=current_hotel_price
    )

    if new_hotel is None:

        return {
            "status": "failed",
            "message": (
                "No cheaper hotel is currently "
                "available for the selected dates."
            )
        }

    new_hotel_price = float(
        new_hotel["total_price"]
    )

    new_total = round(
        float(flight_cost) + new_hotel_price,
        2
    )

    old_total = round(
        float(current_total),
        2
    )

    savings = round(
        old_total - new_total,
        2
    )

    # ------------------------------------------------------
    # Remove old hotel item
    # ------------------------------------------------------

    from backend.itinerary_store import (
        remove_active_hotel_items,
        add_hotel_item
    )

    remove_active_hotel_items(
        itinerary_id
    )

    # ------------------------------------------------------
    # Add new hotel
    # ------------------------------------------------------

    new_item_id = add_hotel_item(
        itinerary_id=itinerary_id,
        hotel=new_hotel
    )

    return {
        "status": "success",
        "hotel": new_hotel,
        "hotel_item_id": new_item_id,
        "old_hotel_price": round(
            current_hotel_price,
            2
        ),
        "new_hotel_price": round(
            new_hotel_price,
            2
        ),
        "old_total": old_total,
        "new_total": new_total,
        "saved": savings
    }