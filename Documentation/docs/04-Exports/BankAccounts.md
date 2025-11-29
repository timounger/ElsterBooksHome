# Kontoverbindung

## Transaktionen abfragen

Mit dieser Funktion können Sie eine sichere Verbindung zu Ihrem Bankkonto herstellen und Ihre Transaktionen abrufen.

??? info "Sicherheitshinweis"
    Benutzername und PIN werden **verschlüsselt** in der Windows-Registrierung Ihres Benutzerkontos gespeichert.

Beim Abruf der Transaktionen ist das gewählte TAN-Verfahren zu verwenden.  
Folgen Sie stets den Anweisungen Ihres Bankensystems.

??? warning "Gefahr: Sperrung des TAN-Verfahrens"
    Mehrfach gestartete, aber nicht abgeschlossene TAN-Vorgänge können zur Sperrung des Sicherheitsverfahrens führen.

Nach erfolgreichem Abruf können offene Zahlungen automatisch zugeordnet werden:

- **Einnahmen:** Zuordnung über die Rechnungsnummer  
- **Ausgaben:** Zuordnung erfolgt derzeit nur anhand des Rechnungsbetrags → dies kann zu Fehlzuordnungen führen
