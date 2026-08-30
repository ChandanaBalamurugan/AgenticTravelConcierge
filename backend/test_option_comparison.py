from backend.tools.flight_search import search_flights
from backend.tools.hotel_search import search_hotels
from backend.option_comparison import compare_options


print("=" * 60)
print("TESTING OPTION COMPARISON")
print("=" * 60)


# --------------------------------------------------
# STEP 1: Search flights
# --------------------------------------------------

flights = search_flights(
    origin="Bengaluru",
    destination="Kolkata",
    travel_date="2026-09-01"
)


# --------------------------------------------------
# STEP 2: Search hotels
# --------------------------------------------------

hotels = search_hotels(
    city="Kolkata",
    check_in="2026-09-01",
    check_out="2026-09-03",
    guests=2
)


print("\nFlights found:", len(flights))
print("Hotels found:", len(hotels))


# --------------------------------------------------
# STEP 3: Compare options
# --------------------------------------------------

result = compare_options(
    flights=flights,
    hotels=hotels,
    budget=6000
)


# --------------------------------------------------
# STEP 4: Display result
# --------------------------------------------------

print("\n" + "=" * 60)
print("COMPARISON RESULT")
print("=" * 60)


if result["status"] == "success":

    flight = result["recommended_flight"]
    hotel = result["recommended_hotel"]

    print("\nRECOMMENDED FLIGHT")
    print("------------------")

    print("Flight:", flight["flight_number"])
    print("Airline:", flight["airline_name"])

    print(
        "Price:",
        result["flight_cost"],
        flight["currency"]
    )


    print("\nRECOMMENDED HOTEL")
    print("-----------------")

    print("Hotel:", hotel["hotel_name"])
    print("Room:", hotel["room_type"])

    print(
        "Price:",
        result["hotel_cost"],
        hotel["currency"]
    )


    print("\nTOTAL")
    print("-----")

    print(
        "Total cost:",
        result["total_cost"],
        flight["currency"]
    )

    print(
        "Budget:",
        25000,
        flight["currency"]
    )

    print(
        "Within budget:",
        result["within_budget"]
    )


    print(
        "\nAlternative flights:",
        len(result["alternative_flights"])
    )

    print(
        "Alternative hotels:",
        len(result["alternative_hotels"])
    )


else:

    print("\nERROR")
    print(result)