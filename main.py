import os
from typing import TypedDict, Annotated

import psycopg
from langgraph.checkpoint.postgres import PostgresSaver
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, ToolMessage, AIMessage
from langchain_groq import ChatGroq

from tools.flight_tool import search_flights
from tools.tavily_tool import search_web


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
    itinerary: str
    llm_call: int


flight_llm = llm.bind_tools([search_flights])
hotel_llm = llm.bind_tools([search_web])
itinerary_llm = llm.bind_tools([search_web])


def flight_agent(state: TravelState):

    system_prompt = """
You are a Flight Agent in an AI Travel Planner.

Your job is to find flight information based on the user's travel request.

Use the search_flights tool when flight information is required.

The tool returns only:
- departure
- arrival
- status

Do not invent flight information.

After receiving the tool result, provide a concise summary of the
available flights.
"""

    local_messages = [
        ("system", system_prompt),
        ("human", state["user_query"]),
    ]

    response = flight_llm.invoke(local_messages)
    local_messages.append(response)

    if response.tool_calls:
        for tool_call in response.tool_calls:
            if tool_call["name"] == "search_flights":
                result = search_flights.invoke(tool_call["args"])
                local_messages.append(
                    ToolMessage(content=str(result), tool_call_id=tool_call["id"])
                )
        final = flight_llm.invoke(local_messages)
        summary = final.content
        calls = 2
    else:
        summary = response.content
        calls = 1

    return {
        "flight_results": summary,
        "messages": [AIMessage(content=f"[Flight Agent] {summary}")],
        "llm_call": state["llm_call"] + calls
    }



def hotel_agent(state: TravelState):
    """
    Hotel Agent:
    - Reads the user's travel request
    - Searches the web for relevant hotels
    - Summarizes the hotel information
    - Stores the result in hotel_results
    """

    system_prompt = """
You are the Hotel Agent in an AI Travel Planner.

Your job is to find relevant hotel information based on the
user's travel request.

Use the search_web tool when hotel information is required.

When searching:
- Identify the destination from the user's request.
- Search for relevant hotels in that destination.
- Consider the user's dates, number of travelers, and preferences
  if they are available.
- Make the search query specific.
- Do not invent hotel information.
- Only use information returned by the search tool.

The search_web tool returns:
- title
- url
- snippet

After receiving the search results, summarize the most relevant
hotel options for the user.

Keep the response concise and useful.
"""

    local_messages = [
        ("system", system_prompt),
        ("human", state["user_query"]),
    ]

    response = hotel_llm.invoke(local_messages)
    local_messages.append(response)

    if response.tool_calls:
        for tool_call in response.tool_calls:
            if tool_call["name"] == "search_web":
                result = search_web.invoke(tool_call["args"])
                local_messages.append(
                    ToolMessage(content=str(result), tool_call_id=tool_call["id"])
                )
        final = hotel_llm.invoke(local_messages)
        summary = final.content
        calls = 2
    else:
        summary = response.content
        calls = 1

    return {
        "hotel_results": summary,
        "messages": [AIMessage(content=f"[Hotel Agent] {summary}")],
        "llm_call": state["llm_call"] + calls
    }


def itinerary_agent(state: TravelState):
    """
    Itinerary Agent:
    - Reads the user's travel request
    - Searches the web for destination information
    - Creates a travel itinerary
    - Stores the result in itinerary
    """

    system_prompt = """
You are the Itinerary Agent in an AI Travel Planner.

Your job is to create a useful travel itinerary based on the
user's travel request.

Use the search_web tool when you need current or relevant
destination information.

When searching:
- Identify the destination from the user's request.
- Identify the trip duration if provided.
- Search for important attractions, activities, and places to visit.
- Consider the user's preferences if they are available.
- Make the search query specific.
- Do not invent information.
- Only use information returned by the search tool.

The search_web tool returns:
- title
- url
- snippet

Create a practical itinerary based on the available search results.

The itinerary should include:
- Day-by-day activities
- Important places to visit
- Suggested activities
- Relevant travel information

Keep the itinerary concise and useful.
"""

    local_messages = [
        ("system", system_prompt),
        ("human", state["user_query"]),
    ]

    response = itinerary_llm.invoke(local_messages)
    local_messages.append(response)

    if response.tool_calls:
        for tool_call in response.tool_calls:
            if tool_call["name"] == "search_web":
                result = search_web.invoke(tool_call["args"])
                local_messages.append(
                    ToolMessage(content=str(result), tool_call_id=tool_call["id"])
                )
        final = itinerary_llm.invoke(local_messages)
        summary = final.content
        calls = 2
    else:
        summary = response.content
        calls = 1

    return {
        "itinerary": summary,
        "messages": [AIMessage(content=f"[Itinerary Agent] {summary}")],
        "llm_call": state["llm_call"] + calls
    }


def final_agent(state: TravelState):
    """
    Final Response Agent:
    - Reads the results from Flight, Hotel, and Itinerary agents
    - Combines them
    - Generates the final travel plan
    """

    system_prompt = """
You are the Final Response Agent in an AI Travel Planner.

Your job is to combine the results produced by the specialized
Flight, Hotel, and Itinerary agents.

Create one clear and useful travel plan for the user.

Use only the information provided by the agents.
Do not invent flight, hotel, or itinerary information.

Organize the response into:

1. Flight Information
2. Hotel Information
3. Day-by-Day Itinerary
4. Important Notes

If information is unavailable, clearly mention that it is unavailable.

Keep the response concise, structured, and easy to understand.
"""

    prompt = f"""
User Request:
{state["user_query"]}

Flight Agent Result:
{state["flight_results"]}

Hotel Agent Result:
{state["hotel_results"]}

Itinerary Agent Result:
{state["itinerary"]}
"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=prompt)
    ]

    response = llm.invoke(messages)

    return {
        "messages": [response],
        "llm_call": state["llm_call"] + 1
    }


# ============================================================
# BUILD GRAPH
# ============================================================

graph = StateGraph(TravelState)


# Add nodes
# graph.add_node("request_parser", request_parser)
graph.add_node("flight_agent", flight_agent)
graph.add_node("hotel_agent", hotel_agent)
graph.add_node("itinerary_agent", itinerary_agent)
graph.add_node("final_agent", final_agent)


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
    "itinerary_agent"
)
graph.add_edge(
    "itinerary_agent",
    "final_agent"
)
graph.add_edge(
    "final_agent",
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
            "itinerary": "",
            "llm_call": 0
        },
        config=config
    )

    print("\n")
    print("=" * 60)
    print("FINAL TRAVEL PLAN")
    print("=" * 60)

    print(result["messages"][-1].content)

    print("\n")
    print("LLM Calls:", result["llm_call"])