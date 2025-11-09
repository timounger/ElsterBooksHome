\page CHANGELOG Changelog 📋️

## v0.3.0  Testversion Release 09.11.2025

[Download](https://github.com/timounger/ElsterBooksHome/releases/tag/v0.3.0)

_[compare to previous version](https://github.com/timounger/ElsterBooksHome/compare/v0.2.0...v0.3.0)_

### Features

- Die Rechnungsvorlage kann auch als PDF oder XML importiert werden.
- Transaktionen: Daten löschen Button
- Integriertes Update für zukünftige neue ElsterBooks Versionen

### Bug fixes

- Export Diagramme unter Berücksichtigung der 10 Tage frit für wiederkehrende Zahlungen dem Vorjahr zuordnen (identisch zu EÜR)
- Dialog für Belege öffnen schneller (Initial Ressourcen vorladen)
- Transaktionen abrufen: Crash fix bie Zuordnung und Löschen Button

## v0.2.0  Testversion Release 29.10.2025

[Download](https://github.com/timounger/ElsterBooksHome/releases/tag/v0.2.0)

_[compare to previous version](https://github.com/timounger/ElsterBooksHome/compare/v0.1.0...v0.2.0)_

### Features

- Bankanbindung über FinTS sowie Zuordnung von Transaktionen
- QR-Code für Rechnungen
- Unvollständige Daten löschen: Löscht automatisch Einnahmen, Ausgaben oder Dokumente welche nur Metadaten oder nur Anhang haben
- Rechnung direkt an Kontakt ausstellen: Diese Option ist im Kontextmenü der Kontakte verfügbar
- Änderungsansicht im Commit Dialog integriert: "TortoiseGit Merge" View
- Update-Benachrichtigung

### Bug fixes

- Die Dokumentationshilfe für den Export wurde angepasst.
- Umsatzsteuer-ID-Format der Kontakte für alle bekannten Länder prüfen.
- Widget Style Veränderungen zurücksetzen (geändertes Verhalten von PyQt)
- In ZUGFeRD eingebettete X-Rechnungen werden erkannt.
- Fälliger Zahlungsbetrag als optional Parameter behandelt
- Gesamt Brutto statt Fälligkeitsbetrag bei erkannten E-Rechnungen importieren
- Elektronische Adresse (BT-34, BT-49) schreiben.
- Artikel Mengenanzahl alle Mengenangaben möglich (Problem mit der Exponentialschreibweise)
- Name der Bank Label bei Rechnungen schreiben im Erweiterten Modus korrigiert

## v0.1.0 Testversion Release 06.09.2025

[Download](https://github.com/timounger/ElsterBooksHome/releases/tag/v0.1.0)

- Initiale Testversion
