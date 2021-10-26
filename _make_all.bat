@echo off
set PATH=\Bin\Python39;%PATH%

cd /D "%~dp0"/templates

python.exe render.py
python.exe sitemap.py

pause