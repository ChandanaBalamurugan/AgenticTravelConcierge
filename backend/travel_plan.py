from backend.trip_parser import TripRequest


def create_travel_plan(trip: TripRequest):

    plan = {
        "title": "Your Travel Plan",

        "steps": [
            {
                "step": 1,
                "action": "Search flights",
                "status": "pending"
            },
            {
                "step": 2,
                "action": "Search hotels",
                "status": "pending"
            },
            {
                "step": 3,
                "action": "Check total cost against budget",
                "status": "pending"
            },
            {
                "step": 4,
                "action": "Compare available options",
                "status": "pending"
            },
            {
                "step": 5,
                "action": "Prepare booking cart",
                "status": "pending"
            },
            {
                "step": 6,
                "action": "Wait for explicit user confirmation",
                "status": "pending"
            }
        ],

        "confirmation_required": True,

        "message": (
            "No booking or payment will happen "
            "without your explicit confirmation."
        )
    }

    return plan