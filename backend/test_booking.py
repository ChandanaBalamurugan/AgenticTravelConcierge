from backend.booking import confirm_booking


# --------------------------------------------------
# SAMPLE FLIGHT
# --------------------------------------------------

flight = {
    "flight_number": "KU-7715",
    "airline_name": "Kuwait Airways",
    "origin_iata": "BLR",
    "destination_iata": "CCU",
    "cabin_class": "Economy",
    "fare_class": "Y",
    "base_fare": 5000,
    "taxes": 835
}


# --------------------------------------------------
# SAMPLE HOTEL
# --------------------------------------------------

hotel = {
    "hotel_name": "Heritage Kothi Inn",
    "room_type": "Deluxe",
    "city": "Kolkata",
    "price": 7172.19
}


total_cost = 13007.19


# ==================================================
# TEST 1 - USER CONFIRMS
# ==================================================

print("=" * 60)
print("TEST 1 - USER CONFIRMS BOOKING")
print("=" * 60)

result = confirm_booking(
    flight=flight,
    hotel=hotel,
    total_cost=total_cost,
    currency="INR",
    user_confirmation=True
)

print(result)


# ==================================================
# TEST 2 - USER DOES NOT CONFIRM
# ==================================================

print("\n" + "=" * 60)
print("TEST 2 - USER DOES NOT CONFIRM")
print("=" * 60)

result = confirm_booking(
    flight=flight,
    hotel=hotel,
    total_cost=total_cost,
    currency="INR",
    user_confirmation=False
)

print(result)