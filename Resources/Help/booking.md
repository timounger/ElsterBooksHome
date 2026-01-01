# Buchhaltung

Dieses Modul dient zur Erfassung und Verwaltung aller buchhaltungsrelevanten Dokumente. Buchungen können ausschließlich zusammen mit einem Beleg im PDF- oder XML-Format erfasst werden.

## Kategorien

- Einnahmen: Erfassen von Zahlungseingängen
- Ausgaben: Erfassen von Zahlungsausgängen
- Dokumente: Ablage weiterer Unterlagen, die keine Zahlungen enthalten (z. B. Verträge, Schriftverkehr)

Buchungen können nur zusammen mit einem Beleg im PDF- oder XML-Format erfasst werden.

## Metadaten-Erfassung

Je nach Dokumenttyp können unterschiedliche Metadaten hinterlegt werden.

Die Metadaten lassen sich teilweise automatisch auslesen:

- Umsatzsteuererklärungen / Umsatzsteuervoranmeldungen: von Elster bereitgestellte PDFs werden automatisch analysiert.
- X-Rechnungen / ZUGFeRD-Rechnungen: Metadaten werden direkt aus den XML-Daten entnommen.
- Sonstige Dokumente: Können per KI-gestützter Texterkennung ausgelesen werden. Die gewünschte KI-Engine lässt sich in den Einstellungen auswählen und konfigurieren.

## Datenablage

Alle Dateien werden im Ordner „Data“ gespeichert.
Für diesen Ordner kann optional ein Git-Repository eingerichtet werden, um Dokumente revisionssicher abzulegen.
Beim Beenden des Programms werden Sie gefragt, ob Änderungen committet werden sollen.

## Anforderungen nach GoBD

Für eine ordnungsgemäße elektronische Buchführung müssen die Grundsätze zur ordnungsmäßigen Führung und Aufbewahrung von Büchern, Aufzeichnungen und Unterlagen (GoBD) eingehalten werden:

- Nachvollziehbarkeit und Nachprüfbarkeit: Alle Prozesse und Daten müssen für Dritte (z. B. Betriebsprüfer) verständlich sein.
- Vollständigkeit und Richtigkeit: Jeder Geschäftsvorfall muss vollständig und korrekt erfasst werden.
- Zeitgerechte Erfassung: Buchungen sollen zeitnah und in chronologischer Reihenfolge erfolgen.
- Unveränderbarkeit: Erfasste Originaldaten dürfen nicht verändert werden, ohne dies zu protokollieren.
- Protokollierung: Änderungen müssen dauerhaft nachvollziehbar sein.
- Verfahrensdokumentation: Es muss dokumentiert sein, wie das System genutzt wird, welche Prozesse existieren und wer dafür verantwortlich ist.
- Aufbewahrungspflichten: Alle Unterlagen müssen in der Regel 10 Jahre aufbewahrt werden.
- Maschinelle Auswertbarkeit: Daten müssen in einem Format vorliegen, das technisch auswertbar ist (z. B. für digitale Betriebsprüfungen).

## Datensicherung

Da die Aufbewahrungspflicht von Belegen 10 Jahre beträgt, ist eine regelmäßige Datensicherung zwingend erforderlich.

Empfohlene Maßnahmen:

- Regelmäßige Backups auf externe Datenträger oder Cloud-Speicher
- Synchronisation mit GitHub zur zusätzlichen Absicherung und revisionssicheren Archivierung
