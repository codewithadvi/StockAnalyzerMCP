import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

async def generate_response(query: str, available_tools: list) -> dict:
    """Use Groq to identify which tool to use and with what parameters."""
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    prompt = f"""Given this user query: "{query}"
    
Available tools:
{json.dumps(available_tools, indent=2)}

Identify which tool to use and what parameters to provide.
Respond ONLY with JSON in this format:
{{"tool_name": "tool_name", "arguments": {{"param": "value"}}}}"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    
    return json.loads(response.choices[0].message.content.strip().replace('```json', '').replace('```', ''))

async def main():
    """Main client that connects to MCP server and uses Gemini for tool selection."""
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_server.py"],
        env=None
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # List available tools
            tools = await session.list_tools()
            available_tools = [
                {"name": tool.name, "description": tool.description, "parameters": tool.inputSchema}
                for tool in tools.tools
            ]
            
            print("MCP Client connected. Available tools:")
            for tool in available_tools:
                print(f"  - {tool['name']}: {tool['description']}")
            print("\nEnter your query (or 'quit' to exit):")
            
            while True:
                query = input("\n> ").strip()
                if query.lower() in ['quit', 'exit', 'q']:
                    break
                
                if not query:
                    continue
                
                try:
                    # Use Gemini to determine tool and arguments
                    decision = await generate_response(query, available_tools)
                    tool_name = decision.get("tool_name")
                    arguments = decision.get("arguments", {})
                    
                    print(f"\nGroq chose tool: {tool_name} with args: {arguments}")
                    
                    # Execute the tool
                    result = await session.call_tool(tool_name, arguments=arguments)
                    print(f"\nResult: {result.content[0].text}")
                    
                except Exception as e:
                    print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())