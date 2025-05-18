from fastapi import Request, HTTPException
from .license.validator import LicenseValidator

class LicenseMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, request: Request, call_next):
        license_key = request.headers.get("X-License-Key")
        if not license_key:
            raise HTTPException(401, "Missing license key")
            
        if not LicenseValidator(license_key).validate("api_access"):
            raise HTTPException(403, "Invalid or expired license")
            
        response = await call_next(request)
        response.headers["X-Quota-Remaining"] = self._get_quota(license_key)
        return response

    def _get_quota(self, key: str) -> str:
        # Call license server for quota status
        return "1000/1000"  # Mocked value