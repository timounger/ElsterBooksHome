# Belegerfassung

In den Tabs **Einnahmen** und **Ausgaben** können Belege effizient erfasst werden.  

Zum Erfassen eines Belegs stehen zwei Möglichkeiten zur Verfügung:  

- Über den Button **„Einnahme bzw. Ausgabe erfassen“** öffnet sich ein Dateidialog, in dem das entsprechende Dokument ausgewählt werden kann.  
- Alternativ können Dateien per **Drag & Drop** direkt in das entsprechende Label auf dem Tab gezogen werden.

## Kategorien

- **Einnahmen:** Erfassen von Zahlungseingängen  
- **Ausgaben:** Erfassen von Zahlungsausgängen  
- **Dokumente:** Ablage weiterer Unterlagen, die keine Zahlungen enthalten (z. B. Verträge, Schriftverkehr)

> Hinweis: Buchungen können nur zusammen mit einem Beleg im **PDF- oder XML-Format** erfasst werden.

## Metadaten-Erfassung

Je nach Dokumenttyp können unterschiedliche **Metadaten** hinterlegt werden.  

Die Metadaten lassen sich teilweise automatisch auslesen:

- **Umsatzsteuererklärungen / Umsatzsteuervoranmeldungen:** PDFs von Elster werden automatisch analysiert.  
- **X-Rechnungen / ZUGFeRD-Rechnungen:** Metadaten werden direkt aus den XML-Daten übernommen.  
- **Sonstige Dokumente:** Metadaten können per KI-gestützter Texterkennung ausgelesen werden. Die gewünschte **KI-Engine** lässt sich in den Einstellungen auswählen und konfigurieren. Siehe [➡️ KI Konfigurieren](../05-Settings/AISettings.md)

> Tipp: Prüfen Sie bei automatischer Erfassung die Metadaten vor dem Speichern, um Korrektheit sicherzustellen.

## Dokumentenablage

Bei der Belegerfassung werden immer **zwei Dateien** im jeweiligen Unterordner des `Data`-Ordners abgelegt:  

1. Der Beleg selbst (PDF/XML)  
2. Eine JSON-Datei mit allen hinterlegten Metadaten  

Da keine zentrale Datenbank verwendet wird, können die Belege **direkt über den Explorer geöffnet oder weiterverarbeitet** werden.

??? danger "Zugriffs- und Konsistenzhinweis"
    Manuelles Entfernen oder Bearbeiten von Dokumenten außerhalb von ElsterBooks kann zu Inkonsistenzen führen.  
    Änderungen sollten immer über die Anwendung vorgenommen werden.  
    Zudem können Probleme auftreten, wenn Dokumente gelöscht oder bearbeitet werden, während sie noch geöffnet sind.
