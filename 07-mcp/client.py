# קובץ 2 – MCP Client
# רכיב גנרי: מתאים לכל Server. הוא לא מכיר את lookup_bill – הוא רק יודע
# להתחבר, לגלות (list_tools) ולהפעיל (call_tool).

import sys
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPClient:
    def __init__(self):
        self.session = None
        self._stack = AsyncExitStack()

    async def connect_to_server(self, server_path: str) -> None:
        """מריצה את ה-Server כתהליך נפרד ופותחת איתו ערוץ stdio."""
        params = StdioServerParameters(command=sys.executable, args=[server_path])
        read, write = await self._stack.enter_async_context(stdio_client(params))
        self.session = await self._stack.enter_async_context(ClientSession(read, write))
        await self.session.initialize()

    async def list_tools(self) -> list:
        response = await self.session.list_tools()
        return response.tools

    async def call_tool(self, name: str, arguments: dict) -> str:
        result = await self.session.call_tool(name, arguments)
        return "\n".join(part.text for part in result.content if hasattr(part, "text"))

    async def close(self) -> None:
        await self._stack.aclose()
