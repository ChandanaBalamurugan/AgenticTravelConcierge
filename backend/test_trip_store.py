from backend.trip_store import create_trip, get_trip


USER_ID = "usr_6afe5712"


trip_id = create_trip(
    owner_user_id=USER_ID,
    title="Bengaluru to Kolkata Trip",
    origin="Bengaluru",
    destination="Kolkata",
    start_date="2026-09-01",
    end_date="2026-09-03",
    party_size=2,
    adults=2,
    children=0,
    trip_type="friends",
    home_currency="INR",
    notes="Created for agent persistence testing"
)


print("CREATED TRIP:")
print(trip_id)


trip = get_trip(trip_id)

print("\nLOADED TRIP:")
print(trip)