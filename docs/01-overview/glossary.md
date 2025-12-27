# MODAX - Glossar / Glossary

**Version:** 0.3.0  
**Letzte Aktualisierung:** 2025-12-07  
**Zweck:** Umfassendes Glossar aller technischen Begriffe im MODAX-System für das Handbuch

---

## A

### AI Layer (KI-Ebene)
Die intelligente Analyseschicht des MODAX-Systems. Führt statistische Anomalieerkennung, Verschleißvorhersage und Optimierungsempfehlungen durch. **WICHTIG:** Nur beratende Funktion, keine Sicherheitsentscheidungen.

### Anomalieerkennung (Anomaly Detection)
Z-Score-basierte statistische Analyse zur Erkennung abnormaler Sensordaten-Muster in Strom, Vibration und Temperatur.

### API (Application Programming Interface)
REST-basierte Schnittstellen für die Kommunikation zwischen den MODAX-Ebenen:
- Control Layer API: Port 8000
- AI Layer API: Port 8001

### API Key
Authentifizierungsschlüssel für den Zugriff auf API-Endpunkte. Format: `X-API-Key` Header.

### Asynchrone Operation
Nicht-blockierende Operation, die im Hintergrund ausgeführt wird (z.B. KI-Analyse-Anfragen).

---

## B

### Baseline Learning
Adaptive Schwellenwerte basierend auf historischen Daten zur Verbesserung der Anomalieerkennung.

### Backoff (Exponentielles)
Strategie zur Wiederverbindung mit exponentiell steigenden Wartezeiten (1s, 2s, 4s, 8s, ..., max 60s).

### Batch Processing
Verarbeitung mehrerer Datensätze in einem Durchgang zur Performance-Optimierung.

---

## C

### CNC (Computer Numerical Control)
Computergesteuerte numerische Maschinensteuerung. MODAX unterstützt vollständige CNC-Funktionalität.

### CNC Controller
Zentrale Steuerungseinheit für CNC-Maschinen. Verwaltet Betriebsmodi, Achsenpositionen, Werkzeuge und Sicherheit.

### CNC Cycles (Festzyklen)
Vordefinierte Bearbeitungszyklen:
- **Bohrzyklen:** G81-G89, G73 (Tieflochbohren)
- **Fräszyklen:** G12/G13 (Kreis-Taschenfräsen)
- **Gewindezyklen:** G84 (Gewindebohren), G76 (Threading)

### Confidence Level
Vertrauensniveau für KI-Analysen (0.0-1.0). Höhere Werte bedeuten verlässlichere Empfehlungen.

### Control Layer (Steuerungsebene)
Zentrale Koordinationsebene. Aggregiert Daten von Feldgeräten, koordiniert mit KI-Ebene, stellt REST API bereit.

### Coordinate System (Koordinatensystem)
- **G53:** Maschinen-Koordinatensystem
- **G54-G59:** Werkstück-Koordinatensysteme
- **G54.1 P1-P300:** Erweiterte Koordinatensysteme

### Coolant (Kühlmittel)
Kühlmittelsystem-Modi:
- **M07:** Nebel-Kühlmittel (Mist)
- **M08:** Flut-Kühlmittel (Flood)
- **M09:** Kühlmittel aus
- **M50:** Hochdruck-Kühlmittel
- **M88/M89:** Through-Spindle Coolant

---

## D

### Data Aggregation (Datenaggregation)
Statistische Verarbeitung von Sensor-Rohdaten über konfigurierbare Zeitfenster (z.B. 10s). Berechnet Durchschnitt, Min, Max, Standardabweichung.

### Data Persistence (Datenpersistenz)
Langzeitspeicherung von Sensordaten in TimescaleDB für historische Analysen und Reporting.

### Digital Twin
Virtuelle Repräsentation einer physischen Maschine zur Simulation und Optimierung (geplant für Phase 4).

### Docker
Containerisierungstechnologie für MODAX-Deployment. Siehe `docker-compose.yml`.

---

## E

### ESP32
Mikrocontroller für die Feldebene. Führt Echtzeit-Sensordatenerfassung und Hardware-Sicherheitsüberwachung durch.

### EtherCAT
Industrielles Echtzeit-Ethernet-Protokoll (geplant für Phase 4).

### Event-Driven Architecture
Architektur-Pattern basierend auf MQTT Pub/Sub für lose Kopplung zwischen Komponenten.

---

## F

### FastAPI
Python-Web-Framework für REST APIs in Control Layer und AI Layer.

### Feed Rate (Vorschubgeschwindigkeit)
Bewegungsgeschwindigkeit des Werkzeugs in mm/min (G94) oder mm/Umdrehung (G95).

### Feed Override
Prozentuale Anpassung der programmierten Vorschubgeschwindigkeit (0-150%). M36/M37 für Bereichsbegrenzung.

### Feldebene (Field Layer)
Unterste Ebene des MODAX-Systems. ESP32-basierte Hardware für Sensordatenerfassung und Sicherheit.

### Festzyklus
Siehe **CNC Cycles**

---

## G

### G-Code
ISO 6983 Standard für CNC-Programmierung. MODAX unterstützt 150+ G/M-Codes plus herstellerspezifische Erweiterungen.

### G-Code Parser
Modul zur Analyse und Interpretation von G-Code-Befehlen. Unterstützt Makros, Variablen und Kontrollstrukturen.

### Grafana
Visualisierungs-Tool für Monitoring-Dashboards (siehe docs/MONITORING.md).

---

## H

### Hardware Interlocks
Physische Sicherheitsverriegelungen auf ESP32-Ebene für Not-Aus und Überlastschutz.

### High Availability (Hochverfügbarkeit)
System-Design für minimale Ausfallzeiten durch Redundanz und Failover-Mechanismen.

### HMI (Human Machine Interface)
Benutzeroberfläche in C#/.NET für Überwachung und Steuerung. Aktualisiert alle 2 Sekunden.

---

## I

### Industry 4.0
Vierte industrielle Revolution mit Fokus auf Vernetzung, Datenanalyse und autonome Systeme. Siehe docs/ADVANCED_CNC_INDUSTRY_4_0.md.

### Interpolation
Bahnberechnung zwischen Punkten:
- **Linear (G01):** Gerade Linie
- **Circular (G02/G03):** Kreisbogen
- **Helical:** Spirale (Kreis + Z-Achse)
- **NURBS (G05):** Freiformflächen

---

## J

### JSON (JavaScript Object Notation)
Datenformat für API-Kommunikation und Konfiguration.

### JWT (JSON Web Token)
Token-basierte Authentifizierung (geplant für Sicherheits-Enhancement).

---

## K

### KI-frei (AI-free)
Designprinzip: Alle sicherheitskritischen Funktionen bleiben ohne KI-Beteiligung.

---

## L

### Logging
Strukturiertes Protokollieren von System-Events. Siehe docs/LOGGING_STANDARDS.md.

### Log-Level
Schweregrad von Log-Nachrichten: DEBUG, INFO, WARNING, ERROR, CRITICAL.

---

## M

### M-Code
Maschinen-Steuerungsbefehle (z.B. M03=Spindel CW, M06=Werkzeugwechsel, M30=Programmende).

### Macro (Makro)
Wiederverwendbare G-Code-Unterroutine mit Parametern. G65/G66/G67 für Aufrufe.

### MQTT (Message Queuing Telemetry Transport)
Leichtgewichtiges Pub/Sub-Messaging-Protokoll für IoT. Broker läuft auf Port 1883.

### Motion Controller
Modul für Bahnplanung und Interpolation. Berechnet Bewegungen zwischen Punkten.

---

## N

### NURBS (Non-Uniform Rational B-Splines)
Mathematische Darstellung von Freiformflächen für komplexe Geometrien (G05).

---

## O

### OPC UA (Open Platform Communications Unified Architecture)
Industriestandard-Protokoll für Maschinen-zu-Maschinen-Kommunikation. Siehe docs/OPC_UA_INTEGRATION.md.

### Optimizer (Optimierer)
KI-Komponente für regelbasierte Empfehlungen zur Prozessoptimierung.

---

## P

### Prometheus
Open-Source Monitoring-System für Metriken-Erfassung und Alerting.

### Protobuf (Protocol Buffers)
Binäres Serialisierungsformat für effiziente MQTT-Nachrichten (optional).

### Pub/Sub (Publish/Subscribe)
Messaging-Pattern: Publisher senden Nachrichten zu Topics, Subscriber empfangen sie.

### Purdue Model
Referenzmodell für industrielle Netzwerk-Architektur mit OT/IT-Trennung. Siehe docs/NETWORK_ARCHITECTURE.md.

---

## Q

### Queue (Warteschlange)
FIFO-Datenstruktur für asynchrone Nachrichtenverarbeitung.

---

## R

### Rate Limiting
Begrenzung der API-Anfragen pro Zeiteinheit zum Schutz vor Überlastung.

### REST (Representational State Transfer)
Architektur-Stil für Web-APIs. Verwendet HTTP-Methoden: GET, POST, PUT, DELETE.

### Ring Buffer
Zirkulärer Puffer mit fester Größe für effiziente Datenspeicherung ohne Reallokation.

---

## S

### Safety (Sicherheit)
Oberste Priorität im MODAX-Design. Mehrschichtig: Hardware → Control Layer → HMI.

### Sensor Data (Sensordaten)
Messwerte von Feldgeräten:
- **current:** Motorstrom (A)
- **vibration:** Schwingung (mm/s²)
- **temperature:** Temperatur (°C)

### Spindle (Spindel)
Hauptspindel der CNC-Maschine:
- **M03:** Rechtsdrehen (CW)
- **M04:** Linksdrehen (CCW)
- **M05:** Spindel stoppen
- **M19:** Spindelorientierung

### Stress Accumulation
Kumulative Belastung eines Systems zur Verschleißvorhersage.

---

## T

### Threading (Gewindeschneiden)
Herstellung von Gewinden:
- **G33:** Gewindeschneiden (einfach)
- **G76:** Mehrgängiges Gewinde
- **G84.2/84.3:** Starr-Gewindebohren

### TimescaleDB
PostgreSQL-Erweiterung für Zeitreihendaten. Optimiert für Sensor-Datenbank.

### Time Window
Zeitfenster für Datenaggregation (Standard: 10 Sekunden).

### Tool Manager (Werkzeugverwaltung)
Verwaltet Werkzeugmagazin (24 Plätze), Werkzeugdaten und automatischen Wechsel.

### Tool Offset (Werkzeugkorrektur)
Kompensation für Werkzeuglänge (G43/G44/G49) und Radius (G41/G42/G40).

---

## U

### Uvicorn
ASGI-Server für FastAPI-Anwendungen.

---

## V

### Verschleißvorhersage (Wear Prediction)
Empirisches Modell zur Vorhersage der Restlebensdauer basierend auf Stress-Akkumulation.

---

## W

### WebSocket
Bidirektionales Kommunikations-Protokoll für Echtzeit-Updates zwischen Server und Client.

### Werkzeug
CNC-Werkzeug mit Eigenschaften:
- **tool_number:** Nummer (1-24)
- **diameter:** Durchmesser (mm)
- **length:** Länge (mm)
- **type:** Art (mill, drill, tap, boring)

### Work Offset (Nullpunktverschiebung)
Verschiebung vom Maschinen-Nullpunkt zum Werkstück-Nullpunkt (G54-G59).

---

## X

### X-Axis (X-Achse)
Hauptachse der CNC-Maschine (typischerweise horizontal, längs).

---

## Y

### Y-Axis (Y-Achse)
Querachse der CNC-Maschine (typischerweise horizontal, quer).

---

## Z

### Z-Axis (Z-Achse)
Vertikalachse der CNC-Maschine (typischerweise vertikal).

### Z-Score
Statistisches Maß für Abweichung vom Mittelwert in Standardabweichungen. Verwendet für Anomalieerkennung.

---

## Symbole & Abkürzungen

### API
Application Programming Interface (Programmierschnittstelle)

### CNC
Computer Numerical Control (Computergesteuerte Numerische Steuerung)

### CSV
Comma-Separated Values (Komma-getrennte Werte)

### CW/CCW
Clockwise/Counter-Clockwise (Rechts-/Linksdrehung)

### HMI
Human Machine Interface (Mensch-Maschine-Schnittstelle)

### IoT
Internet of Things (Internet der Dinge)

### JSON
JavaScript Object Notation

### KI
Künstliche Intelligenz (AI - Artificial Intelligence)

### ML
Machine Learning (Maschinelles Lernen)

### MQTT
Message Queuing Telemetry Transport

### OPC UA
Open Platform Communications Unified Architecture

### REST
Representational State Transfer

### RPM
Revolutions Per Minute (Umdrehungen pro Minute)

### SQL
Structured Query Language

### TLS/SSL
Transport Layer Security / Secure Sockets Layer

### UUID
Universally Unique Identifier

---

## Technische Konstanten

### Timeouts
- **AI_LAYER_TIMEOUT:** 5 Sekunden (Standard)
- **MQTT_RECONNECT_DELAY_MIN:** 1 Sekunde
- **MQTT_RECONNECT_DELAY_MAX:** 60 Sekunden
- **HMI_UPDATE_INTERVAL:** 2 Sekunden

### Frequenzen
- **Sensordaten:** 10 Hz
- **Sicherheitsüberwachung:** 20 Hz

### Ports
- **Control Layer API:** 8000
- **AI Layer API:** 8001
- **MQTT Broker:** 1883
- **PostgreSQL/TimescaleDB:** 5432
- **Prometheus:** 9090
- **Grafana:** 3000

### Limits
- **Werkzeugmagazin:** 24 Plätze
- **Feed Override Range:** 0-150%
- **Z-Score Threshold:** 3.0 (Standard)
- **API Rate Limit:** Konfigurierbar

---

**Hinweis:** Dieses Glossar wird kontinuierlich erweitert. Für detaillierte technische Informationen siehe die entsprechenden Dokumentationsdateien im `docs/` Verzeichnis.
