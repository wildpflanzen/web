@echo off
set python=c:\python37\python.exe

set install=install --upgrade
%python% -m pip %install% pip
%python% -m pip %install% pyyaml
%python% -m pip %install% jinja2
%python% -m pip %install% tinydb
pause
