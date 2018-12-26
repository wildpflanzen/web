@echo off
set python=c:\python37\python.exe

set install=install --upgrade

%python% -m pip %install% pyyaml
%python% -m pip %install% jinja2

pause
