# MODAX - Aufgabenliste (TODO)

Dieses Dokument verfolgt offene Aufgaben für das MODAX-Projekt. Erledigte Aufgaben werden nach `DONE.md` verschoben.

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

### Tests
- [ ] Unit-Tests für Python Control Layer hinzufügen
- [ ] Unit-Tests für Python AI Layer hinzufügen
- [ ] Integrationstests für MQTT-Kommunikation erstellen
- [ ] End-to-End-Tests für komplette Datenflusskette

### Sicherheit
- [x] Sicherheitskonzept dokumentieren (docs/SECURITY.md)
- [ ] MQTT-Authentifizierung implementieren (siehe docs/SECURITY.md)
- [ ] TLS/SSL für Produktionsumgebung einrichten (siehe docs/SECURITY.md)
- [ ] API-Authentifizierung hinzufügen (siehe docs/SECURITY.md)
- [ ] Secrets Management einrichten (siehe docs/SECURITY.md)
- [ ] Sicherheitsaudit durchführen

## Priorität 2: Hoch

### Funktionserweiterungen
- [ ] WebSocket-Unterstützung für Echtzeit-Updates im HMI
- [x] Zeitreihen-Datenbank-Integration dokumentieren (docs/DATA_PERSISTENCE.md)
- [ ] TimescaleDB implementieren (siehe docs/DATA_PERSISTENCE.md)
- [ ] Erweiterte Visualisierungen mit Diagrammen im HMI
- [ ] Daten-Export-Funktion (CSV, JSON)

### Code-Qualität
- [x] Logging-Format über alle Ebenen standardisieren (docs/LOGGING_STANDARDS.md)
- [x] Magic Numbers zu benannten Konstanten extrahieren (anomaly_detector.py, wear_predictor.py, optimizer.py)
- [ ] Fehlerbehandlung in allen API-Endpunkten vereinheitlichen
- [ ] Code-Linting mit flake8/pylint für Python-Code
- [ ] Code-Coverage-Berichte generieren

### Konfiguration
- [x] Standardwerte für alle Konfigurationsoptionen dokumentieren (docs/CONFIGURATION.md)
- [x] API Timeouts konfigurierbar machen (AI_LAYER_TIMEOUT)
- [ ] Umgebungsvariablen-Schema validieren
- [ ] Konfigurationsdatei-Loader mit Validierung erstellen

## Priorität 3: Mittel

### Performance
- [ ] Daten-Aggregations-Performance optimieren
- [ ] MQTT-Nachrichtengröße optimieren
- [ ] API-Response-Zeiten messen und optimieren
- [ ] Speicher-Nutzung überwachen und optimieren

### Benutzererfahrung
- [ ] HMI-Fehler-Dialoge benutzerfreundlicher gestalten
- [ ] Ladeindikatoren für asynchrone Operationen hinzufügen
- [ ] Tastaturkürzel im HMI implementieren
- [ ] Offline-Modus mit lokaler Datenspeicherung

### Wartbarkeit
- [ ] Abhängigkeiten auf neueste stabile Versionen aktualisieren
- [ ] Deprecation-Warnungen beheben
- [ ] Code-Kommentare für komplexe Algorithmen hinzufügen
- [ ] Architektur-Diagramme aktualisieren

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

## Hinweise

- Alle Änderungen müssen getestet werden, bevor sie committed werden
- Dokumentation muss parallel zum Code aktualisiert werden
- Sicherheitsrelevante Änderungen erfordern ein Review
- Breaking Changes müssen im CHANGELOG.md dokumentiert werden
