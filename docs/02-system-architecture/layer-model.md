# MODAX – 4-Ebenen-Architekturmodell

Dieses Dokument beschreibt das zentrale Architekturmodell von MODAX: die strikte Trennung in vier hierarchische Ebenen mit klar definierten Verantwortlichkeiten und Kommunikationswegen.

---

## Überblick

MODAX folgt einem **hierarchischen 4-Ebenen-Modell**, inspiriert von klassischen Automatisierungspyramiden, aber angepasst an moderne IoT- und KI-Anforderungen.

```
┌─────────────────────────────────────────────────────────┐
│  Ebene 4: HMI-Ebene (Interface Layer)                  │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Visualisierung, Bedienerentscheidungen          │   │
│  │ Technologie: C# .NET 8.0 / Windows Forms        │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                         ↕ REST API
┌─────────────────────────────────────────────────────────┐
│  Ebene 3: KI-Ebene (Analytics & ML Layer)              │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Analyse, Prognose, Empfehlungen (BERATEND)     │   │
│  │ Technologie: Python 3.8+ / scikit-learn        │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                         ↕ REST API (Async)
┌─────────────────────────────────────────────────────────┐
│  Ebene 2: Steuerungsebene (Control/Supervisory Layer)  │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Koordination, CNC-Steuerung, Safety-Validation │   │
│  │ Technologie: Python 3.8+ / FastAPI / MQTT      │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                         ↕ MQTT
┌─────────────────────────────────────────────────────────┐
│  Ebene 1: Feldebene (Field Layer)                      │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Sensoren, Aktoren, Hardware-Safety             │   │
│  │ Technologie: ESP32 / C++ / Arduino             │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## Ebene 1: Feldebene (Field Layer)

### Zweck

Echtzeit-Datenerfassung von Sensoren und Hardware-basierte Sicherheitsfunktionen.

### Technologie-Stack

- **Hardware:** ESP32 Mikrocontroller (Dual-Core Xtensa LX6, 240 MHz)
- **Programmiersprache:** C++ (Arduino Framework)
- **Entwicklungsumgebung:** PlatformIO
- **Kommunikation:** WiFi (802.11 b/g/n), MQTT Client

### Hauptverantwortlichkeiten

1. **Sensordatenerfassung**
   - Strom (ACS712): Motorlast-Überwachung
   - Vibration (MPU6050): Unwucht-Erkennung, Kollisionsdetektion
   - Temperatur (DS18B20): Überhitzungsschutz
   - Sampling-Rate: 10 Hz (Daten), 20 Hz (Safety)

2. **Hardware-Sicherheitsfunktionen**
   - Not-Aus (Emergency Stop): Hardware-Interrupt
   - Überlastschutz: Automatische Abschaltung bei Überstrom
   - Temperaturüberwachung: Abschaltung bei Überhitzung
   - Hardware-Watchdog: Automatischer Reset bei Firmware-Crash

3. **Lokale Echtzeit-Reaktion**
   - Sicherheitschecks alle 50 ms
   - Sofortige Reaktion auf kritische Zustände
   - Keine Abhängigkeit von Netzwerk für Safety-Funktionen

4. **Datenübertragung**
   - MQTT Publish: Sensordaten, Sicherheitsstatus
   - MQTT Subscribe: Steuerbefehle (validiert vor Ausführung)
   - QoS 1 (At Least Once) für alle kritischen Nachrichten

### Architektur-Constraints

**Erlaubt:**
- ✅ Einfache Berechnungen (Mittelwert, Min/Max)
- ✅ Schwellenwert-Vergleiche
- ✅ Zustandsmaschinen (State Machines)
- ✅ Hardware-Interlocks

**Verboten:**
- ❌ KI/ML-Algorithmen (zu komplex, nicht deterministisch)
- ❌ Cloud-Zugriffe (Latenz, Abhängigkeit)
- ❌ Datenbank-Zugriffe (Overhead)
- ❌ Komplexe Berechnungen (begrenzte CPU)

### Datenmodell

**MQTT Topics:**
- `modax/sensor/{device_id}/data` → Sensordaten (10 Hz)
- `modax/sensor/{device_id}/safety` → Safety-Status (20 Hz)
- `modax/control/{device_id}/command` ← Steuerbefehle

**Payload-Format:** JSON (einfach, menschenlesbar)

```json
{
  "device_id": "esp32_001",
  "timestamp": 1703678400,
  "current": 2.5,
  "vibration": 0.8,
  "temperature": 45.2,
  "safety_status": "OK"
}
```

### Fehlerbehandlung

- **Sensor-Fehler:** Letzte gültige Werte nutzen + Fehler melden
- **WiFi-Verlust:** Lokale Safety-Funktionen bleiben aktiv
- **MQTT-Disconnect:** Automatische Wiederverbindung (Exponential Backoff)
- **Firmware-Crash:** Watchdog-Reset, Gerät startet neu

### Performance

- **Boot-Time:** <5 Sekunden
- **Sensor-Sampling:** 10 Hz (100 ms pro Sample)
- **Safety-Check-Rate:** 20 Hz (50 ms)
- **MQTT-Latenz:** <20 ms (LAN)
- **Speicher:** ~100 KB RAM-Nutzung, ~500 KB Flash

---

## Ebene 2: Steuerungsebene (Control / Supervisory Layer)

### Zweck

Zentrale Koordination, Datenaggregation, CNC-Steuerung und Sicherheitsvalidierung.

### Technologie-Stack

- **Programmiersprache:** Python 3.8+
- **Web-Framework:** FastAPI (async)
- **MQTT-Client:** paho-mqtt
- **Async-Framework:** asyncio
- **Datenstrukturen:** NumPy (optional, für Performance)

### Hauptverantwortlichkeiten

1. **Datenaggregation**
   - Empfang von Daten von mehreren Feldgeräten
   - Time-Window-Aggregation (konfigurierbares Fenster, z.B. 5s)
   - Statistische Auswertung (Mittelwert, Std-Dev, Min/Max)
   - Datenpuffer für historische Abfragen

2. **CNC-Steuerung**
   - G-Code-Parsing (ISO 6983, 150+ Codes)
   - Motion Control (Linear G0/G1, Circular G2/G3, Helikal)
   - Werkzeugverwaltung (24-Platz-Magazin, automatischer Wechsel)
   - Koordinatensysteme (G54-G59, G54.1)
   - Spindel- und Kühlmittelsteuerung

3. **Sicherheitsvalidierung**
   - `is_system_safe()`: Zentrale Safety-Funktion
   - Validierung aller Steuerbefehle vor Weiterleitung
   - Überwachung von Grenzwerten
   - Alarm-Management

4. **API-Bereitstellung**
   - REST API für HMI (FastAPI, Port 8000)
   - 8 Hauptendpunkte (Status, Devices, Data, Safety, AI-Analysis, Commands)
   - OpenAPI/Swagger-Dokumentation
   - Asynchrone Verarbeitung

5. **KI-Integration (asynchron)**
   - Anfragen an KI-Ebene (REST API, nicht-blockierend)
   - Timeout-Management (5s default)
   - Caching von KI-Empfehlungen
   - Logging aller KI-Interaktionen

### Architektur-Constraints

**Erlaubt:**
- ✅ Komplexe Orchestrierung
- ✅ Datenbank-Zugriffe (zukünftig)
- ✅ Externe API-Calls (asynchron)
- ✅ Datei-I/O (Konfiguration, Logs)

**Verboten:**
- ❌ KI-Algorithmen in Safety-Pfaden
- ❌ Automatische Ausführung von KI-Empfehlungen
- ❌ Blockierende I/O in kritischen Pfaden
- ❌ Unvalidierte Befehle an Feldebene

### Datenfluss

**Eingang:**
- MQTT ← Feldebene (Sensordaten, Safety-Status)
- REST ← HMI (Benutzerbefehle, Abfragen)
- REST ← KI-Ebene (Empfehlungen, Analysen)

**Ausgang:**
- MQTT → Feldebene (Steuerbefehle)
- REST → HMI (Aggregierte Daten, Status)
- REST → KI-Ebene (Rohdaten für Analyse)

### Fehlerbehandlung

- **MQTT-Ausfall:** Automatische Wiederverbindung, Puffer für Nachrichten
- **API-Fehler:** HTTP Status Codes, strukturierte Fehlerantworten
- **KI-Timeout:** Fallback auf Default-Verhalten, Warnung loggen
- **Sensor-Ausfall:** Graceful Degradation, Fehler-Flags setzen

### Performance

- **API-Latenz:** <100 ms (p95)
- **Throughput:** 100+ Requests/s
- **MQTT-Processing:** <10 ms pro Nachricht
- **Speicher:** ~200 MB (typisch)

---

## Ebene 3: KI-Ebene (Analytics & ML Layer)

### Zweck

**Beratende** Datenanalyse, Prognosen und Optimierungsempfehlungen – OHNE Steuerungsfunktionen.

### Technologie-Stack

- **Programmiersprache:** Python 3.8+
- **ML-Framework:** scikit-learn (aktuell), ONNX Runtime (geplant)
- **Web-Framework:** FastAPI
- **Datenverarbeitung:** NumPy, pandas

### Hauptverantwortlichkeiten

1. **Anomalieerkennung**
   - Z-Score-basierte statistische Analyse
   - Erkennung von Ausreißern (Strom, Vibration, Temperatur)
   - Adaptive Schwellenwerte (Baseline-Learning)
   - Confidence-Level für jede Erkennung

2. **Verschleißvorhersage**
   - Stress-Akkumulation basierend auf Betriebsparametern
   - Empirische Restlebenszeit-Schätzung
   - Wartungsintervall-Empfehlungen
   - Historischer Trend-Vergleich

3. **Optimierungsempfehlungen**
   - Regelbasiertes Expertensystem
   - Parameter-Vorschläge (Vorschub, Drehzahl)
   - Energie-Effizienz-Tipps
   - Qualitätsverbesserungen

4. **Modell-Management (zukünftig)**
   - ONNX-Modell-Loading
   - Modell-Versioning
   - A/B-Testing von Modellen
   - Offline-Training-Pipeline

### Architektur-Constraints

**Erlaubt:**
- ✅ Komplexe ML-Algorithmen
- ✅ Große Datenmengen verarbeiten
- ✅ Lange Berechnungszeiten (asynchron)
- ✅ Experimentelle Features

**Verboten:**
- ❌ **DIREKTE Steuerungsbefehle**
- ❌ **Zugriff auf MQTT Control Topics**
- ❌ **Automatische Parameteränderung**
- ❌ **Sicherheitsentscheidungen**
- ❌ **Echtzeit-kritische Pfade**

### API-Design

**Endpoint:** `POST /analyze`

**Request:**
```json
{
  "device_id": "esp32_001",
  "current": [2.1, 2.3, 2.5],
  "vibration": [0.7, 0.8, 0.9],
  "temperature": [44, 45, 46]
}
```

**Response:**
```json
{
  "anomaly_detected": true,
  "anomaly_types": ["vibration_high"],
  "wear_level": 0.45,
  "remaining_life_hours": 120,
  "recommendations": [
    {
      "type": "maintenance",
      "priority": "medium",
      "action": "Inspect bearings",
      "confidence": 0.75
    }
  ],
  "confidence": 0.82,
  "timestamp": "2025-12-27T10:30:00Z"
}
```

### Sicherheitsbarriere

**Wie wird verhindert, dass KI steuert?**

1. **Architektonisch:** Separater Process/Container, keine MQTT-Pub-Rechte für Control
2. **API-Design:** Nur Read-Operationen auf Sensordaten
3. **Logging:** Alle Empfehlungen werden geloggt (Audit-Trail)
4. **Validierung:** Control Layer ignoriert unvalidierte Empfehlungen

### Fehlerbehandlung

- **Modell-Fehler:** Fallback auf einfachere Algorithmen
- **Timeout:** Control Layer wartet nicht ewig (5s default)
- **Ungültige Daten:** Fehler zurückgeben, nicht crashen
- **Out-of-Memory:** Datenmengen limitieren, Warnung

### Performance

- **Analyse-Latenz:** <1s (typisch), <5s (max)
- **Throughput:** 10-50 Analysen/s
- **Speicher:** ~500 MB (je nach Modellgröße)

---

## Ebene 4: HMI-Ebene (Human-Machine Interface)

### Zweck

Visualisierung des Systemzustands und Ermöglichung menschlicher Entscheidungen.

### Technologie-Stack

- **Programmiersprache:** C# .NET 8.0
- **UI-Framework:** Windows Forms (MDI)
- **HTTP-Client:** HttpClient (async)
- **Plattform:** Windows 10/11

### Hauptverantwortlichkeiten

1. **Visualisierung**
   - Echtzeit-Dashboard (MDI mit Tabs)
   - Sicherheitsstatus (farbcodiert)
   - Sensordaten-Trends
   - KI-Empfehlungen-Anzeige
   - Alarme und Ereignisse

2. **Benutzereingaben**
   - Steuerungsbefehle (Start, Stop, Pause)
   - Parameteränderungen
   - G-Code-Eingabe (MDI-Mode)
   - Konfiguration

3. **Entscheidungsunterstützung**
   - Klare Trennung: **Status** (links) vs. **Empfehlungen** (rechts)
   - Confidence-Level für KI-Vorschläge
   - Bediener entscheidet über Ausführung
   - History und Trends

4. **Network Scanner**
   - Automatische Geräteerkennung (CIDR)
   - Port-Scanning
   - Device-Type-Detection

### UI-Design-Prinzipien

**Sicherheit:**
- Kritische Aktionen erfordern Bestätigung
- Farbcodierung (Grün=OK, Gelb=Warnung, Rot=Fehler)
- Klare Alarmierung

**Usability:**
- Tastaturkürzel (F1, Ctrl+D, Ctrl+N, etc.)
- Intuitive Navigation
- Offline-Fähigkeit (Fehlermeldungen bei Verbindungsverlust)

**Trennung:**
- **Links:** Maschinenstatus, Sensordaten (Fakten)
- **Rechts:** KI-Empfehlungen, Optimierungen (Vorschläge)
- **Unten:** Logs, Ereignisse

### Fehlerbehandlung

- **API-Ausfall:** Offline-Modus, letzte bekannte Werte anzeigen
- **Timeout:** Benutzerfreundliche Fehlermeldung
- **Ungültige Eingaben:** Validierung vor Absenden
- **Crash:** Exception-Handler, Fehlerreport

### Performance

- **Update-Rate:** 0.5 Hz (2s) – konfigurierbar
- **Startup-Time:** <3 Sekunden
- **Speicher:** ~100 MB

---

## Kommunikationsmatrix

| Von → Nach | Feldebene | Steuerung | KI | HMI |
|------------|-----------|-----------|----|----|
| **Feldebene** | - | MQTT ↑ | - | - |
| **Steuerung** | MQTT ↓ | - | REST ↑ | REST ↑ |
| **KI** | - | REST ↓ | - | - |
| **HMI** | - | REST ↓ | - | - |

**Legende:**
- ↑ = Daten fließen nach oben
- ↓ = Befehle fließen nach unten
- MQTT = Asynchron, Pub/Sub
- REST = Synchron, Request/Response

---

## Sicherheitskonzept der Ebenen

### Ebene 1 (Feldebene): Hardware-Safety

- **SIL-Potential:** SIL 1-2 (mit Zertifizierung)
- **Reaktionszeit:** <10 ms
- **Fehlertoleranz:** Hardware-Watchdog
- **Determinismus:** Vollständig

### Ebene 2 (Steuerung): Software-Safety

- **SIL-Potential:** SIL 1 (mit Validierung)
- **Reaktionszeit:** <100 ms
- **Fehlertoleranz:** Graceful Degradation
- **Determinismus:** In kritischen Pfaden

### Ebene 3 (KI): Keine Safety-Funktion

- **SIL-Potential:** N/A (nicht safety-relevant)
- **Reaktionszeit:** <5 s (nicht zeitkritisch)
- **Fehlertoleranz:** Kann ausfallen ohne Systemausfall
- **Determinismus:** Nicht erforderlich

### Ebene 4 (HMI): Mensch als Safety-Funktion

- **SIL-Potential:** N/A (Bediener entscheidet)
- **Reaktionszeit:** Menschlich (Sekunden)
- **Fehlertoleranz:** Offline-Fähigkeit
- **Determinismus:** Nicht erforderlich

---

## Deployment-Topologien

### Kleine Deployment (All-in-One)

```
┌──────────────────────────────┐
│      Single PC/Server         │
│  ┌────────┐  ┌────────┐      │
│  │Control │  │   AI   │      │
│  └────────┘  └────────┘      │
│  ┌────────────────────┐      │
│  │   MQTT Broker      │      │
│  └────────────────────┘      │
└──────────────────────────────┘
         ↕ MQTT
┌──────────────────────────────┐
│      ESP32 Feldgeräte         │
└──────────────────────────────┘
```

### Große Deployment (Kubernetes)

```
┌────────────────────────────────────┐
│     Kubernetes Cluster              │
│  ┌─────────┐ ┌─────────┐          │
│  │Control  │ │Control  │ (Replicas)│
│  │ Pod 1   │ │ Pod 2   │          │
│  └─────────┘ └─────────┘          │
│  ┌─────────┐ ┌─────────┐          │
│  │ AI Pod  │ │MQTT Svc │          │
│  └─────────┘ └─────────┘          │
│  ┌──────────────────────┐         │
│  │ TimescaleDB          │         │
│  └──────────────────────┘         │
└────────────────────────────────────┘
         ↕ MQTT (Load Balanced)
┌────────────────────────────────────┐
│      50+ ESP32 Feldgeräte          │
└────────────────────────────────────┘
```

---

## Zusammenfassung

Das 4-Ebenen-Modell von MODAX bietet:

✅ **Klare Verantwortlichkeiten:** Jede Ebene hat definierte Aufgaben  
✅ **Sicherheit durch Trennung:** KI kann nicht steuern  
✅ **Wartbarkeit:** Ebenen einzeln aktualisierbar  
✅ **Skalierbarkeit:** Horizontal skalierbar  
✅ **Testbarkeit:** Ebenen einzeln testbar  
✅ **Flexibilität:** Implementierungen austauschbar  

**Kernprinzip:** Die Architektur **erzwingt** durch Design, dass KI niemals direkt steuern kann. Dies ist keine Konvention, sondern eine architektonische Invariante.

---

**Referenzen:**
- [Datenfluss](data-flow.md)
- [Control Boundaries](control-boundaries.md)
- [ADR-0002: No AI in Control](../09-decisions/adr-0002-no-ai-in-control.md)
