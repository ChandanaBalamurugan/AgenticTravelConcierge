from budget_check import check_budget


# Test 1: Within budget
result = check_budget(
    flight_cost=8400,
    flight_currency="INR",
    hotel_cost=12600,
    hotel_currency="INR",
    budget_limit=25000,
    budget_currency="INR"
)

print("TEST 1 - WITHIN BUDGET")
print(result)


# Test 2: Over budget
result = check_budget(
    flight_cost=12000,
    flight_currency="INR",
    hotel_cost=15000,
    hotel_currency="INR",
    budget_limit=25000,
    budget_currency="INR"
)

print("\nTEST 2 - OVER BUDGET")
print(result)


# Test 3: Currency mismatch
result = check_budget(
    flight_cost=8400,
    flight_currency="INR",
    hotel_cost=12600,
    hotel_currency="CHF",
    budget_limit=25000,
    budget_currency="INR"
)

print("\nTEST 3 - CURRENCY MISMATCH")
print(result)