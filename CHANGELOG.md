# MODAX - Änderungsprotokoll (CHANGELOG)

Alle bemerkenswerten Änderungen an diesem Projekt werden in dieser Datei dokumentiert.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.0.0/),
und dieses Projekt folgt [Semantic Versioning](https://semver.org/lang/de/).

## [Unreleased]

### Hinzugefügt
- TODO.md, ISSUES.md, DONE.md und CHANGELOG.md für strukturiertes Projekt-Management
- Umfassende API-Dokumentation (docs/API.md)
- Vollständige Konfigurationsreferenz (docs/CONFIGURATION.md)
- Erweiterte Docstrings für main.py Module
- **docs/ERROR_HANDLING.md**: Umfassender Fehlerbehandlungs-Leitfaden
- **docs/LOGGING_STANDARDS.md**: Logging-Standards und Konventionen
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

### Entfernt
- Ungenutzte Imports: Thread, numpy, Optional, stats, Dict
- Ungenutzte Variable `sample_count` in wear_predictor.py
- Doppelte `logging.basicConfig()` Aufrufe

### Behoben
- Dataclass-Konfigurationsfehler in config.py (field mit default_factory)
- Code-Qualitätsprobleme (pyflakes-clean)
- **Issue #001**: MQTT-Verbindungsabbruch ohne automatische Wiederverbindung
- **Issue #002**: API-Timeouts nicht konfigurierbar
- **Issue #004**: Inkonsistente Log-Level über Komponenten hinweg
- **Issue #009**: Magic Numbers im Code schwer verständlich und anzupassen

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
