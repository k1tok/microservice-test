from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx

app = FastAPI(title="API Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

DICT_SERVICE_URL = "http://dict-service:8001"
TASK_SERVICE_URL = "http://task-service:8002"

@app.api_route("/dict/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
async def proxy_to_dict(path: str, request: Request):
    if request.method == "OPTIONS":
        return JSONResponse(
            content={},
            status_code=200,
            headers={
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Origin": "*"
            }
        )
    
    url = f"{DICT_SERVICE_URL}/{path}"
    
    headers = dict(request.headers)
    headers.pop("host", None)
    
    body_bytes = await request.body()
    body_content = None
    
    if request.method in ["POST", "PUT"] and body_bytes:
        try:
            body_str = body_bytes.decode('utf-8')
            import json
            json.loads(body_str)
            body_content = body_bytes
            headers["Content-Type"] = "application/json"
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid JSON in request: {str(e)}"
            )
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method=request.method,
                url=url,
                headers=headers,
                content=body_content,
                params=dict(request.query_params)
            )
            
            if response.status_code == 200 and not response.content:
                return JSONResponse(
                    content={"message": "Success"},
                    status_code=response.status_code
                )
            elif response.content:
                return JSONResponse(
                    content=response.json(),
                    status_code=response.status_code
                )
            else:
                return JSONResponse(
                    content={"status": response.status_code},
                    status_code=response.status_code
                )
                
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")

@app.api_route("/tasks/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
async def proxy_to_task(path: str, request: Request):
    if request.method == "OPTIONS":
        return JSONResponse(
            content={},
            status_code=200,
            headers={
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Origin": "*"
            }
        )
    
    url = f"{TASK_SERVICE_URL}/{path}"
    
    headers = dict(request.headers)
    headers.pop("host", None)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method=request.method,
                url=url,
                headers=headers,
                content=await request.body(),
                params=dict(request.query_params)
            )
            
            if response.content:
                return JSONResponse(
                    content=response.json(),
                    status_code=response.status_code,
                    headers={
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS"
                    }
                )
            else:
                return JSONResponse(
                    content={"status": response.status_code},
                    status_code=response.status_code,
                    headers={
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS"
                    }
                )
                
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503, 
                detail=f"Service unavailable: {str(e)}",
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS"
                }
            )

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "api-gateway"}

@app.get("/debug")
async def debug():
    return {
        "service": "API Gateway",
        "dict_service": DICT_SERVICE_URL,
        "task_service": TASK_SERVICE_URL,
        "endpoints": [
            {"path": "/dict/{path}", "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]},
            {"path": "/tasks/{path}", "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]}
        ]
    }

@app.get("/")
async def root():
    return RedirectResponse(url="/docs")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")