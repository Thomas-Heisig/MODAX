# ADR Template – Architecture Decision Record

**Status:** [Proposed | Accepted | Deprecated | Superseded]  
**Date:** YYYY-MM-DD  
**Deciders:** [Liste der Entscheidungsträger]  
**Technical Story:** [Optional: Link zu Issue/Epic]

---

## Context

**Welches Problem wird gelöst?**

[Beschreibe den Kontext und das Problem, das diese Entscheidung adressiert. Sei spezifisch über:
- Die aktuelle Situation
- Die Herausforderung oder das Problem
- Relevante Constraints (technisch, organisatorisch, zeitlich)
- Welche Business- oder technischen Ziele betroffen sind]

**Warum ist eine Entscheidung jetzt notwendig?**

[Erkläre die Dringlichkeit oder den Trigger für diese Entscheidung]

---

## Decision Drivers

**Wichtige Faktoren, die die Entscheidung beeinflussen:**

- **Technisch:**
  - [z.B. Performance-Anforderungen]
  - [z.B. Skalierbarkeits-Constraints]
  - [z.B. Technologie-Kompatibilität]

- **Sicherheit:**
  - [z.B. Safety-Requirements (IEC 61508)]
  - [z.B. Security-Anforderungen (IEC 62443)]
  - [z.B. Compliance-Vorgaben]

- **Organisatorisch:**
  - [z.B. Team-Skills]
  - [z.B. Budget/Ressourcen]
  - [z.B. Zeitrahmen]

- **Wartbarkeit:**
  - [z.B. Langzeit-Support]
  - [z.B. Dokumentation]
  - [z.B. Testing]

---

## Considered Options

### Option 1: [Name der Option]

**Beschreibung:**
[Detaillierte Beschreibung dieser Option]

**Pros (Vorteile):**
- ✅ [Vorteil 1]
- ✅ [Vorteil 2]
- ✅ [Vorteil 3]

**Cons (Nachteile):**
- ❌ [Nachteil 1]
- ❌ [Nachteil 2]
- ❌ [Nachteil 3]

**Bewertung:**
- **Performance:** [Skala 1-5]
- **Sicherheit:** [Skala 1-5]
- **Wartbarkeit:** [Skala 1-5]
- **Kosten:** [Skala 1-5]

---

### Option 2: [Name der Option]

[Gleiche Struktur wie Option 1]

---

### Option 3: [Name der Option]

[Optional: Weitere Optionen]

---

## Decision Outcome

**Gewählte Option:** Option X – [Name]

**Begründung:**
[Warum wurde diese Option gewählt? Welche Decision Drivers waren ausschlaggebend?]

**Erwartete Konsequenzen:**

**Positive:**
- ✅ [Erwarteter Vorteil 1]
- ✅ [Erwarteter Vorteil 2]

**Negative:**
- ⚠️ [Akzeptierter Nachteil 1 + Mitigation]
- ⚠️ [Akzeptierter Nachteil 2 + Mitigation]

**Trade-offs:**
[Welche Kompromisse wurden bewusst eingegangen?]

---

## Implementation

**Erforderliche Änderungen:**
1. [Änderung in Komponente A]
2. [Änderung in Komponente B]
3. [Neue Abhängigkeit C]

**Migration-Pfad:**
[Falls bestehende Systeme betroffen sind: Wie wird migriert?]

**Zeitrahmen:**
- **Prototyp:** [Datum]
- **Implementation:** [Datum]
- **Rollout:** [Datum]

**Verantwortliche:**
- **Lead:** [Name]
- **Contributors:** [Namen]

---

## Validation

**Wie wird validiert, dass die Entscheidung richtig war?**

**Erfolgskriterien:**
- [ ] [Kriterium 1: z.B. Performance <100ms]
- [ ] [Kriterium 2: z.B. Test Coverage >95%]
- [ ] [Kriterium 3: z.B. Zero Safety Incidents]

**Metriken:**
- [Metrik 1: z.B. API Latency]
- [Metrik 2: z.B. MTBF]
- [Metrik 3: z.B. Code Complexity]

**Review-Zeitpunkt:**
[Wann wird diese Entscheidung überprüft? z.B. nach 3 Monaten Produktionsbetrieb]

---

## Risks & Mitigation

| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|--------|-------------------|--------|------------|
| [Risiko 1] | Hoch/Mittel/Niedrig | Hoch/Mittel/Niedrig | [Maßnahme] |
| [Risiko 2] | | | |

---

## Related Decisions

**Abhängigkeiten:**
- [ADR-XXXX: Titel] (benötigt von dieser Entscheidung)
- [ADR-YYYY: Titel] (benötigt diese Entscheidung)

**Konflikte:**
- [ADR-ZZZZ: Titel] (widerspricht/ergänzt diese Entscheidung)

**Supersedes:**
- [Optional: ADR-AAAA wurde durch diese Entscheidung ersetzt]

---

## Notes

**Diskussionen:**
[Optional: Zusammenfassung wichtiger Diskussionspunkte]

**Referenzen:**
- [Externe Dokumente, Standards, Papers]
- [Interne Dokumentation]
- [Code-Repositories, PRs]

**Anhänge:**
- [Optional: Diagramme, Benchmarks, Prototyp-Code]

---

**Autor:** [Name]  
**Reviewer:** [Namen]  
**Letzte Aktualisierung:** YYYY-MM-DD
