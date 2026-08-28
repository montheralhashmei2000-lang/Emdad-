# Android platform files

This repository branch contains a lightweight Flutter project scaffold. To generate the full Android platform folder (android/) and all necessary native files so you can build an APK directly from the repo, run the following commands locally on your machine with Flutter SDK installed:

1. From the branch feature/mobile-scaffold clone/download the repo locally.
2. Run:

   flutter create --platforms=android .

This will populate the `android/` directory with the native project files. After that, you can build an APK:

   flutter build apk --release

If you prefer, I can add the complete `android/` folder to the repo for you (it is large). Reply "أضف android" and I will push the full Android project files into the branch.
