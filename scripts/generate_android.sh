#!/usr/bin/env bash
# Generate Android platform files for this Flutter project
# Usage: ./scripts/generate_android.sh

set -e
if ! command -v flutter >/dev/null 2>&1; then
  echo "Flutter not found in PATH. Install Flutter SDK and add to PATH."
  exit 1
fi

echo "Generating Android platform files..."
flutter create --platforms=android .

echo "Done. You can now run: flutter build apk --release"
