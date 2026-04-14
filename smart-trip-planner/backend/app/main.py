"""FastAPI 应用入口"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.v1 import trip, poi, health
from app.core.exceptions import TripPlannerException
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="智能行程规划助手 API",
    description="AI驱动的旅行规划工具，基于腾讯地图 + QClaw",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(TripPlannerException)
async def trip_planner_exception_handler(request: Request, exc: TripPlannerException):
    return JSONResponse(
        status_code=400,
        content={"code": exc.code, "message": exc.message},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"code": "SYSTEM_ERROR", "message": "系统内部错误"},
    )


app.include_router(health.router)
app.include_router(trip.router)
app.include_router(poi.router)


@app.get("/")
async def root():
    return {
        "name": "Smart Trip Planner",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "generate_trip": "/api/v1/trip/generate",
            "search_poi": "/api/v1/poi/search",
            "health": "/api/v1/health",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
