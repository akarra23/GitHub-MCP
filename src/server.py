from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import aiohttp
import os
from dotenv import load_dotenv
from github import Github
from github_handler import GitHubHandler

# Load environment variables
load_dotenv()

app = FastAPI()

class MCPRequest(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None

class MCPResponse(BaseModel):
    content: List[Dict[str, Any]]
    metadata: Dict[str, Any]

@app.post("/mcp/v1/query", response_model=MCPResponse)
async def handle_mcp_query(request: MCPRequest):
    """
    Handle MCP protocol requests for GitHub context.
    This endpoint processes queries about GitHub repositories and returns relevant context.
    """
    try:
        # Initialize GitHub handler
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            raise HTTPException(
                status_code=500,
                detail="GitHub token not found in environment variables"
            )
        
        handler = GitHubHandler(github_token)
        
        # Process the query
        content = await handler.process_query(request.query, request.context)
        
        return MCPResponse(
            content=content,
            metadata={
                "status": "success",
                "source": "github-mcp-server",
                "version": "0.1.0"
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
