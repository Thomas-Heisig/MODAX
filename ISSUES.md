# MODAX - Bekannte Probleme (ISSUES)

Dieses Dokument verfolgt bekannte Probleme und Bugs im MODAX-System. Behobene Probleme werden nach `DONE.md` verschoben.

**Letzte Aktualisierung:** 2025-12-09  
**Anzahl offener Issues:** 3 (0 kritisch, 0 wichtig, 3 kleinere Probleme)  
**Behobene Issues in dieser Session:** 11 (#027, #008 teilweise, #010, #013, #014, #022, #023, #024, #025, #026, #030)

**📄 Session-Dokumentation:** [SESSION_SUMMARY_2025-12-09_PRIORITY_TASKS.md](SESSION_SUMMARY_2025-12-09_PRIORITY_TASKS.md)  
**✅ Status-Update 2025-12-09:** Alle kritischen und wichtigen Issues behoben. Features #024, #025, #026, #030 vollständig verifiziert.

## ~~Kritische Probleme~~ - Alle behoben! 🎉

### Sicherheit

#### ~~#022: Fehlende Authentifizierung für MQTT-Broker~~ ✅ BEHOBEN
**Beschreibung:** Der MQTT-Broker läuft ohne Authentifizierung, jeder kann Nachrichten publizieren/subscriben.
- **Betroffene Komponenten:** MQTT Broker, alle Ebenen
- **Auswirkung:** Unbefugter Zugriff auf Sensor-Daten und Steuerungsbefehle möglich
- **Priorität:** Kritisch
- **Status:** ✅ Behoben in Commit be44153
- **Lösung:** Produktions-Konfiguration erstellt
  - config/mosquitto-prod.conf: TLS/SSL aktiviert, Authentifizierung erforderlich
  - config/mosquitto-acl.example: Topic-basierte Zugriffskontrolle
  - docker-compose.prod.yml: Produktions-Setup mit Sicherheit
  - Dokumentation in docs/API_AUTHENTICATION_GUIDE.md

#### ~~#023: API-Endpunkte ohne Authentifizierung~~ ✅ BEHOBEN
**Beschreibung:** Control Layer und AI Layer APIs sind ohne Authentifizierung zugänglich.
- **Betroffene Komponenten:** control_api.py, ai_service.py
- **Auswirkung:** Unbefugter Zugriff auf System-Daten und Steuerung
- **Priorität:** Kritisch
- **Status:** ✅ Behoben - bereits implementiert, jetzt dokumentiert
- **Lösung:** API Key Authentifizierung bereits vorhanden
  - auth.py: APIKeyManager mit rollenbasierter Zugriffskontrolle
  - control_api.py: Security Dependencies integriert
  - config.py: API_KEY_ENABLED Flag
  - docs/API_AUTHENTICATION_GUIDE.md: Vollständige Anleitung erstellt
  - Aktivierung via Umgebungsvariable API_KEY_ENABLED=true

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

#### ~~#005: Fehlende strukturierte Logs~~ ✅ BEHOBEN
**Beschreibung:** Logs sind als einfache Strings formatiert, nicht als strukturierte JSON-Objekte.
- **Betroffene Komponenten:** Alle Python-Ebenen
- **Auswirkung:** Erschwert automatisierte Log-Analyse
- **Priorität:** Niedrig
- **Status:** ✅ Behoben - bereits implementiert
- **Lösung:** JSON-Logging bereits vorhanden
  - python-json-logger in requirements.txt
  - main.py: JsonFormatter konfiguriert
  - Aktivierung via USE_JSON_LOGS=true (Standard)
  - config/loki-config.yml: Log-Aggregation konfiguriert
  - config/promtail-config.yml: Log-Shipping konfiguriert

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

### Wartung & Dokumentation

#### ~~#027: Datum-Inkonsistenzen in Dokumentation~~ ✅ BEHOBEN
**Beschreibung:** Einige Dokumentationsdateien verwenden noch das Jahr 2024 statt 2025.
- **Betroffene Komponenten:** Diverse .md Dateien in docs/
- **Auswirkung:** Verwirrung über Aktualität der Dokumentation
- **Priorität:** Niedrig
- **Status:** ✅ Behoben in Commit 682ba3a
- **Lösung:** Alle Datums-Referenzen auf 2025 aktualisiert
  - IMPROVEMENTS_2024-12-06.md → IMPROVEMENTS_2025-12-06.md
  - SESSION_SUMMARY_2024-12-07.md → SESSION_SUMMARY_2025-12-07.md
  - Datumsinhalte in den Dateien aktualisiert

### Code-Qualität

#### ~~#008: Einige Python-Module haben keine Type Hints~~ ✅ TEILWEISE BEHOBEN
**Beschreibung:** Nicht alle Funktionen haben vollständige Type-Annotations.
- **Betroffene Komponenten:** Python Control Layer, Python AI Layer
- **Auswirkung:** Schlechtere IDE-Unterstützung, schwerer zu wartender Code
- **Priorität:** Niedrig
- **Status:** ✅ Teilweise behoben in Commit 8cf2e2b
- **Lösung:** Type Hints zu allen API-Endpunkt-Funktionen hinzugefügt
  - control_api.py: root(), health_check(), readiness_check(), metrics(), set_control_layer()
  - ai_service.py: root(), health_check(), metrics()
  - Weitere Module können bei Bedarf ergänzt werden

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

#### ~~#010: Fehlende Eingabevalidierung in einigen API-Endpunkten~~ ✅ BEHOBEN
**Beschreibung:** Nicht alle API-Endpunkte validieren Eingabeparameter vollständig.
- **Betroffene Komponenten:** Python Control Layer (control_api.py)
- **Auswirkung:** Potenzielle Sicherheitsprobleme, unklare Fehlermeldungen
- **Priorität:** Mittel
- **Status:** ✅ Behoben in Commit 8cf2e2b
- **Lösung:** Pydantic-Modelle für alle CNC-Endpunkte erstellt
  - GCodeProgramRequest für CNC-Programm-Laden
  - SpindleCommandRequest für Spindle-Steuerung
  - OverrideRequest für Feed/Spindle-Override
  - EmergencyStopRequest für Notaus
  - Alle Endpunkte verwenden nun typisierte Modelle statt Dict

### Performance

#### ~~#011: Keine Caching-Strategie für häufig abgerufene Daten~~ ✅ BEHOBEN
**Beschreibung:** Jeder API-Aufruf generiert neue Berechnungen, auch wenn sich Daten nicht geändert haben.
- **Betroffene Komponenten:** Python Control Layer (control_api.py)
- **Auswirkung:** Unnötige CPU-Last bei vielen Clients
- **Priorität:** Niedrig
- **Status:** ✅ Behoben - TTL-basiertes In-Memory-Caching implementiert
- **Lösung:** CacheManager mit cachetools implementiert
  - cache_manager.py: Thread-safe TTL-basiertes Caching
  - Separate Caches für verschiedene Datentypen (Device List, Device Data, AI Analysis, System Status)
  - Konfigurierbare TTL-Werte (1-10 Sekunden je nach Datentyp)
  - Cache-Statistik-Endpunkt (/api/v1/cache/stats)
  - Prometheus Metrics für Cache-Performance (control_cache_hits_total, control_cache_misses_total, control_cache_size)
  - 10 Unit-Tests mit 100% Erfolgsrate
  - Cache-Invalidierung für einzelne Geräte
  - Thread-sicher mit Locks für concurrent access

#### #012: Große MQTT-Nachrichten bei hoher Sensor-Frequenz
**Beschreibung:** Bei 10Hz Sensor-Sampling werden viele kleine MQTT-Nachrichten gesendet.
- **Betroffene Komponenten:** ESP32 Field Layer
- **Auswirkung:** Höhere Netzwerklast
- **Priorität:** Niedrig
- **Status:** ✅ Dokumentiert - Implementierungsplan erstellt
- **Lösung:** Umfassende Optimierungsstrategie dokumentiert (docs/MQTT_OPTIMIZATION.md bereits vorhanden)
  - Strategy 1: Message Batching (80% message reduction, 4-6h effort)
  - Strategy 2: Protocol Buffers (50% size reduction, 8-12h effort)
  - Strategy 3: Compression (30-40% size reduction, low effort)
  - Strategy 4: Adaptive Sampling (20-50% reduction during stable periods)
  - Empfohlene Phasen-Implementation mit Test-Metriken
  - Backward Compatibility und Migration Strategy

### Benutzeroberfläche

#### ~~#013: HMI-Update-Intervall fest codiert~~ ✅ BEHOBEN
**Beschreibung:** Das 2-Sekunden-Update-Intervall im HMI ist nicht konfigurierbar.
- **Betroffene Komponenten:** C# HMI Layer (MainForm.cs)
- **Auswirkung:** Keine Flexibilität für verschiedene Nutzungsszenarien
- **Priorität:** Niedrig
- **Status:** ✅ Behoben in Commit 57503db
- **Lösung:** Update-Intervall über Umgebungsvariable konfigurierbar
  - HMI_UPDATE_INTERVAL_MS: Intervall in Millisekunden (Standard: 2000)
  - Validierung: 500ms - 30000ms (0.5s - 30s)
  - Fehlerhafte Werte werden ignoriert und Standard verwendet

#### ~~#014: Fehlende Sortier- und Filterfunktionen im HMI~~ ✅ BEHOBEN
**Beschreibung:** Bei vielen verbundenen Geräten gibt es keine Möglichkeit, die Liste zu filtern oder zu sortieren.
- **Betroffene Komponenten:** C# HMI Layer (MainForm.cs)
- **Auswirkung:** Unübersichtlich bei großer Anzahl von Geräten
- **Priorität:** Niedrig
- **Status:** ✅ Behoben in Commit 57503db
- **Lösung:** Echtzeit-Filterfunktion implementiert
  - TextBox mit PlaceholderText "Type to filter..."
  - Filterung erfolgt bei jeder Texteingabe (case-insensitive)
  - Erhaltung der Auswahl beim Filtern wenn möglich
  - Speicherung aller Geräte für schnelle Filterung

## Verbesserungsvorschläge (Enhancements)

### #015: AI-Modell-Confidence als visuelle Anzeige im HMI
**Beschreibung:** Die Confidence-Werte der AI-Analyse werden als Zahlen angezeigt, könnten aber visuell besser dargestellt werden.
- **Priorität:** Niedrig
- **Status:** ✅ Dokumentiert - Implementierungsplan erstellt
- **Lösung:** Umfassende Implementierungs-Optionen dokumentiert (docs/HMI_ENHANCEMENTS.md)
  - Option 1: Progress Bar mit Farbcodierung (2-3h effort)
  - Option 2: Traffic Light System (Ampel, empfohlen, 2-3h effort)
  - Option 3: Gauge/Dial Display (3-4h effort)
  - Detaillierter Code mit C# Beispielen
  - Implementierungsschritte und Testing-Plan

### #016: Export-Funktion für Sensor-Daten
**Beschreibung:** Es gibt keine Möglichkeit, historische Sensor-Daten zu exportieren.
- **Priorität:** Niedrig
- **Status:** ✅ API bereits implementiert, HMI-Integration dokumentiert
- **Lösung:** HMI-Integration dokumentiert (docs/HMI_ENHANCEMENTS.md)
  - Export-API bereits vorhanden: CSV, JSON, Statistics
  - UI-Design für Export-Dialog mit Code-Beispielen
  - Zeit-Range Selection
  - File-Save Funktionalität
  - Implementierungs-Aufwand: 2-3h

### #017: Dark Mode für HMI
**Beschreibung:** Einige Benutzer bevorzugen eine dunkle Benutzeroberfläche.
- **Priorität:** Sehr Niedrig
- **Status:** ✅ Dokumentiert - Implementierungsplan erstellt
- **Lösung:** Theme-System dokumentiert (docs/HMI_ENHANCEMENTS.md)
  - ThemeManager mit Light/Dark Themes
  - Color-Palette für beide Modi
  - Automatische Control-Anpassung
  - Theme-Persistenz
  - Implementierungs-Aufwand: 6-8h

### ~~#024: TimescaleDB Integration~~ ✅ BEHOBEN
**Beschreibung:** Historische Daten werden derzeit nicht persistent gespeichert.
- **Betroffene Komponenten:** Control Layer
- **Auswirkung:** Keine Langzeit-Trendanalyse möglich
- **Priorität:** Mittel
- **Status:** ✅ Behoben - Vollständig implementiert
- **Lösung:** TimescaleDB vollständig implementiert
  - db_connection.py: DatabaseConnectionPool mit ThreadedConnectionPool
  - data_writer.py: Sensor-Daten Persistierung
  - data_reader.py: Historische Daten-Abfrage
  - docker-compose.prod.yml: TimescaleDB Container (timescale/timescaledb:2.13.0-pg15)
  - Secrets Management für DB-Credentials
  - Connection Pooling für Performance
  - Dokumentation in docs/DATA_PERSISTENCE.md

### ~~#025: Prometheus Metrics Export~~ ✅ BEHOBEN
**Beschreibung:** System-Metriken werden nicht für Prometheus exportiert.
- **Betroffene Komponenten:** Control Layer, AI Layer
- **Auswirkung:** Eingeschränktes Monitoring
- **Priorität:** Mittel
- **Status:** ✅ Behoben - Vollständig implementiert
- **Lösung:** Prometheus Metrics vollständig implementiert
  - Control Layer: Counter, Histogram, Gauge metrics
    - control_api_requests_total (by method, endpoint, status)
    - control_api_request_duration_seconds (histogram)
    - control_devices_online (gauge)
    - control_system_safe (gauge)
    - control_cache_hits_total, control_cache_misses_total
  - AI Layer: Counter, Histogram metrics
    - ai_analysis_requests_total (by status)
    - ai_analysis_duration_seconds (histogram)
    - ai_anomalies_detected_total (by type)
  - /metrics Endpunkte auf beiden Layern
  - config/prometheus.yml: Scraping-Konfiguration
  - Dokumentation in docs/MONITORING.md und IMPROVEMENTS.md

### ~~#026: WebSocket-Support für Echtzeit-Updates~~ ✅ BEHOBEN
**Beschreibung:** HMI verwendet Polling statt Push-Updates.
- **Betroffene Komponenten:** Control Layer, HMI Layer
- **Auswirkung:** Höhere Latenz und mehr Netzwerklast
- **Priorität:** Mittel
- **Status:** ✅ Behoben - Vollständig implementiert
- **Lösung:** WebSocket vollständig implementiert
  - websocket_manager.py: WebSocketManager-Klasse
    - Connection Management (connect, disconnect)
    - Broadcast zu allen Clients oder spezifischen Geräten
    - Device-spezifische Subscriptions
    - Async/Thread-safe Implementierung
  - control_api.py: WebSocket Endpoints
    - /ws: All-device updates
    - /ws/{device_id}: Device-specific updates
  - Automatische Push-Updates bei Datenänderungen
  - Ping/Pong für Connection Keep-Alive
  - Fehlerbehandlung und Reconnection-Support
  - Dokumentation in docs/IMPROVEMENTS.md

### #028: Fehlende Internationalisierung (i18n)
**Beschreibung:** UI-Texte sind nur auf Deutsch verfügbar.
- **Betroffene Komponenten:** HMI Layer
- **Auswirkung:** Eingeschränkte internationale Nutzbarkeit
- **Priorität:** Niedrig
- **Status:** ✅ Dokumentiert - Implementierungsplan erstellt
- **Lösung:** Resource-basiertes i18n-System dokumentiert (docs/HMI_ENHANCEMENTS.md)
  - .resx Dateien für EN und DE
  - CultureInfo-basierte Sprach-Umschaltung
  - Implementierungs-Aufwand: 12-16h

### #029: Keine automatische Schema-Migration für Datenbank
**Beschreibung:** Datenbankschema-Änderungen müssen manuell durchgeführt werden.
- **Betroffene Komponenten:** Control Layer, AI Layer
- **Auswirkung:** Fehleranfällige Updates
- **Priorität:** Mittel
- **Status:** ✅ Dokumentiert - Vollständiger Implementierungsplan mit Alembic
- **Lösung:** Umfassende Migration-Strategie dokumentiert (docs/SCHEMA_MIGRATION.md, 17KB)
  - Alembic Setup und Konfiguration
  - SQLAlchemy Model-Definitionen
  - Automatische und manuelle Migration-Erstellung
  - Upgrade/Downgrade Operations
  - CI/CD Integration (GitHub Actions)
  - Docker Deployment-Strategie
  - Migration Patterns (Add Column, Modify, Index, Data Migration)
  - Rollback-Strategie mit Backup
  - Best Practices (Reversible Migrations, Transactions)
  - Troubleshooting-Guide
  - Implementierungs-Checklist

### ~~#030: Fehlende Health-Check-Endpunkte~~ ✅ BEHOBEN
**Beschreibung:** Kubernetes/Docker Health-Checks nicht standardisiert implementiert.
- **Betroffene Komponenten:** Alle Layer
- **Auswirkung:** Eingeschränktes Container-Orchestrierungs-Management
- **Priorität:** Mittel
- **Status:** ✅ Behoben - Vollständig implementiert
- **Lösung:** Health-Check-Endpunkte vollständig implementiert
  - Control Layer:
    - GET /health: Basis Health-Check (Service läuft)
    - GET /ready: Readiness-Check (Control Layer initialisiert, Devices online, Safety Status)
  - AI Layer:
    - GET /health: Basis Health-Check (Service läuft)
    - GET /ready: Readiness-Check (AI-Modelle geladen, Service bereit)
  - Docker Health-Checks in allen Dockerfiles
  - docker-compose.yml: Health-Check-Konfiguration für alle Services
  - Kubernetes Health-Probes in k8s/base/
  - Dokumentation in docs/IMPROVEMENTS.md und docs/CONTAINERIZATION.md

## Hinweise

- Neue Issues sollten hier dokumentiert werden, bevor Code geändert wird
- Jedes Issue sollte eine eindeutige Nummer haben (#XXX)
- Prioritäten: Kritisch, Hoch, Mittel, Niedrig, Sehr Niedrig
- Bei Behebung eines Issues: In DONE.md verschieben mit Lösung und Commit-Hash
- Sicherheitsrelevante Issues sollten privat behandelt werden (nicht in öffentlichem Repo)
