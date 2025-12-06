# MODAX - Aufgabenliste (TODO)

Dieses Dokument verfolgt offene Aufgaben für das MODAX-Projekt. Erledigte Aufgaben werden nach `DONE.md` verschoben.

## Priorität 1: Kritisch

### Dokumentation
- [x] API-Dokumentation für alle REST-Endpunkte erstellen (docs/API.md)
- [x] Fehlerbehandlungs-Leitfaden dokumentieren (docs/ERROR_HANDLING.md)
- [x] Konfigurationsoptionen vollständig dokumentieren (docs/CONFIGURATION.md)

### Tests
- [ ] Unit-Tests für Python Control Layer hinzufügen
- [ ] Unit-Tests für Python AI Layer hinzufügen
- [ ] Integrationstests für MQTT-Kommunikation erstellen
- [ ] End-to-End-Tests für komplette Datenflusskette

### Sicherheit
- [ ] MQTT-Authentifizierung implementieren
- [ ] TLS/SSL für Produktionsumgebung einrichten
- [ ] API-Authentifizierung hinzufügen
- [ ] Sicherheitsaudit durchführen

## Priorität 2: Hoch

### Funktionserweiterungen
- [ ] WebSocket-Unterstützung für Echtzeit-Updates im HMI
- [ ] Zeitreihen-Datenbank-Integration (z.B. InfluxDB)
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
- [ ] Prometheus-Metriken exportieren
- [ ] Grafana-Dashboards erstellen
- [ ] Log-Aggregation mit ELK-Stack einrichten
- [ ] Alerting-System für kritische Fehler

### Deployment
- [ ] Docker-Container für alle Ebenen erstellen
- [ ] Docker-Compose-Datei für schnellen Start
- [ ] Kubernetes-Manifeste für Produktionsbereitstellung
- [ ] CI/CD-Pipeline mit GitHub Actions

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
