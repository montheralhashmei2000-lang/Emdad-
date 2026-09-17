"""
نظام الإمداد والتموين - مراقب حالة الشبكة
Network Monitor - checks connectivity and notifies status changes
"""
from __future__ import annotations

import threading
import time
from typing import Callable, Optional

from app.config import settings


class NetworkMonitor:
    """
    مراقب حالة الاتصال بالخادم المركزي.
    يعمل في خيط منفصل ويُعلم الـ UI عند تغير حالة الشبكة.
    """

    def __init__(self, on_status_change: Optional[Callable[[bool], None]] = None):
        self._is_connected = False
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._on_status_change = on_status_change
        self._check_interval = settings.network_check_seconds

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    def start(self) -> None:
        """بدء مراقبة الشبكة في خيط منفصل."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """إيقاف مراقبة الشبكة."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)

    def check_now(self) -> bool:
        """فحص الاتصال فوراً وإرجاع النتيجة."""
        connected = self._ping_server()
        if connected != self._is_connected:
            self._is_connected = connected
            if self._on_status_change:
                self._on_status_change(connected)
        return connected

    def _monitor_loop(self) -> None:
        """حلقة المراقبة الدورية."""
        while self._running:
            self.check_now()
            time.sleep(self._check_interval)

    def _ping_server(self) -> bool:
        """اختبار اتصال فعلي بالخادم."""
        if not settings.server_url:
            return False
        try:
            import httpx
            with httpx.Client(timeout=5) as client:
                response = client.get(
                    f"{settings.server_url.rstrip('/')}/api/ping",
                    headers={"X-Device-ID": settings.device_id},
                )
                return response.status_code == 200
        except Exception:
            return False