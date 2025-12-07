# MODAX - Funktionsreferenz / Function Reference

**Version:** 0.3.0  
**Letzte Aktualisierung:** 2025-12-07  
**Zweck:** Umfassende Funktionsdokumentation für das MODAX-Handbuch

---

## Inhaltsverzeichnis

1. [Control Layer Funktionen](#control-layer-funktionen)
2. [AI Layer Funktionen](#ai-layer-funktionen)
3. [CNC Funktionen](#cnc-funktionen)
4. [API Endpunkte](#api-endpunkte)
5. [Utility Funktionen](#utility-funktionen)

---

## Control Layer Funktionen

### ControlLayer Class

**Datei:** `python-control-layer/control_layer.py`

#### `__init__(config)`
Initialisiert die Steuerungsebene.

**Parameter:**
- `config`: Konfigurationsobjekt mit allen System-Einstellungen

**Funktionalität:**
- Erstellt MQTT-Handler für Geräte-Kommunikation
- Initialisiert Datenaggregator
- Setzt AI-Interface auf
- Startet Hintergrund-Threads für Datenverarbeitung

#### `start()`
Startet die Steuerungsebene.

**Funktionalität:**
- Verbindet mit MQTT-Broker
- Startet Datenaggregations-Thread
- Beginnt KI-Analyse-Anfragen
- Loggt Startup-Information

#### `stop()`
Stoppt die Steuerungsebene sauber.

**Funktionalität:**
- Stoppt alle Hintergrund-Threads
- Trennt MQTT-Verbindung
- Gibt Ressourcen frei

---

### MQTTHandler Class

**Datei:** `python-control-layer/mqtt_handler.py`

#### `connect()`
Stellt Verbindung zum MQTT-Broker her.

**Rückgabe:** `bool` - True bei Erfolg, False bei Fehler

**Funktionalität:**
- Verbindet mit konfigurierbarem Broker (Standard: localhost:1883)
- Implementiert automatische Wiederverbindung mit exponentieller Backoff
- Behandelt Authentifizierung falls konfiguriert

#### `subscribe_to_device(device_id: str)`
Abonniert Sensor-Topics für ein Gerät.

**Parameter:**
- `device_id`: Eindeutige Geräte-ID

**Topics:**
- `modax/{device_id}/sensors` - Sensordaten
- `modax/{device_id}/safety` - Sicherheitsstatus

#### `publish(topic: str, message: dict)`
Publiziert eine Nachricht zu einem Topic.

**Parameter:**
- `topic`: MQTT-Topic
- `message`: Nachricht als Dictionary (wird zu JSON serialisiert)

**Beispiel:**
```python
mqtt.publish("modax/device1/control", {"command": "stop"})
```

---

### DataAggregator Class

**Datei:** `python-control-layer/data_aggregator.py`

#### `add_reading(device_id: str, sensor_data: dict)`
Fügt eine Sensor-Messung hinzu.

**Parameter:**
- `device_id`: Geräte-ID
- `sensor_data`: Dictionary mit Sensordaten (current, vibration, temperature)

**Funktionalität:**
- Speichert Rohdaten in Ring-Buffer
- Triggert Aggregation bei vollem Time-Window

#### `get_aggregated_data(device_id: str) -> dict`
Ruft aggregierte Daten für ein Gerät ab.

**Rückgabe:** Dictionary mit statistischen Werten:
```python
{
    "mean": {"current": 2.5, "vibration": 0.5, "temperature": 45.0},
    "std": {"current": 0.2, "vibration": 0.1, "temperature": 2.0},
    "min": {"current": 2.0, "vibration": 0.3, "temperature": 42.0},
    "max": {"current": 3.0, "vibration": 0.8, "temperature": 48.0},
    "count": 100
}
```

#### `_aggregate_window(device_id: str)`
Interne Funktion zur Berechnung statistischer Werte.

**Funktionalität:**
- Verwendet numpy für effiziente Vektoroperationen
- Berechnet Mean, Std Dev, Min, Max
- Speichert Ergebnisse für AI-Analyse

---

### AIInterface Class

**Datei:** `python-control-layer/ai_interface.py`

#### `request_analysis(device_id: str, aggregated_data: dict) -> dict`
Fordert KI-Analyse für Sensordaten an.

**Parameter:**
- `device_id`: Geräte-ID
- `aggregated_data`: Aggregierte Sensordaten

**Rückgabe:** AI-Analyse-Ergebnis mit:
- `anomaly_detected`: Boolean
- `anomaly_score`: Float (0.0-10.0)
- `wear_level`: Float (0.0-1.0)
- `recommendations`: List[str]
- `confidence`: Float (0.0-1.0)

**Funktionalität:**
- Asynchroner HTTP-Request an AI Layer
- Timeout-Handling (konfigurierbar, Standard 5s)
- Fehlerbehandlung und Retry-Logik

---

## AI Layer Funktionen

### AnomalyDetector Class

**Datei:** `python-ai-layer/anomaly_detector.py`

#### `detect_anomaly(sensor_data: dict) -> dict`
Erkennt Anomalien in Sensordaten mittels Z-Score-Analyse.

**Parameter:**
- `sensor_data`: Dictionary mit mean, std für current, vibration, temperature

**Rückgabe:**
```python
{
    "anomaly_detected": bool,
    "anomaly_score": float,  # 0.0-10.0
    "anomalies": {
        "current": bool,
        "vibration": bool,
        "temperature": bool
    },
    "z_scores": {
        "current": float,
        "vibration": float,
        "temperature": float
    }
}
```

**Algorithmus:**
- Berechnet Z-Score für jeden Sensor: `z = (value - baseline_mean) / baseline_std`
- Anomalie wenn `|z| > threshold` (Standard: 3.0)
- Anomaly Score: Maximaler Z-Score

#### `update_baseline(sensor_data: dict)`
Aktualisiert Baseline-Werte basierend auf historischen Daten.

**Funktionalität:**
- Verwendet exponentielles Moving Average
- Adaptive Schwellenwerte
- Verhindert false positives bei normalen Schwankungen

---

### WearPredictor Class

**Datei:** `python-ai-layer/wear_predictor.py`

#### `predict_wear(device_id: str, sensor_data: dict) -> dict`
Sagt Verschleiß basierend auf Stress-Akkumulation voraus.

**Parameter:**
- `device_id`: Geräte-ID
- `sensor_data`: Aktuelle Sensordaten

**Rückgabe:**
```python
{
    "wear_level": float,  # 0.0-1.0
    "estimated_hours_remaining": float,
    "stress_factors": {
        "current_stress": float,
        "vibration_stress": float,
        "temperature_stress": float
    },
    "maintenance_recommended": bool
}
```

**Modell:**
- **Stress-Berechnung:** Gewichtete Summe von normalisierten Sensor-Werten
- **Wear-Akkumulation:** Kumulative Integration von Stress über Zeit
- **Restlebensdauer:** `remaining = (1 - wear_level) * EXPECTED_LIFETIME`

#### `reset_wear_tracking(device_id: str)`
Setzt Verschleißzähler nach Wartung zurück.

**Verwendung:** Nach Komponententausch oder Wartung

---

### Optimizer Class

**Datei:** `python-ai-layer/optimizer.py`

#### `generate_recommendations(analysis_results: dict) -> list`
Generiert Optimierungsempfehlungen basierend auf Analyseergebnissen.

**Parameter:**
- `analysis_results`: Kombinierte Ergebnisse von Anomalieerkennung und Verschleißvorhersage

**Rückgabe:** Liste von Empfehlungen (strings)

**Regelbasierte Logik:**
```python
if wear_level > 0.8:
    → "Schedule maintenance soon"
if anomaly_score > 5.0:
    → "Investigate sensor readings"
if current > threshold:
    → "Reduce feed rate or spindle speed"
if vibration > threshold:
    → "Check tool condition and balance"
if temperature > threshold:
    → "Improve cooling or reduce cutting speed"
```

---

## CNC Funktionen

### CNCController Class

**Datei:** `python-control-layer/cnc_controller.py`

#### `set_mode(mode: CNCMode)`
Setzt CNC-Betriebsmodus.

**Modi:**
- `MANUAL`: Manuelle Steuerung
- `MDI`: Manual Data Input
- `AUTO`: Automatische Programmausführung
- `HOME`: Referenzfahrt

#### `emergency_stop()`
Führt Not-Aus durch.

**Funktionalität:**
- Stoppt sofort alle Bewegungen
- Schaltet Spindel aus
- Setzt E-Stop-Flag
- Loggt kritisches Event

#### `set_spindle_speed(rpm: float)`
Setzt Spindeldrehzahl.

**Parameter:**
- `rpm`: Umdrehungen pro Minute (0-24000)

**Validierung:** Prüft gegen maximale Spindeldrehzahl

---

### GCodeParser Class

**Datei:** `python-control-layer/gcode_parser.py`

#### `parse_line(line: str, line_number: int) -> GCodeCommand`
Parst eine G-Code-Zeile.

**Parameter:**
- `line`: G-Code-String (z.B. "G01 X10 Y20 F100")
- `line_number`: Zeilennummer für Fehlerbehandlung

**Rückgabe:** GCodeCommand-Objekt mit:
- `g_codes`: Liste von G-Codes
- `m_codes`: Liste von M-Codes
- `parameters`: Dictionary mit Achsenwerten und Parametern

**Beispiel:**
```python
cmd = parser.parse_line("G01 X10.5 Y-20.3 F500", 1)
# cmd.g_codes = [1]
# cmd.parameters = {"X": 10.5, "Y": -20.3, "F": 500}
```

#### `parse_program(program: str) -> list`
Parst ein komplettes G-Code-Programm.

**Rückgabe:** Liste von GCodeCommand-Objekten

**Funktionalität:**
- Unterstützt Kommentare (Klammern, Semikolon)
- Behandelt Zeilennummern (N-Wörter)
- Expandiert Makros

---

### MotionController Class

**Datei:** `python-control-layer/motion_controller.py`

#### `calculate_linear_move(target: dict, feed_rate: float, is_rapid: bool) -> dict`
Berechnet lineare Bewegung.

**Parameter:**
- `target`: Zielposition {"X": 100, "Y": 50, "Z": 10}
- `feed_rate`: Vorschubgeschwindigkeit (mm/min)
- `is_rapid`: True für G00 (Eilgang), False für G01

**Rückgabe:** Bewegungsdaten mit:
- `type`: "linear"
- `start`: Startposition
- `end`: Zielposition
- `distance`: Bewegungsdistanz
- `duration`: Berechnete Zeit
- `feed_rate`: Verwendete Geschwindigkeit

**Algorithmus:**
- Berechnet euklidische Distanz: `sqrt((x2-x1)² + (y2-y1)² + (z2-z1)²)`
- Berechnet Dauer: `duration = distance / feed_rate * 60` (Sekunden)

#### `calculate_circular_move(target: dict, center_offset: dict, feed_rate: float, clockwise: bool, radius: float = None) -> dict`
Berechnet Kreisbewegung (G02/G03).

**Parameter:**
- `target`: Endpunkt
- `center_offset`: Kreismittelpunkt-Offset (I, J, K)
- `feed_rate`: Vorschubgeschwindigkeit
- `clockwise`: True für G02 (CW), False für G03 (CCW)
- `radius`: Optional, R-Wert statt I/J/K

**Algorithmus:**
- Berechnet Kreismittelpunkt
- Bestimmt Start- und Endwinkel
- Berechnet Bogenlänge
- Segmentiert in lineare Schritte für Ausführung

---

### ToolManager Class

**Datei:** `python-control-layer/tool_manager.py`

#### `get_tool(tool_number: int) -> Tool`
Ruft Werkzeug-Informationen ab.

**Parameter:**
- `tool_number`: Werkzeugnummer (1-24)

**Rückgabe:** Tool-Objekt mit:
- `tool_number`: Nummer
- `diameter`: Durchmesser (mm)
- `length`: Länge (mm)
- `type`: Werkzeugart ("mill", "drill", "tap", "boring")
- `offset`: Korrekturwerte
- `wear`: Verschleißwerte

#### `change_tool(new_tool_number: int) -> bool`
Führt Werkzeugwechsel durch.

**Funktionalität:**
1. Fährt zu sicherer Z-Position
2. Bewegt zu Werkzeugwechsel-Position
3. Entfernt aktuelles Werkzeug
4. Lädt neues Werkzeug aus Magazin
5. Anwendung der Werkzeugkorrektur
6. Loggt Werkzeugwechsel

#### `measure_tool(tool_number: int) -> dict`
Misst Werkzeug automatisch (G36/G37).

**Rückgabe:**
```python
{
    "length": float,  # Gemessene Länge
    "diameter": float,  # Gemessener Durchmesser
    "success": bool
}
```

---

### CoordinateSystemManager Class

**Datei:** `python-control-layer/coordinate_system.py`

#### `set_work_offset(coord_sys: str, axis: str, offset: float)`
Setzt Werkstück-Nullpunktverschiebung.

**Parameter:**
- `coord_sys`: Koordinatensystem ("G54"-"G59")
- `axis`: Achse ("X", "Y", "Z", etc.)
- `offset`: Offset-Wert in mm

**Beispiel:**
```python
coords.set_work_offset("G54", "X", 100.0)
coords.set_work_offset("G54", "Y", 50.0)
coords.set_work_offset("G54", "Z", 0.0)
```

#### `transform_to_machine_coords(position: dict, coord_sys: str) -> dict`
Transformiert Werkstück- zu Maschinen-Koordinaten.

**Algorithmus:**
```
machine_pos = work_pos + work_offset + tool_offset + rotation
```

---

## API Endpunkte

### Control Layer API (Port 8000)

#### `GET /status`
Systemstatus abfragen.

**Antwort:**
```json
{
    "status": "running",
    "uptime": 3600,
    "connected_devices": 2,
    "last_update": "2025-12-07T10:30:45Z"
}
```

#### `GET /devices`
Liste aller verbundenen Geräte.

**Antwort:**
```json
{
    "devices": [
        {
            "id": "device1",
            "name": "CNC Mill 1",
            "status": "active",
            "last_seen": "2025-12-07T10:30:45Z"
        }
    ]
}
```

#### `GET /devices/{id}/data`
Aktuelle Sensordaten für Gerät.

**Antwort:**
```json
{
    "device_id": "device1",
    "timestamp": "2025-12-07T10:30:45Z",
    "raw": {
        "current": 2.5,
        "vibration": 0.5,
        "temperature": 45.0
    },
    "aggregated": {
        "mean": {"current": 2.4, "vibration": 0.48, "temperature": 44.5},
        "std": {"current": 0.2, "vibration": 0.05, "temperature": 1.5}
    }
}
```

#### `POST /control/command`
Steuerungsbefehl senden.

**Request Body:**
```json
{
    "device_id": "device1",
    "command": "start",
    "parameters": {}
}
```

**Antwort:**
```json
{
    "success": true,
    "message": "Command executed successfully"
}
```

#### `POST /cnc/execute`
G-Code ausführen.

**Request Body:**
```json
{
    "gcode": "G01 X10 Y20 F500"
}
```

---

### AI Layer API (Port 8001)

#### `POST /analyze`
Sensordaten analysieren.

**Request Body:**
```json
{
    "device_id": "device1",
    "sensor_data": {
        "mean": {"current": 2.5, "vibration": 0.5, "temperature": 45},
        "std": {"current": 0.2, "vibration": 0.1, "temperature": 2}
    }
}
```

**Antwort:**
```json
{
    "device_id": "device1",
    "timestamp": "2025-12-07T10:30:45Z",
    "anomaly_detected": false,
    "anomaly_score": 1.2,
    "wear_level": 0.35,
    "recommendations": [
        "Continue normal operation",
        "Monitor vibration levels"
    ],
    "confidence": 0.85
}
```

#### `GET /models/info`
Model-Informationen abfragen.

**Antwort:**
```json
{
    "version": "1.0.0",
    "anomaly_threshold": 3.0,
    "wear_model": "stress_accumulation",
    "baseline_learning": true
}
```

#### `POST /reset-wear/{device_id}`
Verschleißzähler zurücksetzen.

**Antwort:**
```json
{
    "success": true,
    "device_id": "device1",
    "message": "Wear tracking reset"
}
```

---

## Utility Funktionen

### SecretsManager Class

**Datei:** `python-control-layer/secrets_manager.py`

#### `get_api_key(key_name: str) -> str`
Ruft API-Schlüssel sicher ab.

**Quellen:** Environment Variables → Vault (falls konfiguriert)

#### `get_database_credentials() -> dict`
Ruft Datenbank-Zugangsdaten ab.

**Rückgabe:**
```python
{
    "host": "localhost",
    "port": 5432,
    "database": "modax",
    "user": "modax_user",
    "password": "***"
}
```

---

### DataExporter Class

**Datei:** `python-control-layer/data_export.py`

#### `export_to_csv(device_id: str, start_time: datetime, end_time: datetime) -> str`
Exportiert Daten als CSV.

**Rückgabe:** CSV-String

**Format:**
```csv
timestamp,device_id,current,vibration,temperature
2025-12-07 10:00:00,device1,2.5,0.5,45.0
2025-12-07 10:00:01,device1,2.6,0.51,45.2
```

#### `export_to_json(device_id: str, start_time: datetime, end_time: datetime) -> dict`
Exportiert Daten als JSON.

---

### SecurityAuditLogger Class

**Datei:** `python-control-layer/security_audit.py`

#### `log_api_access(user: str, endpoint: str, method: str, status: int)`
Loggt API-Zugriffe für Audit-Trail.

**Beispiel:**
```python
audit.log_api_access(
    user="hmi-client",
    endpoint="/devices/device1/data",
    method="GET",
    status=200
)
```

#### `log_security_event(event_type: str, details: dict)`
Loggt Sicherheits-Events.

**Event-Typen:**
- `authentication_failed`
- `unauthorized_access`
- `rate_limit_exceeded`
- `emergency_stop`

---

## Best Practices

### Fehlerbehandlung
Alle Funktionen verwenden Try-Catch mit spezifischen Exception-Typen:
```python
try:
    result = function()
except ValueError as e:
    logger.error(f"Invalid value: {e}")
except ConnectionError as e:
    logger.error(f"Connection failed: {e}")
```

### Logging
Strukturiertes Logging mit Kontext:
```python
logger.info("Operation completed", extra={
    "device_id": device_id,
    "duration": duration,
    "result": result
})
```

### Asynchrone Operationen
Verwende `async/await` für I/O-intensive Operationen:
```python
async def fetch_data():
    response = await httpx.get(url)
    return response.json()
```

---

**Hinweis:** Diese Referenz wird kontinuierlich erweitert. Für vollständige Code-Beispiele siehe die Quellcode-Dateien und Unit-Tests.
