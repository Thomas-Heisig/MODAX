# MODAX Roadmap

## Aktueller Status: Version 0.5.0

**Stand:** 2025-12-27  
**Status:** Prototyp / Early Production Ready  
**Nächstes Release:** v0.6.0 (geplant Q1 2026)

## Version History

### v0.5.0 – MDI Interface & Network Scanner (Dezember 2025)
**Status:** ✅ Released

Hauptfeatures:
- MDI (Multiple Document Interface) mit Tab-basierter UI
- Erweitertes Dashboard (Overview, Devices, Analytics, Logs)
- Network Scanner & Port Scanner Integration
- Device Type Detection (Modbus, OPC UA, MODAX)
- Umfangreiche Keyboard Shortcuts
- Rate Limiting für API-Schutz

### v0.4.1 – Robustheit & Industrielle Kommunikation (Dezember 2025)
**Status:** ✅ Released

Hauptfeatures:
- RS485/Modbus RTU Support
- MIDI Audio Feedback
- Pendant Device Support (USB HID)
- Slave Board I2C
- Fehlertoleranz & Graceful Degradation
- Automatische Wiederholungslogik

### v0.4.0 – CNC Erweiterungen (Dezember 2025)
**Status:** ✅ Released

Hauptfeatures:
- Erweiterte G-Code-Unterstützung (150+ Codes)
- NURBS, Threading, Zylindrische Interpolation
- Herstellerspezifische Codes (Siemens, Fanuc, Heidenhain, Okuma, Mazak)
- Makro-Unterstützung (G65/G66/G67)
- Hobbyist CNC Features

### v0.3.0 – Industry 4.0 Foundation (Dezember 2025)
**Status:** ✅ Released

Hauptfeatures:
- OPC UA Integration (dokumentiert)
- Advanced CNC Features Roadmap
- Industry 4.0 Architektur-Blueprint
- Digital Twin Konzept

### v0.2.0 – CNC Grundfunktionalität (November 2025)
**Status:** ✅ Released

Hauptfeatures:
- G-Code Parser (ISO 6983)
- Motion Control (Linear, Circular, Helikal)
- Werkzeugverwaltung (24-Platz-Magazin)
- Koordinatensysteme (G54-G59)
- Festzyklen (Bohren, Fräsen)

### v0.1.0 – Basis-Architektur (Oktober 2025)
**Status:** ✅ Released

Hauptfeatures:
- 4-Ebenen-Architektur
- ESP32 Feldebene
- Python Control & AI Layer
- C# HMI
- MQTT-basierte Kommunikation
- Basis-Anomalieerkennung

---

## Kurzfristige Roadmap (Q1 2026)

### v0.6.0 – Dokumentation & Compliance (geplant Januar 2026)

**Hauptziel:** Vollständige industrielle Dokumentationsstruktur

Features:
- [ ] Strukturierte Dokumentation nach Industrial Template
- [ ] Architecture Decision Records (ADRs)
- [ ] Compliance-Mapping (IEC 61508, IEC 61131, ISO 13849)
- [ ] Audit-Trail-Implementierung
- [ ] Erweiterte Sicherheitsdokumentation

**Zielgruppe:** Auditoren, Zertifizierer, industrielle Anwender

### v0.7.0 – ONNX ML Models (geplant Februar 2026)

**Hauptziel:** Produktionsreife ML-Modell-Integration

Features:
- [ ] ONNX Runtime Integration
- [ ] Modell-Versioning und -Management
- [ ] Offline-Training-Pipeline
- [ ] Modell-Validation Framework
- [ ] Performance-Monitoring

**Zielgruppe:** Data Scientists, ML Engineers

### v0.8.0 – Multi-Tenant & Auth (geplant März 2026)

**Hauptziel:** Enterprise-Ready Authentifizierung

Features:
- [ ] Multi-Tenant-Architektur
- [ ] RBAC (Role-Based Access Control)
- [ ] OAuth2/OIDC Integration
- [ ] Audit-Logging für Zugriffe
- [ ] Mandanten-Isolation

**Zielgruppe:** Enterprise-Kunden, Cloud-Deployments

---

## Mittelfristige Roadmap (Q2-Q3 2026)

### v0.9.0 – TimescaleDB Integration (Q2 2026)

Features:
- [ ] TimescaleDB für Zeitreihendaten
- [ ] Automatische Datenaggregation
- [ ] Historische Trend-Analysen
- [ ] Datenretention-Policies
- [ ] Continuous Aggregates

### v1.0.0 – Production Release (Q3 2026)

**Meilenstein:** Erste stabile Production-Version

Kriterien für 1.0:
- [ ] Vollständige Dokumentation
- [ ] 99%+ Test Coverage
- [ ] Benchmarked Performance
- [ ] Security Audit abgeschlossen
- [ ] Mindestens 3 Produktions-Deployments
- [ ] Community-Support etabliert
- [ ] Breaking Changes stabilisiert

Features:
- [ ] WebSocket Real-time Updates
- [ ] Advanced Visualizations (Grafana Integration)
- [ ] Mobile Companion App
- [ ] REST API v2 (stabil)

---

## Langfristige Roadmap (2026-2027)

### Phase 3: Industry 4.0 Integration (Q4 2026 - Q2 2027)

#### Advanced Communication Protocols
- [ ] OPC UA Server/Client (vollständig)
- [ ] EtherCAT Master
- [ ] PROFINET Integration
- [ ] MTConnect Protocol
- [ ] MQTT Sparkplug B

#### Digital Twin & Simulation
- [ ] Physics-based Digital Twin
- [ ] Real-time Synchronization
- [ ] What-if Scenario Analysis
- [ ] Predictive Simulation
- [ ] Virtual Commissioning

#### ML & AI Advancement
- [ ] Deep Learning für Predictive Maintenance
- [ ] Federated Learning über Flotten
- [ ] Reinforcement Learning für Optimierung
- [ ] Computer Vision Integration
- [ ] NLP für Operator Logs

#### Cloud & Edge
- [ ] AWS IoT Integration
- [ ] Azure IoT Hub Integration
- [ ] Google Cloud IoT
- [ ] Edge Computing Optimizations
- [ ] Hybrid Cloud/On-Prem Deployment

### Phase 4: Next Generation (Q3 2027 - Q4 2027)

#### Advanced HMI
- [ ] AR Maintenance Guidance (HoloLens, ARCore)
- [ ] Voice Control Interface
- [ ] Gesture Control
- [ ] Mobile-First Redesign
- [ ] Dark Mode & Accessibility

#### Enterprise Integration
- [ ] SAP MES Integration
- [ ] Oracle ERP Integration
- [ ] Microsoft Dynamics 365
- [ ] Custom MES/ERP Adapters
- [ ] Blockchain Audit Trails

#### Advanced Features
- [ ] Autonomous Quality Control
- [ ] Self-Healing Systems
- [ ] Quantum-Ready Cryptography
- [ ] 5G Integration
- [ ] Smart Factory Orchestration

---

## Feature-Kategorien

### Sicherheit & Compliance
| Feature | Version | Status | Priorität |
|---------|---------|--------|-----------|
| Hardware Safety Interlocks | v0.1.0 | ✅ | Kritisch |
| Safety Command Validation | v0.1.0 | ✅ | Kritisch |
| Audit Trails | v0.6.0 | 📋 Geplant | Hoch |
| IEC 61508 Compliance Docs | v0.6.0 | 📋 Geplant | Hoch |
| Security Audit | v1.0.0 | 📋 Geplant | Hoch |

### KI & Analytik
| Feature | Version | Status | Priorität |
|---------|---------|--------|-----------|
| Anomalieerkennung (Z-Score) | v0.1.0 | ✅ | Mittel |
| Verschleißvorhersage | v0.1.0 | ✅ | Mittel |
| ONNX Model Deployment | v0.7.0 | 📋 Geplant | Hoch |
| Deep Learning Models | v1.2.0 | 🔮 Future | Mittel |
| Federated Learning | v1.3.0 | 🔮 Future | Niedrig |

### CNC & Motion Control
| Feature | Version | Status | Priorität |
|---------|---------|--------|-----------|
| Basic G-Code (G0-G3) | v0.2.0 | ✅ | Kritisch |
| Extended G-Codes | v0.4.0 | ✅ | Hoch |
| Macro Support | v0.4.0 | ✅ | Mittel |
| 5-Axis Kinematics | v1.1.0 | 📋 Geplant | Mittel |
| Adaptive Feed Control | v1.2.0 | 🔮 Future | Niedrig |

### Kommunikation & Integration
| Feature | Version | Status | Priorität |
|---------|---------|--------|-----------|
| MQTT | v0.1.0 | ✅ | Kritisch |
| REST APIs | v0.1.0 | ✅ | Kritisch |
| OPC UA (Docs) | v0.3.0 | ✅ | Hoch |
| OPC UA (Implementation) | v1.1.0 | 📋 Geplant | Hoch |
| EtherCAT | v1.3.0 | 🔮 Future | Mittel |
| PROFINET | v1.3.0 | 🔮 Future | Mittel |

### Deployment & Operations
| Feature | Version | Status | Priorität |
|---------|---------|--------|-----------|
| Docker Compose | v0.1.0 | ✅ | Hoch |
| Kubernetes/Helm | v0.3.0 | ✅ | Hoch |
| GitOps Deployment | v0.3.0 | ✅ | Mittel |
| Auto-Scaling | v1.0.0 | 📋 Geplant | Mittel |
| High Availability | v1.1.0 | 📋 Geplant | Hoch |

---

## Abhängigkeiten & Constraints

### Technische Abhängigkeiten
- Python 3.8+ Support bis mindestens v2.0
- .NET 8.0 LTS bis November 2026
- ESP32 Platform (Arduino Core)
- MQTT Broker (Mosquitto/HiveMQ)

### Ressourcen-Constraints
- Open-Source-Projekt mit limitierten Ressourcen
- Community-driven Development
- Features werden priorisiert nach:
  1. Sicherheit
  2. Industrielle Anforderungen
  3. Community-Bedarf
  4. Machbarkeit

### Breaking Changes Policy
- Major Versions (1.x → 2.x): Breaking Changes erlaubt
- Minor Versions (1.1 → 1.2): Nur in begründeten Ausnahmen
- Patch Versions (1.1.1 → 1.1.2): Keine Breaking Changes
- Deprecation-Zeitraum: Mindestens 2 Minor Versions

---

## Community-Beiträge

Willkommen sind Beiträge in allen Bereichen:

### Besonders gesucht:
- 🔴 **Hoch:** Safety-Testing, Security Audits
- 🟠 **Mittel:** Industrial Protocol Implementation, CNC Features
- 🟡 **Niedrig:** Documentation, Examples, Tutorials

### Contribution-Prozess:
1. Issue erstellen oder bestehendes Issue assignen
2. Feature Branch erstellen
3. Implementation mit Tests
4. Dokumentation aktualisieren
5. Pull Request öffnen
6. Code Review durchlaufen
7. Merge nach Approval

Siehe [CONTRIBUTING.md](../../CONTRIBUTING.md) für Details.

---

## Feedback & Priorisierung

Roadmap-Anpassungen basierend auf:
- **Community-Feedback:** GitHub Issues & Discussions
- **Industrielle Anforderungen:** Partner-Feedback
- **Sicherheits-Audits:** Erkenntnisse aus Reviews
- **Technische Evolution:** Neue Standards und Technologien

**Kontakt für Roadmap-Feedback:**
- GitHub Issues: Feature Requests
- GitHub Discussions: Allgemeine Vorschläge
- Security: Private Vulnerability Reports

---

**Legende:**
- ✅ Released
- 🚧 In Arbeit
- 📋 Geplant
- 🔮 Future/Vision
- ❌ Verworfen

**Letzte Aktualisierung:** 2025-12-27
