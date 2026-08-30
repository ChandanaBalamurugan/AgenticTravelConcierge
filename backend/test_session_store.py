from backend.session_store import (
    save_agent_session,
    load_agent_session,
    update_agent_session
)


SESSION_ID = "AGT_TEST_001"


# ---------------------------------------------
# SAVE
# ---------------------------------------------

save_agent_session(
    session_id=SESSION_ID,
    goal_text="Test trip from Bengaluru to Kolkata",
    constraints={
        "origin": "Bengaluru",
        "destination": "Kolkata",
        "travellers": 2,
        "start_date": "2026-09-01",
        "end_date": "2026-09-03"
    },
    plan_steps=[
        "Search flights",
        "Search hotels",
        "Check budget",
        "Prepare cart"
    ],
    current_step=4,
    spend_cap=25000,
    spend_committed=13007.19,
    currency="INR",
    requires_confirmation=True,
    status="awaiting_confirmation"
)


# ---------------------------------------------
# LOAD
# ---------------------------------------------

session = load_agent_session(SESSION_ID)

print("\nLOADED SESSION:")
print(session)


# ---------------------------------------------
# UPDATE
# ---------------------------------------------

update_agent_session(
    session_id=SESSION_ID,
    status="booked",
    current_step=5,
    spend_committed=13007.19
)


# ---------------------------------------------
# LOAD AGAIN
# ---------------------------------------------

updated_session = load_agent_session(SESSION_ID)

print("\nUPDATED SESSION:")
print(updated_session)