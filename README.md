# MODAX - Modular Industrial Control System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![.NET](https://img.shields.io/badge/.NET-8.0-blue)](https://dotnet.microsoft.com/)
[![Python](https://img.shields.io/badge/Python-3.8+-green)](https://www.python.org/)
[![ESP32](https://img.shields.io/badge/ESP32-Arduino-orange)](https://www.espressif.com/)

## Überblick

MODAX ist ein industrielles Steuerungssystem mit 4 Ebenen, das maschinelles Lernen für prädiktive Wartung und Optimierung integriert, während alle sicherheitskritischen Funktionen KI-frei bleiben.

**Kernkonzept:** Sichere Automatisierung mit beratender KI - Die KI-Ebene liefert Empfehlungen und Analysen, während die Steuerungsebene alle sicherheitskritischen Entscheidungen trifft. Das System kombiniert Echtzeit-Reaktionsfähigkeit mit intelligenter Langzeit-Analyse.

**Aktuelle Version:** 0.2.0 (mit umfassenden CNC-Funktionen)
- 123+ Unit-Tests, 96-97% Code Coverage
- Vollständige CNC-Maschinen-Funktionalität
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
   - Echtzeit-Überwachung (2s Update-Intervall)
   - Sicherheitsstatus-Anzeige mit Farbcodierung
   - KI-Empfehlungen mit Confidence-Level
   - Steuerungsbefehle mit Verbindungsstatus-Prüfung
   - Fehlerbehandlung mit Troubleshooting-Hinweisen
   - **Entry Point:** `csharp-hmi-layer/Program.cs`

## Hauptmerkmale

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

### 🏭 CNC-Maschinen-Funktionalität (NEU in v0.2.0)
- **G-Code-Unterstützung:** Vollständiger ISO 6983 Parser (100+ G/M-Codes)
- **Motion Control:** Lineare, zirkuläre und helikale Interpolation
- **Werkzeugverwaltung:** 24-Platz-Magazin, automatischer Werkzeugwechsel
- **Koordinatensysteme:** 9 Arbeitskoordinatensysteme, Transformationen
- **Festzyklen:** Bohren (G81-G89), Fräsen (G12/G13), Tappen (G84)
- **Spindelsteuerung:** CW/CCW, Drehzahlregelung, CSS-Modus
- **Vorschubsteuerung:** mm/min, mm/Umdrehung, Override 0-150%
- **Sicherheitsfunktionen:** Software-Endlagen, Not-Aus, Kollisionsvermeidung
- Siehe [CNC_FEATURES.md](docs/CNC_FEATURES.md) für Details

### 🔧 Modular & Skalierbar
- Mehrere Feldgeräte unterstützt
- Horizontale Skalierung
- Cloud-bereit
- Erweiterbare Architektur

## Quick Start

### Voraussetzungen
- Python 3.8+
- .NET 8.0 SDK
- MQTT Broker (Mosquitto)
- PlatformIO (für ESP32)

### Installation

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
pip install -r requirements.txt
python main.py
```

4. **KI-Ebene starten**
```bash
cd python-ai-layer
pip install -r requirements.txt
python main.py
```

5. **HMI starten** (Windows)
```bash
cd csharp-hmi-layer
dotnet run
```

6. **ESP32 konfigurieren und hochladen**
```bash
cd esp32-field-layer
# Edit src/main.cpp with WiFi credentials
pio run --target upload
```

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

### Phase 2 (Geplant)
- ONNX-Modell-Deployment
- Zeitreihen-Datenbank-Integration
- Erweiterte Visualisierungen
- WebSocket-Echtzeit-Updates

### Phase 3 (Zukunft)
- ML-Modell-Training-Pipeline
- Flottenweite Analytik
- Cloud-Integration
- Mobile App (nur Überwachung)

## Testing & Code Quality

Das Projekt verfügt über umfassende Tests und Code-Qualitätstools:

- **98 Unit-Tests** (42 Control Layer, 56 AI Layer)
- **96-97% Code Coverage**
- **Flake8 und Pylint** für Code-Qualitätsprüfungen

### Tests ausführen
```bash
# Alle Tests
./test_with_coverage.sh

# Nur Control Layer
cd python-control-layer && python -m unittest discover -v

# Nur AI Layer
cd python-ai-layer && python -m unittest discover -v
```

### Code-Linting
```bash
./lint.sh
```

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

## Support

Für Probleme und Fragen:
- Öffnen Sie ein Issue auf GitHub
- Überprüfen Sie die Dokumentation im `docs/` Verzeichnis
- Lesen Sie komponentenspezifische READMEs

---

**WICHTIGER HINWEIS**: Dieses System ist für industrielle Anwendungen konzipiert. Alle sicherheitskritischen Funktionen sind KI-frei und befolgen deterministische Echtzeit-Prinzipien. Die KI-Ebene dient nur zu beratenden Zwecken und sollte niemals für Sicherheitsentscheidungen verwendet werden.
