# MODAX – Systemüberblick

**MODAX** (Modular Industrial Control System) ist ein industrielles Steuerungssystem mit 4-Ebenen-Architektur, das maschinelles Lernen für prädiktive Wartung und Optimierung integriert, während alle sicherheitskritischen Funktionen KI-frei bleiben.

---

## Kernkonzept

**Sichere Automatisierung mit beratender KI**

MODAX trennt strikt zwischen:
- **Sicherheitskritischer Steuerung** (deterministisch, KI-frei, Hardware-basiert)
- **Intelligenter Analyse** (KI-gestützt, beratend, nicht-steuernd)

Die KI-Ebene liefert Empfehlungen und Analysen, während die Steuerungsebene alle sicherheitskritischen Entscheidungen trifft. Das System kombiniert Echtzeit-Reaktionsfähigkeit mit intelligenter Langzeit-Analyse.

---

## Systemarchitektur

MODAX ist in vier hierarchische Ebenen organisiert:

### 1. Feldebene (Field Layer)

**Technologie:** ESP32 Mikrocontroller (C++/Arduino)  
**Zweck:** Echtzeit-Sensorik und Hardware-Sicherheit

**Hauptfunktionen:**
- Sensordatenerfassung (Strom, Vibration, Temperatur)
- Hardware-Sicherheitsverriegelungen (Not-Aus, Überlastschutz)
- MQTT-Datenübertragung
- Lokale Echtzeit-Reaktion

**Charakteristik:**
- ✅ Deterministisch
- ✅ KI-frei
- ✅ Hardware-basierte Sicherheit
- ✅ 10-20 Hz Betriebsfrequenz

**Entry Point:** `esp32-field-layer/src/main.cpp`

### 2. Steuerungsebene (Control Layer / Supervisory Layer)

**Technologie:** Python 3.8+ (FastAPI, paho-mqtt)  
**Zweck:** Zentrale Koordination und Datenaggregation

**Hauptfunktionen:**
- Datenaggregation von mehreren Feldgeräten
- CNC-Steuerung (G-Code, Motion Control)
- Sicherheitsvalidierung vor Befehlsausführung
- REST API für HMI
- MQTT-Kommunikation mit Feldebene
- Asynchrone KI-Anfragen

**Charakteristik:**
- ✅ Zentrale Orchestrierung
- ✅ Safety-Command-Validation
- ✅ KI-frei in kritischen Pfaden
- ✅ Fehlertoleranz und Graceful Degradation

**Entry Point:** `python-control-layer/main.py`

### 3. KI-Ebene (Analytics & ML Layer)

**Technologie:** Python 3.8+ (scikit-learn, FastAPI)  
**Zweck:** Intelligente Datenanalyse und Empfehlungen

**Hauptfunktionen:**
- Statistische Anomalieerkennung
- Verschleißvorhersage (Predictive Maintenance)
- Regelbasierte Optimierungsempfehlungen
- Trend-Analysen
- Confidence-Tracking

**Charakteristik:**
- ⚠️ **NUR BERATEND** – keine Steuerungsfunktionen
- ⚠️ Kein direkter Zugriff auf Steuerungsebene
- ✅ Asynchrone Verarbeitung
- ✅ Erklärbare Empfehlungen

**Entry Point:** `python-ai-layer/main.py`

### 4. HMI-Ebene (Human-Machine Interface)

**Technologie:** C# .NET 8.0 (Windows Forms)  
**Zweck:** Visualisierung und menschliche Entscheidungsfindung

**Hauptfunktionen:**
- Echtzeit-Dashboard (MDI-Interface)
- Sicherheitsstatus-Anzeige
- KI-Empfehlungen-Darstellung
- Steuerungsbefehl-Eingabe
- Network Scanner & Device Discovery
- Alarmierung und Ereignisprotokoll

**Charakteristik:**
- ✅ Klare Trennung: Status vs. Empfehlungen
- ✅ Benutzerbestätigung für kritische Aktionen
- ✅ Offline-fähig
- ✅ Tastaturkürzel und effiziente Bedienung

**Entry Point:** `csharp-hmi-layer/Program.cs`

---

## Datenfluss

### Bottom-Up (Sensordaten → Visualisierung)

```
Feldebene (ESP32)
    ↓ MQTT (10 Hz Sensordaten, 20 Hz Safety)
Steuerungsebene (Python)
    ↓ Time-Window-Aggregation
    ├─→ REST API → HMI (2s Updates)
    └─→ Async → KI-Ebene (Analyse)
              ↓
           REST API
              ↓
         HMI (Empfehlungen)
```

### Top-Down (Befehle → Aktorik)

```
HMI (Benutzer)
    ↓ REST API
Steuerungsebene
    ↓ Safety Validation (is_system_safe)
    ↓ MQTT
Feldebene (Hardware-Ausführung)
```

**Wichtig:** KI-Ebene ist **NICHT** im Befehls-Pfad!

---

## Kommunikationsprotokolle

### MQTT (Message Queue Telemetry Transport)

**Verwendung:** Feldebene ↔ Steuerungsebene

**Topics:**
- `modax/sensor/+/data` – Sensordaten (QoS 1)
- `modax/sensor/+/safety` – Sicherheitsstatus (QoS 1)
- `modax/control/+/command` – Steuerbefehle (QoS 1)

**Eigenschaften:**
- Asynchron, Publish-Subscribe
- Automatische Wiederverbindung
- Lose Kopplung

### REST API (HTTP/JSON)

**Verwendung:** 
- Steuerungsebene ↔ HMI
- KI-Ebene ↔ Steuerungsebene

**Protokoll:** HTTP/1.1, JSON  
**Framework:** FastAPI

**Vorteile:**
- Synchron, Request-Response
- Einfache Integration
- Standardisiert

---

## Hauptmerkmale

### 🛡️ Sicherheit zuerst

- Alle sicherheitskritischen Funktionen bleiben KI-frei
- Hardware-Sicherheitsverriegelungen auf ESP32
- Deterministische Echtzeit-Reaktion
- Mehrschichtige Sicherheitsvalidierung
- Not-Aus hat absolute Priorität

### 🤖 KI-Integration (beratend)

- Anomalieerkennung (Z-Score-basiert)
- Verschleißvorhersage (Stress-Akkumulation)
- Optimierungsempfehlungen (regelbasiert)
- Confidence-Tracking für jede Analyse
- Bereit für ONNX ML-Modelle (zukünftig)

### 📊 Echtzeit-Überwachung

- 10 Hz Sensordatenerfassung
- 20 Hz Sicherheitsüberwachung
- 2s HMI-Aktualisierung
- MQTT-basierte Kommunikation
- Time-Window-Aggregation

### 🏭 CNC-Maschinen-Funktionalität

- Vollständiger ISO 6983 G-Code Parser (150+ Codes)
- Motion Control (Linear, Circular, Helikal)
- Werkzeugverwaltung (24-Platz-Magazin)
- Koordinatensysteme (G54-G59, erweitert)
- Festzyklen (Bohren, Fräsen, Tappen)
- Spindel- und Kühlmittelsteuerung

### 🔌 Industrielle Kommunikation

- RS485/Modbus RTU für VFD-Steuerung
- MIDI Audio Feedback
- Pendant Device Support (MPG/Handwheel)
- Slave Board I2C für verteilte I/O
- OPC UA (dokumentiert, Implementation geplant)

### 🔧 Modular & Skalierbar

- Mehrere Feldgeräte unterstützt
- Horizontale Skalierung möglich
- Cloud-bereit
- Erweiterbare Architektur
- Docker-Deployment

---

## Technologie-Stack

| Ebene | Sprache | Frameworks/Libs | Laufzeit |
|-------|---------|-----------------|----------|
| **Feldebene** | C++ | Arduino, PlatformIO | ESP32 |
| **Steuerung** | Python 3.8+ | FastAPI, paho-mqtt | Linux/Windows |
| **KI** | Python 3.8+ | scikit-learn, NumPy | Linux/Windows |
| **HMI** | C# .NET 8.0 | Windows Forms | Windows |

**Zusätzliche Tools:**
- MQTT Broker: Mosquitto / HiveMQ
- Container: Docker, Docker Compose
- Orchestration: Kubernetes (Helm Charts)
- CI/CD: GitHub Actions

---

## Typische Anwendungsfälle

### 1. CNC-Maschinen-Steuerung

**Szenario:** Fräsmaschine mit prädiktiver Wartung

- Feldebene erfasst Motorströme, Vibrationen, Temperaturen
- Steuerungsebene führt G-Code aus, koordiniert Achsen
- KI-Ebene erkennt Anomalien, prognostiziert Werkzeugverschleiß
- HMI zeigt Maschinenstatus und Wartungsempfehlungen

### 2. Produktionslinie-Überwachung

**Szenario:** Mehrere Maschinen in Produktionslinie

- Mehrere ESP32 an verschiedenen Maschinen
- Zentrale Steuerungsebene aggregiert Daten
- KI-Ebene analysiert Gesamtleistung, identifiziert Bottlenecks
- HMI zeigt Flottenübersicht und Optimierungsvorschläge

### 3. Wartungsplanung

**Szenario:** Prädiktive Wartung für Maschinenpark

- Kontinuierliche Datenerfassung über Wochen/Monate
- KI-Ebene lernt Baseline, erkennt Abweichungen
- Vorhersage von Ausfällen Tage/Wochen im Voraus
- Wartung wird geplant, bevor Ausfall eintritt

### 4. Qualitätskontrolle

**Szenario:** Erkennung von Prozessabweichungen

- Sensordaten während Produktion
- KI erkennt Muster, die auf Qualitätsprobleme hindeuten
- Frühwarnung an Bediener
- Prozessparameter werden angepasst

---

## System-Skalierung

### Kleine Deployment

**Konfiguration:**
- 1-5 ESP32 Feldgeräte
- Alle Ebenen auf einem Server/PC
- SQLite Datenbank
- Lokales MQTT

**Anwendung:** Einzelmaschine, Hobbyist, Entwicklung

### Mittlere Deployment

**Konfiguration:**
- 10-50 Feldgeräte
- Ebenen auf separaten Servern/Containern
- PostgreSQL/TimescaleDB
- Dedizierter MQTT Broker
- Reverse Proxy (Nginx)

**Anwendung:** Kleine Produktionslinie, mehrere Maschinen

### Große Deployment

**Konfiguration:**
- 50-500+ Feldgeräte
- Kubernetes-Cluster
- TimescaleDB mit Replikation
- MQTT-Cluster (HiveMQ)
- Load Balancing
- Monitoring Stack (Prometheus, Grafana)

**Anwendung:** Große Fabrik, Flottenmanagement, Cloud

---

## Sicherheitskonzept

### Defense in Depth

**Ebene 1 – Hardware:**
- Physische Sicherheitsverriegelungen
- Not-Aus-Schaltung
- Hardware-Watchdog

**Ebene 2 – Firmware (ESP32):**
- Deterministische Sicherheitslogik
- Überwachung von Grenzwerten
- Automatische Abschaltung

**Ebene 3 – Software (Control Layer):**
- Safety-Command-Validation
- Plausibilitätsprüfungen
- Fehlertoleranz

**Ebene 4 – Netzwerk:**
- Segmentierung (OT/IT-Trennung)
- Firewalls
- Zugriffskontrolle (RBAC geplant)

**Ebene 5 – Prozess:**
- Schulung der Bediener
- Standard Operating Procedures (SOPs)
- Incident Response Plan

### KI-Sicherheitsbarriere

**Regel:** KI darf NIEMALS direkt steuern

**Durchsetzung:**
- Architektonische Trennung (separater Service)
- Keine MQTT-Publish-Rechte für Steuerbefehle
- Empfehlungen werden geloggt, aber nicht ausgeführt
- Mensch oder deterministische Logik validiert Empfehlungen

---

## Limitierungen

### Was MODAX KANN:

✅ CNC-Maschinen steuern (Fräsen, Drehen, Bohren)  
✅ Sensordaten in Echtzeit erfassen  
✅ Anomalien erkennen  
✅ Wartungsbedarf prognostizieren  
✅ Optimierungsempfehlungen geben  
✅ Mehrere Maschinen koordinieren  
✅ Industrielle Protokolle sprechen (Modbus, MQTT)

### Was MODAX NICHT KANN:

❌ SIL 3/4 Safety-Anforderungen erfüllen (aktuell)  
❌ 5-Achsen-Kinematik (noch nicht)  
❌ EtherCAT/PROFINET (noch nicht)  
❌ Autonome Entscheidungen in sicherheitskritischen Bereichen  
❌ Online-Learning im Produktionsbetrieb  
❌ Garantierte Echtzeitfähigkeit <1ms

---

## Nächste Schritte

**Für neue Nutzer:**
1. Lesen Sie [docs/02-system-architecture/layer-model.md](../02-system-architecture/layer-model.md)
2. Siehe [docs/SETUP.md](../SETUP.md) für Installation
3. Folgen Sie [docs/QUICK_REFERENCE.md](../QUICK_REFERENCE.md)

**Für Entwickler:**
1. Lesen Sie [docs/ARCHITECTURE.md](../ARCHITECTURE.md)
2. Siehe [docs/API.md](../API.md) für API-Details
3. Konsultieren Sie [.github/copilot-instructions.md](../../.github/copilot-instructions.md)

**Für Entscheider:**
1. Lesen Sie [docs/00-meta/vision.md](../00-meta/vision.md)
2. Siehe [docs/00-meta/compliance-scope.md](../00-meta/compliance-scope.md)
3. Prüfen Sie [docs/00-meta/roadmap.md](../00-meta/roadmap.md)

---

**Weitere Informationen:**
- [Systemprinizip](system-principles.md)
- [Glossar](glossary.md)
- [Annahmen](assumptions.md)
- [4-Ebenen-Modell](../02-system-architecture/layer-model.md)
