import os
import re
from datetime import date, datetime, timedelta
from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel, Field


# --------------------------------------------------
# Load environment variables
# --------------------------------------------------

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file")


# --------------------------------------------------
# Gemini client
# --------------------------------------------------

client = genai.Client(api_key=api_key)


# --------------------------------------------------
# Structured trip information
# --------------------------------------------------

class TripRequest(BaseModel):

    origin: str | None = Field(
        default=None,
        description="City where the traveller starts the trip"
    )

    destination: str | None = Field(
        default=None,
        description="Destination city"
    )

    travellers: int | None = Field(
        default=None,
        description="Total number of travellers"
    )

    adults: int | None = Field(
        default=None,
        description="Number of adult travellers"
    )

    children: int | None = Field(
        default=None,
        description="Number of child travellers"
    )

    start_date: str | None = Field(
        default=None,
        description="Trip start date in YYYY-MM-DD format"
    )

    end_date: str | None = Field(
        default=None,
        description="Trip end date in YYYY-MM-DD format"
    )

    duration_days: int | None = Field(
        default=None,
        description="Number of days of the trip"
    )

    budget: float | None = Field(
        default=None,
        description="Maximum total trip budget"
    )

    currency: str | None = Field(
        default=None,
        description="Currency of the budget, for example INR"
    )


# --------------------------------------------------
# Parse natural-language travel request
# --------------------------------------------------

def parse_trip_request(user_goal: str) -> TripRequest:

    prompt = f"""
You are a travel requirement extraction assistant.

Extract travel requirements from the user's request.

Return ONLY the fields defined in the TripRequest schema.

IMPORTANT RULES:

1. Never invent missing information.

2. If origin is not mentioned, return null.

3. If destination is not mentioned, return null.

4. If traveller count is not mentioned, return null.

5. If dates are not mentioned, return null.

6. If budget is not mentioned, return null.

7. Convert ALL dates to YYYY-MM-DD format.

8. If the user gives:
   "September 1, 2026 to September 3, 2026"

   return:
   start_date = "2026-09-01"
   end_date = "2026-09-03"

9. If the user gives:
   "from September 1 to September 3"

   return both dates.

10. If the user says:
    "for 3 days starting September 1, 2026"

    then:
    start_date = "2026-09-01"
    end_date = "2026-09-03"

11. For a trip of N days:
    end_date = start_date + (N - 1) days.

12. If both start and end dates are present in the user request,
    extract BOTH.

13. If adults and children are specified,
    calculate total travellers.

14. If only total travellers are specified,
    use that number.

15. If duration is explicitly mentioned,
    extract it if the schema supports it.

16. Do not guess missing values.

17. If the user uses ₹,
    currency = "INR".

18. If another currency is explicitly specified,
    use that currency.

19. Keep destination as a city/place name suitable for database searching.

20. The current year is 2026.

USER REQUEST:

{user_goal}
"""

    # --------------------------------------------------
    # STEP 1: ASK GEMINI TO EXTRACT THE REQUEST
    # --------------------------------------------------

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": TripRequest,
        },
    )

    trip = TripRequest.model_validate_json(response.text)

    # --------------------------------------------------
    # STEP 2: FALLBACK DATE EXTRACTION
    # --------------------------------------------------
    # Gemini sometimes understands the request but returns
    # null dates. We therefore inspect the original request.

    if trip.start_date is None or trip.end_date is None:

        text = user_goal.lower()

        current_year = 2026

        # ----------------------------------------------
        # Pattern:
        # September 1 to September 3
        # ----------------------------------------------

        range_pattern = re.search(
            r"""
            (january|february|march|april|may|june|july|
             august|september|october|november|december)
            \s+(\d{1,2})
            \s*(?:to|-|until)\s*
            (january|february|march|april|may|june|july|
             august|september|october|november|december)
            \s+(\d{1,2})
            (?:\s*,?\s*(\d{4}))?
            """,
            text,
            re.IGNORECASE | re.VERBOSE,
        )

        if range_pattern:

            (
                start_month,
                start_day,
                end_month,
                end_day,
                year,
            ) = range_pattern.groups()

            year = int(year) if year else current_year

            start = datetime.strptime(
                f"{start_month} {start_day} {year}",
                "%B %d %Y",
            ).date()

            end_year = year

            # Handles ranges crossing New Year.
            end = datetime.strptime(
                f"{end_month} {end_day} {end_year}",
                "%B %d %Y",
            ).date()

            if end < start:
                end = end.replace(year=end.year + 1)

            trip.start_date = start.isoformat()
            trip.end_date = end.isoformat()

        # ----------------------------------------------
        # Pattern:
        # "3 days starting September 1"
        # ----------------------------------------------

        else:

            duration_pattern = re.search(
                r"""
                (\d+)\s+days?
                .*?
                (?:starting|from|beginning)
                \s+
                (january|february|march|april|may|june|july|
                 august|september|october|november|december)
                \s+(\d{1,2})
                (?:\s*,?\s*(\d{4}))?
                """,
                text,
                re.IGNORECASE | re.VERBOSE,
            )

            if duration_pattern:

                (
                    duration,
                    start_month,
                    start_day,
                    year,
                ) = duration_pattern.groups()

                year = int(year) if year else current_year

                start = datetime.strptime(
                    f"{start_month} {start_day} {year}",
                    "%B %d %Y",
                ).date()

                end = start + timedelta(days=int(duration) - 1)

                trip.start_date = start.isoformat()
                trip.end_date = end.isoformat()

    return trip