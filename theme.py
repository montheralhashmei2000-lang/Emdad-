"""
Military Warehouse Management System — Unified Design System
All views import from this module to ensure visual consistency.
"""

COLORS = {
    "bg_dark": "#1A2A1A",
    "bg_sidebar": "#1E3321",
    "bg_content": "#F5F3EE",
    "bg_card": "#FFFFFF",
    "bg_table_alt": "#F0EFE8",

    "green_primary": "#2E6B35",
    "green_hover": "#3A8542",
    "gold": "#C5A028",
    "gold_light": "#E8C84A",

    "ok": "#27AE60",
    "warning": "#F39C12",
    "danger": "#C0392B",
    "info": "#2980B9",
    "purple": "#8E44AD",
    "purple_light": "#9B59B6",

    "text_dark": "#1C2B1C",
    "text_medium": "#4A5740",
    "text_light": "#FFFFFF",
    "text_muted": "#888C7A",

    "border": "#C9C6B8",
    "border_dark": "#3E5E3E",
}

FONT_FAMILY = "Cairo, Tajawal, Arial"
FONT_SIZE_SMALL = "11px"
FONT_SIZE_NORMAL = "13px"
FONT_SIZE_LARGE = "15px"
FONT_SIZE_TITLE = "18px"
FONT_SIZE_HEADER = "22px"

SIDEBAR_GROUPS = {
    "الرئيسية": [
        ("الرئيسية", "fa5s.home"),
    ],
    "البيانات الأساسية ⚙️": [
        ("إدارة الأصناف", "fa5s.cubes"),
        ("الموردون", "fa5s.truck"),
        ("الوحدات المستفيدة", "fa5s.users"),
        ("المستودعات", "fa5s.warehouse"),
        ("المطابخ والأفران", "fa5s.utensils"),
    ],
    "العمليات المخزنية 📦": [
        ("أوامر التوجيه المعلقة", "fa5s.bell"),
        ("استلام بضاعة", "fa5s.truck-loading"),
        ("صرف بضاعة", "fa5s.sign-out-alt"),
        ("تحويل مخزني", "fa5s.exchange-alt"),
        ("المرتجعات", "fa5s.undo"),
    ],
    "التشغيل اليومي 📊": [
        ("التفريدة اليومية (حصر القوة)", "fa5s.calendar-check"),
        ("نسب الاستحقاق", "fa5s.balance-scale"),
    ],
    "التقارير والجرد 📈": [
        ("الأرصدة الحالية", "fa5s.boxes"),
        ("جرد المخزون", "fa5s.clipboard-check"),
        ("التقارير", "fa5s.chart-bar"),
    ],
    "الإعدادات 🔧": [
        ("الإعدادات", "fa5s.cog"),
        ("الأرصدة الافتتاحية", "fa5s.clipboard-list"),
    ],
}

APP_STYLESHEET = "".join([
f"""
/* ---- Global ---- */
QWidget {{
    font-family: {FONT_FAMILY};
    font-size: {FONT_SIZE_NORMAL};
    color: {COLORS['text_dark']};
    background-color: {COLORS['bg_content']};
}}

/* ---- Main Window ---- */
QMainWindow {{
    background-color: {COLORS['bg_dark']};
}}

/* ---- Sidebar ---- */
#sidebar {{
    background-color: {COLORS['bg_sidebar']};
    border-left: 2px solid {COLORS['border_dark']};
}}

#sidebar_btn {{
    background-color: transparent;
    color: {COLORS['text_light']};
    font-size: {FONT_SIZE_NORMAL};
    font-family: {FONT_FAMILY};
    text-align: right;
    padding: 10px 12px;
    border-radius: 6px;
    border: none;
}}
#sidebar_btn:hover {{
    background-color: {COLORS['green_hover']};
    color: {COLORS['gold_light']};
}}
#sidebar_btn:checked,
#sidebar_btn[active="true"] {{
    background-color: {COLORS['gold']};
    color: {COLORS['text_dark']};
    font-weight: bold;
}}

#sidebar_group_btn {{
    background-color: rgba(255,255,255,0.08);
    color: {COLORS['gold_light']};
    font-size: 13px;
    font-family: {FONT_FAMILY};
    font-weight: bold;
    text-align: right;
    padding: 8px 10px;
    border: none;
    border-radius: 4px;
    margin-top: 4px;
}}
#sidebar_group_btn:hover {{
    background-color: {COLORS['green_hover']};
}}
#sidebar_group_btn:checked {{
    background-color: rgba(255,255,255,0.12);
}}

#sidebar_items_container {{
    background-color: transparent;
}}

/* ---- Cards ---- */
#card {{
    background-color: {COLORS['bg_card']};
    border-radius: 10px;
    border: 1px solid {COLORS['border']};
}}
#card_title {{
    font-size: {FONT_SIZE_LARGE};
    font-weight: bold;
    color: {COLORS['text_medium']};
}}
#card_value {{
    font-size: 28px;
    font-weight: bold;
    color: {COLORS['text_dark']};
}}

/* ---- Page Header ---- */
#page_header {{
    font-size: {FONT_SIZE_HEADER};
    font-weight: bold;
    color: {COLORS['green_primary']};
    padding-bottom: 4px;
    border-bottom: 2px solid {COLORS['gold']};
}}

/* ---- Buttons ---- */
QPushButton {{
    background-color: {COLORS['green_primary']};
    color: {COLORS['text_light']};
    border: none;
    border-radius: 6px;
    padding: 7px 18px;
    font-size: {FONT_SIZE_NORMAL};
    font-family: {FONT_FAMILY};
}}
QPushButton:hover {{
    background-color: {COLORS['green_hover']};
}}
QPushButton:pressed {{
    background-color: {COLORS['bg_dark']};
}}
QPushButton#danger_btn {{
    background-color: {COLORS['danger']};
}}
QPushButton#danger_btn:hover {{
    background-color: #E74C3C;
}}
QPushButton#gold_btn {{
    background-color: {COLORS['gold']};
    color: {COLORS['text_dark']};
    font-weight: bold;
}}
QPushButton#gold_btn:hover {{
    background-color: {COLORS['gold_light']};
}}

/* ---- Inputs ---- */
QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    border-radius: 5px;
    padding: 5px 8px;
    font-size: {FONT_SIZE_NORMAL};
    font-family: {FONT_FAMILY};
}}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus {{
    border: 1.5px solid {COLORS['green_primary']};
}}

/* ---- Tables ---- */
QTableWidget {{
    background-color: {COLORS['bg_card']};
    alternate-background-color: {COLORS['bg_table_alt']};
    gridline-color: {COLORS['border']};
    font-size: {FONT_SIZE_NORMAL};
    font-family: {FONT_FAMILY};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
}}
QTableWidget::item:selected {{
    background-color: {COLORS['green_primary']};
    color: {COLORS['text_light']};
}}
QHeaderView::section {{
    background-color: {COLORS['green_primary']};
    color: {COLORS['text_light']};
    font-weight: bold;
    font-size: {FONT_SIZE_NORMAL};
    padding: 7px 5px;
    border: none;
}}

/* ---- Dialogs ---- */
QDialog {{
    background-color: {COLORS['bg_content']};
}}

/* ---- Tab Widget ---- */
QTabWidget::pane {{
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    background: {COLORS['bg_card']};
}}
QTabBar::tab {{
    background: {COLORS['bg_table_alt']};
    color: {COLORS['text_medium']};
    padding: 7px 16px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-family: {FONT_FAMILY};
}}
QTabBar::tab:selected {{
    background: {COLORS['green_primary']};
    color: {COLORS['text_light']};
    font-weight: bold;
}}

/* ---- Status Labels ---- */
#status_ok    {{ color: {COLORS['ok']};      font-weight: bold; }}
#status_warn  {{ color: {COLORS['warning']}; font-weight: bold; }}
#status_danger{{ color: {COLORS['danger']};  font-weight: bold; }}

/* ---- Scrollbar ---- */
QScrollBar:vertical {{
    background: {COLORS['bg_content']};
    width: 10px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {COLORS['border']};
    border-radius: 5px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background: {COLORS['green_primary']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
"""
])


def apply_theme(app):
    """Call once at startup: app.apply_theme(QApplication_instance)"""
    app.setStyleSheet(APP_STYLESHEET)


def make_header_label(text: str):
    """Return a styled page-header QLabel."""
    from PyQt6.QtWidgets import QLabel
    lbl = QLabel(text)
    lbl.setObjectName("page_header")
    return lbl


def make_card(title: str, value: str, color: str = None):
    """Return a styled dashboard stat card QFrame."""
    from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel
    from PyQt6.QtCore import Qt

    card = QFrame()
    card.setObjectName("card")
    layout = QVBoxLayout(card)
    layout.setContentsMargins(16, 14, 16, 14)

    title_lbl = QLabel(title)
    title_lbl.setObjectName("card_title")
    title_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)

    value_lbl = QLabel(value)
    value_lbl.setObjectName("card_value")
    value_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    if color:
        value_lbl.setStyleSheet(f"color: {color}; font-size: 28px; font-weight: bold;")

    layout.addWidget(title_lbl)
    layout.addWidget(value_lbl)
    return card, value_lbl
