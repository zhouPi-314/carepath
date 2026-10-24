from __future__ import annotations

import uuid
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest
from sqlalchemy import func, select

from carepath import __version__
from carepath.db import SessionLocal, init_db
from carepath.logging_utils import redact_mapping
from carepath.models import User
from carepath.routers import (
    admin,
    auth,
    clinicians,
    community,
    events,
    government,
    hospital_ops,
    mobile,
    patient,
    pharma,
)
from carepath.seed import seed_database
from carepath.settings import get_settings

logger = structlog.get_logger()
REQUEST_COUNT = Counter(
    "carepath_http_requests_total",
    "Total HTTP requests handled by the platform",
    ["method", "status"],
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    if get_settings().app_env == "development":
        async with SessionLocal() as db:
            count = await db.scalar(select(func.count(User.id)))
            if not count:
                await seed_database()
                logger.info("demo_data_seeded")
    yield


app = FastAPI(
    title="医疗健康保障协同平台 API",
    version=__version__,
    description="医疗健康保障协同平台；不得用于真实诊疗。",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    response = await call_next(request)
    REQUEST_COUNT.labels(request.method, str(response.status_code)).inc()
    logger.info(
        "request_completed",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        request_id=request_id,
        query=redact_mapping(dict(request.query_params)),
    )
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@app.exception_handler(RequestValidationError)
async def invalid_request(request: Request, exc: RequestValidationError) -> JSONResponse:
    details = [
        {
            "loc": list(error.get("loc", [])),
            "msg": error.get("msg", ""),
            "type": error.get("type", ""),
        }
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={
            "code": "INVALID_REQUEST",
            "message": "请求参数不合法",
            "requestId": getattr(request.state, "request_id", None),
            "details": details,
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled_request_error", path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "code": "INTERNAL_ERROR",
            "message": "系统暂时无法处理该请求",
            "requestId": getattr(request.state, "request_id", None),
            "details": {},
        },
    )


@app.get("/health", tags=["运维"])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "carepath-api", "version": __version__}


@app.get("/metrics", include_in_schema=False)
async def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


for router in (
    auth.router,
    patient.router,
    clinicians.router,
    hospital_ops.router,
    community.router,
    mobile.router,
    government.router,
    pharma.router,
    admin.router,
    events.router,
):
    app.include_router(router, prefix="/api/v1")
