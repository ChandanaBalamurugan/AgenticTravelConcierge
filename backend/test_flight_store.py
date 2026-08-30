from backend.flight_store import get_flight_with_fare


flight = get_flight_with_fare(
    flight_id="flt_348fc1e5",
    fare_id="far_c153de57"
)


print("LOADED FLIGHT:")
print(flight)