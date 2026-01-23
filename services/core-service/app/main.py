from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import time  
from prometheus_client import Counter, Histogram, generate_latest, REGISTRY

app = FastAPI(title="API Gateway")

# PROMETHEUS METRICS 
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code', 'service']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint', 'service']
)

ACTIVE_REQUESTS = Counter(
    'http_requests_active',
    'Active HTTP requests',
    ['service']
)

API_CALLS = Counter(
    'api_calls_total',
    'Total API calls to backend services',
    ['target_service', 'status']
)

# PROMETHEUS MIDDLEWARE 
@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    start_time = time.time()
    ACTIVE_REQUESTS.labels(service="api-gateway").inc()
    
    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception as e:
        status_code = 500
        response = JSONResponse(
            content={"error": f"Internal Server Error: {str(e)}"},
            status_code=status_code,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS"
            }
        )
    
    duration = time.time() - start_time
    
    # Запись метрик
    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path,
        service="api-gateway"
    ).observe(duration)
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status_code=status_code,
        service="api-gateway"
    ).inc()
    
    ACTIVE_REQUESTS.labels(service="api-gateway").dec()
    
    return response

# PROMETHEUS ENDPOINT
@app.get("/metrics")
async def metrics():
    """Эндпоинт для Prometheus метрик"""
    from fastapi.responses import Response  # Локальный импорт
    return Response(
        generate_latest(REGISTRY),
        media_type="text/plain",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS"
        }
    )

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
            API_CALLS.labels(target_service="dict-service", status=400).inc()
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

            # Счетчик вызовов API
            API_CALLS.labels(target_service="dict-service", status=response.status_code).inc()
            
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
            API_CALLS.labels(target_service="dict-service", status=503).inc()
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

            # Счетчик вызовов API
            API_CALLS.labels(target_service="task-service", status=response.status_code).inc()
            
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
            API_CALLS.labels(target_service="task-service", status=503).inc()
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
        ],
        "metrics_available": True
    }

@app.get("/")
async def root():
    return RedirectResponse(url="/docs")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")