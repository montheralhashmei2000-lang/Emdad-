import pandas as pd
from PyQt6.QtWidgets import QTableWidget, QFileDialog, QMessageBox


def export_table_to_excel(table: QTableWidget, parent_widget=None, default_filename='export.xlsx'):
    """
    يقرأ محتويات جدول QTableWidget ويقوم بحفظها كملف Excel (.xlsx).
    """
    path, _ = QFileDialog.getSaveFileName(parent_widget, 'تصدير إلى إكسيل', default_filename, 'Excel Files (*.xlsx)')
    if not path:
        return None

    headers = []
    skip_cols = []
    for c in range(table.columnCount()):
        h = table.horizontalHeaderItem(c)
        h_text = h.text() if h else str(c)
        if 'إجراء' in h_text or 'Action' in h_text:
            skip_cols.append(c)
            continue
        headers.append(h_text)

    data = []
    for r in range(table.rowCount()):
        row_data = []
        for c in range(table.columnCount()):
            if c in skip_cols:
                continue
            it = table.item(r, c)
            row_data.append(it.text() if it else '')
        data.append(row_data)

    df = pd.DataFrame(data, columns=headers)
    try:
        df.to_excel(path, index=False)
        QMessageBox.information(parent_widget, 'نجاح', f'تم التصدير بنجاح إلى:\n{path}')
    except Exception as e:
        QMessageBox.critical(parent_widget, 'خطأ', f'فشل التصدير:\n{str(e)}')
        return None


def import_excel_to_dataframe(parent_widget):
    """
    يطلب من المستخدم اختيار ملف إكسل ويعيده كـ DataFrame للتعامل معه جدولياً أو إرساله للـ API.
    """
    path, _ = QFileDialog.getOpenFileName(parent_widget, 'استيراد من إكسيل', '', 'Excel Files (*.xlsx *.xls)')
    if not path:
        return None

    try:
        df = pd.read_excel(path)
        return df
    except Exception as e:
        QMessageBox.critical(parent_widget, 'خطأ', f'فشل قراءة الملف:\n{str(e)}')
        return None


def export_template(columns: list, parent_widget, default_filename='template.xlsx', instructions=None):
    """
    ينشئ ملف إكسل فارغ يحتوي على الأعمدة المعطاة كقالب (Template) ليعبئه المستخدم.
    """
    path, _ = QFileDialog.getSaveFileName(parent_widget, 'حفظ القالب لاستيراد البيانات', default_filename, 'Excel Files (*.xlsx)')
    if not path:
        return None

    df = pd.DataFrame(columns=columns)
    try:
        with pd.ExcelWriter(path) as writer:
            df.to_excel(writer, sheet_name='البيانات', index=False)
            if instructions:
                df_inst = pd.DataFrame({'تعليمات هامة لتعبئة الملف': instructions})
                df_inst.to_excel(writer, sheet_name='التعليمات', index=False)

        QMessageBox.information(parent_widget, 'نجاح', 'تم حفظ القالب بنجاح.')
    except Exception as e:
        QMessageBox.critical(parent_widget, 'خطأ', f'فشل إنشاء القالب:\n{str(e)}')
        return None


def export_emergency_template(parent_widget, default_filename='Emergency_Offline.xlsx'):
    """
    يصدر قالب عمليات الطوارئ بـ 4 أوراق عمل منفصلة حسب نوع العملية.
    """
    path, _ = QFileDialog.getSaveFileName(parent_widget, 'حفظ قالب عمليات الطوارئ (الإكسيل)', default_filename, 'Excel Files (*.xlsx)')
    if not path:
        return None

    sheets_config = {
        'صرف استحقاقات': ['تاريخ العملية', 'كود الصنف', 'اسم الصنف', 'الكمية', 'الوحدة', 'المستودع المصروف منه', 'الوحدة المستلمة', 'رقم المستند الورقي', 'ملاحظات'],
        'عمليات المطابخ': ['تاريخ العملية', 'المطبخ الوجهة', 'الوجبة', 'القوة الفردية', 'كود الصنف', 'اسم الصنف', 'الكمية', 'الوحدة', 'المستودع', 'رقم المستند الورقي', 'ملاحظات'],
        'التوريد والاستلام': ['تاريخ العملية', 'المورد', 'كود الصنف', 'اسم الصنف', 'الكمية الموردة', 'الوحدة', 'المستودع المدخل إليه', 'رقم مستند التوريد', 'ملاحظات'],
        'تحويل ومرتجعات': ['تاريخ العملية', 'نوع الحركة', 'كود الصنف', 'المستودع المصدر', 'المستودع الوجهة / المرجع', 'الكمية', 'المستند الورقي'],
    }

    try:
        with pd.ExcelWriter(path) as writer:
            for sheet_name, cols in sheets_config.items():
                df = pd.DataFrame(columns=cols)
                df.to_excel(writer, sheet_name=sheet_name, index=False)

            instructions = ['1. لا تقم بتغيير أسماء أوراق العمل بالأسفل.', '2. يجب إدخال كود الصنف بشكل دقيق لضمان المزامنة.', '3. في شيت التحويل والمرتجعات، نوع الحركة يكون إما (مرتجع، تحويل، أو تالف).']
            df_inst = pd.DataFrame({'تعليمات هامة للعمل بنظام الطوارئ': instructions})
            df_inst.to_excel(writer, sheet_name='التعليمات (إقرأني)', index=False)

        QMessageBox.information(parent_widget, 'نجاح', 'تم إنشاء وحفظ قالب الطوارئ بنجاح. يرجى تعبئته بدقة لحين عودة السيرفر للعمل.')
    except Exception as e:
        QMessageBox.critical(parent_widget, 'خطأ', f'فشل إنشاء قالب الطوارئ:\n{str(e)}')
        return None