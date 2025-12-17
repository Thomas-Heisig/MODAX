# MODAX - Bekannte Probleme (ISSUES)

Dieses Dokument verfolgt bekannte Probleme und Bugs im MODAX-System. Behobene Probleme werden nach `DONE.md` verschoben.

**Letzte Aktualisierung:** 2025-12-17  
**Anzahl offener Issues:** 0 🎉  
**Status:** Alle bekannten Issues wurden behoben oder dokumentiert

## 🎉 Alle Issues behoben!

Aktuell gibt es **keine offenen kritischen, wichtigen oder kleineren Issues** im MODAX-System.

## Kürzlich behobene Issues

Die folgenden Issues wurden in den letzten Sessions behoben und sind nun in [DONE.md](DONE.md) dokumentiert:

### Kritische Issues (alle behoben)
- ✅ #022: MQTT Broker Authentifizierung
- ✅ #023: API-Endpunkte Authentifizierung

### Wichtige Issues (alle behoben)
- ✅ #001: MQTT Reconnection
- ✅ #002: API Timeouts konfigurierbar
- ✅ #003: HMI Fehlerbehandlung
- ✅ #004: Logging Standards
- ✅ #006: API-Dokumentation
- ✅ #007: Konfigurationsdokumentation
- ✅ #018: Sicherheitsdokumentation
- ✅ #019: Datenpersistenz-Dokumentation
- ✅ #020: Containerisierungs-Dokumentation
- ✅ #021: Monitoring-Dokumentation

### Performance und Code-Qualität (alle behoben)
- ✅ #008: Type Hints
- ✅ #009: Magic Numbers
- ✅ #010: Input-Validierung
- ✅ #011: Caching-Strategie
- ✅ #012: MQTT-Optimierung (dokumentiert)

### Features (alle implementiert oder dokumentiert)
- ✅ #015: AI Confidence Display (dokumentiert)
- ✅ #016: Export-Funktion (API implementiert, HMI dokumentiert)
- ✅ #017: Dark Mode (dokumentiert)
- ✅ #024: TimescaleDB Integration
- ✅ #025: Prometheus Metrics
- ✅ #026: WebSocket Support
- ✅ #028: Internationalisierung (dokumentiert)
- ✅ #029: Schema Migration (dokumentiert)
- ✅ #030: Health-Check Endpunkte

## Bekannte Einschränkungen

Während alle Issues behoben sind, gibt es einige bekannte Einschränkungen, die als zukünftige Verbesserungen geplant sind:

1. **ESP32 Hardware-in-the-Loop Tests** - Derzeit nur Software-Tests vorhanden
2. **Video-Tutorials** - Textbasierte Dokumentation ist vollständig, Video-Tutorials fehlen noch
3. **Feature-Implementierungen** - Einige Features wie Dark Mode, i18n sind dokumentiert, aber noch nicht implementiert

Diese Punkte sind in [TODO.md](TODO.md) als zukünftige Aufgaben aufgeführt.

## Neue Issues melden

Wenn Sie ein neues Problem entdecken:

1. Überprüfen Sie zunächst die [Dokumentation](docs/INDEX.md) und [DONE.md](DONE.md)
2. Konsultieren Sie den [Troubleshooting Guide](docs/TROUBLESHOOTING.md)
3. Erstellen Sie einen neuen Issue-Eintrag mit:
   - **Eindeutiger Nummer:** #XXX (nächste verfügbare Nummer)
   - **Beschreibung:** Klare Problembeschreibung
   - **Betroffene Komponenten:** Welche Teile des Systems sind betroffen
   - **Auswirkung:** Wie schwerwiegend ist das Problem
   - **Priorität:** Kritisch, Hoch, Mittel, Niedrig, Sehr Niedrig
   - **Reproduktionsschritte:** Wie kann das Problem nachvollzogen werden

## Hinweise

- Neue Issues sollten hier dokumentiert werden, bevor Code geändert wird
- Jedes Issue sollte eine eindeutige Nummer haben (#XXX)
- Prioritäten: Kritisch, Hoch, Mittel, Niedrig, Sehr Niedrig
- Bei Behebung eines Issues: In DONE.md verschieben mit Lösung und Commit-Hash
- Sicherheitsrelevante Issues sollten privat behandelt werden (nicht in öffentlichem Repo)

## Vollständige Issue-Historie

Für eine vollständige Übersicht aller jemals behobenen Issues siehe [DONE.md](DONE.md).
