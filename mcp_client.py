import asyncio

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()