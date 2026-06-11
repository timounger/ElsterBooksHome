@echo off
:: setup.bat [groups]
::   no args        - install everything (dev / local default)
::   <groups>       - install main + the comma-separated groups
::                    examples: "source,test", "source,exec", "source,docs"
::
:: Groups defined in pyproject.toml:
::   source  - runtime dependencies (Source folder)
::   exec    - PyInstaller / Nuitka build tools
::   test    - pylint, mypy, pytest, yamllint, etc.
::   docs    - Doxygen helpers

:: In CI (CI=true on GitHub runners) validate the committed lockfile instead of
:: regenerating it: an out-of-date poetry.lock fails the build (reproducible installs).
:: Locally the lock is (re)generated for convenience.
if "%CI%"=="true" (
    poetry check --lock
    if errorlevel 1 exit /b 1
) else (
    poetry lock
)
if "%~1"=="" (
    poetry sync --all-groups
) else (
    poetry sync --only main,%~1
)
::pause
