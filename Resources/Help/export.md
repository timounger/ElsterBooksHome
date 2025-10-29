\page export Export

\tableofcontents

# Tab Export

Über die Registerkarte „Export“ können relevante Dokumente generiert oder Daten exportiert werden.

## Steuerdokumente

### Umsatzsteuer-Voranmeldung

Erstellt eine Zusammenfassung der Umsatzsteuer-Voranmeldung für den definierten Zeitraum (Jahr und Zeitraum).
Die Umsatzsteuer aller Ein- und Ausgaben wird aufgelistet.

### Umsatzsteuererklärung

Erstellt eine Zusammenfassung für die Umsatzsteuererklärung des angegebenen Jahres (nur Jahr, Zeitraum wird ignoriert).
Die Umsatzsteuer aller Ein- und Ausgaben wird aufgelistet.
Zudem werden die bereits gezahlten Beträge in Form der Umsatzsteuer-Voranmeldungen des betroffenen Jahres aufgelistet.
Die Differenzberechnung ergibt, ob noch eine Zahlung an das Finanzamt zu leisten ist oder ob eine Erstattung erfolgt.

### Einnahmenüberschussrechnung

Erstellt eine Zusammenfassung für die Einnahmenüberschussrechnung für das angegebene Jahr.
Die Ein- und Ausgaben werden nach Gruppen getrennt summiert.
Die Umsatzsteuerbeträge werden automatisch als eigene Gruppe aufgelistet, da sie auch im Elsterformular getrennt aufgeschlüsselt werden müssen.

Die Berechnung erfolgt anhand des Datums der Zahlungsein- oder -ausgänge.
Umsatzsteuervoranmeldungen sind wiederkehrende Einnahmen und werden bis zum 10. Januar für das vorherige Jahr verbucht.

## Gewinn- und Verlustrechnung

Nur aktiv, wenn in den Einstellungen ausgewählt.
Im Gegensatz zur Einnahmenüberschussrechnung erfolgt hier die Berechnung nach Belegdatum.

## Export

### Übersicht Gesamt

Erstellt eine Übersicht aller erfassten Einnahmen und Ausgaben.

### Sicherung erstellen

Erstellt ein ZIP-Archiv mit allen Dokumenten, das als Backup verwendet werden kann.

## Kontoverbindung

### Transaktionen abfragen

Damit kann eine Verbindung zu Ihrem Konto hergestellt werden.
🔒 Ihr Benutzername und Ihre PIN werden sicher verschlüsselt in der Windows-Registrierung Ihres Benutzerkontos gespeichert.

Beim Abrufen der Transaktionen ist das ausgewählte TAN-Verfahren zu verwenden.
Folgen Sie dazu den Anweisungen.

⚠️ Achtung: Wenn das TAN-Verfahren mehrmals gestartet, aber nicht erfolgreich durchgeführt wird, kann dies zur Sperrung des Sicherheitsverfahrens führen.

Anschließend können offene Zahlungen automatisch zugeordnet werden:

- Bei den Einnahmen erfolgt dies über die Zuordnung der Rechnungsnummer.
- Bei den Ausgaben erfolgt dies aktuell nur anhand des Rechnungsbetrags, wodurch es zu falschen Zuordnungen kommen kann.

## PDF-Toolbox

### PDF kombinieren

Damit können mehrere PDF-Dateien ausgewählt werden, die zu einer einzigen Datei zusammengefügt werden.
Dies kann beispielsweise verwendet werden, um seine monatlichen Kontoauszüge pro Jahr zusammenzufügen und als eine Datei unter „Dokumente” zu importieren.

## Update

### Daten updaten

Wenn ein Beleg geöffnet und gespeichert wird, ohne die Belegdaten zu ändern, sollte sich die Datei in der Regel nicht verändern.
Bei neueren ElsterBooks-Versionen kann es jedoch zu Anpassungen im JSON-Schema kommen.

Mit dieser Funktionalität kann die JSON-Struktur für alle Belege auf die aktuelle Version gezogen werden.

### Daten updaten (inkl. Dateinamen)

Der Dateiname des Beleges wird initial anhand der Belegdaten vergeben.
Werden diese später geändert, bleibt der Dateiname unverändert.

Mit dieser Funktionalität werden alle Belege zusätzlich neu benannt.

### Unvollständige Daten löschen 🧹

Dabei werden alle Einnahmen, Ausgaben und Dokumente geprüft ob zur jeder PDF eine JSON-Datei mit den Metadaten abliegt und umgekehrt.
Kann keine Zuordnung gefunden werden wird die Datei gelöscht.

Dies kann erforderlich sein, wenn beim Löschen eines Eintrags die PDF noch geöffnet war und nur die JSON-Datei gelöscht werden konnte.

## Git-Aktionen

### Commit

Revisioniert den aktuellen Stand der Daten.

Diese Funktionalität wird beim Beenden des Programms automatisch aufgerufen, sofern Änderungen vorgenommen wurden.
