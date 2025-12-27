# MODAX Documentation – Reorganized Structure

**⚠️ HINWEIS:** Die Dokumentation wurde am 2025-12-27 nach einem industriellen Template reorganisiert.

## 📖 Neuer Hauptindex

**Bitte verwenden Sie:** **[NEW_INDEX.md](NEW_INDEX.md)** für die vollständige Dokumentations-Navigation.

---

## Schnellstart

- **Neu bei MODAX?** → [Systemüberblick](01-overview/index.md)
- **Entwickler?** → [GitHub Copilot Instructions](../.github/copilot-instructions.md) ⚠️ **PFLICHTLEKTÜRE**
- **Installation?** → [Setup-Anleitung](SETUP.md)

---

## Neue Struktur-Übersicht

Die Dokumentation ist jetzt in klare Bereiche organisiert:

```
docs/
├── 00-meta/                  # Projektsteuerung (Vision, Roadmap, Status)
├── 01-overview/              # Systemüberblick für Einsteiger
├── 02-system-architecture/   # Architektur-Details (4 Ebenen, Datenfluss)
├── 03-control-layer/         # Steuerungsebene (Python)
├── 04-supervisory-layer/     # Überwachung & Koordination
├── 05-analytics-and-ml-layer/# KI-Ebene (beratend)
├── 06-interface-layer/       # HMI (C# Windows Forms)
├── 07-implementation/        # Technische Umsetzung
├── 08-operations/            # Betrieb & Wartung
├── 09-decisions/             # Architecture Decision Records (ADRs)
└── 99-appendix/              # Referenzen, Standards-Mapping
```

---

## Wichtige neue Dokumente

### Governance & Vision
- [Vision & Leitprinzipien](00-meta/vision.md)
- [Roadmap](00-meta/roadmap.md)
- [Projektstatus](00-meta/status.md)
- [Compliance-Scope](00-meta/compliance-scope.md)

### Architektur
- [4-Ebenen-Modell](02-system-architecture/layer-model.md) ⭐ **Kern-Dokument**
- [Datenfluss](02-system-architecture/data-flow.md)
- [Control Boundaries](02-system-architecture/control-boundaries.md) ⭐ **Kritisch für Safety**

### Entscheidungen (ADRs)
- [ADR-0001: Warum 4 Ebenen?](09-decisions/adr-0001-layer-separation.md)
- [ADR-0002: Warum keine KI in Steuerung?](09-decisions/adr-0002-no-ai-in-control.md) ⭐ **Fundamentale Safety-Entscheidung**

---

## Migration-Status

| Status | Bedeutung | Beispiele |
|--------|-----------|-----------|
| ✅ | Fertig, neue Struktur | 00-meta/, 01-overview/, 02-system-architecture/ (teilweise), 09-decisions/ |
| 🔄 | In Arbeit | 03-06 Layer-Spezifische Docs |
| 📋 | Geplant | 07-implementation/, 08-operations/, 99-appendix/ |
| 🗄️ | Archiviert | Alte Session-Summaries → archive/ |

Bestehende Dokumentation (ROOT-Ebene) bleibt verfügbar und wird schrittweise migriert oder referenziert.

---

## Für Entwickler: Strikte Regeln

⚠️ **WICHTIG:** Alle Entwickler **MÜSSEN** die [GitHub Copilot Instructions](../.github/copilot-instructions.md) lesen!

**Kernregeln:**
1. **Safety First:** KI niemals in sicherheitskritischen Funktionen
2. **Payload Strict:** Type Hints + Docstrings verpflichtend
3. **Immer dokumentieren:** Jede öffentliche API muss dokumentiert sein
4. **Ebenentrennung:** Strikte Trennung der 4 Ebenen einhalten
5. **Gleiche Codebase:** Konsistente Patterns und Konventionen

---

## Alte Dokumentation

Die alte flache Struktur (alle .md-Dateien im `/docs`-Verzeichnis) bleibt vorerst bestehen und wird schrittweise:
- **Migriert** in neue Struktur (konsolidiert)
- **Referenziert** (wenn bereits gut dokumentiert)
- **Archiviert** (wenn veraltet)

**Übergang:** Beide Strukturen koexistieren während der Migration.

---

## Feedback & Fragen

- **Dokumentations-Issues:** [GitHub Issues](https://github.com/Thomas-Heisig/MODAX/issues) (Label: `documentation`)
- **Fragen:** [GitHub Discussions](https://github.com/Thomas-Heisig/MODAX/discussions)

---

**Reorganisiert:** 2025-12-27  
**Basierend auf:** Industrielles Steuerungssystem-Template (IEC 61508, ISO 13849-konform)  
**Verantwortlich:** Thomas Heisig + Community
