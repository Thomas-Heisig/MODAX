# MODAX - Modular Industrial Control System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![.NET](https://img.shields.io/badge/.NET-8.0-blue)](https://dotnet.microsoft.com/)
[![Python](https://img.shields.io/badge/Python-3.8+-green)](https://www.python.org/)
[![ESP32](https://img.shields.io/badge/ESP32-Arduino-orange)](https://www.espressif.com/)

## Überblick

MODAX ist ein industrielles Steuerungssystem mit 4 Ebenen, das maschinelles Lernen für prädiktive Wartung und Optimierung integriert, während alle sicherheitskritischen Funktionen KI-frei bleiben.

**Kernkonzept:** Sichere Automatisierung mit beratender KI - Die KI-Ebene liefert Empfehlungen und Analysen, während die Steuerungsebene alle sicherheitskritischen Entscheidungen trifft. Das System kombiniert Echtzeit-Reaktionsfähigkeit mit intelligenter Langzeit-Analyse.

**Aktuelle Version:** 0.5.0 (MDI Interface & Network Scanner)
- 172+ Unit-Tests, 96-97% Code Coverage
- **NEU:** MDI (Multiple Document Interface) mit Dashboard und Tabs
- **NEU:** Network Scanner & Port Scanner mit automatischer Geräteerkennung
- **NEU:** Erweiterte Dashboard-Funktionen (Overview, Devices, Analytics, Logs)
- Vollständige CNC-Maschinen-Funktionalität
- RS485/Modbus, MIDI, Pendant, Slave Board Support
- Industrielle Kommunikationsprotokolle
- Produktionsreife Dokumentation
- Docker-ready Architektur
- MQTT-basierte IoT-Kommunikation

## System Architecture

### Die 4 Ebenen

1. **Feldebene (ESP32)** - Echtzeit-Sensordatenerfassung
   - Motorströme (ACS712), Vibrationen (MPU6050), Temperaturen
   - Sicherheitsüberwachung (KI-frei, Hardware-basiert)
   - MQTT-Datenübertragung (10Hz Sensordaten, 20Hz Safety)
   - Hardware-Interlocks für Not-Aus und Überlastschutz
   - **Entry Point:** `esp32-field-layer/src/main.cpp`

2. **Steuerungsebene (Python)** - Zentrale Koordination
   - Datenaggregation von mehreren Geräten mit konfigurierbarem Time-Window
   - REST API für HMI (FastAPI, Port 8000)
   - **NEUE CNC-Funktionalität:** G-Code-Parsing, Motion Control, Werkzeugverwaltung
   - Vollständige CNC-Maschinen-Steuerung (Fräsen, Drehen, Bohren)
   - Asynchrone KI-Analyse-Anfragen mit konfigurierbaren Timeouts
   - MQTT-Handler mit automatischer Reconnection (exponentielles Backoff)
   - Safety-Command-Validation vor Ausführung
   - **Entry Point:** `python-control-layer/main.py`

3. **KI-Ebene (Python)** - Intelligente Analyse (Querschnittsfunktion)
   - Statistische Anomalieerkennung (Z-Score-basiert, konfigurierbare Schwellenwerte)
   - Empirische Verschleißvorhersage (Stress-Akkumulation)
   - Regelbasierte Optimierungsempfehlungen
   - REST API (FastAPI, Port 8001)
   - **NUR BERATEND** - keine Sicherheitsfunktionen, keine Echtzeit-Kontrolle
   - **Entry Point:** `python-ai-layer/main.py`

4. **HMI-Ebene (C#)** - Mensch-Maschine-Schnittstelle
   - **NEU:** MDI (Multiple Document Interface) mit Tabs und Fenstern
   - **NEU:** Erweitertes Dashboard (Overview, Devices, Analytics, Logs)
   - **NEU:** Network Scanner & Port Scanner Integration
   - Echtzeit-Überwachung (2s Update-Intervall)
   - Sicherheitsstatus-Anzeige mit Farbcodierung
   - KI-Empfehlungen mit Confidence-Level
   - Steuerungsbefehle mit Verbindungsstatus-Prüfung
   - Fehlerbehandlung mit Troubleshooting-Hinweisen
   - Umfangreiche Keyboard-Shortcuts (F1, Ctrl+D, Ctrl+N, etc.)
   - **Entry Point:** `csharp-hmi-layer/Program.cs`

## Hauptmerkmale

### 🛡️ Fehlertoleranz & Robustheit (NEU in v0.4.1)
- **Automatische Wiederholungslogik:** Services starten mit bis zu 3 Versuchen bei Fehlern
- **Graceful Degradation:** System läuft weiter, auch wenn einzelne Komponenten ausfallen
- **Globale Exception Handler:** Umfassende Fehlerbehandlung auf allen Ebenen
- **Startup Resilience:** API-Server startet garantiert, unabhängig von anderen Services
- **HMI Offline-Modus:** HMI startet immer, auch wenn Backend nicht verfügbar ist
- **Konfigurationsvalidierung:** Automatische Fallback auf Standardwerte bei Fehlern
- **Comprehensive Logging:** Detaillierte Fehlerprotokolle für schnelle Problemanalyse

### ✅ Sicherheit zuerst
- Alle sicherheitskritischen Funktionen bleiben KI-frei
- Hardware-Sicherheitsverriegelungen auf ESP32
- Deterministische Echtzeit-Reaktion
- Mehrschichtige Sicherheitsvalidierung

### 🤖 KI-Integration (beratend)
- **Anomalieerkennung:** Z-Score-basierte Analyse von Strom, Vibration, Temperatur
- **Verschleißvorhersage:** Stress-Akkumulation mit geschätzter Restlebensdauer
- **Optimierungsempfehlungen:** Regelbasiertes Expertensystem
- **Confidence-Tracking:** Jede Analyse mit Vertrauenslevel
- **Baseline-Learning:** Adaptive Schwellenwerte basierend auf historischen Daten
- Bereit für ONNX ML-Modelle (zukünftige Erweiterung)

### 📊 Echtzeit-Überwachung
- **10Hz Sensordaten:** Kontinuierliche Erfassung von Strom, Vibration, Temperatur
- **20Hz Sicherheitsüberwachung:** Hochfrequente Sicherheitsprüfungen auf ESP32
- **2s HMI-Aktualisierung:** Regelmäßige UI-Updates mit aktuellen Werten
- **MQTT-basierte Kommunikation:** Pub/Sub-Pattern für lose Kopplung
- **Time-Window-Aggregation:** Statistische Auswertung über konfigurierbare Zeitfenster
- **Automatische Reconnection:** Robuste Fehlerbehandlung bei Verbindungsproblemen

### 🏭 CNC-Maschinen-Funktionalität (NEU in v0.2.0, Erweitert in v0.4.0)
- **G-Code-Unterstützung:** Vollständiger ISO 6983 Parser (150+ G/M-Codes)
- **Erweiterte Codes:** NURBS (G05), Zylindrische Interpolation (G07.1), Threading (G33, G76, G84.2/3)
- **Herstellerspezifisch:** Siemens Sinumerik, Fanuc Macro B, Heidenhain TNC, Okuma OSP, Mazak
- **Makro-Unterstützung:** G65/G66/G67, O-Codes, Variablen (#1-#999)
- **Kontrollfluss:** GOTO, GOSUB, RETURN, Labels, Unterprogramme
- **Motion Control:** Lineare, zirkuläre und helikale Interpolation
- **Werkzeugverwaltung:** 24-Platz-Magazin, automatischer Werkzeugwechsel, Auto-Messung (G36/G37)
- **Koordinatensysteme:** 9 + erweiterte (G54.1 P1-P300), Transformationen
- **Festzyklen:** Bohren (G81-G89, G73), Fräsen (G12/G13), Tappen (G84)
- **Spindelsteuerung:** CW/CCW, Orientierung (M19), Getriebe (M21/M22), Starr-Tappen (M29)
- **Kühlmittel:** Flood/Mist (M07/M08), Hochdruck (M50), Through-Spindle (M88/M89)
- **Vorschubsteuerung:** mm/min, mm/Umdrehung, Override 0-150%, Bereichsbegrenzung (M36/M37)
- **Sicherheitsfunktionen:** Software-Endlagen, Not-Aus, Kollisionsvermeidung, Arbeitsbereichsbegrenzung (G22/G23)
- Siehe [CNC_FEATURES.md](docs/CNC_FEATURES.md) und [EXTENDED_GCODE_SUPPORT.md](docs/EXTENDED_GCODE_SUPPORT.md) für Details

### 🚀 Industry 4.0 Roadmap (NEU v0.3.0)
- **Advanced Communication:** OPC UA (✅), MQTT (✅), EtherCAT, PROFINET, MTConnect
- **Intelligent Process Control:** Adaptive Feed Control, Vibration Monitoring, Energy Management
- **Predictive Intelligence:** AI-powered parameter optimization, predictive maintenance
- **Digital Twin:** Virtual machine simulation and optimization
- **Next-Gen HMI:** Cloud-native interfaces, AR guidance, voice control
- Siehe [ADVANCED_CNC_INDUSTRY_4_0.md](docs/ADVANCED_CNC_INDUSTRY_4_0.md) für vollständige Roadmap

### 💻 MDI Interface & Network Scanner (NEU in v0.5.0)
- **MDI (Multiple Document Interface):** Moderne Tab-basierte Benutzeroberfläche
- **Erweitertes Dashboard:** Overview, Devices, Analytics, Logs-Tabs
- **Network Scanner:** Automatische Netzwerk-Geräteerkennung (CIDR-Notation)
- **Port Scanner:** Service-Erkennung mit Common Ports und Custom Ranges
- **Device Type Detection:** Automatische Identifikation (Modbus, OPC UA, MODAX, Web, SSH)
- **Keyboard Shortcuts:** Umfangreiche Tastaturkürzel (F1, Ctrl+D, Ctrl+N, etc.)
- **Window Management:** Cascade, Tile Horizontal/Vertical, Arrange Icons
- **Rate Limiting:** Schutz vor Missbrauch mit API-Ratenbegrenzung
- Siehe [MDI_INTERFACE.md](docs/MDI_INTERFACE.md) für vollständige Dokumentation

### 🔌 Industrielle Kommunikation (NEU in v0.4.1)
- **RS485/Modbus RTU:** Direkte VFD-Steuerung (ABB, Siemens, Schneider, etc.)
- **MIDI Audio Feedback:** Betriebsgeräusche für CNC-Events
- **Pendant Device Support:** USB HID Handwheel/MPG für manuelle Steuerung
- **Slave Board I2C:** Verteilte I/O-Erweiterung (Digital, Analog, PWM)
- Graceful Degradation mit Stub-Implementierungen

### 🔧 Modular & Skalierbar
- Mehrere Feldgeräte unterstützt
- Horizontale Skalierung
- Cloud-bereit
- Erweiterbare Architektur

## Quick Start

### Voraussetzungen
- Python 3.8+
- .NET 8.0 SDK (optional, für HMI)
- MQTT Broker (Mosquitto oder Docker)
- PlatformIO (für ESP32)

### Automatische Installation (Empfohlen)

**Schnellinstallation aller Ebenen:**
```bash
git clone https://github.com/Thomas-Heisig/MODAX.git
cd MODAX
./install.sh
```

Das Installationsskript:
- ✅ Prüft und validiert alle Voraussetzungen
- ✅ Erstellt virtuelle Python-Umgebungen für beide Ebenen
- ✅ Installiert alle Python-Abhängigkeiten
- ✅ Konfiguriert .NET HMI (falls SDK verfügbar)
- ✅ Erstellt Konfigurationsdateien (.env)
- ✅ Generiert Start-/Stop-Skripte
- ✅ Validiert die Installation

**Services starten:**
```bash
./start-all.sh
```

**Services stoppen:**
```bash
./stop-all.sh
```

### Manuelle Installation

<details>
<summary>Klicken Sie hier für manuelle Installationsschritte</summary>

1. **Repository klonen**
```bash
git clone https://github.com/Thomas-Heisig/MODAX.git
cd MODAX
```

2. **MQTT Broker starten**
```bash
# Linux/macOS
sudo systemctl start mosquitto

# Docker
docker run -d -p 1883:1883 eclipse-mosquitto
```

3. **Steuerungsebene starten**
```bash
cd python-control-layer
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

4. **KI-Ebene starten**
```bash
cd python-ai-layer
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

5. **HMI starten** (Windows)
```bash
cd csharp-hmi-layer
dotnet restore
dotnet run
```

6. **ESP32 konfigurieren und hochladen**
```bash
cd esp32-field-layer
# Edit src/main.cpp with WiFi credentials
pio run --target upload
```

</details>

Ausführliche Anweisungen finden Sie unter [docs/SETUP.md](docs/SETUP.md)

## Dokumentation

📚 **[Vollständiger Dokumentations-Index](docs/INDEX.md)** - Umfassender Überblick über alle Dokumentation

### Hauptdokumentation

#### Kern-System
- [📋 Architektur-Übersicht](docs/ARCHITECTURE.md) - Detailliertes Systemdesign
- [🔧 Setup-Anleitung](docs/SETUP.md) - Vollständige Installationsanleitung
- [📡 API-Dokumentation](docs/API.md) - REST API Referenz
- [⚙️ Konfiguration](docs/CONFIGURATION.md) - Konfigurationsoptionen
- [🚀 Quick Wins (TOFU)](docs/TOFU.md) - Produktionsreife Features und Best Practices

#### CNC & Industry 4.0
- [🏭 CNC Features](docs/CNC_FEATURES.md) - CNC machine functionality (G-code, motion control, tools)
- [📝 Extended G-Code Support](docs/EXTENDED_GCODE_SUPPORT.md) - Extended G-codes, macros, manufacturer-specific codes
- [🔧 Hobbyist CNC Systems](docs/HOBBYIST_CNC_SYSTEMS.md) - **NEU** Estlcam, UCCNC, Haas-specific functions
- [🚀 Advanced CNC Industry 4.0](docs/ADVANCED_CNC_INDUSTRY_4_0.md) - Advanced features, communication protocols, intelligent automation, digital twin, AI optimization

#### Sicherheit & Netzwerk
- [🔒 Sicherheit](docs/SECURITY.md) - Sicherheitskonzept und Implementierung
- [🌐 Netzwerkarchitektur](docs/NETWORK_ARCHITECTURE.md) - OT/IT-Trennung, Purdue-Modell, Firewalls
- [🔐 Fehlerbehandlung](docs/ERROR_HANDLING.md) - Fehlerbehandlungs-Patterns
- [📋 Logging-Standards](docs/LOGGING_STANDARDS.md) - Logging-Best-Practices

#### Daten & Persistenz
- [💾 Datenpersistenz](docs/DATA_PERSISTENCE.md) - Datenbank-Strategie und TimescaleDB
- [💿 Backup & Recovery](docs/BACKUP_RECOVERY.md) - Backup-Strategien und Disaster Recovery

#### Deployment & Operations
- [🐳 Containerisierung](docs/CONTAINERIZATION.md) - Docker und Deployment
- [🔄 CI/CD-Pipeline](docs/CI_CD.md) - Continuous Integration/Deployment
- [⚡ High Availability](docs/HIGH_AVAILABILITY.md) - Hochverfügbarkeit und Failover
- [📊 Monitoring](docs/MONITORING.md) - Observability Stack (Prometheus, Loki, Grafana)

#### Integration
- [🔌 OPC UA Integration](docs/OPC_UA_INTEGRATION.md) - OPC UA Server/Client, SCADA-Integration

### Ebenen-spezifische Dokumentation
- [🔌 Feldebene](esp32-field-layer/README.md) - ESP32 Dokumentation
- [⚙️ Steuerungsebene](python-control-layer/README.md) - Python Control Layer
- [🤖 KI-Ebene](python-ai-layer/README.md) - AI Layer Details
- [💻 HMI-Ebene](csharp-hmi-layer/README.md) - C# HMI Dokumentation

### Projekt-Management
- [📝 TODO](TODO.md) - Offene Aufgaben und Roadmap
- [🐛 ISSUES](ISSUES.md) - Bekannte Probleme und Verbesserungsvorschläge
- [✅ DONE](DONE.md) - Erledigte Aufgaben
- [📜 CHANGELOG](CHANGELOG.md) - Änderungsprotokoll

## Projektstruktur

```
MODAX/
├── esp32-field-layer/       # ESP32 Feldebene (C++)
│   ├── src/main.cpp         # Hauptprogramm
│   └── platformio.ini       # Build-Konfiguration
├── python-control-layer/    # Steuerungsebene (Python)
│   ├── control_layer.py     # Hauptorchestrator
│   ├── data_aggregator.py   # Datenaggregation
│   ├── mqtt_handler.py      # MQTT-Kommunikation
│   ├── control_api.py       # REST API
│   └── main.py              # Einstiegspunkt
├── python-ai-layer/         # KI-Ebene (Python)
│   ├── anomaly_detector.py  # Anomalieerkennung
│   ├── wear_predictor.py    # Verschleißvorhersage
│   ├── optimizer.py         # Optimierungsempfehlungen
│   ├── ai_service.py        # REST API
│   └── main.py              # Einstiegspunkt
├── csharp-hmi-layer/        # HMI-Ebene (C#)
│   ├── Models/              # Datenmodelle
│   ├── Services/            # API-Clients
│   ├── Views/               # UI-Formulare
│   └── Program.cs           # Einstiegspunkt
├── protobuf/                # Protokoll-Definitionen
│   └── sensor_data.proto    # Protobuf-Nachrichten
├── config/                  # Konfigurationsdateien
└── docs/                    # Dokumentation
    ├── ARCHITECTURE.md      # System-Architektur
    └── SETUP.md             # Setup-Anleitung
```

## Technologie-Stack

| Ebene | Technologie | Frameworks | Zweck |
|-------|-------------|------------|-------|
| Feldebene | C++/ESP32 | Arduino, PlatformIO | Echtzeit-Datenerfassung |
| Steuerung | Python 3.8+ | FastAPI, paho-mqtt | Zentrale Koordination |
| KI | Python 3.8+ | scikit-learn, ONNX | Intelligente Analyse |
| HMI | C#/.NET 8.0 | Windows Forms | Benutzeroberfläche |

## API-Endpunkte

### Steuerungsebene (Port 8000)
**Implementiert in:** `python-control-layer/control_api.py`
- `GET /status` - Systemstatus mit Uptime und letztem Update
- `GET /devices` - Liste aller verbundenen Geräte
- `GET /devices/{id}/data` - Aktuelle Sensordaten (Raw und Aggregiert)
- `GET /devices/{id}/safety` - Sicherheitsstatus des Geräts
- `GET /devices/{id}/ai-analysis` - Letzte KI-Analyse mit Empfehlungen
- `POST /control/command` - Steuerungsbefehl mit Safety-Validation

### KI-Ebene (Port 8001)
**Implementiert in:** `python-ai-layer/ai_service.py`
- `GET /` - Service-Info und Version
- `GET /health` - Health-Check für Monitoring
- `POST /analyze` - Sensordaten analysieren (mit SensorDataInput-Schema)
- `GET /models/info` - Detaillierte Modellinformationen und Konfiguration
- `POST /reset-wear/{device_id}` - Verschleißzähler nach Wartung zurücksetzen

Vollständige API-Dokumentation siehe: [docs/API.md](docs/API.md)

## Sicherheitsdesign

### KI-freie Sicherheitszone
Die KI-Ebene beteiligt sich **NICHT** an Sicherheitsentscheidungen:
- ❌ Keine Kontrolle über Not-Aus
- ❌ Keine Kontrolle über Sicherheitsverriegelungen
- ❌ Keine Echtzeit-Sicherheitsüberwachung
- ✅ Nur beratende Empfehlungen
- ✅ Trendanalyse und Vorhersage
- ✅ Optimierungsvorschläge

### Mehrschichtige Sicherheitsarchitektur
1. **Hardware-Ebene (ESP32):** Deterministische Sicherheitsüberwachung mit Hardware-Interlocks
2. **Control Layer:** Safety-Command-Validation vor Ausführung (`is_system_safe()`)
3. **HMI-Ebene:** Benutzer-Feedback bei Verbindungsproblemen und Fehlerzuständen

Sicherheitsfunktionen bleiben in der Feldebene (ESP32) Hardware. Siehe [docs/SECURITY.md](docs/SECURITY.md) für Details.

## Zukünftige Erweiterungen

⭐ **Siehe [ADVANCED_CNC_INDUSTRY_4_0.md](docs/ADVANCED_CNC_INDUSTRY_4_0.md) für vollständige Industry 4.0 Roadmap**

### Phase 2 (Monate 1-3) - ✅ DOKUMENTIERT
- ✅ **ONNX-Modell-Deployment** - [Dokumentation](docs/ONNX_MODEL_DEPLOYMENT.md)
- ✅ **Multi-Mandanten-Unterstützung** - [Dokumentation](docs/MULTI_TENANT_ARCHITECTURE.md)
- ✅ **Rollenbasierte Zugriffskontrolle (RBAC)** - Erweitert in `python-control-layer/auth.py`
- ✅ **Mobile App Architektur** - [Dokumentation](docs/MOBILE_APP_ARCHITECTURE.md)
- ✅ OPC UA Server Deployment (bereits dokumentiert)
- ✅ Zeitreihen-Datenbank-Integration (TimescaleDB)
- ✅ WebSocket-Echtzeit-Updates
- ✅ Erweiterte Visualisierungen

### Phase 3 (Monate 4-12) - ✅ DOKUMENTIERT
- ✅ **ML-Modell-Training-Pipeline** - [Dokumentation](docs/ML_TRAINING_PIPELINE.md)
- ✅ **Flottenweite Analytik** - [Dokumentation](docs/FLEET_ANALYTICS.md)
- ✅ **Cloud-Integration** (AWS, Azure, GCP) - [Dokumentation](docs/CLOUD_INTEGRATION.md)
- ✅ **Digital Twin Integration** - [Dokumentation](docs/DIGITAL_TWIN_INTEGRATION.md)
- ✅ **Federated Learning** - [Dokumentation](docs/FEDERATED_LEARNING.md)
- ✅ **Predictive Maintenance mit Deep Learning** - In ML Pipeline & Digital Twin dokumentiert
- ✅ **Automatisierte Wartungsplanung** - [Dokumentation](docs/ADVANCED_FEATURES_ROADMAP.md)
- ✅ **MES/ERP Integration** (SAP, Oracle, Dynamics) - [Dokumentation](docs/ADVANCED_FEATURES_ROADMAP.md)
- ✅ **Blockchain Audit Trails** - [Dokumentation](docs/ADVANCED_FEATURES_ROADMAP.md)
- ✅ **Edge Computing Optimierungen** - [Dokumentation](docs/ADVANCED_FEATURES_ROADMAP.md)

### Phase 4 (Monate 13-18) - In Planung
- EtherCAT/PROFINET Support
- Advanced Digital Twin mit erweiterten Physics
- AR Maintenance Guidance
- Voice Control Interface
- Complete Industry 4.0 Stack

## Testing & Code Quality

Das Projekt verfügt über umfassende Tests und Code-Qualitätstools:

- **98 Unit-Tests** (42 Control Layer, 56 AI Layer)
- **96-97% Code Coverage**
- **Flake8, Pylint und MyPy** für Code-Qualitätsprüfungen
- **Strict Mode** verfügbar für erhöhte Code-Qualität

### Tests ausführen
```bash
# Alle Tests mit Coverage
./test_with_coverage.sh

# Nur Control Layer
cd python-control-layer && python -m unittest discover -v

# Nur AI Layer
cd python-ai-layer && python -m unittest discover -v
```

### Code-Linting
```bash
# Standard-Linting (informativ)
./lint.sh

# Strict Mode (erzwingt alle Prüfungen)
./lint.sh --strict
```

**Linting-Tools:**
- **Flake8:** PEP 8 Compliance, Code-Komplexität
- **Pylint:** Erweiterte Code-Analyse, Best Practices
- **MyPy:** Statische Typprüfung

Siehe [docs/TESTING.md](docs/TESTING.md) für weitere Details.

## Mitwirken

Beiträge sind willkommen! Bitte lesen Sie die Beitragsrichtlinien, bevor Sie einen Pull Request einreichen.

1. Fork das Repository
2. Erstellen Sie einen Feature-Branch
3. Committen Sie Ihre Änderungen
4. Führen Sie Tests und Linting aus (`./test_with_coverage.sh && ./lint.sh`)
5. Pushen Sie zum Branch
6. Öffnen Sie einen Pull Request

## Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert - siehe LICENSE-Datei für Details.

## Autor

Thomas Heisig

## Anerkennungen

- ESP32 Community für Hardware-Support
- FastAPI für die ausgezeichnete Python-API-Framework
- MQTT-Protokoll für zuverlässiges Messaging
- Open-Source-Community

## Projektdokumentation

### Aktive Dokumentation
- [docs/INDEX.md](docs/INDEX.md) - Vollständiger Dokumentations-Index
- [TODO.md](TODO.md) - Offene Aufgaben (2 aktive Items)
- [ISSUES.md](ISSUES.md) - Bekannte Probleme (Alle behoben! 🎉)
- [DONE.md](DONE.md) - Erledigte Aufgaben (123+ Items)
- [CHANGELOG.md](CHANGELOG.md) - Versionshistorie

### Historische Dokumentation
Abgeschlossene Session-Zusammenfassungen und Implementierungsberichte wurden für bessere Übersichtlichkeit archiviert:
- [archive/](archive/README.md) - Implementierungs-Summaries, Session-Notes, Security Audits
- [docs/archive/](docs/archive/README.md) - Historische Dokumentations-Updates

## Support

Für Probleme und Fragen:
- Öffnen Sie ein Issue auf GitHub
- Überprüfen Sie die Dokumentation im `docs/` Verzeichnis
- Konsultieren Sie den [Troubleshooting Guide](docs/TROUBLESHOOTING.md)
- Lesen Sie komponentenspezifische READMEs

---

**WICHTIGER HINWEIS**: Dieses System ist für industrielle Anwendungen konzipiert. Alle sicherheitskritischen Funktionen sind KI-frei und befolgen deterministische Echtzeit-Prinzipien. Die KI-Ebene dient nur zu beratenden Zwecken und sollte niemals für Sicherheitsentscheidungen verwendet werden.
