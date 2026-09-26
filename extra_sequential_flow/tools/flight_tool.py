import os
import requests
from dotenv import load_dotenv
from langchain_core.tools import tool

load_dotenv()

AVIATIONSTACK_API_KEY = os.getenv("AVIATIONSTACK_API_KEY")

from langchain_core.tools import tool
import requests
import os

API_KEY = os.getenv("AVIATIONSTACK_API_KEY")


@tool
def search_flights(query: str) -> list[dict]:
    """
    Search for flights using AviationStack.

    """

    url = "http://api.aviationstack.com/v1/flights"

    # Example:
    # query = "BBI to DEL"
    # But currently the query is not being used to filter the API.

    params = {
        "access_key": API_KEY,
        "limit": 3
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