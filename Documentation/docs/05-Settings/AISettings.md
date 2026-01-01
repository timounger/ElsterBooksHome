# KI-Einstellungen für Intelligente Belegerfassung

In diesem Bereich konfigurieren Sie die Funktionen zur automatischen Belegerkennung und Datenextraktion.

## Verfügbare KI-Engines

- **Deaktiviert:** Keine KI-Unterstützung.
- **ChatGPT:** Nutzt die Online-API von OpenAI. Ein gültiger API-Key ist erforderlich.
- **Mistral:** Nutzt die Online-API von Mistral. Ein gültiger API-Key ist erforderlich.
- **Ollama:** Arbeitet vollständig offline. Erfordert ausreichend Rechenleistung und Speicher.

## Modell

Hier geben Sie das jeweils verwendete Sprachmodell der ausgewählten KI-Engine an.

## API-Key

- Ein API-Key ist erforderlich, um die Online-Engine zu nutzen.
- Sie können den Key über Ihr OpenAI-Konto erstellen:  
  1a. ChatGPT: Besuchen Sie [https://platform.openai.com/account/api-keys](https://platform.openai.com/account/api-keys)  
  1b. Mistral: Besuchen Sie [https://console.mistral.ai/](https://console.mistral.ai/)  
  2. Melden Sie sich an oder erstellen Sie ein Konto.  
  3. Generieren Sie einen neuen API-Key und kopieren Sie ihn in das entsprechende Feld in den KI-Einstellungen.

> ⚠️ **Hinweis:** Der API-Key muss über ein Guthaben verfügen, damit Anfragen verarbeitet werden können. Stellen Sie sicher, dass Ihr Konto aufgeladen ist, bevor Sie die KI-Funktion nutzen.

## Speicherung der Einstellungen

Alle KI-Einstellungen und Zugangsdaten werden verschlüsselt in der **Windows-Registrierung** des aktuellen Benutzers gespeichert.
