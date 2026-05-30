from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config import settings
from app.models.schemas import AdminLoginRequest, AdminLoginResponse

security = HTTPBearer()


class AuthService:
    def login(self, payload: AdminLoginRequest) -> AdminLoginResponse:
        if (
            payload.username != settings.admin_username
            or payload.password != settings.admin_password
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid admin credentials",
            )

        token = self._create_token({"sub": payload.username})
        return AdminLoginResponse(access_token=token)

    def _create_token(self, data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    def verify_token(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
        token = credentials.credentials
        try:
            payload = jwt.decode(
                token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
            )
            username = payload.get("sub")
            if not username:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token missing subject",
                )
            return username
        except JWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            ) from exc
