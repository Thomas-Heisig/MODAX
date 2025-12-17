# MODAX Installation Guide

## Automatische Installation (Empfohlen)

Die einfachste Methode, MODAX zu installieren, ist die Verwendung des automatischen Installationsskripts.

### Voraussetzungen

- Python 3.8 oder höher
- .NET 8.0 SDK (optional, nur für HMI erforderlich)
- MQTT Broker (Mosquitto) oder Docker

### Schnellstart

```bash
# Repository klonen
git clone https://github.com/Thomas-Heisig/MODAX.git
cd MODAX

# Installation ausführen
./install.sh

# Dienste starten
./start-all.sh
```

### Was macht das Installationsskript?

Das `install.sh` Skript führt folgende Schritte automatisch aus:

1. **Systemprüfung**: Erkennt Betriebssystem und prüft Voraussetzungen
2. **Python-Umgebungen**: Erstellt virtuelle Umgebungen für Control- und AI-Layer
3. **Abhängigkeiten**: Installiert alle Python-Pakete
4. **.NET Setup**: Konfiguriert HMI-Layer (falls .NET SDK verfügbar)
5. **Konfiguration**: Erstellt `.env` Konfigurationsdateien
6. **Start-Skripte**: Generiert `start-all.sh` und `stop-all.sh`
7. **Validierung**: Testet alle Komponenten auf korrekte Installation

### Dienste verwalten

```bash
# Alle Dienste starten
./start-all.sh

# Dienste stoppen
./stop-all.sh

# Logs anzeigen
tail -f logs/control-layer.log
tail -f logs/ai-layer.log
```

### Zugriff auf Services

Nach erfolgreicher Installation:

- **Control Layer API**: http://localhost:8000
- **AI Layer API**: http://localhost:8001
- **API Dokumentation**: http://localhost:8000/docs

### HMI starten (Windows)

```bash
cd csharp-hmi-layer
dotnet run
```

## Manuelle Installation

Siehe [docs/SETUP.md](docs/SETUP.md) für detaillierte manuelle Installationsschritte.

## Fehlertoleranz

Das MODAX-System ist fehlertolerant gestaltet:

### Automatische Wiederholungen

- Alle Services versuchen 3-mal zu starten bei Fehlern
- 2 Sekunden Wartezeit zwischen Versuchen
- Detaillierte Fehlerprotokollierung

### Graceful Degradation

- Control Layer startet auch ohne OPC UA
- AI Layer kann unabhängig neu gestartet werden
- HMI startet immer, auch wenn Backend nicht verfügbar

### Fehlerbehandlung

- Globale Exception Handler in allen Layern
- Konfigurationsfehler werden abgefangen
- Services laufen weiter bei nicht-kritischen Fehlern

## Fehlerbehebung

### MQTT Broker nicht verfügbar

```bash
# Mit Docker starten
docker run -d -p 1883:1883 eclipse-mosquitto

# Oder auf Ubuntu installieren
sudo apt-get install mosquitto mosquitto-clients
sudo systemctl start mosquitto
```

### Python-Abhängigkeiten fehlen

```bash
cd python-control-layer
source venv/bin/activate
pip install -r requirements.txt
```

### Port bereits belegt

Passen Sie die Ports in den `.env` Dateien an:

```bash
# python-control-layer/.env
API_PORT=8080

# python-ai-layer/.env
AI_PORT=8081
```

### Logs prüfen

```bash
# Control Layer Log
cat logs/control-layer.log

# AI Layer Log
cat logs/ai-layer.log
```

## Code-Qualität

### Linting ausführen

```bash
# Standard Modus (informativ)
./lint.sh

# Strict Modus (erzwingt alle Checks)
./lint.sh --strict
```

### Tests ausführen

```bash
# Alle Tests mit Coverage
./test_with_coverage.sh

# Nur Control Layer
cd python-control-layer && python -m unittest discover -v

# Nur AI Layer
cd python-ai-layer && python -m unittest discover -v
```

## Entwicklungsumgebung

### Dev-Dependencies installieren

```bash
# Control Layer
cd python-control-layer
source venv/bin/activate
pip install -r dev-requirements.txt

# AI Layer
cd python-ai-layer
source venv/bin/activate
pip install -r dev-requirements.txt
```

### Verfügbare Tools

- **flake8**: PEP 8 Compliance
- **pylint**: Code-Analyse
- **mypy**: Statische Typprüfung
- **pytest**: Unit-Testing
- **black**: Code-Formatierung
- **isort**: Import-Sortierung

## Docker Deployment

Siehe [docker-compose.yml](docker-compose.yml) für Container-basiertes Deployment:

```bash
# Mit Docker Compose starten
docker-compose up -d

# Logs anzeigen
docker-compose logs -f

# Stoppen
docker-compose down
```

## Produktionsumgebung

Siehe [docker-compose.prod.yml](docker-compose.prod.yml) für Produktion:

```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Weitere Dokumentation

- [README.md](README.md) - Projektübersicht
- [docs/SETUP.md](docs/SETUP.md) - Detaillierte Setup-Anleitung
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - System-Architektur
- [docs/API.md](docs/API.md) - API-Dokumentation
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) - Problemlösungen

## Support

Bei Problemen:

1. Prüfen Sie die Logs in `logs/`
2. Konsultieren Sie [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
3. Öffnen Sie ein Issue auf GitHub

---

**Version**: 1.0.0  
**Aktualisiert**: Dezember 2024
