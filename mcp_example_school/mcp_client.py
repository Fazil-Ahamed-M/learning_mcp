import asyncio
import json
import os
import sys
from contextlib import AsyncExitStack

from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client
from openai import OpenAI

HERE = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(HERE, ".env"))

HTTP_SERVER_URL = "http://127.0.0.1:8050/mcp"
MODEL = "grok-build-0.1"  # cheapest Grok model on the xAI API (Oct 2026)

SYSTEM_PROMPT = """You are a helpful assistant for a school.
Answer questions about students using the tools you have.
- get_personal_data / get_academic_data: when the student's sl_no is known.
- query_database: for anything else (search by name, rankings, averages, comparisons).
Never make up student data. Keep answers short and clear."""

# Grok is reached through xAI's OpenAI-compatible API
llm = OpenAI(api_key=os.getenv("grok_api_key"), base_url="https://api.x.ai/v1")


async def connect_to_servers(stack: AsyncExitStack) -> dict[str, ClientSession]:
    """Connect to both MCP servers and return a map of tool name -> session."""
    # 1. HTTP server: must already be running (python mcp_server_http.py)
    read, write, _ = await stack.enter_async_context(streamablehttp_client(HTTP_SERVER_URL))
    http_session = await stack.enter_async_context(ClientSession(read, write))

    # 2. stdio server: the client launches it as a child process
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[os.path.join(HERE, "mcp_server_stdio.py")],
    )
    read, write = await stack.enter_async_context(stdio_client(server_params))
    stdio_session = await stack.enter_async_context(ClientSession(read, write))

    tool_sessions = {}
    for session in [http_session, stdio_session]:
        await session.initialize()
        for tool in (await session.list_tools()).tools:
            tool_sessions[tool.name] = session
    return tool_sessions


async def get_tool_definitions(tool_sessions: dict[str, ClientSession]) -> list[dict]:
    """Convert MCP tool descriptions into the function-calling format Grok expects."""
    definitions = []
    for session in set(tool_sessions.values()):
        for tool in (await session.list_tools()).tools:
            definitions.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema,
                },
            })
    return definitions


async def ask(messages: list, tools: list, tool_sessions: dict[str, ClientSession]) -> str:
    """Send the conversation to Grok, run any tools it asks for, and return its answer."""
    while True:
        response = llm.chat.completions.create(model=MODEL, messages=messages, tools=tools)
        message = response.choices[0].message
        messages.append(message)

        # No tool requested: this is the final answer
        if not message.tool_calls:
            return message.content

        # Run each requested tool on the MCP server that owns it
        for tool_call in message.tool_calls:
            name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments or "{}")
            print(f"  [tool] {name}({arguments})")

            result = await tool_sessions[name].call_tool(name, arguments=arguments)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result.content[0].text if result.content else "",
            })


async def run_chat():
    async with AsyncExitStack() as stack:
        tool_sessions = await connect_to_servers(stack)
        tools = await get_tool_definitions(tool_sessions)
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        print("\n===== School MCP Chat =====")
        print(f"Tools: {', '.join(tool_sessions)}")
        print("Type 'exit' or 'quit' to end, 'clear' to reset the conversation")
        print("===========================\n")

        while True:
            user_input = input("\nYou: ").strip()
            if user_input.lower() in ["exit", "quit"]:
                print("Ending conversation...")
                break
            if user_input.lower() == "clear":
                messages = messages[:1]
                print("Conversation history cleared.")
                continue
            if not user_input:
                continue

            messages.append({"role": "user", "content": user_input})
            try:
                answer = await ask(messages, tools, tool_sessions)
                print(f"\nAssistant: {answer}")
            except Exception as e:
                print(f"\nError: {e}")


if __name__ == "__main__":
    asyncio.run(run_chat())
