:: "uninstall_packages.bat"
:: uninstall all packages

@echo off

set ENV_PATH=..\..\.venv
set PY_PATH=%ENV_PATH%\Scripts\python
set PACKAGE_FILE=installed_packages.txt

%PY_PATH% -m pip freeze > %PACKAGE_FILE%
%PY_PATH% -m pip uninstall -r %PACKAGE_FILE% -y
del %PACKAGE_FILE%

pause
