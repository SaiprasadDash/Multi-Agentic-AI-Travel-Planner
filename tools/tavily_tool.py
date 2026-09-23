import os
from langchain_tavily import TavilySearch
from dotenv import load_dotenv
from langchain_core.tools import tool

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

tavily_search = TavilySearch(
    max_results=5
)

# Store previous searches
_search_cache = {}

@tool
def search_web(query: str) -> list[dict]:

    query = query.strip()

    if not query:
        return []

    # Check cache first
    if query in _search_cache:
        return _search_cache[query]

    # Call Tavily
    response = tavily_search.invoke({
        "query": query
    })

    results = []

    for result in response.get("results", []):

        results.append({
            "title": result.get("title", "Unknown"),
            "url": result.get("url", ""),
            "snippet": result.get("content", "")
        })

    # Save results to cache
    _search_cache[query] = results

    return results