# Hobbyist & Desktop CNC Systems Support

## Übersicht

Zusätzlich zu industriellen CNC-Steuerungssystemen unterstützt MODAX auch hobbyistische und Desktop-CNC-Systeme, die einzigartige Funktionen für kleinere Maschinen, Maker-Spaces und Desktop-Fertigung bieten.

**Version:** 0.4.0  
**Zuletzt aktualisiert:** 2025-12-07

---

## Estlcam - Desktop CNC Software

Estlcam ist eine beliebte Software für Desktop-CNC-Maschinen und bietet CAM-Funktionalität mit integrierter Maschinensteuerung, die sich besonders an Hobbyisten und Maker richtet.

### Hauptfunktionen

#### 1. CAM & Steuerungssoftware

Estlcam kombiniert CAM-Programmierung mit direkter Maschinensteuerung in einer integrierten Anwendung.

**Hauptmerkmale:**
- G-Code-Generierung aus 2D/3D-Designs
- Direkte Maschinensteuerung ohne separate Control-Software
- Echtzeit-Visualisierung des Werkzeugpfads
- Integrierter Postprozessor für verschiedene Maschinen

#### 2. Bild- und QR-Code-Bearbeitung

Eine einzigartige Funktion von Estlcam ist die Möglichkeit, Bearbeitungsprogramme direkt aus Bilddateien zu generieren.

**Unterstützte Formate:**
- PNG (Portable Network Graphics)
- JPG/JPEG (Joint Photographic Experts Group)
- GIF (Graphics Interchange Format)
- BMP (Bitmap)

**Anwendungsfälle:**
```
Image-to-Toolpath Konvertierung:
1. Logo-Gravur aus PNG-Dateien
2. QR-Code-Fräsen für Produktkennzeichnung
3. Foto-Relief-Fräsen (2.5D)
4. Schablonen aus Bitmap-Grafiken
```

**Workflow:**
1. Bilddatei importieren
2. Kontrast und Schwellenwerte anpassen
3. Bearbeitungsstrategie wählen (Gravieren, Fräsen, Relief)
4. Werkzeug- und Schnittparameter definieren
5. G-Code generieren und ausführen

#### 3. Alternative Steuerungsmethoden

Estlcam bietet flexible Steuerungsoptionen, die über Standard-Tastatur-/Maussteuerung hinausgehen:

##### Gamepad-Steuerung
- Jog-Bewegungen über Analog-Sticks
- Digitale Tasten für Schnellbefehle
- Anpassbare Button-Belegung
- Unterstützung für Xbox/PlayStation-Controller

**Vorteile:**
- Intuitive Bedienung mit beiden Händen
- Präzise analoge Geschwindigkeitssteuerung
- Kostengünstige Alternative zu industriellen Pendants

##### Handrad-Pendant
- Manuelle Positionierung mit Präzision
- Achsenauswahl über Drehschalter
- Schrittweiten-Auswahl (0.01mm - 1mm - 10mm)
- Enable/Disable-Schalter

**MPG (Manual Pulse Generator) Unterstützung:**
- Standard-Handräder mit USB-Anschluss
- Encoder-basierte Eingabe
- Echtzeit-Feedback auf Display

##### Tastatur und Maus
- Standard-Jog-Tasten (Pfeiltasten, PageUp/Down)
- Mausklick-Positionierung in Visualisierung
- Shortcuts für häufige Befehle
- Anpassbare Tastenbelegung

**Standard-Tastenbelegungen:**
```
Pfeiltasten:    X/Y-Bewegung
PageUp/Down:    Z-Achse
Shift + Pfeil:  Schnellvorschub
Ctrl + Pfeil:   Mikroschritte
Space:          Pause/Resume
ESC:            Stop
Home:           Referenzfahrt
```

#### 4. Winkelfehler-Kompensation

Eine spezielle Funktion zur werkstückbezogenen Einrichtung, die Ausrichtungsfehler ausgleicht.

**Funktionsweise:**
1. Werkstück auf Maschinentisch positionieren (mit leichter Schräglage)
2. Zwei oder mehr Referenzpunkte auf dem Werkstück antasten
3. Software berechnet Rotationsmatrix automatisch
4. G-Code wird in Echtzeit transformiert

**Vorteile:**
- Kein präzises Ausrichten des Werkstücks erforderlich
- Zeitersparnis bei der Werkstück-Einrichtung
- Reduziert Materialverschwendung
- Ideal für ungleichmäßige oder bereits bearbeitete Rohlinge

**Mathematischer Hintergrund:**
```
Transformation = Rotation_Matrix × Original_Position
Rotation_Matrix wird aus Referenzpunkten berechnet
```

### 5. Fernsteuerungs-API (Experimental)

Estlcam bietet eine experimentelle API zur Fernsteuerung über externe Programme.

⚠️ **Hinweis:** Diese API ist als experimentell markiert und kann sich in zukünftigen Versionen ändern.

#### START-Befehle

##### START LOCAL
Startet ein G-Code-Programm relativ zur aktuellen Maschinenposition.

**Syntax:**
```
START LOCAL
```

**Verwendung:**
- Programm beginnt an der aktuellen Position als Nullpunkt
- Ideal für wiederholende Operationen an verschiedenen Positionen
- Werkstück-Koordinatensystem wird temporär an aktueller Position gesetzt

**Beispiel-Szenario:**
```
1. Maschine zu Position (X=50, Y=50) fahren
2. "START LOCAL" aufrufen
3. Programm läuft mit (50, 50) als neuem (0, 0)
```

##### START AT FIRST COORDINATE
Startet ein Programm relativ zur ersten Koordinate im Programm.

**Syntax:**
```
START AT FIRST COORDINATE
```

**Verwendung:**
- Programm beginnt mit Offset zur ersten programmierten Position
- Werkstück kann an verschiedenen Positionen platziert werden
- Erste G-Code-Koordinate wird als Referenz verwendet

#### Programm-Abfragebefehle

Diese Befehle ermöglichen es, Programminformationen abzufragen, bevor das Programm ausgeführt wird.

##### Gesamtausdehnung abfragen

**PROG DX?**
Fragt die Gesamtausdehnung in X-Richtung ab.

```
Befehl:   PROG DX?
Antwort:  <Wert in mm>
Beispiel: 125.5
```

**PROG DY?**
Fragt die Gesamtausdehnung in Y-Richtung ab.

```
Befehl:   PROG DY?
Antwort:  <Wert in mm>
Beispiel: 85.0
```

**PROG DZ?**
Fragt die Gesamtausdehnung in Z-Richtung ab.

```
Befehl:   PROG DZ?
Antwort:  <Wert in mm>
Beispiel: -15.5
```

**Anwendungsfall:**
- Kollisionsprüfung vor Programmstart
- Werkstück-Platzbedarf ermitteln
- Automatische Maschinenauswahl basierend auf Bauteilgröße

##### Min/Max-Koordinaten abfragen

**PROG MIN X? / PROG MAX X?**
Fragt minimale/maximale X-Koordinate ab.

```
Befehl:   PROG MIN X?
Antwort:  -50.5

Befehl:   PROG MAX X?
Antwort:  75.0
```

**PROG MIN Y? / PROG MAX Y?**
Fragt minimale/maximale Y-Koordinate ab.

**PROG MIN Z? / PROG MAX Z?**
Fragt minimale/maximale Z-Koordinate ab.

**Anwendungsfall:**
- Bounding-Box-Berechnung
- Arbeitsbereich-Validierung
- Sichere Positionierung vor Programmstart

#### Arbeitsverzeichnis-Befehl

**DIR**
Legt das Arbeitsverzeichnis für das Laden von CNC-Dateien fest.

**Syntax:**
```
DIR <pfad>
```

**Beispiele:**
```
DIR C:\CNC\Projekte\
DIR /home/user/gcode/
DIR .\relativ\pfad\
```

**Verwendung:**
- Zentrale Verwaltung von G-Code-Bibliotheken
- Programmatisches Wechseln zwischen Projekten
- Batch-Verarbeitung mehrerer Dateien

#### Kommunikations-Befehl

**REMOTE**
Legt das Antwortfenster für die Fernsteuerungs-Kommunikation fest.

**Syntax:**
```
REMOTE <window_handle>
```

**Verwendung:**
- Definiert das Zielfenster für API-Antworten
- Ermöglicht bidirektionale Kommunikation
- Erforderlich für Request-Response-Pattern

**Implementierung (Windows):**
```cpp
// C++ Beispiel
HWND hWnd = FindWindow(NULL, "Mein Steuerungsprogramm");
SendMessage(estlcam_hwnd, WM_COPYDATA, 
    (WPARAM)hWnd, (LPARAM)&"REMOTE");
```

### Estlcam in MODAX Integration

MODAX kann als übergeordnetes Steuerungssystem mit Estlcam als CAM-Preprocessor integriert werden:

**Integrationsmöglichkeiten:**
1. **G-Code Import:** Von Estlcam generierte Programme in MODAX ausführen
2. **Fernsteuerungs-API Bridge:** MODAX steuert Estlcam über API-Befehle
3. **Sensor-Integration:** MODAX-Sensordaten zur Estlcam-Prozessoptimierung nutzen
4. **Hybridansatz:** Estlcam für CAM, MODAX für Maschinensteuerung und Überwachung

**Vorteile der Integration:**
- Estlcam's intuitive CAM-Oberfläche
- MODAX's industrielle Steuerungs- und KI-Features
- Sensor-basierte Prozessüberwachung
- Predictive Maintenance für Desktop-Maschinen

---

## UCCNC - Universal CNC Controller

UCCNC ist eine vielseitige CNC-Steuerungssoftware, die verschiedene Motion-Controller unterstützt.

### Übersicht

**UCCNC** (Universal CNC Controller) ist eine professionelle CNC-Steuerungssoftware für Windows, die mit verschiedenen Motion-Control-Hardware-Plattformen arbeitet.

### Hauptmerkmale

#### Unterstützte Hardware
- **UC100:** USB Motion Controller
- **UC300:** Ethernet Motion Controller (5-Achsen)
- **UC400ETH:** Erweiterte Ethernet-Steuerung (6-Achsen)
- **Pokeys57CNC:** PoKeys-basierte Steuerung
- **Axbb-E:** Ethernet-basierte Steuerung

#### Software-Features
- Bis zu 6-Achsen-Steuerung
- Makro-Unterstützung (VB.NET Scripts)
- Plugin-System für Erweiterungen
- Touchscreen-optimierte Oberfläche
- Werkzeugverwaltung mit Verschleiß-Tracking
- Probing- und Auto-Leveling-Funktionen

### Dokumentationszugang

⚠️ **Wichtiger Hinweis zur Dokumentation**

Das offizielle UCCNC-Benutzerhandbuch sollte über folgende Quelle verfügbar sein:
```
URL: https://www.cncdrive.com/UCCNC/UCCNC_usersmanual.pdf
Status: Bei automatischer Analyse nicht zugänglich
```

**Alternative Dokumentationsquellen:**
1. **Offizielle Website:** https://www.cncdrive.com/
2. **Forum:** https://www.cnczone.com/forums/uccnc-software/
3. **YouTube-Tutorials:** Offizielle CNCdrive-Kanal
4. **Wiki:** Community-gepflegte Dokumentation

**Für detaillierte UCCNC-Informationen:**
- Manuelles Herunterladen der PDF-Dokumentation empfohlen
- Bei spezifischen Fragen: Hersteller-Support kontaktieren
- Community-Forum für Anwendungs-Tipps nutzen

### UCCNC G-Code-Dialekt

UCCNC verwendet weitgehend Standard-G-Code (ISO 6983), bietet aber auch einige spezifische Erweiterungen:

**Bekannte UCCNC-spezifische Codes:**
- Makro-Aufrufe über M-Codes (M1000-M9999)
- Plugin-spezifische G-Codes (variabel je nach Installation)
- Probing-Zyklen (herstellerspezifisch)

### MODAX Integration mit UCCNC

Da UCCNC primär als eigenständige Steuerungssoftware konzipiert ist, erfolgt die Integration mit MODAX typischerweise über:

1. **G-Code-Kompatibilität:**
   - MODAX-generierte Programme in UCCNC ausführen
   - Standard-ISO-Codes sind kompatibel
   - Herstellerspezifische Codes erfordern Mapping

2. **Datenexport:**
   - MODAX kann Sensor- und Produktionsdaten erfassen
   - Parallel zu UCCNC-Steuerung für Monitoring
   - Keine direkte Control-Übernahme

3. **Empfohlene Architektur:**
   ```
   [MODAX AI/Monitoring Layer]
           |
           v (Data Only)
   [UCCNC Control Software] --> [Motion Controller] --> [CNC Machine]
   ```

**Hinweis:** Direkte Steuerungsübernahme nicht empfohlen, da UCCNC als primäre Steuerung ausgelegt ist.

---

## Haas - Industrielle CNC-Maschinen

Haas Automation ist ein führender Hersteller von industriellen CNC-Maschinen mit proprietären Erweiterungen zum Standard-G-Code.

### Haas-spezifische G-Codes

#### G47 - Engraving (Gravieren)

Vereinfachte Gravierfunktion für Text und einfache Formen.

**Syntax:**
```gcode
G47 (Text) X__ Y__ Z__ I__ J__ D__ F__
```

**Parameter:**
- **X, Y:** Startposition der Gravur
- **Z:** Gravur-Tiefe (negativ)
- **I:** Zeichenhöhe
- **J:** Zeichenabstand
- **D:** Linienabstand (für mehrzeiligen Text)
- **F:** Vorschubgeschwindigkeit

**Beispiel:**
```gcode
G90 G54
T1 M06 (Gravierwerkzeug)
M03 S3000
G47 (HAAS CNC) X10.0 Y10.0 Z-0.5 I5.0 J0.5 D6.0 F200
M05
M30
```

**Verwendung:**
- Seriennummern-Gravur
- Produktkennzeichnung
- Logo-Beschriftung
- Datums-/Chargennummer-Stempel

**Vorteile:**
- Keine separate CAM-Programmierung erforderlich
- Direkte Texteingabe im G-Code
- Automatische Buchstaben-Definition
- Schnelle Einrichtung für einfache Gravuren

#### G71 - Turning Roughing Cycle (Radial)

Schrupp-Zyklus für Drehmaschinen in radialer Richtung.

**Syntax:**
```gcode
G71 P__ Q__ U__ W__ D__ F__ S__
```

**Parameter:**
- **P:** Startblock-Nummer der Fertigteilkontur
- **Q:** Endblock-Nummer der Fertigteilkontur
- **U:** Aufmaß in X-Richtung (radial)
- **W:** Aufmaß in Z-Richtung
- **D:** Zustelltiefe pro Schnitt
- **F:** Vorschubgeschwindigkeit
- **S:** Spindeldrehzahl

**Beispiel:**
```gcode
G00 X100.0 Z5.0
G71 P100 Q200 U1.0 W0.5 D2.0 F0.3 S800
N100 G00 X50.0  (Start Fertigteilkontur)
N110 G01 Z-50.0 F0.15
N120 G01 X80.0 Z-65.0
N130 G01 Z-100.0
N200 G01 X100.0  (Ende Fertigteilkontur)
```

**Verwendung:**
- Automatisches Schruppen von Außenkonturen
- Zeitersparnis durch automatische Zustellberechnung
- Konstante Schnittbedingungen
- Optimale Werkzeug- und Maschinenauslastung

#### G72 - Turning Roughing Cycle (Facing)

Schrupp-Zyklus für Drehmaschinen in axialer Richtung (Plandrehen).

**Syntax:**
```gcode
G72 P__ Q__ U__ W__ D__ F__ S__
```

**Parameter:** (analog zu G71)
- **P:** Startblock-Nummer
- **Q:** Endblock-Nummer
- **U:** Aufmaß in X-Richtung
- **W:** Aufmaß in Z-Richtung
- **D:** Zustelltiefe pro Schnitt (axial)
- **F:** Vorschubgeschwindigkeit
- **S:** Spindeldrehzahl

**Beispiel:**
```gcode
G00 X120.0 Z2.0
G72 P300 Q400 U1.0 W0.5 D2.0 F0.3 S600
N300 G00 Z-50.0  (Start Fertigteilkontur)
N310 G01 X50.0 F0.15
N320 G01 Z-70.0 X30.0
N330 G01 X20.0
N400 G01 Z-80.0  (Ende Fertigteilkontur)
```

**Verwendung:**
- Planflächen-Bearbeitung
- Große Stirnflächen effizient schruppen
- Taschenfräsen auf Drehmaschinen
- Reduziert Programmieraufwand erheblich

**Unterschied G71 vs. G72:**
```
G71: Schnitte parallel zur Z-Achse (außen nach innen)
G72: Schnitte parallel zur X-Achse (vorne nach hinten)
```

### Haas-spezifische M-Codes

#### M130 - Media Player Control

Steuert den integrierten Media Player der Haas-Maschine.

**Syntax:**
```gcode
M130 (Dateiname.mp4)
```

**Funktionalität:**
- Spielt Video-/Audio-Dateien während der Bearbeitung
- Operator-Anweisungen als Video-Tutorial
- Musik zur Arbeitsumgebungsverbesserung
- Wartungsanweisungen visuell darstellen

**Beispiel:**
```gcode
O1000
(Setup-Anweisungen Video abspielen)
M130 (SETUP-PART-123.mp4)
M00 (Stop für Operator-Interaktion)

(Hauptprogramm)
T1 M06
G54 G90
M03 S1200
G00 X0 Y0 Z50
...
M30
```

**Anwendungsfälle:**
1. **Schulung:** Video-Tutorials für neue Mitarbeiter
2. **Setup-Hilfe:** Visuelles Werkstück-Positionierungs-Tutorial
3. **Qualitätskontrolle:** Prüfanweisungen als Video
4. **Entertainment:** Musik während langen Bearbeitungen

**Technische Details:**
- Unterstützte Formate: MP4, AVI, WMV
- Dateien auf USB-Stick oder Maschinen-Speicher
- Automatische Pause/Resume bei Maschinenstop
- Display-Integration im HMI

### Haas Control System

**NGC (Next Generation Control):**
- Proprietäre Steuerung von Haas
- Erweiterte Makro-Funktionalität
- Integriertes HMI mit Touchscreen
- Wireless-Probing-Unterstützung
- VPS (Visual Programming System)

**Integration mit MODAX:**
- G-Code-Kompatibilität für Standard-Operationen
- Haas-spezifische Codes optional nutzbar
- Sensor-Daten parallel erfassbar
- Produktions-Monitoring ohne Steuerungseingriff

---

## Vergleichstabelle: Hobbyist vs. Industrial CNC

| Feature | Estlcam | UCCNC | Haas |
|---------|---------|-------|------|
| **Zielgruppe** | Hobbyist, Maker | Semi-Pro, Retrofit | Industrial |
| **Preis** | € 50-100 | € 150-300 | > € 10.000 |
| **Max. Achsen** | 4 | 6 | 5+ |
| **CAM integriert** | ✅ Ja | ❌ Nein | ⚠️ Optional (VPS) |
| **Bildverarbeitung** | ✅ Ja (PNG/JPG) | ❌ Nein | ❌ Nein |
| **Makros** | ⚠️ Basis | ✅ VB.NET | ✅ Fanuc Macro B |
| **Fernsteuerung** | ✅ API | ⚠️ Plugin | ⚠️ Proprietary |
| **Open Source** | ❌ Nein | ❌ Nein | ❌ Nein |
| **Hardware-Support** | Arduino, Grbl | UC100/300/400 | Proprietär |

---

## MODAX Integrations-Empfehlungen

### Für Hobbyisten (Estlcam)

**Empfohlene Architektur:**
```
[Estlcam CAM & Control]
         |
         v (G-Code oder API)
[MODAX Monitoring Layer]
         |
         v (Sensor Data)
[AI Analysis & Predictive Maintenance]
```

**Vorteile:**
- Estlcam für einfache CAM-Programmierung
- MODAX für erweiterte Überwachung
- KI-basierte Prozessoptimierung
- Kostengünstige Komplettlösung

### Für Semi-Professional (UCCNC)

**Empfohlene Architektur:**
```
[CAM Software (Fusion 360, etc.)]
         |
         v (G-Code)
[UCCNC Control] ←→ [MODAX Monitoring]
         |              |
         v              v
    [Machine]    [AI Analytics]
```

**Vorteile:**
- UCCNC als zuverlässige Primärsteuerung
- MODAX für Production Intelligence
- Getrennte Verantwortlichkeiten
- Maximale Stabilität

### Für Industrial (Haas)

**Empfohlene Architektur:**
```
[Haas NGC Control] (Primär)
         |
         v (Parallel Data Collection)
[MODAX IoT Gateway]
         |
         v
[Central MODAX System]
         |
         v
[Fleet Analytics & AI]
```

**Vorteile:**
- Keine Eingriffe in Haas-Steuerung
- Flottenweite Datenerfassung
- Zentrale KI-Analyse
- Predictive Maintenance
- OEE-Optimierung

---

## Sicherheitshinweise

⚠️ **WICHTIG:** Bei der Integration von hobbyistischen und industriellen Systemen:

1. **Trennung der Safety-Systeme:**
   - Steuerungssoftware bleibt primäres Safety-System
   - MODAX nur für Monitoring und nicht-sicherheitskritische Funktionen
   - Hardware-E-Stop unabhängig von Software

2. **Datenintegrität:**
   - Keine Echtzeitsteuerung über externe APIs
   - Lesender Zugriff bevorzugen
   - Validierung aller externen Befehle

3. **Compliance:**
   - CE-Konformität bei industriellen Maschinen beachten
   - Sicherheitsrichtlinien (ISO 12100, ISO 13849) einhalten
   - Dokumentation aller Modifikationen

---

## Weiterführende Ressourcen

### Estlcam
- **Website:** https://www.estlcam.de/
- **Forum:** https://www.estlcam.de/forum/
- **Video-Tutorials:** YouTube-Kanal "Estlcam"
- **Download:** https://www.estlcam.de/download.php

### UCCNC
- **Website:** https://www.cncdrive.com/
- **Handbuch:** https://www.cncdrive.com/UCCNC/UCCNC_usersmanual.pdf
- **Forum:** CNCZone UCCNC Section
- **Support:** support@cncdrive.com

### Haas
- **Website:** https://www.haascnc.com/
- **G-Code Quick Reference:** https://www.haascnc.com/service/codes-settings.html
- **Mill Operator's Manual:** Verfügbar auf Haas-Website
- **Lathe Programming Manual:** Verfügbar auf Haas-Website
- **Video-Training:** HFO (Haas Factory Outlet) YouTube

---

## Zusammenfassung

Die Unterstützung von Hobbyist- und Desktop-CNC-Systemen erweitert MODAX's Anwendungsbereich:

✅ **Estlcam:** Ideale CAM-Software für Maker mit einzigartiger Bildverarbeitung  
✅ **UCCNC:** Professionelle Control-Software für Retrofit-Maschinen  
✅ **Haas:** Industrieller Standard mit nützlichen proprietären Features  

**MODAX-Mehrwert:**
- Einheitliche Überwachung über alle Maschinentypen
- KI-Analyse für Hobby- und Industriemaschinen
- Flottenweite Optimierung
- Predictive Maintenance unabhängig vom Control-System

---

**Letzte Aktualisierung:** 2025-12-07  
**Nächste Review:** 2025-03-07  
**Autor:** Thomas Heisig / MODAX Development Team
