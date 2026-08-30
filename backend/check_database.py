import os
import sqlite3


DATABASE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data",
    "APS-01.db"
)


print("=" * 60)
print("DATABASE CHECK")
print("=" * 60)

print("\nDatabase path:")
print(os.path.abspath(DATABASE))

print("\nDatabase exists:")
print(os.path.exists(DATABASE))

connection = sqlite3.connect(DATABASE)
cursor = connection.cursor()

cursor.execute(
    """
    SELECT
        inventory_id,
        entity_id,
        for_date,
        total_units,
        booked_units,
        held_units,
        price,
        closed_to_arrival
    FROM inventory_calendar
    WHERE inventory_id IN (
        'inv_ed02ad94',
        'inv_00fb4c3c'
    )
    ORDER BY for_date
    """
)

rows = cursor.fetchall()

print("\nInventory rows:")

for row in rows:
    print(row)

connection.close()