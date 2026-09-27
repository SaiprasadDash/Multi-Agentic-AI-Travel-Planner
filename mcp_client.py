import os
i
from langchain_mcp_adapters.client import MultiServerMCPClient

from config import TAVILY_API_KEY, AVIATION_STACK_API_KEY, OPENWEATHER_API_KEY 

client = MultiServerMCPClient(
    {
        "tavily": {
            "transport": "streamable_http",
            "url": f"https://mcp.tavily.com/mcp/?tavilyApiKey={TAVILY_API_KEY}"
        },
        
        "aviationstack": {
            "transport": "stdio",
        "command": r"E:\WORK\AI Travel Planner\aviationstack-mcp\.venv\Scripts\python.exe",
            "args": [
                "-m",
                "aviationstack_mcp",
                "mcp",
                "run"
            ],
            "env": {
                "AVIATION_STACK_API_KEY": AVIATION_STACK_API_KEY
            }
        },

        "weather": {
            "transport": "stdio",
            "command": r"E:\WORK\AI Travel Planner\.venv\Scripts\python.exe",
            "args": [
                r"E:\WORK\AI Travel Planner\weather_mcp_server.py"
            ],
            "env": {
                "OPENWEATHER_API_KEY": OPENWEATHER_API_KEY
            }
        }
    }
)

# async def main():
#     tools = await client.get_tools()
#     print("Available tools:")
#     for tool in tools:
#         print(tool.name)

# async def main():
#     tools = await client.get_tools()
#     print("Available tools:")
#     search_tool = next(tool for tool in tools if tool.name == "search")
#     result = await search_tool.ainvoke({
#         "query": "Best hotel in Odisha"
#     })
#     print("Search result:")
#     print(result)


_tools_cache = None
# aviation_tools = {}

async def get_tools():
    """connenct to mcp server and discove tools once."""

    global _tools_cache

    if _tools_cache is not None:
        try:
                _tools_cache = await client.get_tools()
        except Exception as e:
            print(f"Error connecting to MCP server:")
            print(type(e))
            print(repr(e))

            if hasattr(e, "exception"):
                print("\nSUB EXCEPTIONS:")
                for i, sub in enumerate(e.exceptions):
                    print(f"\n--- Exception {i+1} ---")
                    print(type(sub))
                    print(repr(sub))


    return _tools_cache


async def call_tool(tool_name: str, tool_args: dict = None):
    """Call a tool by name with the given arguments."""
    tools = get_tools()

    tool = next(t for t in tools if t.name == tool_name)

    if tool is None:
        raise ValueError(f"Tool '{tool_name}' not found.")

    result = await tool.ainvoke(tool_args or {})

    return result
    
        

# ------------------------
# Tavily MCP Tools
# ------------------------



async def tavily_search(query: str):
    return await call_tool("tavily_search", {"query": query})


async def list_airports(search: str = "", limit: int = 10):
    return await call_tool("list_airports", {"search": search, "limit": limit, "offset": 0})


async def list_airlines(search: str = "", limit: int = 10):
    return await call_tool("list_airlines", {"search": search, "limit": limit, "offset": 0})


async def current_weather(city: str):
    return await call_tool("get_current_weather", {"city": city})


async def forecast(city: str):
    return await call_tool("get_forecast", {"city": city})