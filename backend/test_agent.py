from backend.agent_controller import run_agent


goal = """
Plan a trip from Bengaluru to Kolkata for 2 people
from September 1 2026 to September 3 2026
with a maximum budget of 25000 INR.
"""


# ============================================================
# TEST 1 - USER DOES NOT CONFIRM
# ============================================================

print("\n" + "=" * 60)
print("TEST 1 - USER DOES NOT CONFIRM")
print("=" * 60)

state = run_agent(
    goal,
    user_confirmed=False
)

print("\nFINAL AGENT STATE")
print("=" * 60)
print("Session ID:", state.session_id)
print("Status:", state.status)
print("Current step:", state.current_step)
print("Requires confirmation:", state.requires_confirmation)
print("Confirmed:", state.confirmed)


# ============================================================
# TEST 2 - USER CONFIRMS
# ============================================================

print("\n" + "=" * 60)
print("TEST 2 - USER CONFIRMS BOOKING")
print("=" * 60)

state = run_agent(
    goal,
    user_confirmed=True
)

print("\nFINAL AGENT STATE")
print("=" * 60)
print("Session ID:", state.session_id)
print("Status:", state.status)
print("Current step:", state.current_step)
print("Requires confirmation:", state.requires_confirmation)
print("Confirmed:", state.confirmed)

if state.cart:
    print("Booking cart exists: True")