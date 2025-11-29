:: run mkdoc serve

::set puml_jar_path=plantuml.jar
::start /b java -jar %puml_jar_path% -picoweb:8080:127.0.0.1
::set PLANTUML_SERVER=http://127.0.0.1:8080
start http://localhost:8000

..\.venv\Scripts\mkdocs serve

pause
