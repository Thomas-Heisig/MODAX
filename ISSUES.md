# MODAX - Bekannte Probleme (ISSUES)

Dieses Dokument verfolgt bekannte Probleme und Bugs im MODAX-System. Behobene Probleme werden nach `DONE.md` verschoben.

## Kritische Probleme

*Derzeit keine kritischen Probleme bekannt.*

## Wichtige Probleme

### Fehlerbehandlung & Robustheit

#### #001: Fehlende Fehlerbehandlung bei MQTT-Verbindungsabbruch
**Beschreibung:** Wenn die MQTT-Verbindung während des Betriebs abbricht, wird nicht automatisch eine Wiederverbindung hergestellt.
- **Betroffene Komponenten:** Python Control Layer (mqtt_handler.py)
- **Auswirkung:** Datenverlust bei Netzwerkproblemen
- **Priorität:** Hoch
- **Vorgeschlagene Lösung:** Automatische Reconnect-Logik mit exponentieller Backoff-Strategie implementieren

#### #002: API-Timeouts nicht konfigurierbar
**Beschreibung:** Timeouts für AI-Layer-Anfragen sind fest codiert und können nicht über Konfiguration angepasst werden.
- **Betroffene Komponenten:** Python Control Layer (ai_interface.py)
- **Auswirkung:** Keine Flexibilität für verschiedene Netzwerkbedingungen
- **Priorität:** Mittel
- **Vorgeschlagene Lösung:** Timeout-Werte in config.py konfigurierbar machen

#### #003: HMI zeigt keine Fehlermeldung bei API-Verbindungsfehler
**Beschreibung:** Wenn das HMI keine Verbindung zum Control Layer herstellen kann, bleibt die Benutzeroberfläche leer ohne Fehlermeldung.
- **Betroffene Komponenten:** C# HMI Layer (MainForm.cs)
- **Auswirkung:** Schlechte Benutzererfahrung, unklare Fehlerursache
- **Priorität:** Mittel
- **Vorgeschlagene Lösung:** Verbindungsstatus-Indikator und aussagekräftige Fehlerdialoge hinzufügen

### Logging & Monitoring

#### #004: Inkonsistente Log-Level über Komponenten hinweg
**Beschreibung:** Verschiedene Ebenen verwenden unterschiedliche Log-Level für ähnliche Events (z.B. DEBUG vs. INFO für Sensor-Daten).
- **Betroffene Komponenten:** Alle Python-Ebenen
- **Auswirkung:** Schwierige Fehlersuche, zu viele oder zu wenige Logs
- **Priorität:** Mittel
- **Vorgeschlagene Lösung:** Logging-Standard definieren und konsistent anwenden

#### #005: Fehlende strukturierte Logs
**Beschreibung:** Logs sind als einfache Strings formatiert, nicht als strukturierte JSON-Objekte.
- **Betroffene Komponenten:** Alle Python-Ebenen
- **Auswirkung:** Erschwert automatisierte Log-Analyse
- **Priorität:** Niedrig
- **Vorgeschlagene Lösung:** python-json-logger oder strukturiertes Logging einführen

### Dokumentation

#### #006: Fehlende API-Dokumentation
**Beschreibung:** REST-API-Endpunkte sind nicht vollständig dokumentiert (z.B. fehlen Request/Response-Schemas).
- **Betroffene Komponenten:** Python Control Layer, Python AI Layer
- **Auswirkung:** Schwierig für neue Entwickler, APIs zu nutzen
- **Priorität:** Mittel
- **Vorgeschlagene Lösung:** OpenAPI/Swagger-Dokumentation mit FastAPI generieren

#### #007: Konfigurationsoptionen nicht vollständig dokumentiert
**Beschreibung:** Einige Umgebungsvariablen und Konfigurationsoptionen sind nicht in den README-Dateien erklärt.
- **Betroffene Komponenten:** Alle Ebenen
- **Auswirkung:** Schwierige Konfiguration für Deployment
- **Priorität:** Mittel
- **Vorgeschlagene Lösung:** Vollständige Konfigurationsreferenz in SETUP.md erstellen

## Kleinere Probleme

### Code-Qualität

#### #008: Einige Python-Module haben keine Type Hints
**Beschreibung:** Nicht alle Funktionen haben vollständige Type-Annotations.
- **Betroffene Komponenten:** Python Control Layer, Python AI Layer
- **Auswirkung:** Schlechtere IDE-Unterstützung, schwerer zu wartender Code
- **Priorität:** Niedrig
- **Vorgeschlagene Lösung:** Schrittweise Type Hints hinzufügen, mypy für Type-Checking nutzen

#### #009: Magic Numbers in Code
**Beschreibung:** Einige Threshold-Werte sind direkt im Code als Zahlen geschrieben (z.B. Temperatur-Limits, Strom-Schwellenwerte).
- **Betroffene Komponenten:** ESP32 Field Layer, Python AI Layer (anomaly_detector.py)
- **Auswirkung:** Schwer zu verstehen und anzupassen
- **Priorität:** Niedrig
- **Vorgeschlagene Lösung:** Als benannte Konstanten extrahieren mit erklärenden Kommentaren

#### #010: Fehlende Eingabevalidierung in einigen API-Endpunkten
**Beschreibung:** Nicht alle API-Endpunkte validieren Eingabeparameter vollständig.
- **Betroffene Komponenten:** Python Control Layer (control_api.py)
- **Auswirkung:** Potenzielle Sicherheitsprobleme, unklare Fehlermeldungen
- **Priorität:** Mittel
- **Vorgeschlagene Lösung:** Pydantic-Modelle für alle Request-Bodies verwenden

### Performance

#### #011: Keine Caching-Strategie für häufig abgerufene Daten
**Beschreibung:** Jeder API-Aufruf generiert neue Berechnungen, auch wenn sich Daten nicht geändert haben.
- **Betroffene Komponenten:** Python Control Layer (control_api.py)
- **Auswirkung:** Unnötige CPU-Last bei vielen Clients
- **Priorität:** Niedrig
- **Vorgeschlagene Lösung:** Redis-Cache oder In-Memory-Cache für häufige Abfragen

#### #012: Große MQTT-Nachrichten bei hoher Sensor-Frequenz
**Beschreibung:** Bei 10Hz Sensor-Sampling werden viele kleine MQTT-Nachrichten gesendet.
- **Betroffene Komponenten:** ESP32 Field Layer
- **Auswirkung:** Höhere Netzwerklast
- **Priorität:** Niedrig
- **Vorgeschlagene Lösung:** Sensor-Daten batchen oder Protobuf für Kompression nutzen

### Benutzeroberfläche

#### #013: HMI-Update-Intervall fest codiert
**Beschreibung:** Das 2-Sekunden-Update-Intervall im HMI ist nicht konfigurierbar.
- **Betroffene Komponenten:** C# HMI Layer (MainForm.cs)
- **Auswirkung:** Keine Flexibilität für verschiedene Nutzungsszenarien
- **Priorität:** Niedrig
- **Vorgeschlagene Lösung:** Update-Intervall in Einstellungen konfigurierbar machen

#### #014: Fehlende Sortier- und Filterfunktionen im HMI
**Beschreibung:** Bei vielen verbundenen Geräten gibt es keine Möglichkeit, die Liste zu filtern oder zu sortieren.
- **Betroffene Komponenten:** C# HMI Layer (MainForm.cs)
- **Auswirkung:** Unübersichtlich bei großer Anzahl von Geräten
- **Priorität:** Niedrig
- **Vorgeschlagene Lösung:** Such- und Filterfunktion für Geräteliste hinzufügen

## Verbesserungsvorschläge (Enhancements)

### #015: AI-Modell-Confidence als visuelle Anzeige im HMI
**Beschreibung:** Die Confidence-Werte der AI-Analyse werden als Zahlen angezeigt, könnten aber visuell besser dargestellt werden.
- **Priorität:** Niedrig
- **Vorgeschlagene Lösung:** Fortschrittsbalken oder Ampel-System für Confidence-Level

### #016: Export-Funktion für Sensor-Daten
**Beschreibung:** Es gibt keine Möglichkeit, historische Sensor-Daten zu exportieren.
- **Priorität:** Niedrig
- **Vorgeschlagene Lösung:** CSV/JSON-Export-Button im HMI hinzufügen

### #017: Dark Mode für HMI
**Beschreibung:** Einige Benutzer bevorzugen eine dunkle Benutzeroberfläche.
- **Priorität:** Sehr Niedrig
- **Vorgeschlagene Lösung:** Theme-System mit Light/Dark-Mode-Unterstützung

## Hinweise

- Neue Issues sollten hier dokumentiert werden, bevor Code geändert wird
- Jedes Issue sollte eine eindeutige Nummer haben (#XXX)
- Prioritäten: Kritisch, Hoch, Mittel, Niedrig, Sehr Niedrig
- Bei Behebung eines Issues: In DONE.md verschieben mit Lösung und Commit-Hash
- Sicherheitsrelevante Issues sollten privat behandelt werden (nicht in öffentlichem Repo)
