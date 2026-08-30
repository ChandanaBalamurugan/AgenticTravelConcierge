from backend.trip_parser import parse_trip_request


# --------------------------------------------------
# Test 1: Complete travel request
# --------------------------------------------------

user_goal = (
    "Plan a 3 day trip from Bengaluru to Kolkata "
    "for 2 people from September 1 to September 3 "
    "with a budget of 25000 INR"
)


print("=" * 50)
print("TEST 1 - COMPLETE TRAVEL REQUEST")
print("=" * 50)

result = parse_trip_request(user_goal)

print(result.model_dump_json(indent=2))


# --------------------------------------------------
# Test 2: Missing information
# --------------------------------------------------

user_goal_2 = """
Plan a trip to Goa for me.
"""


print()
print("=" * 50)
print("TEST 2 - MISSING INFORMATION")
print("=" * 50)

result_2 = parse_trip_request(user_goal_2)

print(result_2.model_dump_json(indent=2))