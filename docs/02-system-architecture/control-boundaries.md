# MODAX – Control Boundaries & KI-Grenzen

Dieses Dokument definiert präzise, welche Funktionen die KI-Ebene ausführen **darf** und welche **verboten** sind. Diese Grenzen sind architektonisch durchgesetzt und nicht verhandelbar.

---

## Überblick

**Grundprinzip:** KI ist **Berater**, niemals **Entscheider** in sicherheitskritischen Bereichen.

**Durchsetzung:** Architektonische Barrieren verhindern, dass KI direkt steuern kann – selbst bei Fehlkonfiguration oder Bugs.

---

## Sperrzonen (No-Go-Areas für KI)

### 1. Sicherheitsfunktionen

**Verboten:**
- ❌ Not-Aus-Logik
- ❌ Sicherheitsverriegelungen (Interlocks)
- ❌ Überlastschutz
- ❌ Temperatur-Shutdown
- ❌ Kollisionsvermeidung (reaktiv)
- ❌ Arbeitsbere ichsbegrenzung (Software-Limits)

**Begründung:** Diese Funktionen müssen deterministisch, zuverlässig und nachvollziehbar sein. KI/ML ist inhärent nicht-deterministisch.

**Architektonische Durchsetzung:**
- Implementiert in Feldebene (ESP32) und Control Layer
- KI-Ebene hat keinen Code-Zugriff auf diese Module
- Keine API-Endpoints für Safety-Override

### 2. Echtzeit-Steuerung

**Verboten:**
- ❌ Motion Control (G0/G1/G2/G3 Interpolation)
- ❌ Spindelsteuerung (Start/Stop/Geschwindigkeit)
- ❌ Achsen-Bewegungen
- ❌ Werkzeugwechsel
- ❌ Kühlmittel-Steuerung
- ❌ Koordinatensystem-Wechsel

**Begründung:** Echtzeit-kritische Funktionen benötigen garantierte Antwortzeiten. KI-Inferenz kann variabel lange dauern.

**Architektonische Durchsetzung:**
- CNC-Steuerung ist in Control Layer implementiert
- KI-Ebene hat keine MQTT-Publish-Rechte für `modax/control/+/command`
- Firewall-Regeln verhindern direkte ESP32-Kommunikation

### 3. Parameter-Änderungen

**Verboten (automatisch):**
- ❌ Automatische Anpassung von Vorschubrate
- ❌ Automatische Änderung der Spindeldrehzahl
- ❌ Automatische Werkzeug-Offset-Korrektur
- ❌ Automatische Koordinatensystem-Verschiebung
- ❌ Änderung von Safety-Limits

**Erlaubt (nur als Empfehlung):**
- ✅ Vorschlag für Vorschubrate
- ✅ Vorschlag für Spindeldrehzahl
- ✅ Hinweis auf suboptimale Parameter

**Durchsetzung:** HMI zeigt Empfehlungen an, Bediener muss bestätigen.

---

## Erlaubte KI-Funktionen

### 1. Analyse & Monitoring

**Erlaubt:**
- ✅ Anomalieerkennung (statistische Ausreißer)
- ✅ Trend-Analyse (Verschlechterung über Zeit)
- ✅ Baseline-Learning (normale Betriebsparameter)
- ✅ Korrelations-Analyse (Muster zwischen Sensoren)
- ✅ Performance-Metriken (OEE, MTBF, MTTR)

**Beispiel:**
```python
# Erlaubt: Analyse durchführen
analysis = ai_layer.detect_anomaly(
    current=sensor_data.current,
    vibration=sensor_data.vibration,
    temperature=sensor_data.temperature
)

# Erlaubt: Warnung ausgeben
if analysis.anomaly_detected:
    logger.warning(f"Anomalie erkannt: {analysis.anomaly_types}")
    notify_operator("Vibration ungewöhnlich hoch")

# VERBOTEN: Direkt reagieren
# ❌ control_layer.stop_machine()  # NIEMALS!
```

### 2. Prädiktive Wartung

**Erlaubt:**
- ✅ Verschleiß-Vorhersage
- ✅ Restlebenszeit-Schätzung
- ✅ Wartungsintervall-Empfehlungen
- ✅ Ausfall-Wahrscheinlichkeit berechnen
- ✅ Wartungs-Tickets erstellen (informativ)

**Beispiel:**
```python
# Erlaubt: Verschleiß prognostizieren
prediction = ai_layer.predict_wear(
    stress_history=device.stress_history
)

# Erlaubt: Empfehlung geben
if prediction.remaining_life_hours < 48:
    recommendation = {
        "type": "maintenance",
        "priority": "high",
        "action": "Inspect bearings within 48h",
        "confidence": prediction.confidence
    }
    store_recommendation(recommendation)

# VERBOTEN: Automatisch Wartung starten
# ❌ maintenance_scheduler.schedule_now(device_id)  # Nur mit Bestätigung!
```

### 3. Optimierungsempfehlungen

**Erlaubt:**
- ✅ Vorschläge für Parameter-Optimierung
- ✅ Energie-Effizienz-Tipps
- ✅ Qualitätsverbesserungs-Hinweise
- ✅ Prozess-Optimierung (z.B. Scheduling)
- ✅ Was-wäre-wenn-Simulationen

**Beispiel:**
```python
# Erlaubt: Optimierung vorschlagen
optimization = ai_layer.suggest_parameters(
    current_feed=120,  # mm/min
    current_speed=3000,  # RPM
    material="aluminum"
)

# Erlaubt: Empfehlung mit Confidence
recommendation = {
    "type": "optimization",
    "priority": "low",
    "action": "Increase feed rate to 150 mm/min for 20% faster cycle time",
    "confidence": 0.75,
    "expected_improvement": "20% faster, 5% energy savings"
}

# VERBOTEN: Automatisch anwenden
# ❌ cnc_controller.set_feed_rate(150)  # Nur nach Bediener-Bestätigung!
```

### 4. Reporting & Visualisierung

**Erlaubt:**
- ✅ Dashboards generieren
- ✅ Reports erstellen (PDF, Excel)
- ✅ Visualisierungen (Grafiken, Heatmaps)
- ✅ Zusammenfassungen
- ✅ KPIs berechnen

---

## Architektonische Barrieren

### 1. Netzwerk-Segmentierung

**Implementierung:**
```
┌────────────────────────────────────────┐
│  OT-Netzwerk (Operational Technology)  │
│  ┌──────────┐      ┌──────────────┐   │
│  │  ESP32   │◄────►│  Control     │   │
│  │ Devices  │ MQTT │  Layer       │   │
│  └──────────┘      └──────────────┘   │
└────────────────────────────────────────┘
                        ↕ REST API
┌────────────────────────────────────────┐
│  DMZ (Demilitarized Zone)              │
│  ┌──────────────┐                      │
│  │  AI Layer    │                      │
│  │  (Read-Only) │                      │
│  └──────────────┘                      │
└────────────────────────────────────────┘
                        ↕ REST API
┌────────────────────────────────────────┐
│  IT-Netzwerk (Information Technology)  │
│  ┌──────────────┐                      │
│  │  HMI / SCADA │                      │
│  └──────────────┘                      │
└────────────────────────────────────────┘
```

**Firewall-Regeln:**
- KI → Control: Nur GET (Read-Only)
- KI → ESP32: **Blockiert**
- KI → HMI: **Blockiert**
- Control → KI: POST für Analysen
- HMI → Control: GET + POST (mit Auth)

### 2. MQTT-Berechtigungen

**ACL (Access Control List):**
```
# Control Layer
user: control_layer
  publish: modax/control/+/command
  subscribe: modax/sensor/+/data
  subscribe: modax/sensor/+/safety

# AI Layer
user: ai_layer
  publish: NONE (keine Publish-Rechte!)
  subscribe: NONE (erhält Daten via REST)

# ESP32 Devices
user: esp32_{device_id}
  publish: modax/sensor/{device_id}/data
  publish: modax/sensor/{device_id}/safety
  subscribe: modax/control/{device_id}/command
```

**Wichtig:** KI-Ebene hat **KEINE** MQTT-Credentials und kann **nicht** publishen!

### 3. API-Berechtigungen

**Control Layer API (Port 8000):**
```python
# Öffentliche Endpoints (Read-Only)
@app.get("/status")  # Alle dürfen lesen
@app.get("/devices")
@app.get("/devices/{id}/data")
@app.get("/devices/{id}/safety")

# Geschützte Endpoints (nur HMI mit Auth)
@app.post("/control/command")  # Erfordert Authentifizierung
@app.put("/config/update")

# Gesperrte Endpoints (KI hat keinen Zugriff)
@app.post("/safety/override")  # 403 Forbidden für KI-User
```

**AI Layer API (Port 8001):**
```python
# Nur Analyse-Endpoints (keine Steuerung)
@app.post("/analyze")  # KI-Analyse durchführen
@app.get("/models/info")  # Modell-Informationen
@app.post("/reset-wear/{device_id}")  # Nach Wartung (nur mit Admin-Auth)
```

### 4. Code-Struktur

**Separation of Concerns:**
```
python-control-layer/
├── safety_validator.py  # ❌ KI darf diesen Code NICHT importieren
├── motion_controller.py  # ❌ KI darf diesen Code NICHT importieren
├── control_api.py
└── data_aggregator.py

python-ai-layer/
├── anomaly_detector.py  # ✅ Nur Analyse
├── wear_predictor.py    # ✅ Nur Prognose
├── optimizer.py         # ✅ Nur Empfehlungen
└── ai_service.py        # ✅ Nur REST API
```

**Import-Restrictions:**
- AI Layer **darf NICHT** Control Layer Module importieren
- AI Layer **darf NICHT** MQTT-Client initialisieren
- Dependency-Management verhindert versehentliche Abhängigkeiten

---

## Validierungs-Checkliste

Für jede neue KI-Funktion:

- [ ] **Funktions-Check:** Ist es Analyse/Empfehlung oder Steuerung?
- [ ] **Safety-Check:** Kann es Sicherheit beeinflussen? → Dann VERBOTEN
- [ ] **Echtzeit-Check:** Ist es zeitkritisch? → Dann VERBOTEN in KI
- [ ] **Autonomie-Check:** Wird automatisch ausgeführt? → Dann VERBOTEN
- [ ] **Audit-Check:** Wird geloggt? → Muss sein für alle KI-Empfehlungen
- [ ] **Confidence-Check:** Hat es Confidence-Level? → Erforderlich
- [ ] **Explainability-Check:** Ist es erklärbar? → Sollte sein

---

## Beispiel-Szenarien

### Szenario 1: Vibration zu hoch ✅ KORREKT

**KI erkennt:**
```python
if vibration > threshold:
    recommendation = {
        "type": "safety_warning",
        "priority": "high",
        "action": "High vibration detected. Stop machine and inspect bearings.",
        "confidence": 0.92
    }
    # ✅ Speichern für HMI
    store_recommendation(recommendation)
    
    # ✅ Alarm auslösen (informativ)
    send_notification("Vibration zu hoch!")
```

**Was KI NICHT tut:**
```python
# ❌ VERBOTEN: Direkt stoppen
# control_layer.stop_machine()

# ❌ VERBOTEN: Safety-Override
# control_layer.disable_vibration_check()
```

**Korrekter Ablauf:**
1. KI erkennt und meldet
2. HMI zeigt Warnung
3. **Bediener** entscheidet: Stop oder Weiter (auf eigene Verantwortung)
4. Falls Bediener stoppt: Control Layer validiert und führt aus

### Szenario 2: Wartung empfohlen ✅ KORREKT

**KI prognostiziert:**
```python
remaining_hours = predict_remaining_life(wear_data)
if remaining_hours < 48:
    recommendation = {
        "type": "maintenance",
        "priority": "high",
        "action": "Schedule bearing replacement within 48 hours",
        "confidence": 0.85,
        "remaining_hours": remaining_hours
    }
    # ✅ Empfehlung speichern
    create_maintenance_ticket(recommendation)
```

**Korrekter Ablauf:**
1. KI erstellt Wartungs-Ticket (informativ)
2. Wartungsplaner sieht Ticket
3. **Planer** entscheidet: Wann und wie
4. Wartung wird manuell durchgeführt
5. Wear-Counter wird zurückgesetzt (nach Bestätigung)

### Szenario 3: Parameter-Optimierung ❌ FALSCH vs. ✅ KORREKT

**❌ FALSCH (automatisch):**
```python
# KI schlägt vor
optimal_feed_rate = 150  # mm/min

# ❌ VERBOTEN: Automatisch anwenden
cnc_controller.set_feed_rate(optimal_feed_rate)
```

**✅ KORREKT (mit Bestätigung):**
```python
# KI schlägt vor
optimal_feed_rate = 150  # mm/min
recommendation = {
    "type": "optimization",
    "priority": "low",
    "action": f"Increase feed rate to {optimal_feed_rate} mm/min",
    "expected_benefit": "20% faster cycle time",
    "confidence": 0.70
}

# ✅ In HMI anzeigen
store_recommendation(recommendation)

# Bediener sieht Empfehlung in HMI
# Bediener klickt "Anwenden"
# HMI sendet POST /control/command mit neuem Wert
# Control Layer validiert und setzt Parameter
```

---

## Audit & Compliance

### Logging-Anforderungen

**Alle KI-Aktivitäten werden geloggt:**
```json
{
  "timestamp": "2025-12-27T10:30:00Z",
  "event_type": "ai_recommendation",
  "device_id": "esp32_001",
  "recommendation_type": "maintenance",
  "priority": "high",
  "action": "Inspect bearings",
  "confidence": 0.85,
  "applied": false,  // Wurde NICHT automatisch angewendet
  "operator_decision": null  // Warten auf Entscheidung
}
```

**Wenn Empfehlung umgesetzt wird:**
```json
{
  "timestamp": "2025-12-27T10:35:00Z",
  "event_type": "ai_recommendation_applied",
  "recommendation_id": "rec_12345",
  "operator": "john.doe",
  "method": "manual",  // Manuell durch Bediener
  "notes": "Bearing inspection scheduled for tomorrow"
}
```

### Zertifizierungs-Relevanz

**Für IEC 61508 / ISO 13849:**
- KI ist **NICHT** Teil der Safety-Funktion
- KI ist **NICHT** im SIL-Scope
- KI ist optional (System funktioniert ohne KI)
- KI-Ausfall hat **KEINE** Safety-Auswirkung

**Begründung für Auditoren:**
> "Die KI-Ebene ist vollständig vom Sicherheitssystem getrennt. Alle sicherheitsrelevanten Entscheidungen werden deterministisch in der Steuerungsebene oder Feldebene getroffen. Ein Ausfall oder Fehler der KI-Ebene führt lediglich zum Verlust von Analysefunktionen, nicht aber zu einem unsicheren Zustand."

---

## Zusammenfassung

**Kernprinzipien:**
1. ✅ KI analysiert, empfiehlt, informiert
2. ❌ KI steuert NICHT, entscheidet NICHT (in Safety/Echtzeit)
3. ✅ Mensch oder deterministische Logik validiert KI-Empfehlungen
4. ✅ Architektonische Barrieren verhindern KI-Steuerung
5. ✅ Alle KI-Aktivitäten sind auditierbar

**Grenzen:**
- **Sperrzonen:** Safety, Echtzeit-Steuerung, automatische Parameter-Änderung
- **Erlaubte Zonen:** Analyse, Prognose, Empfehlungen, Reporting

**Durchsetzung:**
- Netzwerk-Segmentierung
- MQTT ACLs
- API-Berechtigungen
- Code-Struktur
- Audit-Logging

---

**Revision:**
- **Erstellt:** 2025-12-27
- **Nächste Review:** Bei Architekturänderungen oder ADRs
- **Verantwortlich:** Safety-Architect

**Referenzen:**
- [ADR-0002: No AI in Control](../09-decisions/adr-0002-no-ai-in-control.md)
- [4-Ebenen-Modell](layer-model.md)
- [KI-Ebene Details](../05-analytics-and-ml-layer/constraints.md)
