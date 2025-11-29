# Update

## Daten aktualisieren

Beim Speichern eines Belegs ohne Änderungen bleiben die Dateien normalerweise unverändert.  
Mit neueren Versionen kann es jedoch Anpassungen am **JSON-Schema** geben.  

Diese Funktion aktualisiert die JSON-Struktur aller Belege auf die aktuelle Version, um die Kompatibilität sicherzustellen.

## Daten aktualisieren (inkl. Dateinamen)

Initial wird der Dateiname eines Belegs anhand der erfassten Daten vergeben.  
Änderungen an den Belegdaten führen jedoch nicht automatisch zu einem neuen Dateinamen.

Mit dieser Funktion können alle Dateinamen **automatisch an die aktuellen Belegdaten angepasst** werden.

## Unvollständige Daten löschen

Überprüft alle Einnahmen, Ausgaben und Dokumente auf fehlende Zuordnungen:  

- PDF ohne passende JSON-Datei  
- JSON ohne passende PDF-Datei  

Unvollständige Dateien werden automatisch gelöscht.  

Dies ist besonders nützlich, wenn beim Löschen eines Eintrags eine Datei noch geöffnet war und nur die Gegenstelle gelöscht wurde. So wird die Datenintegrität wiederhergestellt.
