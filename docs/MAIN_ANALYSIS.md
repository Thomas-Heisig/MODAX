# MODAX Main Entry Points - Analyse und Implementierungsdetails

**Erstellt:** 2025-12-07  
**Analysierte Version:** 0.1.0  
**Zweck:** Detaillierte Analyse der Main-Entry-Points für Dokumentations-Synchronisierung

## Übersicht

Dieses Dokument enthält die Ergebnisse der Analyse der Main-Entry-Points des MODAX-Systems. Basierend auf dieser Analyse wurden alle Dokumentationsdateien (README.md, TODO.md, ISSUES.md, CHANGELOG.md) aktualisiert, um die tatsächliche Implementierung widerzuspiegeln.

## Analysierte Main-Dateien

### 1. python-ai-layer/main.py

**Framework:** FastAPI + uvicorn  
**Port:** 8001  
**Logging:** Konfiguriert in main.py mit StreamHandler zu stdout

#### Implementierte Features

```python
# Entry Point
def main():
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
```

#### AI-Service-Komponenten (ai_service.py)

1. **StatisticalAnomalyDetector**
   - Z-Score-basierte Anomalieerkennung
   - Konfigurierbare Schwellenwerte (z_threshold=3.0)
   - Getrennte Analyse für Strom, Vibration, Temperatur
   - Baseline-Learning für adaptive Schwellenwerte

2. **SimpleWearPredictor**
   - Empirische Verschleißvorhersage
   - Stress-Akkumulations-Modell
   - Geschätzte Restlebensdauer in Stunden
   - Contributing-Factors-Tracking

3. **OptimizationRecommender**
   - Regelbasiertes Expertensystem
   - Generiert Empfehlungen basierend auf Anomalien und Verschleiß
   - Priorisierte Empfehlungsliste

#### REST API Endpoints

| Endpoint | Methode | Beschreibung |
|----------|---------|--------------|
| `/` | GET | Service-Info und Version |
| `/health` | GET | Health-Check für Monitoring |
| `/analyze` | POST | Hauptanalyse-Endpunkt (SensorDataInput → AIAnalysisResponse) |
| `/models/info` | GET | Detaillierte Modellinformationen |
| `/reset-wear/{device_id}` | POST | Verschleißzähler nach Wartung zurücksetzen |

#### Datenmodelle

**SensorDataInput:**
- device_id, time_window_start/end
- current_mean/std/max (Listen)
- vibration_mean/std/max (Dicts mit x/y/z/magnitude)
- temperature_mean/max (Listen)
- sample_count

**AIAnalysisResponse:**
- timestamp, device_id
- anomaly_detected, anomaly_score, anomaly_description
- predicted_wear_level, estimated_remaining_hours
- recommendations (List[str])
- confidence, analysis_details (Optional[Dict])

#### Wichtige Design-Entscheidungen

1. **Advisory Only:** KI-Ebene beteiligt sich NICHT an Sicherheitsentscheidungen
2. **Stateless:** Jede Analyse-Anfrage ist unabhängig
3. **Baseline-Tracking:** Anomaly-Detector speichert Baselines pro Device
4. **Confidence-Tracking:** Jede Analyse enthält Vertrauenslevel
5. **Fehlerbehandlung:** Try-Catch mit HTTPException(500) bei Fehlern

### 2. python-control-layer/main.py

**Framework:** FastAPI + uvicorn  
**Port:** 8000  
**Logging:** Konfiguriert in main.py mit StreamHandler zu stdout

#### Implementierte Features

```python
def main():
    # Signal-Handler für graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Control Layer initialisieren und starten
    control_layer_instance = ControlLayer(config)
    control_api.set_control_layer(control_layer_instance)
    control_layer_instance.start()
    
    # API-Server starten
    uvicorn.run(control_api.app, host=config.control.api_host, 
                port=config.control.api_port, log_level="info")
```

#### ControlLayer-Komponenten (control_layer.py)

1. **DataAggregator**
   - Time-Window-basierte Datenaggregation
   - Statistische Berechnungen (mean, std, max)
   - Konfigurierbare Window-Größe und Max-Points
   - Safety-Status-Tracking

2. **MQTTHandler**
   - MQTT-Broker-Verbindung
   - Topic-basiertes Pub/Sub
   - Automatische Reconnection mit exponentieller Backoff
   - Callback-System für Sensor-Daten, Safety-Status, AI-Analysis

3. **AI-Analysis-Loop**
   - Periodische AI-Anfragen (konfigurierbar)
   - Threading für Non-Blocking-Betrieb
   - Error-Handling mit Logging

#### REST API Endpoints (control_api.py)

| Endpoint | Methode | Beschreibung |
|----------|---------|--------------|
| `/status` | GET | Systemstatus mit Uptime und letztem Update |
| `/devices` | GET | Liste aller verbundenen Geräte |
| `/devices/{id}/data` | GET | Aktuelle Sensordaten (Raw und Aggregiert) |
| `/devices/{id}/safety` | GET | Sicherheitsstatus des Geräts |
| `/devices/{id}/ai-analysis` | GET | Letzte KI-Analyse mit Empfehlungen |
| `/control/command` | POST | Steuerungsbefehl mit Safety-Validation |

#### Wichtige Design-Entscheidungen

1. **Zentrale Orchestrierung:** Control Layer koordiniert alle Datenflüsse
2. **Safety-First:** Alle Befehle werden auf Systemsicherheit validiert
3. **Async AI-Requests:** Nicht-blockierende AI-Anfragen mit Timeout
4. **Robust MQTT:** Automatische Reconnection bei Verbindungsproblemen
5. **Graceful Shutdown:** Signal-Handler für sauberes Herunterfahren

### 3. ESP32 Field Layer (esp32-field-layer/src/main.cpp)

**Sprache:** C++ (Arduino Framework)  
**Plattform:** ESP32 mit PlatformIO

#### Hauptfunktionen

- **Sensor-Datenerfassung:**
  - Motorströme (ACS712)
  - Vibrationen (MPU6050)
  - Temperaturen
  - 10Hz Sampling-Rate

- **Sicherheitsüberwachung (KI-frei):**
  - Hardware-basierte Interlocks
  - 20Hz Sicherheitschecks
  - Deterministische Echtzeit-Reaktion
  - Not-Aus und Überlastschutz

- **MQTT-Kommunikation:**
  - Publiziert Sensor-Daten
  - Empfängt Steuerungsbefehle
  - WiFi-basierte Verbindung

### 4. C# HMI Layer (csharp-hmi-layer/Program.cs)

**Framework:** .NET 8.0 Windows Forms  
**Funktion:** Desktop-Anwendung für Operator-Interface

#### Hauptfunktionen

- **Echtzeit-Überwachung:**
  - 2s Update-Intervall
  - Anzeige aller Sensordaten
  - Sicherheitsstatus mit Farbcodierung

- **KI-Integration:**
  - Anzeige von Anomalie-Warnungen
  - Verschleißvorhersage
  - Optimierungsempfehlungen
  - Confidence-Level

- **Fehlerbehandlung:**
  - Verbindungsstatus-Anzeige
  - Troubleshooting-Dialoge
  - Automatische Verbindungsprüfung

## Konfiguration und Umgebungsvariablen

### Control Layer (config.py)

```python
# MQTT Configuration
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))

# AI Layer Configuration
AI_LAYER_URL = os.getenv("AI_LAYER_URL", "http://localhost:8001/analyze")
AI_LAYER_TIMEOUT = int(os.getenv("AI_LAYER_TIMEOUT", "5"))

# Control Layer Configuration
CONTROL_API_HOST = os.getenv("CONTROL_API_HOST", "0.0.0.0")
CONTROL_API_PORT = int(os.getenv("CONTROL_API_PORT", "8000"))
```

### AI Layer

Keine spezifischen Umgebungsvariablen, verwendet Port 8001 fest codiert.

## Datenfluss-Analyse

### Normaler Betrieb

1. **ESP32 → MQTT Broker:** Sensor-Daten (10Hz), Safety-Status (20Hz)
2. **MQTT Broker → Control Layer:** Subscribe auf Topics, Daten-Aggregation
3. **Control Layer → AI Layer:** POST /analyze mit aggregierten Daten (periodisch)
4. **AI Layer → Control Layer:** Analyse-Ergebnis mit Anomalien, Verschleiß, Empfehlungen
5. **Control Layer → HMI:** REST API für Status, Daten, AI-Analyse (2s Polling)
6. **HMI → Control Layer:** POST /control/command für Steuerungsbefehle

### Fehlerbehandlung

1. **MQTT-Verbindungsabbruch:** Automatische Reconnection mit exponentieller Backoff (1s-60s)
2. **AI-Layer-Timeout:** Konfigurierbar (Standard 5s), Error-Logging, weiter ohne AI
3. **HMI-Verbindungsfehler:** Farbcodierter Status, Fehlerdialoge mit Troubleshooting
4. **Safety-Violation:** Kommando-Ablehnung mit RuntimeError

## Code-Qualität und Tests

### Test-Coverage

- **Control Layer:** 42 Unit-Tests
- **AI Layer:** 56 Unit-Tests
- **Gesamt:** 98 Tests, 96-97% Code-Coverage
- **Test-Script:** `./test_with_coverage.sh`

### Code-Standards

- **Linting:** flake8, pylint via `./lint.sh`
- **Magic Numbers:** Alle extrahiert (47 benannte Konstanten)
- **Logging:** Standardisiert über alle Module (docs/LOGGING_STANDARDS.md)
- **Error Handling:** Dokumentiert in docs/ERROR_HANDLING.md

## Sicherheitsarchitektur

### Ebenen-basierte Sicherheit

1. **Hardware-Ebene (ESP32):**
   - Deterministische Sicherheitsüberwachung
   - Hardware-Interlocks
   - KI-frei

2. **Control Layer:**
   - Safety-Command-Validation
   - `is_system_safe()` Check vor Befehlsausführung
   - Sicherheitsstatus-Tracking

3. **AI Layer:**
   - **NUR BERATEND**
   - Keine Sicherheitsfunktionen
   - Keine Echtzeit-Kontrolle

### Offene Sicherheitsprobleme

Siehe ISSUES.md #022, #023:
- MQTT-Authentifizierung fehlt
- API-Authentifizierung fehlt
- TLS/SSL nicht implementiert

## Dokumentations-Synchronisierung

### Aktualisierte Dateien

1. **README.md:**
   - Detaillierte 4-Ebenen-Beschreibung mit Entry-Points
   - Erweiterte Hauptmerkmale
   - API-Endpunkte mit Implementierungs-Referenzen
   - Sicherheitsarchitektur präzisiert

2. **TODO.md:**
   - Status aktualisiert (98 Tests, 96-97% Coverage)
   - Abgeschlossene Tasks markiert
   - Neue Test-Kategorien hinzugefügt
   - Code-Qualität-Status aktualisiert

3. **ISSUES.md:**
   - Neue kritische Sicherheits-Issues (#022, #023)
   - Neue Enhancements (#024-#026)
   - Anzahl offener Issues dokumentiert

4. **CHANGELOG.md:**
   - Unreleased-Sektion mit Dokumentations-Updates

5. **docs/INDEX.md:**
   - Neue Sektion "Main Entry Points & Implementation"
   - System-Status mit Test-Coverage

## Empfehlungen für nächste Schritte

### Priorität 1: Sicherheit

1. MQTT-Authentifizierung implementieren
2. API-Authentifizierung hinzufügen
3. TLS/SSL für Produktionsumgebung

### Priorität 2: Monitoring

1. Prometheus-Metriken exportieren
2. Grafana-Dashboards erstellen
3. Structured Logging implementieren

### Priorität 3: Persistence

1. TimescaleDB integrieren
2. Historische Daten speichern
3. Langzeit-Trendanalyse ermöglichen

## Fazit

Die Analyse der Main-Entry-Points zeigt ein gut strukturiertes, modulares System mit klarer Trennung zwischen Sicherheitsfunktionen (Field Layer) und beratender KI (AI Layer). Die Implementierung ist produktionsreif mit hoher Test-Coverage, aber es fehlen noch kritische Sicherheitsfeatures (Authentifizierung, TLS) für den echten Produktionseinsatz.

Die Dokumentation wurde vollständig synchronisiert und spiegelt nun die tatsächliche Implementierung wider. Alle offenen Issues und TODOs sind klar dokumentiert mit Prioritäten.

---

**Dokument-Ende**
