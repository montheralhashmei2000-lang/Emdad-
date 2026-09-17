import sys
import os
sys.path.insert(0, r'E:\Emdad_system')

views_dir = r'E:\Emdad_system\views'
required = [
    'inventory_view', 'items_management_view', 'receive_view', 'issue_view',
    'transfer_view', 'warehouses_view', 'beneficiary_units_view', 'entitlements_view',
    'daily_strength_view', 'returns_view', 'facilities_view', 'inventory_count_view',
    'suppliers_view', 'reports_view', 'logistics_tracker_view', 'settings_view',
    'transfer_notifications_view', 'emergency_view', 'emergency_sync_view',
    'opening_balance_view', 'notification_view', 'personnel_view'
]

missing = [m for m in required if not os.path.exists(os.path.join(views_dir, m + '.py'))]
print(f"Missing views: {missing}")

# Test imports
for m in required:
    if m not in missing:
        try:
            exec(f"from views.{m} import *")
            print(f"  {m}: OK")
        except Exception as e:
            print(f"  {m}: ERROR - {e}")
