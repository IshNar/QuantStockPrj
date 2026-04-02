@echo off
echo ============================================
echo   퀀트 인사이트 - EXE 빌드 스크립트
echo ============================================
echo.

echo [1/3] 의존성 설치 중...
pip install -r requirements.txt
if errorlevel 1 (
    echo 의존성 설치 실패!
    pause
    exit /b 1
)
echo.

echo [2/3] PyInstaller로 EXE 빌드 중...
pyinstaller --noconfirm --onefile --windowed ^
    --name "QuantInsight" ^
    --hidden-import=clr ^
    --hidden-import=webview ^
    --collect-all webview ^
    --add-data "templates;templates" ^
    --exclude-module PyQt6 ^
    main.py

if errorlevel 1 (
    echo 빌드 실패!
    pause
    exit /b 1
)
echo.

echo [3/3] 빌드 완료!
echo.
echo  EXE 파일 위치: dist\QuantInsight.exe
echo.
echo  이 파일을 원하는 곳에 복사하여 실행하세요.
echo  (첫 실행 시 설정에서 API 키를 입력해야 합니다)
echo.
pause
