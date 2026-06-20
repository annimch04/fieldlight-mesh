#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PYTHON="${PYTHON:-$ROOT/.venv/bin/python}"
VERSION="$($PYTHON -c 'import fieldlight_mesh; print(fieldlight_mesh.__version__)')"
ARCH="$(uname -m)"
APP_NAME="Fieldlight Mesh"
DMG_NAME="Fieldlight-Mesh-${VERSION}-macOS-${ARCH}.dmg"

"$PYTHON" -m PyInstaller \
  --noconfirm \
  --clean \
  --windowed \
  --name "$APP_NAME" \
  --osx-bundle-identifier "org.fieldlight.mesh" \
  --collect-data fieldlight_mesh \
  --hidden-import zeroconf \
  scripts/fieldlight_mesh_app.py

PLIST="dist/$APP_NAME.app/Contents/Info.plist"
plutil -replace CFBundleShortVersionString -string "$VERSION" "$PLIST"
/usr/libexec/PlistBuddy -c "Add :CFBundleVersion string $VERSION" "$PLIST" 2>/dev/null || \
  /usr/libexec/PlistBuddy -c "Set :CFBundleVersion $VERSION" "$PLIST"
/usr/libexec/PlistBuddy -c \
  "Add :NSLocalNetworkUsageDescription string Fieldlight Mesh discovers and exchanges messages with peers on your local network." \
  "$PLIST" 2>/dev/null || true
/usr/libexec/PlistBuddy -c "Add :NSBonjourServices array" "$PLIST" 2>/dev/null || true
/usr/libexec/PlistBuddy -c "Add :NSBonjourServices:0 string _fieldlight._tcp" "$PLIST" 2>/dev/null || true

codesign --force --deep --sign - "dist/$APP_NAME.app"

STAGE="build/dmg-stage"
rm -rf "$STAGE"
mkdir -p "$STAGE"
cp -R "dist/$APP_NAME.app" "$STAGE/"
ln -s /Applications "$STAGE/Applications"
cp docs/MAC_ALPHA_RUNBOOK.md "$STAGE/README.md"

rm -f "dist/$DMG_NAME"
hdiutil create \
  -volname "$APP_NAME" \
  -srcfolder "$STAGE" \
  -ov \
  -format UDZO \
  "dist/$DMG_NAME"

echo "Built: $ROOT/dist/$DMG_NAME"
