from backend.trip_parser import parse_trip_request
from backend.travel_plan import create_travel_plan


user_goal = """
Plan a 3-day Goa trip for 2 people from Bengaluru
from September 18 to September 20, 2026
under ₹25,000.
"""


# Parse user request
trip = parse_trip_request(user_goal)


# Create transparent plan
plan = create_travel_plan(trip)


print("=" * 60)
print("TRAVEL PLAN")
print("=" * 60)

print()

print("Destination:", trip.destination)
print("Travellers:", trip.travellers)
print("Start date:", trip.start_date)
print("End date:", trip.end_date)
print("Budget:", trip.budget, trip.currency)

print()

print("Agent will:")

for step in plan["steps"]:
    print(
        f"{step['step']}. "
        f"{step['action']}"
    )

print()

print("Confirmation required:", plan["confirmation_required"])

print()

print(plan["message"])