"""
نظام الإمداد والتموين - شاشة المزامنة
Data Synchronization Screen
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView,
    QPushButton, QLabel, QProgressBar, QGroupBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon

from core.models.sync import SyncLog
from sync.sync_engine import SyncEngine

class SyncScreen(QWidget):
    """شاشة مزامنة البيانات مع الخادم المركزي"""
    sync_completed = Signal(bool)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("مزامنة البيانات")
        self.setWindowIcon(QIcon(":/icons/sync"))
        
        self.sync_engine = SyncEngine()
        self._setup_ui()
        
    def _setup_ui(self):
        """تهيئة واجهة المستخدم"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)
        
        # حالة الاتصال
        self.connection_status = QLabel("حالة الاتصال: غير متصل")
        self.connection_status.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.connection_status)
        
        # زر المزامنة
        self.sync_btn = QPushButton("بدء المزامنة")
        self.sync_btn.setIcon(QIcon(":/icons/sync"))
        self.sync_btn.clicked.connect(self._start_sync)
        main_layout.addWidget(self.sync_btn)
        
        # شريط التقدم
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)
        
        # إحصائيات المزامنة
        stats_group = QGroupBox("إحصائيات المزامنة")
        stats_layout = QHBoxLayout(stats_group)
        
        self.pushed_label = QLabel("0 سجل مرسل")
        self.pulled_label = QLabel("0 سجل مستلم")
        self.errors_label = QLabel("0 خطأ")
        
        stats_layout.addWidget(self.pushed_label)
        stats_layout.addWidget(self.pulled_label)
        stats_layout.addWidget(self.errors_label)
        
        main_layout.addWidget(stats_group)
        
        # سجل المزامنة
        self.log_table = QTableView()
        main_layout.addWidget(self.log_table, stretch=1)
        
        # تحميل آخر سجلات المزامنة
        self._load_sync_logs()
        
    def _load_sync_logs(self):
        """تحميل سجلات المزامنة السابقة"""
        try:
            logs = self.sync_engine.get_sync_logs(limit=50)
            self._update_log_table(logs)
        except Exception as e:
            print(f"Error loading sync logs: {str(e)}")
            
    def _update_log_table(self, logs: list[SyncLog]):
        """تحديث جدول سجلات المزامنة"""
        # TODO: تنفيذ عرض البيانات في الجدول
        pass
        
    def _start_sync(self):
        """بدء عملية المزامنة"""
        self.sync_btn.setEnabled(False)
        self.sync_btn.setText("جاري المزامنة...")
        
        try:
            # تنفيذ المزامنة في خلفية منفصلة
            self.sync_engine.sync_all(
                progress_callback=self._update_progress,
                completion_callback=self._sync_completed
            )
        except Exception as e:
            self._sync_failed(str(e))
            
    def _update_progress(self, current: int, total: int, message: str):
        """تحديث شريط التقدم"""
        progress = int((current / total) * 100) if total > 0 else 0
        self.progress_bar.setValue(progress)
        self.connection_status.setText(f"حالة الاتصال: {message}")
        
    def _sync_completed(self, success: bool, stats: dict):
        """عند اكتمال المزامنة"""
        self.sync_btn.setEnabled(True)
        self.sync_btn.setText("بدء المزامنة")
        self.progress_bar.setValue(100)
        
        if success:
            self.connection_status.setText("حالة الاتصال: مكتمل بنجاح")
            self._update_stats(stats)
            self._load_sync_logs()
        else:
            self.connection_status.setText("حالة الاتصال: فشل في المزامنة")
            
        self.sync_completed.emit(success)
        
    def _sync_failed(self, error: str):
        """عند فشل المزامنة"""
        self.sync_btn.setEnabled(True)
        self.sync_btn.setText("بدء المزامنة")
        self.connection_status.setText(f"حالة الاتصال: خطأ - {error}")
        
    def _update_stats(self, stats: dict):
        """تحديث إحصائيات المزامنة"""
        self.pushed_label.setText(f"{stats['pushed']} سجل مرسل")
        self.pulled_label.setText(f"{stats['pulled']} سجل مستلم")
        self.errors_label.setText(f"{stats['errors']} خطأ")