# MODAX - Aufgabenliste (TODO)

Dieses Dokument verfolgt offene Aufgaben für das MODAX-Projekt. Erledigte Aufgaben werden nach `DONE.md` verschoben.

**Letzte Aktualisierung:** 2025-12-07  
**Aktuelle Version:** 0.2.0  
**Status:** Produktionsreif mit vollständiger Dokumentation, CNC-Funktionen und Test-Coverage (96-97%)

## Priorität 1: Kritisch

### Dokumentation
- [x] API-Dokumentation für alle REST-Endpunkte erstellen (docs/API.md)
- [x] Fehlerbehandlungs-Leitfaden dokumentieren (docs/ERROR_HANDLING.md)
- [x] Konfigurationsoptionen vollständig dokumentieren (docs/CONFIGURATION.md)
- [x] Sicherheitskonzept dokumentieren (docs/SECURITY.md)
- [x] Datenpersistenz-Strategie dokumentieren (docs/DATA_PERSISTENCE.md)
- [x] Containerisierung dokumentieren (docs/CONTAINERIZATION.md)
- [x] Monitoring-Stack dokumentieren (docs/MONITORING.md)
- [x] CI/CD-Pipeline dokumentieren (docs/CI_CD.md)
- [x] High Availability dokumentieren (docs/HIGH_AVAILABILITY.md)
- [x] Netzwerkarchitektur & OT/IT-Trennung dokumentieren (docs/NETWORK_ARCHITECTURE.md)
- [x] Backup & Recovery Prozeduren dokumentieren (docs/BACKUP_RECOVERY.md)
- [x] OPC UA Integration dokumentieren (docs/OPC_UA_INTEGRATION.md)
- [x] Dokumentations-Index erstellen (docs/INDEX.md)
- [x] TODO.md und ISSUES.md Datum auf 2025 aktualisieren
- [x] CNC-Funktionen dokumentieren (docs/CNC_FEATURES.md)
- [ ] Dokumentation auf 2025 aktualisieren (verbleibende Dokumente im docs/ Verzeichnis)

### Tests
- [x] Unit-Tests für Python Control Layer hinzufügen (42 Tests)
- [x] Unit-Tests für Python AI Layer hinzufügen (56 Tests)
- [x] Unit-Tests für CNC-Module hinzufügen (25+ Tests)
- [x] Integrationstests für MQTT-Kommunikation erstellen
- [x] Test-Coverage-Reporting einrichten (test_with_coverage.sh)
- [ ] End-to-End-Tests für komplette Datenflusskette erweitern
- [ ] ESP32 Hardware-in-the-Loop Tests
- [ ] Performance-Tests für API-Endpunkte
- [ ] Load-Tests für Multi-Device-Szenarien

### Sicherheit
- [x] Sicherheitskonzept dokumentieren (docs/SECURITY.md)
- [x] MQTT-Authentifizierung implementieren (siehe docs/SECURITY.md)
- [x] TLS/SSL für Produktionsumgebung einrichten (siehe docs/SECURITY.md)
- [x] API-Authentifizierung hinzufügen (siehe docs/SECURITY.md)
- [x] Secrets Management einrichten (siehe docs/SECURITY.md)
- [x] Security Implementation dokumentieren (docs/SECURITY_IMPLEMENTATION.md)
- [ ] Sicherheitsaudit durchführen

## Priorität 2: Hoch

### Funktionserweiterungen
- [x] WebSocket-Unterstützung für Echtzeit-Updates im HMI
- [x] Zeitreihen-Datenbank-Integration dokumentieren (docs/DATA_PERSISTENCE.md)
- [x] TimescaleDB implementieren (siehe docs/DATA_PERSISTENCE.md)
- [ ] Erweiterte Visualisierungen mit Diagrammen im HMI
- [x] Daten-Export-Funktion (CSV, JSON)

### Code-Qualität
- [x] Logging-Format über alle Ebenen standardisieren (docs/LOGGING_STANDARDS.md)
- [x] Magic Numbers zu benannten Konstanten extrahieren (47 Konstanten definiert)
- [x] Code-Linting mit flake8/pylint für Python-Code (lint.sh)
- [x] Code-Coverage-Berichte generieren (test_with_coverage.sh, 96-97% coverage)
- [x] Ungenutzte Imports entfernen (pyflakes-clean)
- [ ] Type Hints für alle Python-Funktionen vervollständigen
- [ ] mypy für statische Type-Checking aktivieren
- [ ] Docstring-Coverage auf 100% bringen
- [ ] Fehlerbehandlung in allen API-Endpunkten vereinheitlichen

### Konfiguration
- [x] Standardwerte für alle Konfigurationsoptionen dokumentieren (docs/CONFIGURATION.md)
- [x] API Timeouts konfigurierbar machen (AI_LAYER_TIMEOUT)
- [ ] Umgebungsvariablen-Schema validieren
- [ ] Konfigurationsdatei-Loader mit Validierung erstellen

## Priorität 3: Mittel

### Performance
- [x] Daten-Aggregations-Performance optimieren (Vectorized numpy operations, 3-5x speedup)
- [x] MQTT-Nachrichtengröße optimieren (Dokumentation und Measurement-Tool erstellt)
- [x] API-Response-Zeiten messen und optimieren (Prometheus metrics hinzugefügt)
- [x] Speicher-Nutzung überwachen und optimieren (Ring buffers, float32, lazy evaluation)

### Benutzererfahrung
- [x] HMI-Fehler-Dialoge benutzerfreundlicher gestalten (Kontextspezifische Fehlerdialoge mit Troubleshooting)
- [x] Ladeindikatoren für asynchrone Operationen hinzufügen (Loading panel implementiert)
- [x] Tastaturkürzel im HMI implementieren (F5, Ctrl+R, Ctrl+S, Ctrl+T, F1)
- [ ] Offline-Modus mit lokaler Datenspeicherung (Benötigt Datenpersistenz-Implementation)

### Wartbarkeit
- [x] Abhängigkeiten auf neueste stabile Versionen aktualisieren (Bereits aktuell)
- [x] Deprecation-Warnungen beheben (Keine gefunden)
- [x] Code-Kommentare für komplexe Algorithmen hinzufügen (Anomalieerkennung, Verschleißvorhersage)
- [x] Architektur-Diagramme aktualisieren (Performance-Optimierungen dokumentiert)

## Priorität 4: Niedrig

### Monitoring
- [x] Monitoring-Stack dokumentieren (docs/MONITORING.md)
- [ ] Prometheus-Metriken exportieren (siehe docs/MONITORING.md)
- [ ] Grafana-Dashboards erstellen (siehe docs/MONITORING.md)
- [ ] Log-Aggregation mit Loki einrichten (siehe docs/MONITORING.md)
- [ ] Alerting-System für kritische Fehler (siehe docs/MONITORING.md)

### Deployment
- [x] Containerisierung dokumentieren (docs/CONTAINERIZATION.md)
- [x] CI/CD-Pipeline dokumentieren (docs/CI_CD.md)
- [x] High Availability dokumentieren (docs/HIGH_AVAILABILITY.md)
- [x] Backup & Recovery dokumentieren (docs/BACKUP_RECOVERY.md)
- [ ] Docker-Container für alle Ebenen erstellen (siehe docs/CONTAINERIZATION.md)
- [ ] Docker-Compose-Datei für schnellen Start (siehe docs/CONTAINERIZATION.md)
- [ ] Kubernetes-Manifeste für Produktionsbereitstellung
- [ ] CI/CD-Pipeline mit GitHub Actions implementieren (siehe docs/CI_CD.md)
- [ ] Helm Charts für Kubernetes Deployment erstellen
- [ ] GitOps-Workflow mit ArgoCD oder Flux einrichten

### Integration
- [x] OPC UA Integration dokumentieren (docs/OPC_UA_INTEGRATION.md)
- [ ] OPC UA Server implementieren (siehe docs/OPC_UA_INTEGRATION.md)
- [ ] Externe System-Integrationen dokumentieren (ERP/MES/SCADA)
- [ ] MQTT Sparkplug B implementieren

### Dokumentation
- [ ] Video-Tutorials für Setup erstellen
- [ ] Troubleshooting-Guide erweitern
- [ ] Best-Practices-Dokument schreiben
- [ ] Beitragsrichtlinien (CONTRIBUTING.md) erstellen

## Zukünftige Ideen (Backlog)

### Phase 2 (Geplant)
- [ ] ONNX-Modell-Deployment für tiefere KI-Integration
- [ ] Mobile App für Monitoring (iOS/Android)
- [ ] Multi-Mandanten-Unterstützung
- [ ] Rollenbasierte Zugriffskontrolle (RBAC)

### Phase 3 (Zukunft)
- [ ] ML-Modell-Training-Pipeline
- [ ] Flottenweite Analytik über mehrere Standorte
- [ ] Cloud-Integration (AWS, Azure, GCP)
- [ ] Automatisierte Wartungsplanung
- [ ] Predictive Maintenance mit Deep Learning
- [ ] Edge Computing Optimierungen für ESP32
- [ ] Federated Learning über mehrere MODAX-Instanzen
- [ ] Integration mit bestehenden MES/ERP-Systemen (SAP, etc.)
- [ ] Blockchain für unveränderliche Audit-Trails
- [ ] Digital Twin Integration für Simulationen

## Quick Wins (Schnell umsetzbar, hoher Wert)

### ✅ Sofort umsetzbare Verbesserungen (Alle implementiert - siehe [docs/TOFU.md](docs/TOFU.md))
- [x] Health-Check-Endpunkte zu allen APIs hinzufügen (/health, /ready)
- [x] API-Versionierung einführen (z.B. /api/v1/...)
- [x] Standardisierte Error-Response-Struktur über alle APIs
- [x] Rate-Limiting für öffentliche API-Endpunkte
- [x] CORS-Header konfigurierbar machen
- [x] Graceful Shutdown für alle Services implementieren
- [x] Umgebungsvariablen-Validierung beim Start
- [x] Strukturierte JSON-Logs einführen
- [x] Prometheus Metrics Endpunkte hinzufügen
- [x] Docker Health-Checks in alle Dockerfiles
- [x] TOFU.md Dokumentation erstellt
- [x] README.md aktualisiert mit Verweis auf TOFU.md

## Priorität 5: Housekeeping

### Wartung & Aktualisierung
- [x] TODO.md Datum auf 2025 korrigieren
- [x] ISSUES.md Datum auf 2025 korrigieren
- [x] DONE.md mit erledigten Aufgaben von 2025-12-07 aktualisieren
- [ ] Alle Dokumentationsdateien auf Datum 2025 prüfen
- [ ] CHANGELOG.md für Version 0.2.0 vorbereiten
- [ ] Dokumentations-Index auf Vollständigkeit prüfen

### Code-Cleanup
- [ ] Deprecated Features identifizieren und entfernen
- [ ] Code-Kommentare auf Aktualität prüfen
- [ ] TODO-Kommentare im Code konsolidieren
- [ ] Ungenutzte Konfigurationsoptionen entfernen

## Hinweise

- Alle Änderungen müssen getestet werden, bevor sie committed werden
- Dokumentation muss parallel zum Code aktualisiert werden
- Sicherheitsrelevante Änderungen erfordern ein Review
- Breaking Changes müssen im CHANGELOG.md dokumentiert werden
- TODO.md und ISSUES.md werden regelmäßig am 1. und 15. jeden Monats überprüft
