# MODAX – Compliance Scope & Normen

**Stand:** 2025-12-27  
**Status:** Prototyp / Vorbereitung zur Zertifizierung

---

## Überblick

Dieses Dokument definiert den Umfang der Norm- und Richtlinienkonformität von MODAX sowie den aktuellen Stand der Compliance-Bemühungen.

## Wichtiger Hinweis

⚠️ **MODAX ist aktuell NICHT formal zertifiziert**

MODAX wurde nach Best Practices der genannten Normen entwickelt, besitzt aber keine formalen Zertifizierungen. Für den Einsatz in sicherheitskritischen Umgebungen ist eine formale Zertifizierung erforderlich.

---

## Anwendbare Normen & Standards

### 1. Funktionale Sicherheit

#### IEC 61508 – Functional Safety of Electrical/Electronic Systems

**Relevanz:** Hoch  
**Anwendbare Teile:** 1-7  
**Ziel-SIL:** SIL 2 (mittelfristig)  
**Aktueller Stand:** Architektur-konform, nicht zertifiziert

**MODAX Alignment:**
- ✅ Systematische Fehlervermeidung durch Architektur-Design
- ✅ Deterministische Sicherheitsfunktionen (KI-frei)
- ✅ Diversität durch Hardware-/Software-Trennung
- ✅ Fehlertoleranz und Graceful Degradation
- 🚧 Formale Safety-Analyse ausstehend
- 📋 V-Modell-Entwicklung teilweise umgesetzt

**Anwendbare Konzepte:**
- Safety Integrity Levels (SIL)
- Hardware Fault Tolerance
- Safe Failure Fraction
- Systematic Capability
- Safety Lifecycle Management

**Nicht anwendbar:**
- SIL 3/4 Anforderungen (zu komplex für aktuellen Scope)
- Vollständig redundante Systeme

#### IEC 61131 – Programmable Controllers

**Relevanz:** Mittel  
**Anwendbare Teile:** 1, 2, 3  
**Aktueller Stand:** Konzeptionell konform

**MODAX Alignment:**
- ✅ Strukturierte Programmierung (Teil 3)
- ✅ Klare Trennung von Steuerlogik
- ✅ Dokumentierte Programmstruktur
- 🚧 IEC 61131-3 Programmiersprachen nicht direkt verwendet
  - Stattdessen: Python (hochsprachig, getestet)

**Begründung für Abweichung:**
- Python bietet bessere Testbarkeit
- Moderne Entwicklungstools
- Bessere Integration mit KI/ML
- Trade-off: Echtzeit-Determinismus durch Architektur-Design kompensiert

#### ISO 13849 – Safety of Machinery

**Relevanz:** Hoch (für Maschinenbau-Anwendungen)  
**Anwendbare Teile:** 1, 2  
**Ziel-PL:** PL d  
**Aktueller Stand:** Architektur-konform

**MODAX Alignment:**
- ✅ Kategorie 3-Architektur (Fehlertoleranz)
- ✅ Regelmäßige Selbsttests
- ✅ Hardware-Interlocks
- ✅ Not-Aus-Funktion
- 📋 MTTF-Berechnungen ausstehend
- 📋 Formale Risikobewertung ausstehend

### 2. Industrielle Kommunikation

#### IEC 62541 – OPC UA

**Relevanz:** Hoch (zukünftig)  
**Aktueller Stand:** Dokumentiert, nicht implementiert

**MODAX Roadmap:**
- ✅ Architektur vorbereitet
- ✅ Dokumentation erstellt
- 📋 Server-Implementierung geplant (v1.1.0)
- 📋 Client-Implementierung geplant (v1.1.0)

#### IEEE 802.3 / EtherCAT / PROFINET

**Relevanz:** Mittel (zukünftig)  
**Aktueller Stand:** Nicht implementiert

**Roadmap:**
- 📋 EtherCAT Master (v1.3.0)
- 📋 PROFINET Integration (v1.3.0)

### 3. Informationssicherheit

#### IEC 62443 – Industrial Communication Networks Security

**Relevanz:** Hoch  
**Anwendbare Teile:** 2-4, 4-2  
**Ziel-SL:** SL 2  
**Aktueller Stand:** Teilweise umgesetzt

**MODAX Alignment:**
- ✅ Defense in Depth (Netzwerk-Segmentierung)
- ✅ Least Privilege (geplant mit RBAC)
- ✅ Secure by Design (Architektur-Prinzipien)
- 🚧 Formale Security-Zone-Definition
- 🚧 Comprehensive Security Testing
- 📋 Incident Response Plan

**Umgesetzte Konzepte:**
- Purdue-Modell-konforme Architektur
- Separierung OT/IT (konzeptionell)
- Authentifizierung (Basic, OAuth2 geplant)
- Audit-Logging (teilweise)

**Offene Punkte:**
- [ ] Penetration Testing
- [ ] Security Assessment nach IEC 62443-2-4
- [ ] Zone & Conduit Definition
- [ ] Security Patch Management

### 4. Qualitätsmanagement

#### ISO 9001 – Quality Management Systems

**Relevanz:** Mittel  
**Aktueller Stand:** Best Practices angewendet

**MODAX Alignment:**
- ✅ Dokumentation (umfassend)
- ✅ Versionskontrolle (Git)
- ✅ Testing (96%+ Coverage)
- ✅ Traceability (Git History, Issues)
- 🚧 Formales QMS nicht etabliert

#### ISO/IEC 25010 – Software Product Quality

**Relevanz:** Hoch  
**Aktueller Stand:** Informell angewendet

**Qualitätsmerkmale:**
- ✅ Functionality: Feature-komplett für Scope
- ✅ Reliability: Robuste Fehlerbehandlung
- ✅ Usability: Intuitive HMI
- ✅ Maintainability: Modulare Architektur, dokumentiert
- ✅ Portability: Docker, multi-platform
- 🚧 Performance: Optimierung ausstehend
- 🚧 Security: Audit ausstehend

### 5. G-Code & CNC-Standards

#### ISO 6983 – Numerical Control of Machines

**Relevanz:** Hoch (für CNC-Funktionen)  
**Aktueller Stand:** Vollständig implementiert

**MODAX Alignment:**
- ✅ ISO 6983 G-Code Parser
- ✅ 150+ Standard G/M-Codes
- ✅ Erweiterte Codes (NURBS, Threading, etc.)
- ✅ Herstellerspezifische Erweiterungen

#### DIN 66025 – Deutsche CNC-Norm

**Relevanz:** Mittel (für deutsche Maschinen)  
**Aktueller Stand:** Kompatibel

---

## Compliance-Matrix

| Norm | Relevanz | Ziel | Status | Priorität | Timeline |
|------|----------|------|--------|-----------|----------|
| IEC 61508 (SIL 2) | Hoch | Zertifizierung | 🚧 Vorbereitung | Hoch | 2026 Q3 |
| IEC 61131 | Mittel | Konformität | ✅ Konzeptionell | Mittel | - |
| ISO 13849 (PL d) | Hoch | Zertifizierung | 🚧 Vorbereitung | Hoch | 2026 Q4 |
| IEC 62443 (SL 2) | Hoch | Assessment | 🚧 Teilweise | Hoch | 2026 Q2 |
| IEC 62541 (OPC UA) | Hoch | Implementation | 📋 Geplant | Hoch | 2026 Q2 |
| ISO 6983 | Hoch | Konformität | ✅ Implementiert | - | - |
| ISO 9001 | Mittel | Best Practices | 🚧 Informell | Niedrig | - |

**Legende:**
- ✅ Erfüllt / Implementiert
- 🚧 In Arbeit / Teilweise
- 📋 Geplant
- ❌ Nicht anwendbar

---

## Zertifizierungs-Roadmap

### Phase 1: Dokumentation & Vorbereitung (Q1 2026)

- [ ] Vollständige Systemdokumentation nach Norm-Anforderungen
- [ ] Architecture Decision Records (ADRs)
- [ ] Failure Mode and Effects Analysis (FMEA)
- [ ] Hazard and Operability Study (HAZOP)
- [ ] Risk Assessment nach ISO 13849

**Deliverables:**
- Safety Manual
- System Architecture Documentation
- Risk Analysis Report
- Test Plans

### Phase 2: Testing & Validation (Q2 2026)

- [ ] Systematic Testing nach IEC 61508
- [ ] Security Assessment nach IEC 62443
- [ ] Performance Benchmarks
- [ ] Long-term Stability Tests
- [ ] Environmental Testing (Temperature, EMC)

**Deliverables:**
- Test Reports
- Validation Documentation
- Performance Metrics
- Security Assessment Report

### Phase 3: Formal Assessment (Q3-Q4 2026)

- [ ] Auswahl TÜV/Notified Body
- [ ] Formale Begutachtung
- [ ] Audit & Review
- [ ] Corrective Actions
- [ ] Zertifizierung

**Deliverables:**
- Certification (IEC 61508 SIL 2)
- Declaration of Conformity
- CE Marking (falls anwendbar)

---

## Scope-Einschränkungen

### Nicht im Scope

MODAX **strebt KEINE Zertifizierung an für:**

- ❌ SIL 3/4 Anwendungen (zu hohe Komplexität)
- ❌ Nuklearanwendungen
- ❌ Medizinische Geräte (MDR/FDA)
- ❌ Luftfahrt (DO-178C)
- ❌ Automotive (ISO 26262)

**Begründung:** Diese Bereiche erfordern spezialisierte Architektur und Prozesse, die außerhalb des aktuellen MODAX-Fokus liegen.

### Geografischer Scope

**Primär:**
- 🇪🇺 Europäische Union (CE)
- 🇩🇪 Deutschland

**Sekundär (zukünftig):**
- 🇺🇸 USA (UL, CSA)
- 🇨🇳 China (CCC)
- 🇯🇵 Japan (PSE)

---

## Verantwortlichkeiten

### Compliance-Management

**Verantwortlich:** Projekt-Maintainer  
**Unterstützung:** Community, externe Berater (bei Bedarf)

**Aufgaben:**
- Norm-Updates verfolgen
- Compliance-Dokumentation pflegen
- Audits koordinieren
- Nicht-Konformitäten managen

### Normative Referenzen pflegen

**Prozess:**
1. Quartalsweise Review von relevanten Normen
2. Impact-Analyse bei Norm-Updates
3. Anpassung von Architektur/Code bei Bedarf
4. Dokumentation aktualisieren

---

## Haftungsausschluss

**WICHTIG:**

MODAX wird "AS IS" ohne jegliche Garantien bereitgestellt. Die Entwickler übernehmen keine Haftung für Schäden, die durch die Nutzung von MODAX entstehen.

Für **sicherheitskritische Anwendungen** ist eine **formale Risikoanalyse** und ggf. **Zertifizierung** durch den Anwender erforderlich.

Die Erwähnung von Normen in dieser Dokumentation bedeutet **nicht**, dass MODAX diese Normen **erfüllt** oder **zertifiziert** ist, sondern dass sie als **Leitlinien** für die Entwicklung dienen.

---

## Referenzen

### Normative Dokumente

- IEC 61508-1:2010 bis -7:2010 – Functional safety
- IEC 61131-1:2003, -2:2007, -3:2013 – Programmable controllers
- ISO 13849-1:2015, -2:2012 – Safety of machinery
- IEC 62443 Serie – Industrial network security
- IEC 62541 Serie – OPC Unified Architecture
- ISO 6983-1:2009 – Numerical control (G-Code)

### Informative Dokumente

- ISO 9001:2015 – Quality management
- ISO/IEC 25010:2011 – Software quality
- DIN 66025 – CNC programming

---

**Letzte Aktualisierung:** 2025-12-27  
**Nächste Review:** 2026-03-27  
**Verantwortlich:** Projekt-Maintainer
