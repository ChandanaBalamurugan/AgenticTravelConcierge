import uuid

from backend.session_store import (
    save_agent_session,
    update_agent_session
)

from backend.itinerary_store import (
    create_itinerary,
    add_hotel_item
)

from backend.trip_store import create_trip
from backend.booking import confirm_booking
from backend.trip_parser import parse_trip_request
from backend.travel_plan import create_travel_plan
from backend.option_comparison import compare_options

from backend.tools.flight_search import search_flights
from backend.tools.hotel_search import search_hotels
from backend.tools.budget_check import check_budget

from backend.agent_state import AgentState


# ==========================================================
# TEMPORARY IN-MEMORY SESSION STORE
# ==========================================================

SESSIONS = {}


def run_agent(goal: str, user_confirmed: bool = False):

    # ==================================================
    # CREATE AGENT SESSION
    # ==================================================

    session_id = "AGT_" + uuid.uuid4().hex[:8]

    state = AgentState(
        session_id=session_id,
        goal=goal
    )

    print("\n" + "=" * 60)
    print("AGENT STARTED")
    print("=" * 60)

    # ==================================================
    # STEP 1 - UNDERSTAND USER REQUEST
    # ==================================================

    print("\nSTEP 1: Understanding travel request...")

    trip = parse_trip_request(goal)

    state.trip = trip

    print("Destination:", trip.destination)
    print("Travellers:", trip.travellers)
    print("Start:", trip.start_date)
    print("End:", trip.end_date)
    print("Budget:", trip.budget, trip.currency)

    # ==================================================
    # CHECK REQUIRED INFORMATION
    # ==================================================

    required_fields = [
        "origin",
        "destination",
        "travellers",
        "start_date",
        "end_date",
        "budget",
        "currency"
    ]

    missing_fields = []

    for field in required_fields:

        value = getattr(trip, field)

        if value is None:
            missing_fields.append(field)

    # --------------------------------------------------
    # NEED CLARIFICATION
    # --------------------------------------------------

    if missing_fields:

        state.status = "NEEDS_CLARIFICATION"

        state.last_error = (
            "Missing required information: "
            + ", ".join(missing_fields)
        )

        print("\nMissing information:")
        print(missing_fields)

        return state

    # ==================================================
    # CREATE PERSISTENT TRIP
    # ==================================================

    print("\nCreating persistent trip...")

    adults = (
        trip.adults
        if trip.adults is not None
        else trip.travellers
    )

    children = (
        trip.children
        if trip.children is not None
        else 0
    )

    if trip.travellers == 1:
        trip_type = "solo"

    elif trip.travellers == 2:
        trip_type = "couple"

    else:
        trip_type = "friends"

    trip_id = create_trip(
        owner_user_id="usr_6afe5712",
        title=f"{trip.origin} to {trip.destination} Trip",
        origin=trip.origin,
        destination=trip.destination,
        start_date=trip.start_date,
        end_date=trip.end_date,
        party_size=trip.travellers,
        adults=adults,
        children=children,
        trip_type=trip_type,
        home_currency=trip.currency,
        notes="Created by Agentic Travel Concierge"
    )

    state.trip_id = trip_id

    print("Persistent trip created:", trip_id)

    # ==================================================
    # SAVE INITIAL AGENT SESSION
    # ==================================================

    save_agent_session(
        session_id=state.session_id,
        goal_text=state.goal,
        constraints={
            "origin": trip.origin,
            "destination": trip.destination,
            "travellers": trip.travellers,
            "start_date": trip.start_date,
            "end_date": trip.end_date,
            "budget": trip.budget,
            "currency": trip.currency
        },
        plan_steps=[],
        current_step=1,
        spend_cap=trip.budget,
        spend_committed=0,
        currency=trip.currency,
        requires_confirmation=False,
        status="planning",
        user_id="usr_6afe5712",
        trip_id=state.trip_id,
        replan_count=0
    )

    print(
        "Initial agent session saved:",
        state.session_id
    )

    # ==================================================
    # STEP 2 - CREATE TRANSPARENT PLAN
    # ==================================================

    print("\nSTEP 2: Creating transparent travel plan...")

    state.plan = create_travel_plan(trip)
    update_agent_session(
    session_id=state.session_id,
    current_step=2,
    plan_steps=[
        step["action"]
        for step in state.plan["steps"]
    ]
)

    for step in state.plan["steps"]:

        print(
            f"{step['step']}. "
            f"{step['action']}"
        )

    # ==================================================
    # STEP 3 - SEARCH FLIGHTS
    # ==================================================

    print("\nSTEP 3: Searching flights...")

    state.flight_results = search_flights(
        origin=trip.origin,
        destination=trip.destination,
        travel_date=trip.start_date
    )

    print(
        "Flights found:",
        len(state.flight_results)
    )

    if not state.flight_results:

        state.status = "FAILED"
        state.last_error = "No flights found."

        update_agent_session(
            session_id=state.session_id,
            current_step=3,
            status="failed",
            last_error_code="NO_FLIGHTS"
        )

        print("\nNo flights found.")

        return state

    # ==================================================
    # STEP 4 - SEARCH HOTELS
    # ==================================================

    print("\nSTEP 4: Searching hotels...")

    state.hotel_results = search_hotels(
        city=trip.destination,
        check_in=trip.start_date,
        check_out=trip.end_date,
        guests=trip.travellers
    )

    print(
        "Hotels found:",
        len(state.hotel_results)
    )

    if not state.hotel_results:

        state.status = "FAILED"
        state.last_error = "No hotels found."

        update_agent_session(
            session_id=state.session_id,
            current_step=4,
            status="failed",
            last_error_code="NO_HOTELS"
        )

        print("\nNo hotels found.")

        return state

    # ==================================================
    # STEP 5 - COMPARE OPTIONS
    # ==================================================

    print("\nSTEP 5: Comparing available options...")

    comparison = compare_options(
        state.flight_results,
        state.hotel_results,
        trip.budget
    )

    # ==================================================
    # RE-PLANNING WHEN OVER BUDGET
    # ==================================================

    if comparison["status"] != "success":

        reason = comparison.get("reason")

        if reason == "OVER_BUDGET":

            print("\nInitial plan is over budget.")
            print("Starting automatic re-planning...")

            state.replan_count += 1

            update_agent_session(
                session_id=state.session_id,
                current_step=5,
                replan_count=state.replan_count,
                status="replanning",
                last_error_code="OVER_BUDGET"
            )

            print(
                "Re-plan attempt:",
                state.replan_count
            )

            replanned = None

            cheapest_flight = comparison.get(
                "cheapest_flight"
            )

            cheapest_hotel = comparison.get(
                "cheapest_hotel"
            )

            alternative_flights = comparison.get(
                "alternative_flights",
                []
            )

            alternative_hotels = comparison.get(
                "alternative_hotels",
                []
            )

            # ------------------------------------------
            # BUILD UNIQUE ALTERNATIVE LISTS
            # ------------------------------------------

            all_flights = []

            if cheapest_flight is not None:
                all_flights.append(cheapest_flight)

            all_flights.extend(
                alternative_flights
            )

            all_hotels = []

            if cheapest_hotel is not None:
                all_hotels.append(cheapest_hotel)

            all_hotels.extend(
                alternative_hotels
            )

            unique_flights = {}

            for flight in all_flights:

                key = (
                    flight.get("flight_id"),
                    flight.get("fare_id")
                )

                unique_flights[key] = flight

            unique_hotels = {}

            for hotel in all_hotels:

                key = (
                    hotel.get("hotel_id"),
                    hotel.get("room_type_id")
                )

                unique_hotels[key] = hotel

            flight_options = list(
                unique_flights.values()
            )

            hotel_options = list(
                unique_hotels.values()
            )

            # ------------------------------------------
            # TRY ALL AVAILABLE ALTERNATIVE COMBINATIONS
            # ------------------------------------------

            for flight in flight_options:

                current_flight_cost = round(
                    float(flight["base_fare"])
                    + float(flight["taxes"]),
                    2
                )

                for hotel in hotel_options:

                    current_hotel_cost = round(
                        float(hotel["price"]),
                        2
                    )

                    current_total = round(
                        current_flight_cost
                        + current_hotel_cost,
                        2
                    )

                    if current_total <= float(
                        trip.budget
                    ):

                        replanned = {
                            "flight": flight,
                            "hotel": hotel,
                            "flight_cost": current_flight_cost,
                            "hotel_cost": current_hotel_cost,
                            "total_cost": current_total
                        }

                        break

                if replanned is not None:
                    break

            # ------------------------------------------
            # RE-PLAN SUCCESS
            # ------------------------------------------

            if replanned is not None:

                print(
                    "\nRe-planning successful."
                )

                state.selected_flight = (
                    replanned["flight"]
                )

                state.selected_hotel = (
                    replanned["hotel"]
                )

                print(
                    "New recommended flight:",
                    state.selected_flight[
                        "flight_number"
                    ]
                )

                print(
                    "New recommended hotel:",
                    state.selected_hotel[
                        "hotel_name"
                    ]
                )

                print(
                    "New total:",
                    replanned["total_cost"],
                    trip.currency
                )

                # --------------------------------------
                # CHECK BUDGET AGAIN
                # --------------------------------------

                print(
                    "\nSTEP 6: Checking budget "
                    "after re-planning..."
                )

                budget_result = check_budget(
                    flight_cost=replanned["flight_cost"],
                    flight_currency=(
                        state.selected_flight[
                            "currency"
                        ]
                    ),
                    hotel_cost=replanned["hotel_cost"],
                    hotel_currency=(
                        state.selected_hotel[
                            "currency"
                        ]
                    ),
                    budget_limit=trip.budget,
                    budget_currency=trip.currency
                )

                state.budget_result = budget_result

                if (
                    budget_result["status"] != "success"
                    or not budget_result["within_budget"]
                ):

                    state.status = "FAILED"

                    state.last_error = (
                        "Re-planning could not produce "
                        "a valid plan within the "
                        "user's budget."
                    )

                    update_agent_session(
                        session_id=state.session_id,
                        current_step=6,
                        spend_committed=0,
                        replan_count=state.replan_count,
                        status="failed",
                        last_error_code="OVER_BUDGET"
                    )

                    return state

            # ------------------------------------------
            # RE-PLAN FAILED
            # ------------------------------------------

            else:

                state.status = "FAILED"

                state.last_error = (
                    "No available alternative "
                    "combination fits within the "
                    "user's budget."
                )

                update_agent_session(
                    session_id=state.session_id,
                    current_step=5,
                    spend_committed=0,
                    replan_count=state.replan_count,
                    status="failed",
                    last_error_code="OVER_BUDGET"
                )

                print("\nRe-planning failed.")
                print(state.last_error)

                return state

        else:

            state.status = "FAILED"

            state.last_error = comparison.get(
                "message",
                "Could not compare available options."
            )

            update_agent_session(
                session_id=state.session_id,
                current_step=5,
                status="failed",
                last_error_code=reason or "COMPARISON_FAILED"
            )

            print("\nComparison failed:")
            print(state.last_error)

            return state

    # ==================================================
    # NORMAL COMPARISON SUCCESS
    # ==================================================

    else:

        state.selected_flight = (
            comparison["recommended_flight"]
        )

        state.selected_hotel = (
            comparison["recommended_hotel"]
        )

        print(
            "Recommended flight:",
            state.selected_flight[
                "flight_number"
            ]
        )

        print(
            "Recommended hotel:",
            state.selected_hotel[
                "hotel_name"
            ]
        )

        print(
            "Flight cost:",
            comparison["flight_cost"],
            trip.currency
        )

        print(
            "Hotel cost:",
            comparison["hotel_cost"],
            trip.currency
        )

        # ------------------------------------------------
        # STEP 6 - CHECK BUDGET
        # ------------------------------------------------

        print("\nSTEP 6: Checking budget...")

        flight_cost = comparison["flight_cost"]
        hotel_cost = comparison["hotel_cost"]

        flight_currency = (
            state.selected_flight["currency"]
        )

        hotel_currency = (
            state.selected_hotel["currency"]
        )

        budget_result = check_budget(
            flight_cost=flight_cost,
            flight_currency=flight_currency,
            hotel_cost=hotel_cost,
            hotel_currency=hotel_currency,
            budget_limit=trip.budget,
            budget_currency=trip.currency
        )

        state.budget_result = budget_result

        print("\nBudget result:")
        print(budget_result)

        if budget_result["status"] == "error":

            state.status = "FAILED"

            state.last_error = (
                budget_result["message"]
            )

            update_agent_session(
                session_id=state.session_id,
                current_step=6,
                status="failed",
                last_error_code="BUDGET_ERROR"
            )

            print("\nBudget check failed.")

            return state

        if not budget_result["within_budget"]:

            state.status = "FAILED"

            state.last_error = (
                "Recommended trip exceeds "
                "the user's budget."
            )

            update_agent_session(
                session_id=state.session_id,
                current_step=6,
                status="failed",
                last_error_code="OVER_BUDGET"
            )

            print(
                "\nRecommended trip is over budget."
            )

            return state

    # ==================================================
    # STEP 7 - PREPARE RECOMMENDATION
    # ==================================================

    print("\nSTEP 7: Preparing recommendation...")

    print("\n" + "=" * 60)
    print("RECOMMENDED TRIP")
    print("=" * 60)

    print(
        "Flight:",
        state.selected_flight[
            "flight_number"
        ]
    )

    print(
        "Airline:",
        state.selected_flight[
            "airline_name"
        ]
    )

    print(
        "Hotel:",
        state.selected_hotel[
            "hotel_name"
        ]
    )

    print(
        "Room:",
        state.selected_hotel[
            "room_type"
        ]
    )

    print(
        "Total:",
        budget_result["total_cost"],
        trip.currency
    )

    print(
        "Remaining:",
        budget_result["remaining"],
        trip.currency
    )

    # ==================================================
    # STEP 8 - CREATE PERSISTENT ITINERARY
    # ==================================================

    print("\nSTEP 8: Creating persistent itinerary...")

    itinerary_id = create_itinerary(
        trip_id=state.trip_id,
        name=(
            f"{trip.origin} to "
            f"{trip.destination} "
            f"Agent Recommendation"
        ),
        total_cost=budget_result["total_cost"],
        currency=trip.currency,
        total_duration_minutes=state.selected_flight[
            "duration_minutes"
        ],
        generated_by="agent",
        status="active"
    )

    print(
        "Itinerary created:",
        itinerary_id
    )

    # ==================================================
    # ADD HOTEL TO ITINERARY
    # ==================================================

    hotel_item_id = add_hotel_item(
        itinerary_id=itinerary_id,
        hotel=state.selected_hotel,
        day_index=1,
        sort_order=1
    )

    print(
        "Hotel itinerary item created:",
        hotel_item_id
    )

    # ==================================================
    # STEP 9 - CREATE BOOKING CART
    # ==================================================

    print("\nSTEP 9: Creating booking cart...")

    state.cart = {
        "flight": state.selected_flight,
        "hotel": state.selected_hotel,
        "itinerary_id": itinerary_id,
        "total_cost": budget_result["total_cost"],
        "currency": trip.currency
    }

    state.requires_confirmation = True
    state.current_step = 9

    # ==================================================
    # UPDATE PERSISTENT AGENT SESSION
    # ==================================================

    update_agent_session(
    session_id=state.session_id,
    current_step=state.current_step,
    spend_committed=budget_result["total_cost"],
    requires_confirmation=True,
    replan_count=state.replan_count,
    status="awaiting_confirmation",
    constraints={
        "origin": trip.origin,
        "destination": trip.destination,
        "travellers": trip.travellers,
        "start_date": trip.start_date,
        "end_date": trip.end_date,
        "budget": trip.budget,
        "currency": trip.currency,
        "selected_flight_id": state.selected_flight[
            "flight_id"
        ],
        "selected_fare_id": state.selected_flight[
            "fare_id"
        ],
        "itinerary_id": itinerary_id
    },
    plan_steps=[
        step["action"]
        for step in state.plan["steps"]
    ]
)

    print("\n" + "=" * 60)
    print("BOOKING CART READY")
    print("=" * 60)

    print(
        "Flight:",
        flight_cost,
        trip.currency
    )

    print(
        "Hotel:",
        hotel_cost,
        trip.currency
    )

    print(
        "Total:",
        budget_result["total_cost"],
        trip.currency
    )

    print(
        "Remaining budget:",
        budget_result["remaining"],
        trip.currency
    )

    # ==================================================
    # STEP 10 - EXPLICIT USER CONFIRMATION
    # ==================================================

    print("\nSTEP 10: Checking user confirmation...")

    if not user_confirmed:

        state.status = "WAITING_FOR_CONFIRMATION"

        SESSIONS[state.session_id] = state

        print("\nNO BOOKING HAS BEEN MADE.")
        print(
            "Waiting for explicit user confirmation..."
        )

        return state

    # ==================================================
    # STEP 11 - CONFIRM BOOKING
    # ==================================================

    print("\nSTEP 11: Confirming booking...")

    booking_result = confirm_booking(
        flight=state.selected_flight,
        hotel=state.selected_hotel,
        total_cost=budget_result["total_cost"],
        currency=trip.currency,
        user_confirmation=user_confirmed
    )

    # ==================================================
    # BOOKING FAILED
    # ==================================================

    if booking_result["status"] != "confirmed":

        state.status = "CANCELLED"
        state.last_error = booking_result[
            "message"
        ]

        update_agent_session(
            session_id=state.session_id,
            current_step=11,
            replan_count=state.replan_count,
            status="cancelled",
            last_error_code="BOOKING_FAILED"
        )

        SESSIONS[state.session_id] = state

        print("\nBooking cancelled.")

        return state

    # ==================================================
    # BOOKING SUCCESS
    # ==================================================

    state.confirmed = True
    state.status = "BOOKED"
    state.current_step = 11
    state.last_error = None

    update_agent_session(
        session_id=state.session_id,
        current_step=state.current_step,
        spend_committed=budget_result["total_cost"],
        requires_confirmation=False,
        replan_count=state.replan_count,
        status="completed"
    )

    SESSIONS[state.session_id] = state

    print("\n" + "=" * 60)
    print("BOOKING CONFIRMED")
    print("=" * 60)

    print(
        "Booking ID:",
        booking_result["booking_id"]
    )

    print(
        "Total:",
        booking_result["total_cost"],
        booking_result["currency"]
    )

    print(
        "Payment status:",
        booking_result["payment_status"]
    )

    print(
        "\nNOTE:",
        booking_result["message"]
    )

    return state