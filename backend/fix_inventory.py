import os
import sqlite3


DATABASE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data",
    "APS-01.db"
)


connection = sqlite3.connect(DATABASE)
cursor = connection.cursor()


print("=" * 60)
print("FIXING DEMO HOTEL INVENTORY")
print("=" * 60)

# --------------------------------------------------
# Make the cheaper Family Room available
# for both nights.
# --------------------------------------------------

cursor.execute(
    """
    UPDATE inventory_calendar
    SET
        booked_units = 0,
        closed_to_arrival = 0
    WHERE inventory_id IN (
        'inv_ed02ad94',
        'inv_00fb4c3c'
    )
    """
)

print("\nRows changed:", cursor.rowcount)

connection.commit()


# --------------------------------------------------
# Verify immediately using the SAME connection
# --------------------------------------------------

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

print("\nInventory after update:")

for row in rows:
    print(row)


connection.close()