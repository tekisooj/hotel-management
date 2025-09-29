import os
import requests
from fastapi import Request, HTTPException
from jose import jwt
from starlette.middleware.base import BaseHTTPMiddleware

class CognitoAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.jwks_url = os.getenv("JWKS_URL")
        self.audience = os.getenv("AUDIENCE")
        self._cached_keys = None

    def _get_jwks(self):
        if self._cached_keys is None:
            try:
                response = requests.get(self.jwks_url, timeout=5)
                response.raise_for_status()
                self._cached_keys = response.json()["keys"]
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to load JWKS: {str(e)}")
        return self._cached_keys

    async def dispatch(self, request: Request, call_next):
        auth = request.headers.get("Authorization")
        if not auth or not auth.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

        token = auth.split(" ")[1]
        try:
            header = jwt.get_unverified_header(token)
            jwks = self._get_jwks()
            key = next(k for k in jwks if k["kid"] == header["kid"])
            payload = jwt.decode(token, key, algorithms=["RS256"], audience=self.audience)
            request.state.user = payload
        except Exception as e:
            raise HTTPException(status_code=403, detail=f"Token validation failed: {str(e)}")

        return await call_next(request)
