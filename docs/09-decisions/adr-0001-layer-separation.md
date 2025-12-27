# ADR-0001: 4-Ebenen-Architektur mit strikter Trennung

**Status:** Accepted  
**Date:** 2025-12-27  
**Deciders:** Thomas Heisig (Projekt-Maintainer)  
**Technical Story:** Grundlegende Architektur-Entscheidung für MODAX

---

## Context

MODAX soll ein industrielles Steuerungssystem werden, das KI-Funktionen integriert, aber gleichzeitig Safety-Anforderungen erfüllt. Die Herausforderung besteht darin, moderne KI-Technologie mit den strikten Anforderungen der Industrieautomatisierung zu vereinen.

**Problemstellung:**
- Wie strukturieren wir ein System, das sowohl sicherheitskritische Steuerung als auch nicht-deterministische KI-Analysen umfasst?
- Wie stellen wir sicher, dass KI niemals Sicherheitsfunktionen beeinflussen kann?
- Wie schaffen wir eine wartbare, skalierbare Architektur?

**Warum ist eine Entscheidung jetzt notwendig?**

Die Architektur ist fundamental für alle weiteren Entwicklungen. Eine spätere Änderung wäre sehr aufwendig.

---

## Decision Drivers

**Technisch:**
- Trennung von deterministischen und nicht-deterministischen Funktionen
- Skalierbarkeit (1-500+ Geräte)
- Echtzeit-Anforderungen (Sensordaten 10 Hz, Safety 20 Hz)
- Modularität und Austauschbarkeit

**Sicherheit:**
- IEC 61508 SIL 2-Konformität (Ziel)
- ISO 13849 PL d-Konformität (Ziel)
- Klare Safety-Zone (KI-frei)
- Auditierbarkeit

**Organisatorisch:**
- Verschiedene Technologie-Stacks (C++, Python, C#) sinnvoll nutzen
- Separate Teams können an verschiedenen Ebenen arbeiten
- Open-Source-Community (verschiedene Skill-Levels)

**Wartbarkeit:**
- Langfristige Wartbarkeit (10+ Jahre)
- Technologie-Updates einzelner Ebenen
- Klare Verantwortlichkeiten

---

## Considered Options

### Option 1: Monolithische Architektur

**Beschreibung:**
Alle Funktionen (Safety, Control, AI, HMI) in einer einzigen Anwendung.

**Pros:**
- ✅ Einfacher zu deployen (eine Binary)
- ✅ Keine Netzwerk-Latenz zwischen Komponenten
- ✅ Einfachere Entwicklung initial

**Cons:**
- ❌ KI und Safety im selben Prozess (schwer zu trennen)
- ❌ Schwierig zu skalieren
- ❌ Ein Fehler kann gesamtes System crashen
- ❌ Schwierig zu zertifizieren (Safety + KI gemischt)
- ❌ Keine Technologie-Diversität

**Bewertung:**
- Performance: 5/5
- Sicherheit: 1/5 (kritisch)
- Wartbarkeit: 2/5
- Skalierbarkeit: 1/5

---

### Option 2: 2-Ebenen-Architektur (Embedded + Backend)

**Beschreibung:**
ESP32 (Embedded) + kombinierter Backend-Server (Control+AI+HMI).

**Pros:**
- ✅ Trennung Embedded vs. Backend
- ✅ Einfacher als 4-Ebenen
- ✅ Moderate Komplexität

**Cons:**
- ❌ AI und Control immer noch im selben Backend
- ❌ HMI nicht eigenständig (muss mit Backend laufen)
- ❌ Schwierige Safety-Argumentation
- ❌ Eingeschränkte Skalierbarkeit

**Bewertung:**
- Performance: 4/5
- Sicherheit: 2/5 (unzureichend)
- Wartbarkeit: 3/5
- Skalierbarkeit: 2/5

---

### Option 3: 4-Ebenen-Architektur (Gewählt)

**Beschreibung:**
Strikte Trennung in 4 Ebenen:
1. Feldebene (ESP32, C++, Hardware-Safety)
2. Steuerungsebene (Python, Control, CNC, Safety-Validation)
3. KI-Ebene (Python, Analyse, Empfehlungen)
4. HMI-Ebene (C#, Visualisierung, Bedienung)

**Pros:**
- ✅ Klare Safety-Zone (Ebene 1+2, KI-frei)
- ✅ KI kann niemals direkt steuern (architektonisch unmöglich)
- ✅ Jede Ebene unabhängig skalierbar
- ✅ Verschiedene Technologien optimal genutzt
- ✅ Einfachere Zertifizierung (nur Ebene 1+2 im Scope)
- ✅ Parallele Entwicklung möglich
- ✅ Graceful Degradation (Ebenen können ausfallen)

**Cons:**
- ❌ Höhere Komplexität initial
- ❌ Netzwerk-Latenz zwischen Ebenen
- ❌ Mehr Deployment-Aufwand
- ❌ Mehrere Services zu managen

**Bewertung:**
- Performance: 3/5 (Netzwerk-Latenz)
- Sicherheit: 5/5 (optimal)
- Wartbarkeit: 5/5 (optimal)
- Skalierbarkeit: 5/5 (optimal)

---

### Option 4: Microservices (10+ Services)

**Beschreibung:**
Feinere Granularität: Separate Services für Anomaly Detection, Wear Prediction, G-Code Parser, etc.

**Pros:**
- ✅ Maximale Flexibilität
- ✅ Sehr granular skalierbar

**Cons:**
- ❌ Overkill für aktuelle Größe
- ❌ Sehr hohe Komplexität
- ❌ Operations-Overhead
- ❌ Schwierig für kleinere Deployments

**Bewertung:**
- Performance: 3/5
- Sicherheit: 4/5
- Wartbarkeit: 2/5 (zu komplex)
- Skalierbarkeit: 5/5 (aber nicht benötigt)

---

## Decision Outcome

**Gewählte Option:** Option 3 – 4-Ebenen-Architektur

**Begründung:**
- **Sicherheit hat Priorität:** Klare Trennung Safety vs. KI ist essentiell für Zertifizierung
- **Architektonische Durchsetzung:** KI kann physisch nicht steuern (keine MQTT-Rechte, keine Netzwerk-Verbindung zu Feldebene)
- **Wartbarkeit:** Jede Ebene eigenständig, klare Verantwortlichkeiten
- **Skalierbarkeit:** Von 1 Gerät (All-in-One) bis 500+ Geräte (Kubernetes)
- **Technologie-Vielfalt:** Jede Ebene nutzt optimale Technologie

**Erwartete Konsequenzen:**

**Positive:**
- ✅ Zertifizierbarkeit (IEC 61508 SIL 2 möglich)
- ✅ Klare Audit-Trails (KI-Empfehlungen vs. Ausführung)
- ✅ Fehlertoleranz (KI-Ausfall nicht kritisch)
- ✅ Community-Entwicklung (verschiedene Skill-Levels)

**Negative:**
- ⚠️ Höhere Latenz durch Netzwerk (mitigiert durch async Kommunikation für KI)
- ⚠️ Mehr Deployment-Komplexität (mitigiert durch Docker Compose/Helm Charts)
- ⚠️ Mehrere Services zu monitoren (mitigiert durch Observability-Stack)

**Trade-offs:**
- **Performance vs. Safety:** Akzeptieren wir ~50ms Netzwerk-Latenz für klare Safety-Trennung ✅
- **Einfachheit vs. Skalierbarkeit:** Akzeptieren wir höhere initiale Komplexität für spätere Skalierbarkeit ✅

---

## Implementation

**Erforderliche Änderungen:**
1. **Feldebene:** ESP32 C++ Firmware (Arduino Framework)
2. **Steuerungsebene:** Python FastAPI Service + MQTT Handler
3. **KI-Ebene:** Python FastAPI Service (separater Process)
4. **HMI-Ebene:** C# .NET Windows Forms Application

**Kommunikation:**
- Feldebene ↔ Steuerung: MQTT (Mosquitto)
- Steuerung ↔ KI: REST API (HTTP/JSON)
- Steuerung ↔ HMI: REST API (HTTP/JSON)

**Migration-Pfad:**
N/A (neue Architektur, kein Legacy-System)

**Zeitrahmen:**
- ✅ Prototyp: Abgeschlossen (v0.1.0)
- ✅ Implementation: Abgeschlossen (v0.5.0)
- 🔄 Optimierung: Laufend

**Verantwortliche:**
- Lead: Thomas Heisig
- Contributors: Open-Source-Community

---

## Validation

**Erfolgskriterien:**
- [x] Feldebene unabhängig von Netzwerk funktionsfähig (Safety lokal)
- [x] KI-Ausfall führt nicht zu Systemausfall
- [x] Alle Ebenen können separat deployt werden
- [x] Skalierung von 1 auf 10 Geräte getestet
- [ ] Formale Safety-Analyse durchgeführt
- [ ] Performance-Benchmarks dokumentiert

**Metriken:**
- Sensor→HMI End-to-End Latenz: <500ms (aktuell ~200ms)
- KI-Analyse-Zeit: <5s (aktuell ~1s)
- System Uptime: >95% (aktuell ~95%)

**Review-Zeitpunkt:**
Nach v1.0.0 (Production Release) und 6 Monate Produktionsbetrieb

---

## Risks & Mitigation

| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|--------|-------------------|--------|------------|
| Netzwerk-Latenz zu hoch | Mittel | Mittel | Async Kommunikation für KI, Optimierung von Protokollen |
| Deployment-Komplexität | Hoch | Niedrig | Docker Compose (einfach), Helm Charts (K8s), install.sh |
| Service-Discovery schwierig | Niedrig | Mittel | Statische Config für kleine Deployments, K8s DNS für große |
| Monitoring-Overhead | Mittel | Niedrig | Prometheus + Grafana (geplant), strukturiertes Logging |

---

## Related Decisions

**Abhängigkeiten:**
- ADR-0002: No AI in Control (implementiert 4-Ebenen-Prinzip)
- ADR-0003: Predictive Maintenance (nutzt KI-Ebene)

**Konflikte:**
- Keine

**Supersedes:**
- Keine (initiale Architektur-Entscheidung)

---

## Notes

**Diskussionen:**
- Alternativen wie 3-Ebenen (ohne separate HMI) wurden verworfen, da HMI eigenständig sein soll (offline-fähig)
- Microservices (Option 4) für zukünftige Versionen (v2.x) nicht ausgeschlossen

**Referenzen:**
- IEC 61508-1:2010 (Functional Safety)
- ISO 13849-1:2015 (Safety of Machinery)
- Purdue Enterprise Reference Architecture (PERA)
- ISA-95 (Hierarchical Control Model)

**Anhänge:**
- [4-Ebenen-Modell Diagramm](../02-system-architecture/layer-model.md)
- [Datenfluss-Diagramm](../02-system-architecture/data-flow.md)

---

**Autor:** Thomas Heisig  
**Reviewer:** Community (Open Review)  
**Letzte Aktualisierung:** 2025-12-27
