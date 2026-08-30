from backend.trip_parser import TripRequest


def get_missing_fields(trip: TripRequest):

    missing = []

    if not trip.origin:
        missing.append("origin")

    if not trip.destination:
        missing.append("destination")

    if not trip.travellers:
        missing.append("travellers")

    if not trip.start_date:
        missing.append("start_date")

    if not trip.end_date:
        missing.append("end_date")

    if trip.budget is None:
        missing.append("budget")

    return missing


def create_clarification_message(missing_fields):

    questions = []

    if "origin" in missing_fields:
        questions.append(
            "Where will you be travelling from?"
        )

    if "destination" in missing_fields:
        questions.append(
            "Where would you like to go?"
        )

    if "travellers" in missing_fields:
        questions.append(
            "How many people will be travelling?"
        )

    if "start_date" in missing_fields:
        questions.append(
            "What is your travel start date?"
        )

    if "end_date" in missing_fields:
        questions.append(
            "What is your travel end date?"
        )

    if "budget" in missing_fields:
        questions.append(
            "What is your maximum total budget?"
        )

    if not questions:
        return None

    message = (
        "I need a few details before I can safely plan your trip:\n\n"
    )

    for index, question in enumerate(questions, start=1):
        message += f"{index}. {question}\n"

    return message