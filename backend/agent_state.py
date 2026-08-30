from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentState:

    session_id: str

    goal: str

    trip: Any = None
    
    trip_id: str | None = None

    plan: dict = field(default_factory=dict)

    flight_results: list = field(default_factory=list)

    hotel_results: list = field(default_factory=list)

    budget_result: dict = field(default_factory=dict)

    selected_flight: dict | None = None

    selected_hotel: dict | None = None

    cart: dict | None = None

    status: str = "STARTING"

    current_step: int = 0

    replan_count: int = 0

    requires_confirmation: bool = False

    confirmed: bool = False

    last_error: str | None = None