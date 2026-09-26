import asyncio
import os
from typing import TypedDict, Annotated

import psycopg
from langgraph.checkpoint.postgres import PostgresSaver
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, ToolMessage, AIMessage
from langchain_groq import ChatGroq

# from tools.flight_tool import search_flights
# from tools.tavily_tool import search_web

from mcp_client import tavily_mcp_search, aviation_mcp_call, get_airports, get_airlines, weather_mcp_search, forecast_mcp_search, extract_destination


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# --------------------------------
# LLM
# --------------------------------

llm = ChatGroq(
    model=os.getenv("GROQ_MODEL"),
    temperature=0.1,
    max_tokens=800
)


# --------------------------------
# Travel State
# --------------------------------

class TravelState(TypedDict):
    user_query: str

    messages: Annotated[list[BaseMessage], add_messages]

    flight_results: str
    hotel_results: str
    weather_results: str
    itinerary: str
    llm_calls: int


# flight_llm = llm.bind_tools([search_flights])
# hotel_llm = llm.bind_tools([search_web])
# itinerary_llm = llm.bind_tools([search_web])

# Flight Tool Router Prompt
FLIGHT_AGENT_PROMPT = """
You are a travel flight expert.

User Query:
{query}

Airport Information:
{airport_data}

Airline Information:
{airline_data}

Generate:

1. Likely departure airport
2. Likely arrival airport
3. Airlines serving this route
4. Typical flight duration
5. Estimated airfare range
6. Peak season pricing warning
7. Booking advice

Return concise travel guidance.
"""

def flight_agent(state: TravelState):
    print("\nINSIDE FLIGHT AGENT\n")
    query = state["user_query"]
    try:

        airports = asyncio.run(
            aviation_mcp_call(
                "list_airports"
            )
        )

        airlines = asyncio.run(
            aviation_mcp_call(
                "list_airlines"
            )
        )

        prompt = FLIGHT_AGENT_PROMPT.format(
            query=query,
            airport_data=str(airports)[:3000],
            airline_data=str(airlines)[:3000]
        )

        response = llm.invoke([
            SystemMessage(
                content="You are an expert travel flight planner."
            ),
            HumanMessage(content=prompt)
        ])

        flight_data = response.content

    except Exception as e:

        flight_data = f"Flight information unavailable: {str(e)}"

    return {
        "flight_results": flight_data,
        "messages": [
            AIMessage(
                content="Flight recommendations generated"
            )
        ],
        "llm_calls": state.get("llm_calls", 0) + 1
    }



def hotel_agent(state: TravelState):
    query = f"Best hotels for {state['user_query']}"

    hotel_results = asyncio.run(
        tavily_mcp_search(query)
    )

    return {
        "hotel_results": hotel_results,
        "messages": [
            AIMessage(content="Hotel information fetched")
        ],
        "llm_calls": state.get("llm_calls", 0) + 1
    }


def weather_agent(state: TravelState):
    city = extract_destination(state["user_query"])

    weather_data = asyncio.run(
        weather_mcp_search(city)
    )

    forecast_data = asyncio.run(
        forecast_mcp_search(city)
    )

    return {
        "weather_results": f"""
        Current Weather:
        {weather_data}

        Forecast:
        {forecast_data}
        """,
        "messages": [
            AIMessage(
                content="Weather information fetched"
            )
        ]
    }


# Itinerary Agent
def itinerary_agent(state: TravelState):

    prompt = f"""
    Create a travel itinerary.
    User Query:
    {state['user_query']}

    Flight Results:
    {state['flight_results']}

    Hotel Results:
    {state['hotel_results']}

    Weather Information:
    {state['weather_results']}
    """

    response = llm.invoke([
        SystemMessage(
            content="You are an expert travel planner"
        ),
        HumanMessage(content=prompt)
    ])

    return {
        "itinerary": response.content,
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1
    }



# ============================================================
# BUILD GRAPH
# ============================================================

graph = StateGraph(TravelState)


# Add nodes
# graph.add_node("request_parser", request_parser)
graph.add_node("flight_agent", flight_agent)
graph.add_node("hotel_agent", hotel_agent)
graph.add_node("weather_agent", weather_agent)
graph.add_node("itinerary_agent", itinerary_agent)
# graph.add_node("final_agent", final_agent)


# ============================================================
# EDGES
# ============================================================
graph.add_edge(
    START,
    "flight_agent"
)
graph.add_edge(
    "flight_agent",
    "hotel_agent"
)
graph.add_edge(
    "hotel_agent",
    "weather_agent"
)
graph.add_edge(
    "weather_agent",
    "itinerary_agent"
)
graph.add_edge(
    "itinerary_agent",
    END
)


# Persistent connection so both CLI and Streamlit can share the compiled app
_conn = psycopg.connect(DATABASE_URL, autocommit=True)
checkpointer = PostgresSaver(_conn)
checkpointer.setup()

app = graph.compile(checkpointer=checkpointer)

# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    # thread_id = input("Enter your user/thread ID: ").strip() or "default_user"

    user_query = input("Enter your travel request: ").strip()

    if not user_query:
        print("Travel request cannot be empty.")
        exit()

    config = {
        "configurable": {
            # "thread_id": thread_id
            "thread_id": "user_sai"
        }
    }

    result = app.invoke(
        {
            "user_query": user_query,
            "messages": [],
            "flight_results": "",
            "hotel_results": "",
            "weather_results": "",
            "itinerary": "",
            "llm_calls": 0
        },
        config=config
    )

    print("\n")
    print("=" * 60)
    print("FINAL TRAVEL PLAN")
    print("=" * 60)

    print(result["messages"][-1].content)

    print("\n")
    print("LLM Calls:", result["llm_calls"])