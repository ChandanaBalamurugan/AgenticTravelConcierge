import sqlite3

DATABASE = "data/APS-01.db"

connection = sqlite3.connect(DATABASE)
connection.row_factory = sqlite3.Row

cursor = connection.cursor()

query = """
SELECT
    origin_city.name AS origin,
    destination_city.name AS destination,
    DATE(f.departs_at) AS travel_date,
    COUNT(*) AS flights

FROM flights f

JOIN airports oa
    ON f.origin_airport_id = oa.airport_id

JOIN cities origin_city
    ON oa.city_id = origin_city.city_id

JOIN airports da
    ON f.dest_airport_id = da.airport_id

JOIN cities destination_city
    ON da.city_id = destination_city.city_id

WHERE f.status = 'active'

GROUP BY
    origin_city.name,
    destination_city.name,
    DATE(f.departs_at)

ORDER BY travel_date

LIMIT 50
"""

cursor.execute(query)

rows = cursor.fetchall()

print("=" * 70)
print("AVAILABLE FLIGHT ROUTES")
print("=" * 70)

for row in rows:
    print(
        row["origin"],
        "->",
        row["destination"],
        "|",
        row["travel_date"],
        "| Flights:",
        row["flights"]
    )

connection.close()