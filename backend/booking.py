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


def confirm_booking(
    flight: dict,
    hotel: dict,
    total_cost: float,
    currency: str,
    user_confirmation: bool,
    user_id: str,
    trip_id: str,
    itinerary_id: str
):
    """
    Safely confirm a travel booking.

    This is an MVP booking simulation.
    No real payment or external booking is performed.

    After explicit confirmation, the booking is persisted
    in the SQLite `bookings` table.
    """

    # --------------------------------------------------
    # 1. EXPLICIT USER CONFIRMATION
    # --------------------------------------------------

    if not user_confirmation:

        return {
            "status": "cancelled",
            "message": (
                "Booking was not completed because "
                "explicit user confirmation was not provided."
            ),
            "booking_id": None
        }

    # --------------------------------------------------
    # 2. REQUIRED INFORMATION
    # --------------------------------------------------

    if not flight:

        return {
            "status": "error",
            "message": "Flight information is missing.",
            "booking_id": None
        }

    if not hotel:

        return {
            "status": "error",
            "message": "Hotel information is missing.",
            "booking_id": None
        }

    if not user_id:

        return {
            "status": "error",
            "message": "User ID is missing.",
            "booking_id": None
        }

    if not trip_id:

        return {
            "status": "error",
            "message": "Trip ID is missing.",
            "booking_id": None
        }

    if not itinerary_id:

        return {
            "status": "error",
            "message": "Itinerary ID is missing.",
            "booking_id": None
        }

    # --------------------------------------------------
    # 3. GENERATE IDS
    # --------------------------------------------------

    booking_id = (
        "BKG_" + uuid.uuid4().hex[:8].upper()
    )

    booking_reference = (
        "TRV-" + uuid.uuid4().hex[:8].upper()
    )

    idempotency_key = (
        "IDEMP_" + uuid.uuid4().hex
    )

    now = datetime.now(timezone.utc).isoformat()

    # --------------------------------------------------
    # 4. CALCULATE TAX AMOUNT
    # --------------------------------------------------

    flight_price = (
        float(flight.get("base_fare", 0))
        + float(flight.get("taxes", 0))
    )

    hotel_price = float(
        hotel.get("price", 0)
    )

    total_amount = round(
        float(total_cost),
        2
    )

    tax_amount = round(
        float(flight.get("taxes", 0)),
        2
    )

    # --------------------------------------------------
    # 5. PERSIST BOOKING
    # --------------------------------------------------

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            INSERT INTO bookings (
                booking_id,
                user_id,
                trip_id,
                itinerary_id,
                booking_reference,
                channel,
                total_amount,
                currency,
                tax_amount,
                idempotency_key,
                status,
                confirmed_at,
                cancelled_at,
                cancellation_reason,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                booking_id,
                user_id,
                trip_id,
                itinerary_id,
                booking_reference,
                "agentic_mvp",
                f"{total_amount:.2f}",
                currency.upper(),
                f"{tax_amount:.2f}",
                idempotency_key,
                "confirmed",
                now,
                None,
                None,
                now,
                now
            )
        )

        connection.commit()

    except sqlite3.IntegrityError as e:

        connection.rollback()

        connection.close()

        return {
            "status": "error",
            "message": (
                f"Could not persist booking: {str(e)}"
            ),
            "booking_id": None
        }

    except Exception as e:

        connection.rollback()

        connection.close()

        return {
            "status": "error",
            "message": (
                f"Booking persistence failed: {str(e)}"
            ),
            "booking_id": None
        }

    connection.close()

    # --------------------------------------------------
    # 6. RETURN BOOKING RESULT
    # --------------------------------------------------

    booking = {
        "status": "confirmed",

        "booking_id": booking_id,

        "booking_reference": booking_reference,

        "created_at": now,

        "trip_id": trip_id,

        "itinerary_id": itinerary_id,

        "flight": {
            "flight_number": flight.get(
                "flight_number"
            ),
            "airline": flight.get(
                "airline_name"
            ),
            "origin": flight.get(
                "origin_iata"
            ),
            "destination": flight.get(
                "destination_iata"
            ),
            "cabin_class": flight.get(
                "cabin_class"
            ),
            "fare_class": flight.get(
                "fare_class"
            ),
            "price": round(
                flight_price,
                2
            )
        },

        "hotel": {
            "hotel_name": hotel.get(
                "hotel_name"
            ),
            "room_type": hotel.get(
                "room_type"
            ),
            "city": hotel.get(
                "city"
            ),
            "price": round(
                hotel_price,
                2
            ),
            "nights": hotel.get(
                "nights"
            )
        },

        "total_cost": total_amount,

        "currency": currency.upper(),

        "payment_status": "NOT_PROCESSED",

        "message": (
            "Booking confirmed successfully for the MVP. "
            "No real payment or external booking was performed."
        )
    }

    return booking

def get_existing_booking(
    trip_id: str,
    itinerary_id: str
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM bookings
        WHERE trip_id = ?
          AND itinerary_id = ?
          AND status = 'confirmed'
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (
            trip_id,
            itinerary_id
        )
    )

    row = cursor.fetchone()

    connection.close()

    if row is None:
        return None

    return dict(row)