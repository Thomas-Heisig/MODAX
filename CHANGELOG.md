# MODAX - Änderungsprotokoll (CHANGELOG)

Alle bemerkenswerten Änderungen an diesem Projekt werden in dieser Datei dokumentiert.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.0.0/),
und dieses Projekt folgt [Semantic Versioning](https://semver.org/lang/de/).

## [Unreleased]

### Hinzugefügt - Dokumentationskonsolidierung & Feature-Verifizierung (2025-12-09)

- **📄 SESSION_SUMMARY_2025-12-09_PRIORITY_TASKS.md** - Umfassende Session-Dokumentation
  - Vollständige Verifizierung aller implementierten Features
  - Status-Update für 20 Prioritätsaufgaben aus TODO.md und ISSUES.md
  - Dokumentations-Konsolidierung abgeschlossen
  - 18/20 Aufgaben erfolgreich abgeschlossen (90%)
  - Security Audit PASSED - Zero Vulnerabilities
  - Feature-Status-Übersicht (Implementiert vs. Dokumentiert)
  - Empfehlungen für nächste Schritte
  
- **✅ Feature-Verifizierung Abgeschlossen:**
  - WebSocket Support (#026) - Vollständig implementiert und getestet
  - TimescaleDB Integration (#024) - Vollständig implementiert und getestet
  - Prometheus Metrics (#025) - Vollständig implementiert und getestet
  - Health-Check Endpoints (#030) - Vollständig implementiert und getestet
  
- **📚 Dokumentations-Status Verifiziert:**
  - Docstring Coverage: 95-98% (Production-ready)
  - Type Hints: Vollständig für alle API-Endpunkte
  - 40+ Dokumentationsdateien (~800KB)
  - QUICK_REFERENCE.md vorhanden und aktuell
  - Alle Issues #15, #17, #28, #29 als dokumentiert markiert
  
- **🧪 Test-Status Verifiziert:**
  - 126+ Tests (100% pass rate)
  - test_performance.py (8 Suites) - Alle Performance-Ziele erreicht
  - test_load.py (7 Suites) - Skalierbarkeit bestätigt
  - test_end_to_end.py (11 Tests) - Vollständige Integration getestet
  - WebSocket Integration Tests (11 Tests)
  
### Dokumentiert - Geplante Features für zukünftige Phasen

- **📋 OPC UA Server (#122)** - Vollständig dokumentiert in docs/OPC_UA_INTEGRATION.md
  - Implementierungsplan vorhanden
  - Server-Architektur definiert
  - Sicherheitsmodell dokumentiert
  - Geplant für Phase 2
  
- **📋 Advanced HMI Visualizations (#55)** - Dokumentiert in docs/HMI_ENHANCEMENTS.md
  - Visual AI Confidence Display (#015)
  - Chart-Integration definiert
  - Code-Beispiele verfügbar
  - Enhancement Backlog
  
- **📋 Offline Mode (#91)** - Teilweise dokumentiert
  - Daten-Persistenz-Infrastruktur vorhanden
  - Export-Funktionalität implementiert
  - Sync-Logik ausstehend
  - Geplant für Phase 3

### Hinzugefügt - Umfassende Entwicklerdokumentation (2025-12-09)
- **📚 CONTRIBUTING.md** - Vollständige Contribution Guidelines
  - Code of Conduct und Entwicklungsworkflow
  - Coding Standards für Python, C# und C++
  - Type Hints und Docstring-Konventionen
  - Testing-Anforderungen (95% Coverage-Minimum)
  - Pull Request Checkliste
  - Branching-Strategie (feature/, fix/, docs/, refactor/, test/)
  - Sicherheitsrichtlinien für Safety-Critical Code
  
- **📚 docs/TROUBLESHOOTING.md** - Umfassender Troubleshooting-Guide
  - Quick Diagnostics mit System Health Check
  - Detaillierte Problemlösung für alle Komponenten:
    - Connection Issues (HMI, Control Layer, AI Layer)
    - MQTT Problems (Broker, Authentication, Connection Drops)
    - API Issues (500 Errors, Timeouts, Authentication)
    - HMI Problems (No Data, Crashes, Chart Updates)
    - ESP32 Field Layer (WiFi, Sensors, Memory)
    - Performance Issues (CPU, Memory, Database)
    - Data Issues (Missing Data, Incorrect Analysis)
    - Security Issues (Unauthorized Access, TLS)
    - Docker/Deployment Issues (Container, Network)
  - Diagnose-Befehle und Lösungsstrategien
  - Emergency Support Guidelines
  
- **📚 docs/BEST_PRACTICES.md** - Development Best Practices
  - Architecture & Design:
    - Separation of Concerns (Safety-Critical vs. AI)
    - Layered Communication Pattern
    - Scalability Considerations
  - Code Quality Standards:
    - Type Hints und Docstring Examples
    - Error Handling Patterns
    - Logging Standards (DEBUG/INFO/WARNING/ERROR/CRITICAL)
    - Configuration Management
  - Security Best Practices:
    - Authentication & Authorization
    - TLS/SSL Encryption
    - Secrets Management (Vault)
    - Input Validation mit Pydantic
  - Performance Optimization:
    - Data Aggregation mit Numpy
    - Asynchronous Operations
    - Caching Strategies
    - Database Optimization
  - Testing Strategies:
    - Unit Testing Examples
    - Integration Testing
    - Load Testing mit Locust
  - Deployment & Operations:
    - Container Best Practices
    - Docker Compose Setup
    - Environment-Specific Configuration
    - Graceful Shutdown Handling
  - Monitoring & Observability:
    - Prometheus Metrics Collection
    - Health Checks (/health, /ready)
    - Structured Logging
  - Data Management:
    - Data Retention Policies
    - Archival Strategies
    - Backup Procedures

### Hinzugefügt - Erweiterte Test-Suites (2025-12-09)
- **🧪 test_end_to_end.py erweitert** - Von 5 auf 11 umfassende Tests
  - test_complete_ai_pipeline: Komplette AI-Pipeline Integration
  - test_data_flow_with_gaps: Behandlung von Netzwerkunterbrechungen
  - test_concurrent_device_analysis: Gleichzeitige Analyse von 5 Geräten
  - test_gradual_wear_accumulation: 100 Zyklen Verschleiß-Simulation
  - test_emergency_shutdown_flow: Vollständiger Notfall-Ablauf

- **🧪 test_performance.py** - Neue Performance-Test-Suite (16KB)
  - 8 umfassende Performance-Test-Suites
  - Benchmarks für alle kritischen Operationen:
    - Data Aggregation: < 50ms avg, < 100ms P95
    - Anomaly Detection: < 10ms avg, < 20ms P95
    - Wear Prediction: < 15ms avg, < 30ms P95
    - Complete AI Pipeline: < 100ms avg, < 150ms P95
  - Concurrent Device Processing Tests (10+ Geräte/Sekunde)
  - Memory Usage Stability Tests (< 1000 Objekte Wachstum)
  - Large Data Volume Tests (> 1000 Messwerte/Sekunde)
  - Detaillierte Performance-Metriken (Average, Min, Max, P95)

- **🧪 test_load.py** - Neue Load-Test-Suite (19.5KB)
  - 7 umfassende Load- und Stress-Tests
  - Multi-Device Scenarios:
    - 10 Devices Sustained Load (10s, 10 Messwerte/s/Gerät)
    - 50 Devices Concurrent Analysis
    - Burst Load Handling (5 Bursts × 2000 Messwerte)
  - Scalability Tests:
    - Gradual Device Scaling (0-30 Geräte)
    - Sustained Operation (25 Geräte, 30 Sekunden)
  - Stress Scenarios:
    - Rapid Device Churn (20 Zyklen)
    - Extreme Data Variance Handling
  - Performance-Metriken: Throughput, Latenz, Stabilität

### Geändert
- **TODO.md** aktualisiert mit erledigten Test-Items
  - End-to-End-Tests als erweitert markiert
  - Performance-Tests als erledigt markiert
  - Load-Tests als erledigt markiert
- **docs/INDEX.md** aktualisiert mit neuen Dokumenten
  - Developer Resources Section hinzugefügt
  - CONTRIBUTING.md, TROUBLESHOOTING.md, BEST_PRACTICES.md verlinkt
  - Quick Reference Card erweitert
  - "For Developers" Section aktualisiert
  - Last Updated auf 2025-12-09

## [0.4.0] - 2025-12-07

### Hinzugefügt - Extended G-Code Support & Interpreter

- **🔧 Erweiterte G-Code-Unterstützung (150+ Codes):**
  - **Advanced Interpolation:** G05 (NURBS), G05.1 (Look-Ahead), G07.1/G107 (Zylindrisch), G12.1/G13.1 (Polar)
  - **Threading:** G33 (konstante Steigung), G76 (Threading-Zyklus), G84.2/G84.3 (Rechts-/Links-Tappen)
  - **Workspace:** G22/G23 (Arbeitsbereichsbegrenzung), G25/G26 (Spindel-Schwankungserkennung)
  - **Probing:** G31 (Skip/Probe), G36 (Auto-Offset), G37 (Auto-Länge), G38.2-G38.5 (erweitert)
  - **Advanced Cycles:** G73 (High-Speed-Peck), G74 (Links-Tappen), G34/G35 (Lochkreis)
  - **Coordinate Systems:** G54.1 Pxx (erweiterte WCS P1-P300), G98/G99 (Rückkehr-Modi)

- **🔧 Erweiterte M-Code-Unterstützung:**
  - **Spindle:** M19 (Orientierung), M21/M22 (Getriebe-Schaltung), M29 (Starr-Tappen)
  - **Coolant:** M50/M51 (Hochdruck), M88 (Through-Spindle), M89 (Through-Tool)
  - **Feed Override:** M36/M37 (Bereichsbegrenzung)
  - **User Macros:** M100-M199 (frei konfigurierbar)
  - **Pallet Control:** M200-M203 (Mazak Palettensteuerung)

- **🤖 Makro-Unterstützung:**
  - Fanuc Macro B: G65 (Makro-Aufruf), G66/G67 (Modal)
  - O-Codes: Programm-/Makro-Nummern (O1000-O9999)
  - Variablen: #1-#999 (Common Variables)
  - Parameter-Übergabe an Makros

- **🔀 Kontrollfluss & Interpreter:**
  - **GOTO:** Unbedingter Sprung zu Labels oder N-Nummern
  - **GOSUB/RETURN:** Unterprogramm-Aufrufe mit Call-Stack
  - **Labels:** Mit oder ohne Doppelpunkt (:START, LOOP, N100)
  - **Verschachtelte Aufrufe:** Mehrere GOSUB-Ebenen unterstützt
  - **Infinite Loop Protection:** Max. Ausführungszähler

- **🏭 Herstellerspezifische Unterstützung:**
  - **Siemens Sinumerik:** G05, G107, CYCLE-Befehle
  - **Heidenhain TNC:** G05.1, CYCL DEF (vorbereitet)
  - **Fanuc Macro B:** G54.1, G65/G66/G67, #-Variablen
  - **Okuma OSP:** VC-Variable (vorbereitet), CALL OOxx (vorbereitet)
  - **Mazak Mazatrol:** M200+ Serie (Palettensteuerung)

- **📝 Kommentar-Unterstützung:**
  - Beide Stile: Parentheses `(comment)` und Semicolon `; comment`
  - Kommentare werden geparst und gespeichert

- **📊 F und S Code Handling:**
  - `has_spindle_speed()`, `get_spindle_speed()` - S-Parameter
  - `has_feed_rate()`, `get_feed_rate()` - F-Parameter
  - Vollständige Integration in Parser

- **✅ Umfangreiche Tests:**
  - `test_gcode_extended.py`: 18 Tests für erweiterte Codes
  - `test_gcode_interpreter.py`: 17 Tests für Interpreter
  - 100% Code-Abdeckung für neue Features

- **📚 Dokumentation:**
  - `docs/EXTENDED_GCODE_SUPPORT.md`: Vollständige Referenz (13KB)
  - API-Dokumentation für Parser und Interpreter
  - Beispiele für alle Features
  - Sicherheitshinweise für Produktionseinsatz

### Geändert
- **gcode_parser.py:** Erweitert um 60+ neue G-Codes, 20+ M-Codes
- **README.md:** Aktualisiert mit neuen Features (v0.4.0)
- **docs/INDEX.md:** Neue Dokumentation verlinkt

### Neue Dateien
- `python-control-layer/gcode_interpreter.py` (273 Zeilen)
- `python-control-layer/test_gcode_extended.py` (312 Zeilen)
- `python-control-layer/test_gcode_interpreter.py` (315 Zeilen)
- `docs/EXTENDED_GCODE_SUPPORT.md` (13KB)

## [0.3.0] - 2025-12-07

### Hinzugefügt - Industry 4.0 Advanced Features Documentation
- **📚 Umfassende Industry 4.0 Dokumentation (`docs/ADVANCED_CNC_INDUSTRY_4_0.md`):**
  - 1.672 Zeilen detaillierte Dokumentation für moderne CNC-Funktionen
  - Advanced Communication Protocols:
    - OPC UA (✅ dokumentiert und bereit)
    - MQTT (✅ implementiert und operational)
    - EtherCAT, PROFINET, SERCOS III (Roadmap)
    - MTConnect (Roadmap)
    - Hersteller-spezifische Ökosysteme (Siemens, Heidenhain, Okuma, Mazak)
  
  - Intelligente Prozesssteuerung:
    - Adaptive Feed Control mit Code-Beispielen
    - In-Process Gauging mit Touch-Probe
    - Vibration Monitoring & Chatter Detection (⭐ hohe Priorität)
    - Energy Consumption Monitoring
    - Automated Job Setup (RFID/Barcode)
    - Predictive Maintenance Analytics (⭐ sehr hohe Priorität)
    - Lights-Out Production Capabilities
  
  - Zukunftsfähige Integration:
    - AI-Powered Parameter Optimization
    - Digital Twin Synchronization
    - Peer-to-Peer Machine Learning (Federated Learning)
    - Augmented Reality Overlays
    - Cloud-Native, Customizable HMIs
    - Voice & Gesture Control
  
  - Implementation Roadmap:
    - Phase 1 (Monate 1-3): Foundation Enhancement
    - Phase 2 (Monate 4-6): Intelligence & Automation
    - Phase 3 (Monate 7-12): Advanced Integration
  
  - ROI-Analyse für alle Features
  - Best Practices und Startpunkte
  - Sicherheitsüberlegungen und Netzwerkarchitektur

- **📝 Session Summary (`docs/SESSION_SUMMARY_2024-12-07_INDUSTRY_4_0.md`):**
  - Vollständige Dokumentation aller Änderungen
  - Implementierungsstrategien
  - Prioritäten und nächste Schritte

### Geändert
- **README.md:**
  - Version auf 0.3.0 aktualisiert (Industry 4.0 Roadmap)
  - Industry 4.0 Roadmap Sektion hinzugefügt
  - Zukünftige Erweiterungen in 4 Phasen strukturiert
  - Referenzen zur neuen Advanced-Dokumentation

- **docs/CNC_FEATURES.md:**
  - Referenz zu ADVANCED_CNC_INDUSTRY_4_0.md hinzugefügt
  - Industry 4.0 Advanced Features Sektion ergänzt
  - Klare Wegweiser zur umfassenden Dokumentation

- **docs/INDEX.md:**
  - ADVANCED_CNC_INDUSTRY_4_0.md in Core System Documentation aufgenommen
  - Als ⭐ **NEW** markiert
  - Zusammenfassung der behandelten Themen

### Technische Details
- Alle Protokollbeschreibungen basieren auf Industriestandards
- 22 Python-Code-Beispiele mit praktischen Implementierungen
- Alle internen Links verifiziert und funktionsfähig
- Seamlose Integration mit bestehender MODAX-Dokumentation
- OT/IT-Netzwerktrennung dokumentiert
- Sicherheits-Best-Practices für Industry 4.0

## [0.2.0] - 2025-12-07

### Hinzugefügt - Umfassende CNC-Funktionalität
- **🏭 CNC-Controller (`cnc_controller.py`):**
  - Vollständige Maschinenzustandsverwaltung (IDLE, RUNNING, PAUSED, STOPPED, ERROR, EMERGENCY)
  - 8 Betriebsmodi (AUTO, MANUAL, MDI, REFERENCE, HANDWHEEL, SINGLE_STEP, DRY_RUN, SIMULATION)
  - Positionsverfolgung (Maschinen-, Arbeits- und Restweg-Koordinaten)
  - Spindelsteuerung mit Drehzahl, Richtung und Override (50-150%)
  - Vorschubsteuerung mit Override (0-150%)
  - Kühlmittelsteuerung (OFF, FLOOD, MIST, BOTH)
  - Not-Aus-Funktionalität
  - Software-Endlagen für alle Achsen
  - Fehler- und Warnungsverfolgung

- **📝 G-Code-Parser (`gcode_parser.py`):**
  - Vollständiger ISO 6983 (DIN 66025) Standard-Parser
  - 100+ G-Codes unterstützt (G00-G99, erweiterte Codes)
  - 15+ M-Codes (M00-M99)
  - Bewegungsbefehle: G00/G01 (Linear), G02/G03 (Zirkular)
  - Ebenenauswahl: G17 (XY), G18 (ZX), G19 (YZ)
  - Einheiten: G20 (Zoll), G21 (Metrisch)
  - Positionierungsmodi: G90 (Absolut), G91 (Inkrementell)
  - Werkzeugkompensationen: G40-G42 (Radius), G43-G49 (Länge)
  - 9 Arbeitskoordinatensysteme (G54-G59.3)
  - Koordinatentransformationen: G68/G69 (Rotation), G50/G51 (Skalierung), G92 (Offset)
  - Bohrzyklen: G81-G89 (Bohren, Tappen, Senken)
  - Fräszyklen: G12/G13 (Kreistasche)
  - Kommentar- und Zeilennummern-Parsing
  - Befehlsvalidierung und Fehlerprüfung

- **🎯 Motion Controller (`motion_controller.py`):**
  - Lineare Interpolation (G01) mit Vorschubsteuerung
  - Zirkuläre Interpolation (G02/G03) mit IJK- und R-Format
  - Helikale Interpolation (Spirale mit Z-Bewegung)
  - Bahnoptimierung mit Look-Ahead (100 Blöcke)
  - Geschwindigkeitsplanung mit Eckenabrundung
  - S-Kurven-Beschleunigung
  - Konfigurierbare Bewegungsgrenzen
  - Max. Vorschub: 15.000 mm/min
  - Max. Eilgang: 30.000 mm/min
  - Max. Beschleunigung: 5.000 mm/s²
  - Max. Ruck: 50.000 mm/s³

- **🔧 Tool Manager (`tool_manager.py`):**
  - Werkzeugtabellen-Verwaltung (bis zu 999 Werkzeuge)
  - 24-Platz-Werkzeugmagazin (konfigurierbar)
  - Automatischer Werkzeugwechsel (M06)
  - Werkzeug-Vorauswahl
  - Werkzeuglängenkompensation (G43/G44/G49)
  - Werkzeugradiuskompensation (G40/G41/G42)
  - Verschleißverfolgung und Lebensdauerverwaltung
  - Werkzeugbrucherkennung
  - Automatische Werkzeugmessung
  - Detaillierte Werkzeugeigenschaften (Durchmesser, Länge, Schneiden, Material, Beschichtung)

- **📐 Coordinate System Manager (`coordinate_system.py`):**
  - 9 Arbeitskoordinatensysteme (G54-G59, G59.1-G59.3)
  - Maschinenkoordinatensystem (G53)
  - Lokales Koordinatensystem (G52)
  - G92 Koordinatenversatz
  - Koordinatenrotation (G68/G69) mit beliebigem Winkel
  - Koordinatenskalierung (G50/G51) pro Achse
  - Koordinatenspiegelung
  - Polarkoordinaten (G15/G16)
  - Koordinatenkonvertierung (Maschine ↔ Arbeit)
  - Transformationsstatus-Überwachung

- **⚙️ CNC Cycles (`cnc_cycles.py`):**
  - **Bohrzyklen:**
    - G81: Einfaches Bohren
    - G82: Bohren mit Verweilzeit
    - G83: Tiefbohren (Peck Drilling)
    - G84: Gewindebohren (synchronisiert mit Spindel)
    - G85: Ausreiben
    - G86: Ausreiben mit Spindelstopp
  - **Fräszyklen:**
    - G12/G13: Kreistaschenfräsen (CW/CCW)
    - G26: Rechtecktaschenfräsen
  - Konfigurierbare Zyklus-Parameter
  - Automatische Bewegungsgenerierung

- **🔗 CNC Integration (`cnc_integration.py`):**
  - Vereint alle CNC-Komponenten
  - G-Code-Programm-Laden und -Parsing
  - Befehlsausführung
  - Statusüberwachung
  - Demo-Werkzeug-Initialisierung
  - Umfassende Zustandsabfrage

- **🌐 CNC REST API-Endpunkte (in `control_api.py`):**
  - `GET /api/v1/cnc/status` - Umfassender Maschinenstatus
  - `POST /api/v1/cnc/program/load` - G-Code-Programm laden
  - `POST /api/v1/cnc/mode/{mode}` - Betriebsmodus setzen
  - `POST /api/v1/cnc/spindle` - Spindelsteuerung
  - `POST /api/v1/cnc/tool/change/{tool_number}` - Werkzeugwechsel
  - `GET /api/v1/cnc/tools` - Werkzeugliste abrufen
  - `GET /api/v1/cnc/magazine` - Magazinstatus
  - `POST /api/v1/cnc/coordinate-system/{system}` - Koordinatensystem setzen
  - `POST /api/v1/cnc/override/feed` - Vorschub-Override
  - `POST /api/v1/cnc/override/spindle` - Spindel-Override
  - `POST /api/v1/cnc/emergency-stop` - Not-Aus
  - `GET /api/v1/cnc/gcode/parse` - G-Code parsen (ohne Ausführung)

- **✅ Umfassende Unit-Tests:**
  - `test_cnc_controller.py` - 11 Tests für CNC-Controller
  - `test_gcode_parser.py` - 14 Tests für G-Code-Parser
  - Alle Tests erfolgreich (25+ neue Tests)
  - Test-Coverage beibehalten bei 96-97%

- **📚 Dokumentation:**
  - **docs/CNC_FEATURES.md** - Vollständige CNC-Funktionsdokumentation
    - Architekturübersicht
    - Komponentenbeschreibungen
    - G-Code-Referenz (100+ Codes)
    - API-Endpunkt-Dokumentation
    - Sicherheitsfunktionen
    - Performance-Spezifikationen
    - Beispielprogramme
    - Integration mit MODAX
  - README.md aktualisiert mit CNC-Features
  - docs/INDEX.md aktualisiert

### Geändert
- Versionsnummer auf 0.2.0 erhöht
- Test-Anzahl von 98 auf 123+ erhöht
- control_api.py erweitert um CNC-Endpunkte
- README.md Hauptfeatures um CNC-Abschnitt erweitert

## [0.1.0] - 2024-12-06

### Hinzugefügt
- **README.md erweitert:** Detaillierte Main-Analyse mit Entry-Points und Implementierungsdetails
- **TODO.md aktualisiert:** Realistischer Status mit 98 Tests und 96-97% Coverage
- **ISSUES.md erweitert:** Neue kritische Sicherheits-Issues (#022, #023) und Enhancements (#024-#026)
- **Dokumentation synchronisiert:** Alle Docs spiegeln aktuelle Implementierung wider
- TODO.md, ISSUES.md, DONE.md und CHANGELOG.md für strukturiertes Projekt-Management
- Umfassende API-Dokumentation (docs/API.md)
- Vollständige Konfigurationsreferenz (docs/CONFIGURATION.md)
- Erweiterte Docstrings für main.py Module
- **docs/ERROR_HANDLING.md**: Umfassender Fehlerbehandlungs-Leitfaden
- **docs/LOGGING_STANDARDS.md**: Logging-Standards und Konventionen
- **docs/SECURITY.md**: Vollständiges Sicherheitskonzept
  - Transport-Sicherheit (TLS/SSL für MQTT und HTTPS)
  - Authentifizierung & Autorisierung (MQTT, API, RBAC)
  - Audit-Logging für Sicherheitsereignisse
  - Secrets Management (HashiCorp Vault)
  - Netzwerk-Segmentierung (OT/IT-Trennung)
  - Vulnerability Management und Incident Response
  - Compliance (IEC 62443, NIST SP 800-82)
- **docs/DATA_PERSISTENCE.md**: Datenpersistenz-Strategie
  - TimescaleDB als empfohlene Zeit-Reihen-Datenbank
  - Vollständiges Datenbankschema mit Hypertables
  - Continuous Aggregates für Performance
  - Datei-Retention-Policies (7 Tage bis 10 Jahre)
  - Python-Integration mit Connection Pooling
  - Backup & Recovery mit PITR
- **docs/CONTAINERIZATION.md**: Containerisierungs-Guide
  - Dockerfiles für alle Komponenten (MQTT, DB, Control, AI)
  - docker-compose.yml für Entwicklung und Produktion
  - Build und Deployment-Skripte
  - Zero-Downtime Updates
  - CI/CD Integration (GitHub Actions)
  - Security Best Practices für Container
- **docs/MONITORING.md**: Monitoring-Stack-Dokumentation
  - Prometheus für Metrics Collection
  - Loki für Log Aggregation
  - Grafana für Visualisierung und Dashboards
  - AlertManager für Alerting
  - OpenTelemetry für Distributed Tracing
  - Vollständige Konfigurationsbeispiele
  - Custom Metrics für MODAX-Komponenten
- **MQTT Reconnection**: Automatische Wiederverbindung mit exponentieller Backoff-Strategie
- **Konfigurierbare API Timeouts**: AI_LAYER_URL und AI_LAYER_TIMEOUT Umgebungsvariablen

### Geändert
- README.md aktualisiert mit Links zur neuen Dokumentation
- Logging-Konfiguration nur noch in main.py (entfernt aus anderen Modulen)
- Dependency-Versionen erhöht für Sicherheitsfixes
- **anomaly_detector.py**: 12 Magic Numbers zu benannten Konstanten extrahiert
- **wear_predictor.py**: 17 Magic Numbers zu benannten Konstanten extrahiert
- **optimizer.py**: 18 Magic Numbers zu benannten Konstanten extrahiert
- **ai_interface.py**: Verwendet jetzt konfigurierbare AI Layer URL und Timeout
- **mqtt_handler.py**: Erweitert um automatische Reconnection mit exponentieller Backoff
- **config.py**: Neue Konfigurationsoptionen für AI Layer (URL, Timeout)
- **CONFIGURATION.md**: Dokumentation neuer Umgebungsvariablen hinzugefügt
- **MainForm.cs**: Verbesserte Fehlerbehandlung mit Verbindungsstatus-Anzeige
- **ControlLayerClient.cs**: Exceptions für Connection/Timeout-Fehler werden durchgereicht

### Entfernt
- Ungenutzte Imports: Thread, numpy, Optional, stats, Dict
- Ungenutzte Variable `sample_count` in wear_predictor.py
- Doppelte `logging.basicConfig()` Aufrufe

### Behoben
- Dataclass-Konfigurationsfehler in config.py (field mit default_factory)
- Code-Qualitätsprobleme (pyflakes-clean)
- **Issue #001**: MQTT-Verbindungsabbruch ohne automatische Wiederverbindung
- **Issue #002**: API-Timeouts nicht konfigurierbar
- **Issue #003**: HMI zeigt keine Fehlermeldung bei API-Verbindungsfehler
- **Issue #004**: Inkonsistente Log-Level über Komponenten hinweg
- **Issue #006**: Fehlende API-Dokumentation - docs/API.md erstellt
- **Issue #007**: Konfigurationsoptionen nicht dokumentiert - docs/CONFIGURATION.md erstellt
- **Issue #009**: Magic Numbers im Code schwer verständlich und anzupassen
- **Issue #018**: Fehlende Sicherheitsdokumentation - docs/SECURITY.md erstellt
- **Issue #019**: Fehlende Datenpersistenz-Dokumentation - docs/DATA_PERSISTENCE.md erstellt
- **Issue #020**: Fehlende Containerisierungs-Dokumentation - docs/CONTAINERIZATION.md erstellt
- **Issue #021**: Fehlende Monitoring-Dokumentation - docs/MONITORING.md erstellt

### Sicherheit
- protobuf auf >=4.25.8 erhöht (CVE-Fix für DoS-Schwachstellen)
- fastapi auf >=0.109.1 erhöht (Fix für ReDoS-Schwachstelle)

## [0.1.0] - 2024-12-06

### Hinzugefügt
- Initiale 4-Ebenen-Architektur (Field, Control, AI, HMI)
- ESP32 Field Layer für Echtzeit-Sensordatenerfassung
  - Motor-Strom-Monitoring (ACS712)
  - Vibrations-Analyse (MPU6050)
  - Temperatur-Überwachung
  - Sicherheits-Interlocks (KI-frei)
- Python Control Layer
  - MQTT-Kommunikation mit Field Layer
  - Daten-Aggregation und Pufferung
  - REST API für HMI
  - AI-Layer-Integration
- Python AI Layer (beratend, nicht sicherheitskritisch)
  - Statistische Anomalie-Erkennung
  - Empirische Verschleiß-Vorhersage
  - Regelbasierte Optimierungs-Empfehlungen
- C# HMI Layer (Windows Forms)
  - Echtzeit-Überwachung von Sensordaten
  - Sicherheitsstatus-Anzeige
  - AI-Empfehlungen-Display
  - Steuerungsbefehle (sicherheitsvalidiert)
- Umfassende Dokumentation
  - README.md mit Systemübersicht
  - ARCHITECTURE.md mit detailliertem System-Design
  - SETUP.md mit Installations-Anleitung
  - Ebenen-spezifische README-Dateien
- Konfigurations-Beispiele für alle Ebenen
- Protobuf-Schema für zukünftige Nachrichten-Optimierung

### Sicherheit
- Hardware-basierte Sicherheits-Interlocks auf ESP32
- KI-freie Sicherheitszone implementiert
- Mehrschichtige Sicherheitsvalidierung
- Deterministisches Echtzeit-Verhalten für Sicherheitsfunktionen

---

## Format-Richtlinien

### Kategorien
- **Hinzugefügt** (Added): Neue Features
- **Geändert** (Changed): Änderungen an bestehender Funktionalität
- **Veraltet** (Deprecated): Features, die bald entfernt werden
- **Entfernt** (Removed): Entfernte Features
- **Behoben** (Fixed): Bugfixes
- **Sicherheit** (Security): Sicherheitsrelevante Änderungen

### Versionsnummern
- **MAJOR.MINOR.PATCH** (z.B. 1.0.0)
- **MAJOR**: Breaking Changes (inkompatible API-Änderungen)
- **MINOR**: Neue Features (rückwärtskompatibel)
- **PATCH**: Bugfixes (rückwärtskompatibel)

### Beispiel-Eintrag
```markdown
## [1.0.0] - 2024-01-15

### Hinzugefügt
- Neue Feature-Beschreibung mit Details

### Geändert
- Geänderte Funktion mit Begründung

### Behoben
- Bug #123: Beschreibung des behobenen Problems
```

---

[Unreleased]: https://github.com/Thomas-Heisig/MODAX/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Thomas-Heisig/MODAX/releases/tag/v0.1.0
