# ADR-0002: KI darf nicht in Steuerung eingreifen

**Status:** Accepted  
**Date:** 2025-12-27  
**Deciders:** Thomas Heisig (Projekt-Maintainer), Safety-Architect  
**Technical Story:** Fundamentale Safety-Entscheidung für MODAX

---

## Context

MODAX integriert Machine Learning für prädiktive Wartung und Optimierung. Gleichzeitig müssen strikte Safety-Anforderungen erfüllt werden. Die zentrale Frage: **Darf KI direkt in die Maschinensteuerung eingreifen?**

**Problemstellung:**
- KI/ML-Modelle sind nicht-deterministisch
- KI-Fehler können zu gefährlichen Situationen führen
- Gleichzeitig soll KI wertvolle Insights liefern
- Wie balancieren wir Innovation und Sicherheit?

**Warum ist eine Entscheidung jetzt notwendig?**

Diese Grundsatzentscheidung beeinflusst:
- Gesamte Systemarchitektur
- API-Design
- Sicherheitskonzept
- Zertifizierungsfähigkeit
- Benutzerakzeptanz

---

## Decision Drivers

**Sicherheit (Safety):**
- **IEC 61508 Anforderungen:** Sicherheitsfunktionen müssen deterministisch sein
- **ISO 13849:** Predictable behavior erforderlich
- **Haftung:** Bei KI-Fehlern wäre Haftung unklar
- **Zertifizierung:** KI in Safety-Funktionen erschwert Zertifizierung erheblich

**Technisch:**
- **Determinismus:** KI/ML ist inhärent nicht-deterministisch
- **Nachvollziehbarkeit:** "Black Box" bei komplexen Modellen
- **Fehlerrate:** Auch beste Modelle haben Fehlerquote >0%
- **Echtzeit:** KI-Inferenz kann variabel lange dauern

**Ethisch:**
- **Verantwortung:** Wer ist verantwortlich bei KI-Fehlentscheidung?
- **Transparenz:** Bediener müssen verstehen, warum etwas passiert
- **Trust:** Vertrauen in automatisierte Systeme

**Praktisch:**
- **Debugging:** KI-Fehler schwer zu reproduzieren
- **Updates:** Modell-Updates könnten Safety beeinflussen
- **Wartung:** Training-Daten müssen langfristig verfügbar sein

---

## Considered Options

### Option 1: KI hat volle Steuerungsbefugnis

**Beschreibung:**
KI kann direkt Maschinen steuern, Parameter ändern, Not-Aus auslösen.

**Pros:**
- ✅ Maximale Automatisierung
- ✅ Schnellste Reaktion auf KI-Erkenntnisse
- ✅ Keine menschliche Verzögerung

**Cons:**
- ❌ **KRITISCH:** Nicht zertifizierbar (IEC 61508, ISO 13849)
- ❌ **KRITISCH:** Safety-Risiko bei KI-Fehler
- ❌ Unvorhersagbares Verhalten
- ❌ Haftungsprobleme
- ❌ Keine Möglichkeit für menschliche Intervention
- ❌ "Black Box" entscheidet über Sicherheit

**Bewertung:**
- Performance: 5/5
- Sicherheit: **0/5 (inakzeptabel)**
- Wartbarkeit: 2/5
- Compliance: 0/5

**Fazit:** NICHT AKZEPTABEL

---

### Option 2: KI mit eingeschränkten Steuerungsrechten

**Beschreibung:**
KI darf nicht-sicherheitskritische Parameter automatisch ändern (z.B. Kühlmittel), aber nicht Safety-Funktionen.

**Pros:**
- ✅ Teilautomatisierung
- ✅ Reaktionsfähigkeit für unkritische Funktionen
- ✅ Lerneffekte in Produktion

**Cons:**
- ❌ Grenze "sicherheitskritisch" vs. "unkritisch" ist fließend
- ❌ Risiko von Scope-Creep (mehr und mehr Funktionen)
- ❌ Schwierig zu auditieren (welche Funktionen sind OK?)
- ❌ Komplexe Berechtigungslogik erforderlich
- ❌ Teilweise Zertifizierungsprobleme

**Bewertung:**
- Performance: 4/5
- Sicherheit: 2/5 (riskant)
- Wartbarkeit: 2/5
- Compliance: 2/5

**Fazit:** Zu riskant, unklare Grenzen

---

### Option 3: KI ist rein beratend (Gewählt)

**Beschreibung:**
KI analysiert Daten und gibt Empfehlungen. **Alle Entscheidungen** werden von Menschen oder deterministischer Logik getroffen.

**Pros:**
- ✅ Klare Sicherheitszone (KI-frei)
- ✅ Zertifizierbar (KI nicht im Safety-Scope)
- ✅ Menschliche Kontrolle immer vorhanden
- ✅ Auditierbar (Empfehlungen werden geloggt)
- ✅ Verständlich für Bediener
- ✅ Einfach zu begründen (für Audits)

**Cons:**
- ❌ Keine vollständige Automatisierung
- ❌ Verzögerung durch menschliche Entscheidung
- ❌ Bediener könnte KI-Empfehlung ignorieren

**Bewertung:**
- Performance: 3/5 (menschliche Verzögerung)
- Sicherheit: **5/5 (optimal)**
- Wartbarkeit: 5/5
- Compliance: 5/5

**Fazit:** OPTIMAL für Safety-kritisches System

---

### Option 4: Hybrid (KI mit Human-in-the-Loop für Validation)

**Beschreibung:**
KI schlägt vor, Mensch genehmigt oder lehnt ab, dann automatische Ausführung.

**Pros:**
- ✅ Balance zwischen Automatisierung und Kontrolle
- ✅ Mensch als Safety-Funktion

**Cons:**
- ❌ Sehr ähnlich zu Option 3 (faktisch gleich)
- ❌ "Automation Bias" (Mensch stimmt blind zu)
- ❌ Zusätzliche Komplexität

**Bewertung:**
Ähnlich zu Option 3, aber mit Risiko von "Rubber-Stamping"

---

## Decision Outcome

**Gewählte Option:** Option 3 – KI ist rein beratend

**Begründung:**

1. **Safety First:** Sicherheit hat absolute Priorität. KI in Steuerung ist inakzeptables Risiko.

2. **Zertifizierbarkeit:** IEC 61508 SIL 2 / ISO 13849 PL d sind nur erreichbar, wenn KI **nicht** Teil der Safety-Funktion ist.

3. **Nachvollziehbarkeit:** Audits erfordern klare Verantwortung. Mit KI als Berater ist klar: Mensch oder deterministische Logik entscheidet.

4. **Haftung:** Bei Unfällen muss nachvollziehbar sein, wer entschieden hat. KI-Empfehlung ist dokumentiert, aber Ausführung ist menschliche/deterministische Entscheidung.

5. **Trust & Acceptance:** Bediener vertrauen einem System mehr, bei dem sie die Kontrolle behalten.

**Erwartete Konsequenzen:**

**Positive:**
- ✅ Klare Audit-Trails (KI empfiehlt X, Bediener führt Y aus)
- ✅ Zertifizierung möglich
- ✅ Keine Safety-Incidents durch KI-Fehler
- ✅ Einfach zu erklären (für Kunden, Auditoren, Versicherer)
- ✅ Schutz vor "AI Hallucinations"

**Negative:**
- ⚠️ Langsamere Reaktion (mitigiert: KI-Empfehlungen sind nicht zeitkritisch)
- ⚠️ Bediener könnte gute Empfehlung ignorieren (mitigiert: Logging, Metriken)
- ⚠️ Keine vollautonomen Funktionen (mitigiert: Deterministische Automatisierung möglich)

**Trade-offs:**
- **Automatisierung vs. Safety:** Akzeptieren wir manuelle Entscheidung für garantierte Sicherheit ✅
- **Reaktionszeit vs. Nachvollziehbarkeit:** Akzeptieren wir Verzögerung für klare Verantwortung ✅

---

## Implementation

**Architektonische Durchsetzung:**

1. **Netzwerk-Trennung:**
   - KI-Ebene hat **KEINE** direkte Verbindung zu Feldebene
   - Firewall blockiert KI → ESP32 Kommunikation

2. **MQTT-Berechtigungen:**
   ```
   # ai_layer User:
   publish: NONE  # Keine Publish-Rechte für Control Topics!
   subscribe: NONE  # Erhält Daten via REST API
   ```

3. **API-Design:**
   - KI-Ebene hat nur **Read-Only** Zugriff auf Sensordaten
   - Keine Endpoints für Steuerungsbefehle in AI Layer API
   - Alle Empfehlungen werden gespeichert, nicht ausgeführt

4. **Code-Struktur:**
   ```python
   # python-ai-layer/
   # DARF NICHT importieren:
   # ❌ from control_layer import motion_controller
   # ❌ from control_layer import safety_validator
   
   # DARF NICHT haben:
   # ❌ mqtt_client.publish("modax/control/+/command", ...)
   ```

5. **HMI-Design:**
   - Klare visuelle Trennung:
     - **Links:** Systemstatus (Fakten)
     - **Rechts:** KI-Empfehlungen (Vorschläge)
   - Button "Empfehlung anwenden" (explizite Bestätigung)

**Prozess-Flow:**
```
1. KI analysiert Daten
2. KI erstellt Empfehlung (mit Confidence)
3. Empfehlung wird gespeichert + geloggt
4. HMI zeigt Empfehlung an
5. Bediener prüft Empfehlung
6. Bediener entscheidet: Anwenden oder Ignorieren
7. Falls "Anwenden":
   - HMI sendet POST /control/command
   - Control Layer validiert (is_system_safe)
   - Falls safe: Befehl an Feldebene
8. Audit-Log: KI-Empfehlung + Bediener-Entscheidung
```

**Zeitrahmen:**
- ✅ Architektur: Implementiert (v0.1.0)
- ✅ MQTT-ACLs: Implementiert
- 🔄 Firewall-Regeln: Dokumentiert, optional in Deployment
- 📋 Formale Sicherheits-Analyse: Geplant (v0.6.0)

---

## Validation

**Erfolgskriterien:**
- [x] KI-Ebene kann **nicht** direkt MQTT-Steuerbefehle publishen
- [x] Alle KI-Empfehlungen werden geloggt
- [x] HMI zeigt KI-Empfehlungen als "Vorschläge", nicht als "Befehle"
- [x] System läuft weiter, wenn KI-Ebene ausfällt (Graceful Degradation)
- [ ] Penetration-Test: KI-Ebene versucht, Steuerung zu kompromittieren
- [ ] Audit durch externen Safety-Experten

**Metriken:**
- **KI-Empfehlungen gegeben:** [Counter]
- **KI-Empfehlungen angewendet:** [Counter]
- **KI-Empfehlungen ignoriert:** [Counter]
- **Acceptance-Rate:** Applied / Given
- **False-Positive-Rate:** (Applied + später revertiert) / Applied

**Review-Zeitpunkt:**
- Bei jedem Major-Release (v1.0, v2.0, ...)
- Nach Safety-Incidents (falls aufgetreten)
- Bei Einführung neuer KI-Modelle

---

## Risks & Mitigation

| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|--------|-------------------|--------|------------|
| Bediener ignoriert kritische KI-Warnung | Mittel | Hoch | UI-Design: Kritische Warnungen prominent. Eskalation. |
| "Automation Bias" (blindes Vertrauen) | Mittel | Mittel | Schulung. Confidence-Level anzeigen. Fehlerberichte. |
| Umgehung der Architektur (Bug) | Niedrig | Kritisch | Code Reviews. Automated Tests. Penetration Tests. |
| Langsame Reaktion bei echter Gefahr | Niedrig | Hoch | Hardware-Safety (ESP32) reagiert lokal ohne KI/Control. |

---

## Related Decisions

**Abhängigkeiten:**
- **ADR-0001:** 4-Ebenen-Architektur (ermöglicht diese Trennung)

**Beeinflusst:**
- **ADR-0003:** Predictive Maintenance (KI nur empfehlend)
- **Zukünftig:** ONNX Model Deployment (ebenfalls nur empfehlend)

**Konflikte:**
- Keine

---

## Notes

**Diskussionen:**
- Option 2 (eingeschränkte Rechte) wurde intensiv diskutiert, aber verworfen wegen unklarer Grenzen
- "Automation Bias" ist bekanntes Risiko, wird durch UX-Design und Schulung adressiert
- Online-Learning im Produktionsbetrieb wurde verworfen (separate Entscheidung, verstärkt durch diese ADR)

**Referenzen:**
- IEC 61508-1:2010 (Functional Safety of E/E/PE Safety-Related Systems)
- ISO 13849-1:2015 (Safety of Machinery – Safety-Related Parts of Control Systems)
- "Human Factors in Automation and AI" (Parasuraman & Riley, 1997)
- "Explainable AI" (DARPA Program)

**Zitate:**
> "In safety-critical systems, AI should inform, not decide." – Safety Engineering Principle

> "The question is not whether AI can make better decisions, but whether we can prove it always will." – Certification Expert

**Anhänge:**
- [Control Boundaries](../02-system-architecture/control-boundaries.md)
- [KI-Ebene Constraints](../05-analytics-and-ml-layer/constraints.md)

---

**Autor:** Thomas Heisig  
**Reviewer:** Safety-Architect (Community Review offen)  
**Letzte Aktualisierung:** 2025-12-27

---

## Appendix: Realworld Examples

**Positive Beispiele (KI als Berater):**
- **Tesla Autopilot:** Warnt Fahrer, übernimmt nicht vollständig
- **Medical AI:** Schlägt Diagnosen vor, Arzt entscheidet
- **Google Spam Filter:** Markiert als Spam, Nutzer kann übersteuern

**Negative Beispiele (KI steuert direkt):**
- **Boeing 737 MAX MCAS:** Automatische Korrektur führte zu Abstürzen
- **Uber Self-Driving Car Fatal Crash:** Keine menschliche Kontrolle
- **Flash Crash 2010:** Algorithmen handelten autonom, Börse crashte

**Lehre:** In sicherheitskritischen Bereichen ist menschliche Überwachung essentiell.
