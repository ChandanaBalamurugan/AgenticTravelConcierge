from backend.itinerary_store import (
    create_itinerary,
    add_hotel_item,
    get_itinerary
)


TRIP_ID = "trp_dd18b045"


hotel = {
    "hotel_id": "htl_47d978bd",
    "hotel_name": "Heritage Kothi Inn",
    "room_type": "Deluxe",
    "price": 14721.00,
    "currency": "INR"
}


print("=" * 60)
print("TESTING ITINERARY STORE")
print("=" * 60)


# --------------------------------------------------
# CREATE ITINERARY
# --------------------------------------------------

itinerary_id = create_itinerary(
    trip_id=TRIP_ID,
    name="Bengaluru to Kolkata Agent Recommendation",
    total_cost=20556.00,
    currency="INR",
    total_duration_minutes=172,
    generated_by="agent"
)

print("\nCreated itinerary:")
print(itinerary_id)


# --------------------------------------------------
# ADD HOTEL
# --------------------------------------------------

item_id = add_hotel_item(
    itinerary_id=itinerary_id,
    hotel=hotel
)

print("\nCreated hotel item:")
print(item_id)


# --------------------------------------------------
# LOAD ITINERARY
# --------------------------------------------------

itinerary = get_itinerary(itinerary_id)

print("\nLoaded itinerary:")
print(itinerary)