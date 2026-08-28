# Emdad - Mobile (Android only)

هذا الفرع feature/mobile-scaffold يحتوي على مشروع Flutter كامل الخِبرة لكن للمرونة قمت بإضافة scaffold خفيف + سكربت لتوليد ملفات Android المحلية.

ما تمّ إضافته في هذا الالتزام:
- .gitignore
- pubspec.yaml
- lib/main.dart (تطبيق بسيط: صفحة رئيسية + صفحة حول)
- scripts/generate_android.sh (يقوم بتشغيل `flutter create --platforms=android .` لإنشاء مجلد android)
- android/README.md (تعليمات)

لماذا هذا الخيار؟
- مجلد android الناتج عن `flutter create` كبير جدًا (عدة مئات من الملفات) ورفع كلّها يمكن أن يجعل الريبو كبيرًا — لذلك أضفت سكربت لتوليد المجلد محليًا.
- إن رغبت أن أرفع مجلد `android/` كاملاً إلى الريبو، أكتب: "أضف android" وسأدفعه.

كيفية التشغيل محليًا:
1. ثبت Flutter SDK: https://flutter.dev
2. نفّذ في جذر المشروع:
   flutter pub get
3. أنشئ مجلد android محليًا (أو شغّل السكربت):
   ./scripts/generate_android.sh
4. شغّل على محاكي Android أو جهاز:
   flutter run -d android
5. لبناء APK:
   flutter build apk --release

