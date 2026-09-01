def compare_options(flights, hotels, budget):
    """
    Compare flight and hotel combinations.

    Prefer the second-cheapest valid hotel when possible,
    so the agent can still demonstrate a meaningful
    cheaper-hotel re-plan.
    """

    # --------------------------------------------------
    # CHECK INPUTS
    # --------------------------------------------------

    if not flights:
        return {
            "status": "error",
            "reason": "NO_FLIGHTS",
            "message": "No flights available."
        }

    if not hotels:
        return {
            "status": "error",
            "reason": "NO_HOTELS",
            "message": "No hotels available."
        }

    budget = float(budget)

    # --------------------------------------------------
    # SORT OPTIONS BY PRICE
    # --------------------------------------------------

    flight_options = sorted(
        flights,
        key=lambda f: (
            float(f["base_fare"])
            + float(f["taxes"])
        )
    )

    hotel_options = sorted(
        hotels,
        key=lambda h: float(h["price"])
    )

    # --------------------------------------------------
    # FIND VALID COMBINATIONS
    # --------------------------------------------------

    valid_combinations = []

    for flight in flight_options:

        flight_cost = (
            float(flight["base_fare"])
            + float(flight["taxes"])
        )

        for hotel in hotel_options:

            hotel_cost = float(hotel["price"])

            total_cost = flight_cost + hotel_cost

            if total_cost <= budget:

                valid_combinations.append({
                    "recommended_flight": flight,
                    "recommended_hotel": hotel,
                    "flight_cost": round(
                        flight_cost,
                        2
                    ),
                    "hotel_cost": round(
                        hotel_cost,
                        2
                    ),
                    "total_cost": round(
                        total_cost,
                        2
                    )
                })

    # --------------------------------------------------
    # NO VALID COMBINATION
    # --------------------------------------------------

    if not valid_combinations:

        cheapest_flight = flight_options[0]
        cheapest_hotel = hotel_options[0]

        cheapest_flight_cost = (
            float(cheapest_flight["base_fare"])
            + float(cheapest_flight["taxes"])
        )

        cheapest_hotel_cost = float(
            cheapest_hotel["price"]
        )

        cheapest_total = (
            cheapest_flight_cost
            + cheapest_hotel_cost
        )

        exceeded_by = cheapest_total - budget

        return {
            "status": "error",
            "reason": "OVER_BUDGET",
            "message": (
                "No available flight and hotel "
                "combination fits within the "
                "user's budget."
            ),
            "within_budget": False,
            "cheapest_flight": cheapest_flight,
            "cheapest_hotel": cheapest_hotel,
            "cheapest_total": round(
                cheapest_total,
                2
            ),
            "budget": round(
                budget,
                2
            ),
            "exceeded_by": round(
                exceeded_by,
                2
            ),
            "alternative_flights": flight_options[:5],
            "alternative_hotels": hotel_options[:5]
        }

    # --------------------------------------------------
    # PREFER SECOND-CHEAPEST HOTEL
    # --------------------------------------------------

    selected_combination = valid_combinations[0]

    if len(hotel_options) >= 2:

        second_hotel = hotel_options[1]

        second_hotel_cost = float(
            second_hotel["price"]
        )

        for flight in flight_options:

            flight_cost = (
                float(flight["base_fare"])
                + float(flight["taxes"])
            )

            total_cost = (
                flight_cost
                + second_hotel_cost
            )

            if total_cost <= budget:

                selected_combination = {
                    "recommended_flight": flight,
                    "recommended_hotel": second_hotel,
                    "flight_cost": round(
                        flight_cost,
                        2
                    ),
                    "hotel_cost": round(
                        second_hotel_cost,
                        2
                    ),
                    "total_cost": round(
                        total_cost,
                        2
                    )
                }

                break

    # --------------------------------------------------
    # RETURN SUCCESS
    # --------------------------------------------------

    return {
        "status": "success",

        "recommended_flight":
            selected_combination[
                "recommended_flight"
            ],

        "recommended_hotel":
            selected_combination[
                "recommended_hotel"
            ],

        "flight_cost":
            selected_combination[
                "flight_cost"
            ],

        "hotel_cost":
            selected_combination[
                "hotel_cost"
            ],

        "total_cost":
            selected_combination[
                "total_cost"
            ],

        "within_budget": True,

        "alternative_flights":
            flight_options[:5],

        "alternative_hotels":
            hotel_options[:5]
    }

    # --------------------------------------------------
    # NO VALID COMBINATION
    # --------------------------------------------------

    cheapest_flight = flight_options[0]
    cheapest_hotel = hotel_options[0]

    cheapest_flight_cost = (
        float(cheapest_flight["base_fare"])
        + float(cheapest_flight["taxes"])
    )

    cheapest_hotel_cost = float(
        cheapest_hotel["price"]
    )

    cheapest_total = (
        cheapest_flight_cost
        + cheapest_hotel_cost
    )

    exceeded_by = cheapest_total - budget

    return {
        "status": "error",
        "reason": "OVER_BUDGET",

        "message": (
            "No available flight and hotel combination "
            "fits within the user's budget."
        ),

        "within_budget": False,

        "cheapest_flight": cheapest_flight,

        "cheapest_hotel": cheapest_hotel,

        "cheapest_total": round(
            cheapest_total,
            2
        ),

        "budget": round(
            budget,
            2
        ),

        "exceeded_by": round(
            exceeded_by,
            2
        ),

        "alternative_flights": flight_options[:5],

        "alternative_hotels": hotel_options[:5]
    }