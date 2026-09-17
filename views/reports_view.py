# Reports View — إدارة التقارير (شجرة + فلاتر + جدول).
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTreeWidget, QTreeWidgetItem, QStackedWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton, QComboBox, QDateEdit,
    QMessageBox, QGroupBox, QGridLayout, QCheckBox,
    QDialog, QPrintDialog, QFileDialog,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QTextDocument

try:
    import qtawesome as qta
except Exception:
    qta = None

REPORT_LIST = (
    ("حركة المخزون اليومية", "fa5s.exchange-alt"),
    ("كشف حساب وحدة مستفيدة", "fa5s.file-invoice"),
    ("تقرير أرصدة المخزون", "fa5s.boxes"),
    ("تحليل الاستهلاك", "fa5s.chart-pie"),
    ("تقرير حصر القوة", "fa5s.users"),
    ("أداء المطابخ والأفران", "fa5s.utensils"),
    ("ملخص توريدات الموردين", "fa5s.truck"),
    ("تقرير المرتجعات", "fa5s.undo"),
    ("تقرير العمل اليومي", "fa5s.clipboard-list"),
)
class ReportsView(QWidget):
    def __init__(self, parent=None, api_service=None):
        super().__init__(parent)
        self.api_service = api_service
        self.main_window = parent
        self.current_report_idx = 0
        self.report_title = None
        self.warehouses_map = {}
        self.units_map = {}
        self.camps_map = {}
        self.categories_map = {}
        self.suppliers_map = {}
        self.facilities_map = {}
        self._init_ui()
