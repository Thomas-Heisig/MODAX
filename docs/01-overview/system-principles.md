# MODAX – Systemgrundsätze

Diese Grundsätze definieren die unveränderlichen Prinzipien, nach denen MODAX entwickelt wurde und weiterentwickelt wird.

---

## 1. Safety First – Sicherheit hat absolute Priorität

### Grundsatz

**Menschenleben und Anlagensicherheit gehen vor allen anderen Zielen.**

### Praktische Umsetzung

- Alle sicherheitskritischen Funktionen sind deterministisch und nachvollziehbar
- KI/ML wird NIEMALS in Sicherheitsentscheidungen einbezogen
- Hardware-basierte Sicherheitsverriegelungen haben Vorrang vor Software
- Not-Aus-Funktionen sind Hardware-implementiert und können nicht per Software deaktiviert werden
- Fail-Safe-Design: Bei Ausfall wird ein sicherer Zustand angestrebt

### Konsequenzen für Entwicklung

- **Code Reviews für Safety-Code sind verpflichtend**
- Tests für Sicherheitsfunktionen haben 100% Coverage-Anforderung
- Sicherheitsrelevante Änderungen erfordern FMEA/HAZOP-Analyse
- Keine "Quick-Fixes" in Sicherheitslogik
- Dokumentation ist für Safety-Funktionen Pflicht

---

## 2. KI ist beratend, niemals steuernd

### Grundsatz

**KI-Systeme dürfen analysieren und empfehlen, aber niemals direkt steuern.**

### Rationale

- KI/ML-Modelle sind nicht deterministisch
- Unerwartetes Verhalten ist inhärent in neuronalen Netzen
- Explainability ist bei komplexen Modellen limitiert
- Fehlerhafte Trainingsdaten können zu gefährlichen Entscheidungen führen

### Architektonische Durchsetzung

- **KI-Ebene hat keine MQTT-Publish-Rechte für Steuerbefehle**
- KI-Ebene läuft in separatem Process/Container
- Alle KI-Empfehlungen werden geloggt, aber nicht automatisch ausgeführt
- Steuerungsebene validiert alle Befehle unabhängig von der Quelle

### Erlaubte KI-Funktionen

✅ Anomalieerkennung und Warnung  
✅ Prognosen (Wartung, Verschleiß, Ausfall)  
✅ Optimierungsvorschläge (Parameter, Scheduling)  
✅ Qualitätsvorhersagen  
✅ Trend-Analysen  

### Verbotene KI-Funktionen

❌ Direkte Maschinensteuerung  
❌ Sicherheitsentscheidungen  
❌ Not-Aus-Logik  
❌ Automatische Parameteränderung ohne Validierung  
❌ Übersteuerung von Sicherheitsverriegelungen  

---

## 3. Strikte Ebenentrennung

### Grundsatz

**Jede Ebene hat klare Verantwortlichkeiten. Verantwortungen überschneiden sich nicht.**

### Die 4 Ebenen

#### Feldebene (ESP32)
- **Verantwortung:** Sensordatenerfassung, Hardware-Sicherheit
- **Darf:** Sensoren auslesen, Hardware-Interlocks setzen, MQTT publishen
- **Darf nicht:** KI-Algorithmen ausführen, komplexe Berechnungen, Datenbankzugriffe

#### Steuerungsebene (Python Control)
- **Verantwortung:** Zentrale Koordination, Datenaggregation, CNC-Steuerung
- **Darf:** Geräte koordinieren, G-Code ausführen, Sicherheit validieren
- **Darf nicht:** KI-Entscheidungen treffen, Hardware direkt ansprechen (nur via Feld)

#### KI-Ebene (Python AI)
- **Verantwortung:** Datenanalyse, Empfehlungen
- **Darf:** Analysieren, prognostizieren, vorschlagen
- **Darf nicht:** Steuern, Sicherheitsentscheidungen, Datenaggregation übernehmen

#### HMI-Ebene (C# UI)
- **Verantwortung:** Visualisierung, menschliche Entscheidung
- **Darf:** Anzeigen, Benutzereingaben entgegennehmen, Befehle an Control senden
- **Darf nicht:** Direkte Feldgeräte-Kommunikation, KI-Logik implementieren

### Kommunikationsregeln

- **Daten fließen aufwärts:** Feld → Control → AI → HMI
- **Befehle fließen abwärts:** HMI → Control → Feld
- **KI ist Seitenkanal:** Control → AI → Control (nur Empfehlungen)

---

## 4. Transparenz und Nachvollziehbarkeit

### Grundsatz

**Jede Entscheidung und jeder Prozess muss dokumentiert und nachvollziehbar sein.**

### Logging-Anforderungen

- **Alle Sicherheitsereignisse werden geloggt** (Not-Aus, Interlocks, etc.)
- **Alle Steuerbefehle werden geloggt** (Quelle, Zeitstempel, Validierung)
- **Alle KI-Empfehlungen werden geloggt** (Input, Output, Confidence)
- **Fehler werden mit Kontext geloggt** (Stack-Trace, Systemzustand)

### Audit-Trail

- Unveränderbare Logs für sicherheitsrelevante Ereignisse
- Zeitstempel mit Nanosekunden-Präzision
- Eindeutige Ereignis-IDs
- Korrelation über Ebenen hinweg möglich

### Explainability

- KI-Empfehlungen müssen begründbar sein
- Welche Daten führten zur Entscheidung?
- Welche Features waren wichtig?
- Confidence-Level für jede Vorhersage

---

## 5. Deterministisches Verhalten in kritischen Pfaden

### Grundsatz

**Sicherheitskritische Funktionen müssen vorhersagbar und wiederholbar reagieren.**

### Was bedeutet "deterministisch"?

- Gleicher Input → Gleicher Output (immer)
- Maximale Antwortzeit ist bekannt und garantiert
- Keine Zufälligkeit in Sicherheitslogik
- Keine Machine-Learning-Modelle in Echtzeit-Pfaden

### Echtzeit-Anforderungen

| Funktion | Maximale Reaktionszeit | Implementierung |
|----------|------------------------|-----------------|
| Not-Aus | <10 ms | Hardware (ESP32) |
| Überlastschutz | <50 ms | Hardware (ESP32) |
| Sicherheitsvalidierung | <100 ms | Software (Control Layer) |
| HMI-Update | <2000 ms | Software (Control/HMI) |

### Nicht-deterministische Bereiche (erlaubt)

- KI-Analysen (asynchron, nicht zeitkritisch)
- Visualisierung (HMI-Rendering)
- Langzeit-Trend-Analysen
- Modell-Training (offline)

---

## 6. Fehlertoleranz und Graceful Degradation

### Grundsatz

**Das System bleibt funktionsfähig, auch wenn Komponenten ausfallen.**

### Resilience-Patterns

- **Automatische Wiederverbindung:** MQTT, REST APIs
- **Timeout-Handling:** Alle I/O-Operationen haben Timeouts
- **Fallback-Werte:** Bei Sensorfehler werden Default-Werte verwendet
- **Partial Failure:** Ein Geräteausfall stoppt nicht das gesamte System
- **Circuit Breaker:** Wiederholte Fehler führen zu temporärer Deaktivierung

### Degradation-Stufen

| Level | Zustand | Funktionalität |
|-------|---------|----------------|
| **Normal** | Alle Komponenten OK | 100% |
| **Degraded** | KI-Ebene ausgefallen | 90% (nur Analytik fehlt) |
| **Limited** | Steuerung nur lokal | 70% (kein Zentral-Monitoring) |
| **Safe** | Nur Hardware-Safety | 20% (Not-Aus funktioniert) |

### Fail-Safe-Prinzip

Bei kritischem Ausfall:
1. Maschine in sicheren Zustand bringen (Stop)
2. Alarm auslösen
3. Ereignis loggen
4. Auf manuelle Intervention warten

---

## 7. Modularität und lose Kopplung

### Grundsatz

**Komponenten sind austauschbar und unabhängig wartbar.**

### Architektur-Patterns

- **Microservices:** Jede Ebene ist separater Service
- **API-First:** Klare, dokumentierte Schnittstellen
- **Publish-Subscribe:** MQTT für asynchrone Kommunikation
- **Dependency Injection:** Keine harten Abhängigkeiten

### Vorteile

- **Wartbarkeit:** Komponenten einzeln aktualisierbar
- **Testbarkeit:** Services einzeln testbar
- **Skalierbarkeit:** Horizontale Skalierung möglich
- **Austauschbarkeit:** Implementierung änderbar bei gleicher Schnittstelle

---

## 8. Dokumentation als Code

### Grundsatz

**Dokumentation ist Teil des Produkts, nicht Anhängsel.**

### Anforderungen

- **Jede öffentliche API ist dokumentiert** (Docstrings, OpenAPI)
- **Architektur-Entscheidungen sind dokumentiert** (ADRs)
- **Setup-Prozesse sind automatisiert und dokumentiert**
- **Troubleshooting-Guides existieren**

### Living Documentation

- Dokumentation wird mit Code versioniert (Git)
- Code-Beispiele sind getestet und funktionieren
- API-Docs werden automatisch aus Code generiert
- Diagramme werden aus Code/Config generiert (wo möglich)

---

## 9. Security by Design

### Grundsatz

**Sicherheit wird von Anfang an eingebaut, nicht nachträglich hinzugefügt.**

### Defense in Depth

Mehrere Sicherheitsebenen:
1. **Netzwerk-Segmentierung** (OT/IT-Trennung)
2. **Authentifizierung** (Zugriffskontrolle)
3. **Autorisierung** (RBAC)
4. **Verschlüsselung** (TLS für APIs)
5. **Audit-Logging** (Nachvollziehbarkeit)

### Least Privilege

- Komponenten haben nur minimale erforderliche Rechte
- KI-Ebene hat keine Schreibrechte auf Control-Endpoints
- Feldgeräte können nur publishen, nicht subscriben (selektiv)

### Input Validation

- Alle Benutzereingaben werden validiert
- Alle API-Inputs werden gegen Schema validiert
- SQL-Injection, XSS, Command-Injection werden verhindert

---

## 10. Performance ist ein Feature

### Grundsatz

**Akzeptable Performance ist Voraussetzung, nicht Optional.**

### Performance-Ziele

- **Sensordaten:** 10-50 Hz (konfiguralbar)
- **Safety-Checks:** >20 Hz
- **API-Latenz:** <100 ms (p95)
- **HMI-Update:** <2 s
- **MQTT-Latenz:** <50 ms

### Monitoring

- Alle kritischen Metriken werden gemessen
- Performance-Regression wird in CI/CD erkannt
- Profiling bei Performance-Problemen

---

## Zusammenfassung

Diese 10 Grundsätze sind **nicht verhandelbar**. Sie definieren die Identität von MODAX als sicheres industrielles Steuerungssystem mit beratender KI.

Jede Änderung oder neue Funktion muss gegen diese Prinzipien geprüft werden. Bei Konflikt hat **Safety First** immer Vorrang.

---

**Referenzen:**
- [Vision](../00-meta/vision.md)
- [Architektur](../02-system-architecture/layer-model.md)
- [Copilot-Regeln](../../.github/copilot-instructions.md)
