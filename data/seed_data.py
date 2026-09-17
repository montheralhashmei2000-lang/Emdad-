from core.services.user_service import UserService
from data.database import get_session

def init_sample_data():
    # إنشاء مستخدم مدير إذا لم يكن موجوداً
    UserService.create_admin_user('admin', 'admin123', 'المدير العام')
    
    # يمكن إضافة بيانات أولية أخرى هنا
    print("تم تهيئة البيانات الأولية بنجاح")