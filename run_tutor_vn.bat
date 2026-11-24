@echo off
chcp 65001 >nul
title AuraTutor - Lớp Học Trực Tuyến 1:1
echo =======================================================
echo          ĐANG MỞ LỚP HỌC 1:1 AURATUTOR...
echo =======================================================

netstat -ano | findstr ":8010 " | findstr "LISTENING" >nul
if %errorlevel% equ 0 (
    echo [OK] Máy chủ AI đang chạy sẵn sàng trên cổng 8010!
    goto OPEN_APP
)

echo [INFO] Đang khởi động máy chủ AI trong nền...
cd /d "C:\Users\Tonton Yuta\LiveTalking"
call .venv\Scripts\activate.bat
start /b python app.py --transport webrtc --model wav2lip --avatar_id wav2lip_avatar_glass_man --tts edgetts --REF_FILE vi-VN-NamMinhNeural --listenport 8010 > server.log 2>&1
timeout /t 3 /nobreak >nul

:OPEN_APP
echo [INFO] Đang mở giao diện lớp học trực tuyến...
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --app=http://localhost:8010/index.html
    exit
)
if exist "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" (
    start "" "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --app=http://localhost:8010/index.html
    exit
)
start http://localhost:8010/index.html
exit
