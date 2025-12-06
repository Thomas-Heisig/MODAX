# MODAX - Bekannte Probleme (ISSUES)

Dieses Dokument verfolgt bekannte Probleme und Bugs im MODAX-System. Behobene Probleme werden nach `DONE.md` verschoben.

## Kritische Probleme

*Derzeit keine kritischen Probleme bekannt.*

## Wichtige Probleme

### Fehlerbehandlung & Robustheit

#### ~~#001: Fehlende Fehlerbehandlung bei MQTT-Verbindungsabbruch~~ ✅ BEHOBEN
**Beschreibung:** Wenn die MQTT-Verbindung während des Betriebs abbricht, wird nicht automatisch eine Wiederverbindung hergestellt.
- **Betroffene Komponenten:** Python Control Layer (mqtt_handler.py)
- **Auswirkung:** Datenverlust bei Netzwerkproblemen
- **Priorität:** Hoch
- **Status:** ✅ Behoben in Commit 5dafac9
- **Lösung:** Automatische Reconnect-Logik mit exponentieller Backoff-Strategie implementiert
  - MQTT_RECONNECT_DELAY_MIN = 1s
  - MQTT_RECONNECT_DELAY_MAX = 60s
  - MQTT_RECONNECT_BACKOFF_MULTIPLIER = 2
  - Automatische Wiederverbindung bei Verbindungsabbruch

#### ~~#002: API-Timeouts nicht konfigurierbar~~ ✅ BEHOBEN
**Beschreibung:** Timeouts für AI-Layer-Anfragen sind fest codiert und können nicht über Konfiguration angepasst werden.
- **Betroffene Komponenten:** Python Control Layer (ai_interface.py, config.py)
- **Auswirkung:** Keine Flexibilität für verschiedene Netzwerkbedingungen
- **Priorität:** Mittel
- **Status:** ✅ Behoben in Commit 5dafac9
- **Lösung:** Timeout-Werte über Umgebungsvariablen konfigurierbar
  - AI_LAYER_URL (Standard: http://localhost:8001/analyze)
  - AI_LAYER_TIMEOUT (Standard: 5 Sekunden)

#### ~~#003: HMI zeigt keine Fehlermeldung bei API-Verbindungsfehler~~ ✅ BEHOBEN
**Beschreibung:** Wenn das HMI keine Verbindung zum Control Layer herstellen kann, bleibt die Benutzeroberfläche leer ohne Fehlermeldung.
- **Betroffene Komponenten:** C# HMI Layer (MainForm.cs, ControlLayerClient.cs)
- **Auswirkung:** Schlechte Benutzererfahrung, unklare Fehlerursache
- **Priorität:** Mittel
- **Status:** ✅ Behoben in Commit e20cd31
- **Lösung:** Verbindungsstatus-Anzeige und Fehlerbehandlung implementiert
  - Verbindungsstatus in System-Status-Label mit Farbcodierung
  - Unterscheidung zwischen Verbindungs-, Timeout- und allgemeinen Fehlern
  - Fehlerdialog beim Startup mit Troubleshooting-Hinweisen
  - "No data available" Anzeige wenn Daten nicht abgerufen werden können
  - Automatische Verbindungsprüfung vor Datenabfragen

### Logging & Monitoring

#### ~~#004: Inkonsistente Log-Level über Komponenten hinweg~~ ✅ BEHOBEN
**Beschreibung:** Verschiedene Ebenen verwenden unterschiedliche Log-Level für ähnliche Events (z.B. DEBUG vs. INFO für Sensor-Daten).
- **Betroffene Komponenten:** Alle Python-Ebenen
- **Auswirkung:** Schwierige Fehlersuche, zu viele oder zu wenige Logs
- **Priorität:** Mittel
- **Status:** ✅ Behoben in Commit 5dafac9
- **Lösung:** Logging-Standard dokumentiert und angewendet
  - docs/LOGGING_STANDARDS.md erstellt mit vollständigen Richtlinien
  - Konsistentes Format über alle Python-Module
  - Klare Definition wann welches Log-Level zu verwenden ist

#### #005: Fehlende strukturierte Logs
**Beschreibung:** Logs sind als einfache Strings formatiert, nicht als strukturierte JSON-Objekte.
- **Betroffene Komponenten:** Alle Python-Ebenen
- **Auswirkung:** Erschwert automatisierte Log-Analyse
- **Priorität:** Niedrig
- **Vorgeschlagene Lösung:** python-json-logger oder strukturiertes Logging einführen

### Dokumentation

#### ~~#006: Fehlende API-Dokumentation~~ ✅ BEHOBEN
**Beschreibung:** REST-API-Endpunkte sind nicht vollständig dokumentiert (z.B. fehlen Request/Response-Schemas).
- **Betroffene Komponenten:** Python Control Layer, Python AI Layer
- **Auswirkung:** Schwierig für neue Entwickler, APIs zu nutzen
- **Priorität:** Mittel
- **Status:** ✅ Behoben - docs/API.md erstellt
- **Lösung:** Vollständige API-Dokumentation mit allen Endpunkten, Request/Response-Schemas und Beispielen

#### ~~#007: Konfigurationsoptionen nicht vollständig dokumentiert~~ ✅ BEHOBEN
**Beschreibung:** Einige Umgebungsvariablen und Konfigurationsoptionen sind nicht in den README-Dateien erklärt.
- **Betroffene Komponenten:** Alle Ebenen
- **Auswirkung:** Schwierige Konfiguration für Deployment
- **Priorität:** Mittel
- **Status:** ✅ Behoben - docs/CONFIGURATION.md erstellt
- **Lösung:** Vollständige Konfigurationsreferenz mit allen Umgebungsvariablen und Standardwerten

#### #018: Fehlende Sicherheitsdokumentation
**Beschreibung:** Sicherheitskonzept (TLS, Authentifizierung, Audit-Logging) nicht dokumentiert.
- **Betroffene Komponenten:** Alle Ebenen
- **Auswirkung:** Unsichere Produktionsbereitstellung
- **Priorität:** Kritisch
- **Status:** ✅ Behoben - docs/SECURITY.md erstellt
- **Lösung:** Umfassendes Sicherheitskonzept mit Implementierungsrichtlinien

#### #019: Fehlende Datenpersistenz-Dokumentation
**Beschreibung:** Strategie für historische Datenspeicherung nicht dokumentiert.
- **Betroffene Komponenten:** Control Layer, AI Layer
- **Auswirkung:** Keine Langzeitanalyse möglich
- **Priorität:** Hoch
- **Status:** ✅ Behoben - docs/DATA_PERSISTENCE.md erstellt
- **Lösung:** Vollständige Datenpersistenz-Strategie mit TimescaleDB

#### #020: Fehlende Containerisierungs-Dokumentation
**Beschreibung:** Docker und Container-Deployment nicht dokumentiert.
- **Betroffene Komponenten:** Alle Ebenen
- **Auswirkung:** Schwierige Produktionsbereitstellung
- **Priorität:** Hoch
- **Status:** ✅ Behoben - docs/CONTAINERIZATION.md erstellt
- **Lösung:** Umfassende Containerisierungs-Anleitung mit Dockerfiles und docker-compose

#### #021: Fehlende Monitoring-Dokumentation
**Beschreibung:** Monitoring und Observability Stack nicht dokumentiert.
- **Betroffene Komponenten:** Alle Ebenen
- **Auswirkung:** Keine System-Überwachung in Produktion
- **Priorität:** Hoch
- **Status:** ✅ Behoben - docs/MONITORING.md erstellt
- **Lösung:** Vollständige Monitoring-Stack-Dokumentation mit Prometheus, Loki, Grafana

## Kleinere Probleme

### Code-Qualität

#### #008: Einige Python-Module haben keine Type Hints
**Beschreibung:** Nicht alle Funktionen haben vollständige Type-Annotations.
- **Betroffene Komponenten:** Python Control Layer, Python AI Layer
- **Auswirkung:** Schlechtere IDE-Unterstützung, schwerer zu wartender Code
- **Priorität:** Niedrig
- **Vorgeschlagene Lösung:** Schrittweise Type Hints hinzufügen, mypy für Type-Checking nutzen

#### ~~#009: Magic Numbers in Code~~ ✅ BEHOBEN
**Beschreibung:** Einige Threshold-Werte sind direkt im Code als Zahlen geschrieben (z.B. Temperatur-Limits, Strom-Schwellenwerte).
- **Betroffene Komponenten:** Python AI Layer (anomaly_detector.py, wear_predictor.py, optimizer.py)
- **Auswirkung:** Schwer zu verstehen und anzupassen
- **Priorität:** Niedrig
- **Status:** ✅ Behoben in Commit 5dafac9
- **Lösung:** Alle magic numbers als benannte Konstanten extrahiert
  - anomaly_detector.py: 12 Konstanten für Schwellenwerte
  - wear_predictor.py: 17 Konstanten für Verschleiß-Berechnungen
  - optimizer.py: 18 Konstanten für Optimierungs-Empfehlungen
  - Alle Konstanten mit beschreibenden Namen und Kommentaren

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
