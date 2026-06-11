:: run mkdoc serve

::set puml_jar_path=plantuml.jar
::start /b java -jar %puml_jar_path% -picoweb:8080:127.0.0.1
::set PLANTUML_SERVER=http://127.0.0.1:8080
start http://localhost:8000

mkdir "docs\_assets\images"
copy "..\Resources\app.ico" "docs\_assets\images\app.ico"
copy "..\Resources\favicon.ico" "docs\_assets\images\favicon.ico"
copy "..\Resources\splash.gif" "docs\_assets\images\splash.gif"
copy "..\Resources\InvoiceImage\zugferd.svg" "docs\_assets\images\zugferd.svg"

poetry run mkdocs serve

pause
