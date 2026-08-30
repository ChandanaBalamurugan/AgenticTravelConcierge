import os

from dotenv import load_dotenv
from google import genai


# Load variables from .env
load_dotenv()

# Get Gemini API key
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found")


# Create Gemini client
client = genai.Client(api_key=api_key)


# Send a simple test request
response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents="Explain in one sentence what an AI travel agent does."
)


print("Gemini response:")
print(response.text)