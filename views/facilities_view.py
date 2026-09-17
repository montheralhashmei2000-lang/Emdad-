from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QComboBox, QLineEdit, QDateEdit,
    QMessageBox, QTabWidget, QFormLayout, QScrollArea, QCheckBox,
)
from PyQt6.QtCore import Qt, QDate

import api_service
from api_service import ApiService
import theme
from theme import apply_theme


class FacilitiesView(QWidget):
    """
    واجهة إدارة المطابخ والأفران والاشتراكات والعمليات اليومية.
    تحتوي على 3 تبويبات: المنشآت، الاشتراكات، العمليات اليومية.
    """

    def __init__(self, parent=None, api_service: ApiService = None):
        super().__init__(parent)
        self.api_service = api_service
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._facilities = []
        self._units = []
        self._items = []
        self._item_units = {}
        self._init_ui()
        self.load_metadata()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)

        header = QLabel("إدارة المطابخ والأفران")
        header.setStyleSheet("font-size:18px; font-weight:bold; color:#2E6B35; padding:5px;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(header)

        self.tabs = QTabWidget()

        self.tab_setup = QWidget()
        self._setup_facility_tab()
        self.tabs.addTab(self.tab_setup, "المنشآت (إضافة/قائمة)")

        self.tab_subs = QWidget()
        self._setup_subscriptions_tab()
        self.tabs.addTab(self.tab_subs, "الاشتراكات (قوة المنشأة)")

        self.tab_daily = QWidget()
        self._setup_daily_log_tab()
        self.tabs.addTab(self.tab_daily, "السجل اليومي (الوجبات)")

        self.tabs.currentChanged.connect(self._on_tab_changed)
        main_layout.addWidget(self.tabs)

        user = getattr(self.parent(), "current_user", None) or {}
        is_admin = user.get("role", "") == "ADMIN"
        bp = user.get("permissions", {}).get("basic_data", {})
        dp = user.get("permissions", {}).get("daily_ops", {})

        self.btn_save.setVisible(is_admin or bp.get("tafreeda", {}).get("add", False))
        self.btn_save_subs.setVisible(is_admin or bp.get("tafreeda", {}).get("add", False))
        self.btn_add_log.setVisible(is_admin or dp.get("tafreeda", {}).get("create", False))

    def _setup_facility_tab(self):
        layout = QHBoxLayout(self.tab_setup)

        form_panel = QWidget()
        form_layout = QFormLayout(form_panel)

        self.txt_fac_name = QLineEdit()
        self.cb_fac_type = QComboBox()
        self.cb_fac_type.addItems(["KITCHEN (مطبخ)", "BAKERY (فرن)"])
        self.cb_parent_unit = QComboBox()

        self.btn_save = QPushButton("💾 حفظ وإضافة")
        self.btn_save.clicked.connect(self._create_facility)
        self.btn_save.setStyleSheet(
            "background-color:#27AE60; color:white; font-weight:bold; padding:8px;"
        )

        form_layout.addRow("اسم المنشأة:", self.txt_fac_name)
        form_layout.addRow("النوع:", self.cb_fac_type)
        form_layout.addRow("يرتبط بوحدة (اختياري):", self.cb_parent_unit)
        form_layout.addRow("", self.btn_save)
        layout.addWidget(form_panel)

        table_panel = QWidget()
        t_layout = QVBoxLayout(table_panel)
        header = QLabel("قائمة المطابخ والأفران الموجودة:")
        t_layout.addWidget(header)

        self.tbl_facilities = QTableWidget()
        self.tbl_facilities.setHorizontalHeaderLabels(["م", "الاسم", "النوع", "الوحدة المرتبطة"])
        self.tbl_facilities.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        t_layout.addWidget(self.tbl_facilities)
        layout.addWidget(table_panel)

    def _setup_subscriptions_tab(self):
        layout = QVBoxLayout(self.tab_subs)

        header_lay = QHBoxLayout()
        header_lay.addWidget(QLabel("اختر المنشأة:"))
        self.cb_sub_facility = QComboBox()
        self.cb_sub_facility.currentIndexChanged.connect(self._load_current_subscriptions)
        header_lay.addWidget(self.cb_sub_facility)
        header_lay.addStretch(True)
        layout.addLayout(header_lay)

        layout.addWidget(QLabel(
            "الوحدات الفرعية المشتركة في هذه المنشأة (ستصرف لهم الوجبات بدلاً من الإعاشة الناشفة):"
        ))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.chk_container = QWidget()
        self.chk_layout = QVBoxLayout(self.chk_container)
        self.chk_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self.chk_container)
        layout.addWidget(scroll)

        self.btn_save_subs = QPushButton("💾 حفظ الاشتراكات")
        self.btn_save_subs.setStyleSheet(
            "background-color:#2980B9; color:white; font-weight:bold; padding:8px;"
        )
        self.btn_save_subs.clicked.connect(self._save_subscriptions)
        layout.addWidget(self.btn_save_subs)

        self._checkbox_list = {}

    def _setup_daily_log_tab(self):
        layout = QVBoxLayout(self.tab_daily)

        form_lay = QHBoxLayout()
        form_lay.addWidget(QLabel("المنشأة:"))
        self.cb_daily_facility = QComboBox()
        form_lay.addWidget(self.cb_daily_facility)

        form_lay.addWidget(QLabel("التاريخ:"))
        self.dt_daily = QDateEdit()
        self.dt_daily.setCalendarPopup(True)
        self.dt_daily.setDate(QDate.currentDate())
        form_lay.addWidget(self.dt_daily)

        form_lay.addWidget(QLabel("النوع:"))
        self.cb_meal_type = QComboBox()
        self.cb_meal_type.addItems([
            "BREAKFAST (صبوح)", "LUNCH (غداء)", "DINNER (عشاء)", "BREAD (خبز للفرن)"
        ])
        form_lay.addWidget(self.cb_meal_type)

        self.btn_add_log = QPushButton("➕ تسجيل التقرير وطباعة السند")
        self.btn_add_log.setStyleSheet("background-color:#27AE60; color:white;")
        self.btn_add_log.clicked.connect(self._create_daily_log)
        form_lay.addWidget(self.btn_add_log)
        layout.addLayout(form_lay)

        layout.addWidget(QLabel("سجل التقارير السابقة للمنشأة المحددة:"))
        self.tbl_logs = QTableWidget()
        self.tbl_logs.setHorizontalHeaderLabels(
            ["التاريخ", "المنشأة", "نوع الوجبة", "الكمية/القوة المبني عليها", "إجراء"]
        )
        self.tbl_logs.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.tbl_logs)

        self.cb_daily_facility.currentIndexChanged.connect(self._load_daily_logs)

    def load_metadata(self):
        user = getattr(self.parent(), "current_user", None) or {}
        is_admin = user.get("role", "") == "ADMIN"
        has_explicit = isinstance(user.get("permissions", {}).get("facilities"), dict)
        perms = user.get("permissions", {}).get("facilities", {})
        tabs_p = perms.get("tabs", {})

        self.tabs.setTabVisible(
            0, is_admin or not has_explicit or tabs_p.get("tab_setup", {}).get("view", False)
        )
        self.tabs.setTabVisible(
            1, is_admin or not has_explicit or tabs_p.get("tab_subs", {}).get("view", False)
        )
        self.tabs.setTabVisible(
            2, is_admin or not has_explicit or tabs_p.get("tab_daily", {}).get("view", False)
        )

        ok_u, data_u = self.api_service.get_units() if self.api_service else (False, None)
        if ok_u:
            self._units = data_u
        self._refresh_unit_combos()
        self._load_facilities()

    def _refresh_unit_combos(self):
        self.cb_parent_unit.clear()
        self.cb_parent_unit.addItem("--- بدون (مطبخ عام) ---", None)
        for u in self._units:
            self.cb_parent_unit.addItem(u["name"], u["id"])

    def _load_facilities(self):
        import PyQt6.QtWidgets as QtWidgets

        ok, data = self.api_service.get_facilities() if self.api_service else (False, None)
        if not ok:
            return

        self._facilities = data
        self.tbl_facilities.setRowCount(len(data))
        self.cb_sub_facility.clear()
        self.cb_daily_facility.clear()

        for i, fac in enumerate(data):
            self.tbl_facilities.setItem(i, 0, QTableWidgetItem(str(i)))
            self.tbl_facilities.setItem(i, 1, QTableWidgetItem(fac.get("name")))
            ftype_str = "مطبخ" if fac.get("f_type") == "KITCHEN" else "فرن"
            self.tbl_facilities.setItem(i, 2, QTableWidgetItem(ftype_str))
            pun = fac.get("parent_unit_name") or "مطبخ عام"
            self.tbl_facilities.setItem(i, 3, QTableWidgetItem(pun))

            fac_disp = fac.get("name") + " (" + ftype_str + ")"
            self.cb_sub_facility.addItem(fac_disp, fac.get("id"))
            self.cb_daily_facility.addItem(fac_disp, fac.get("id"))

            QtWidgets.QApplication.processEvents()

    def _create_facility(self):
        name = self.txt_fac_name.text().strip()
        if not name:
            QMessageBox.warning(self, "خطأ", "يرجى كتابة اسم المنشأة.")
            return

        ftype = "KITCHEN" if self.cb_fac_type.currentIndex() == 0 else "BAKERY"
        uid = self.cb_parent_unit.currentData()

        payload = {"name": name, "f_type": ftype, "parent_unit_id": uid}
        ok, resp = self.api_service.create_facility(payload) if self.api_service else (False, 'No API service')
        if ok:
            self.txt_fac_name.clear()
            self._load_facilities()
            QMessageBox.information(self, "نجاح", "تمت الإضافة بنجاح.")
        else:
            QMessageBox.warning(self, "خطأ", f"فشل الإضافة: {resp}")

    def _on_tab_changed(self, idx):
        if idx == 1:
            self._build_subscription_checkboxes()
            self._load_current_subscriptions()
        else:
            self._load_daily_logs()

    def _build_subscription_checkboxes(self):
        for i in reversed(range(self.chk_layout.count())):
            widget = self.chk_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        self._checkbox_list.clear()

        root_units = [u for u in self._units if u.get("parent_id") is None]
        child_map = {}
        for u in self._units:
            pid = u.get("parent_id")
            if pid is not None:
                child_map.setdefault(pid, []).append(u)

        for root in root_units:
            lbl = QLabel("🏕️ " + root["name"])
            lbl.setStyleSheet(
                "font-size: 15px; font-weight: bold; color: #2E6B35; "
                "padding: 8px 2px 2px 2px; border-bottom: 1px solid #ccc;"
            )
            self.chk_layout.addWidget(lbl)

            children = child_map.get(root["id"], [])
            for child in children:
                chk = QCheckBox("    🔹 " + child["name"])
                chk.setStyleSheet("font-size: 14px; padding: 3px 15px;")
                self.chk_layout.addWidget(chk)
                self._checkbox_list[child["id"]] = chk

    def _load_current_subscriptions(self):
        f_id = self.cb_sub_facility.currentData()
        if f_id is None:
            return

        for chk in self._checkbox_list.values():
            chk.setChecked(False)

        ok, subs = self.api_service.get_facility_subscriptions(f_id) if self.api_service else (False, None)
        if ok:
            for s in subs:
                uid = s.get("unit_id")
                if uid in self._checkbox_list:
                    self._checkbox_list[uid].setChecked(True)

    def _save_subscriptions(self):
        f_id = self.cb_sub_facility.currentData()
        if f_id is None:
            return

        selected_units = [uid for uid, chk in self._checkbox_list.items() if chk.isChecked()]
        payload = {"facility_id": f_id, "unit_ids": selected_units}
        ok, resp = self.api_service.subscribe_units(payload) if self.api_service else (False, 'No API service')
        if ok:
            QMessageBox.information(self, "نجاح", "تم حفظ الاشتراكات.")
        else:
            QMessageBox.warning(self, "خطأ", f"فشل الحفظ: {resp}")

    def _create_daily_log(self):
        f_id = self.cb_daily_facility.currentData()
        if f_id is None:
            return

        dt_str = self.dt_daily.date().toString("yyyy-MM-dd")
        meal_idx = self.cb_meal_type.currentIndex()
        meal_types = ("BREAKFAST", "LUNCH", "DINNER", "BREAD")
        m_type = meal_types[meal_idx]

        payload = {
            "facility_id": f_id,
            "log_date": dt_str,
            "meal_type": m_type,
            "notes": "تم الصرف آلياً",
        }
        ok, resp = self.api_service.create_daily_log(payload) if self.api_service else (False, 'No API service')
        if ok:
            b_count = resp.get("items", {}).get("beneficiaries_count")
            QMessageBox.information(
                self,
                "نجاح",
                f"تم تسجيل التقرير للوجبة.\nإجمالي قوة الوحدات المشتركة المستفيدة: {b_count} فرد",
            )
            self._load_daily_logs()
        else:
            QMessageBox.warning(self, "خطأ", f"فشل التسجيل: {resp}")

    def _load_daily_logs(self):
        f_id = self.cb_daily_facility.currentData()
        if f_id is None:
            return

        ok, logs = self.api_service.get_daily_logs(f_id) if self.api_service else (False, None)
        if not ok:
            return

        self.tbl_logs.setRowCount(0)
        for i, log in enumerate(logs):
            self.tbl_logs.insertRow(i)
            self.tbl_logs.setItem(i, 0, QTableWidgetItem(log.get("log_date")))
            self.tbl_logs.setItem(i, 1, QTableWidgetItem(self.cb_daily_facility.currentText()))
            self.tbl_logs.setItem(i, 2, QTableWidgetItem(log.get("meal_type")))
            self.tbl_logs.setItem(
                i, 3, QTableWidgetItem(f"{log.get('beneficiaries_count')} فرد")
            )

            btn_print = QPushButton("🖨️ طباعة")
            btn_print.clicked.connect(
                lambda _, l=log: QMessageBox.information(
                    self,
                    "طباعة",
                    f"سيتم إرسال السجل الخاص بتاريخ {l.get('log_date')} إلى الطابعة...",
                )
            )
            self.tbl_logs.setCellWidget(i, 4, btn_print)
