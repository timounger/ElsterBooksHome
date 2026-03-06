# Export

Über die Registerkarte „Export“ können steuerrelevante Dokumente erzeugt sowie Daten aus dem System exportiert werden.

## Steuerdokumente

### Umsatzsteuer-Voranmeldung

Erstellt eine Zusammenfassung der Umsatzsteuer-Voranmeldung für den angegebenen Zeitraum (Jahr und Zeitraum).
Alle Umsatzsteuerbeträge aus Einnahmen und Ausgaben werden aufgeführt.

### Umsatzsteuererklärung

Erstellt eine Zusammenfassung für die Umsatzsteuererklärung des ausgewählten Jahres.
Der Zeitraum wird hierbei ignoriert.

Aufgeführt werden:

- alle Umsatzsteuerbeträge des Jahres
- alle im selben Jahr bereits gemeldeten und gezahlten Beträge aus den Umsatzsteuer-Voranmeldungen

Aus der Differenz ergibt sich, ob eine Nachzahlung zu leisten ist oder eine Erstattung erfolgt.

### Einnahmenüberschussrechnung (EÜR)

Erstellt eine Zusammenfassung der Einnahmenüberschussrechnung für das angegebene Jahr.

- Einnahmen und Ausgaben werden gruppiert und summiert.
- Umsatzsteuerbeträge werden gesondert ausgewiesen, wie es auch im Elster-Formular erforderlich ist.

Die Berechnung erfolgt auf Basis des Zahlungsdatums.
Umsatzsteuer-Voranmeldungen werden als wiederkehrende Einnahmen behandelt und bis zum 10. Januar des Folgejahres dem alten Jahr zugerechnet.

## Gewinn- und Verlustrechnung (GuV)

Diese Funktion ist nur verfügbar, wenn sie in den Einstellungen aktiviert wurde.
Im Gegensatz zur EÜR erfolgt die Berechnung nach Belegdatum.

## Export

### Übersicht Gesamt

Erstellt eine vollständige Übersicht aller erfassten Einnahmen und Ausgaben.

### Sicherung erstellen

Erstellt ein ZIP-Archiv mit allen gespeicherten Dokumenten zur Verwendung als Backup.

## Kontoverbindung

### Transaktionen abfragen

Über diese Funktion kann eine Verbindung zu Ihrem Bankkonto hergestellt werden.

🔒 Sicherheit: Benutzername und PIN werden verschlüsselt in der Windows-Registrierung Ihres Benutzerkontos gespeichert.

Beim Abruf der Transaktionen ist das ausgewählte TAN-Verfahren zu verwenden.
Folgen Sie den Anweisungen des Systems.

⚠️ Achtung: Mehrfach gestartete, aber nicht abgeschlossene TAN-Vorgänge können zur Sperrung des Sicherheitsverfahrens führen.

Nach erfolgreichem Abruf können offene Zahlungen automatisch zugeordnet werden:

- Einnahmen: Zuordnung über die Rechnungsnummer
- Ausgaben: Zuordnung erfolgt derzeit nur anhand des Rechnungsbetrags → kann zu Fehlzuordnungen führen

## PDF-Toolbox

### PDF kombinieren

Hiermit können mehrere PDF-Dateien zu einer einzigen Datei zusammengeführt werden.
Dies ist z. B. nützlich, um monatliche Kontoauszüge eines Jahres zu einer Datei zusammenzufassen und unter „Dokumente“ zu importieren.

## Update

### Daten aktualisieren

Wenn ein Beleg geöffnet und gespeichert wird, ohne dass Daten geändert wurden, sollte die Datei normalerweise unverändert bleiben.
Bei neueren Versionen kann es jedoch Anpassungen am JSON-Schema geben.

Diese Funktion aktualisiert die JSON-Struktur aller Belege auf die aktuelle Version.

### Daten aktualisieren (inkl. Dateinamen)

Der Dateiname eines Belegs wird initial anhand der erfassten Daten vergeben.
Änderungen an den Belegdaten führen jedoch nicht automatisch zu einem neuen Dateinamen.

Diese Funktion aktualisiert zusätzlich alle Dateinamen entsprechend den aktuellen Belegdaten.

### Unvollständige Daten löschen 🧹

Prüft alle Einnahmen, Ausgaben und Dokumente darauf, ob zu jeder PDF-Datei eine passende JSON-Datei vorhanden ist – und umgekehrt.
Wird keine passende Zuordnung gefunden, wird die Datei gelöscht.

Dies ist z. B. erforderlich, wenn beim Löschen eines Eintrags die PDF noch geöffnet war und deshalb nur die JSON-Datei gelöscht wurde.

## Git-Aktionen

### Commit

Erstellt eine Revision des aktuellen Datenstands.
Diese Funktion wird beim Beenden des Programms automatisch ausgeführt, sofern Änderungen vorgenommen wurden.
