# Standardwerte

Mit den Standardwerten können bestimmte Felder in Belegen, Rechnungen und Buchungen automatisch mit vordefinierten Werten befüllt werden.  
Dies erleichtert die Dateneingabe und sorgt für einheitliche Prozesse.

- **UStVA-Periode:** Voreinstellung für den Abgabezeitraum der Umsatzsteuervoranmeldung (monatlich oder quartalsweise).
- **Bezahlt:** Legt fest, ob der Status „bezahlt“ bei neuen Belegen standardmäßig aktiviert ist.
- **Bar bezahlt:** Automatische Voreinstellung, ob ein neuer Beleg als Barzahlung gekennzeichnet wird.
- **Standard Gruppe Einnahme:** Vordefinierte Kategorie für neue Einnahmebelege.
- **Standard Gruppe Ausgabe:** Vordefinierte Kategorie für neue Ausgabenbelege.
- **Liste aller Gruppen:** Auflistung aller üblichen Einnahme- und Ausgabenkategorien für eine schnellere Auswahl.
- **Rechnungsnummer:** Siehe detaillierte Beschreibung unten.
- **Zahlungsziel:** Voreingestellte Anzahl an Tagen bis zur Fälligkeit einer Rechnung (z. B. 14, 30, 60 Tage).
- **Verwendungszweck:** Verwendungszweck mit Rechnungsnummer als Platzhalter `{number}`.

## Rechnungsnummer (detaillierte Beschreibung)

Die Rechnungsnummer kann flexibel über Platzhalter und Sequenzen aufgebaut werden, um individuelle Nummerierungssysteme abzubilden.

**Verfügbare Platzhalter:**

- `{YYYY}` – Vierstellige Jahreszahl (z. B. 2025)
- `{YY}` – Zweistellige Jahreszahl (z. B. 25)
- `{Y}` – Einstellige Jahreszahl (z. B. 5)
- `{MM}` – Monat zweistellig (01–12)
- `{DD}` – Tag zweistellig (01–31)
- `{SEQ:<reset>:<length>:<start>:<increment>}` – Laufende Nummer
  - **reset:** none / yearly / monthly / daily (default: none)
  - **length:** Stellenanzahl (mit führenden Nullen) (default: 0)
  - **start:** Startwert der Sequenz (default: 1)
  - **increment:** Schrittweite der Nummerierung (default: 1)

**Beispiele:**

- `RE-{YYYY}-{SEQ:none:4:1:1}` → `RE-2025-0001`, `RE-2025-0002`
- `{YYYY}{MM}-{SEQ:monthly:3:1:1}` → Januar: `202501-001`, Februar: `202502-001`
- `{YY}{MM}{DD}-{SEQ:daily:2:0:1}` → `250312-00`, `250312-01`
- `{SEQ:none:6:1:1}` → `000001`, `000002`
