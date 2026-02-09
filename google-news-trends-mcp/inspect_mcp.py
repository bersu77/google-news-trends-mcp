from mcp_server import mcp
import asyncio
import inspect

async def main():
    tools = await mcp.get_tools()
    print(f"Tools: {list(tools.keys())}")
    if tools:
        tool_name = list(tools.keys())[0]
        tool = tools[tool_name]
        print(f"Tool {tool_name} type: {type(tool)}")
        
        for name, member in inspect.getmembers(tool):
             if not name.startswith("_"):
                 print(f" - {name}")
                 
        # If it's a FunctionTool, it probably has a .fn attribute
        if hasattr(tool, 'fn'):
            print(f"Fn: {tool.fn}")

asyncio.run(main())
