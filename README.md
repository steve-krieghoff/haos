# haos

Home Assistant configuration bits and custom integrations.

## Cat Feeding Tracker (`custom_components/cat_feeding`)

Trackt die Fütterung deiner Katze direkt in Home Assistant: Tagesgesamtmenge,
Anzahl Fütterungen, letzte Fütterung, Wochendurchschnitt und Restmenge bis zum
Tagesziel. Erfassung per Dashboard-Button (Standardportion) oder per Service
mit exakter Menge (z.B. per Sprachassistent/Assist oder Handy-Kurzbefehl).

### Installation über HACS

1. In Home Assistant: **HACS → drei Punkte oben rechts → Benutzerdefinierte
   Repositories**.
2. Repository-URL `https://github.com/steve-krieghoff/haos` eintragen,
   Kategorie **Integration** wählen, hinzufügen.
3. "Cat Feeding Tracker" in HACS suchen → installieren → Home Assistant neu
   starten.
4. **Einstellungen → Geräte & Dienste → Integration hinzufügen** → nach
   "Cat Feeding Tracker" suchen → Katzenname, Standardportion, Tagesziel
   eingeben.

### Was wird erzeugt?

Pro konfigurierter Katze (ein Gerät in Home Assistant; die genauen
`entity_id`s hängen vom gewählten Katzennamen ab und lassen sich unter
**Entwicklerwerkzeuge → Zustände** nachschlagen):

- `sensor.<katze>_futter_heute_gesamt` – Summe der heutigen Fütterungen (g)
- `sensor.<katze>_futterungen_heute` – Anzahl Fütterungen heute
- `sensor.<katze>_letzte_futterung` – Zeitpunkt der letzten Fütterung
- `sensor.<katze>_letzte_menge` – Menge der letzten Fütterung (g)
- `sensor.<katze>_durchschnitt_7_tage` – Durchschnittliche Tagesmenge, letzte 7 Tage
- `sensor.<katze>_restmenge_bis_tagesziel` – Restmenge bis zum konfigurierten Tagesziel
- `button.<katze>_jetzt_futtern` – Trägt sofort eine Standardportion ein
- Service `cat_feeding.log_feeding` – Trägt eine Fütterung mit exakter Menge,
  optionaler Futtersorte und Notiz ein (auch für mehrere Katzen nutzbar über
  das Feld `device_id`)

Die Fütterungshistorie wird zusätzlich 180 Tage lang in einer eigenen
Storage-Datei gespeichert (unabhängig von der Home-Assistant-Recorder-Historie),
damit Wochendurchschnitt & Co. auch nach einem Neustart korrekt bleiben.

### Dashboard

Siehe [`dashboard_example.yaml`](dashboard_example.yaml) für eine
Beispiel-Karte (Entitäten-Karte, Button, Verlaufsgrafik).

### Fütterung erfassen

- **Schnell (Standardportion):** Button `Jetzt füttern` auf dem Dashboard
  drücken.
- **Exakte Menge / Sprachbefehl:** Service `cat_feeding.log_feeding` aufrufen,
  z.B. aus einem Skript, einer Automatisierung, einer Handy-Kurzbefehl-App
  oder als Assist-Aktion:

  ```yaml
  action: cat_feeding.log_feeding
  data:
    amount_g: 50
    food_type: Nassfutter Huhn
  ```

  Um das per Sprache ("Hey Assist, füttere die Katze mit 50 Gramm") nutzbar
  zu machen, lege dir in **Einstellungen → Sprachassistenten → Skripte/Szenen**
  ein kleines Skript an, das diesen Service aufruft, und exponiere es für
  Assist.

### Hinweis

Dies ist eine HACS-**Integration** (kein Home-Assistant-**Supervisor-Add-on**
im Docker-Sinn). Sie läuft direkt im Home-Assistant-Core-Prozess und
funktioniert daher auch auf Home Assistant Container/Core-Installationen ohne
Supervisor. Die Daten landen in der normalen Home-Assistant-Historie/Statistik
(z.B. für die `statistics-graph`-Karte).
