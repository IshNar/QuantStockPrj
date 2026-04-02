#!/usr/bin/env bash
set -e

echo "============================================"
echo "  퀀트 인사이트 - APK 빌드 v3"
echo "  (Android 16 호환 / 사전 패치 방식)"
echo "============================================"
echo ""

# ── 가상환경 ────────────────────────────────────────────────────
VENV_DIR=".venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "[SETUP] Python 가상환경 생성 중..."
    python3 -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"

echo "[1/5] Python 의존성 설치..."
pip install --upgrade pip -q
pip install -r requirements-mobile.txt -q
pip install buildozer "cython<3" setuptools -q
echo "  [OK]"

# ── p4a 다운로드 (최초 1회) ──────────────────────────────────────
P4A_DIR=".buildozer/android/platform/python-for-android"
if [ ! -d "$P4A_DIR" ]; then
    echo ""
    echo "[2/5] p4a / SDK / NDK 다운로드 중 (최초 1회, 시간 소요)..."
    # android update triggers p4a download without full build
    timeout 600 buildozer android update 2>&1 | tail -5 || true
fi

# ── p4a 웹뷰 부트스트랩 사전 패치 ───────────────────────────────
echo ""
echo "[3/5] p4a 웹뷰 부트스트랩 사전 패치..."

BOOT_DIR="$P4A_DIR/pythonforandroid/bootstraps/webview/build"

# --- Patch A: AndroidManifest 템플릿 ---
echo ""
echo "  [A] AndroidManifest 템플릿 패치..."
MANIFEST_TMPL=$(find "$P4A_DIR" -path "*/webview/build/templates/AndroidManifest*.xml" 2>/dev/null | head -1)
if [ -z "$MANIFEST_TMPL" ]; then
    MANIFEST_TMPL=$(find "$P4A_DIR" -path "*/webview/build/AndroidManifest*.xml" 2>/dev/null | head -1)
fi
if [ -n "$MANIFEST_TMPL" ] && [ -f "$MANIFEST_TMPL" ]; then
    echo "      대상: $MANIFEST_TMPL"
    if ! grep -q "usesCleartextTraffic" "$MANIFEST_TMPL"; then
        sed -i 's|<application|<application android:usesCleartextTraffic="true"|' "$MANIFEST_TMPL"
        echo "      [OK] usesCleartextTraffic=true 추가"
    else
        echo "      [SKIP] 이미 적용됨"
    fi
    if ! grep -q "networkSecurityConfig" "$MANIFEST_TMPL"; then
        sed -i 's|<application|<application android:networkSecurityConfig="@xml/network_security_config"|' "$MANIFEST_TMPL"
        echo "      [OK] networkSecurityConfig 참조 추가"
    else
        echo "      [SKIP] 이미 적용됨"
    fi
    echo "      --- 패치 결과 확인 ---"
    grep -n "application" "$MANIFEST_TMPL" | head -3
    echo "      ---"
else
    echo "      [WARN] AndroidManifest 템플릿을 찾을 수 없습니다"
    echo "      검색 경로: $P4A_DIR"
    find "$P4A_DIR" -name "AndroidManifest*" 2>/dev/null || true
fi

# --- Patch B: network_security_config.xml 추가 ---
echo ""
echo "  [B] network_security_config.xml 생성..."
NSC_DIRS=$(find "$BOOT_DIR" -type d -name "main" 2>/dev/null)
if [ -z "$NSC_DIRS" ]; then
    NSC_DIRS="$BOOT_DIR/src/main"
fi
for d in $NSC_DIRS; do
    mkdir -p "$d/res/xml"
    cat > "$d/res/xml/network_security_config.xml" << 'XMLEOF'
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <domain-config cleartextTrafficPermitted="true">
        <domain includeSubdomains="false">localhost</domain>
        <domain includeSubdomains="false">127.0.0.1</domain>
    </domain-config>
</network-security-config>
XMLEOF
    echo "      [OK] $d/res/xml/network_security_config.xml"
done

# --- Patch C: AbsoluteLayout → FrameLayout ---
echo ""
echo "  [C] AbsoluteLayout 패치..."
JAVA_FILES=$(find "$P4A_DIR" -name "*.java" -exec grep -l "AbsoluteLayout" {} \; 2>/dev/null || true)
if [ -n "$JAVA_FILES" ]; then
    for jf in $JAVA_FILES; do
        echo "      패치: $jf"
        sed -i 's|import android\.widget\.AbsoluteLayout;|import android.widget.FrameLayout;|g' "$jf"
        sed -i 's|AbsoluteLayout\.LayoutParams|FrameLayout.LayoutParams|g' "$jf"
        sed -i 's|new AbsoluteLayout|new FrameLayout|g' "$jf"
        sed -i 's|AbsoluteLayout |FrameLayout |g' "$jf"
        echo "      [OK]"
    done
else
    echo "      [SKIP] AbsoluteLayout 미사용"
fi

# --- Patch D: WebView 설정 강화 ---
echo ""
echo "  [D] WebView 설정 강화..."
WV_LOADER=$(find "$P4A_DIR" -name "*.java" -path "*webview*" 2>/dev/null)
if [ -z "$WV_LOADER" ]; then
    WV_LOADER=$(find "$P4A_DIR" -name "*.java" -exec grep -l "WebView" {} \; 2>/dev/null | head -3)
fi
echo "      WebView 관련 Java 파일:"
echo "$WV_LOADER" | head -5
for wf in $WV_LOADER; do
    if [ -f "$wf" ] && grep -q "setJavaScriptEnabled" "$wf"; then
        echo "      패치 대상: $wf"
        if ! grep -q "setDomStorageEnabled" "$wf"; then
            sed -i '/setJavaScriptEnabled/a\
                webViewSettings.setDomStorageEnabled(true);\
                webViewSettings.setDatabaseEnabled(true);' "$wf" 2>/dev/null || \
            sed -i '/setJavaScriptEnabled/a\
                settings.setDomStorageEnabled(true);\
                settings.setDatabaseEnabled(true);' "$wf" 2>/dev/null || true
            echo "      [OK] DOM Storage 활성화"
        else
            echo "      [SKIP] 이미 적용됨"
        fi
    fi
done

# ── 기존 dist 삭제 (패치된 템플릿으로 재생성 강제) ──────────────
echo ""
echo "[4/5] 이전 dist 삭제 + 클린 빌드..."
rm -rf .buildozer/android/platform/build-arm64-v8a/dists/quantinsight
rm -rf .buildozer/android/platform/build-arm64-v8a/build/bootstrap_builds
rm -rf .buildozer/android/app
rm -rf bin/

echo "  빌드 시작 (소요 시간: 5~15분)..."
echo ""
buildozer android debug 2>&1 | tee build.log

# ── 빌드 후 검증 ─────────────────────────────────────────────────
echo ""
echo "[5/5] 빌드 결과 검증..."

DIST_DIR=".buildozer/android/platform/build-arm64-v8a/dists/quantinsight"
FINAL_MANIFEST="$DIST_DIR/src/main/AndroidManifest.xml"

if [ -f "$FINAL_MANIFEST" ]; then
    echo ""
    echo "  --- 최종 AndroidManifest.xml 확인 ---"
    if grep -q "usesCleartextTraffic" "$FINAL_MANIFEST"; then
        echo "  [OK] usesCleartextTraffic = true"
    else
        echo "  [FAIL] usesCleartextTraffic 누락!"
    fi
    if grep -q "networkSecurityConfig" "$FINAL_MANIFEST"; then
        echo "  [OK] networkSecurityConfig 참조됨"
    else
        echo "  [FAIL] networkSecurityConfig 누락!"
    fi
    echo "  ---"
fi

NSC_FINAL="$DIST_DIR/src/main/res/xml/network_security_config.xml"
if [ -f "$NSC_FINAL" ]; then
    echo "  [OK] network_security_config.xml 존재"
else
    echo "  [WARN] network_security_config.xml 누락 — 수동 복사 시도"
    mkdir -p "$DIST_DIR/src/main/res/xml"
    cat > "$NSC_FINAL" << 'XMLEOF'
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <domain-config cleartextTrafficPermitted="true">
        <domain includeSubdomains="false">localhost</domain>
        <domain includeSubdomains="false">127.0.0.1</domain>
    </domain-config>
</network-security-config>
XMLEOF
    echo "  [OK] 수동 복사 완료 — 재빌드 필요"
    echo ""
    echo "  재빌드 중..."
    rm -rf "$DIST_DIR/build/"
    buildozer android debug 2>&1 | tee build_rebuild.log
fi

echo ""
echo "============================================"
echo "  최종 결과"
echo "============================================"
echo ""

APK_FILE=$(ls -t bin/*.apk 2>/dev/null | head -1)
if [ -n "$APK_FILE" ]; then
    ls -lh "$APK_FILE"
    echo ""
    echo "  Windows로 복사:"
    echo "    cp \"$APK_FILE\" \"/mnt/f/PythonProjects/Quant Stock Daily/\""
else
    echo "  [ERROR] APK 파일을 찾을 수 없습니다!"
    echo "  build.log 를 확인해주세요"
    echo ""
    echo "  마지막 에러:"
    tail -30 build.log | grep -i "error\|fail\|exception" || tail -10 build.log
fi
echo ""
