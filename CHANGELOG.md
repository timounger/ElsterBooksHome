# Changelog

## Legende

| Kategorie         | Bedeutung                                |
| ----------------- | ---------------------------------------- |
| ✨ Feature        | Neue Funktionen, Erweiterungen           |
| 🔧 Bugfix         | Fehlerbehebungen, Stabilitätskorrekturen |
| 🚀 Verbesserungen | Optimierungen, Performance, Reworks      |
| 📚 Dokumentation  | Änderungen an Dokumentation & Texten     |

## [v0.4.0](https://github.com/timounger/ElsterBooksHome/releases/tag/v0.4.0) latest

- ✨ Mistral als KI für intelligente Belegerkennung verfügbar
- 🔧 Export Übersicht Gesamt: Auch nicht bezahlte Belege auflisten
- 🔧 Ausschreibung/Los (BT-17) korrekt schreiben (hat Wareneingangsmeldung (BT-15) überschrieben)
- 🔧 Ollama eigene Modellauswahl
- 🔧 Export Tab: Nach dem Jahreswechsel wird für weitere 10 Tage das vorherige Jahr angezeigt.
- 🚀 Artikelpositionen in Rechnungen verschieben und Löschen
- 🚀 Verwendungszweck: abhängig von der Rechnungsnummer in den Einstellungen definierbar
- 🚀 KI-Assistent verfasst Beschreibungsfeld für Belegerkennung auf Deutsch
- 🚀 ZUGFeRD letzte Tab Ansicht persistieren (PDF oder XML)
- 📚 Positionssumme bei Rechnung erstellen immer anzeigen
- 📚 ToolTip bei E-Rechnungsfeldern hinzugefügt

## [v0.3.1](https://github.com/timounger/ElsterBooksHome/releases/tag/v0.3.1) Testversion Release 29.11.2025

- 🚀 Rechnungsnummern: Individuell in den Einstellungen mit Hilfe von Datum und Sequenz Pattern gestalten
- 🚀 QR-Code: Letzte Einstellung wird gespeichert
- 🚀 Verbesserte Darstellung erstellter Rechnungen
- 📚 Lizenztext hinzugefügt

## [v0.3.0](https://github.com/timounger/ElsterBooksHome/releases/tag/v0.3.0) Testversion Release 09.11.2025

- ✨ Rechnungsvorlagen: Import von ZUGFeRD PDF oder XML möglich
- ✨ Integrierter Update-Mechanismus für zukünftige ElsterBooks-Versionen
- 🔧 Export Diagramme: Berücksichtigung der 10-Tage-Frist für wiederkehrende Zahlungen (identisch zu EÜR)
- 🔧 Transaktionen abrufen: Crash behoben bei Zuordnung und Löschen
- 🚀 Transaktionen: Daten-Löschen-Button hinzugefügt
- 🚀 Dialog „Belege öffnen“ beschleunigt (Initial-Ressourcen vorladen)

## [v0.2.0](https://github.com/timounger/ElsterBooksHome/releases/tag/v0.2.0) Testversion Release 29.10.2025

- ✨ Bankanbindung über FinTS und automatische Transaktionszuordnung
- ✨ QR-Code für Rechnungen
- ✨ „Unvollständige Daten löschen“: Löscht Einnahmen, Ausgaben oder Dokumente, die nur Metadaten oder Anhänge enthalten
- ✨ Änderungsansicht im Commit-Dialog integriert („TortoiseGit Merge“-View)
- ✨ Update-Benachrichtigung hinzugefügt
- 🔧 Umsatzsteuer-ID-Format für alle bekannten Länder geprüft
- 🔧 Widget-Style zurückgesetzt (PyQt-Änderungen korrigiert)
- 🔧 Eingebettete X-Rechnungen in ZUGFeRD werden erkannt
- 🔧 Fälliger Zahlungsbetrag als optionaler Parameter behandelt
- 🔧 Gesamtbrutto statt Fälligkeitsbetrag bei E-Rechnungen importiert
- 🔧 Elektronische Adresse (BT-34, BT-49) schreiben.
- 🔧 Mengenangaben bei Artikeln korrekt importiert (Problem mit Exponentialschreibweise behoben)
- 🔧 Bankname-Label bei Rechnungen im erweiterten Modus korrigiert
- 🚀 Rechnungen direkt an Kontakte ausstellen (über Kontextmenü)
- 📚 Dokumentationshilfe für Export angepasst

## [v0.1.0](https://github.com/timounger/ElsterBooksHome/releases/tag/v0.1.0) Testversion Release 06.09.2025

- ✨ Initiale Testversion
