# MODAX - Aufgabenliste (TODO)

Dieses Dokument verfolgt offene Aufgaben für das MODAX-Projekt. Erledigte Aufgaben werden nach `DONE.md` verschoben.

**Letzte Aktualisierung:** 2025-12-09  
**Aktuelle Version:** 0.4.0  
**Status:** Produktionsreif mit vollständiger Dokumentation, CNC-Funktionen, Test-Coverage (96-97%), CI/CD und Kubernetes-Support

## Offene Aufgaben

### Tests
- [ ] ESP32 Hardware-in-the-Loop Tests

### Dokumentation
- [ ] Video-Tutorials für Setup erstellen

## Zukünftige Ideen (Backlog)

### Phase 2 Features (Dokumentiert, bereit zur Implementierung)
Alle Phase 2 Features sind vollständig dokumentiert. Implementierung erfolgt nach Priorität und verfügbaren Ressourcen:
- ONNX-Modell-Deployment (siehe [docs/ONNX_MODEL_DEPLOYMENT.md](docs/ONNX_MODEL_DEPLOYMENT.md))
- Rollenbasierte Zugriffskontrolle - RBAC (siehe `python-control-layer/auth.py`)
- Multi-Mandanten-Unterstützung (siehe [docs/MULTI_TENANT_ARCHITECTURE.md](docs/MULTI_TENANT_ARCHITECTURE.md))
- Mobile App für Monitoring (siehe [docs/MOBILE_APP_ARCHITECTURE.md](docs/MOBILE_APP_ARCHITECTURE.md))

### Phase 3 Features (Dokumentiert, bereit zur Implementierung)
Alle Phase 3 Features sind vollständig dokumentiert. Implementierung erfolgt nach Priorität und verfügbaren Ressourcen:
- ML-Modell-Training-Pipeline (siehe [docs/ML_TRAINING_PIPELINE.md](docs/ML_TRAINING_PIPELINE.md))
- Flottenweite Analytik (siehe [docs/FLEET_ANALYTICS.md](docs/FLEET_ANALYTICS.md))
- Cloud-Integration - AWS, Azure, GCP (siehe [docs/CLOUD_INTEGRATION.md](docs/CLOUD_INTEGRATION.md))
- Digital Twin Integration (siehe [docs/DIGITAL_TWIN_INTEGRATION.md](docs/DIGITAL_TWIN_INTEGRATION.md))
- Federated Learning (siehe [docs/FEDERATED_LEARNING.md](docs/FEDERATED_LEARNING.md))
- Predictive Maintenance mit Deep Learning (dokumentiert in ML Pipeline und Digital Twin)
- Automatisierte Wartungsplanung (siehe [docs/ADVANCED_FEATURES_ROADMAP.md](docs/ADVANCED_FEATURES_ROADMAP.md))
- Edge Computing Optimierungen für ESP32 (siehe [docs/ADVANCED_FEATURES_ROADMAP.md](docs/ADVANCED_FEATURES_ROADMAP.md))
- Integration mit MES/ERP-Systemen wie SAP (siehe [docs/ADVANCED_FEATURES_ROADMAP.md](docs/ADVANCED_FEATURES_ROADMAP.md))
- Blockchain für unveränderliche Audit-Trails (siehe [docs/ADVANCED_FEATURES_ROADMAP.md](docs/ADVANCED_FEATURES_ROADMAP.md))

## Hinweise

- Alle Änderungen müssen getestet werden, bevor sie committed werden
- Dokumentation muss parallel zum Code aktualisiert werden
- Sicherheitsrelevante Änderungen erfordern ein Review
- Breaking Changes müssen im CHANGELOG.md dokumentiert werden
- TODO.md und ISSUES.md werden regelmäßig am 1. und 15. jeden Monats überprüft

## Abgeschlossene Aufgaben

Für eine vollständige Liste der abgeschlossenen Aufgaben siehe [DONE.md](DONE.md).

Kürzlich abgeschlossene Highlights:
- ✅ 123+ abgeschlossene TODO-Items (Stand: 2025-12-09)
- ✅ Vollständige Dokumentation (50+ Dokumente)
- ✅ CNC-Funktionalität implementiert und getestet
- ✅ Security-Features implementiert (MQTT TLS, API Auth, Audit Logging)
- ✅ Monitoring-Stack (Prometheus, Grafana, Loki)
- ✅ CI/CD Pipeline mit GitHub Actions
- ✅ Kubernetes-Support mit Helm Charts
- ✅ 96-97% Test-Coverage
