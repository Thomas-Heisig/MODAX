# MODAX – Dokumentations-Index

**Version:** 0.6.0 (Reorganisiert nach Industrial Template)  
**Stand:** 2025-12-27

---

## Schnellstart

**Neu bei MODAX?** Starten Sie hier:
1. 📖 [Vision & Leitprinzipien](00-meta/vision.md)
2. 🏗️ [Systemüberblick](01-overview/index.md)
3. 🔧 [Setup-Anleitung](SETUP.md)
4. 📱 [Quick Reference](QUICK_REFERENCE.md)

**Entwickler?** Wichtige Ressourcen:
1. 💻 [GitHub Copilot Instructions](../.github/copilot-instructions.md) ⚠️ **PFLICHTLEKTÜRE**
2. 🏛️ [Architektur-Modell](02-system-architecture/layer-model.md)
3. 📋 [API-Dokumentation](API.md)
4. 🤝 [Contributing Guide](../CONTRIBUTING.md)

---

## 📚 Dokumentationsstruktur

### 00-meta – Projektsteuerung & Governance

Grundlegende Projekt-Informationen und strategische Dokumente.

| Dokument | Beschreibung |
|----------|--------------|
| [vision.md](00-meta/vision.md) | Vision, Leitprinzipien, Ziele, Abgrenzung |
| [roadmap.md](00-meta/roadmap.md) | Versions-Historie, Feature-Roadmap (v0.1-v2.0+) |
| [status.md](00-meta/status.md) | Aktueller Projektstatus, Metriken, Risiken |
| [compliance-scope.md](00-meta/compliance-scope.md) | Normen, Standards, Zertifizierungsplan |
| [contribution-model.md](00-meta/contribution-model.md) | Beitrags-Richtlinien (Kopie von CONTRIBUTING.md) |

**Für wen:** Projektleiter, Entscheider, Auditoren

---

### 01-overview – Systemüberblick

Einführung in MODAX für neue Nutzer und Stakeholder.

| Dokument | Beschreibung |
|----------|--------------|
| [index.md](01-overview/index.md) | **Haupteinstieg:** Was ist MODAX? Ebenen, Datenfluss, Use Cases |
| [system-principles.md](01-overview/system-principles.md) | 10 unveränderliche Grundsätze (Safety First, KI beratend, ...) |
| [glossary.md](01-overview/glossary.md) | Fachbegriffe und Definitionen (Automatisierung, CNC, KI) |
| [assumptions.md](01-overview/assumptions.md) | Technische & organisatorische Annahmen, Geltungsbereich |

**Für wen:** Alle Nutzer, Sales, Marketing

---

### 02-system-architecture – Gesamtsystemarchitektur

Detaillierte Architektur-Beschreibungen.

| Dokument | Beschreibung |
|----------|--------------|
| [layer-model.md](02-system-architecture/layer-model.md) | **Kern-Dokument:** 4-Ebenen-Architektur im Detail |
| [data-flow.md](02-system-architecture/data-flow.md) | Bottom-Up & Top-Down Datenflüsse, Performance-Metriken |
| [control-boundaries.md](02-system-architecture/control-boundaries.md) | **Kritisch:** KI-Grenzen, Sperrzonen, architektonische Durchsetzung |
| redundancy.md | Ausfallsicherheit, Failover-Mechanismen *(geplant)* |
| limitations.md | Bewusste Einschränkungen, Was MODAX nicht kann *(geplant)* |

**Für wen:** Architekten, Entwickler, Safety-Engineers

---

### 03-control-layer – Steuerungsebene (Python)

Details zur zentralen Koordinationsebene.

| Dokument | Beschreibung |
|----------|--------------|
| overview.md | Überblick Steuerungsebene *(zu migrieren)* |
| real-time-behavior.md | Echtzeit-Verhalten, Latenz-Garantien *(geplant)* |
| state-machines.md | Zustandsautomaten für CNC-Steuerung *(geplant)* |
| safety-functions.md | `is_system_safe()`, Safety-Validation *(zu dokumentieren)* |
| failure-handling.md | Fehlerbehandlung, Graceful Degradation *(zu migrieren)* |
| validation.md | Testing & Validation der Steuerungsebene *(geplant)* |

**Für wen:** Backend-Entwickler, CNC-Programmierer

**Migration-Status:** 🔄 Inhalte aus `ERROR_HANDLING.md`, `TESTING.md` zu migrieren

---

### 04-supervisory-layer – Überwachung & Koordination

Supervisory Control and Data Acquisition (SCADA)-Funktionen.

| Dokument | Beschreibung |
|----------|--------------|
| overview.md | Überwachungs- und Koordinationsfunktionen *(geplant)* |
| scheduling.md | Task-Scheduling, Priorisierung *(geplant)* |
| alarms-events.md | Alarm-Management, Ereignisprotokoll *(geplant)* |
| diagnostics.md | Systemdiagnostik, Health-Checks *(geplant)* |

**Für wen:** Operations-Team, SCADA-Engineers

**Migration-Status:** 📋 Inhalte aus `MONITORING.md` zu migrieren

---

### 05-analytics-and-ml-layer – KI-Ebene (Python)

Machine Learning & Analytics (beratend, nicht-steuernd).

| Dokument | Beschreibung |
|----------|--------------|
| purpose.md | Zweck der KI-Ebene, beratende Funktion *(zu dokumentieren)* |
| data-inputs.md | Welche Daten fließen in KI-Analysen? *(geplant)* |
| models.md | Prognosemodelle (Anomaly, Wear) *(zu migrieren)* |
| predictive-maintenance.md | Prädiktive Wartung im Detail *(zu erweitern)* |
| optimization-suggestions.md | Optimierungsempfehlungen, Parametrierung *(geplant)* |
| explainability.md | Erklärbarkeit von KI-Entscheidungen *(geplant)* |
| constraints.md | **Kritisch:** Was KI NICHT darf *(zu erstellen aus control-boundaries.md)* |

**Für wen:** Data Scientists, ML-Engineers

**Migration-Status:** 🔄 Inhalte aus `python-ai-layer/README.md`, `ONNX_MODEL_DEPLOYMENT.md` zu migrieren

---

### 06-interface-layer – Mensch-Maschine-Schnittstelle (C#)

HMI (Human-Machine Interface) Beschreibungen.

| Dokument | Beschreibung |
|----------|--------------|
| overview.md | HMI-Übersicht, MDI-Interface *(zu migrieren aus MDI_INTERFACE.md)* |
| operator-workflows.md | Bediener-Arbeitsabläufe *(geplant)* |
| decision-support.md | Entscheidungsunterstützung durch KI-Empfehlungen *(geplant)* |
| visualization.md | Visualisierungs-Konzepte, Dashboard *(geplant)* |
| access-control.md | Zugriffskontrolle, RBAC *(zu migrieren)* |

**Für wen:** Frontend-Entwickler, UX-Designer, Bediener

**Migration-Status:** 🔄 Inhalte aus `MDI_INTERFACE.md`, `HMI_ENHANCEMENTS.md` zu migrieren

---

### 07-implementation – Technische Umsetzung

Konkrete Implementierungs-Details.

| Dokument | Beschreibung |
|----------|--------------|
| system-overview.md | Technologie-Stack Überblick *(zu migrieren aus ARCHITECTURE.md)* |
| hardware-platforms.md | ESP32, Server-Hardware *(zu dokumentieren)* |
| communication-protocols.md | MQTT, REST, Protobuf *(zu migrieren aus DEVICE_COMMUNICATION_PROTOCOLS.md)* |
| deployment.md | Docker, Kubernetes, Helm *(zu migrieren aus CONTAINERIZATION.md, GITOPS_DEPLOYMENT.md)* |
| performance-notes.md | Performance-Tuning, Benchmarks *(geplant)* |

**Für wen:** DevOps, Integrations-Engineers

**Migration-Status:** 🔄 Viele Inhalte vorhanden, zu konsolidieren

---

### 08-operations – Betrieb & Wartung

Installations-, Konfigurations- und Betriebsdokumentation.

| Dokument | Beschreibung |
|----------|--------------|
| installation.md | **Installations-Anleitung** *(→ SETUP.md, INSTALL_GUIDE.md)* |
| configuration.md | Konfigurationsoptionen *(→ CONFIGURATION.md)* |
| update-strategy.md | Update-Prozeduren, Migrations *(→ SCHEMA_MIGRATION.md)* |
| logging.md | Logging-Standards, Log-Management *(→ LOGGING_STANDARDS.md)* |
| incident-response.md | Fehlersuche, Incident Response *(→ TROUBLESHOOTING.md)* |

**Für wen:** Admins, Operations-Team

**Migration-Status:** ✅ Meiste Inhalte bereits vorhanden, Referenzen zu setzen

---

### 09-decisions – Architektur- & Safety-Entscheidungen (ADRs)

Architecture Decision Records dokumentieren wichtige Entscheidungen.

| Dokument | Beschreibung |
|----------|--------------|
| [adr-template.md](09-decisions/adr-template.md) | **Template** für neue ADRs |
| [adr-0001-layer-separation.md](09-decisions/adr-0001-layer-separation.md) | **Warum 4 Ebenen?** Begründung der Architektur |
| [adr-0002-no-ai-in-control.md](09-decisions/adr-0002-no-ai-in-control.md) | **Warum keine KI in Steuerung?** Safety-Begründung |
| adr-0003-predictive-maintenance.md | Prädiktive Wartung (ML-Modelle) *(geplant)* |
| adr-0004-offline-training.md | Warum kein Online-Learning? *(geplant)* |
| adr-0005-mqtt-vs-opcua.md | MQTT für Feldebene, OPC UA für Integration *(geplant)* |

**Für wen:** Architekten, Entscheider, Auditoren

**Besonderheit:** ADRs sind **unveränderlich** (außer Status). Neue Entscheidungen = Neues ADR.

---

### 99-appendix – Anhänge

Referenzen, Standards-Mapping, Audit-Hinweise.

| Dokument | Beschreibung |
|----------|--------------|
| references.md | Normen, Fachliteratur, externe Links *(geplant)* |
| standards-mapping.md | Mapping zu IEC, ISO, etc. *(geplant)* |
| audit-notes.md | Hinweise für Auditoren *(geplant)* |

**Für wen:** Auditoren, Zertifizierer

---

## 🗂️ Bestehende Dokumentation (zur Migration/Archivierung)

### Kern-Dokumente (bleiben auf Root-Ebene)

| Datei | Status | Aktion |
|-------|--------|--------|
| [README.md](../README.md) | ✅ Aktuell | Verweist auf neue Struktur (zu aktualisieren) |
| [SETUP.md](SETUP.md) | ✅ Aktuell | Wird referenziert von `08-operations/installation.md` |
| [API.md](API.md) | ✅ Aktuell | Bleibt (wichtig für Entwickler) |
| [CONFIGURATION.md](CONFIGURATION.md) | ✅ Aktuell | Wird referenziert von `08-operations/configuration.md` |
| [CHANGELOG.md](../CHANGELOG.md) | ✅ Aktuell | Bleibt (wichtig für Versionierung) |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | ✅ Aktualisiert | Referenziert Copilot Instructions |
| [SECURITY.md](SECURITY.md) | ✅ Aktuell | Bleibt (wichtig für Security Reporting) |

### Feature-Dokumentation (zu migrieren/archivieren)

| Kategorie | Dateien | Ziel |
|-----------|---------|------|
| **CNC Features** | CNC_FEATURES.md, EXTENDED_GCODE_SUPPORT.md, HOBBYIST_CNC_SYSTEMS.md | → `03-control-layer/` + `99-appendix/` |
| **Industry 4.0** | ADVANCED_CNC_INDUSTRY_4_0.md, ADVANCED_FEATURES_ROADMAP.md | → `00-meta/roadmap.md` + `99-appendix/` |
| **Integration** | OPC_UA_INTEGRATION.md, DIGITAL_TWIN_INTEGRATION.md, FEDERATED_LEARNING.md, CLOUD_INTEGRATION.md | → `07-implementation/` |
| **ML/AI** | ML_TRAINING_PIPELINE.md, ONNX_MODEL_DEPLOYMENT.md, FLEET_ANALYTICS.md | → `05-analytics-and-ml-layer/` |
| **Deployment** | CONTAINERIZATION.md, CI_CD.md, GITOPS_DEPLOYMENT.md, HIGH_AVAILABILITY.md | → `07-implementation/` + `08-operations/` |
| **Operations** | MONITORING.md, LOGGING_STANDARDS.md, TROUBLESHOOTING.md, BACKUP_RECOVERY.md | → `08-operations/` |
| **Kommunikation** | DEVICE_COMMUNICATION_PROTOCOLS.md, MQTT_OPTIMIZATION.md, MQTT_SPARKPLUG_B.md, NETWORK_ARCHITECTURE.md | → `07-implementation/communication-protocols.md` |
| **Security** | SECURITY_IMPLEMENTATION.md, API_AUTHENTICATION_GUIDE.md, AUTHENTICATION_IMPLEMENTATION_GUIDE.md | → `06-interface-layer/access-control.md` + `99-appendix/` |
| **HMI** | MDI_INTERFACE.md, HMI_ENHANCEMENTS.md, MOBILE_APP_ARCHITECTURE.md | → `06-interface-layer/` |
| **Data** | DATA_PERSISTENCE.md, SCHEMA_MIGRATION.md | → `08-operations/` |
| **Testing** | TESTING.md, ERROR_HANDLING.md | → `03-control-layer/validation.md` |
| **Sonstiges** | ARCHITECTURE.md, BEST_PRACTICES.md, FUNCTION_REFERENCE.md, GLOSSARY.md, QUICK_REFERENCE.md, HELP.md | → Verschiedene Ziele oder `99-appendix/` |

**Status-Legende:**
- ✅ Fertig
- 🔄 In Arbeit
- 📋 Geplant
- 🗄️ Archiviert

---

## 📂 Spezielle Verzeichnisse

### archive/

Historische Implementierungs-Summaries, Session-Notes, Security Audits.

**Dateien:**
- `PHASE_X_IMPLEMENTATION_SUMMARY.md`
- `SESSION_SUMMARY_*.md`
- `SECURITY_AUDIT_*.md`
- `README.md` (Index)

**Für wen:** Projekt-Historie, nachträgliche Analyse

### docs/archive/

Ältere Dokumentations-Versionen.

**Dateien:**
- Archivierte Versions von Dokumenten nach größeren Rewrites

---

## 🔍 Dokumentation finden

### Nach Rolle

| Rolle | Start hier |
|-------|------------|
| **Neuer Nutzer** | [Systemüberblick](01-overview/index.md) → [Setup](SETUP.md) |
| **Entwickler** | [Copilot Instructions](../.github/copilot-instructions.md) → [Architektur](02-system-architecture/layer-model.md) → [API](API.md) |
| **CNC-Programmierer** | [CNC Features](CNC_FEATURES.md) → [G-Code Support](EXTENDED_GCODE_SUPPORT.md) |
| **Data Scientist** | [KI-Ebene](05-analytics-and-ml-layer/) → [ML Pipeline](ML_TRAINING_PIPELINE.md) |
| **DevOps** | [Deployment](07-implementation/deployment.md) → [Operations](08-operations/) |
| **Entscheider** | [Vision](00-meta/vision.md) → [Roadmap](00-meta/roadmap.md) → [Status](00-meta/status.md) |
| **Auditor** | [Compliance](00-meta/compliance-scope.md) → [ADRs](09-decisions/) → [Appendix](99-appendix/) |
| **Bediener** | [Quick Reference](QUICK_REFERENCE.md) → [HMI](06-interface-layer/) |

### Nach Thema

| Thema | Dokumente |
|-------|----------|
| **Sicherheit (Safety)** | [System-Prinzipien](01-overview/system-principles.md), [Control Boundaries](02-system-architecture/control-boundaries.md), [ADR-0002](09-decisions/adr-0002-no-ai-in-control.md), [Safety Functions](03-control-layer/safety-functions.md) |
| **KI/ML** | [KI-Ebene](05-analytics-and-ml-layer/), [Control Boundaries](02-system-architecture/control-boundaries.md), [ADR-0002](09-decisions/adr-0002-no-ai-in-control.md) |
| **Architektur** | [4-Ebenen-Modell](02-system-architecture/layer-model.md), [Datenfluss](02-system-architecture/data-flow.md), [ADR-0001](09-decisions/adr-0001-layer-separation.md) |
| **Installation** | [Setup](SETUP.md), [Installation Guide](../INSTALL_GUIDE.md), [Deployment](07-implementation/deployment.md) |
| **API** | [API Reference](API.md), [API Authentication](API_AUTHENTICATION_GUIDE.md) |
| **Troubleshooting** | [Troubleshooting](TROUBLESHOOTING.md), [Error Handling](ERROR_HANDLING.md), [Monitoring](MONITORING.md) |

---

## 📝 Dokumentations-Konventionen

### Sprache

- **Primär:** Deutsch (für deutsche Community)
- **Code-Kommentare:** Deutsch oder Englisch
- **API-Docs:** Englisch (internationale Nutzung)
- **README & Setup:** Englisch (Einsteiger weltweit)

### Markdown-Style

- **Überschriften:** # H1 (Titel), ## H2 (Hauptabschnitte), ### H3 (Unterabschnitte)
- **Code-Blöcke:** Mit Sprach-Tag ```python, ```bash, ```json
- **Tabellen:** Für strukturierte Daten
- **Emojis:** Sparsam, für visuelle Orientierung (✅❌📋🔄)
- **Links:** Relative Pfade bevorzugen

### Dateinamen

- **Kebab-case:** `layer-model.md`, nicht `Layer_Model.md` oder `layerModel.md`
- **ADRs:** `adr-XXXX-short-title.md` (führende Nullen)
- **Verzeichnisse:** Numerisch mit Beschreibung: `00-meta/`, `01-overview/`

---

## 🆘 Support & Feedback

**Probleme mit Dokumentation?**
- GitHub Issue: [Documentation Issue Template](https://github.com/Thomas-Heisig/MODAX/issues/new?labels=documentation)
- GitHub Discussions: [Q&A](https://github.com/Thomas-Heisig/MODAX/discussions)

**Verbesserungsvorschläge?**
- Pull Request willkommen! Siehe [Contributing Guide](../CONTRIBUTING.md)

---

**Letzte Aktualisierung:** 2025-12-27  
**Dokumentations-Version:** 0.6.0 (Industrial Template)  
**Maintainer:** Thomas Heisig
