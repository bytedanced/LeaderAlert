@echo off
chcp 65001 >nul

REM 若本地已有 insightface 缓存模型而项目内缺失，复制检测/识别两个模型（其余模型本项目用不到）
if not exist "assets\models\buffalo_s\w600k_mbf.onnx" (
    if exist "%USERPROFILE%\.insightface\models\buffalo_s" (
        echo 正在复制 buffalo_s 模型到 assets\models ...
        mkdir "assets\models\buffalo_s" 2>nul
        copy /Y "%USERPROFILE%\.insightface\models\buffalo_s\det_*.onnx" "assets\models\buffalo_s\" >nul
        copy /Y "%USERPROFILE%\.insightface\models\buffalo_s\w*.onnx" "assets\models\buffalo_s\" >nul
    )
)
if not exist "assets\models\buffalo_s" (
    echo [警告] 未找到 buffalo_s 模型。请先联网运行一次主程序（自动下载），再重新打包。
)

uv sync
uv run python -m PyInstaller --noconfirm --clean --onefile --windowed --name LeaderAlert ^
  --add-data "assets\models;models" main.py

echo.
echo 打包完成：dist\LeaderAlert.exe
pause
127.0.0.1:6864