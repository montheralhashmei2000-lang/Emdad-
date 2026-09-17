import requests
import json
import os
from typing import Tuple, Any, Optional
import sys
import uuid


def _get_hardware_id():
    appdata = os.getenv('APPDATA')
    if appdata:
        dir_path = os.path.join(appdata, 'PyWarehouse')
    else:
        dir_path = os.path.join(os.path.expanduser('~'), '.pywarehouse')

    os.makedirs(dir_path, exist_ok=True)
    key_path = os.path.join(dir_path, 'device_identity.key')

    if os.path.exists(key_path):
        with open(key_path, 'r', encoding='utf-8') as f:
            hwid = f.read().strip()
            if hwid:
                return hwid

    new_hwid = str(uuid.uuid4())
    try:
        with open(key_path, 'w', encoding='utf-8') as f:
            f.write(new_hwid)
    except Exception:
        pass
    return new_hwid


def _load_config():
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    config_path = os.path.join(base_dir, 'config.json')
    defaults = {'server_url': 'http://127.0.0.1:8000', 'timeout_seconds': 10}

    if os.path.isfile(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
            defaults.update(cfg)
        except Exception:
            pass

    return defaults


class ApiService:
    def __init__(self, base_url: str = None):
        cfg = _load_config()
        self.BASE_URL = base_url or cfg['server_url']
        self._timeout = cfg.get('timeout_seconds', 15)
        self.current_user_id = None
        self.is_offline = False
        self.hardware_id = _get_hardware_id()
        self._session = requests.Session()

    def _request(self, method: str, endpoint: str, **kwargs) -> Tuple[bool, Any]:
        if getattr(self, 'is_offline', False):
            return (False, 'النظام يعمل حالياً في وضع الطوارئ (دون اتصال بالخادم).')

        url = f'{self.BASE_URL}{endpoint}'

        headers = kwargs.pop('headers', {})
        headers['Device-ID'] = self.hardware_id
        if self.current_user_id:
            headers['X-User-ID'] = str(self.current_user_id)

        try:
            import concurrent.futures
            import time
            from PyQt6.QtWidgets import QApplication

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self._session.request, method, url, timeout=self._timeout, headers=headers, **kwargs)
                app = QApplication.instance()

                while not future.done():
                    if app:
                        app.processEvents()
                    time.sleep(0.01)

                resp = future.result()
        except requests.exceptions.RequestException as e:
            return (False, f'تعذر الاتصال بخادم الإمداد: {e}')

        if resp.status_code in (200, 201):
            try:
                return (True, resp.json())
            except ValueError:
                return (True, resp.text)
        else:
            try:
                error_json = resp.json()
                message = error_json.get('detail') or str(error_json)
            except ValueError:
                message = resp.text

            return (False, message)
    def get_items(self, limit=1000):
        return self._request('GET', '/items/', params={'limit': limit})

    def create_item(self, data):
        return self._request('POST', '/items/', json=data)

    def get_stock_balance(self, wh_id):
        params = {'warehouse_id': wh_id} if wh_id else {}
        return self._request('GET', '/stock/balance', params=params)

    def get_low_stock(self):
        return self._request('GET', '/stock/low-stock')

    def receive_stock(self, data):
        return self._request('POST', '/stock/receive', json=data)

    def issue_stock(self, data):
        return self._request('POST', '/stock/issue', json=data)

    def transfer_stock(self, data):
        return self._request('POST', '/stock/transfer', json=data)

    def receive_stock_bulk(self, data):
        return self._request('POST', '/stock/receive-bulk', json=data)

    def issue_stock_bulk(self, data):
        return self._request('POST', '/stock/issue-bulk', json=data)

    def transfer_stock_bulk(self, data):
        return self._request('POST', '/stock/transfer-bulk', json=data)

    def get_pending_transfers(self, warehouse_id):
        return self._request('GET', f"/stock/pending-transfers/{warehouse_id}")

    def accept_transfer(self, data):
        return self._request('POST', '/stock/accept-transfer', json=data)

    def get_unit_history(self, unit_id, date_from, date_to):
        p = {}
        if date_from:
            p['date_from'] = date_from
        if date_to:
            p['date_to'] = date_to

        return self._request('GET', f'/stock/unit-history/{unit_id}', params=p)

    def get_movements(self, limit):
        return self._request('GET', '/stock/movements', params={'limit': limit})

    def get_movements_filtered(self, item_id, movement_type, limit, unit_id):
        p = {'limit': limit}
        if item_id:
            p['item_id'] = item_id
        if movement_type:
            p['movement_type'] = movement_type
        if unit_id:
            p['unit_id'] = unit_id

        return self._request('GET', '/stock/movements', params=p)

    def get_drafts(self, warehouse_id):
        return self._request('GET', '/stock/drafts', params={'warehouse_id': warehouse_id})

    def approve_draft(self, movement_id):
        return self._request('POST', f"/stock/drafts/{movement_id}/approve")

    def approve_draft_bulk(self, movement_ids):
        return self._request('POST', '/stock/drafts/approve-bulk', json=movement_ids)

    def delete_draft(self, movement_id):
        return self._request('DELETE', f"/stock/drafts/{movement_id}")

    def get_warehouses(self, limit=1000):
        return self._request('GET', '/warehouses/', params={'limit': limit})

    def create_warehouse(self, data):
        return self._request('POST', '/warehouses/', json=data)

    def update_warehouse(self, wh_id, data):
        return self._request('PUT', f"/warehouses/{wh_id}", json=data)

    def get_units(self, limit=1000):
        return self._request('GET', '/units/', params={'limit': limit})

    def create_unit(self, data):
        return self._request('POST', '/units/', json=data)

    def get_entitlements(self):
        return self._request('GET', '/entitlements/')

    def create_entitlement(self, data):
        return self._request('POST', '/entitlements/', json=data)

    def create_entitlements_bulk(self, data):
        return self._request('POST', '/entitlements/bulk', json=data)

    def enter_daily_strength(self, data):
        return self._request('POST', '/daily-strength/', json=data)

    def enter_daily_strength_bulk(self, data):
        return self._request('POST', '/daily-strength/bulk', json=data)

    def get_latest_strength(self, unit_id):
        return self._request('GET', f"/daily-strength/latest/{unit_id}")

    def get_strength_by_date(self, target_date):
        return self._request('GET', '/daily-strength/by-date', params={'target_date': target_date})

    def get_daily_strength_summary(self):
        return self._request('GET', '/daily-strength/summary')

    def get_camp_dates(self, camp_id):
        return self._request('GET', f"/daily-strength/camp-dates/{camp_id}")

    def create_inspection(self, data):
        return self._request('POST', '/inspection/', json=data)

    def get_tafreedas(self):
        return self._request('GET', '/tafreeda/')

    def create_tafreeda(self, data):
        return self._request('POST', '/tafreeda/', json=data)

    def update_tafreeda(self, t_id, data):
        return self._request('PUT', f"/tafreeda/{t_id}", json=data)

    def delete_tafreeda(self, t_id):
        return self._request('DELETE', f"/tafreeda/{t_id}")

    def calculate_transfer(self, to_wh, target_date, days):
        return self._request('GET', '/entitlements/calculate-transfer', params={'to_warehouse_id': to_wh, 'target_date': target_date, 'days': days})

    def get_returns(self, return_type, limit):
        p = {'limit': limit}
        if return_type:
            p['return_type'] = return_type

        return self._request('GET', '/returns/', params=p)

    def create_bulk_return(self, payload):
        return self._request('POST', '/returns/bulk', json=payload)

    def get_returnable_balance(self, entity_type, entity_id, item_id, unit_id, warehouse_id):
        p = {'entity_type': entity_type, 'entity_id': entity_id, 'item_id': item_id, 'unit_id': unit_id}
        if warehouse_id:
            p['warehouse_id'] = warehouse_id

        return self._request('GET', '/returns/returnable-balance', params=p)

    def cancel_return(self, return_id):
        return self._request('POST', f"/returns/{return_id}/cancel")

    def get_facilities(self):
        return self._request('GET', '/facilities/')

    def create_facility(self, data):
        return self._request('POST', '/facilities/', json=data)

    def get_facility_subscriptions(self, f_id):
        return self._request('GET', f"/facilities/{f_id}/subscriptions")

    def subscribe_units(self, f_id, data):
        return self._request('POST', f"/facilities/{f_id}/subscribe", json=data)

    def get_daily_logs(self, f_id):
        return self._request('GET', f"/facilities/{f_id}/daily-log")

    def create_daily_log(self, data):
        return self._request('POST', '/facilities/daily-log', json=data)

    def get_voucher(self, ref_no, movement_type):
        params = {}
        if movement_type:
            params['movement_type'] = movement_type

        return self._request('GET', f'/stock/voucher/{ref_no}', params=params)

    def get_next_reference(self, prefix):
        return self._request('GET', f"/stock/next-reference/{prefix}")

    def update_voucher_duration(self, ref_no, duration_days):
        return self._request('PUT', f"/stock/voucher/{ref_no}/duration", json={'duration_days': duration_days})

    def update_voucher_entitlement(self, ref_no, data):
        return self._request('PUT', f"/stock/voucher/{ref_no}/entitlement", json=data)

    def get_categories(self, limit):
        return self._request('GET', '/categories/', params={'limit': limit})

    def create_category(self, data):
        return self._request('POST', '/categories/', json=data)

    def update_category(self, cat_id, data):
        return self._request('PUT', f"/categories/{cat_id}", json=data)

    def delete_category(self, cat_id):
        return self._request('DELETE', f"/categories/{cat_id}")

    def get_suppliers(self, limit):
        return self._request('GET', '/suppliers/', params={'limit': limit})

    def create_supplier(self, data):
        return self._request('POST', '/suppliers/', json=data)

    def update_supplier(self, sup_id, data):
        return self._request('PUT', f"/suppliers/{sup_id}", json=data)

    def delete_supplier(self, sup_id):
        return self._request('DELETE', f"/suppliers/{sup_id}")

    def get_supplier_items(self, sup_id):
        return self._request('GET', f"/suppliers/{sup_id}/items")

    def report_daily_movements(self, params):
        return self._request('GET', '/reports/daily-movements', params=params)

    def report_transfers_history(self, params):
        return self._request('GET', '/reports/transfers-history', params=params)

    def report_unit_account(self, unit_id, params):
        return self._request('GET', f"/reports/unit-account/{unit_id}", params=params)

    def report_unit_account_multi(self, unit_ids, params):
        p = dict(params) if params else {}
        p['unit_ids'] = unit_ids

        return self._request('GET', '/reports/unit-account-multi', params=p)

    def report_current_stock(self, params):
        return self._request('GET', '/reports/current-stock', params=params)

    def report_consumption(self, params):
        return self._request('GET', '/reports/consumption', params=params)

    def report_strength(self, params):
        return self._request('GET', '/reports/strength', params=params)

    def report_kitchen_performance(self, params):
        return self._request('GET', '/reports/kitchen-performance', params=params)

    def report_supplier_summary(self, params):
        return self._request('GET', '/reports/supplier-summary', params=params)

    def report_returns(self, params):
        return self._request('GET', '/reports/returns', params=params)

    def get_dashboard_stats(self):
        return self._request('GET', '/dashboard/stats')

    def check_device(self, device_name):
        import platform
        import socket

        if not device_name:
            try:
                device_name = f'{socket.gethostname()} ({platform.system()})'
            except Exception:
                device_name = 'Unknown Device'

        return self._request('POST', '/device-check', json={'hardware_id': self.hardware_id, 'device_name': device_name})

    def get_devices(self):
        return self._request('GET', '/devices')

    def update_device_status(self, device_id: int, status: str):
        return self._request('PUT', f"/devices/{device_id}/status", json={'status': status})

    def login(self, username, password):
        """تسجيل الدخول - يتحقق من قاعدة البيانات المحلية أولاً ثم يحاول الخادم."""
        import os
        import json
        import hashlib
        import sqlite3

        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))

        auth_file = os.path.join(base_dir, 'auth_cache.json')
        pwd_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()

        # =============================================
        # 1) التحقق من قاعدة البيانات المحلية (offline-first)
        # =============================================
        db_path = os.path.join(base_dir, 'data', 'logistics.db')
        if os.path.exists(db_path):
            try:
                import bcrypt
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute(
                    "SELECT id, username, full_name, role, is_active, password_hash FROM users WHERE username=? AND is_active=1",
                    (username,)
                )
                row = cur.fetchone()
                conn.close()

                if row:
                    stored_hash = row['password_hash']
                    pwd_valid = False
                    # التحقق: bcrypt (افتراضي) أو SHA256 (cache قديم)
                    if stored_hash.startswith('$2b$') or stored_hash.startswith('$2a$'):
                        try:
                            pwd_valid = bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
                        except Exception:
                            pwd_valid = False
                    elif len(stored_hash) == 64:
                        pwd_valid = hashlib.sha256(password.encode('utf-8')).hexdigest() == stored_hash
                    else:
                        # إذا لم يكن مشفر - قارن مباشرة (للحسابات القديمة)
                        pwd_valid = (password == stored_hash)

                    if pwd_valid:
                        self.current_user_id = row['id']
                        role = row['role'] or 'viewer'
                        # تحويل الـ role إلى uppercase للتوافق مع كود الـ permissions
                        role_upper = role.upper()
                        user_data = {
                            'id': row['id'],
                            'username': row['username'],
                            'full_name': row['full_name'],
                            'role': role_upper,
                            'permissions': {},
                            'offline_mode': False,
                        }
                        try:
                            with open(auth_file, 'w', encoding='utf-8') as f:
                                json.dump({'username': username, 'pwd_hash': pwd_hash, 'user_data': user_data}, f)
                        except Exception:
                            pass
                        return (True, user_data)
            except ImportError:
                pass  # bcrypt غير مثبت - ننتقل للـ fallback
            except Exception as e:
                # مشكلة في قاعدة البيانات - ننتقل للـ fallback
                pass

        # =============================================
        # 2) محاولة الاتصال بالخادم البعيد (اختياري)
        # =============================================
        ok, user = self._request('POST', '/login', json={'username': username, 'password': password})

        if ok and isinstance(user, dict):
            self.current_user_id = user.get('id')
            if not user.get('permissions') and user.get('role_profile'):
                user['permissions'] = user['role_profile'].get('permissions')

            try:
                with open(auth_file, 'w', encoding='utf-8') as f:
                    json.dump({'username': username, 'pwd_hash': pwd_hash, 'user_data': user}, f)
            except Exception:
                pass

            user['offline_mode'] = False
            return (ok, user)

        # =============================================
        # 3) Fallback: استخدام auth_cache إن وجد
        # =============================================
        if not ok:
            try:
                if os.path.exists(auth_file):
                    with open(auth_file, 'r', encoding='utf-8') as f:
                        cache = json.load(f)
                    if cache.get('username') == username and cache.get('pwd_hash') == pwd_hash:
                        cached_user = cache.get('user_data', {})
                        self.current_user_id = cached_user.get('id')
                        cached_user['offline_mode'] = True
                        self.is_offline = True
                        return (True, cached_user)
            except Exception:
                pass

        return (ok, user)

    def get_users(self):
        return self._request('GET', '/users')

    def create_user(self, data):
        return self._request('POST', '/users', json=data)

    def update_user(self, user_id, data):
        return self._request('PUT', f"/users/{user_id}", json=data)

    def delete_user(self, user_id):
        return self._request('DELETE', f"/users/{user_id}")

    def get_roles(self):
        return self._request('GET', '/roles')

    def create_role(self, data):
        return self._request('POST', '/roles', json=data)

    def update_role(self, role_id, data):
        return self._request('PUT', f"/roles/{role_id}", json=data)

    def delete_role(self, role_id):
        return self._request('DELETE', f"/roles/{role_id}")

    def get_system_settings(self):
        try:
            ok, res = self._request('GET', '/system-settings')
            if ok and isinstance(res, dict) and res:
                return (True, res)
        except Exception:
            pass
        try:
            import sqlite3, os
            base = os.path.dirname(os.path.abspath(__file__))
            db = os.path.join(base, 'data', 'logistics.db')
            if not os.path.exists(db):
                db = os.path.join(base, 'logistics.db')
            if not os.path.exists(db):
                return (True, {})
            conn = sqlite3.connect(db)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT key, value FROM system_settings")
            result = {row['key']: row['value'] for row in cur.fetchall()}
            conn.close()
            return (True, result)
        except Exception as e:
            return (False, str(e))

    def update_system_settings(self, data):
        try:
            ok, res = self._request('PUT', '/system-settings', json=data)
            if ok:
                return (True, res)
        except Exception:
            pass
        try:
            import sqlite3, os
            base = os.path.dirname(os.path.abspath(__file__))
            db = os.path.join(base, 'data', 'logistics.db')
            if not os.path.exists(db):
                db = os.path.join(base, 'logistics.db')
            conn = sqlite3.connect(db)
            cur = conn.cursor()
            for key, value in (data or {}).items():
                cur.execute("INSERT INTO system_settings (key, value, updated_at) VALUES (?, ?, datetime('now')) ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=datetime('now')", (str(key), str(value)))
            conn.commit()
            conn.close()
            return (True, data)
        except Exception as e:
            return (False, str(e))

    def get_audit_logs(self, limit, **kwargs):
        params = {'limit': limit}
        params.update(kwargs)

        return self._request('GET', '/audit-logs', params=params)

    def run_backup(self, path):
        url = '/backup'
        if path:
            url += f'?path={path}'

        return self._request('POST', url)

    def get_drafts(self, warehouse_id):
        return self._request('GET', f"/stock/drafts?warehouse_id={warehouse_id}")

    def delete_draft(self, movement_id):
        return self._request('DELETE', f"/stock/drafts/{movement_id}")

    def reject_draft(self, movement_id, reason):
        return self._request('POST', f"/stock/drafts/{movement_id}/reject", json={'reason': reason})

    def approve_draft_bulk(self, movement_ids):
        return self._request('POST', '/stock/drafts/approve-bulk', json=movement_ids)

    def get_recent_activity(self, since_id, exclude_user_id):
        params = {'since_id': since_id, 'limit': 20}
        if exclude_user_id:
            params['exclude_user_id'] = exclude_user_id

        return self._request('GET', '/activity/recent', params=params)

    def create_inventory_count(self, data):
        return self._request('POST', '/inventory-counts/', json=data)

    def get_inventory_counts(self, warehouse_id, status):
        p = {}
        if warehouse_id:
            p['warehouse_id'] = warehouse_id
        if status:
            p['status'] = status

        return self._request('GET', '/inventory-counts/', params=p)

    def get_inventory_count_detail(self, count_id):
        return self._request('GET', f"/inventory-counts/{count_id}")

    def update_inventory_count_items(self, count_id, items):
        return self._request('PUT', f"/inventory-counts/{count_id}/items", json=items)

    def update_inventory_count_reasons(self, count_id, items):
        return self._request('PUT', f"/inventory-counts/{count_id}/reasons", json=items)

    def approve_inventory_count(self, count_id):
        return self._request('POST', f"/inventory-counts/{count_id}/approve")

    def cancel_inventory_count(self, count_id):
        return self._request('POST', f"/inventory-counts/{count_id}/cancel")

    def upload_inventory_count_attachment(self, count_id, base64_str):
        return self._request('POST', f"/inventory-counts/{count_id}/attachment", json={'attachment_base64': base64_str})

    def add_item_to_inventory_count(self, count_id, item_id):
        return self._request('POST', f"/inventory-counts/{count_id}/add-item", json={'item_id': item_id})

    def get_tracker_data(self, entity_type: str, entity_id: int, date_from, date_to, item_id):
        p = {'entity_type': entity_type, 'entity_id': entity_id}
        if date_from:
            p['date_from'] = date_from
        if date_to:
            p['date_to'] = date_to
        if item_id:
            p['item_id'] = item_id

        return self._request('GET', '/tracker/', params=p)

    def get_org_units(self):
        return self._request('GET', '/hr/org-units')

    def create_org_unit(self, payload):
        return self._request('POST', '/hr/org-units', json=payload)

    def get_personnel(self, params):
        return self._request('GET', '/hr/personnel', params=params)

    def get_personnel_by_id(self, personnel_id):
        return self._request('GET', f"/hr/personnel/{personnel_id}")

    def create_personnel(self, files, data):
        import requests

        url = f'{self.BASE_URL}/hr/personnel'
        headers = {'Device-ID': self.hardware_id}
        if self.current_user_id:
            headers['X-User-ID'] = str(self.current_user_id)

        try:
            r = requests.post(url, headers=headers, files=files, data=data, timeout=self._timeout)

            if r.status_code == 200:
                return (True, r.json())

            return (False, r.text)
        except Exception as e:
            return (False, str(e))

    def update_personnel_status(self, personnel_id, payload):
        return self._request('PUT', f"/hr/personnel/{personnel_id}/status", json=payload)

    def get_personnel_status_history(self, personnel_id):
        return self._request('GET', f"/hr/personnel/{personnel_id}/status-history")

    def transfer_personnel(self, personnel_id, files, data):
        import requests

        url = f'{self.BASE_URL}/hr/personnel/{personnel_id}/transfer'
        headers = {'Device-ID': self.hardware_id}
        if self.current_user_id:
            headers['X-User-ID'] = str(self.current_user_id)

        try:
            r = requests.post(url, headers=headers, files=files, data=data, timeout=self._timeout)

            if r.status_code == 200:
                return (True, r.json())

            return (False, r.text)
        except Exception as e:
            return (False, str(e))

    def get_personnel_transfer_history(self, personnel_id):
        return self._request('GET', f"/hr/personnel/{personnel_id}/transfer-history")

    def import_org_units(self, filepath):
        import requests

        url = f'{self.BASE_URL}/hr/org-units/import'
        headers = {'Device-ID': self.hardware_id}
        if self.current_user_id:
            headers['X-User-ID'] = str(self.current_user_id)

        try:
            with open(filepath, 'rb') as f:
                r = requests.post(url, headers=headers, files={'file': (os.path.basename(filepath), f)}, timeout=30)

            if r.status_code == 200:
                return (True, r.json())

            return (False, r.text)
        except Exception as e:
            return (False, str(e))

    def import_personnel_file(self, filepath):
        import requests

        url = f'{self.BASE_URL}/hr/personnel/import'
        headers = {'Device-ID': self.hardware_id}
        if self.current_user_id:
            headers['X-User-ID'] = str(self.current_user_id)

        try:
            with open(filepath, 'rb') as f:
                r = requests.post(url, headers=headers, files={'file': (os.path.basename(filepath), f)}, timeout=30)

            if r.status_code == 200:
                return (True, r.json())

            return (False, r.text)
        except Exception as e:
            return (False, str(e))

    def download_hr_file(self, endpoint, save_path):
        import requests

        url = f'{self.BASE_URL}{endpoint}'
        headers = {'Device-ID': self.hardware_id}
        if self.current_user_id:
            headers['X-User-ID'] = str(self.current_user_id)

        try:
            r = requests.get(url, headers=headers, timeout=30, stream=True)

            if r.status_code == 200:
                with open(save_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)

                return (True, save_path)

            return (False, r.text)
        except Exception as e:
            return (False, str(e))
