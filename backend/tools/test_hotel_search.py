from backend.tools.hotel_search import search_hotels


results = search_hotels(
    city="Kolkata",
    check_in="2026-09-01",
    check_out="2026-09-03",
    guests=2
)


print(
    "Number of hotel rooms found:",
    len(results)
)


for hotel in results[:10]:

    print("\nHotel:", hotel["hotel_name"])

    print("Room:", hotel["room_type"])

    print(
        "Stay:",
        hotel["check_in"],
        "to",
        hotel["check_out"]
    )

    print(
        "Nights:",
        hotel["nights"]
    )

    print(
        "Total price:",
        hotel["price"],
        hotel["currency"]
    )

    print("Available each night:")

    for night in hotel["nightly_prices"]:

        print(
            "  ",
            night["date"],
            "| Price:",
            night["price"],
            night["currency"],
            "| Available:",
            night["available_units"]
        )