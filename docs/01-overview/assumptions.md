# MODAX – Technische und organisatorische Annahmen

Dieses Dokument dokumentiert die grundlegenden Annahmen, die bei der Entwicklung von MODAX getroffen wurden. Diese Annahmen definieren den Geltungsbereich und die Grenzen des Systems.

---

## Technische Annahmen

### Hardware

#### Feldebene (ESP32)

**Annahmen:**
- ESP32-Mikrocontroller sind verfügbar und funktionsfähig
- Sensoren (ACS712, MPU6050, DS18B20) liefern zuverlässige Werte
- WiFi-Netzwerk ist verfügbar (WLAN-Abdeckung)
- Stromversorgung ist stabil (5V DC)
- Hardware-Safety-Interlocks sind vorhanden und getestet

**Limitierungen:**
- Flash-Speicher: ~4 MB (begrenzt Firmware-Größe)
- RAM: ~520 KB (begrenzt Datenstrukturen)
- CPU: 240 MHz (begrenzt Berechnungskomplexität)
- WiFi-Reichweite: typisch 50-100m indoor

**Nicht angenommen:**
- Fehlerfreie Hardware (Fail-Safe-Design kompensiert Ausfälle)
- Konstante Netzwerkverbindung (Auto-Reconnect implementiert)
- Unbegrenzte Lebenszeit (Verschleiß wird erwartet)

#### Steuerungs- und KI-Ebene (Server/PC)

**Annahmen:**
- x86/ARM-CPU mit mindestens 2 Cores
- Mindestens 4 GB RAM
- Netzwerkverbindung verfügbar
- Betriebssystem: Linux (bevorzugt) oder Windows
- Python 3.8+ Runtime verfügbar

**Empfohlene Konfiguration:**
- 4+ Cores (für parallele Verarbeitung)
- 8+ GB RAM (für größere Deployments)
- SSD Storage (für schnelle Datenbank-Zugriffe)
- Gigabit Ethernet

#### HMI-Ebene (Client)

**Annahmen:**
- Windows 10/11 Betriebssystem
- .NET 8.0 Runtime installiert
- Bildschirmauflösung mindestens 1280x720
- Maus und Tastatur verfügbar
- Netzwerkverbindung zu Steuerungsebene

**Nicht angenommen:**
- Touch-Screen (aber unterstützt)
- Multi-Monitor-Setup (aber unterstützt)
- Hochauflösende Displays (UI skaliert)

### Netzwerk

#### Topologie

**Annahmen:**
- TCP/IP-Netzwerk verfügbar
- MQTT Broker erreichbar (Mosquitto/HiveMQ)
- Keine NAT zwischen Feldebene und Steuerung (bevorzugt)
- Firewall-Regeln erlauben erforderliche Ports

**Erforderliche Ports:**
- 1883: MQTT (unverschlüsselt)
- 8883: MQTT over TLS (optional)
- 8000: Control Layer REST API
- 8001: AI Layer REST API

**Latenz-Annahmen:**
- MQTT: <50 ms (LAN)
- REST API: <100 ms (LAN)
- Internet-Zugriff: nicht erforderlich (außer für Updates)

#### Sicherheit

**Annahmen:**
- Netzwerk ist **nicht** von vornherein vertrauenswürdig
- OT/IT-Trennung wird empfohlen (Purdue-Modell)
- Firewall zwischen Ebenen ist möglich
- VPN für Remote-Zugriff wird empfohlen

**Nicht angenommen:**
- Verschlüsselung ist standardmäßig aktiv (muss konfiguriert werden)
- Authentifizierung ist standardmäßig aktiv (Basic Auth verfügbar)

### Software-Abhängigkeiten

#### Python-Umgebung

**Annahmen:**
- Python 3.8, 3.9, 3.10, 3.11 oder 3.12 verfügbar
- pip installiert
- Virtuelle Umgebungen (venv) nutzbar
- Alle Dependencies in requirements.txt sind verfügbar

**Kritische Abhängigkeiten:**
- FastAPI (Web-Framework)
- paho-mqtt (MQTT-Client)
- NumPy, scikit-learn (KI-Ebene)

**Annahme zu Updates:**
- Dependencies werden regelmäßig aktualisiert (Dependabot)
- Breaking Changes werden in Minor-Versions vermieden

#### .NET-Umgebung

**Annahmen:**
- .NET 8.0 SDK/Runtime installiert
- Windows Forms verfügbar
- NuGet-Pakete sind erreichbar

#### C++-Umgebung (ESP32)

**Annahmen:**
- PlatformIO installiert
- Arduino ESP32 Core verfügbar
- USB-Treiber für ESP32 installiert

### Datenbank

**Annahmen:**
- Für Prototyp: Keine Datenbank erforderlich (In-Memory)
- Für Produktion: PostgreSQL oder TimescaleDB empfohlen
- Datenpersistenz ist konfigurierbar

**Nicht angenommen:**
- Unbegrenzte Datenspeicherung (Retention Policies erforderlich)
- Echtzeit-Datenbank (Time-Series-DB empfohlen)

---

## Organisatorische Annahmen

### Einsatzumgebung

#### Industrielle Umgebung

**Annahmen:**
- Betrieb in Produktionshalle / Werkstatt
- Umgebungstemperatur: 0-40°C (typisch)
- Luftfeuchtigkeit: 20-80% (nicht kondensierend)
- Elektrische Störungen (EMI) vorhanden
- Mechanische Vibrationen möglich

**Nicht angenommen:**
- Ex-Schutz-Umgebung (ATEX-Zertifizierung nicht vorhanden)
- Outdoor-Einsatz (IP-Schutzklasse nicht spezifiziert)
- Extremtemperaturen (<0°C, >40°C)

#### Hobbyisten-Umgebung

**Annahmen:**
- Betrieb in Werkstatt / Garage / Maker-Space
- Stabilere Umgebungsbedingungen als Industrie
- Niedrigere Safety-Anforderungen (aber Safety-Features vorhanden)

### Bediener-Kompetenz

#### Industrielle Anwender

**Annahmen:**
- Grundkenntnisse in CNC-Bedienung
- Vertrautheit mit G-Code (für CNC-Anwendungen)
- Grundverständnis von Maschinensteuerung
- Schulung vor Inbetriebnahme erforderlich

**Nicht angenommen:**
- Programmierkenntnisse erforderlich (für Betrieb)
- Detailliertes Verständnis von KI/ML
- Netzwerk-Administration (für Basis-Betrieb)

#### Hobbyisten

**Annahmen:**
- Technisches Interesse und Lernbereitschaft
- Grundkenntnisse in Linux/Windows-Administration (hilfreich)
- Bereitschaft, Dokumentation zu lesen

### Support und Wartung

**Annahmen:**
- Community-basierter Support (GitHub Issues/Discussions)
- Selbst-Wartung durch Anwender (Open-Source)
- Keine 24/7-Support-Verfügbarkeit
- Keine SLAs (Service Level Agreements)

**Für Enterprise:**
- Kommerzielle Support-Verträge können existieren (zukünftig)
- Customization und Consulting möglich

### Rechtliche Annahmen

#### Haftung

**Annahmen:**
- Software wird "AS IS" bereitgestellt (MIT-Lizenz)
- Keine Gewährleistung oder Garantie
- Anwender sind für Risikobewertung verantwortlich
- Anwender sind für Einhaltung lokaler Gesetze verantwortlich

**Disclaimer:**
- MODAX ist **nicht zertifiziert** für sicherheitskritische Anwendungen
- Formale Risikobewertung durch Anwender erforderlich
- Einsatz auf eigenes Risiko

#### Compliance

**Annahmen:**
- Anwender sind verantwortlich für:
  - CE-Kennzeichnung (falls erforderlich)
  - Maschinenrichtlinien-Konformität
  - Arbeitsschutz-Vorschriften
  - Versicherung

---

## Szenario-spezifische Annahmen

### Szenario 1: Einzelne CNC-Fräsmaschine (Hobbyist)

**Annahmen:**
- 1 ESP32 Feldgerät
- Alle Ebenen auf einem PC
- Lokales Netzwerk (kein Internet erforderlich)
- Bediener ist technisch versiert
- Niedrigere Safety-Anforderungen (aber grundlegende Safety-Features aktiv)

### Szenario 2: Kleine Produktionslinie (5-10 Maschinen)

**Annahmen:**
- 5-10 ESP32 Feldgeräte
- Dedizierter Server für Control/AI Layer
- Lokales Netzwerk mit Firewall
- Geschulte Bediener
- Höhere Safety-Anforderungen
- Regelmäßige Wartungsfenster

### Szenario 3: Großer Maschinenpark (50+ Maschinen)

**Annahmen:**
- 50+ ESP32 Feldgeräte
- Kubernetes-Cluster für Ebenen
- Enterprise-Netzwerk mit Segmentierung
- IT-Support-Team vorhanden
- Hohe Verfügbarkeitsanforderungen
- Compliance-Audits erforderlich

---

## Ausschlusskriterien

MODAX ist **nicht geeignet** für:

### Technisch

❌ **Echtzeit-harte Anforderungen <1 ms**  
   → ESP32 kann <10 ms, Python Control Layer ~100 ms

❌ **SIL 3/4 Safety-Anwendungen** (aktuell)  
   → Keine formale Zertifizierung

❌ **Autonome Fahrzeuge**  
   → ISO 26262 nicht erfüllt

❌ **Medizinische Geräte**  
   → MDR/FDA nicht erfüllt

❌ **Luftfahrt**  
   → DO-178C nicht erfüllt

### Organisatorisch

❌ **Unkritische Dateninfrastruktur**  
   → Backup und Disaster Recovery müssen geplant werden

❌ **Keine Wartungsfenster**  
   → Updates erfordern Downtime (aktuell)

❌ **Garantierte 100% Uptime**  
   → Keine SLAs, Community-Support

---

## Änderungsmanagement

### Annahmen über Änderungen

**Erwartete Änderungen:**
- Dependencies werden aktualisiert (minor/patch versions)
- Features werden hinzugefügt (backward-compatible)
- Bugs werden behoben

**Unerwartete Breaking Changes:**
- Werden in Major-Versions isoliert (1.x → 2.x)
- Mindestens 2 Minor-Versions Deprecation-Zeitraum
- Migration Guides werden bereitgestellt

### Annahmen über Rückwärtskompatibilität

**Garantiert:**
- REST API innerhalb Major-Version (v1.x)
- MQTT Topic-Schema innerhalb Major-Version
- Konfigurations-Format (mit Migrations-Hilfe)

**Nicht garantiert:**
- Interne Code-APIs (können sich ändern)
- Database-Schema (Migrationen erforderlich)
- Performance-Charakteristiken (können verbessert werden)

---

## Validierung der Annahmen

### Wie Annahmen getestet werden

- **Unit Tests:** Funktionale Annahmen
- **Integration Tests:** Ebenen-Interaktion
- **Performance Tests:** Latenz und Durchsatz
- **End-to-End Tests:** Reale Szenarien
- **User Acceptance Tests:** Mit Beta-Testern

### Feedback-Loop

Annahmen werden überprüft durch:
1. Community-Feedback (GitHub Issues)
2. Real-World-Deployments
3. Performance-Metriken
4. Fehlerberichte
5. Feature-Requests

Bei Verletzung kritischer Annahmen:
- Issue erstellen
- Impact-Analyse
- Architektur-Anpassung (falls erforderlich)
- Dokumentation aktualisieren

---

## Zusammenfassung

Diese Annahmen definieren den **Sweet Spot** von MODAX:

✅ **Gut geeignet für:**
- CNC-Maschinen-Steuerung (Hobbyist bis mittelgroße Industrie)
- Predictive Maintenance mit KI-Unterstützung
- Flexible, modulare Automatisierungslösungen
- Rapid Prototyping und Forschung

⚠️ **Bedingt geeignet für:**
- SIL 2 Anwendungen (mit Zertifizierung)
- Große Deployments (>100 Geräte)
- Mission-critical Applications (mit HA-Setup)

❌ **Nicht geeignet für:**
- SIL 3/4, Medizin, Luftfahrt, Automotive
- Harte Echtzeit <1 ms
- Vollautonome Systeme ohne menschliche Überwachung

---

**Revision:**
- **Erstellt:** 2025-12-27
- **Nächste Review:** 2026-06-27
- **Verantwortlich:** Projekt-Maintainer
