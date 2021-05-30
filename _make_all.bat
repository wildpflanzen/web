@echo off
cd /D "%~dp0"/templates
/Bin/Python39/python.exe  render.py
pause