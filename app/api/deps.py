from fastapi import Header, HTTPException, Request

from ..security.permissions import Principal


def get_principal(request: Request, x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> Principal:
    settings = request.app.state.settings
    if not x_api_key or x_api_key not in settings.api_keys:
        raise HTTPException(status_code=401, detail={"code": "UNAUTHENTICATED", "message": "Missing or invalid X-API-Key"})
    rec = settings.api_keys[x_api_key]
    principal = Principal(key_id=rec.key_id, role=rec.role, account_id=rec.account_id)
    request.app.state.rate_limiter.check(principal.key_id)
    return principal
