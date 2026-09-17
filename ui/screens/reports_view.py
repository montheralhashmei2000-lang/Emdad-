"""
نظام الإمداد والتموين - شاشة التقارير
Reports and Statistics Screen
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QTableView, QPushButton, QComboBox, QDateEdit,
    QLabel, QMessageBox
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QIcon

from core.services.report_service import ReportService

class ReportsView(QWidget):
    """شاشة التقارير والإحصائيات"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("التقارير والإحصائيات")
        self.setWindowIcon(QIcon(":/icons/reports"))
        
        self.report_service = ReportService()
        self._setup_ui()
        
    def _setup_ui(self):
        """تهيئة واجهة المستخدم"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)
        
        # شريط الفلاتر
        filter_bar = QHBoxLayout()
        
        # نوع التقرير
        self.report_combo = QComboBox()
        self.report_combo.addItem("حركة صنف", "item_movement")
        self.report_combo.addItem("حركة مستودع", "warehouse_movement")
        self.report_combo.addItem("الوارد والمنصرف", "in_out")
        self.report_combo.addItem("العهد", "custody")
        filter_bar.addWidget(QLabel("نوع التقرير:"))
        filter_bar.addWidget(self.report_combo)
        
        # الفترة الزمنية
        self.from_date = QDateEdit(QDate.currentDate().addMonths(-1))
        self.from_date.setCalendarPopup(True)
        filter_bar.addWidget(QLabel("من:"))
        filter_bar.addWidget(self.from_date)
        
        self.to_date = QDateEdit(QDate.currentDate())
        self.to_date.setCalendarPopup(True)
        filter_bar.addWidget(QLabel("إلى:"))
        filter_bar.addWidget(self.to_date)
        
        # زر التحميل
        load_btn = QPushButton("تحميل")
        load_btn.setIcon(QIcon(":/icons/refresh"))
        load_btn.clicked.connect(self._load_report)
        filter_bar.addWidget(load_btn)
        
        main_layout.addLayout(filter_bar)
        
        # تبويبات التقارير
        self.tabs = QTabWidget()
        
        # تبويب البيانات
        self.data_tab = QWidget()
        self.data_table = QTableView()
        data_layout = QVBoxLayout(self.data_tab)
        data_layout.addWidget(self.data_table)
        self.tabs.addTab(self.data_tab, "البيانات")
        
        # تبويب الرسوم البيانية
        self.chart_tab = QWidget()
        # TODO: إضافة الرسوم البيانية
        chart_layout = QVBoxLayout(self.chart_tab)
        chart_layout.addWidget(QLabel("الرسوم البيانية ستظهر هنا"))
        self.tabs.addTab(self.chart_tab, "الرسوم البيانية")
        
        main_layout.addWidget(self.tabs, stretch=1)
        
        # شريط الأدوات
        toolbar = QHBoxLayout()
        
        # زر التصدير
        export_btn = QPushButton("تصدير Excel")
        export_btn.setIcon(QIcon(":/icons/excel"))
        export_btn.clicked.connect(self._export_report)
        toolbar.addWidget(export_btn)
        
        # زر الطباعة
        print_btn = QPushButton("طباعة")
        print_btn.setIcon(QIcon(":/icons/print"))
        print_btn.clicked.connect(self._print_report)
        toolbar.addWidget(print_btn)
        
        toolbar.addStretch()
        main_layout.addLayout(toolbar)
        
    def _load_report(self):
        """تحميل التقرير المحدد"""
        report_type = self.report_combo.currentData()
        from_date = self.from_date.date().toString(Qt.ISODate)
        to_date = self.to_date.date().toString(Qt.ISODate)
        
        try:
            report_data = self.report_service.generate_report(
                report_type=report_type,
                from_date=from_date,
                to_date=to_date
            )
            
            # TODO: عرض البيانات في الجدول
            self._update_table(report_data)
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في تحميل التقرير: {str(e)}")
            
    def _update_table(self, data):
        """تحديث الجدول ببيانات التقرير"""
        # TODO: تنفيذ عرض البيانات في الجدول
        pass
        
    def _export_report(self):
        """تصدير التقرير إلى Excel"""
        try:
            report_type = self.report_combo.currentData()
            from_date = self.from_date.date().toString(Qt.ISODate)
            to_date = self.to_date.date().toString(Qt.ISODate)
            
            file_path = self.report_service.export_to_excel(
                report_type=report_type,
                from_date=from_date,
                to_date=to_date
            )
            
            QMessageBox.information(self, "تم", f"تم التصدير بنجاح إلى: {file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في التصدير: {str(e)}")
            
    def _print_report(self):
        """طباعة التقرير"""
        # TODO: تنفيذ الطباعة
        QMessageBox.information(self, "طباعة", "سيتم تنفيذ الطباعة هنا")