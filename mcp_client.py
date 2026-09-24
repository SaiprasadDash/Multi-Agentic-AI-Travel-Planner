import os
import asyncio
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
client = MultiServerMCPClient(
    {
        "tavily": {
            "transport": "streamable_http",
            "url": f"https://mcp.tavily.com/mcp/?tavilyApiKey={TAVILY_API_KEY}"
        },
    }
)

async def main():
    tools = await client.get_tools()
    print("Available tools:")
    for tool in tools:
        print(tool.name)

if __name__ == "__main__":
    asyncio.run(main())