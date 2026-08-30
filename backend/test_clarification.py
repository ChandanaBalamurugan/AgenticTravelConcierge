from backend.trip_parser import parse_trip_request
from backend.clarification import (
    get_missing_fields,
    create_clarification_message
)


# --------------------------------------------------
# TEST 1
# --------------------------------------------------

user_goal = """
Plan a trip to Goa for me.
"""


print("=" * 60)
print("TEST 1 - INCOMPLETE REQUEST")
print("=" * 60)

trip = parse_trip_request(user_goal)

missing = get_missing_fields(trip)

print("Missing fields:")
print(missing)

print()

print("Clarification message:")
print(create_clarification_message(missing))


# --------------------------------------------------
# TEST 2
# --------------------------------------------------

user_goal_2 = """
Plan a 3-day Goa trip for 2 people from Bengaluru
from September 18 to September 20, 2026
under ₹25,000.
"""


print()
print("=" * 60)
print("TEST 2 - COMPLETE REQUEST")
print("=" * 60)

trip_2 = parse_trip_request(user_goal_2)

missing_2 = get_missing_fields(trip_2)

print("Missing fields:")
print(missing_2)

print()

print("Clarification message:")
print(create_clarification_message(missing_2))