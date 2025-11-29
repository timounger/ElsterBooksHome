:: run mkdoc build

mkdir "docs\_assets\images"
copy "..\Resources\app.ico" "docs\_assets\images\app.ico"
copy "..\Resources\favicon.ico" "docs\_assets\images\favicon.ico"
copy "..\Resources\splash.gif" "docs\_assets\images\splash.gif"
copy "..\Resources\InvoiceImage\zugferd.svg" "docs\_assets\images\zugferd.svg"

rmdir /S /Q public
..\.venv\Scripts\mkdocs build

pause
