@echo off
echo ==============================================
echo 正在編譯 ImportSCL.cs ...
echo ==============================================

set COMPILER_PATH=C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe
set DLL_PATH="C:\Program Files\Siemens\Automation\Portal V17\PublicAPI\V17\Siemens.Engineering.dll"

"%COMPILER_PATH%" /reference:%DLL_PATH% /out:ImportSCL.exe ImportSCL.cs

if %errorlevel% neq 0 (
    echo [錯誤] 編譯失敗！
    exit /b %errorlevel%
)

echo [成功] 已產生 ImportSCL.exe。
pause
