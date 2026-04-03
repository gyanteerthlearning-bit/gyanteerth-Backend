import sys
import os
# Fix for Vercel: add Backend/ directory to Python path so all local modules resolve
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI,HTTPException,Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import uvicorn
from sqlalchemy import text
from Database.DB import SessionLocal
from routers.Auth import router_auth
from routers.user import router_user
from routers.Admin import router_admin
from routers.Trainer import router_trainer
import time
from Database.DB import query_times

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="your_super_secret_key_here")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": f"HTTP {exc.status_code}",
            "message": exc.detail,
            "path": str(request.url)
        }
    )

@app.middleware("http")
async def add_process_time_header(request, call_next):

    start_time = time.time()

    response = await call_next(request)

    api_time = time.time() - start_time
    db_time = sum(query_times)
    query_count = len(query_times)

    response.headers["X-API-Time"] = str(round(api_time, 5))
    response.headers["X-DB-Time"] = str(round(db_time, 5))
    response.headers["X-Query-Count"] = str(query_count)

    query_times.clear()

    return response

app.include_router(router_auth,prefix="/gyantreeth/v1/auth_checkpoint",tags=["Authentication"])
app.include_router(router_user,prefix="/gyantreeth/v1/user",tags=["User"])
app.include_router(router_admin,prefix="/gyantreeth/v1/admin",tags=["Admin"])
app.include_router(router_trainer,prefix="/gyantreeth/v1/trainer",tags=["Trainer"])

if __name__ == "__main__":
    uvicorn.run("main:app",host="0.0.0.0",port=8000,reload=True)