"""
وحدة الطباعة المشتركة — Military Print Helper
تولد مستندات HTML احترافية بطابع عسكري رسمي وترسلها للطباعة عبر QPrintPreviewDialog.
تم تلافي أي مشكلة مع محرك Bidi في Qt عبر عزل العناوين (بدون نقطتين) عن البيانات 
في مربعات جدولية صلبة لتظهر كما نكتبها بیدنا من اليمين لليسار.
"""
from PyQt6.QtWidgets import QWidget
from PyQt6.QtPrintSupport import QPrinter, QPrintPreviewDialog
from PyQt6.QtGui import QTextDocument
from datetime import date, datetime
import os


def _get_settings(parent_widget=None):
    lines = []
    logo_base64 = ''

    if parent_widget:
        api = getattr(parent_widget, 'api_service', None)

        if not api and hasattr(parent_widget, 'parent') and parent_widget.parent():
            api = getattr(parent_widget.parent(), 'api_service', None)

        if api:
            ok, res = api.get_system_settings()

            if ok:
                org = res.get('org_name', '')

                if org:
                    lines.extend([x for x in org.split('\n') if x.strip()])

                contact = res.get('contact_info', '')

                if contact:
                    lines.extend([x for x in contact.split('\n') if x.strip()])

                if res.get('org_logo_base64'):
                    logo_base64 = res['org_logo_base64']

    return (lines, logo_base64)


def _get_org_html(parent_widget=None):
    lines, _ = _get_settings(parent_widget)

    html = '<div dir="rtl" style="text-align:right; font-weight:bold; line-height:1.2;">'

    for i, line in enumerate(lines):
        if i == 0:
            html += f'<span style="font-size:15px;">{line}</span><br>'
        else:
            html += f'<span style="font-size:13px;">{line}</span><br>'

    html += '</div>'
    return html


def _get_current_username(parent_widget=None):
    if parent_widget:
        api = getattr(parent_widget, 'api_service', None)

        if not api and hasattr(parent_widget, 'parent') and parent_widget.parent():
            api = getattr(parent_widget.parent(), 'api_service', None)

        if api and hasattr(api, 'current_user_id') and api.current_user_id:
            mw = parent_widget

            while mw:
                if hasattr(mw, 'current_user') and mw.current_user:
                    return mw.current_user.get('full_name', '')

                mw = mw.parent() if hasattr(mw, 'parent') and callable(mw.parent) else None

    return ''


def _document_header(date_str, ref_str, title, org_html, title_color='#C0392B', header_ref_label='رقم السند', logo_base64='', show_manager_approval=False):
    ref_display = ref_str if ref_str else '................'

    logo_html = '&nbsp;'

    if logo_base64:
        logo_html = f'<img src="data:image/png;base64,{logo_base64}" height="95" style="max-height:95px; object-fit:contain;">'

    approval_box = ''

    if show_manager_approval:
        approval_box = '''
        <div style="border:1px solid #333; padding:5px; margin-right:15px; text-align:center; float:left; width:150px;">
            <div style="font-size:10px; font-weight:bold; border-bottom:1px solid #ccc; padding-bottom:3px; margin-bottom:15px;">مصادقة رئيس شعبة الامداد والتموين</div>
            <div style="font-size:10px; color:#555;">التوقيع: ...................</div>
        </div>
        '''

    return f'''
<table width="100%" cellpadding="0" cellspacing="0" style="font-family: Arial, sans-serif; margin-bottom:2px; border:none;">
  <tr>
    <td width="33%" align="left" valign="top">
      {approval_box}
      <table border="0" cellpadding="1" cellspacing="0" style="font-size:12px; line-height:1.2; float:right;">
        <tr>
          <td align="right" dir="rtl">{date_str}</td>
          <td align="right" dir="rtl" style="font-weight:bold;">التاريخ</td>
        </tr>
        <tr>
          <td align="right" dir="rtl">{ref_display}</td>
          <td align="right" dir="rtl" style="font-weight:bold;">{header_ref_label}</td>
        </tr>
        <tr>
          <td align="right" dir="rtl">............</td>
          <td align="right" dir="rtl" style="font-weight:bold;">رقم القيد</td>
        </tr>
      </table>
      <div style="clear:both;"></div>
    </td>
    <td width="34%" align="center" valign="middle">
      {logo_html}
    </td>
    <td width="33%" align="right" valign="top">
      {org_html}
    </td>
  </tr>
</table>
<hr style="border:2px solid #2E6B35; margin:3px 0;">
<table width="100%" border="0" cellpadding="0" cellspacing="0" style="margin:2px 0 5px 0;">
  <tr>
    <td width="10%">&nbsp;</td>
    <td width="20%" align="center" valign="middle">
      <div dir="rtl" style="font-size:14px; font-weight:bold; text-align:center;">رقم {ref_display}</div>
    </td>
    <td width="40%" align="center" valign="middle">
      <h3 style="color:{title_color}; margin:0; font-size:16px; white-space:nowrap;">{title}</h3>
    </td>
    <td width="20%" align="center" valign="middle">
      <div dir="rtl" style="font-size:14px; font-weight:bold; text-align:center; color:transparent;">رقم {ref_display}</div>
    </td>
    <td width="10%">&nbsp;</td>
  </tr>
</table>
'''


def _info_row_2cols(label_right, val_right, label_left, val_left):
    return f'''<tr>
      <td width="35%" align="right" dir="rtl" style="padding:2px 8px; font-size:12px; border-bottom:1px dotted #bbb;">{val_left}</td>
      <td width="15%" align="right" dir="rtl" style="font-weight:bold; padding:2px 8px; font-size:12px; border-bottom:1px dotted #bbb; background:#fafafa; color:#333; white-space:nowrap;">{label_left}</td>
      <td width="35%" align="right" dir="rtl" style="padding:2px 8px; font-size:12px; border-bottom:1px dotted #bbb;">{val_right}</td>
      <td width="15%" align="right" dir="rtl" style="font-weight:bold; padding:2px 8px; font-size:12px; border-bottom:1px dotted #bbb; background:#fafafa; color:#333; white-space:nowrap;">{label_right}</td>
    </tr>'''


def _info_row_full(label_right, val_right):
    return f'''<tr>
      <td width="85%" colspan="3" align="right" dir="rtl" style="padding:2px 8px; font-size:12px; border-bottom:1px dotted #bbb;">{val_right}</td>
      <td width="15%" align="right" dir="rtl" style="font-weight:bold; padding:2px 8px; font-size:12px; border-bottom:1px dotted #bbb; background:#fafafa; color:#333; white-space:nowrap;">{label_right}</td>
    </tr>'''


def _section_header(title):
    return f'<tr><td colspan="4" align="right" dir="rtl" style="padding:2px 5px; font-weight:bold; font-size:13px; border-bottom:1px solid #2E6B35; color:#2E6B35;">{title}</td></tr>'


def _items_table(headers, rows, col_widths=None):
    headers_rev = headers[::-1]

    if col_widths is None:
        n = len(headers)

        if n == 5:
            col_widths = ['20%', '35%', '10%', '10%', '25%']
        elif n == 6:
            col_widths = ['15%', '25%', '10%', '10%', '20%', '20%']
        elif n == 7:
            col_widths = ['12%', '20%', '8%', '8%', '12%', '20%', '20%']
        else:
            w = f'{100 // n}%'
            col_widths = [w] * n

    widths_rev = col_widths[::-1]

    html = '<table width="100%" style="border-collapse:collapse; font-family: Arial, sans-serif; font-size:11px; margin-bottom:5px;">'
    html += '<thead><tr>'

    for i, h in enumerate(headers_rev):
        html += f'<th width="{widths_rev[i]}" dir="rtl" style="background:#2E6B35; color:white; padding:3px 4px; border:1px solid #333; text-align:center; font-size:11px;">{h}</th>'

    html += '</tr></thead><tbody>'

    if not rows:
        html += '<tr style="background:#ffffff;"><td colspan="{}" align="center" dir="rtl" style="padding:8px; font-size:12px;">لا توجد أصناف</td></tr>'.format(len(headers))
    else:
        for i, row in enumerate(rows):
            bg = '#f9f9f9' if i % 2 == 0 else '#ffffff'
            html += f'<tr style="background:{bg};">'

            row_rev = row[::-1]

            for j, cell in enumerate(row_rev):
                html += f'<td width="{widths_rev[j]}" align="center" dir="rtl" style="padding:2px 3px; border:1px solid #999; font-size:10px;">{cell}</td>'

            html += '</tr>'

    html += '</tbody></table>'
    return html


def _signatures(type_, master_info=None):
    if master_info is None:
        master_info = {}

    if type_ in ('issue', 'transfer'):
        return '''
        <table width="100%" style="font-family: Arial, sans-serif; font-size:14px; margin-top:20px; border:none;">
        <tr>
          <!-- Left Signature (Col 1) -->
          <td width="50%" align="left" valign="top" style="padding-left:40px;">
            <div dir="rtl" style="text-align:center; display:inline-block;">
              <b>ركن إدارة الإمداد</b>
            </div>
          </td>
          <!-- Right Signature (Col 2) -->
          <td width="50%" align="right" valign="top" style="padding-right:40px;">
            <div dir="rtl" style="text-align:center; display:inline-block;">
              <b>مكتب إدارة الإمداد</b>
            </div>
          </td>
        </tr>
        </table>
        '''

    if type_ == 'receive':
        warehouse = master_info.get('warehouse', '')
        supervision = master_info.get('supervision', '')
        audit = master_info.get('audit', '')

        return f'''
        <table width="100%" style="font-family: Arial, sans-serif; font-size:13px; margin-top:20px; border:none;">
        <tr>
          <!-- Col 1 -->
          <td width="25%" align="center" valign="top">
            <div dir="rtl" style="text-align:center; display:inline-block;">
              <b>ركن إدارة الإمداد</b>
            </div>
          </td>
          <!-- Col 2 -->
          <td width="25%" align="center" valign="top">
            <div dir="rtl" style="text-align:center; display:inline-block;">
              <b>مدير مخزن</b><br>
              <span style="font-size:13px; color:#555;">{warehouse}</span>
            </div>
          </td>
          <!-- Col 3 -->
          <td width="25%" align="center" valign="top">
            <div dir="rtl" style="text-align:center; display:inline-block;">
              <b>المراجعة والتدقيق</b><br>
              <span style="font-size:13px; color:#555;">{audit}</span>
            </div>
          </td>
          <!-- Col 4 -->
          <td width="25%" align="center" valign="top">
            <div dir="rtl" style="text-align:center; display:inline-block;">
              <b>الرقابة والتفتيش</b><br>
              <span style="font-size:13px; color:#555;">{supervision}</span>
            </div>
          </td>
        </tr>
        </table>
        '''

    warehouse = master_info.get('warehouse', '')

    if not warehouse:
        warehouse = '..................'

    return f'''
        <table width="100%" style="font-family: Arial, sans-serif; font-size:13px; margin-top:15px; border:none;">
        <tr>
          <!-- Left Signature (Col 1) -->
          <td width="50%" align="left" valign="top" style="padding-left:40px;">
            <div dir="rtl" style="text-align:center; display:inline-block;">
              <b>الجهة المسلّمة</b><br>
              <span style="font-size:12px; color:#555;">{warehouse}</span>
            </div>
          </td>
          <!-- Right Signature (Col 2) -->
          <td width="50%" align="right" valign="top" style="padding-right:40px;">
            <div dir="rtl" style="text-align:center; display:inline-block;">
              <b>المستلم</b>
            </div>
          </td>
        </tr>
        </table>
        '''


def _wrap(body):
    return f'''<!DOCTYPE html>
<html>
<head><meta charset="utf-8">
<style>
  body {{ text-align: right; font-family: Arial, sans-serif; margin: 0; padding: 5px 15px; }}
</style></head>
<body>{body}</body></html>'''


def _build_pages(parent_widget, master_info, items_rows, title, title_color, type_):
    date_str = master_info.get('start_date') or master_info.get('date') or str(date.today())
    ref_str = master_info.get('ref', '')

    first_page_max = 20
    other_page_max = 30

    pages = []

    if not items_rows:
        chunks = [[]]
    else:
        chunks = [items_rows[:first_page_max]]
        left = items_rows[first_page_max:]

        while left:
            chunks.append(left[:other_page_max])
            left = left[other_page_max:]

    header_ref_label = ''

    if type_ == 'issue':
        header_ref_label = 'رقم أمر الصرف'
    elif type_ == 'receipt' or type_ == 'transfer_receipt':
        header_ref_label = 'رقم الاستلام'
    elif type_ == 'receive':
        header_ref_label = 'رقم سند التوريد'
    elif type_ == 'transfer':
        header_ref_label = 'رقم إذن التحويل'
    else:
        header_ref_label = 'رقم السند'

    org_html = _get_org_html(parent_widget)
    _, logo_base64 = _get_settings(parent_widget)

    show_approval = type_ in ('receive', 'daily_work')

    header_html = _document_header(date_str, ref_str, title, org_html, title_color, header_ref_label, logo_base64, show_manager_approval=show_approval)

    info_html = ''

    if type_ == 'issue':
        info_html = f'''<table width="100%" style="font-size:12px; margin-bottom:5px; font-family: Arial; border-collapse:collapse;">
          {_section_header('بيانات المخزن')}
          {_info_row_2cols('جهة الصرف', master_info.get('warehouse', ''), 'التوجيه', 'يتم صرف الأصناف المبينة في الجدول أدناه')}
          {_section_header('بيانات الجهة المستفيدة')}
          {_info_row_2cols('اسم الوحدة', master_info.get('beneficiary', ''), 'قوة الأفراد', master_info.get('strength', ''))}
          {_info_row_2cols('من تاريخ', master_info.get('start_date', ''), 'إلى تاريخ', master_info.get('end_date', ''))}
          {_info_row_2cols('نوع الصرف', f"إعاشة لمدة {master_info.get('days', '')} يوم", 'المبررات والملاحظات', master_info.get('notes', ''))}
        </table>'''
    elif type_ == 'receipt':
        info_html = f'''<table width="100%" style="font-size:12px; margin-bottom:5px; font-family: Arial; border-collapse:collapse;">
          {_section_header('بيانات المستلم')}
          {_info_row_2cols('الاسم', '.................................', 'الرتبة', '.................................')}
          {_section_header('بيانات الجهة المستفيدة')}
          {_info_row_2cols('الوحدة المستفيدة', master_info.get('beneficiary', ''), 'قوة الأفراد', master_info.get('strength', ''))}
          {_info_row_2cols('تاريخ الاستلام', '.................................', 'نوع الصرف', f"إعاشة لمدة {master_info.get('days', '')} يوم")}
        </table>'''
    elif type_ == 'receive':
        info_html = f'''<table width="100%" style="font-size:12px; margin-bottom:5px; font-family: Arial; border-collapse:collapse;">
          {_section_header('بيانات السند')}
          {_info_row_2cols('المستودع', master_info.get('warehouse', ''), 'رقم المستند', master_info.get('ref', ''))}
          {_info_row_2cols('الجهة الموردة', master_info.get('supplier', ''), 'تاريخ التوريد', master_info.get('date', ''))}
          {_info_row_2cols('رقم الفاتورة / اسم التاجر', master_info.get('report_no', ''), 'ملاحظات السند', master_info.get('notes', ''))}
        </table>'''
    elif type_ == 'transfer_receipt':
        ent_row = ''

        if master_info.get('strength') and master_info.get('days'):
            ent_row = _info_row_2cols('قوة الأفراد', master_info.get('strength', ''), 'إعاشة لمدة', f"{master_info.get('days', '')} يوم")
            ent_row += _info_row_2cols('من تاريخ', master_info.get('start_date', ''), 'إلى تاريخ', master_info.get('end_date', ''))

        info_html = f'''<table width="100%" style="font-size:12px; margin-bottom:5px; font-family: Arial; border-collapse:collapse;">
          {_section_header('بيانات المستلم (أمين المستودع الهدف)')}
          {_info_row_2cols('الاسم', '.................................', 'الرتبة', '.................................')}
          {_section_header('بيانات التحويل')}
          {_info_row_2cols('إلى المستودع', master_info.get('to_wh', ''), 'من المستودع', master_info.get('from_wh', ''))}
          {_info_row_2cols('تاريخ الاستلام', '.................................', 'المبررات', master_info.get('notes', ''))}
          {ent_row}
        </table>'''
    elif type_ == 'transfer':
        ent_row = ''

        if master_info.get('strength') and master_info.get('days'):
            ent_row = _info_row_2cols('قوة الأفراد', master_info.get('strength', ''), 'إعاشة لمدة', f"{master_info.get('days', '')} يوم")
            ent_row += _info_row_2cols('من تاريخ', master_info.get('start_date', ''), 'إلى تاريخ', master_info.get('end_date', ''))

        info_html = f'''<table width="100%" style="font-size:12px; margin-bottom:5px; font-family: Arial; border-collapse:collapse;">
          {_section_header('بيانات التحويل')}
          {_info_row_2cols('من مستودع', master_info.get('from_wh', ''), 'إلى مستودع', master_info.get('to_wh', ''))}
          {_info_row_2cols('رقم الإذن', master_info.get('ref', ''), 'التاريخ', master_info.get('date', ''))}
          {ent_row}
          {_info_row_full('المبررات', master_info.get('notes', ''))}
        </table>'''

    for i, chunk in enumerate(chunks):
        page_html = header_html

        if i == 0 and info_html:
            page_html += info_html

        page_indicator = f'صفحة {i + 1} من {len(chunks)}'

        page_html += f'''
        <table width="100%" border="0" cellpadding="0" cellspacing="0"><tr>
          <td align="left" dir="rtl" style="font-size:11px; color:#555;">{page_indicator}</td>
          <td align="right" dir="rtl" style="font-weight:bold; font-size:14px; margin:5px 0; color:#2E6B35;">جدول الأصناف</td>
        </tr></table>
        '''

        if master_info.get('is_multi_unit'):
            headers = ['م', 'اسم الصنف', 'الكمية', 'الوحدة', 'الوحدة المستفيدة', 'ملاحظة']
        else:
            headers = ['م', 'اسم الصنف', 'الكمية', 'الوحدة', 'ملاحظة']

        page_html += _items_table(headers, chunk)

        if type_ in ('receipt', 'transfer_receipt'):
            page_html += '''
            <table width="100%" border="0" cellpadding="0" cellspacing="0" style="margin-top:10px;"><tr>
              <td align="right" dir="rtl" style="font-size:13px; font-weight:bold; padding-right:10px;">
                استلمت أنا الموضحة بياناتي أعلاه الأصناف المبينة أعلاه بتمامها وكمالها.
              </td>
            </tr></table>
            '''

        page_html += _signatures(type_, master_info)

        uname = _get_current_username(parent_widget)

        printed_by = f'طُبع بواسطة: {uname} — ' if uname else 'طُبع بواسطة نظام الإمداد والتموين — '

        page_html += f'<p dir="rtl" style="text-align:center; font-size:9px; color:#aaa; margin-top:10px;">{printed_by}{datetime.now().strftime("%Y-%m-%d %H:%M")}</p>'

        pages.append(page_html)

    return pages


def _join_pages(pages):
    body = ''

    for i, p in enumerate(pages):
        if i > 0:
            body += f'<table width="100%" style="page-break-before:always; border:none; margin:0; padding:0;"><tr><td style="padding:0;">{p}</td></tr></table>'
        else:
            body += f'<table width="100%" style="border:none; margin:0; padding:0;"><tr><td style="padding:0;">{p}</td></tr></table>'

    return body


def _print_html(parent: QWidget, html_content: str):
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)

    doc = QTextDocument()
    doc.setHtml(html_content)

    def handle_paint(p):
        doc.setPageSize(p.pageRect(QPrinter.Unit.Point).size())
        doc.print(p)

    preview = QPrintPreviewDialog(printer, parent)
    preview.setWindowTitle('معاينة الطباعة — جاهز')
    preview.setMinimumSize(900, 700)
    preview.paintRequested.connect(handle_paint)
    preview.exec()


def print_issue_voucher(parent, master_info, items_rows):
    pages = _build_pages(parent, master_info, items_rows, 'أمر صرف مخزني', '#C0392B', 'issue')
    _print_html(parent, _wrap(_join_pages(pages)))


def print_receipt_voucher(parent, master_info, items_rows):
    pages = _build_pages(parent, master_info, items_rows, 'استلام مخزني', '#2E6B35', 'receipt')
    _print_html(parent, _wrap(_join_pages(pages)))


def print_issue_with_receipt(parent, master_info, items_rows):
    pages_issue = _build_pages(parent, master_info, items_rows, 'أمر صرف مخزني', '#C0392B', 'issue')
    pages_receipt = _build_pages(parent, master_info, items_rows, 'استلام مخزني', '#2E6B35', 'receipt')
    all_pages = pages_issue + pages_receipt
    _print_html(parent, _wrap(_join_pages(all_pages)))


def print_receive_voucher(parent, master_info, items_rows):
    pages = _build_pages(parent, master_info, items_rows, 'سند توريد مخزني', '#2E6B35', 'receive')
    _print_html(parent, _wrap(_join_pages(pages)))


def print_transfer_order(parent, master_info, items_rows):
    pages = _build_pages(parent, master_info, items_rows, 'أمر تحويل مخزني داخلي', '#2980B9', 'transfer')
    _print_html(parent, _wrap(_join_pages(pages)))


def print_transfer_with_receipt(parent, master_info, items_rows):
    pages_transfer = _build_pages(parent, master_info, items_rows, 'أمر تحويل مخزني داخلي', '#2980B9', 'transfer')
    pages_receipt = _build_pages(parent, master_info, items_rows, 'استلام مخزني', '#2E6B35', 'transfer_receipt')
    all_pages = pages_transfer + pages_receipt
    _print_html(parent, _wrap(_join_pages(all_pages)))


def print_inventory_report(parent, warehouse_name, rows):
    title = f'كشف جرد المخزون — {warehouse_name}'
    date_str = str(date.today())

    org_html = _get_org_html(parent)
    _, logo_base64 = _get_settings(parent)

    header_html = _document_header(date_str, '', title, org_html, '#2E6B35', logo_base64=logo_base64)

    first_page_max = 25
    other_page_max = 30

    pages = []

    if not rows:
        chunks = [[]]
    else:
        chunks = [rows[:first_page_max]]
        left = rows[first_page_max:]

        while left:
            chunks.append(left[:other_page_max])
            left = left[other_page_max:]

    for i, chunk in enumerate(chunks):
        page_html = header_html

        page_indicator = f'صفحة {i + 1} من {len(chunks)}'

        page_html += f'''
        <table width="100%" border="0" cellpadding="0" cellspacing="0"><tr>
          <td align="left" dir="rtl" style="font-size:11px; color:#555;">{page_indicator}</td>
          <td align="right" dir="rtl" style="font-weight:bold; font-size:14px; margin:5px 0; color:#2E6B35;">جدول الأصناف</td>
        </tr></table>
        '''

        page_html += _items_table(['م', 'كود الصنف', 'الاسم', 'الكمية', 'الوحدة', 'المستودع', 'الحالة'], chunk)
        page_html += _signatures('issue', {})

        uname = _get_current_username(parent)

        printed_by = f'طُبع بواسطة: {uname} — ' if uname else 'طُبع بواسطة نظام الإمداد والتموين — '

        page_html += f'<p dir="rtl" style="text-align:center; font-size:10px; color:#aaa; margin-top:30px;">{printed_by}{datetime.now().strftime("%Y-%m-%d %H:%M")}</p>'

        pages.append(page_html)

    _print_html(parent, _wrap(_join_pages(pages)))


def print_item_card(parent, item_name, rows):
    title = f'كارت حركة الصنف: {item_name}'
    date_str = str(date.today())

    org_html = _get_org_html(parent)
    _, logo_base64 = _get_settings(parent)

    header_html = _document_header(date_str, '', title, org_html, '#2E6B35', logo_base64=logo_base64)

    first_page_max = 25
    other_page_max = 30

    pages = []

    if not rows:
        chunks = [[]]
    else:
        chunks = [rows[:first_page_max]]
        left = rows[first_page_max:]

        while left:
            chunks.append(left[:other_page_max])
            left = left[other_page_max:]

    for i, chunk in enumerate(chunks):
        page_html = header_html

        page_indicator = f'صفحة {i + 1} من {len(chunks)}'

        page_html += f'''
        <table width="100%" border="0" cellpadding="0" cellspacing="0"><tr>
          <td align="left" dir="rtl" style="font-size:11px; color:#555;">{page_indicator}</td>
          <td align="right" dir="rtl" style="font-weight:bold; font-size:14px; margin:5px 0;">سجل الحركات</td>
        </tr></table>
        '''

        page_html += _items_table(['التاريخ', 'النوع', 'المستودع/الجهة', 'الكمية', 'الوحدة', 'المستند', 'ملاحظات'], chunk)
        page_html += _signatures('issue', {})

        uname = _get_current_username(parent)

        printed_by = f'طُبع بواسطة: {uname} — ' if uname else 'طُبع بواسطة نظام الإمداد والتموين — '

        page_html += f'<p dir="rtl" style="text-align:center; font-size:10px; color:#aaa; margin-top:30px;">{printed_by}{datetime.now().strftime("%Y-%m-%d %H:%M")}</p>'

        pages.append(page_html)

    _print_html(parent, _wrap(_join_pages(pages)))


def print_returns_voucher(parent, master_info, rows):
    date_str = str(date.today())

    title_prefix = 'سند مرتجع وارد (إلى المورد)' if master_info.get('type', '') == 'RETURN_IN' else 'سند مرتجع صادر (من الوحدة)'

    org_html = _get_org_html(parent)
    _, logo_base64 = _get_settings(parent)

    header_html = _document_header(master_info.get('date', date_str), master_info.get('ref', 'بدون مرجع'), title_prefix, org_html, title_color='#C0392B', logo_base64=logo_base64)

    info_html = f'''<table width="100%" style="font-size:13px; margin-bottom:15px; font-family: Arial; border-collapse:collapse;">
      {_section_header('بيانات المرتجع')}
      {_info_row_2cols('نوع المرتجع', master_info.get('type', 'نوع غير محدد'), 'المستودع', master_info.get('warehouse', ''))}
      {_info_row_2cols('الوحدة المستفيدة', master_info.get('unit', ''), 'تاريخ المرتجع', master_info.get('date', ''))}
      {_info_row_full('ملاحظات المرتجع', master_info.get('notes', ''))}
    </table>'''

    first_page_max = 12
    other_page_max = 20

    pages = []

    if len(rows) <= first_page_max:
        chunks = [rows]
    else:
        chunks = [rows[:first_page_max]]
        left = rows[first_page_max:]

        while left:
            chunks.append(left[:other_page_max])
            left = left[other_page_max:]

    for i, chunk in enumerate(chunks):
        page_html = header_html

        if i == 0:
            page_html += info_html
        else:
            page_html += f'<div align="left" dir="rtl" style="font-size:11px; color:#555; margin-bottom:10px;">تابع صفحة ({i + 1}) من السند</div>'

        page_html += _items_table(['م', 'الصنف', 'السبب', 'الوحدة', 'الكمية المرتجعة'], chunk)

        if i == len(chunks) - 1:
            page_html += _signatures('receive' if master_info.get('type', '') == 'RETURN_OUT' else 'issue', {})

        uname = _get_current_username(parent)

        printed_by = f'طُبع بواسطة: {uname} — ' if uname else 'طُبع بواسطة نظام الإمداد والتموين — '

        page_html += f'<p dir="rtl" style="text-align:center; font-size:10px; color:#aaa; margin-top:30px;">{printed_by}{datetime.now().strftime("%Y-%m-%d %H:%M")}</p>'

        pages.append(page_html)

    _print_html(parent, _wrap(_join_pages(pages)))


def print_aggregated_report(parent, master_info, rows, title='تقرير مجمّع'):
    from datetime import datetime, date

    date_str = str(date.today())

    org_html = _get_org_html(parent)
    _, logo_base64 = _get_settings(parent)

    header_html = _document_header(date_str, 'بدون', title, org_html, title_color='#8E44AD', logo_base64=logo_base64)

    info_html = f'''<table width="100%" style="font-size:13px; margin-bottom:15px; font-family: Arial; border-collapse:collapse;">
      {_section_header('محددات التقرير')}
      {_info_row_2cols('المستودع', master_info.get('warehouse', 'الكل'), 'الوحدة المستفيدة', master_info.get('unit', 'الكل'))}
      {_info_row_2cols('من تاريخ', master_info.get('date_from', ''), 'إلى تاريخ', master_info.get('date_to', ''))}
    </table>'''

    first_page_max = 15
    other_page_max = 22

    pages = []

    if len(rows) <= first_page_max:
        chunks = [rows]
    else:
        chunks = [rows[:first_page_max]]
        left = rows[first_page_max:]

        while left:
            chunks.append(left[:other_page_max])
            left = left[other_page_max:]

    for i, chunk in enumerate(chunks):
        page_html = header_html

        if i == 0:
            page_html += info_html
        else:
            page_html += f'<div align="left" dir="rtl" style="font-size:11px; color:#555; margin-bottom:10px;">تابع صفحة ({i + 1}) من التقرير المجمّع</div>'

        page_html += _items_table(['م', 'اسم الصنف', 'إجمالي الكمية', 'الوحدة', 'ملاحظات'], chunk)

        uname = _get_current_username(parent)

        printed_by = f'طُبع بواسطة: {uname} — ' if uname else 'طُبع بواسطة نظام الإمداد والتموين — '

        page_html += f'<p dir="rtl" style="text-align:center; font-size:10px; color:#aaa; margin-top:30px;">{printed_by}{datetime.now().strftime("%Y-%m-%d %H:%M")}</p>'

        pages.append(page_html)

    _print_html(parent, _wrap(_join_pages(pages)))


def print_daily_strength(camp_name, ref_date, global_pct, rows_data, totals, parent):
    today_str = date.today().strftime('%Y-%m-%d')

    org_html = _get_org_html(parent)
    _, logo_path = _get_settings(parent)

    logo_html = '&nbsp;'

    if logo_path and os.path.isfile(logo_path):
        logo_html = f'<img src="file:///{logo_path}" height="95" style="max-height:95px; object-fit:contain;">'

    header_html = f'''
<table width="100%" cellpadding="0" cellspacing="0" style="font-family: Arial, sans-serif; margin-bottom:2px; border:none;">
  <tr>
    <td width="33%" align="left" valign="top">
      <table border="0" cellpadding="1" cellspacing="0" style="font-size:12px; line-height:1.2;">
        <tr>
          <td align="right" dir="rtl">{today_str}</td>
          <td align="right" dir="rtl" style="font-weight:bold;">التاريخ</td>
        </tr>
      </table>
    </td>
    <td width="34%" align="center" valign="middle">
      {logo_html}
    </td>
    <td width="33%" align="right" valign="top">
      {org_html}
    </td>
  </tr>
</table>
<hr style="border:2px solid #2E6B35; margin:3px 0;">
<table width="100%" border="0" cellpadding="0" cellspacing="0" style="margin:2px 0 5px 0;">
  <tr>
    <td width="100%" align="center" valign="middle">
      <h3 style="color:#2E6B35; margin:0; font-size:18px;">تفريدة يومية</h3>
    </td>
  </tr>
</table>
'''

    info_html = f'''
    <table width="100%" border="1" cellpadding="3" cellspacing="0" style="margin-bottom:5px; border-collapse:collapse; border:1px solid #555; font-size:11px;">
        <tr>
            <td width="10%" align="center"><strong>{global_pct} %</strong></td>
            <td width="10%" align="center" style="background-color:#E8EAE6; font-weight:bold;">نسبة الزيادة</td>
            <td width="18%" align="center"><strong>{ref_date}</strong></td>
            <td width="12%" align="center" style="background-color:#E8EAE6; font-weight:bold;">تاريخ التفريدة</td>
            <td width="38%" align="center"><strong>{camp_name}</strong></td>
            <td width="12%" align="center" style="background-color:#E8EAE6; font-weight:bold;">الجهة / المعسكر</td>
        </tr>
    </table>
    '''

    headers_ltr = ['الإجمالي النهائي', 'الزيادة', 'الأساسي (القوة الفعلية)', 'اسم الوحدة الفرعية', 'م']

    tbl_html = '<table width="100%" style="border-collapse:collapse; font-family:Arial,sans-serif; font-size:10px;">'
    tbl_html += '<thead><tr>'

    for h in headers_ltr:
        tbl_html += f'<th style="background:#2E6B35; color:white; padding:2px 3px; border:1px solid #333; text-align:center; font-size:10px;">{h}</th>'

    tbl_html += '</tr></thead><tbody>'

    for i, row in enumerate(rows_data):
        bg = '#f9f9f9' if i % 2 == 0 else '#ffffff'
        row_num = str(i + 1)

        cells = [row[3], row[2], row[1], row[0], row_num]

        tbl_html += f'<tr style="background:{bg};">'

        for cell in cells:
            tbl_html += f'<td align="center" style="padding:1px 3px; border:1px solid #bbb; font-size:10px; line-height:1.2;">{cell}</td>'

        tbl_html += '</tr>'

    tbl_html += '</tbody></table>'

    summary_html = f'''
    <table width="100%" border="1" cellpadding="3" cellspacing="0" style="margin-top:5px; border-collapse:collapse; border:2px solid #2E6B35; font-size:11px; background-color:#f9fbef;">
        <tr>
            <td align="center">مجموع الزيـادات</td>
            <td align="center">مجموع القوة الفعلية</td>
            <td align="center">عدد الوحدات</td>
            <td rowspan="2" align="center" valign="middle" width="25%" style="font-weight:bold; color:#2E6B35; font-size:13px;">إجماليات المعسكر</td>
        </tr>
        <tr>
            <td align="center" style="font-weight:bold; color:#C0392B;">{totals.get('increase', 0)}</td>
            <td align="center" style="font-weight:bold;">{totals.get('base', 0)}</td>
            <td align="center" style="font-weight:bold;">{totals.get('units', 0)}</td>
        </tr>
        <tr>
            <td colspan="4" align="center" style="background-color:#2E6B35; color:#fff; font-weight:bold; font-size:14px; padding:4px;">
                الإجمالي الكلي للمعسكر: {totals.get('grand', 0)} فرد
            </td>
        </tr>
    </table>
    '''

    sig_html = '''
    <table width="100%" border="0" cellpadding="0" cellspacing="0" style="margin-top:20px; font-size:12px; font-weight:bold;">
      <tr>
        <td width="50%" align="center">ركن إدارة الإمداد<br><br>...........................</td>
        <td width="50%" align="center">مدير مكتب إدارة الإمداد<br><br>...........................</td>
      </tr>
    </table>
    '''

    uname = _get_current_username(parent)

    printed_by = f'طُبع بواسطة: {uname} — ' if uname else 'طُبع بواسطة نظام الإمداد والتموين — '

    footer_html = f'<p dir="rtl" style="text-align:center; font-size:9px; color:#aaa; margin-top:10px;">{printed_by}{datetime.now().strftime("%Y-%m-%d %H:%M")}</p>'

    page_html = header_html + info_html + tbl_html + summary_html + sig_html + footer_html

    _print_html(parent, _wrap(page_html))


def print_daily_workflow_report(parent, meta, movements_data):
    from datetime import datetime

    report_date = meta.get('date', str(date.today()))
    warehouse_name = meta.get('warehouse', 'جميع المستودعات')
    movement_type_label = meta.get('movement_type', 'الكل')

    org_html = _get_org_html(parent)
    _, logo_base64 = _get_settings(parent)

    uname = _get_current_username(parent)

    type_order = ['OUT', 'IN', 'TRANSFER', 'RETURN_IN', 'RETURN_OUT', 'OPENING']

    type_labels = {
        'OUT': 'حركة الصادر (المنصرف)',
        'IN': 'حركة الوارد',
        'TRANSFER': 'حركة التحويلات المخزنية',
        'RETURN_OUT': 'حركة المرتجعات من الوحدات',
        'RETURN_IN': 'حركة المرتجعات إلى الموردين',
        'OPENING': 'أرصدة افتتاحية',
    }

    grouped = {}
    warehouses_present = []

    for m in movements_data:
        wn = m.get('warehouse_name', 'مستودع غير محدد')
        mt = m.get('movement_type', 'OTHER')

        key = (wn, mt)

        if key not in grouped:
            grouped[key] = []

        grouped[key].append(m)

        if wn not in warehouses_present:
            warehouses_present.append(wn)

    sig_html = '''
    <table width="100%" style="font-family: Arial, sans-serif; font-size:13px; margin-top:20px; border:none;">
    <tr>
      <td width="33%" align="center" valign="top">
        <div dir="rtl" style="text-align:center;">
          <b>ركن إدارة الإمداد</b><br><br>...........................
        </div>
      </td>
      <td width="34%" align="center" valign="top">
        <div dir="rtl" style="text-align:center;">
          <b>مدير المخزن</b><br><br>...........................
        </div>
      </td>
      <td width="33%" align="center" valign="top">
        <div dir="rtl" style="text-align:center;">
          <b>مكتب إدارة الإمداد</b><br><br>...........................
        </div>
      </td>
    </tr>
    </table>
    '''

    first_page_max = 18
    other_page_max = 25

    pages = []

    ordered_keys = []

    if warehouse_name == 'جميع المستودعات':
        for wn in warehouses_present:
            for mt in type_order:
                if (wn, mt) in grouped:
                    ordered_keys.append((wn, mt))

            for k_wn, k_mt in grouped.keys():
                if k_wn == wn:
                    if k_mt not in type_order:
                        if (wn, k_mt) not in ordered_keys:
                            ordered_keys.append((wn, k_mt))
    else:
        wn = warehouse_name

        for mt in type_order:
            if (wn, mt) in grouped:
                ordered_keys.append((wn, mt))

        for k_wn, k_mt in grouped.keys():
            if k_wn == wn:
                if k_mt not in type_order:
                    if (wn, k_mt) not in ordered_keys:
                        ordered_keys.append((wn, k_mt))

    for wn, mt in ordered_keys:
        items = grouped[(wn, mt)]

        base_label = type_labels.get(mt, mt)

        label = f'{base_label} / {wn}' if warehouse_name == 'جميع المستودعات' else base_label

        table_rows = []
        seen_refs = set()

        for i, m in enumerate(items):
            entity = m.get('recipient_display', '')

            if not entity:
                if mt in ('IN', 'RETURN_IN'):
                    entity = m.get('supplier_name', '')
                elif mt in ('OUT', 'RETURN_OUT'):
                    entity = m.get('beneficiary_unit_name') or m.get('beneficiary_unit', '')
                elif mt == 'TRANSFER':
                    notes = m.get('notes', '')
                    entity = notes.split('|')[0].strip() if 'المستودع' in notes else 'مستودع آخر'
                elif mt == 'OPENING':
                    entity = 'النظام / إعداد أولي'

            if mt == 'RETURN_IN' and entity:
                entity = f'مرتجع للمورد: {entity}'
            elif mt == 'RETURN_OUT' and entity:
                entity = f'مرتجع من وحدة: {entity}'

            notes = m.get('notes', '') or ''
            ref = m.get('reference_no', '')

            voucher_id = ref if ref else f"no_ref_{m.get('movement_date', '')}_{entity}"

            if mt == 'OUT' and voucher_id not in seen_refs:
                seen_refs.add(voucher_id)

                duration = m.get('duration_days', 0)

                if duration and duration > 1:
                    start_str = m.get('movement_date', '')[:10]

                    try:
                        y, mo, d = map(int, start_str.split('-'))

                        from PyQt6.QtCore import QDate, Qt

                        end_str = QDate(y, mo, d).addDays(int(duration) - 1).toString(Qt.DateFormat.ISODate)

                        note_addon = f'إعاشة لمدة {duration} من {start_str} إلى {end_str}'

                        notes = f'{note_addon} | {notes}' if notes else note_addon
                    except Exception:
                        pass

            table_rows.append([str(i + 1), m.get('item_name', ''), str(m.get('quantity', 0)), m.get('unit_name', ''), entity, notes])

        if not table_rows:
            chunks = [[]]
        else:
            chunks = [table_rows[:first_page_max]]
            left = table_rows[first_page_max:]

            while left:
                chunks.append(left[:other_page_max])
                left = left[other_page_max:]

        for ci, chunk in enumerate(chunks):
            header_html = _document_header(report_date, '', 'تقرير الحركة اليومية', org_html, '#2E6B35', 'رقم التقرير', logo_base64, show_manager_approval=True)
            page_html = header_html

            if ci == 0:
                page_html += f'''
                <table width="100%" style="font-size:12px; margin-bottom:8px; font-family: Arial; border-collapse:collapse; border:1px solid #ddd;">
                  <tr>
                    <td width="30%" align="right" dir="rtl" style="padding:3px 8px; font-size:12px; border-bottom:1px solid #ddd;">{movement_type_label}</td>
                    <td width="10%" align="right" dir="rtl" style="font-weight:bold; padding:3px 8px; font-size:12px; border-bottom:1px solid #ddd; background:#fafafa;">نوع الحركة</td>
                    <td width="25%" align="right" dir="rtl" style="padding:3px 8px; font-size:12px; border-bottom:1px solid #ddd;">{warehouse_name}</td>
                    <td width="10%" align="right" dir="rtl" style="font-weight:bold; padding:3px 8px; font-size:12px; border-bottom:1px solid #ddd; background:#fafafa;">اسم المخزن</td>
                    <td width="15%" align="right" dir="rtl" style="padding:3px 8px; font-size:12px; border-bottom:1px solid #ddd;">{report_date}</td>
                    <td width="10%" align="right" dir="rtl" style="font-weight:bold; padding:3px 8px; font-size:12px; border-bottom:1px solid #ddd; background:#fafafa;">التاريخ</td>
                  </tr>
                </table>
                '''

            total_pages_for_type = len(chunks)

            page_label = f'صفحة {ci + 1} من {total_pages_for_type}' if total_pages_for_type > 1 else ''

            page_html += f'''
            <table width="100%" border="0" cellpadding="0" cellspacing="0"><tr>
              <td align="left" dir="rtl" style="font-size:11px; color:#555;">{page_label}</td>
              <td align="right" dir="rtl" style="font-weight:bold; font-size:14px; margin:5px 0; color:#2E6B35;">{label}</td>
            </tr></table>
            '''

            headers = ['م', 'اسم الصنف', 'الكمية', 'الوحدة', 'الجهة / الوحدة المستفيدة', 'ملاحظة']

            page_html += _items_table(headers, chunk)
            page_html += sig_html

            printed_by = f'طُبع بواسطة: {uname} — ' if uname else 'طُبع بواسطة نظام الإمداد والتموين — '

            page_html += f'<p dir="rtl" style="text-align:center; font-size:9px; color:#aaa; margin-top:5px;">{printed_by}{datetime.now().strftime("%Y-%m-%d %H:%M")}</p>'

            pages.append(page_html)

    if not pages:
        header_html = _document_header(report_date, '', 'تقرير الحركة اليومية', org_html, '#2E6B35', 'رقم التقرير', logo_base64, show_manager_approval=True)
        page_html = header_html

        page_html += f'<div dir="rtl" style="text-align:center; font-size:14px; padding:40px; color:#777;">لا توجد حركات مسجلة لهذا اليوم ({report_date})</div>'
        page_html += sig_html

        pages.append(page_html)

    _print_html(parent, _wrap(_join_pages(pages)))


def print_inventory_count_form(parent, count_detail):
    title = f"استمارة جرد مخزني - {count_detail.get('count_type', '')}"
    count_no = count_detail.get('count_no', '')
    date_str = count_detail.get('start_date', str(date.today()))

    org_html = _get_org_html(parent)
    _, logo_base64 = _get_settings(parent)

    header_html = _document_header(date_str, count_no, title, org_html, '#2E6B35', 'رقم الأمر', logo_base64=logo_base64)

    info_html = f'''<table width="100%" style="font-size:12px; margin-bottom:15px; font-family: Arial; border-collapse:collapse;">
      {_section_header('بيانات أمر الجرد')}
      {_info_row_2cols('المستودع', count_detail.get('warehouse_name', ''), 'التصنيف', count_detail.get('category_name', 'الكل'))}
      {_info_row_2cols('أعضاء اللجنة', count_detail.get('committee_members', ''), 'ملاحظات', count_detail.get('notes', ''))}
    </table>'''

    items = count_detail.get('items', [])

    max_units = 0

    for item in items:
        details = item.get('details', [])

        if len(details) > max_units:
            max_units = len(details)

    if max_units == 0:
        max_units = 1

    headers = ['م', 'كود الصنف', 'الاسم']

    for u in range(max_units):
        headers.append(f'الوحدة {u + 1}')
        headers.append(f'الفعلي {u + 1}')

    headers.append('ملاحظات')

    rows = []

    for i, item in enumerate(items):
        row = [str(i + 1), item.get('item_code', ''), item.get('item_name', '')]

        details = item.get('details', [])

        for u in range(max_units):
            if u < len(details):
                row.append(details[u].get('unit_name', ''))
            elif details == [] and u == 0:
                row.append(item.get('unit_name', ''))
            else:
                row.append('-')

            row.append('...................')

        row.append('............')

        rows.append(row)

    first_page_max = 12
    other_page_max = 20

    pages = []

    if not rows:
        chunks = [[]]
    else:
        chunks = [rows[:first_page_max]]
        left = rows[first_page_max:]

        while left:
            chunks.append(left[:other_page_max])
            left = left[other_page_max:]

    for i, chunk in enumerate(chunks):
        page_html = header_html

        if i == 0:
            page_html += info_html

        page_indicator = f'صفحة {i + 1} من {len(chunks)}'

        page_html += f'''
        <table width="100%" border="0" cellpadding="0" cellspacing="0"><tr>
          <td align="left" dir="rtl" style="font-size:11px; color:#555;">{page_indicator}</td>
          <td align="right" dir="rtl" style="font-weight:bold; font-size:14px; margin:5px 0; color:#2E6B35;">استمارة العد</td>
        </tr></table>
        '''

        page_html += _items_table(headers, chunk)

        if i == len(chunks) - 1:
            page_html += '''
            <table width="100%" border="0" cellpadding="0" cellspacing="0" style="margin-top:20px; font-size:12px; font-weight:bold;">
              <tr>
                <td width="33%" align="center">رئيس اللجنة<br><br>...........................</td>
                <td width="33%" align="center">أعضاء اللجنة<br><br>...........................</td>
                <td width="34%" align="center">أمين المستودع<br><br>...........................</td>
              </tr>
            </table>
            '''

        uname = _get_current_username(parent)

        printed_by = f'طُبع بواسطة: {uname} — ' if uname else 'طُبع بواسطة نظام الإمداد والتموين — '

        page_html += f'<p dir="rtl" style="text-align:center; font-size:9px; color:#aaa; margin-top:20px;">{printed_by}{datetime.now().strftime("%Y-%m-%d %H:%M")}</p>'

        pages.append(page_html)

    _print_html(parent, _wrap(_join_pages(pages)))


def print_inventory_count_variances(parent, count_detail):
    title = 'تقرير فروقات الجرد المخزني'
    count_no = count_detail.get('count_no', '')
    date_str = count_detail.get('start_date', str(date.today()))

    org_html = _get_org_html(parent)
    _, logo_base64 = _get_settings(parent)

    header_html = _document_header(date_str, count_no, title, org_html, '#C0392B', 'رقم الأمر', logo_base64=logo_base64)

    info_html = f'''<table width="100%" style="font-size:12px; margin-bottom:15px; font-family: Arial; border-collapse:collapse;">
      {_section_header('بيانات أمر الجرد')}
      {_info_row_2cols('المستودع', count_detail.get('warehouse_name', ''), 'إجمالي الأصناف المجرودة', str(count_detail.get('counted_items', 0)))}
      {_info_row_2cols('عدد الأصناف ذات الفروقات', str(count_detail.get('variance_items', 0)), 'تاريخ الإغلاق', count_detail.get('closed_at', 'قيد التنفيذ')[:10] if count_detail.get('closed_at') else 'قيد التنفيذ')}
    </table>'''

    items = count_detail.get('items', [])

    variance_items = [it for it in items if any((d.get('variance', 0) != 0 for d in it.get('details', []))) and any((d.get('physical_quantity') is not None for d in it.get('details', [])))]

    max_units = 0

    for item in variance_items:
        details = item.get('details', [])

        if len(details) > max_units:
            max_units = len(details)

    if max_units == 0:
        max_units = 1

    headers = ['م', 'الصنف']

    for u in range(max_units):
        headers.extend([f'و{u + 1}', 'دفتري', 'فعلي', 'الفرق'])

    headers.extend(['السبب', 'القرار'])

    rows = []

    for i, item in enumerate(variance_items):
        dec = item.get('adjustment_decision', '')
        dec_map = {'ADJUST': 'تسوية', 'KEEP': 'إبقاء', 'PENDING': 'تعليق'}
        dec_str = dec_map.get(dec, dec)

        row = [str(i + 1), item.get('item_name', '')]

        details = item.get('details', [])

        for u in range(max_units):
            if u < len(details):
                d = details[u]
                var = d.get('variance', 0)

                var_str = f"<span style='color:red;'>{var:+g}</span>" if var < 0 else f"<span style='color:green;'>{var:+g}</span>"

                row.extend([d.get('unit_name', ''), str(d.get('book_quantity', 0)), str(d.get('physical_quantity', 0)), var_str])
            else:
                row.extend(['-', '-', '-', '-'])

        row.extend([item.get('variance_reason', ''), dec_str])

        rows.append(row)

    first_page_max = 12
    other_page_max = 20

    pages = []

    if not rows:
        chunks = [[]]
    else:
        chunks = [rows[:first_page_max]]
        left = rows[first_page_max:]

        while left:
            chunks.append(left[:other_page_max])
            left = left[other_page_max:]

    for i, chunk in enumerate(chunks):
        page_html = header_html

        if i == 0:
            page_html += info_html

            if not variance_items:
                page_html += "<h3 dir='rtl' style='text-align:center; color:#2E6B35; margin:40px;'>لا توجد فروقات في هذا الجرد (مطابق تماماً).</h3>"

        if variance_items:
            page_indicator = f'صفحة {i + 1} من {len(chunks)}'

            page_html += f'''
            <table width="100%" border="0" cellpadding="0" cellspacing="0"><tr>
              <td align="left" dir="rtl" style="font-size:11px; color:#555;">{page_indicator}</td>
              <td align="right" dir="rtl" style="font-weight:bold; font-size:14px; margin:5px 0; color:#C0392B;">الأصناف ذات الفروقات</td>
            </tr></table>
            '''

            page_html += _items_table(headers, chunk)

        if i == len(chunks) - 1:
            page_html += '''
            <table width="100%" border="0" cellpadding="0" cellspacing="0" style="margin-top:20px; font-size:12px; font-weight:bold;">
              <tr>
                <td width="50%" align="center">لجنة الجرد<br><br>...........................</td>
                <td width="50%" align="center">مدير إدارة الإمداد والتموين<br><br>...........................</td>
              </tr>
            </table>
            '''

        uname = _get_current_username(parent)

        printed_by = f'طُبع بواسطة: {uname} — ' if uname else 'طُبع بواسطة نظام الإمداد والتموين — '

        page_html += f'<p dir="rtl" style="text-align:center; font-size:9px; color:#aaa; margin-top:20px;">{printed_by}{datetime.now().strftime("%Y-%m-%d %H:%M")}</p>'

        pages.append(page_html)

    _print_html(parent, _wrap(_join_pages(pages)))


def print_aggregated_transfers_report(parent_widget, aggregated_rows, src_name, tgt_name, dt_from, dt_to):
    org_html = _get_org_html(parent_widget)
    _, logo_base64 = _get_settings(parent_widget)
    today = date.today().strftime('%Y-%m-%d')
    username = _get_current_username(parent_widget)

    html = _document_header(today, '', 'تقرير إجمالي التحويلات (مجمّع)', org_html=org_html, title_color='#2E6B35', header_ref_label='', logo_base64=logo_base64, show_manager_approval=False)

    html += f'''
<table width="100%" cellpadding="3" cellspacing="0" style="font-family: Arial, sans-serif; font-size:14px; margin-bottom:10px; border:2px solid #2E6B35; background-color:#F5F5F5;">
  <tr>
    <td align="right" dir="rtl"><b>إلى مستودع:</b> {tgt_name}</td>
    <td align="right" dir="rtl"><b>من مستودع:</b> {src_name}</td>
  </tr>
  <tr>
    <td align="right" dir="rtl"><b>الفترة إلى:</b> {dt_to}</td>
    <td align="right" dir="rtl"><b>الفترة من:</b> {dt_from}</td>
  </tr>
</table>
'''

    table_rows = []

    for i, row in enumerate(aggregated_rows):
        table_rows.append([str(i + 1), str(row.get('code', '')), str(row.get('name', '')), str(row.get('unit', '')), str(row.get('quantity', 0))])

    html += _items_table(['رقم', 'رقم الصنف', 'اسم الصنف', 'الوحدة', 'إجمالي الكمية'], table_rows)

    html += f'''
<table width="100%" cellpadding="0" cellspacing="0" style="font-family: Arial, sans-serif; font-size:14px; margin-top:30px;">
  <tr>
    <td align="center" width="33%">
      <b>أمين المستودع المُسْتَقْبِل</b><br><br>
      الاسم: ........................<br><br>
      التوقيع: ........................
    </td>
    <td align="center" width="33%">
      <b>طُبع بواسطة</b><br><br>
      الاسم: {username if username else '........................'}<br><br>
      التوقيع: ........................
    </td>
    <td align="center" width="33%">
      <b>أمين المستودع المُصْدِر</b><br><br>
      الاسم: ........................<br><br>
      التوقيع: ........................
    </td>
  </tr>
</table>
'''

    printed_by = f'طُبع بواسطة: {username} — ' if username else 'طُبع بواسطة نظام الإمداد والتموين — '

    html += f'<p dir="rtl" style="text-align:center; font-size:9px; color:#aaa; margin-top:10px;">{printed_by}{datetime.now().strftime("%Y-%m-%d %H:%M")}</p>'

    _print_html(parent_widget, _wrap(html))
