from datetime import datetime, timedelta

from fastapi import HTTPException, Request, status


class RateLimitService:
    def __init__(self, limit: int = 30, window_seconds: int = 60) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._bucket: dict[str, list[datetime]] = {}

    def check(self, request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self.window_seconds)

        timestamps = self._bucket.get(client_ip, [])
        timestamps = [ts for ts in timestamps if ts >= window_start]

        if len(timestamps) >= self.limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please retry shortly.",
            )

        timestamps.append(now)
        self._bucket[client_ip] = timestamps
