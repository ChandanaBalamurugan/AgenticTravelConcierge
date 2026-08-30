def check_budget(
    flight_cost: float,
    flight_currency: str,
    hotel_cost: float,
    hotel_currency: str,
    budget_limit: float,
    budget_currency: str
):
    """
    Validate the total flight + hotel cost
    against the user's spending limit.
    """

    # 1. Currency validation
    if flight_currency.upper() != budget_currency.upper():
        return {
            "status": "error",
            "message": (
                f"Flight currency ({flight_currency}) "
                f"does not match budget currency ({budget_currency})."
            )
        }

    if hotel_currency.upper() != budget_currency.upper():
        return {
            "status": "error",
            "message": (
                f"Hotel currency ({hotel_currency}) "
                f"does not match budget currency ({budget_currency})."
            )
        }

    # 2. Convert values to float
    flight_cost = float(flight_cost)
    hotel_cost = float(hotel_cost)
    budget_limit = float(budget_limit)

    # 3. Calculate total
    total_cost = flight_cost + hotel_cost

    # 4. Calculate remaining amount
    remaining = budget_limit - total_cost

    # 5. Check budget
    if total_cost <= budget_limit:

        return {
            "status": "success",
            "flight_cost": flight_cost,
            "hotel_cost": hotel_cost,
            "total_cost": total_cost,
            "budget_limit": budget_limit,
            "remaining": remaining,
            "currency": budget_currency.upper(),
            "within_budget": True,
            "exceeded_by": 0
        }

    # 6. Over-budget case
    exceeded_by = total_cost - budget_limit

    return {
        "status": "success",
        "flight_cost": flight_cost,
        "hotel_cost": hotel_cost,
        "total_cost": total_cost,
        "budget_limit": budget_limit,
        "remaining": remaining,
        "currency": budget_currency.upper(),
        "within_budget": False,
        "exceeded_by": exceeded_by
    }