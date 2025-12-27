# GitHub Copilot Instructions for MODAX

## Projekt-Leitprinzipien

MODAX ist ein **industrielles Steuerungssystem** mit strikter Ebenentrennung und funktionaler Sicherheit. Alle Copilot-generierten Vorschläge müssen diese Prinzipien einhalten.

## Strikte Regeln

### 1. Sicherheit zuerst (Safety First)

- **NIEMALS** KI/ML-Code in sicherheitskritischen Bereichen vorschlagen
- **NIEMALS** KI-Entscheidungen in Steuerungslogik integrieren
- Alle sicherheitskritischen Funktionen müssen deterministisch und nachvollziehbar sein
- Hardware-Sicherheitsverriegelungen dürfen nicht durch Software ersetzt werden

### 2. Strikte Ebenentrennung

#### Feldebene (ESP32 - C++)
- Nur Echtzeit-Datenerfassung und Hardware-Sicherheitsfunktionen
- Keine KI/ML-Integration
- Deterministisches Verhalten erforderlich
- Hardware-basierte Interlocks für Not-Aus

#### Steuerungsebene (Python Control Layer)
- Zentrale Koordination und Datenaggregation
- Sicherheitsvalidierung vor Befehlsausführung
- KI-Anfragen nur asynchron und nicht-blockierend
- Keine KI-Abhängigkeiten in kritischen Pfaden

#### KI-Ebene (Python AI Layer)
- **NUR BERATEND** - keine Steuerungsfunktionen
- Analysiert Daten, gibt Empfehlungen
- Hat KEINEN direkten Zugriff auf Steuerungsebene
- Alle Empfehlungen müssen von Menschen oder deterministischer Logik validiert werden

#### HMI-Ebene (C# Windows Forms)
- Visualisierung und menschliche Entscheidungsfindung
- Zeigt KI-Empfehlungen an, führt sie nicht automatisch aus
- Klare Trennung zwischen Systemstatus und KI-Vorschlägen

### 3. Code-Qualität (Payload Strict)

#### Python
- **Immer Type Hints verwenden:**
  ```python
  def process_data(device_id: str, temperature: float) -> Dict[str, Any]:
      pass
  ```
- **Immer Docstrings verwenden (Google-Style):**
  ```python
  """
  Kurzbeschreibung der Funktion.
  
  Args:
      device_id: Eindeutige Geräte-ID
      temperature: Temperatur in Celsius
      
  Returns:
      Dictionary mit Analyseergebnissen
      
  Raises:
      ValueError: Wenn Eingabewerte ungültig sind
  """
  ```
- PEP 8 konform (max 100 Zeichen pro Zeile)
- MyPy strict mode kompatibel
- Keine `Any` type hints ohne guten Grund

#### C#
- Immer XML-Dokumentation für öffentliche APIs:
  ```csharp
  /// <summary>
  /// Beschreibung der Methode
  /// </summary>
  /// <param name="deviceId">Geräte-ID</param>
  /// <returns>Status des Geräts</returns>
  public async Task<DeviceStatus> GetStatusAsync(string deviceId)
  ```
- Nullable reference types aktiviert
- Async/await für I/O-Operationen
- Exception-Handling mit spezifischen Exception-Typen

#### C++ (ESP32)
- Kommentare für alle nicht-trivialen Funktionen
- Sicherheitskritischer Code muss einfach und testbar sein
- Keine dynamische Speicherverwaltung in Interrupt-Handlern
- Hardware-Timer für zeitkritische Operationen

### 4. Dokumentation (Immer dokumentieren)

#### Code-Dokumentation
- **Jede öffentliche Funktion/Klasse muss dokumentiert sein**
- Parameter, Rückgabewerte und Exceptions dokumentieren
- Komplexe Algorithmen mit Inline-Kommentaren erklären
- Sicherheitsrelevante Entscheidungen begründen

#### Projekt-Dokumentation
- Neue Features müssen in relevanten Dokumenten erfasst werden:
  - `docs/API.md` für API-Änderungen
  - `docs/CONFIGURATION.md` für neue Konfigurationsoptionen
  - `docs/ARCHITECTURE.md` für Architekturänderungen
  - `CHANGELOG.md` für alle Änderungen
- ADRs (Architecture Decision Records) für wichtige Entscheidungen erstellen

### 5. Gleiche Codebase-Standards

#### Konsistenz
- Bestehende Patterns und Strukturen beibehalten
- Namenskonventionen des jeweiligen Layers folgen:
  - Python: `snake_case` für Funktionen/Variablen, `PascalCase` für Klassen
  - C#: `PascalCase` für öffentliche Member, `camelCase` für private
  - C++: Bestehende Arduino-Konventionen

#### Error Handling
- Einheitliche Fehlerbehandlung innerhalb jedes Layers
- Logging mit strukturierten Nachrichten
- Niemals Exceptions unbehandelt lassen
- Graceful degradation wo möglich

#### Testing
- Neue Funktionen benötigen Tests
- Minimum 95% Code Coverage für neuen Code
- Unit Tests, Integration Tests wo angemessen
- Mock externe Abhängigkeiten

### 6. Architektur-Constraints

#### Datenfluss
- Daten fließen von unten nach oben: Feld → Steuerung → KI → HMI
- Befehle fließen von oben nach unten: HMI → Steuerung → Feld
- **KI-Ebene darf NIE direkt Befehle an Steuerung/Feld senden**

#### Kommunikation
- MQTT für asynchrone Geräte-zu-Steuerung-Kommunikation
- REST APIs für synchrone Layer-zu-Layer-Kommunikation
- Protobuf für strukturierte Datenübertragung (wo implementiert)

#### Sicherheitsvalidierung
- Alle Steuerbefehle müssen durch `is_system_safe()` validiert werden
- Sicherheitschecks dürfen nicht umgangen werden
- Not-Aus hat immer Vorrang

### 7. Verbotene Patterns

- ❌ KI-Code in Control Layer Safety-Funktionen
- ❌ Direkte Datenbankzugriffe aus ESP32
- ❌ Blocking I/O in Echtzeit-Pfaden
- ❌ Unvalidierte Benutzereingaben
- ❌ Hardcodierte Credentials
- ❌ Globale veränderbare Zustände ohne Synchronisation
- ❌ Automatische Ausführung von KI-Empfehlungen ohne Benutzerbestätigung

### 8. Bevorzugte Patterns

- ✅ Dependency Injection
- ✅ Async/await für I/O
- ✅ Klare Trennung von Concerns
- ✅ Immutable Datenstrukturen wo möglich
- ✅ Factory Pattern für Objekt-Erstellung
- ✅ Repository Pattern für Datenzugriff
- ✅ Observer Pattern für Event-Handling

## Spezifische Hinweise für KI-Code

### Was KI-Code DARF:
- Sensordaten analysieren
- Anomalien erkennen
- Vorhersagen treffen
- Optimierungsempfehlungen geben
- Trends visualisieren
- Wartungsintervalle vorschlagen

### Was KI-Code NICHT DARF:
- Sicherheitsentscheidungen treffen
- Maschinen direkt steuern
- Not-Aus-Logik implementieren
- Echtzeit-kritische Pfade blockieren
- Sicherheitsparameter ändern
- Hardware-Interlocks überschreiben

## Code Review Checkliste

Vor dem Commit prüfen:
- [ ] Ebenentrennungsprinzipien eingehalten?
- [ ] KI bleibt beratend?
- [ ] Type Hints/XML-Docs vorhanden?
- [ ] Tests geschrieben?
- [ ] Dokumentation aktualisiert?
- [ ] Sicherheitsaspekte berücksichtigt?
- [ ] Fehlerbehandlung implementiert?
- [ ] Logging hinzugefügt?
- [ ] Performance-Implikationen bedacht?

## Compliance & Standards

- IEC 61508 Prinzipien für funktionale Sicherheit beachten
- IEC 61131 für Steuerungssysteme berücksichtigen
- Purdue-Modell für Netzwerk-Segmentierung
- Defense in Depth für Sicherheitsarchitektur

## Kontakt bei Unklarheiten

Bei Unsicherheiten über Architektur-Entscheidungen:
1. Konsultiere relevante ADRs in `docs/09-decisions/`
2. Siehe Architektur-Dokumentation in `docs/02-system-architecture/`
3. Prüfe bestehenden Code im entsprechenden Layer
4. Im Zweifel: Frage nach, anstatt gegen Prinzipien zu verstoßen

---

**Kernprinzip:** Sicherheit durch Design, KI als Berater niemals als Entscheider, strikte Ebenentrennung, vollständige Dokumentation.
