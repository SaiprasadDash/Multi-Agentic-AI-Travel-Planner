import os
import requests
from dotenv import load_dotenv
from langchain_core.tools import tool

load_dotenv()

AVIATIONSTACK_API_KEY = os.getenv("AVIATIONSTACK_API_KEY")

@tool
def search_flights(query: str) -> list[dict]:
    
    url = "http://api.aviationstack.com/v1/flights"

    params = {
        "access_key": API_KEY,
        "limit": 5
    }

    response = requests.get(
        url,
        params=params,
        timeout=15
    )

    response.raise_for_status()

    data = response.json()

    flights = []

    for flight in data.get("data", []):

        departure = flight.get(
            "departure", {}
        ).get("airport", "Unknown")

        arrival = flight.get(
            "arrival", {}
        ).get("airport", "Unknown")

        status = flight.get(
            "flight_status", "Unknown"
        )

        flights.append({
            "departure": departure,
            "arrival": arrival,
            "status": status
        })

    return flights