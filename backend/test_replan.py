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


connection = get_connection()
cursor = connection.cursor()


print("=" * 60)
print("DIRECT REPLAN DATABASE TEST")
print("=" * 60)


# --------------------------------------------------
# 1. Check city
# --------------------------------------------------

cursor.execute(
    """
    SELECT city_id, name
    FROM cities
    WHERE LOWER(name) = LOWER(?)
      AND status = 'active'
    """,
    ("Kolkata",)
)

city = cursor.fetchone()

print("\nCITY:")
print(dict(city) if city else None)


# --------------------------------------------------
# 2. Get all Kolkata rooms
# --------------------------------------------------

cursor.execute(
    """
    SELECT
        h.hotel_id,
        h.name AS hotel_name,
        rt.room_type_id,
        rt.name AS room_type,
        rt.max_occupancy,
        rt.base_rate
    FROM hotels h
    JOIN hotel_room_types rt
        ON rt.hotel_id = h.hotel_id
    WHERE h.city_id = ?
      AND h.status = 'active'
      AND rt.status = 'active'
      AND rt.max_occupancy >= ?
    ORDER BY CAST(rt.base_rate AS REAL)
    """,
    (
        city["city_id"],
        2
    )
)

rooms = cursor.fetchall()

print("\nKOLKATA ROOMS:")
for room in rooms:
    print(dict(room))


# --------------------------------------------------
# 3. Check the known cheaper room directly
# --------------------------------------------------

room_id = "rmt_7b889ec3"

cursor.execute(
    """
    SELECT
        entity_id,
        for_date,
        total_units,
        booked_units,
        held_units,
        price,
        currency,
        closed_to_arrival
    FROM inventory_calendar
    WHERE entity_type = 'room_type'
      AND entity_id = ?
      AND for_date IN (?, ?)
    ORDER BY for_date
    """,
    (
        room_id,
        "2026-09-01",
        "2026-09-02"
    )
)

inventory_rows = cursor.fetchall()

print("\nKNOWN CHEAPER ROOM INVENTORY:")

for row in inventory_rows:
    print(dict(row))


# --------------------------------------------------
# 4. Calculate its actual total
# --------------------------------------------------

total = 0.0
valid = True

for row in inventory_rows:

    available = (
        int(row["total_units"])
        - int(row["booked_units"])
        - int(row["held_units"])
    )

    print(
        f"\n{row['for_date']}: "
        f"price={row['price']}, "
        f"available={available}"
    )

    if available <= 0:
        valid = False

    if int(row["closed_to_arrival"] or 0) == 1:
        valid = False

    total += float(row["price"])


print("\nCHEAPER ROOM CHECK:")
print("Valid:", valid)
print("Total:", round(total, 2))
print("Current hotel:", 14721.00)
print(
    "Is cheaper:",
    total < 14721.00
)


connection.close()