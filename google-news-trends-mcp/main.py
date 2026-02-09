from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse, JSONResponse

from mcp_server import mcp, mcp_http_app

app = FastAPI(lifespan=mcp_http_app.lifespan)
app.mount("/mcp", mcp_http_app)


@app.post("/mcp-direct")
async def direct_call(request: Request):
    try:
        data = await request.json()
        print(f"Received data: {data}")
        
        tool_name = data.get("method")
        # In MCP JSON-RPC, method is often "tools/call", we want the actual tool name from params
        if tool_name == "tools/call":
            params = data.get("params", {})
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
        else:
            arguments = data.get("params", {})

        print(f"Tool name: {tool_name}, Arguments: {arguments}")

        if not tool_name:
            raise HTTPException(status_code=400, detail="Missing tool name")

        # Get registered tools from FastMCP
        try:
            # Use get_tools() which returns a dict of tool_name -> tool_object
            tools_dict = await mcp.get_tools()
            print(f"Available tools: {list(tools_dict.keys())}")
            
            if tool_name not in tools_dict:
                available = ", ".join(tools_dict.keys()) if tools_dict else "none"
                raise HTTPException(
                    status_code=404, 
                    detail=f"Tool '{tool_name}' not found. Available tools: {available}"
                )
            
            tool = tools_dict[tool_name]
            
            # Get the actual function from the tool object
            # FastMCP tools are wrapped, we need to get the underlying function
            if hasattr(tool, 'fn'):
                tool_func = tool.fn
            elif hasattr(tool, '__call__'):
                tool_func = tool
            else:
                raise Exception(f"Unable to extract function from tool '{tool_name}'")
            
            # Create a minimal Context object for the tool
            import inspect
            
            # Check if the function requires a Context parameter
            sig = inspect.signature(tool_func)
            params = list(sig.parameters.keys())
            
            # Create a minimal context that provides required methods
            class MinimalContext:
                async def report_progress(self, progress: int = None, total: int = None, **kwargs):
                    pass
                
                async def info(self, message: str):
                    print(f"[INFO] {message}")
                
                async def debug(self, message: str):
                    print(f"[DEBUG] {message}")
                
                async def sample(self, prompt: str):
                    # Return a mock object for LLM sampling (empty text means no summary)
                    # In a real scenario, this would call an LLM
                    class MockTextContent:
                        def __init__(self):
                            self.type = "text"
                            self.text = ""
                    return MockTextContent()
            
            ctx = MinimalContext()
            
            # Prepare arguments - add context if needed
            if params and params[0] == 'ctx':
                call_args = {'ctx': ctx, **arguments}
            else:
                call_args = arguments
            
            # Call the tool function
            result = await tool_func(**call_args)
            
            # Format the result as MCP expects
            import json
            if isinstance(result, (dict, list)):
                result_text = json.dumps(result, indent=2)
            else:
                result_text = str(result)
            
            print(f"Tool result: {result_text[:200]}...")
            return {
                "jsonrpc": "2.0",
                "id": data.get("id", 1),
                "result": {
                    "content": [{"type": "text", "text": result_text}]
                }
            }
                
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error calling tool: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=str(e))
                
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in direct_call: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse({"error": {"message": str(e)}}, status_code=500)


@app.get("/healthz")
async def healthz() -> PlainTextResponse:
    return PlainTextResponse("ok")
