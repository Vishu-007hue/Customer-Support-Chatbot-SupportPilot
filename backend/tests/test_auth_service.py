from fastapi import HTTPException

from app.models.schemas import AdminLoginRequest
from app.services.auth_service import AuthService


def test_login_success_returns_token() -> None:
    service = AuthService()
    payload = AdminLoginRequest(username="admin", password="admin123")
    response = service.login(payload)
    assert response.access_token
    assert response.token_type == "bearer"


def test_login_failure_raises_exception() -> None:
    service = AuthService()
    payload = AdminLoginRequest(username="admin", password="wrong")
    try:
        service.login(payload)
        assert False, "Expected HTTPException for invalid login"
    except HTTPException as exc:
        assert exc.status_code == 401
