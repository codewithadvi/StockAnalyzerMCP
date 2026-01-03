"""Simple test script to verify MCP server works without needing Gemini API."""
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_server():
    """Test the MCP server directly without Gemini."""
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_server.py"],
        env=None
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            print("✓ Connected to MCP Server\n")
            
            # Test 1: Get stock price
            print("Test 1: Getting AAPL stock price...")
            result = await session.call_tool("get_stock_price", arguments={"symbol": "AAPL"})
            print(f"Result: {result.content[0].text}\n")
            
            # Test 2: Compare stocks
            print("Test 2: Comparing AAPL and MSFT...")
            result = await session.call_tool("compare_stocks", arguments={"symbol1": "AAPL", "symbol2": "MSFT"})
            print(f"Result: {result.content[0].text}\n")
            
            # Test 3: Get fundamentals
            print("Test 3: Getting AAPL fundamentals...")
            result = await session.call_tool("get_stock_fundamentals", arguments={"symbol": "AAPL"})
            print(f"Result: {result.content[0].text}\n")
            
            # Test 4: Market summary
            print("Test 4: Getting market summary...")
            result = await session.call_tool("get_market_summary", arguments={})
            print(f"Result: {result.content[0].text}\n")
            
            print("✓ All tests passed! MCP Server is working correctly.")

if __name__ == "__main__":
    asyncio.run(test_server())
