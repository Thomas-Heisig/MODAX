# Extended G-Code Support and Interpreter

## Übersicht

MODAX unterstützt eine umfangreiche Bibliothek von CNC G-Codes und M-Codes, einschließlich herstellerspezifischer Codes von Siemens, Fanuc, Heidenhain, Okuma und Mazak. Der neue G-Code-Interpreter ermöglicht die Ausführung von Programmen mit Kontrollfluss-Befehlen wie GOTO, GOSUB und RETURN.

## Neue Funktionen

### 1. Erweiterte Interpolations- und Zyklus-Codes

#### NURBS und High-Speed-Bearbeitung
- **G05**: High-Speed-Machining / NURBS-Interpolation
- **G05.1**: AI Contour Control / Look-Ahead (Heidenhain)
- **G07.1**: Zylindrische Interpolation
- **G107**: Zylindrische Koordinateninterpolation (Siemens)

#### Polare Interpolation
- **G12.1**: Polare Interpolationsmodus ein
- **G13.1**: Polare Interpolationsmodus aus

#### Erweiterte Bohrzyklen
- **G73**: Hochgeschwindigkeits-Peckbohren
- **G74**: Linkshand-Gewindebohren
- **G34**: Lochkreis
- **G35**: Lochkreis mit Winkelinkrement

#### Threading (Gewinde)
- **G33**: Gewindeschneiden mit konstanter Steigung
- **G76**: Feinbohr-Zyklus / Gewindezyklus
- **G84.2**: Rechtsgewindebohren
- **G84.3**: Linksgewindebohren

### 2. Arbeitsbereichsbegrenzung und Messung

#### Arbeitsbereich
- **G22**: Arbeitsbereichsbegrenzung ein
- **G23**: Arbeitsbereichsbegrenzung aus
- **G25**: Spindeldrehzahl-Schwankungserkennung aus
- **G26**: Spindeldrehzahl-Schwankungserkennung ein

#### Werkzeugmessung und Taster
- **G31**: Sprungfunktion / Taster (Skip Function)
- **G36**: Automatische Werkzeugoffset-Messung
- **G37**: Automatische Werkzeuglängenmessung
- **G38**: Werkzeugdurchmesser-Messung
- **G38.2-G38.5**: Erweiterte Tasterfunktionen

### 3. Erweiterte Koordinatensysteme

- **G54.1 Pxx**: Erweitertes Werkstück-Koordinatensystem (P1-P300)
  - Beispiel: `G54.1 P10` aktiviert das 10. erweiterte Koordinatensystem
- **G98**: Rückkehr zum Anfangspunkt im Bohrzyklus
- **G99**: Rückkehr zum R-Punkt im Bohrzyklus

### 4. Erweiterte M-Codes

#### Spindelsteuerung
- **M19**: Spindelorientierung
- **M21**: Spindelgetriebe niedrig (hohes Drehmoment)
- **M22**: Spindelgetriebe hoch (hohe Drehzahl)
- **M29**: Starres Gewindeschneiden

#### Kühlmittelsteuerung
- **M50/M51**: Hochdruck-Kühlmittel ein/aus
- **M88**: Through-Spindle-Kühlmittel (durch Spindel)
- **M89**: Through-Tool-Kühlmittel (durch Werkzeug)

#### Vorschub-Override
- **M36**: Vorschub-Override-Bereichsbegrenzung ein
- **M37**: Vorschub-Override-Bereichsbegrenzung aus

#### Benutzerdefinierte M-Codes
- **M100-M199**: Benutzer-Makros (frei konfigurierbar)
- **M200+**: Makro-Aufrufe (z.B. Palettenwechsel bei Mazak)

#### Palettensteuerung (Mazak)
- **M200**: Palettenwechsel
- **M201**: Palette klemmen
- **M202**: Palette lösen
- **M203**: Palette drehen

### 5. Makro-Unterstützung

#### Fanuc Macro B
```gcode
O1000                    ; Makro-Programm O1000
G65 P1000 A10 B20 C5    ; Makro-Aufruf mit Parametern
#100=10.5                ; Variable setzen
```

#### Macro-Features
- **G65**: Makro-Aufruf (einmalig)
- **G66**: Modaler Makro-Aufruf
- **G67**: Modaler Makro-Aufruf abbrechen
- **O-Codes**: Programm-/Makronummer (z.B. O1000)
- **Variablen**: #1-#999 (Common Variables)

### 6. Kontrollfluss (Interpreter)

#### GOTO - Unbedingter Sprung
```gcode
N10 G00 X0 Y0
N20 G01 X100 F500
N30 GOTO N10           ; Springe zu N10
```

#### GOSUB/RETURN - Unterprogramm-Aufruf
```gcode
N10 G00 X0
N20 GOSUB SUB1        ; Rufe Unterprogramm auf
N30 M30

:SUB1                  ; Label für Unterprogramm
N100 G01 X50 F500
N110 M99              ; Rückkehr zum Hauptprogramm
```

#### Labels
Labels können mit oder ohne Doppelpunkt definiert werden:
```gcode
:START                 ; Label mit Doppelpunkt
LOOP                   ; Label ohne Doppelpunkt
N100                   ; N-Nummern dienen auch als Labels
```

### 7. Kommentare

Zwei Kommentar-Stile werden unterstützt:
```gcode
G00 X10 (Schnellpositionierung)  ; Parentheses-Style
G01 Y20 F500 ; Semicolon-Style   ; Semicolon-Style
```

### 8. Spindle Speed (S) und Feed Rate (F)

Die Parser erkennt und extrahiert S- und F-Werte:
```gcode
M03 S1200              ; Spindel CW mit 1200 RPM
G01 X100 F500          ; Linear mit 500 mm/min
G01 X100 Y50 F800 S1500 ; Kombiniert
```

API:
```python
cmd = parser.parse_line("G01 X100 F500 S1200", 1)
if cmd.has_spindle_speed():
    speed = cmd.get_spindle_speed()  # 1200.0
if cmd.has_feed_rate():
    feed = cmd.get_feed_rate()  # 500.0
```

## G-Code Interpreter Verwendung

### Grundlegende Verwendung

```python
from gcode_interpreter import GCodeInterpreter

# Interpreter erstellen
interpreter = GCodeInterpreter()

# Programm laden
program = """
O1000
G90 G54
N10 G00 X0 Y0
N20 GOSUB DRILL
M30

:DRILL
N100 G81 Z-10 R2 F100
M99
"""

interpreter.load_program(program)

# Programm ausführen
executed_commands = interpreter.execute_program()

# Log anzeigen
for log_entry in interpreter.get_execution_log():
    print(log_entry)
```

### Variablen verwenden

```python
# Variable setzen
interpreter.set_variable("#100", 42.5)

# Variable lesen
value = interpreter.get_variable("#100")  # 42.5

# Makro mit Parametern
program = """
G65 P1000 A10.5 B20.3
"""
interpreter.load_program(program)
interpreter.execute_program()

# Parameter werden als Variablen gespeichert
a_value = interpreter.get_variable("#A")  # 10.5
b_value = interpreter.get_variable("#B")  # 20.3
```

### Kontrollfluss-Beispiele

#### Einfache Schleife mit GOTO
```gcode
O2000
N10 #1=0                ; Zähler initialisieren

:LOOP_START
N20 #1=#1+1            ; Zähler erhöhen
N30 G00 X[#1*10]       ; Position basierend auf Zähler
N40 IF [#1 LT 5] GOTO LOOP_START  ; Wenn < 5, wiederholen
N50 M30
```

#### Verschachtelte Unterprogramme
```gcode
O3000
N10 GOSUB SUB1
M30

:SUB1
N100 G00 X100
N110 GOSUB SUB2        ; Verschachtelter Aufruf
N120 M99

:SUB2
N200 G01 Y100 F500
N210 M99
```

## Herstellerspezifische Codes

### Unterstützte Hersteller

Der Parser kann herstellerspezifische Codes identifizieren:

```python
parser = GCodeParser()

# Prüfen ob Code herstellerspezifisch ist
is_specific, mfr = parser.is_manufacturer_specific("G05")
# Returns: (True, "Siemens Sinumerik")

is_specific, mfr = parser.is_manufacturer_specific("G65")
# Returns: (True, "Fanuc (Macro B)")

# Liste aller unterstützten Systeme
supported = parser.supports_foreign_machine_codes()
# Returns: ["Siemens Sinumerik (G05, G107, CYCLE)", 
#           "Heidenhain TNC (G05.1, CYCL DEF)", ...]
```

### Siemens Sinumerik
- G05: High-Speed-Machining
- G107: Zylindrische Interpolation
- CYCLE Befehle (in Zukunft)

### Heidenhain TNC
- G05.1: AI Contour Control
- CYCL DEF Zyklen (in Zukunft)

### Fanuc Macro B
- G65/G66/G67: Makro-Aufrufe
- G54.1: Erweiterte Koordinatensysteme
- #-Variablen: Makro-Variablen

### Haas (NEU)
- **G47**: Engraving (Gravieren) - Vereinfachte Textgravur
- **G71**: Turning Roughing Cycle (Radial) - Schrupp-Zyklus für Drehmaschinen
- **G72**: Turning Roughing Cycle (Facing) - Plandrehen-Schrupp-Zyklus
- **M130**: Media Player Control - Steuert integrierten Media Player

**Beispiel G47 (Engraving):**
```gcode
G47 (PART-123) X10.0 Y10.0 Z-0.5 I5.0 J0.5 D6.0 F200
; Graviert "PART-123" bei (10,10) mit 5mm Höhe
```

**Beispiel G71 (Roughing):**
```gcode
G71 P100 Q200 U1.0 W0.5 D2.0 F0.3 S800
; Schruppt Kontur zwischen N100-N200 mit 2mm Zustellung
```

**Beispiel M130 (Media Player):**
```gcode
M130 (SETUP-INSTRUCTIONS.mp4)
; Spielt Setup-Video während Werkstückeinrichtung
```

### Okuma OSP
- VC-Befehle: Variable Code (in Zukunft)
- CALL OOxx: Makro-Aufrufe (in Zukunft)

### Mazak Mazatrol
- M200+ Serie: Palettensteuerung

### Estlcam (Hobbyist/Desktop CNC)
Estlcam ist eine spezialisierte Software für Desktop-CNC-Maschinen mit einzigartigen Features.
Siehe [HOBBYIST_CNC_SYSTEMS.md](HOBBYIST_CNC_SYSTEMS.md) für detaillierte Informationen zu:
- Bild- und QR-Code-Bearbeitung (PNG/JPG/GIF)
- Alternative Steuerungsmethoden (Gamepad, Handrad)
- Winkelfehler-Kompensation
- Fernsteuerungs-API (START LOCAL, PROG queries, etc.)

## API-Referenz

### GCodeParser

#### Methoden

**`parse_line(line: str, line_number: int) -> Optional[GCodeCommand]`**
Parst eine einzelne G-Code-Zeile.

**`parse_program(program: str) -> List[GCodeCommand]`**
Parst ein vollständiges G-Code-Programm.

**`validate_command(cmd: GCodeCommand) -> Tuple[bool, List[str]]`**
Validiert einen geparsten Befehl.

**`get_g_code_description(g_code: str) -> str`**
Gibt die Beschreibung eines G-Codes zurück.

**`get_m_code_description(m_code: str) -> str`**
Gibt die Beschreibung eines M-Codes zurück.

**`is_manufacturer_specific(g_code: str) -> Tuple[bool, str]`**
Prüft, ob ein G-Code herstellerspezifisch ist.

**`supports_foreign_machine_codes() -> List[str]`**
Gibt eine Liste der unterstützten Fremdhersteller-Systeme zurück.

### GCodeCommand

#### Attribute

- `line_number: int` - Zeilennummer
- `raw_line: str` - Original-Zeile
- `comment: str` - Kommentar
- `g_codes: List[str]` - Liste der G-Codes
- `m_codes: List[str]` - Liste der M-Codes
- `parameters: Dict[str, float]` - Parameter (X, Y, Z, F, S, etc.)
- `n_number: Optional[int]` - N-Nummer
- `tool_number: Optional[int]` - Werkzeugnummer
- `label: Optional[str]` - Label für GOTO/GOSUB
- `goto_target: Optional[str]` - GOTO-Ziel
- `gosub_target: Optional[str]` - GOSUB-Ziel
- `macro_call: Optional[str]` - Makro-Aufruf
- `macro_params: Dict[str, float]` - Makro-Parameter

#### Methoden

**`has_motion() -> bool`**
Prüft, ob Befehl Bewegungscode enthält.

**`has_coordinates() -> bool`**
Prüft, ob Befehl Koordinaten enthält.

**`get_target_position() -> Dict[str, float]`**
Gibt Zielposition zurück.

**`is_control_flow() -> bool`**
Prüft, ob Befehl Kontrollfluss ist (GOTO/GOSUB).

**`is_label() -> bool`**
Prüft, ob Befehl ein Label ist.

**`is_macro_call() -> bool`**
Prüft, ob Befehl ein Makro-Aufruf ist.

**`has_spindle_speed() -> bool`**
Prüft, ob S-Parameter vorhanden.

**`has_feed_rate() -> bool`**
Prüft, ob F-Parameter vorhanden.

**`get_spindle_speed() -> Optional[float]`**
Gibt Spindeldrehzahl zurück.

**`get_feed_rate() -> Optional[float]`**
Gibt Vorschubgeschwindigkeit zurück.

### GCodeInterpreter

#### Methoden

**`load_program(program_text: str) -> bool`**
Lädt und preprocessed ein G-Code-Programm.

**`execute_next_command() -> Tuple[Optional[GCodeCommand], bool]`**
Führt den nächsten Befehl aus.

**`execute_program(max_commands: int = 10000) -> List[GCodeCommand]`**
Führt das gesamte Programm aus.

**`get_variable(var_name: str) -> Optional[float]`**
Liest eine Variable.

**`set_variable(var_name: str, value: float)`**
Setzt eine Variable.

**`get_execution_log() -> List[str]`**
Gibt das Ausführungsprotokoll zurück.

**`reset()`**
Setzt den Interpreter-Status zurück.

## Sicherheitshinweise

⚠️ **WICHTIG**: Der Interpreter ist für Simulations- und Testzwecke konzipiert. Für die Ausführung auf echten CNC-Maschinen:

1. **Validierung**: Alle Befehle müssen vor der Ausführung validiert werden
2. **Sicherheitsprüfungen**: Implementieren Sie Bereichsprüfungen für alle Bewegungen
3. **E-Stop Integration**: Not-Aus muss jederzeit funktionieren
4. **Trockenläufe**: Testen Sie neue Programme immer im Simulationsmodus
5. **Schrittweise Ausführung**: Verwenden Sie Single-Block-Modus für neue Programme

## Beispiele

### Vollständiges Programm mit allen Features

```gcode
O5000 (Demo-Programm mit erweiterten Features)

; Initialisierung
G90 G54 G17               ; Absolut, WCS 1, XY-Ebene
G21                       ; Metrische Einheiten
G40 G49 G80               ; Kompensationen aus

; Spindel und Kühlmittel
M03 S1200                 ; Spindel CW, 1200 RPM
M88                       ; Through-Spindle-Kühlmittel

; Hauptprogramm
N10 G00 X0 Y0 Z50        ; Startposition
N20 #1=0                 ; Zähler initialisieren

:MAIN_LOOP
N30 #1=#1+1              ; Zähler erhöhen
N40 GOSUB DRILL_HOLE     ; Bohren
N50 G00 X[#1*25]         ; Nächste Position
N60 IF [#1 LT 4] GOTO MAIN_LOOP

; Ende
M09                       ; Kühlmittel aus
M05                       ; Spindel aus
G28 Z0                    ; Z nach Hause
M30                       ; Programmende

; Unterprogramm Bohren
:DRILL_HOLE
N100 G81 X[#1*25] Y25 Z-15 R2 F200
N110 M99                  ; Rückkehr

%
```

### Makro mit Parametern

```gcode
O1000 (Lochkreis-Makro)
; Parameter: A=Radius, B=Anzahl, C=Startwinkel

#10=#4001               ; Speichere A (Radius)
#11=#4002               ; Speichere B (Anzahl)
#12=#4003               ; Speichere C (Startwinkel)

#13=360/#11             ; Winkelschritt berechnen
#14=0                   ; Loch-Zähler

:LOOP
#15=#12+#14*#13         ; Aktueller Winkel
#16=#10*COS[#15]        ; X-Position
#17=#10*SIN[#15]        ; Y-Position

G81 X#16 Y#17 Z-10 R2 F100

#14=#14+1
IF [#14 LT #11] GOTO LOOP

M99
```

### Verwendung des Makros

```gcode
O2000 (Hauptprogramm)

G90 G54 G17
M03 S1000

; Lochkreis mit D=100mm, 8 Löcher, Start bei 0°
G65 P1000 A50 B8 C0

M30
```

## Tests

Umfangreiche Tests sind verfügbar in:
- `test_gcode_extended.py` - Tests für erweiterte G-Code-Features
- `test_gcode_interpreter.py` - Tests für Interpreter-Funktionalität

Tests ausführen:
```bash
cd python-control-layer
python -m unittest test_gcode_extended.py -v
python -m unittest test_gcode_interpreter.py -v
```

## Bekannte Einschränkungen

1. **IF-Bedingungen**: Aktuell nicht vollständig implementiert (in Beispielen gezeigt)
2. **Mathematische Ausdrücke**: Variablen-Arithmetik ist teilweise implementiert
3. **CYCLE-Befehle**: Siemens/Heidenhain-Zyklen sind definiert, aber nicht vollständig ausgeführt
4. **System-Variablen**: #1000+ Systemvariablen sind nicht implementiert

## Zukünftige Erweiterungen

- [ ] IF/WHILE/FOR Kontrollstrukturen
- [ ] Vollständige Makro-Arithmetik
- [ ] Siemens CYCLE-Implementierung
- [ ] Heidenhain CYCL DEF-Implementierung
- [ ] Okuma VC-Variable-Unterstützung
- [ ] System-Variablen (#1000+)
- [ ] Verschachtelte Makro-Aufrufe
- [ ] Lokale vs. globale Variablen

## Referenzen

- ISO 6983 (G-Code Standard)
- Fanuc Series 30i/31i/32i Operator's Manual
- Siemens Sinumerik 840D Programming Manual
- Heidenhain TNC 640 Programming Manual
- Okuma OSP-P300 Programming Manual
- Mazak Mazatrol Programming Guide
