from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from backend.agent_controller import run_agent, SESSIONS

from backend.booking import (
    confirm_booking,
    get_existing_booking
)

from backend.replan import (
    replan_hotel,
    get_city_id
)

from backend.tools.flight_search import search_flights
from backend.tools.hotel_search import search_hotels
from backend.tools.budget_check import check_budget

from backend.session_store import (
    load_agent_session,
    update_agent_session
)

from backend.itinerary_store import (
    get_active_itinerary_for_trip
)

from backend.flight_store import (
    get_flight_with_fare
)


# ==========================================================
# REQUEST MODELS
# ==========================================================

class FlightSearchRequest(BaseModel):
    origin: str
    destination: str
    travel_date: str
    max_budget: float | None = None


class HotelSearchRequest(BaseModel):
    city: str
    check_in: str
    check_out: str
    guests: int
    max_budget: float | None = None


class BudgetCheckRequest(BaseModel):
    flight_cost: float
    flight_currency: str
    hotel_cost: float
    hotel_currency: str
    budget_limit: float
    budget_currency: str


class AgentPlanRequest(BaseModel):
    goal: str


class ReplanRequest(BaseModel):
    request: str


app = FastAPI(
    title="Agentic Travel Concierge API",
    description="AI-powered travel planning and booking API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "http://localhost:5173",
    "http://127.0.0.1:5173",
],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================================
# HOME
# ==========================================================

@app.get("/")
def home():
    return {
        "message": "Agentic Travel Concierge API is running"
    }


# ==========================================================
# FLIGHT SEARCH
# ==========================================================

@app.post("/tools/flights/search")
def flight_search(request: FlightSearchRequest):

    try:

        results = search_flights(
            origin=request.origin,
            destination=request.destination,
            travel_date=request.travel_date,
            max_budget=request.max_budget
        )

        return {
            "count": len(results),
            "flights": results
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ==========================================================
# HOTEL SEARCH
# ==========================================================

@app.post("/tools/hotels/search")
def hotel_search(request: HotelSearchRequest):

    try:

        results = search_hotels(
            city=request.city,
            check_in=request.check_in,
            check_out=request.check_out,
            guests=request.guests,
            max_budget=request.max_budget
        )

        return {
            "count": len(results),
            "hotels": results
        }

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ==========================================================
# BUDGET CHECK
# ==========================================================

@app.post("/tools/budget/check")
def budget_check(request: BudgetCheckRequest):

    try:

        result = check_budget(
            flight_cost=request.flight_cost,
            flight_currency=request.flight_currency,
            hotel_cost=request.hotel_cost,
            hotel_currency=request.hotel_currency,
            budget_limit=request.budget_limit,
            budget_currency=request.budget_currency
        )

        return result

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ==========================================================
# MAIN AI AGENT
# ==========================================================

@app.post("/agent/plan")
def agent_plan(request: AgentPlanRequest):

    try:

        # --------------------------------------------------
        # RUN AGENT
        # --------------------------------------------------

        state = run_agent(request.goal)

        # --------------------------------------------------
        # SAFETY CHECK
        # --------------------------------------------------

        if state.trip is None:

            raise HTTPException(
                status_code=400,
                detail=(
                    state.last_error
                    or "Could not understand travel request."
                )
            )

        # --------------------------------------------------
        # TRIP INFORMATION
        # --------------------------------------------------

        trip_data = {
            "origin": state.trip.origin,
            "destination": state.trip.destination,
            "travellers": state.trip.travellers,
            "start_date": state.trip.start_date,
            "end_date": state.trip.end_date,
            "budget": state.trip.budget,
            "currency": state.trip.currency
        }

        # --------------------------------------------------
        # RECOMMENDATION
        # --------------------------------------------------

        recommendation = {
            "flight": state.selected_flight,
            "hotel": state.selected_hotel
        }

        # --------------------------------------------------
        # RETURN RESULT
        # --------------------------------------------------

        return {
    "session_id": state.session_id,
    "status": state.status,
    "goal": state.goal,
    "requires_confirmation": state.requires_confirmation,
    "trip_id": state.trip_id,
    "trip": trip_data,
    "plan_steps": [
        step["action"]
        for step in state.plan.get("steps", [])
    ],
    "recommendation": recommendation,
    "budget": state.budget_result,
    "cart": state.cart,
    "confirmed": state.confirmed,
    "replan_count": state.replan_count,
    "error": state.last_error
}

    # ------------------------------------------------------
    # HTTP EXCEPTIONS
    # ------------------------------------------------------

    except HTTPException:
        raise

    # ------------------------------------------------------
    # OTHER ERRORS
    # ------------------------------------------------------

    except Exception as e:

        print("\nERROR IN /agent/plan:")
        print(str(e))

        error_message = str(e)

        # --------------------------------------------------
        # GEMINI QUOTA ERROR
        # --------------------------------------------------

        if (
            "429" in error_message
            or "RESOURCE_EXHAUSTED" in error_message
        ):

            raise HTTPException(
                status_code=429,
                detail=(
                    "Gemini API quota exceeded. "
                    "Please retry later."
                )
            )

        # --------------------------------------------------
        # GEMINI TEMPORARY UNAVAILABLE
        # --------------------------------------------------

        if (
            "503" in error_message
            or "UNAVAILABLE" in error_message
        ):

            raise HTTPException(
                status_code=503,
                detail=(
                    "The AI model is temporarily unavailable. "
                    "Please retry the request."
                )
            )

        # --------------------------------------------------
        # GENERAL SERVER ERROR
        # --------------------------------------------------

        raise HTTPException(
            status_code=500,
            detail=error_message
        )


# ==========================================================
# CONFIRM BOOKING
# ==========================================================

@app.post("/agent/{session_id}/confirm")
def agent_confirm(session_id: str):

    # ==================================================
    # LOAD SESSION FROM DATABASE
    # ==================================================

    session = load_agent_session(session_id)

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Agent session not found."
        )

    # ==================================================
    # CHECK STATUS
    # ==================================================

    if session["status"] != "awaiting_confirmation":
        raise HTTPException(
            status_code=400,
            detail=(
                "This session is not awaiting confirmation. "
                f"Current status: {session['status']}"
            )
        )

    # ==================================================
    # CHECK CONFIRMATION FLAG
    # ==================================================

    if not bool(session["requires_confirmation"]):
        raise HTTPException(
            status_code=400,
            detail="This session does not require confirmation."
        )

    # ==================================================
    # GET TRIP ID
    # ==================================================

    trip_id = session["trip_id"]

    if not trip_id:
        raise HTTPException(
            status_code=400,
            detail="Trip ID is missing from the session."
        )

    # ==================================================
    # GET SAVED CONSTRAINTS
    # ==================================================

    constraints = session.get("constraints", {})

    flight_id = constraints.get(
        "selected_flight_id"
    )

    fare_id = constraints.get(
        "selected_fare_id"
    )

    itinerary_id = constraints.get(
        "itinerary_id"
    )

    if not flight_id:
        raise HTTPException(
            status_code=400,
            detail="Selected flight ID is missing."
        )

    if not fare_id:
        raise HTTPException(
            status_code=400,
            detail="Selected fare ID is missing."
        )

    # ==================================================
    # LOAD FLIGHT + FARE FROM DATABASE
    # ==================================================

    flight = get_flight_with_fare(
        flight_id=flight_id,
        fare_id=fare_id
    )

    if flight is None:
        raise HTTPException(
            status_code=400,
            detail="Selected flight or fare was not found."
        )

    # ==================================================
    # LOAD ACTIVE ITINERARY
    # ==================================================

    itinerary = get_active_itinerary_for_trip(
        trip_id
    )

    if itinerary is None:
        raise HTTPException(
            status_code=400,
            detail="Active itinerary not found."
        )

    # ==================================================
    # VERIFY ITINERARY ID
    # ==================================================

    if itinerary_id:
        if itinerary["itinerary_id"] != itinerary_id:
            raise HTTPException(
                status_code=400,
                detail="Saved itinerary does not match the active itinerary."
            )

    # ==================================================
    # FIND HOTEL ITEM
    # ==================================================

    hotel_item = None

    for item in itinerary["items"]:

        if (
            item["item_type"] == "hotel"
            and item["entity_type"] == "hotel"
            and item["status"] != "removed"
        ):
            hotel_item = item
            break

    if hotel_item is None:
        raise HTTPException(
            status_code=400,
            detail="Hotel item not found in itinerary."
        )

    # ==================================================
    # RECONSTRUCT HOTEL
    # ==================================================

    hotel_title = hotel_item["title"]

    if " - " in hotel_title:

        hotel_name, room_type = hotel_title.split(
            " - ",
            1
        )

    else:

        hotel_name = hotel_title
        room_type = None

    hotel = {
        "hotel_id": hotel_item["entity_id"],
        "hotel_name": hotel_name,
        "room_type": room_type,
        "city": constraints.get("destination"),
        "price": float(hotel_item["cost"]),
        "currency": hotel_item["currency"],
        "nights": (
            hotel_item.get("nights")
            or (
                __import__("datetime").date.fromisoformat(
                    constraints["end_date"]
                )
                -
                __import__("datetime").date.fromisoformat(
                    constraints["start_date"]
                )
            ).days
        )
    }

    # ==================================================
    # CALCULATE TOTAL
    # ==================================================

    flight_cost = round(
        float(flight["base_fare"])
        + float(flight["taxes"]),
        2
    )

    hotel_cost = round(
        float(hotel["price"]),
        2
    )

    total_cost = round(
        flight_cost + hotel_cost,
        2
    )

    # ==================================================
    # CHECK SPEND CAP
    # ==================================================

    spend_cap = float(
        session["spend_cap"]
    )

    if total_cost > spend_cap:

        raise HTTPException(
            status_code=400,
            detail=(
                "Booking rejected because the current "
                "total exceeds the spend cap."
            )
        )
        
     # ==================================================
    # CHECK FOR EXISTING BOOKING
    # ==================================================

    existing_booking = get_existing_booking(
        trip_id=trip_id,
        itinerary_id=itinerary["itinerary_id"]
    )

    if existing_booking is not None:

        raise HTTPException(
            status_code=400,
            detail=(
                "This trip and itinerary have already "
                "been booked."
            )
        )


    # ==================================================
    # CREATE BOOKING
    # ==================================================

    booking_result = confirm_booking(
        flight=flight,
        hotel=hotel,
        total_cost=total_cost,
        currency=session["currency"],
        user_confirmation=True,
        user_id=session["user_id"],
        trip_id=trip_id,
        itinerary_id=itinerary["itinerary_id"]
    )

    # ==================================================
    # BOOKING FAILED
    # ==================================================

    if booking_result["status"] != "confirmed":

        update_agent_session(
            session_id=session_id,
            requires_confirmation=False,
            status="cancelled",
            last_error_code="BOOKING_FAILED"
        )

        raise HTTPException(
            status_code=400,
            detail=booking_result["message"]
        )

    # ==================================================
    # BOOKING SUCCESS
    # ==================================================

    update_agent_session(
        session_id=session_id,
        current_step=11,
        spend_committed=total_cost,
        requires_confirmation=False,
        status="completed"
    )

    return {
        "session_id": session_id,
        "status": "BOOKED",
        "confirmed": True,
        "booking": booking_result,
        "trip_id": trip_id,
        "itinerary_id": itinerary["itinerary_id"],
        "total_cost": total_cost,
        "currency": session["currency"],
        "error": None
    }


@app.get("/agent/{session_id}/resume")
def agent_resume(session_id: str):

    # ==================================================
    # LOAD PERSISTENT SESSION
    # ==================================================

    session = load_agent_session(session_id)

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Agent session not found."
        )

    # ==================================================
    # LOAD SAVED DATA
    # ==================================================

    constraints = session.get("constraints", {})

    trip_id = session["trip_id"]

    if not trip_id:
        raise HTTPException(
            status_code=400,
            detail="Trip ID is missing."
        )

    flight_id = constraints.get(
        "selected_flight_id"
    )

    fare_id = constraints.get(
        "selected_fare_id"
    )

    itinerary_id = constraints.get(
        "itinerary_id"
    )

    # ==================================================
    # LOAD FLIGHT
    # ==================================================

    flight = None

    if flight_id and fare_id:

        flight = get_flight_with_fare(
            flight_id=flight_id,
            fare_id=fare_id
        )

    # ==================================================
    # LOAD ITINERARY
    # ==================================================

    itinerary = get_active_itinerary_for_trip(
        trip_id
    )

    # ==================================================
    # LOAD HOTEL FROM ITINERARY
    # ==================================================

    hotel = None

    if itinerary is not None:

        for item in itinerary["items"]:

            if (
                item["item_type"] == "hotel"
                and item["entity_type"] == "hotel"
                and item["status"] != "removed"
            ):

                hotel_title = item["title"]

                if " - " in hotel_title:

                    hotel_name, room_type = (
                        hotel_title.split(
                            " - ",
                            1
                        )
                    )

                else:

                    hotel_name = hotel_title
                    room_type = None

                try:

                    from datetime import date

                    start_date = date.fromisoformat(
                        constraints["start_date"]
                    )

                    end_date = date.fromisoformat(
                        constraints["end_date"]
                    )

                    nights = (
                        end_date - start_date
                    ).days

                except Exception:

                    nights = None

                hotel = {
                    "hotel_id": item["entity_id"],
                    "hotel_name": hotel_name,
                    "room_type": room_type,
                    "city": constraints.get(
                        "destination"
                    ),
                    "price": float(item["cost"]),
                    "currency": item["currency"],
                    "nights": nights
                }

                break

    # ==================================================
    # RECONSTRUCT BUDGET
    # ==================================================

    budget_result = {}

    if flight is not None and hotel is not None:

        flight_cost = round(
            float(flight["base_fare"])
            + float(flight["taxes"]),
            2
        )

        hotel_cost = round(
            float(hotel["price"]),
            2
        )

        total_cost = round(
            flight_cost + hotel_cost,
            2
        )

        budget_limit = float(
            session["spend_cap"]
        )

        remaining = round(
            budget_limit - total_cost,
            2
        )

        budget_result = {
            "status": "success",
            "flight_cost": flight_cost,
            "hotel_cost": hotel_cost,
            "total_cost": total_cost,
            "budget_limit": budget_limit,
            "remaining": remaining,
            "currency": session["currency"],
            "within_budget": total_cost <= budget_limit,
            "exceeded_by": (
                round(
                    total_cost - budget_limit,
                    2
                )
                if total_cost > budget_limit
                else 0
            )
        }

    # ==================================================
    # RECONSTRUCT CART
    # ==================================================

    cart = None

    if (
        flight is not None
        and hotel is not None
        and itinerary is not None
        and budget_result
    ):

        cart = {
            "flight": flight,
            "hotel": hotel,
            "itinerary_id": itinerary[
                "itinerary_id"
            ],
            "total_cost": budget_result[
                "total_cost"
            ],
            "currency": session["currency"]
        }

    # ==================================================
    # RETURN COMPLETE RESUMED SESSION
    # ==================================================

    return {
        "session_id": session["session_id"],
        "status": session["status"],
        "goal": session["goal_text"],
        "trip_id": session["trip_id"],
        "current_step": session["current_step"],
        "spend_cap": session["spend_cap"],
        "spend_committed": session["spend_committed"],
        "currency": session["currency"],
        "requires_confirmation": bool(
            session["requires_confirmation"]
        ),
        "replan_count": session["replan_count"],
        "last_error_code": session[
            "last_error_code"
        ],
        "plan_steps": session["plan_steps"],
        "constraints": constraints,

        # NEW
        "recommendation": {
            "flight": flight,
            "hotel": hotel
        },

        # NEW
        "budget": budget_result,

        # NEW
        "cart": cart
    }
    
    
# ==========================================================
# USER REQUESTED RE-PLAN
# ==========================================================

@app.post("/agent/{session_id}/replan")
def agent_replan(
    session_id: str,
    request: ReplanRequest
):

    # --------------------------------------------------
    # LOAD SESSION
    # --------------------------------------------------

    session = load_agent_session(
        session_id
    )

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Agent session not found."
        )

    # --------------------------------------------------
    # ALLOW ONLY ACTIVE TRIPS
    # --------------------------------------------------

    if session["status"] not in [
        "awaiting_confirmation",
        "replanning"
    ]:

        raise HTTPException(
            status_code=400,
            detail=(
                "This trip cannot be re-planned "
                f"because its status is "
                f"{session['status']}."
            )
        )

    # --------------------------------------------------
    # READ USER REQUEST
    # --------------------------------------------------

    user_request = request.request.lower().strip()

    supported_hotel_request = (
        "cheaper hotel" in user_request
        or "cheaper hotel" in user_request.replace(
            "find me",
            ""
        )
        or "make it cheaper" in user_request
        or "hotel cheaper" in user_request
    )

    if not supported_hotel_request:

        raise HTTPException(
            status_code=400,
            detail=(
                "Currently supported re-plan requests "
                "are: 'Find a cheaper hotel' or "
                "'Make it cheaper'."
            )
        )

    # --------------------------------------------------
    # LOAD CONSTRAINTS
    # --------------------------------------------------

    constraints = session.get(
        "constraints",
        {}
    )

    trip_id = session["trip_id"]

    itinerary_id = constraints.get(
        "itinerary_id"
    )

    if not itinerary_id:

        raise HTTPException(
            status_code=400,
            detail="Itinerary ID is missing."
        )

    # --------------------------------------------------
    # LOAD ITINERARY
    # --------------------------------------------------

    itinerary = get_active_itinerary_for_trip(
        trip_id
    )

    if itinerary is None:

        raise HTTPException(
            status_code=400,
            detail="Active itinerary not found."
        )

    # --------------------------------------------------
    # FIND CURRENT HOTEL
    # --------------------------------------------------

    current_hotel = None

    for item in itinerary["items"]:

        if (
            item["item_type"] == "hotel"
            and item["entity_type"] == "hotel"
            and item["status"] != "removed"
        ):

            title = item["title"]

            if " - " in title:

                hotel_name, room_type = title.split(
                    " - ",
                    1
                )

            else:

                hotel_name = title
                room_type = None

            current_hotel = {
                "hotel_id": item["entity_id"],
                "hotel_name": hotel_name,
                "room_type": room_type,
                "price": float(item["cost"]),
                "currency": item["currency"],
                "nights": (
                    (
                        __import__("datetime").date.fromisoformat(
                            constraints["end_date"]
                        )
                        -
                        __import__("datetime").date.fromisoformat(
                            constraints["start_date"]
                        )
                    ).days
                )
            }

            break

    if current_hotel is None:

        raise HTTPException(
            status_code=400,
            detail="Current hotel was not found."
        )

    # --------------------------------------------------
    # CURRENT TOTAL
    # --------------------------------------------------

    current_total = float(
        session["spend_committed"]
    )

    # --------------------------------------------------
    # UPDATE STATUS
    # --------------------------------------------------

    new_replan_count = (
    int(session["replan_count"] or 0) + 1
)
    
    update_agent_session(
        session_id=session_id,
        status="replanning",
        replan_count=new_replan_count
    )

    # --------------------------------------------------
    # RUN RE-PLAN
    # --------------------------------------------------
    city_id = get_city_id(
        constraints["destination"]
    )

    if city_id is None:
        update_agent_session(
            session_id=session_id,
            status="awaiting_confirmation"
        )

        raise HTTPException(
            status_code=400,
            detail="Destination city was not found."
        )

    flight_cost = round(
        current_total -
        float(current_hotel["price"]),
        2
    )

    replanned = replan_hotel(
        city_id=city_id,
        check_in=constraints["start_date"],
        check_out=constraints["end_date"],
        guests=int(constraints["travellers"]),
        current_hotel=current_hotel,
        itinerary_id=itinerary_id,
        current_total=current_total,
        flight_cost=flight_cost
    )

    # --------------------------------------------------
    # RE-PLAN FAILED
    # --------------------------------------------------

    if replanned["status"] != "success":

        update_agent_session(
            session_id=session_id,
            status="awaiting_confirmation"
        )

        raise HTTPException(
            status_code=400,
            detail=replanned["message"]
        )

    # --------------------------------------------------
    # UPDATE SESSION CONSTRAINTS
    # --------------------------------------------------

    constraints["selected_hotel_id"] = replanned[
        "hotel"
    ]["hotel_id"]

    constraints["itinerary_id"] = itinerary_id

    new_replan_count = (
        int(session["replan_count"] or 0) + 1
    )

    update_agent_session(
        session_id=session_id,
        current_step=9,
        spend_committed=replanned["new_total"],
        requires_confirmation=True,
        replan_count=new_replan_count,
        status="awaiting_confirmation",
        constraints=constraints
    )

    # --------------------------------------------------
    # RETURN NEW PLAN
    # --------------------------------------------------

    return {
        "session_id": session_id,
        "status": "REPLAN_SUCCESS",
        "message": "Trip successfully re-planned.",
        "change": "cheaper_hotel",

        "old_hotel_price": replanned[
            "old_hotel_price"
        ],

        "new_hotel_price": replanned[
            "new_hotel_price"
        ],

        "old_total": replanned[
            "old_total"
        ],

        "new_total": replanned[
            "new_total"
        ],

        "saved": replanned[
            "saved"
        ],

        "hotel": replanned[
            "hotel"
        ],

        "hotel_item_id": replanned[
            "hotel_item_id"
        ],

        "requires_confirmation": True,

        "replan_count": new_replan_count
    }