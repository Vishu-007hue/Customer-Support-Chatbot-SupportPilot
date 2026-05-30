import time
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models.schemas import (
    AnalyticsSummary,
    AdminLoginRequest,
    AdminLoginResponse,
    ChatRequest,
    ChatResponse,
    HandoverRequest,
    HandoverResponse,
    ResponseRecordIn,
    ResponseRecordOut,
)
from app.services.admin_service import AdminService
from app.services.analytics_service import AnalyticsService
from app.services.auth_service import AuthService
from app.services.chat_service import ChatService
from app.services.handover_service import HandoverService
from app.services.rate_limit_service import RateLimitService

app = FastAPI(title=settings.app_name)
chat_service = ChatService()
handover_service = HandoverService()
admin_service = AdminService()
analytics_service = AnalyticsService()
auth_service = AuthService()
rate_limit_service = RateLimitService(limit=40, window_seconds=60)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "env": settings.app_env}


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    request_id = str(uuid4())
    start_time = time.time()
    response = await call_next(request)
    duration_ms = int((time.time() - start_time) * 1000)
    response.headers["X-Request-Id"] = request_id
    response.headers["X-Response-Time-Ms"] = str(duration_ms)
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.post(f"{settings.api_prefix}/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, request: Request) -> ChatResponse:
    try:
        rate_limit_service.check(request)
        return chat_service.handle_chat(payload)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {exc}") from exc


@app.post(f"{settings.api_prefix}/handover", response_model=HandoverResponse)
def handover(payload: HandoverRequest, request: Request) -> HandoverResponse:
    try:
        rate_limit_service.check(request)
        return handover_service.create_handover(payload)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Handover failed: {exc}") from exc


@app.post(f"{settings.api_prefix}/admin/login", response_model=AdminLoginResponse)
def admin_login(payload: AdminLoginRequest) -> AdminLoginResponse:
    return auth_service.login(payload)


@app.get(f"{settings.api_prefix}/admin/responses", response_model=list[ResponseRecordOut])
def list_responses(_: str = Depends(auth_service.verify_token)) -> list[ResponseRecordOut]:
    return admin_service.list_responses()


@app.post(f"{settings.api_prefix}/admin/responses", response_model=ResponseRecordOut)
def create_response(
    payload: ResponseRecordIn, _: str = Depends(auth_service.verify_token)
) -> ResponseRecordOut:
    return admin_service.create_response(payload)


@app.put(f"{settings.api_prefix}/admin/responses/{{record_id}}", response_model=ResponseRecordOut)
def update_response(
    record_id: str, payload: ResponseRecordIn, _: str = Depends(auth_service.verify_token)
) -> ResponseRecordOut:
    updated = admin_service.update_response(record_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Response record not found")
    return updated


@app.delete(f"{settings.api_prefix}/admin/responses/{{record_id}}")
def delete_response(record_id: str, _: str = Depends(auth_service.verify_token)) -> dict:
    deleted = admin_service.delete_response(record_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Response record not found")
    return {"status": "deleted", "id": record_id}


@app.get(f"{settings.api_prefix}/analytics/summary", response_model=AnalyticsSummary)
def analytics_summary(_: str = Depends(auth_service.verify_token)) -> AnalyticsSummary:
    return analytics_service.summary()
