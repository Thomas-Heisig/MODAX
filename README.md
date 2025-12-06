# MODAX - Modular Industrial Control System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![.NET](https://img.shields.io/badge/.NET-8.0-blue)](https://dotnet.microsoft.com/)
[![Python](https://img.shields.io/badge/Python-3.8+-green)](https://www.python.org/)
[![ESP32](https://img.shields.io/badge/ESP32-Arduino-orange)](https://www.espressif.com/)

## Überblick

MODAX ist ein industrielles Steuerungssystem mit 4 Ebenen, das maschinelles Lernen für prädiktive Wartung und Optimierung integriert, während alle sicherheitskritischen Funktionen KI-frei bleiben.

## System Architecture

### Die 4 Ebenen

1. **Feldebene (ESP32)** - Echtzeit-Sensordatenerfassung
   - Motorströme, Vibrationen, Temperaturen
   - Sicherheitsüberwachung (KI-frei)
   - MQTT-Datenübertragung

2. **Steuerungsebene (Python)** - Zentrale Koordination
   - Datenaggregation von mehreren Geräten
   - REST API für HMI
   - Schnittstelle zur KI-Ebene

3. **KI-Ebene (Python)** - Intelligente Analyse (Querschnittsfunktion)
   - Anomalieerkennung
   - Verschleißvorhersage
   - Optimierungsempfehlungen
   - **NUR BERATEND** - keine Sicherheitsfunktionen

4. **HMI-Ebene (C#)** - Mensch-Maschine-Schnittstelle
   - Echtzeit-Überwachung
   - Sicherheitsstatus-Anzeige
   - KI-Empfehlungen
   - Steuerungsbefehle

## Hauptmerkmale

### ✅ Sicherheit zuerst
- Alle sicherheitskritischen Funktionen bleiben KI-frei
- Hardware-Sicherheitsverriegelungen auf ESP32
- Deterministische Echtzeit-Reaktion
- Mehrschichtige Sicherheitsvalidierung

### 🤖 KI-Integration (beratend)
- Statistische Anomalieerkennung
- Empirische Verschleißvorhersage
- Regelbasierte Optimierung
- Bereit für ONNX ML-Modelle

### 📊 Echtzeit-Überwachung
- 10Hz Sensordaten
- 20Hz Sicherheitsüberwachung
- 2s HMI-Aktualisierung
- MQTT-basierte Kommunikation

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

### Hauptdokumentation
- [📋 Architektur-Übersicht](docs/ARCHITECTURE.md) - Detailliertes Systemdesign
- [🔧 Setup-Anleitung](docs/SETUP.md) - Vollständige Installationsanleitung
- [📡 API-Dokumentation](docs/API.md) - REST API Referenz
- [⚙️ Konfiguration](docs/CONFIGURATION.md) - Konfigurationsoptionen

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
- `GET /status` - Systemstatus
- `GET /devices` - Verbundene Geräte
- `GET /devices/{id}/data` - Aktuelle Sensordaten
- `GET /devices/{id}/ai-analysis` - KI-Analyse
- `POST /control/command` - Steuerungsbefehl senden

### KI-Ebene (Port 8001)
- `POST /analyze` - Sensordaten analysieren
- `GET /models/info` - Modellinformationen
- `POST /reset-wear/{id}` - Verschleißzähler zurücksetzen

## Sicherheitsdesign

### KI-freie Sicherheitszone
Die KI-Ebene beteiligt sich **NICHT** an Sicherheitsentscheidungen:
- ❌ Keine Kontrolle über Not-Aus
- ❌ Keine Kontrolle über Sicherheitsverriegelungen
- ❌ Keine Echtzeit-Sicherheitsüberwachung
- ✅ Nur beratende Empfehlungen
- ✅ Trendanalyse und Vorhersage
- ✅ Optimierungsvorschläge

Sicherheitsfunktionen bleiben in der Feldebene (ESP32) Hardware.

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

## Mitwirken

Beiträge sind willkommen! Bitte lesen Sie die Beitragsrichtlinien, bevor Sie einen Pull Request einreichen.

1. Fork das Repository
2. Erstellen Sie einen Feature-Branch
3. Committen Sie Ihre Änderungen
4. Pushen Sie zum Branch
5. Öffnen Sie einen Pull Request

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
