"""نظام الإمداد والتموين - Material Design 3 Vibrant Theme"""
from __future__ import annotations
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import QApplication, QLabel, QGraphicsDropShadowEffect

# ===== Material Design 3 Vibrant Palette =====
PRIMARY = "#10B981"
PRIMARY_LIGHT = "#34D399"
PRIMARY_DARK = "#059669"
ACCENT = "#F59E0B"
DANGER = "#EF4444"
SUCCESS = "#22C55E"
WARNING = "#EAB308"
INFO = "#3B82F6"
PURPLE = "#A855F7"
TEAL = "#14B8A6"
GOLD = "#FBBF24"
PINK = "#EC4899"

BG = "#F9FAFB"
BG_SECONDARY = "#F3F4F6"
BG_CARD = "#FFFFFF"
BG_SIDEBAR = "#111827"
BG_SIDEBAR_END = "#1E293B"
TEXT = "#111827"
TEXT_SEC = "#6B7280"
TEXT_MUTED = "#9CA3AF"
TEXT_LIGHT = "#F9FAFB"
BORDER = "#E5E7EB"


def get_arabic_font():
    return "Cairo"


def get_font(size=14, bold=False):
    f = QFont(get_arabic_font(), size)
    f.setBold(bold)
    return f


def apply_card_shadow(widget, color="#00000030", blur=50, offset=18):
    s = QGraphicsDropShadowEffect()
    s.setBlurRadius(blur)
    s.setColor(QColor(color))
    s.setOffset(0, offset)
    widget.setGraphicsEffect(s)

QTableWidget, QTableView {
    background-color: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px;
    gridline-color: #ECF0F1; font-family: 'Cairo', sans-serif; font-size: 13px;
}
QTableWidget::item, QTableView::item { padding: 10px 14px; border-bottom: 1px solid #ECF0F1; }
QTableWidget::item:selected, QTableView::item:selected { background-color: #ECFDF5; color: #111827; }
QHeaderView::section { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10B981, stop:1 #06B6D4); color: white; font-weight: 700; padding: 12px 14px; border: none; }
QTableView::row:nth-child(even) { background-color: #F8F9FA; }

QTabWidget::pane { background-color: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px; padding: 12px; margin-top: -1px; }
QTabBar::tab { background-color: #ECF0F1; color: #7F8C8D; font-family: 'Cairo', sans-serif; font-size: 14px; font-weight: 600; padding: 10px 20px; margin-left: 2px; border-top-left-radius: 12px; border-top-right-radius: 12px; border: 1px solid #E5E7EB; }
QTabBar::tab:selected { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10B981, stop:1 #06B6D4); color: white; border-bottom: 2px solid #10B981; }
QTabBar::tab:hover:!selected { background-color: #D5DBDB; }

QLabel { font-family: 'Cairo', sans-serif; color: #2C3E50; background: transparent; }
QLabel#headerTitle { font-size: 28px; font-weight: 800; color: #111827; padding: 8px 0 16px 0; }
QLabel#cardTitle { font-size: 13px; font-weight: 600; color: #7F8C8D; }
QLabel#cardValue { font-size: 28px; font-weight: 800; color: #2C3E50; }
QLabel#badge { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #EF4444, stop:1 #DC2626); color: white; border-radius: 12px; padding: 4px 10px; font-size: 11px; font-weight: 700; }

QToolTip { background-color: #2C3E50; color: white; border: none; border-radius: 12px; padding: 6px 12px; font-family: 'Cairo', sans-serif; font-size: 12px; }

QProgressBar { background-color: #F3F4F6; border: 1px solid #E5E7EB; border-radius: 12px; height: 20px; text-align: center; }
QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10B981, stop:1 #06B6D4); border-radius: 11px; }

QCheckBox { font-family: 'Cairo', sans-serif; font-size: 14px; color: #2C3E50; spacing: 10px; }
QCheckBox::indicator { width: 20px; height: 20px; border: 2px solid #E5E7EB; border-radius: 6px; background: white; }
QCheckBox::indicator:checked { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10B981, stop:1 #06B6D4); border: 2px solid #10B981; }
QRadioButton { font-family: 'Cairo', sans-serif; font-size: 14px; color: #2C3E50; spacing: 10px; }
QRadioButton::indicator { width: 20px; height: 20px; border: 2px solid #E5E7EB; border-radius: 10px; background: white; }
QRadioButton::indicator:checked { border: 2px solid #10B981; background-color: #10B981; }

QSlider::groove:horizontal { height: 6px; background: #E5E7EB; border-radius: 3px; }
QSlider::sub-page:horizontal { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10B981, stop:1 #06B6D4); border-radius: 3px; }
QSlider::handle:horizontal { width: 18px; height: 18px; margin: -6px 0; background: #FFFFFF; border: 2px solid #10B981; border-radius: 9px; }

QGroupBox { border: 2px solid #E5E7EB; border-radius: 12px; margin-top: 12px; padding: 12px; font-weight: 700; color: #111827; background: #FFFFFF; }
QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top right; padding: 0 8px; color: #10B981; }

QDialog { background-color: #F9FAFB; }

QStatusBar { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #111827, stop:1 #1E293B); color: #ECF0F1; padding: 6px 12px; font-family: 'Cairo', sans-serif; }

QTreeWidget, QTreeView, QListWidget, QListView { background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px; font-family: 'Cairo', sans-serif; padding: 6px; }
QTreeWidget::item, QListWidget::item { padding: 8px 12px; border-radius: 6px; }
QTreeWidget::item:hover, QListWidget::item:hover { background: #ECF0F1; }
QTreeWidget::item:selected, QListWidget::item:selected { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ECFDF5, stop:1 #DBEAFE); color: #059669; }

QWidget#sidebar { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #111827, stop:1 #1E293B); }

QPushButton#sidebar_btn, QPushButton#sidebar_btn_sub {
    background-color: transparent; color: #9CA3AF; border: none;
    padding: 10px 14px; font-family: 'Cairo', sans-serif;
    font-size: 13px; text-align: right; border-radius: 10px;
}
QPushButton#sidebar_btn:hover, QPushButton#sidebar_btn_sub:hover {
    background-color: #374151; color: #FFFFFF;
}
QPushButton#sidebar_btn:checked, QPushButton#sidebar_btn_sub:checked {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10B981, stop:1 #06B6D4);
    color: #FFFFFF; font-weight: 700;
}
QPushButton#sidebar_group_btn {
    color: #A855F7; font-size: 12px; font-weight: 800;
    background-color: rgba(168, 85, 247, 0.1); border: none;
    padding: 10px 14px; text-align: right; border-radius: 10px; letter-spacing: 1px;
}
QPushButton#sidebar_group_btn:hover {
    color: #FFFFFF; background-color: rgba(168, 85, 247, 0.2);
}
"""
CSS = """
QMainWindow, QWidget { background-color: #F9FAFB; font-family: 'Cairo', 'Segoe UI', sans-serif; color: #111827; }

QScrollBar:vertical { background: transparent; width: 10px; }
QScrollBar::handle:vertical { background: #95A5A6; min-height: 30px; border-radius: 5px; }
QScrollBar::handle:vertical:hover { background: #7F8C8D; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { background: transparent; height: 10px; }
QScrollBar::handle:horizontal { background: #95A5A6; min-width: 30px; border-radius: 5px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10B981, stop:1 #06B6D4);
    color: white; border: none; border-radius: 12px;
    padding: 10px 20px; font-family: 'Cairo', sans-serif;
    font-size: 14px; font-weight: 700; min-height: 38px;
}
QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #0891B2); }
QPushButton:pressed { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #047857, stop:1 #0E7490); }
QPushButton:disabled { background: #E5E7EB; color: #9CA3AF; }

QPushButton[btnType="danger"] { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #EF4444, stop:1 #DC2626); }
QPushButton[btnType="danger"]:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #DC2626, stop:1 #B91C1C); }
QPushButton[btnType="success"] { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #22C55E, stop:1 #16A34A); }
QPushButton[btnType="success"]:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #16A34A, stop:1 #15803D); }
QPushButton[btnType="warning"] { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #F59E0B, stop:1 #D97706); color: white; }
QPushButton[btnType="warning"]:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #D97706, stop:1 #B45309); }
QPushButton[btnType="info"] { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3B82F6, stop:1 #2563EB); }
QPushButton[btnType="info"]:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563EB, stop:1 #1D4ED8); }
QPushButton[btnType="ghost"] { background-color: transparent; color: #10B981; border: 2px solid #10B981; border-radius: 12px; }
QPushButton[btnType="ghost"]:hover { background-color: #ECFDF5; }
QPushButton[btnType="icon"] { background-color: transparent; color: #7F8C8D; border: none; padding: 6px; border-radius: 8px; }
QPushButton[btnType="icon"]:hover { background-color: #ECF0F1; color: #10B981; }

QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #FFFFFF; border: 2px solid #E5E7EB; border-radius: 12px;
    padding: 10px 14px; font-family: 'Cairo', sans-serif; font-size: 14px; min-height: 38px;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus { border: 2px solid #10B981; background-color: #FFFFFF; }
QLineEdit:placeholder { color: #9CA3AF; }

QComboBox {
    background-color: #FFFFFF; border: 2px solid #E5E7EB; border-radius: 12px;
    padding: 10px 14px; font-family: 'Cairo', sans-serif; font-size: 14px; min-height: 38px;
}
QComboBox:focus { border: 2px solid #10B981; }
QComboBox::drop-down { border: none; width: 30px; }
QComboBox::down-arrow { image: none; border-left: 5px solid transparent; border-right: 5px solid transparent; border-top: 6px solid #7F8C8D; margin-right: 8px; }
QComboBox QAbstractItemView { background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px; padding: 4px; selection-background-color: #ECFDF5; }
"""
# ================ التوافق ================
apply_theme = setup_theme
COLORS = {
    "green_primary": PRIMARY_COLOR,
    "green_light": PRIMARY_LIGHT,
    "green_dark": PRIMARY_DARK,
    "blue_primary": SECONDARY_COLOR,
    "orange": ACCENT_COLOR,
    "danger": DANGER_COLOR,
    "success": SUCCESS_COLOR,
    "warning": WARNING_COLOR,
    "info": INFO_COLOR,
    "gold": "#D4A017",
    "bg": BG_COLOR,
    "card": CARD_BG,
}
SIDEBAR_GROUPS = {
    "الرئيسية": [("لوحة القيادة", "fa5s.home")],
    "إدارة المخزون": [
        ("إدارة الأصناف", "fa5s.box-open"),
        ("الموردون", "fa5s.truck"),
        ("المستودعات", "fa5s.warehouse"),
        ("الوحدات المستفيدة", "fa5s.users"),
    ],
    "الحركات": [
        ("استلام بضاعة", "fa5s.arrow-down"),
        ("صرف بضاعة", "fa5s.arrow-up"),
        ("تحويل مخزني", "fa5s.exchange-alt"),
        ("المرتجعات", "fa5s.undo"),
    ],
    "المراقبة": [
        ("جرد المخزون", "fa5s.clipboard-check"),
        ("الأرصدة الحالية", "fa5s.chart-line"),
        ("التقارير", "fa5s.file-alt"),
    ],
    "إعدادات النظام": [
        ("الإعدادات", "fa5s.cog"),
        ("مزامنة بيانات الطوارئ", "fa5s.sync-alt"),
    ],
}

def make_header_label(text: str):
    from PyQt6.QtWidgets import QLabel
    lbl = QLabel(text)
    lbl.setStyleSheet("font-size: 22px; font-weight: bold; color: #1B5E20; padding: 10px 0;")
    return lbl

def make_card(title: str, value_text: str, color: str = PRIMARY_COLOR):
    from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
    card = QFrame()
    card.setObjectName("card")
    card.setStyleSheet(f"QFrame#card {{ background-color: {CARD_BG}; border: 1px solid {BORDER_COLOR}; border-radius: 8px; padding: 15px; }} QLabel {{ font-size: 14px; color: {TEXT_PRIMARY}; }}")
    layout = QVBoxLayout(card)
    layout.setContentsMargins(10, 10, 10, 10)
    lbl_title = QLabel(title)
    lbl_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #757575;")
    lbl_value = QLabel(str(value_text))
    lbl_value.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {color};")
    layout.addWidget(lbl_title)
    layout.addWidget(lbl_value)
    return card, lbl_value
