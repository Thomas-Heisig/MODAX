# MODAX - Änderungsprotokoll (CHANGELOG)

Alle bemerkenswerten Änderungen an diesem Projekt werden in dieser Datei dokumentiert.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.0.0/),
und dieses Projekt folgt [Semantic Versioning](https://semver.org/lang/de/).

## [Unreleased]

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
