@echo off
set output=index.txt
echo.>>index.txt
echo listdir:>>index.txt
for /f %%f in ('dir /b') do echo   - %%f>>index.txt
pause