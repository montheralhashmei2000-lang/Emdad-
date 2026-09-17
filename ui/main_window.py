"""Main window of the desktop client with Stacked Panel Routing."""
import sys
import logging
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QFrame, QStackedWidget, QGridLayout, QMessageBox, QScrollArea, QDialog, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt, QSize, QTimer, QEvent, QObject
import qtawesome as qta
import pyqtgraph as pg

from .theme import apply_theme, SIDEBAR_GROUPS, make_card, make_header_label
from .api_service import ApiService
from .views.inventory_view import InventoryView
from .views.items_management_view import ItemsManagementView
from .views.receive_view import ReceiveView
from .views.issue_view import IssueView
from .views.transfer_view import TransferView
from .views.warehouses_view import WarehousesView
from .views.beneficiary_units_view import BeneficiaryUnitsView
from .views.entitlements_view import EntitlementsView
from .views.daily_strength_view import DailyStrengthView
from .views.returns_view import ReturnsView
from .views.facilities_view import FacilitiesView
from .views.inventory_count_view import InventoryCountView
from .views.suppliers_view import SuppliersView
from .views.reports_view import ReportsView
from .views.logistics_tracker_view import LogisticsTrackerView
from .views.settings_view import SettingsView
from .views.transfer_notifications_view import TransferNotificationsView
from .views.login_dialog import LoginDialog
from .views.emergency_view import EmergencyView
from .views.emergency_sync_view import EmergencySyncView
from .views.opening_balance_view import OpeningBalanceView
from .views.notification_view import NotificationView
from .views.personnel_view import PersonnelView
from .toast_widget import ToastManager


class ActivityFilter(QObject):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

    def eventFilter(self, obj, event):
        if event.type() in (QEvent.Type.MouseMove, QEvent.Type.MouseButtonPress, QEvent.Type.KeyPress):
            self.main_window.reset_idle_timer()

        return super().eventFilter(obj, event)


class MainWindow(QMainWindow):
    """Professional RTL Dashboard for Military PyWarehouse."""

    def __init__(self, api_service: ApiService | None = None, parent=None):
        super().__init__(parent)
        self.api_service = api_service or ApiService()

        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setWindowTitle('نظام الإمداد والتموين العسكري')
        self.setMinimumSize(1200, 800)

        self.sidebar_buttons = {}
        self.current_user = None
        self.idle_timer = QTimer(self)
        self.idle_timeout_ms = 300000
        self.idle_timer.timeout.connect(self.show_lock_screen)

        self._require_login()

        self._init_ui()

        from .loading_overlay import LoadingOverlay
        self.loading_overlay = LoadingOverlay(self)
        self.loading_overlay.hide()

        if self.current_user and self.current_user.get('offline_mode'):
            self._navigate('وضع الطوارئ (مغلق)')
            return

        self._load_dashboard_data()
        self._setup_inactivity_tracker()
        self._setup_activity_poller()

    def _require_login(self, is_lock_screen=False):
        dlg = LoginDialog(self.api_service, self, is_lock_screen=is_lock_screen)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.current_user = dlg.user_data

            if self.current_user:
                perms = self.current_user.get('permissions') or {}
                if not perms and self.current_user.get('role_profile'):
                    perms = self.current_user['role_profile'].get('permissions') or {}

                self.current_user['permissions'] = perms

            if not is_lock_screen:
                self.setWindowTitle(f"نظام الإمداد والتموين العسكري - مستخدم: {self.current_user['full_name']} [{self.current_user['role']}]")

            self.reset_idle_timer()

            ok, res = self.api_service.get_system_settings()
            if ok and 'org_name' in res:
                pass

            self._apply_screenshot_protection()
            return

        if not is_lock_screen:
            sys.exit(0)
            return

    @property
    def _is_admin(self) -> bool:
        """Return True if the current user is an admin (case-insensitive)."""
        if not self.current_user:
            return False
        role = (self.current_user.get('role') or '').strip().upper()
        return role == 'ADMIN'

    def _setup_inactivity_tracker(self):
        ok, res = self.api_service.get_system_settings()
        if ok and 'idle_timeout_minutes' in res:
            self.idle_timeout_ms = res['idle_timeout_minutes'] * 60 * 1000

        app = QApplication.instance()
        self.activity_filter = ActivityFilter(self)
        app.installEventFilter(self.activity_filter)
        self.reset_idle_timer()

    def reset_idle_timer(self):
        if self.idle_timer.isActive():
            self.idle_timer.stop()

        self.idle_timer.start(self.idle_timeout_ms)

    def show_lock_screen(self):
        if getattr(self, 'lock_overlay', None) is not None:
            return

        self.idle_timer.stop()

        from PyQt6.QtWidgets import QLineEdit, QGridLayout
        from .theme import COLORS

        self.lock_overlay = QWidget(self)
        self.lock_overlay.setStyleSheet(f"""
            QWidget {{ background-color: rgba(20, 30, 15, 230); }}
            QLabel {{ color: white; background: transparent; }}
            QLineEdit {{ padding: 8px; font-size: 14px; border: 2px solid {COLORS['primary']}; border-radius: 5px; background: white; color: #333; }}
            QPushButton {{ padding: 10px 20px; font-size: 14px; font-weight: bold; background: {COLORS['primary']}; color: white; border-radius: 5px; }}
        """)
        self.lock_overlay.setGeometry(self.centralWidget().geometry())

        lock_lay = QVBoxLayout(self.lock_overlay)
        lock_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QWidget()
        card.setFixedSize(420, 320)
        card.setStyleSheet(f"background-color: rgba(40, 55, 30, 240); border-radius: 15px; border: 2px solid {COLORS['primary']};")

        card_lay = QVBoxLayout(card)
        card_lay.setSpacing(12)
        card_lay.setContentsMargins(30, 25, 30, 25)

        lbl_title = QLabel('🔒 حماية النظام - يرجى إدخال هويتك')
        lbl_title.setStyleSheet(f"color: {COLORS['gold']}; font-size: 16px; font-weight: bold;")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_lay.addWidget(lbl_title)

        lbl_msg = QLabel('تم قفل الشاشة لحماية بياناتك بسبب الخمول.')
        lbl_msg.setStyleSheet(f"color: {COLORS['danger']}; font-weight: bold; font-size: 12px;")
        lbl_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_lay.addWidget(lbl_msg)

        card_lay.addWidget(QLabel('رمز المستخدم:'))

        self.lock_txt_user = QLineEdit()
        self.lock_txt_user.setPlaceholderText('اسم المستخدم (Username)')
        card_lay.addWidget(self.lock_txt_user)

        card_lay.addWidget(QLabel('كلمة المرور:'))

        self.lock_txt_pass = QLineEdit()
        self.lock_txt_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.lock_txt_pass.setPlaceholderText('كلمة المرور')
        card_lay.addWidget(self.lock_txt_pass)

        btn_unlock = QPushButton('🔓 دخول')
        btn_unlock.clicked.connect(self._unlock)
        card_lay.addWidget(btn_unlock)

        lock_lay.addWidget(card)

        self.lock_overlay.show()
        self.lock_overlay.raise_()
        self.lock_txt_user.setFocus()

    def _unlock(self):
        user = self.lock_txt_user.text().strip()
        pwd = self.lock_txt_pass.text().strip()

        if not user or not pwd:
            QMessageBox.warning(self, 'خطأ', 'يرجى تعبئة كافة الحقول')
            return

        ok, res = self.api_service.login(user, pwd)

        if ok and 'id' in res:
            self.current_user = res

            if self.current_user:
                perms = self.current_user.get('permissions') or {}
                if not perms and self.current_user.get('role_profile'):
                    perms = self.current_user['role_profile'].get('permissions') or {}

                self.current_user['permissions'] = perms

            self.lock_overlay.hide()
            self.lock_overlay.deleteLater()
            self.lock_overlay = None
            self.reset_idle_timer()
            return

        err = res.get('detail', 'خطأ في الاتصال') if isinstance(res, dict) else res
        QMessageBox.critical(self, 'فشل', str(err))

    def resizeEvent(self, event):
        super().resizeEvent(event)

        if hasattr(self, 'lock_overlay') and self.lock_overlay and self.lock_overlay.isVisible():
            self.lock_overlay.setGeometry(self.centralWidget().geometry())

    def _init_ui(self):
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

        self.sidebar = self._build_sidebar()
        self.sidebar.setFixedWidth(240)
        main_layout.addWidget(self.sidebar)

        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack, stretch=1)

        self._build_panels()

        self.setCentralWidget(central_widget)

    def _build_sidebar(self) -> QWidget:
        outer = QWidget()
        outer.setObjectName('sidebar')
        outer_layout = QVBoxLayout(outer)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # Logo Header
        logo_container = QFrame()
        logo_lay = QVBoxLayout(logo_container)
        logo_lay.setSpacing(2)
        logo_lay.setContentsMargins(0, 12, 0, 12)

        logo = QLabel('نظام الإمداد والتموين')
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_lay.addWidget(logo)

        sub_logo = QLabel('Emdad System')
        sub_logo.setStyleSheet('color: #BDC3C7; font-size: 11px;')
        sub_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_lay.addWidget(sub_logo)
        outer_layout.addWidget(logo_container)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet('QScrollArea { background: transparent; border: none; } QWidget#sidebar_scroll_content { background: transparent; }')

        w = QWidget()
        w.setObjectName('sidebar_scroll_content')
        layout = QVBoxLayout(w)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(4)

        SCREEN_PERM_MAP = {
            'لوحة القيادة': 'dashboard',
            'إدارة الأصناف': 'items_management',
            'الموردون': 'suppliers',
            'المستودعات': 'warehouses',
            'الوحدات المستفيدة': 'beneficiaries',
            'المطابخ والأفران': 'facilities',
            'استلام بضاعة': 'receipts',
            'صرف بضاعة': 'issues',
            'تحويل مخزني': 'transfers',
            'أوامر التوجيه المعلقة': 'transfers',
            'المرتجعات': 'returns',
            'التفريدة اليومية (حصر القوة)': 'tafreeda',
            'نسب الاستحقاق': 'tafreeda',
            'الأرصدة الحالية': 'reports',
            'جرد المخزون': 'stocktake',
            'المستكشف اللوجستي': 'reports',
            'التقارير': 'reports',
            'إدارة القوة البشرية': 'personnel',
            'الإعدادات': 'settings',
            'الأرصدة الافتتاحية': 'settings',
            'مزامنة بيانات الطوارئ': 'settings',
            'إشعارات التحويلات': 'transfers',
        }

        user_perms = {}
        if self.current_user and 'permissions' in self.current_user and self.current_user['permissions']:
            user_perms = self.current_user['permissions'].copy()

        if 'basic_data' in user_perms:
            legacy_perms = user_perms['basic_data']
            for new_key in ('items_management', 'suppliers', 'beneficiaries', 'warehouses', 'facilities'):
                if new_key not in user_perms:
                    user_perms[new_key] = legacy_perms

        is_offline = self.current_user and self.current_user.get('offline_mode', False)

        if is_offline:
            btn = QPushButton('  وضع الطوارئ (مغلق)')
            btn.setObjectName('sidebar_btn')
            btn.setIcon(qta.icon('fa5s.exclamation-triangle', color='white'))
            btn.setIconSize(QSize(20, 20))
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, t='وضع الطوارئ (مغلق)': self._navigate(t))
            self.sidebar_buttons['وضع الطوارئ (مغلق)'] = btn
            layout.addWidget(btn)

        for group_name, items in SIDEBAR_GROUPS.items():
            if is_offline:
                break

            allowed_items = []
            for label, icon_name in items[:2]:
                # إظهار كل الأزرار لجميع المستخدمين (للبطء التشخيصي)
                p_key = SCREEN_PERM_MAP.get(label)
                # TODO: يمكن تفعيل فحص الصلاحيات لاحقاً عند الحاجة
                # currently disabled for debugging

                allowed_items.append((label, icon_name))

            if not allowed_items and group_name != 'الرئيسية':
                continue

            if len(items) == 1 and group_name == 'الرئيسية':
                label, icon_name = items[0]
                btn = QPushButton(f'  {label}')
                btn.setObjectName('sidebar_btn')
                btn.setIcon(qta.icon(icon_name, color='white'))
                btn.setIconSize(QSize(20, 20))
                btn.setCheckable(True)
                btn.clicked.connect(lambda checked=False, t=label: self._navigate(t))
                self.sidebar_buttons[label] = btn
                layout.addWidget(btn)
                continue

            group_btn = QPushButton(f'  ▶  {group_name}')
            group_btn.setObjectName('sidebar_group_btn')
            group_btn.setCheckable(True)
            layout.addWidget(group_btn)

            item_container = QWidget()
            item_container.setObjectName('sidebar_items_container')
            item_layout = QVBoxLayout(item_container)
            item_layout.setContentsMargins(0, 0, 0, 0)
            item_layout.setSpacing(2)

            for label, icon_name in allowed_items:
                btn = QPushButton(f'  {label}')
                btn.setObjectName('sidebar_btn_sub')
                btn.setIcon(qta.icon(icon_name, color='white'))
                btn.setIconSize(QSize(18, 18))
                btn.setCheckable(True)
                btn.clicked.connect(lambda checked=False, t=label: self._navigate(t))
                self.sidebar_buttons[label] = btn
                item_layout.addWidget(btn)

            layout.addWidget(item_container)

            def make_toggle(btn, container):
                def toggle(checked):
                    container.setVisible(checked)
                    name = btn.text().replace('  ▶  ', '').replace('  ▼  ', '')
                    btn.setText(f'  ▼  {name}' if checked else f'  ▶  {name}')
                return toggle

            group_btn.toggled.connect(make_toggle(group_btn, item_container))
            item_container.setVisible(False)
            group_btn.setChecked(False)

        layout.addStretch()

        uname = self.current_user.get('full_name', 'مستخدم') if self.current_user else 'مستخدم'
        urole = self.current_user.get('role', '') if self.current_user else ''
        role_label = ''

        if self.current_user and self.current_user.get('role_profile'):
            role_label = self.current_user['role_profile'].get('name', urole)
        else:
            role_label = 'مدير نظام' if urole.strip().upper() == 'ADMIN' else 'مُدخل بيانات'

        # User Profile
        self.lbl_sidebar_user = QLabel(f'👤 {uname}')
        self.lbl_sidebar_user.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_sidebar_user.setStyleSheet('color: white; padding: 6px 0; font-weight: 700; font-size: 13px;')
        layout.addWidget(self.lbl_sidebar_user)

        role_lbl = QLabel(role_label)
        role_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        role_lbl.setStyleSheet('color: #BDC3C7; font-size: 11px; padding-bottom: 6px;')
        layout.addWidget(role_lbl)

        # Logout
        btn_logout = QPushButton('تسجيل خروج')
        btn_logout.clicked.connect(self._do_logout)
        layout.addWidget(btn_logout)

        btn_exit = QPushButton('خروج')
        btn_exit.clicked.connect(self._do_exit)
        layout.addWidget(btn_exit)

        scroll.setWidget(w)
        outer_layout.addWidget(scroll)

        return outer

    def _build_panels(self):
        self.pnl_dashboard = QWidget()
        self._setup_dashboard(self.pnl_dashboard)
        self.content_stack.addWidget(self.pnl_dashboard)

        self._lazy_routes = {
            'جرد المخزون': self._safe_create(InventoryCountView),
            'المستكشف اللوجستي': self._safe_create(LogisticsTrackerView),
            'الأرصدة الحالية': self._safe_create(InventoryView),
            'استلام بضاعة': self._safe_create(ReceiveView),
            'صرف بضاعة': self._safe_create(IssueView),
            'أوامر التوجيه المعلقة': self._safe_create(NotificationView),
            'تحويل مخزني': self._safe_create(TransferView),
            'المرتجعات': self._safe_create(ReturnsView),
            'المطابخ والأفران': self._safe_create(FacilitiesView),
            'إدارة الأصناف': self._safe_create(ItemsManagementView),
            'الوحدات المستفيدة': self._safe_create(BeneficiaryUnitsView),
            'نسب الاستحقاق': self._safe_create(EntitlementsView),
            'التفريدة اليومية (حصر القوة)': self._safe_create(DailyStrengthView),
            'المستودعات': self._safe_create(WarehousesView),
            'الموردون': self._safe_create(SuppliersView),
            'التقارير': self._safe_create(ReportsView),
            'الإعدادات': self._safe_create(SettingsView),
            'مزامنة بيانات الطوارئ': self._safe_create(EmergencySyncView),
            'الأرصدة الافتتاحية': self._safe_create(OpeningBalanceView),
            'إشعارات التحويلات': self._safe_create(TransferNotificationsView),
            'وضع الطوارئ (مغلق)': self._safe_create(EmergencyView),
            'إدارة القوة البشرية': self._safe_create(PersonnelView),
        }

        self.routes = {'لوحة القيادة': self.pnl_dashboard}

        self._navigate('لوحة القيادة')

    def _setup_dashboard(self, widget: QWidget):
        lay = QVBoxLayout(widget)
        lay.addWidget(make_header_label('لوحة القيادة (Dashboard)'))

        cards_lay = QHBoxLayout()
        cards_lay.setSpacing(15)

        self.card_balances, self.lbl_balances = make_card('إجمالي الأصناف بالمستودع', '...')
        self.card_low, self.lbl_low = make_card('أصناف منخفضة الرصيد', '...', color='#C0392B')
        self.card_moves, self.lbl_moves = make_card('حركات اليوم', '...')
        self.card_units, self.lbl_units = make_card('إجمالي الوحدات المستفيدة', '...')

        for c in (self.card_balances, self.card_low, self.card_moves, self.card_units):
            cards_lay.addWidget(c)

        lay.addLayout(cards_lay)

        charts_lay = QHBoxLayout()

        self.plot_trend = pg.PlotWidget(title='حجم الاستهلاك العام (لآخر 30 يوماً)')
        self.plot_trend.setBackground('w')
        self.plot_trend.showGrid(x=True, y=True)
        charts_lay.addWidget(self.plot_trend, stretch=2)

        self.plot_units = pg.PlotWidget(title='أكثر الوحدات استهلاكاً (إجمالي)')
        self.plot_units.setBackground('w')
        charts_lay.addWidget(self.plot_units, stretch=1)

        lay.addLayout(charts_lay, stretch=1)

        self.tbl_low_stock = QTableWidget(0, 4)
        self.tbl_low_stock.setHorizontalHeaderLabels(['كود الصنف', 'اسم الصنف', 'الرصيد الفعلي الحالي', 'حد الطوارئ (الأدنى)'])
        self.tbl_low_stock.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_low_stock.setStyleSheet('QTableWidget { border: 2px solid #C0392B; font-size: 14px; }')

        lay.addWidget(QLabel('⚠️ الأصناف الواصلة لحد الطوارئ (تحتاج لتعميد طلب توليف أو تموين فوري):'))
        lay.addWidget(self.tbl_low_stock, stretch=1)

    def show_loading(self, text='جاري التحميل...'):
        if hasattr(self, 'loading_overlay'):
            self.loading_overlay.show_overlay(text)

            import PyQt6.QtWidgets as QtWidgets
            QtWidgets.QApplication.processEvents()

    def hide_loading(self):
        if hasattr(self, 'loading_overlay'):
            self.loading_overlay.hide_overlay()

    def _safe_create(self, ViewClass):
        """Wrapper آمن لإنشاء أي view مع معالجة الأخطاء"""
        def creator():
            try:
                # جرب مع api_service و parent
                return ViewClass(parent=self, api_service=self.api_service)
            except TypeError:
                try:
                    # جرب فقط مع api_service
                    return ViewClass(api_service=self.api_service)
                except TypeError:
                    try:
                        # جرب فقط مع parent
                        return ViewClass(parent=self)
                    except TypeError:
                        try:
                            # جرب بدون معاملات
                            return ViewClass()
                        except Exception as e:
                            # أخيراً: إنشاء widget فارغ
                            from PyQt6.QtWidgets import QLabel, QVBoxLayout
                            msg = 'الشاشة غير متاحة: ' + ViewClass.__name__
                            w = QLabel(msg)
                            return w
        return creator

    def _navigate(self, route_name: str):
        for name, btn in self.sidebar_buttons.items():
            btn.setChecked(name == route_name)

        if route_name not in self.routes and hasattr(self, '_lazy_routes') and route_name in self._lazy_routes:
            self.show_loading(f'جاري بناء شاشة {route_name}...')

            def _do_load():
                try:
                    panel = self._lazy_routes[route_name]()
                    self.content_stack.addWidget(panel)
                    self.routes[route_name] = panel
                    self.content_stack.setCurrentWidget(panel)
                    if hasattr(panel, 'load_data'):
                        panel.load_data()
                        panel._data_loaded = True
                finally:
                    self.hide_loading()

            QTimer.singleShot(50, _do_load)
            return

        if route_name in self.routes:
            panel = self.routes[route_name]
            self.content_stack.setCurrentWidget(panel)

            if hasattr(panel, 'load_data') and not getattr(panel, '_data_loaded', False):
                panel.load_data()
                panel._data_loaded = True

            if route_name == 'الرئيسية':
                self._load_dashboard_data()

    def _load_dashboard_data(self):
        try:
            ok, data = self.api_service.get_dashboard_stats()
        except Exception as e:
            logging.warning(f"_load_dashboard_stats failed: {e}")
            return

        if not (ok and data):
            return

        cards = data.get('cards', {})
        self.lbl_balances.setText(str(cards.get('total_items', 0)))
        self.lbl_units.setText(str(cards.get('total_units', 0)))
        self.lbl_moves.setText(str(cards.get('total_moves_today', 0)))
        self.lbl_low.setText(str(cards.get('low_stock_count', 0)))

        self.plot_trend.clear()
        trend = data.get('trend', [])
        if trend:
            y = [float(item['qty']) for item in trend]
            x = list(range(len(y)))
            pen = pg.mkPen(color=(39, 174, 96), width=3)
            self.plot_trend.plot(x, y, pen=pen, symbol='o', symbolBrush=(39, 174, 96))
            ticks = [(i, item['date'][-5:]) for i, item in enumerate(trend) if i % 5 == 0]
            axis = self.plot_trend.getAxis('bottom')
            axis.setTicks([ticks])

        self.plot_units.clear()
        top_units = data.get('top_units', [])
        if top_units:
            xItem = [i for i in range(len(top_units))]
            yItem = [u['qty'] for u in top_units]
            bg = pg.BarGraphItem(x=xItem, height=yItem, width=0.6, brush=(41, 128, 185))
            self.plot_units.addItem(bg)
            ticks = [(i, u['name'][:15]) for i, u in enumerate(top_units)]
            axis = self.plot_units.getAxis('bottom')
            axis.setTicks([ticks])

        low_stock = data.get('low_stock', [])
        self.tbl_low_stock.setRowCount(len(low_stock))

        for row, item in enumerate(low_stock):
            self.tbl_low_stock.setItem(row, 0, QTableWidgetItem(str(item.get('item_code'))))
            self.tbl_low_stock.setItem(row, 1, QTableWidgetItem(str(item.get('name'))))

            qty_item = QTableWidgetItem(str(item.get('balance')))
            qty_item.setForeground(Qt.GlobalColor.red)
            qty_item.setFont(self.font())
            self.tbl_low_stock.setItem(row, 2, qty_item)

            self.tbl_low_stock.setItem(row, 3, QTableWidgetItem(str(item.get('min_limit'))))

    def _do_logout(self):
        reply = QMessageBox.question(self, 'تسجيل خروج', 'هل تريد تسجيل الخروج والعودة لشاشة الدخول؟', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            self.idle_timer.stop()
            self.current_user = None
            self._require_login()

            uname = self.current_user.get('full_name', 'مستخدم') if self.current_user else 'مستخدم'
            urole = self.current_user.get('role', '') if self.current_user else ''
            role_label = ''

            if self.current_user and self.current_user.get('role_profile'):
                role_label = self.current_user['role_profile'].get('name', urole)
            else:
                role_label = 'مدير نظام' if urole.strip().upper() == 'ADMIN' else 'مُدخل بيانات'

            self.lbl_sidebar_user.setText(f'👤 {uname}\n{role_label}')
            self.setWindowTitle(f"نظام الإمداد والتموين العسكري - مستخدم: {self.current_user['full_name']} [{self.current_user['role']}]")
            self._apply_screenshot_protection()
            self._navigate('الرئيسية')

    def _do_exit(self):
        reply = QMessageBox.question(self, 'إغلاق النظام', 'هل أنت متأكد من إغلاق النظام بالكامل؟', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            QApplication.quit()

    def _setup_activity_poller(self):
        self._toast_manager = ToastManager()
        self._last_activity_id = 0

        if not self.current_user or (not self._is_admin):
            return

        ok, data = self.api_service.get_recent_activity(since_id=0, exclude_user_id=self.current_user.get('id'))

        if ok and isinstance(data, list) and data:
            self._last_activity_id = max(a.get('id', 0) for a in data)

        self._activity_timer = QTimer(self)
        self._activity_timer.timeout.connect(self._poll_activity)
        self._activity_timer.start(10000)

    def _poll_activity(self):
        if not self.current_user or (not self._is_admin):
            return

        try:
            ok, data = self.api_service.get_recent_activity(since_id=self._last_activity_id, exclude_user_id=self.current_user.get('id'))

            if not (ok and isinstance(data, list) and data):
                return

            data.sort(key=lambda x: x.get('id', 0))

            for activity in data:
                aid = activity.get('id', 0)
                if aid > self._last_activity_id:
                    self._last_activity_id = aid
                    self._toast_manager.show_toast(activity)
        except Exception:
            return

    def _apply_screenshot_protection(self):
        if sys.platform != 'win32':
            return

        protect = False

        if self.current_user:
            if self._is_admin:
                protect = (self.current_user.get('permissions') or {}).get('screenshot_protect', False)
            else:
                protect = (self.current_user.get('permissions') or {}).get('screenshot_protect', False)

        try:
            import ctypes

            hwnd = int(self.winId())
            affinity = 17 if protect else 0
            ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, affinity)
        except Exception as e:
            print(f'Could not apply screenshot protection: {e}')


def run():
    app = QApplication(sys.argv)
    apply_theme(app)

    try:
        window = MainWindow()
        window.showMaximized()
        sys.exit(app.exec())
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f'فشل تشغيل الواجهة: {e}')


if __name__ == '__main__':
    run()

