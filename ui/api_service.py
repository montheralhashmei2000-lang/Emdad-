"""ApiService - Frontend API wrapper with offline-first fallback and dynamic dispatch."""
from typing import Optional, Tuple, Dict, List, Any
from sync.api_client import ApiClient


class ApiService:
    """Frontend API wrapper with offline-first fallback and dynamic dispatch."""

    def __init__(self):
        self.api_client = ApiClient()
        self._method_map: Dict[str, Tuple[str, str]] = {
            "get_dashboard_stats": ("GET", "/api/dashboard/stats"),
            "get_units": ("GET", "/api/units"),
            "get_unit_history": ("GET", "/api/units/{uid}/history"),
            "create_unit": ("POST", "/api/units"),
            "update_unit": ("PUT", "/api/units/{uid}"),
            "delete_unit": ("DELETE", "/api/units/{uid}"),
            "get_beneficiary_units": ("GET", "/api/beneficiary-units"),
            "get_strength_by_date": ("GET", "/api/daily-strength"),
            "enter_daily_strength_bulk": ("POST", "/api/daily-strength/bulk"),
            "get_camp_strengths": ("GET", "/api/daily-strength/camps"),
            "create_supplier": ("POST", "/api/suppliers"),
            "get_inventory": ("GET", "/api/inventory"),
            "get_pending_drafts": ("GET", "/api/transactions/drafts"),
            "create_draft": ("POST", "/api/transactions/draft"),
            "delete_draft": ("DELETE", "/api/transactions/draft/{uid}"),
            "receive_stock_bulk": ("POST", "/api/transactions/receive-bulk"),
            "issue_stock_bulk": ("POST", "/api/transactions/issue-bulk"),
            "transfer_stock_bulk": ("POST", "/api/transactions/transfer-bulk"),
            "return_stock_bulk": ("POST", "/api/transactions/return-bulk"),
            "get_movements_filtered": ("GET", "/api/transactions/movements"),
            "get_next_reference": ("GET", "/api/transactions/next-reference"),
            "get_stocktakes": ("GET", "/api/stocktakes"),
            "create_stocktake": ("POST", "/api/stocktakes"),
            "update_stocktake": ("PUT", "/api/stocktakes/{uid}"),
            "delete_stocktake": ("DELETE", "/api/stocktakes/{uid}"),
            "sync_emergency_dry_run": ("POST", "/api/sync/emergency/dry-run"),
            "sync_emergency_commit": ("POST", "/api/sync/emergency/commit"),
            "get_sync_status": ("GET", "/api/sync/status"),
            "get_notifications": ("GET", "/api/notifications"),
            "get_personnel": ("GET", "/api/personnel"),
            "create_personnel": ("POST", "/api/personnel"),
            "update_personnel": ("PUT", "/api/personnel/{uid}"),
            "get_emergency_status": ("GET", "/api/emergency/status"),
            "get_opening_balances": ("GET", "/api/opening-balances"),
            "save_opening_balance": ("POST", "/api/opening-balances"),
            "get_beneficiaries": ("GET", "/api/beneficiaries"),
            "get_entitlements": ("GET", "/api/entitlements"),
            "create_entitlement": ("POST", "/api/entitlements"),
            "update_entitlement": ("PUT", "/api/entitlements/{uid}"),
            "get_facilities": ("GET", "/api/facilities"),
            "create_facility": ("POST", "/api/facilities"),
            "update_facility": ("PUT", "/api/facilities/{uid}"),
            "get_logistics": ("GET", "/api/logistics"),
        }

    def __getattr__(self, name: str) -> Any:
        # Only called for missing attributes (Python's normal attribute lookup
        # already finds attributes defined on the class or instance).
        # We only auto-stub names that DON'T start with underscore.
        if name.startswith("_") or name == "api_client":
            raise AttributeError(name)
        if name in self._method_map:
            method, path_template = self._method_map[name]
            return _AutoApiMethod(self, name, method, path_template)
        return _AutoApiMethod(self, name, "GET", "/api/" + name.replace("_", "/"))

    def _call_endpoint(self, method: str, path_template: str, *args, **kwargs) -> Tuple[bool, Any]:
        path = path_template
        if args and "{" in path:
            first = args[0]
            path = path.replace("{uid}", str(first))
            path = path.replace("{wid}", str(first))
            path = path.replace("{cid}", str(first))
            args = args[1:]
        for key in ("uid", "wid", "cid"):
            if "{" + key + "}" in path and key in kwargs:
                path = path.replace("{" + key + "}", str(kwargs.pop(key)))

        request_kwargs: Dict[str, Any] = {}
        if method.upper() in ("POST", "PUT", "PATCH"):
            if args:
                request_kwargs["json"] = args[0]
            elif "data" in kwargs:
                request_kwargs["json"] = kwargs.pop("data")
            elif "payload" in kwargs:
                request_kwargs["json"] = kwargs.pop("payload")
            elif "json" in kwargs:
                request_kwargs["json"] = kwargs.pop("json")
        if "params" in kwargs:
            request_kwargs["params"] = kwargs.pop("params")
        return self._request(method, path, **request_kwargs)

    def _request(self, method: str, path: str, **kwargs) -> Tuple[bool, Any]:
        """Execute an HTTP request via the API client."""
        return self.api_client.request(method, path, **kwargs)

    # ======================================================================
    # AUTHENTICATION
    # ======================================================================
    def login(self, username: str, password: str) -> Tuple[bool, Dict]:
        try:
            user = self._login_offline(username, password)
            if user:
                return True, user
        except Exception:
            pass
        try:
            result = self.api_client.authenticate(username, password)
            if result and isinstance(result, dict) and result.get("id"):
                return True, result
        except Exception:
            pass
        return False, {"detail": "اسم المستخدم أو كلمة المرور غير صحيحة"}

    def _login_offline(self, username: str, password: str) -> Optional[Dict]:
        try:
            from data.repositories_impl.repository_factory import RepositoryFactory
            from data.orm_models import UserModel
            from core.security.authentication import verify_password
        except Exception:
            return None
        try:
            factory = RepositoryFactory()
            session = factory.session
            row = session.query(UserModel).filter_by(username=username, is_active=True).first()
            if row is None:
                return None
            if not verify_password(password, row.password_hash):
                return None
            from datetime import datetime, timezone
            row.last_login = datetime.now(timezone.utc).isoformat()
            session.commit()
            # Normalize role to UPPERCASE so it matches main_window.py checks
            raw_role = (row.role or '').strip()
            role_normalized = raw_role.upper() if raw_role else ''
            return {
                "id": row.id,
                "username": row.username,
                "full_name": row.full_name,
                "role": role_normalized,
                "is_active": row.is_active,
                "permissions": {},
            }
        except Exception:
            return None

    def check_device(self) -> Tuple[bool, Dict]:
        try:
            device_id = self.api_client.device_id
            response = self.api_client._client.get(f"/api/devices/{device_id}/status")
            if response.status_code == 200:
                data = response.json()
                return True, {
                    "status": data.get("status", "ACTIVE"),
                    "hardware_id": device_id,
                }
            return True, {"status": "ACTIVE", "hardware_id": device_id}
        except Exception:
            return True, {"status": "ACTIVE", "hardware_id": self.api_client.device_id}

    # ======================================================================
    # CONVENIENCE METHODS
    # ======================================================================
    def ping(self) -> bool:
        return self.api_client.ping()

    def get_system_settings(self) -> Tuple[bool, Dict]:
        try:
            response = self.api_client._client.get("/api/system/settings")
            if response.status_code == 200:
                return True, response.json()
            return False, {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return False, {"error": str(e)}

    def get_camps(self) -> Tuple[bool, List[Dict]]:
        try:
            camps = self.api_client.get_camps()
            return (True, camps) if camps else (False, [])
        except Exception as e:
            return False, []

    def register_camp(self, camp_data: Dict) -> Tuple[bool, Dict]:
        try:
            result = self.api_client.register_camp(camp_data)
            return (True, result) if result else (False, {"error": "Failed to register camp"})
        except Exception as e:
            return False, {"error": str(e)}

    def get_items(self, limit: int = 1000) -> Tuple[bool, List[Dict]]:
        try:
            response = self.api_client._client.get("/api/items")
            if response.status_code == 200:
                data = response.json()
                return True, data.get("items", [])
            return False, []
        except Exception as e:
            return False, []

    def create_item(self, item_data: Dict) -> Tuple[bool, Dict]:
        try:
            response = self.api_client._client.post("/api/items", json=item_data)
            if response.status_code in (200, 201):
                return True, response.json()
            return False, {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return False, {"error": str(e)}

    def update_item(self, item_id: str, item_data: Dict) -> Tuple[bool, Dict]:
        try:
            response = self.api_client._client.put(f"/api/items/{item_id}", json=item_data)
            if response.status_code == 200:
                return True, response.json()
            return False, {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return False, {"error": str(e)}

    def delete_item(self, item_id: str) -> Tuple[bool, str]:
        try:
            response = self.api_client._client.delete(f"/api/items/{item_id}")
            if response.status_code == 200:
                return True, "تم الحذف بنجاح"
            return False, f"HTTP {response.status_code}"
        except Exception as e:
            return False, str(e)

    def get_warehouses(self, limit: int = 1000) -> Tuple[bool, List[Dict]]:
        try:
            response = self.api_client._client.get("/api/warehouses")
            if response.status_code == 200:
                data = response.json()
                return True, data.get("warehouses", [])
            return False, []
        except Exception as e:
            return False, []

    def create_warehouse(self, warehouse_data: Dict) -> Tuple[bool, Dict]:
        try:
            response = self.api_client._client.post("/api/warehouses", json=warehouse_data)
            if response.status_code in (200, 201):
                return True, response.json()
            return False, {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return False, {"error": str(e)}

    def update_warehouse(self, warehouse_id: str, warehouse_data: Dict) -> Tuple[bool, Dict]:
        try:
            response = self.api_client._client.put(f"/api/warehouses/{warehouse_id}", json=warehouse_data)
            if response.status_code == 200:
                return True, response.json()
            return False, {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return False, {"error": str(e)}

    def delete_warehouse(self, warehouse_id: str) -> Tuple[bool, str]:
        try:
            response = self.api_client._client.delete(f"/api/warehouses/{warehouse_id}")
            if response.status_code == 200:
                return True, "تم الحذف بنجاح"
            return False, f"HTTP {response.status_code}"
        except Exception as e:
            return False, str(e)

    def get_transactions(self) -> Tuple[bool, List[Dict]]:
        try:
            response = self.api_client._client.get("/api/transactions")
            if response.status_code == 200:
                data = response.json()
                return True, data.get("transactions", [])
            return False, []
        except Exception as e:
            return False, []

    def create_transaction(self, transaction_data: Dict) -> Tuple[bool, Dict]:
        try:
            response = self.api_client._client.post("/api/transactions", json=transaction_data)
            if response.status_code in (200, 201):
                return True, response.json()
            return False, {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return False, {"error": str(e)}

    def get_facilities(self, limit=1000):
        return self._request("GET", "/api/facilities", params={"limit": limit})

    def get_units(self, limit=1000):
        return self._request("GET", "/api/units", params={"limit": limit})

    def get_beneficiaries(self, limit=1000):
        return self._request("GET", "/api/beneficiaries", params={"limit": limit})

    def get_movements(self, limit=100):
        return self._request("GET", "/api/movements", params={"limit": limit})

    def get_suppliers(self, limit=1000):
        return self._request("GET", "/api/suppliers", params={"limit": limit})

    def get_beneficiaries_offline(self) -> Tuple[bool, List[Dict]]:
        try:
            response = self.api_client._client.get("/api/suppliers")
            if response.status_code == 200:
                data = response.json()
                return True, data.get("suppliers", [])
            return False, []
        except Exception as e:
            return False, []

    def get_custodies(self) -> Tuple[bool, List[Dict]]:
        try:
            response = self.api_client._client.get("/api/custodies")
            if response.status_code == 200:
                data = response.json()
                return True, data.get("custodies", [])
            return False, []
        except Exception as e:
            return False, []

    def get_reports(self) -> Tuple[bool, List[Dict]]:
        try:
            response = self.api_client._client.get("/api/reports")
            if response.status_code == 200:
                data = response.json()
                return True, data.get("reports", [])
            return False, []
        except Exception as e:
            return False, []

    def sync_now(self) -> Tuple[bool, Dict]:
        try:
            return self.api_client.sync_now()
        except Exception as e:
            return False, {"error": str(e)}

    def get_sync_logs(self) -> Tuple[bool, List[Dict]]:
        try:
            response = self.api_client._client.get("/api/sync/logs")
            if response.status_code == 200:
                data = response.json()
                return True, data.get("logs", [])
            return False, []
        except Exception as e:
            return False, []

    def get_recent_activity(self, since_id: int = 0, exclude_user_id: Optional[str] = None) -> Tuple[bool, List[Dict]]:
        try:
            params = {"since_id": since_id}
            if exclude_user_id is not None:
                params["exclude_user_id"] = exclude_user_id
            response = self.api_client._client.get("/api/activity/recent", params=params)
            if response.status_code == 200:
                data = response.json()
                return True, data.get("activity", [])
            return False, []
        except Exception as e:
            return False, []

    def close(self):
        try:
            self.api_client.close()
        except Exception:
            pass


class _AutoApiMethod:
    """Lightweight proxy returned by ApiService.__getattr__ for dynamic endpoints."""

    def __init__(self, api_service: "ApiService", name: str, method: str, path_template: str):
        object.__setattr__(self, "_api", api_service)
        object.__setattr__(self, "_name", name)
        object.__setattr__(self, "_method", method)
        object.__setattr__(self, "_path_template", path_template)

    def __call__(self, *args, **kwargs) -> Tuple[bool, Any]:
        api = object.__getattribute__(self, "_api")
        return api._call_endpoint(self._method, self._path_template, *args, **kwargs)

    def __repr__(self) -> str:
        return f"<AutoApiMethod {self._method} {self._path_template}>"
