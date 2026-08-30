from flight_search import search_flights


results = search_flights(
    origin="Bengaluru",
    destination="Kolkata",
    travel_date="2026-09-01",
    max_budget=10000
)

print("Number of flights found:", len(results))

for flight in results:
    total_price = flight["base_fare"] + flight["taxes"]

    print(
        flight["flight_number"],
        "|",
        flight["airline_name"],
        "|",
        flight["cabin_class"],
        "|",
        flight["fare_class"],
        "| Total: ₹",
        round(total_price, 2)
    )