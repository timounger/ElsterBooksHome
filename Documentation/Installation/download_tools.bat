:: "download_tools.bat"
:: download tools

@echo off

set "URL=https://github.com/timounger/ElsterBooksTools/releases/download/latest/Tools.zip"
set "DEST_DIR=..\..\Resources"
set "ZIP_FILE=%DEST_DIR%\Tools.zip"
set "TOOLS_DIR=%DEST_DIR%\Tools"

:: Check if Tools folder already exist
if exist "%TOOLS_DIR%" (
    echo Folder "%TOOLS_DIR%" already exist.
    goto :END
)

:: Create outptu folder if not exist
if not exist "%DEST_DIR%" (
    mkdir "%DEST_DIR%"
    if errorlevel 1 (
        echo Destination folder "%DEST_DIR%" could not be created.
        goto :END
    )
)

:: Download Tools Date from URL
echo Lade "%URL%" herunter...
curl -L -o "%ZIP_FILE%" "%URL%"
if errorlevel 1 (
    echo Error downloading the file.
    goto :END
)

:: Unpack ZIP-File
echo Entpacke "%ZIP_FILE%" nach "%DEST_DIR%"...
powershell -Command "Expand-Archive -Path '%ZIP_FILE%' -DestinationPath '%DEST_DIR%' -Force"
if errorlevel 1 (
    echo Error unpacking the file.
    goto :END
)

:: Delete ZIP-File
echo Lösche "%ZIP_FILE%"...
del "%ZIP_FILE%"
if errorlevel 1 (
    echo Error deleting the ZIP file.
    goto :END
)

:END

::pause
