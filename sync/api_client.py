"""
نظام الإمداد والتموين - عميل REST API للمزامنة
Async HTTP Client for Central Server Communication
"""
from __future__ import annotations

import json
from typing import Any, Optional

import httpx

from app.config import settings, APP_VERSION


class ApiClient:
    """
    عميل REST API للتواصل مع الخادم المركزي.
    يستخدم httpx مع دعم async (للاستخدام المستقبلي مع Android).
    """

    def __init__(self, base_url: Optional[str] = None, timeout: int = 10):
        self.base_url = (base_url or settings.server_url).rstrip("/")
        self.timeout = timeout
        self.device_id = settings.device_id
        self.camp_id = settings.camp_id

        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout),
            headers=self._default_headers(),
        )

    def _default_headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "X-Device-ID": self.device_id or "",
            "X-Camp-ID": self.camp_id or "",
            "User-Agent": f"LogisticsSupplySystem/{APP_VERSION}",
        }

    def _build_url(self, endpoint: str) -> str:
        """بناء عنوان URL كامل."""
        endpoint = endpoint.lstrip("/")
        return f"{self.base_url}/{endpoint}"

    # ==================== اختبار الاتصال ====================

    def ping(self) -> bool:
        """اختبار الاتصال بالخادم."""
        try:
            if not self.base_url or not self.base_url.startswith(("http://", "https://")):
                return False
            response = self._client.get("/api/ping", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def request(self, method: str, path: str, **kwargs) -> tuple[bool, Any]:
        """Generic request helper used by ApiService.

        Returns ``(success, payload)`` where ``payload`` is the decoded JSON
        body on success or a dict describing the error on failure.
        """
        method_upper = (method or "GET").upper()
        client = self._client
        try:
            if method_upper == "GET":
                resp = client.get(path, **kwargs)
            elif method_upper == "POST":
                resp = client.post(path, **kwargs)
            elif method_upper == "PUT":
                resp = client.put(path, **kwargs)
            elif method_upper == "PATCH":
                resp = client.patch(path, **kwargs)
            elif method_upper == "DELETE":
                resp = client.delete(path, **kwargs)
            else:
                return False, {"error": f"Unsupported HTTP method: {method}"}

            if resp.status_code in (200, 201):
                try:
                    return True, resp.json()
                except Exception:
                    return True, {"raw": resp.text}
            try:
                return False, resp.json()
            except Exception:
                return False, {"error": f"HTTP {resp.status_code}", "raw": resp.text}
        except Exception as e:
            return False, {"error": str(e)}

    # ==================== المزامنة (Push / Pull) ====================

    def push_records(self, records: list[dict]) -> dict:
        """
        رفع سجلات معلقة إلى الخادم المركزي.
        يُتوقع من الخادم إرجاع:
        {
            "synced_ids": ["id1", "id2"],
            "failed_ids": {"id3": "سبب الخطأ"},
            "conflicts": [...]
        }
        """
        response = self._client.post(
            "/api/sync/push",
            json={
                "camp_id": self.camp_id,
                "device_id": self.device_id,
                "records": records,
            },
        )
        response.raise_for_status()
        return response.json()

    def pull_records(self, since: Optional[str] = None) -> list[dict]:
        """
        سحب التحديثات من الخادم المركزي منذ آخر مزامنة.
        """
        params = {"camp_id": self.camp_id}
        if since:
            params["since"] = since

        response = self._client.get("/api/sync/pull", params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("records", [])

    def pull_full_sync(self) -> list[dict]:
        """سحب جميع البيانات من الخادم (للمزامنة الأولية)."""
        response = self._client.get("/api/sync/full", params={"camp_id": self.camp_id})
        response.raise_for_status()
        data = response.json()
        return data.get("records", [])

    # ==================== المعسكرات ====================

    def get_camps(self) -> list[dict]:
        """الحصول على قائمة المعسكرات من الخادم."""
        response = self._client.get("/api/camps")
        response.raise_for_status()
        return response.json().get("camps", [])

    def register_camp(self, camp_data: dict) -> dict:
        """تسجيل معسكر جديد على الخادم المركزي."""
        response = self._client.post("/api/camps/register", json=camp_data)
        response.raise_for_status()
        return response.json()

    # ==================== المصادقة ====================

    def authenticate(self, username: str, password: str) -> Optional[dict]:
        """مصادقة المستخدم على الخادم المركزي."""
        try:
            response = self._client.post(
                "/api/auth/login",
                json={"username": username, "password": password},
                timeout=10,
            )
            if response.status_code == 200:
                return response.json()
            return None
        except (httpx.ConnectError, httpx.TimeoutException):
            return None

    def close(self) -> None:
        """إغلاق الاتصال."""
        self._client.close()

    def __enter__(self) -> "ApiClient":
        return self

    def __exit__(self, *args) -> None:
        self.close()