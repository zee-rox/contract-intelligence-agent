from collections.abc import Awaitable, Callable
from uuid import uuid4
from collections import defaultdict, deque
from time import monotonic

from fastapi import Request, Response
from fastapi.responses import JSONResponse

from app.observability.context import request_id_var
from app.config import get_settings

_request_times: dict[str, deque[float]] = defaultdict(deque)


async def request_id_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    request_id = request.headers.get("x-request-id") or str(uuid4())
    limit = get_settings().rate_limit_per_minute
    if limit:
        now = monotonic()
        bucket = _request_times[request.client.host if request.client else "unknown"]
        while bucket and now - bucket[0] >= 60:
            bucket.popleft()
        if len(bucket) >= limit:
            return JSONResponse(status_code=429, content={"detail": "rate limit exceeded"}, headers={"retry-after": "60"})
        bucket.append(now)
    token = request_id_var.set(request_id)
    request.state.request_id = request_id
    try:
        response = await call_next(request)
    finally:
        request_id_var.reset(token)
    response.headers["x-request-id"] = request_id
    return response
