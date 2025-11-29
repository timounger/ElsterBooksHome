# E-Mail-Vorlagen

Sie können individuelle E-Mail-Vorlagen erstellen, die beim Versand automatisch verwendet werden.  
Diese Vorlage wird genutzt, wenn Sie unter dem Tab **Kontakte** auf eine E-Mail doppelklicken.

- **Mail Betreff:** Inhalt der Betreffzeile.  
  *Beispiel Standardwert:* `Rechnung <Betreff>`  

- **Mailvorlage:** Text der E-Mail, mit Platzhaltern im Format `[%tag_name%]`.  
  Beim Versand werden die Platzhalter automatisch durch die entsprechenden Daten ersetzt.  

**Beispiel-Standardtext:**

```text
Hallo <Name>,

<Text>

Mit freundlichen Grüßen

[%name%]
[%line1%]
[%postCode%] [%city%]
[%phone%]
```
