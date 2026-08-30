import { useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [goal, setGoal] = useState(
    "Plan a 3 day trip from Bengaluru to Kolkata for 2 people from September 1 to September 3 with a budget of 25000 INR"
  );

  const [resumeId, setResumeId] = useState("");

  const [result, setResult] = useState(null);
  const [booking, setBooking] = useState(null);

  const [loading, setLoading] = useState(false);
  const [confirming, setConfirming] = useState(false);

  const [error, setError] = useState("");
  const [replanRequest, setReplanRequest] = useState("");
const [replanning, setReplanning] = useState(false);
const [replanMessage, setReplanMessage] = useState("");

  // ==================================================
  // PLAN TRIP
  // ==================================================

  const planTrip = async () => {
    if (!goal.trim()) {
      setError("Please describe your trip.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);
    setBooking(null);

    try {
      const response = await fetch(
        `${API_URL}/agent/plan`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            goal: goal.trim(),
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Failed to plan the trip."
        );
      }

      setResult(data);

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // ==================================================
  // RESUME SESSION
  // ==================================================

  const resumeSession = async () => {
    if (!resumeId.trim()) {
      setError("Please enter a session ID.");
      return;
    }

    setLoading(true);
    setError("");
    setBooking(null);

    try {
      const response = await fetch(
        `${API_URL}/agent/${resumeId.trim()}/resume`
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Could not resume this session."
        );
      }

      setResult({
        session_id: data.session_id,
        status: data.status,
        goal: data.goal,
        trip_id: data.trip_id,
        current_step: data.current_step,
        requires_confirmation:
          data.requires_confirmation,
        replan_count: data.replan_count,
        plan_steps: data.plan_steps || [],
        trip: data.constraints,
        recommendation:
          data.recommendation || {
            flight: null,
            hotel: null,
          },
        budget: data.budget || {},
        cart: data.cart || null,
        error: null,
      });

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const replanTrip = async () => {
  if (!replanRequest.trim()) {
    setError("Please describe what you want to change.");
    return;
  }

  if (!result?.session_id) {
    setError("Session ID is missing.");
    return;
  }

  setReplanning(true);
  setError("");
  setReplanMessage("");

  try {
    const response = await fetch(
      `${API_URL}/agent/${result.session_id}/replan`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          request: replanRequest.trim(),
        }),
      }
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(
        data.detail || "Re-planning failed."
      );
    }

    // --------------------------------------------
    // Update hotel
    // --------------------------------------------

    const oldHotelCost =
      Number(data.old_hotel_price);

    const newHotelCost =
      Number(data.new_hotel_price);

    const newTotal =
      Number(data.new_total);

    const budgetLimit =
      Number(
        result.budget?.budget_limit ??
        result.trip?.budget ??
        0
      );

    const newRemaining =
      budgetLimit - newTotal;

    // --------------------------------------------
    // Update React result
    // --------------------------------------------

    setResult((previous) => ({
      ...previous,

      status: "awaiting_confirmation",

      requires_confirmation: true,

      replan_count: data.replan_count,

      recommendation: {
        ...previous.recommendation,

        hotel: data.hotel,
      },

      budget: {
        ...previous.budget,

        hotel_cost: newHotelCost,

        total_cost: newTotal,

        remaining: newRemaining,

        within_budget:
          newTotal <= budgetLimit,

        budget_limit: budgetLimit,
      },
    }));

    // --------------------------------------------
    // Message shown to user
    // --------------------------------------------

    setReplanMessage(
      `Trip re-planned successfully. You save ₹${Number(
        data.saved
      ).toLocaleString("en-IN", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      })}.`
    );

    setReplanRequest("");

  } catch (err) {
    setError(err.message);
  } finally {
    setReplanning(false);
  }
};

  // ==================================================
  // CONFIRM BOOKING
  // ==================================================

  const confirmBooking = async () => {
    if (!result?.session_id) {
      setError("Session ID is missing.");
      return;
    }

    setConfirming(true);
    setError("");

    try {
      const response = await fetch(
        `${API_URL}/agent/${result.session_id}/confirm`,
        {
          method: "POST",
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Booking failed."
        );
      }

      setBooking(data);

      setResult((previous) => ({
        ...previous,
        status: data.status,
        requires_confirmation: false,
      }));

    } catch (err) {
      setError(err.message);
    } finally {
      setConfirming(false);
    }
  };

  // ==================================================
  // RESET
  // ==================================================

  const startNewTrip = () => {
    setResult(null);
    setBooking(null);
    setError("");
    setResumeId("");
  };

  // ==================================================
  // HELPERS
  // ==================================================

  const formatMoney = (value) => {
    const number = Number(value);

    if (!Number.isFinite(number)) {
      return "₹—";
    }

    return `₹${number.toLocaleString("en-IN", {
      maximumFractionDigits: 2,
    })}`;
  };

  const status = result?.status?.toLowerCase() || "";

  const isFailed = status === "failed";

  const isWaiting =
    status === "awaiting_confirmation";

  const isBooked =
    status === "booked" ||
    status === "completed";

  const showConfirmation =
    result?.requires_confirmation === true &&
    isWaiting &&
    !isFailed &&
    !isBooked;

  return (
    <div className="app">

      {/* ==================================================
          HEADER
          ================================================== */}

      <header className="header">

        <div className="brand">
          <div className="brand-logo">
            ✈
          </div>

          <div>
            <h1>AI Travel Concierge</h1>
            <p>
              Intelligent planning, budgeting and booking
            </p>
          </div>
        </div>

        <div className="header-badge">
          <span></span>
          AI Agent
        </div>

      </header>

      <main className="container">

        {/* ==================================================
            HERO
            ================================================== */}

        {!result && (
          <section className="hero">

            <div className="hero-content">

              <div className="hero-tag">
                SMART TRAVEL PLANNER
              </div>

              <h2>
                Plan your entire trip
                <br />
                with one request.
              </h2>

              <p>
                Tell the agent where you want to go,
                your dates, travellers and budget.
                It searches, compares and plans the
                best available option.
              </p>

            </div>

          </section>
        )}

        {/* ==================================================
            ACTION AREA
            ================================================== */}

        {!result && (
          <section className="action-grid">

            {/* PLAN */}
            <div className="action-card main-action">

              <div className="action-header">
                <div>
                  <span className="step-label">
                    01
                  </span>

                  <h3>Plan a new trip</h3>
                </div>

                <span className="action-icon">
                  🧭
                </span>
              </div>

              <p className="action-description">
                Describe your journey naturally.
              </p>

              <textarea
                value={goal}
                onChange={(e) =>
                  setGoal(e.target.value)
                }
                placeholder="Example: Plan a 3 day trip from Bengaluru to Kolkata..."
              />

              <button
                className="primary-button"
                onClick={planTrip}
                disabled={loading}
              >
                {loading ? (
                  <>
                    <span className="spinner"></span>
                    Planning...
                  </>
                ) : (
                  <>
                    Plan My Trip
                    <span>→</span>
                  </>
                )}
              </button>

            </div>

            {/* RESUME */}
            <div className="action-card">

              <div className="action-header">

                <div>
                  <span className="step-label">
                    02
                  </span>

                  <h3>Resume a trip</h3>
                </div>

                <span className="action-icon">
                  ↻
                </span>

              </div>

              <p className="action-description">
                Continue a saved trip using its session ID.
              </p>

              <input
                value={resumeId}
                onChange={(e) =>
                  setResumeId(e.target.value)
                }
                placeholder="AGT_XXXXXXXX"
              />

              <button
                className="secondary-button"
                onClick={resumeSession}
                disabled={loading}
              >
                {loading
                  ? "Loading..."
                  : "Resume Trip"}
              </button>

              <p className="resume-note">
                Your session is stored persistently.
              </p>

            </div>

          </section>
        )}

        {/* ==================================================
            ERROR
            ================================================== */}

        {error && (
          <div className="alert">

            <div className="alert-icon">
              !
            </div>

            <div>
              <strong>
                Unable to complete request
              </strong>

              <p>{error}</p>
            </div>

          </div>
        )}

        {/* ==================================================
            RESULT
            ================================================== */}

        {result && (

          <section className="result-card">

            {/* RESULT TOP */}
            <div className="result-top">

              <div>
                <span className="result-label">
                  TRAVEL PLAN
                </span>

                <h2>
                  {isFailed
                    ? "Trip could not be planned"
                    : isBooked
                    ? "Trip booked successfully"
                    : "Your trip is ready"}
                </h2>
              </div>

             

              <div
                className={`status-badge ${
                  isFailed
                    ? "failed"
                    : isBooked
                    ? "booked"
                    : "waiting"
                }`}
              >
                <span></span>
                {result.status}
              </div>

            </div>

            <div className="session-display">
  <div>
    <span>SESSION ID</span>
    <strong>{result.session_id}</strong>
  </div>

  <button
    className="copy-button"
    onClick={() =>
      navigator.clipboard.writeText(
        result.session_id
      )
    }
  >
    Copy
  </button>
</div>

            {/* SESSION */}

            
            <div className="session-row">

  <div>
    <small>TRIP ID</small>
    <strong>
      {result.trip_id || "—"}
    </strong>
  </div>

  {result.replan_count > 0 && (
    <div>
      <small>RE-PLANS</small>
      <strong>
        {result.replan_count}
      </strong>
    </div>
  )}

  <button
    className="new-trip-button"
    onClick={startNewTrip}
  >
    + New Trip
  </button>

</div>

            {/* ==================================================
                AGENT PLAN
                ================================================== */}

            {result.plan_steps?.length > 0 && (
              <div className="section">

                <div className="section-heading">

                  <div>
                    <span>01</span>
                    <h3>Agent plan</h3>
                  </div>

                  {result.replan_count > 0 && (
                    <div className="replan-badge">
                      🔄 {result.replan_count} re-plan
                      {result.replan_count > 1
                        ? "s"
                        : ""}
                    </div>
                  )}

                </div>

                <div className="agent-steps">

                  {result.plan_steps.map(
                    (step, index) => {

                      const waitingStep =
                        step
                          .toLowerCase()
                          .includes("wait");

                      const skipped =
                        isFailed && waitingStep;

                      return (
                        <div
                          className={`agent-step ${
                            skipped
                              ? "skipped"
                              : "completed"
                          }`}
                          key={index}
                        >

                          <div className="step-check">
                            {skipped ? "–" : "✓"}
                          </div>

                          <span>
                            {step}
                          </span>

                        </div>
                      );
                    }
                  )}

                  {isFailed && (
                    <div className="agent-step failed-step">

                      <div className="step-check">
                        !
                      </div>

                      <span>
                        No valid travel combination found
                      </span>

                    </div>
                  )}

                </div>

              </div>
            )}

            {/* ==================================================
                FAILED
                ================================================== */}

            {isFailed && (
              <div className="failure-box">

                <div className="failure-icon">
                  !
                </div>

                <div>
                  <h3>
                    We couldn't find a suitable plan
                  </h3>

                  <p>
                    {result.error ||
                      "No available combination fits within the selected budget."}
                  </p>
                </div>

              </div>
            )}

            {/* ==================================================
                TRIP SUMMARY
                ================================================== */}

            {result.trip && (
              <div className="section">

                <div className="section-heading">
                  <div>
                    <span>02</span>
                    <h3>Trip summary</h3>
                  </div>
                </div>

                <div className="trip-summary">

                  <div className="route">
                    <div>
                      <small>FROM</small>
                      <strong>
                        {result.trip.origin}
                      </strong>
                    </div>

                    <div className="route-arrow">
                      →
                    </div>

                    <div>
                      <small>TO</small>
                      <strong>
                        {result.trip.destination}
                      </strong>
                    </div>
                  </div>

                  <div className="summary-divider"></div>

                  <div className="summary-stats">

                    <div>
                      <small>DATES</small>
                      <strong>
                        {result.trip.start_date}
                        {" → "}
                        {result.trip.end_date}
                      </strong>
                    </div>

                    <div>
                      <small>TRAVELLERS</small>
                      <strong>
                        {result.trip.travellers}
                      </strong>
                    </div>

                    <div>
                      <small>BUDGET</small>
                      <strong>
                        {formatMoney(
                          result.trip.budget
                        )}
                      </strong>
                    </div>

                  </div>

                </div>

              </div>
            )}

            {/* ==================================================
                FLIGHT + HOTEL
                ================================================== */}

            {!isFailed &&
              result.recommendation && (

                <div className="section">

                  <div className="section-heading">
                    <div>
                      <span>03</span>
                      <h3>Recommended options</h3>
                    </div>
                  </div>

                  <div className="options-grid">

                    {/* FLIGHT */}
                    {result.recommendation.flight && (

                      <div className="option-card">

                        <div className="option-top">
                          <span>
                            ✈ FLIGHT
                          </span>

                          <span className="available">
                            Available
                          </span>
                        </div>

                        <h3>
                          {
                            result.recommendation
                              .flight.airline_name
                          }
                        </h3>

                        <p>
                          Flight{" "}
                          {
                            result.recommendation
                              .flight.flight_number
                          }
                        </p>

                        <div className="route-display">

                          <div>
                            <strong>
                              {
                                result.recommendation
                                  .flight.origin_iata
                              }
                            </strong>

                            <small>
                              Origin
                            </small>
                          </div>

                          <div className="route-middle">
                            ─── ✈ ───
                          </div>

                          <div>
                            <strong>
                              {
                                result.recommendation
                                  .flight.destination_iata
                              }
                            </strong>

                            <small>
                              Destination
                            </small>
                          </div>

                        </div>

                        <div className="option-footer">

                          <div>
                            <small>PRICE</small>

                            <strong>
                              {formatMoney(
                                result.budget?.flight_cost
                              )}
                            </strong>
                          </div>

                          <div>
                            <small>DURATION</small>

                            <strong>
                              {
                                result.recommendation
                                  .flight.duration_minutes
                              }{" "}
                              min
                            </strong>
                          </div>

                        </div>

                      </div>
                    )}

                    {/* HOTEL */}
                    {result.recommendation.hotel && (

                      <div className="option-card">

                        <div className="option-top">

                          <span>
                            🏨 HOTEL
                          </span>

                          <span className="available">
                            Available
                          </span>

                        </div>

                        <h3>
                          {
                            result.recommendation
                              .hotel.hotel_name
                          }
                        </h3>

                        <p>
                          {
                            result.recommendation
                              .hotel.room_type
                          }
                        </p>

                        <div className="hotel-details">

                          <div className="hotel-symbol">
                            🏨
                          </div>

                          <div>
                            <strong>
                              {
                                result.recommendation
                                  .hotel.nights
                              }{" "}
                              nights
                            </strong>

                            <small>
                              {
                                result.recommendation
                                  .hotel.check_in
                              }
                              {" → "}
                              {
                                result.recommendation
                                  .hotel.check_out
                              }
                            </small>
                          </div>

                        </div>

                        <div className="option-footer">

                          <div>
                            <small>TOTAL STAY</small>

                            <strong>
                              {formatMoney(
                                result.budget?.hotel_cost
                              )}
                            </strong>
                          </div>

                          <div>
                            <small>GUESTS</small>

                            <strong>
                              {
                                result.trip
                                  ?.travellers
                              }
                            </strong>
                          </div>

                        </div>

                      </div>
                    )}

                  </div>

                </div>
              )}

            {/* ==================================================
                BUDGET
                ================================================== */}

            {!isFailed &&
              result.budget &&
              Object.keys(result.budget).length > 0 && (

                <div className="section">

                  <div className="section-heading">

                    <div>
                      <span>04</span>
                      <h3>Budget</h3>
                    </div>

                    <span
                      className={
                        result.budget.within_budget
                          ? "budget-safe"
                          : "budget-danger"
                      }
                    >
                      {result.budget.within_budget
                        ? "✓ Within budget"
                        : "✕ Over budget"}
                    </span>

                  </div>

                  <div className="budget-card">

                    <div>
                      <small>TOTAL TRIP COST</small>

                      <strong>
                        {formatMoney(
                          result.budget.total_cost
                        )}
                      </strong>
                    </div>

                    <div>
                      <small>REMAINING</small>

                      <strong className="remaining">
                        {formatMoney(
                          result.budget.remaining
                        )}
                      </strong>
                    </div>

                    <div>
                      <small>BUDGET LIMIT</small>

                      <strong>
                        {formatMoney(
                          result.budget.budget_limit
                        )}
                      </strong>
                    </div>

                  </div>

                </div>
              )}

              {showConfirmation && (
  <div className="replan-box">

    <div className="replan-heading">

      <div>
        <span>05</span>

        <div>
          <span className="replan-label">
            NEED A CHANGE?
          </span>

          <h3>
            Ask the agent to re-plan.
          </h3>

          <p>
            Change your hotel or ask the agent to find
            a better option.
          </p>
        </div>
      </div>

      <span className="replan-icon">
        🔄
      </span>

    </div>

    <div className="replan-actions">

      <input
        type="text"
        value={replanRequest}
        onChange={(e) =>
          setReplanRequest(e.target.value)
        }
        placeholder="Example: Find a cheaper hotel"
      />

      <button
        className="replan-button"
        onClick={replanTrip}
        disabled={replanning}
      >
        {replanning ? (
          <>
            <span className="spinner"></span>
            Re-planning...
          </>
        ) : (
          <>
            🔄 Re-plan Trip
          </>
        )}
      </button>

    </div>

    <div className="replan-examples">

      <button
        onClick={() =>
          setReplanRequest(
            "Find a cheaper hotel"
          )
        }
      >
        Find a cheaper hotel
      </button>

      <button
        onClick={() =>
          setReplanRequest(
            "Find a different hotel"
          )
        }
      >
        Find a different hotel
      </button>

      <button
        onClick={() =>
          setReplanRequest(
            "Make the trip cheaper"
          )
        }
      >
        Make the trip cheaper
      </button>

    </div>

    {replanMessage && (
      <div className="replan-success">
        ✓ {replanMessage}
      </div>
    )}

  </div>
)}

            {/* ==================================================
                CONFIRMATION
                ================================================== */}

            {showConfirmation && (
              <div className="confirmation">

                <div>
                  <span>
                    READY TO BOOK
                  </span>

                  <h3>
                    Your trip is within budget.
                  </h3>

                  <p>
                    Review the details above.
                    Booking will only happen after
                    you explicitly confirm.
                  </p>
                </div>

                <button
                  className="confirm-button"
                  onClick={confirmBooking}
                  disabled={confirming}
                >
                  {confirming ? (
                    <>
                      <span className="spinner dark"></span>
                      Confirming...
                    </>
                  ) : (
                    <>
                      Confirm Booking
                      <span>→</span>
                    </>
                  )}
                </button>

              </div>
            )}

            {/* ==================================================
                BOOKING SUCCESS
                ================================================== */}

            {booking && (

              <div className="booking-success">

                <div className="success-icon">
                  ✓
                </div>

                <div className="success-main">

                  <span>
                    BOOKING CONFIRMED
                  </span>

                  <h2>
                    Your trip is booked!
                  </h2>

                  <div className="booking-grid">

                    <div>
                      <small>BOOKING ID</small>
                      <strong>
                        {
                          booking.booking
                            ?.booking_id
                        }
                      </strong>
                    </div>

                    <div>
                      <small>REFERENCE</small>
                      <strong>
                        {
                          booking.booking
                            ?.booking_reference
                        }
                      </strong>
                    </div>

                    <div>
                      <small>TOTAL</small>
                      <strong>
                        {formatMoney(
                          booking.total_cost
                        )}
                      </strong>
                    </div>

                    <div>
                      <small>STATUS</small>
                      <strong>
                        Confirmed
                      </strong>
                    </div>

                  </div>

                </div>

              </div>
            )}

          </section>
        )}

      </main>

      {/* ==================================================
          FOOTER
          ================================================== */}

      <footer className="footer">
        <span>AI Travel Concierge</span>
        <span>•</span>
        <span>Agent-powered travel planning</span>
      </footer>

    </div>



  );
}

export default App;