# MODAX – Datenfluss

Dieses Dokument beschreibt detailliert, wie Daten durch das MODAX-System fließen, von der Sensorerfassung bis zur Visualisierung und zurück zu Steuerungsbefehlen.

---

## Übersicht

MODAX verwendet zwei primäre Datenfluss-Richtungen:

1. **Bottom-Up (Sensordaten → Visualisierung):** Messungen → Verarbeitung → Anzeige
2. **Top-Down (Befehle → Aktorik):** Benutzer → Validierung → Ausführung

**Wichtig:** KI-Ebene ist ein **Seitenkanal**, nicht im Haupt-Datenfluss!

---

## Bottom-Up: Sensordaten-Fluss

### Phase 1: Erfassung (Feldebene)

**Akteur:** ESP32 Mikrocontroller

**Prozess:**
1. **Sensoren auslesen** (alle 100 ms)
   - Strom: ACS712 über Analog-Input
   - Vibration: MPU6050 über I2C
   - Temperatur: DS18B20 über OneWire

2. **Lokale Verarbeitung**
   - Einfache Filterung (gleitender Mittelwert über 3 Samples)
   - Schwellenwert-Checks (Überstrom, Übertemperatur)
   - Safety-Status ermitteln

3. **Daten serialisieren**
   - JSON-Format erstellen
   - Timestamp hinzufügen (Unix-Time)
   - Device-ID einfügen

4. **MQTT Publish**
   - Topic: `modax/sensor/{device_id}/data`
   - QoS: 1 (At Least Once)
   - Retain: false (nur aktuelle Werte)

**Payload-Beispiel:**
```json
{
  "device_id": "esp32_001",
  "timestamp": 1703678400,
  "current": 2.35,
  "vibration": 0.82,
  "temperature": 45.1,
  "safety_status": "OK"
}
```

**Fehlerbehandlung:**
- Sensor-Timeout: Letzter gültiger Wert + Error-Flag
- MQTT-Disconnect: Lokaler Puffer (max 100 Nachrichten)
- WiFi-Loss: Automatische Wiederverbindung

### Phase 2: Aggregation (Steuerungsebene)

**Akteur:** Python Control Layer (MQTT Handler)

**Prozess:**
1. **MQTT Subscribe**
   - Topic-Pattern: `modax/sensor/+/data`
   - Callback-Handler: `on_message()`

2. **Empfang & Parsing**
   - JSON deserialisieren
   - Validierung (Schema-Check)
   - Device-ID extrahieren

3. **Datenpuffer-Management**
   - Time-Window-Puffer (default: 5 Sekunden)
   - Sliding-Window für kontinuierliche Aggregation
   - Alte Daten verwerfen (nach Window-Ablauf)

4. **Statistische Aggregation**
   ```python
   aggregated_data = {
       "current": {
           "mean": 2.33,
           "std": 0.12,
           "min": 2.1,
           "max": 2.5
       },
       "vibration": {...},
       "temperature": {...},
       "sample_count": 50,
       "window_start": 1703678395,
       "window_end": 1703678400
   }
   ```

5. **Speicherung** (optional)
   - In-Memory: Python Dictionary (aktuell)
   - Persistent: TimescaleDB (geplant)

**Fehlerbehandlung:**
- Ungültige JSON: Fehler loggen, Nachricht verwerfen
- Fehlende Felder: Default-Werte verwenden
- Duplikate: Timestamp-basierte Deduplizierung

### Phase 3: Bereitstellung (REST API)

**Akteur:** FastAPI Endpoints (Control Layer)

**Prozess:**
1. **API-Request von HMI**
   - Endpoint: `GET /devices/{device_id}/data`
   - Authentication: Basic Auth (optional)

2. **Daten abrufen**
   - Device-ID aus Path-Parameter
   - Aggregierte Daten aus Puffer laden
   - Letzte Raw-Daten hinzufügen

3. **Response formatieren**
   ```json
   {
       "device_id": "esp32_001",
       "last_update": "2025-12-27T10:30:00Z",
       "raw": {
           "current": 2.35,
           "vibration": 0.82,
           "temperature": 45.1
       },
       "aggregated": {
           "current": {
               "mean": 2.33,
               "std": 0.12,
               "min": 2.1,
               "max": 2.5
           },
           ...
       },
       "status": "OK"
   }
   ```

4. **HTTP Response**
   - Status: 200 OK
   - Content-Type: application/json
   - Cache-Control: no-cache (Live-Daten)

**Fehlerbehandlung:**
- Device nicht gefunden: 404 Not Found
- Keine Daten verfügbar: 503 Service Unavailable
- Interne Fehler: 500 Internal Server Error

### Phase 4: Visualisierung (HMI)

**Akteur:** C# HMI Application

**Prozess:**
1. **Polling** (alle 2 Sekunden)
   - Timer-Event triggert API-Call
   - HttpClient.GetAsync()

2. **Deserialisierung**
   - JSON → C# DeviceData-Objekt
   - Validierung

3. **UI-Update**
   - Labels aktualisieren (Current, Vibration, Temp)
   - Farben anpassen (Grün/Gelb/Rot basierend auf Schwellenwerten)
   - Grafiken aktualisieren (Trend-Kurven)

4. **Alarmierung**
   - Visuelle Warnung bei Anomalien
   - Optional: Audio-Alarm (MIDI)

**Fehlerbehandlung:**
- API-Timeout: Letzte Werte beibehalten, Verbindungsstatus anzeigen
- Parsing-Fehler: Fehlerlog, generische Fehlermeldung
- UI-Thread-Safety: Invoke für Thread-safe Updates

---

## KI-Seitenkanal (Asynchron)

### Anfrage: Steuerung → KI

**Trigger:** Neue Sensordaten empfangen (nicht jede Nachricht!)

**Prozess:**
1. **Throttling** (z.B. nur alle 10 Sekunden)
   - Verhindert Überlastung der KI-Ebene
   - Batch-Processing effizienter

2. **Daten vorbereiten**
   - Letzte N Samples sammeln (z.B. 30 Samples = 3 Sekunden)
   - Arrays für Zeitreihen erstellen

3. **Asynchrone REST API Call**
   ```python
   async with httpx.AsyncClient(timeout=5.0) as client:
       response = await client.post(
           "http://ai-layer:8001/analyze",
           json={
               "device_id": "esp32_001",
               "current": [2.1, 2.2, 2.3, ...],
               "vibration": [0.7, 0.8, 0.9, ...],
               "temperature": [44, 45, 46, ...]
           }
       )
   ```

4. **Timeout-Handling**
   - Max 5 Sekunden warten
   - Bei Timeout: Warnung loggen, weiter ohne KI

5. **Empfehlung speichern**
   - KI-Response in Cache schreiben
   - Für HMI bereitstellen (GET /devices/{id}/ai-analysis)
   - Audit-Log: Alle Empfehlungen protokollieren

**Wichtig:** Control Layer **wartet NICHT** auf KI-Antwort für normale Operationen!

### Antwort: KI → Steuerung

**Response-Struktur:**
```json
{
  "anomaly_detected": false,
  "anomaly_types": [],
  "wear_level": 0.35,
  "remaining_life_hours": 240,
  "recommendations": [
    {
      "type": "optimization",
      "priority": "low",
      "action": "Reduce feed rate by 10%",
      "confidence": 0.65
    }
  ],
  "confidence": 0.78,
  "timestamp": "2025-12-27T10:30:05Z"
}
```

**Verwendung:**
- **NICHT automatisch ausführen!**
- In HMI anzeigen (separater Bereich "KI-Empfehlungen")
- Bediener entscheidet über Umsetzung
- Bei Wartungsempfehlung: Ticket erstellen (manuell/automatisch)

---

## Top-Down: Befehlsfluss

### Phase 1: Benutzereingabe (HMI)

**Akteur:** Bediener über HMI

**Prozess:**
1. **Befehlseingabe**
   - Button-Click (z.B. "Start Machine")
   - MDI-Eingabe (G-Code)
   - Parameter-Änderung

2. **Lokale Validierung**
   - Sind alle erforderlichen Felder gefüllt?
   - Ist Format korrekt? (z.B. G-Code-Syntax)
   - Ist Aktion erlaubt? (Berechtigungen)

3. **Bestätigung** (bei kritischen Befehlen)
   - MessageBox: "Machine starten? [Ja] [Nein]"
   - Bei "Nein": Abbruch

4. **REST API Call**
   ```csharp
   var command = new {
       device_id = "esp32_001",
       command = "START_SPINDLE",
       parameters = new { speed = 3000 }
   };
   
   var response = await httpClient.PostAsJsonAsync(
       "http://control-layer:8000/control/command",
       command
   );
   ```

**Fehlerbehandlung:**
- Netzwerkfehler: Retry (max 3x), dann Fehlermeldung
- Validierungsfehler: Hinweis an Benutzer, Korrektur ermöglichen

### Phase 2: Sicherheitsvalidierung (Steuerungsebene)

**Akteur:** Python Control Layer (Safety Validator)

**Prozess:**
1. **Befehl empfangen**
   - Endpoint: `POST /control/command`
   - Request-Body parsen und validieren

2. **Safety-Check**
   ```python
   def is_system_safe(device_id: str) -> bool:
       device = get_device(device_id)
       
       # Hardware-Safety-Status prüfen
       if device.safety_status != "OK":
           return False
       
       # Schwellenwerte prüfen
       if device.temperature > TEMP_CRITICAL_THRESHOLD:
           return False
       
       if device.current > CURRENT_MAX_THRESHOLD:
           return False
       
       # Weitere Checks...
       return True
   ```

3. **Entscheidung**
   - **Falls safe:** Befehl an Feldebene weiterleiten
   - **Falls unsafe:** HTTP 400 Bad Request + Grund

4. **Audit-Logging**
   - Jeder Befehl wird geloggt (auch abgelehnte!)
   - Timestamp, Quelle (HMI), Befehl, Validierungsergebnis

**Wichtig:** Auch wenn HMI "vertrauenswürdig" ist, wird JEDER Befehl validiert!

### Phase 3: Ausführung (Feldebene)

**Akteur:** ESP32 Mikrocontroller

**Prozess:**
1. **MQTT Subscribe**
   - Topic: `modax/control/{device_id}/command`

2. **Befehl empfangen**
   ```json
   {
       "command": "START_SPINDLE",
       "parameters": {
           "speed": 3000,
           "direction": "CW"
       },
       "timestamp": 1703678410
   }
   ```

3. **Lokale Safety-Prüfung** (zusätzlich!)
   - Auch ESP32 prüft Safety-Status
   - Defense in Depth: Doppelte Absicherung

4. **Hardware-Ansteuerung**
   - GPIO setzen (Relais, SSR)
   - PWM für Drehzahlsteuerung
   - DAC für analoge Ausgänge

5. **Status zurückmelden**
   - MQTT Publish auf `modax/sensor/{device_id}/status`
   - Bestätigung oder Fehler

**Fehlerbehandlung:**
- Ungültiger Befehl: Ignorieren + Fehler melden
- Hardware-Fehler: Not-Aus auslösen + Fehler melden
- Kommunikationsfehler: Timeout, dann Safe-State

---

## Datenfluss-Diagramme

### Echtzeit-Datenfluss (Normal Operation)

```
┌──────────┐      ┌───────────┐      ┌──────┐      ┌─────┐
│  ESP32   │─────>│  Control  │─────>│  HMI │      │ KI  │
│  (10 Hz) │ MQTT │  (Aggr.)  │ REST │ (2s) │      │     │
└──────────┘      └───────────┘      └──────┘      └─────┘
                        │                              ↑
                        └─────────────────────────────┘
                           Async REST (10s)
```

### Befehlsfluss (mit Validation)

```
┌─────┐      ┌───────────┐      ┌──────────┐
│ HMI │─────>│  Control  │─────>│  ESP32   │
│     │ REST │ (Validate)│ MQTT │          │
└─────┘      └───────────┘      └──────────┘
                   │
                   ├─> is_system_safe() ✓
                   ├─> log_command()
                   └─> forward_to_mqtt()
```

### KI-Seitenkanal (Asynchron)

```
┌───────────┐                    ┌──────┐
│  Control  │───────────────────>│  KI  │
│           │ POST /analyze      │      │
│           │ (Async, Timeout 5s)│      │
│           │<───────────────────│      │
│           │ Recommendations    │      │
└───────────┘                    └──────┘
      │
      └─> Cache-Empfehlung
      └─> NICHT automatisch ausführen!
```

---

## Performance-Metriken

| Datenfluss-Segment | Latenz (Typical) | Latenz (Max) | Throughput |
|--------------------|------------------|--------------|------------|
| ESP32 → MQTT | 10-20 ms | 50 ms | 10 msg/s |
| MQTT → Control | 5-10 ms | 30 ms | 100 msg/s |
| Control Aggregation | 1-5 ms | 20 ms | - |
| Control → HMI (REST) | 20-50 ms | 100 ms | 10 req/s |
| Control → KI (REST) | 100-1000 ms | 5000 ms | 1 req/10s |
| HMI → Control (Command) | 20-50 ms | 100 ms | 1 req/s |
| Control → ESP32 (Command) | 10-30 ms | 100 ms | 10 cmd/s |

---

## Datenvolumen

### Pro Gerät (10 Hz Sensordaten)

**Payload-Größe:** ~200 Bytes/Nachricht (JSON)  
**Rate:** 10 Nachrichten/Sekunde  
**Bandbreite:** 2 KB/s = 16 Kbit/s

**Pro Stunde:** 7.2 MB  
**Pro Tag:** 173 MB  
**Pro Monat:** 5.2 GB

### Skalierung (100 Geräte)

**Bandbreite:** 1.6 Mbit/s (peak)  
**Speicher pro Tag:** 17.3 GB  
**Speicher pro Monat:** 520 GB

**Empfehlung:**
- Datenaggregation auf Control Layer
- Retention Policy (z.B. Raw-Daten 7 Tage, Aggregiert 1 Jahr)
- Kompression (gzip für Storage)

---

## Fehlerszenarien

### Szenario 1: MQTT Broker-Ausfall

**Symptome:**
- ESP32 kann nicht publishen
- Control Layer empfängt keine Daten

**Auswirkung:**
- **Feldebene:** Safety funktioniert weiter (lokal)
- **Control:** Keine neuen Daten, HMI zeigt "Offline"
- **HMI:** Letzter bekannter Status

**Recovery:**
- MQTT Auto-Reconnect (Exponential Backoff)
- Gepufferte Nachrichten werden nachgeliefert
- System normalisiert sich automatisch

### Szenario 2: Control Layer-Crash

**Symptome:**
- HMI verliert Verbindung
- ESP32 empfängt keine Befehle

**Auswirkung:**
- **Feldebene:** Läuft weiter, Safety aktiv
- **KI:** Keine neuen Analysen
- **HMI:** Offline-Modus

**Recovery:**
- Control Layer neu starten (Docker/K8s macht das automatisch)
- Daten aus MQTT Retained Messages (falls konfiguriert)

### Szenario 3: Netzwerk-Partition

**Symptome:**
- ESP32 kann Control Layer nicht erreichen (WiFi-Problem)

**Auswirkung:**
- **Feldebene:** Lokale Safety funktioniert
- **Control:** Gerät erscheint "offline"

**Recovery:**
- WiFi-Reconnect auf ESP32
- MQTT Reconnect
- Automatische Normalisierung

---

## Zusammenfassung

**Datenfluss-Prinzipien:**
1. ✅ Daten fließen bottom-up (Sensoren → HMI)
2. ✅ Befehle fließen top-down (HMI → Aktoren)
3. ✅ KI ist asynchroner Seitenkanal (nicht im kritischen Pfad)
4. ✅ Alle Befehle werden validiert (Defense in Depth)
5. ✅ Fehlertoleranz auf allen Ebenen

**Sicherheit:**
- Keine automatische Ausführung von KI-Empfehlungen
- Mehrfache Validierung (Control + ESP32)
- Audit-Logging für alle Befehle
- Graceful Degradation bei Ausfällen

---

**Referenzen:**
- [4-Ebenen-Modell](layer-model.md)
- [Control Boundaries](control-boundaries.md)
- [Fehlerbehandlung](../03-control-layer/failure-handling.md)
