# NOTE: هذا الملف أُعيد بناؤه يدوياً من ملف emergency_view.pyc
# الملف الأصلي مُصرَّف بصيغة Python 3.14 (RC) التي لا تدعمها أدوات فك التشفير
# الحالية. تم استخراج كل الأسماء والنصوص (بما فيها نص التعليمات الكامل) بدقة
# كاملة عبر قارئ marshal مخصص، وأُعيد بناء المنطق بالاعتماد عليها وعلى نمط
# الملفات السابقة من نفس المشروع. هذا الملف بسيط نسبياً وأغلب محتواه نصوص
# ثابتة، لذا مستوى الثقة في الإعادة عالٍ جداً.

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QGridLayout
)
from PyQt6.QtCore import Qt

import qtawesome as qta
from theme import COLORS
from excel_helper import export_emergency_template


class EmergencyView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._init_ui()

    def _init_ui(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(20)
        lay.setContentsMargins(20, 20, 20, 20)

        header_frame = QFrame()
        header_frame.setStyleSheet(
            'background-color: rgba(200, 30, 30, 0.15); border: 2px solid '
            + COLORS['danger'] + '; border-radius: 10px;'
        )
        h_lay = QHBoxLayout(header_frame)

        warn_icon = QLabel()
        warn_icon.setPixmap(qta.icon('fa5s.exclamation-triangle').pixmap(32, 32))
        h_lay.addWidget(warn_icon)

        lbl = QLabel('⚠️ وضع الطوارئ نشط - السيرفر الرئيسي مغلق أو الشبكة غير متاحة')
        lbl.setStyleSheet(
            'font-size: 22px; color: ' + COLORS['danger']
            + '; font-weight: bold; background: transparent; border: none;'
        )
        h_lay.addWidget(lbl)
        lay.addWidget(header_frame)

        inst_label = QLabel(
            "<b>تعليمات العمل الفوري:</b><br><br>"
            "1. النظام الآن منعزل تماماً ولا يمكنه الوصول للبيانات المركزية لحمايتها من التضارب.<br>"
            "2. لتسجيل العمليات (صرف، استلام، تحويل) يرجى تحميل قالب الإكسيل الخاص بالطوارئ.<br>"
            "3. قم بتعبئة بيانات العمليات بدقة عالية داخل ملف الإكسيل طوال فترة الانقطاع.<br>"
            "4. بعد عودة السيرفر للعمل وتوفر الاتصال، ستقوم برفع الملف من خلال "
            "'مزامنة بيانات الطوارئ' ليتم تدقيقها وحفظها."
        )
        inst_label.setWordWrap(True)
        inst_label.setStyleSheet('font-size: 16px; line-height: 1.5; color: #EEE;')
        lay.addWidget(inst_label)

        grid = QGridLayout()

        self.btn_export = QPushButton('تحميل قالب إكسيل لعمليات الطوارئ 📥')
        self.btn_export.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_export.setStyleSheet(
            'background-color: ' + COLORS['gold']
            + '; color: black; font-weight: bold; font-size: 18px; padding: 20px; border-radius: 8px;'
        )
        self.btn_export.clicked.connect(self._do_export)
        grid.addWidget(self.btn_export)

        self.btn_print = QPushButton('طباعة مستند ورقي فارغ (للتعبئة اليدوية) 🖨️')
        self.btn_print.setStyleSheet(
            'background-color: ' + COLORS['green_primary']
            + '; color: white; font-weight: bold; font-size: 18px; padding: 20px; border-radius: 8px;'
        )
        self.btn_print.clicked.connect(self._do_print)
        grid.addWidget(self.btn_print)

        lay.addLayout(grid)
        lay.addStretch()

    def _do_export(self):
        export_emergency_template()

    def _do_print(self):
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(
            self, 'تحت التطوير',
            'سيتم تفعيل طباعة المستند الورقي الفارغ لاحقاً. يرجى التركيز على تعبئة ملف الإكسيل لضمان حفظ العمليات.'
        )
