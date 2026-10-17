---
name: guardrails-sop
description: "Standard Operating Procedure (SOP) zur verfassungskonformen Bearbeitung, Erweiterung und Schärfung der Groundsole-Kerndokumente (STYLE_AND_GUARDRAILS.md, DYNAMIC_STATE.md, AGENTS.md, CORE_PRINCIPLES)."
version: 1.0.0
author: Emanuel Gössler
tags: [groundsole, governance, guardrails, sop, architecture, rules]
---

# Guardrails SOP Skill (Verfassungs- & Governance-Prozedur)

Dieser Skill ist das verbindliche Gatekeeper-Protokoll zur Pflege, Schärfung und Erweiterung der Groundsole-Kerndokumente – allen voran `00_MEMORY/STYLE_AND_GUARDRAILS.md` (`S_&_G`), `00_MEMORY/DYNAMIC_STATE.md` und `00_FRAMEWORK/architecture/01_CORE_PRINCIPLES_AND_SSOT.md`.

Er verhindert zuverlässig **„Rule Creep“ (Regel-Entropie)**, Kontext-Aufblähung bei jedem Session-Start und das Hineinrutschen von operativen Werkzeug-Anweisungen in die systemweite Verfassung.

---

## 🎯 Trigger Conditions

Aktiviere diesen Skill zwingend, sobald:
- Der Benutzer anweist: *„Nimm Regel X in S_A_G auf“*, *„Ergänze die Guardrails um...“*, *„Schärfe die Regeln“*, *„Passe STYLE_AND_GUARDRAILS an“*.
- Ein wiederkehrendes Fehlverhalten des Agenten eine dauerhafte Systemanpassung erfordert.
- `DYNAMIC_STATE.md`, `AGENTS.md` oder die `CORE_PRINCIPLES` editiert oder restrukturiert werden sollen.

---

## 🛡️ Die 4 Prüf-Gates (Gatekeeper-Protokoll)

Bevor auch nur eine einzige Zeile in `STYLE_AND_GUARDRAILS.md` oder verwandten Verfassungsdateien verändert wird, MUSS der Agent folgende vier Gates durchlaufen und das Ergebnis transparent darlegen:

```
[Vorschlag] ➔ Gate 1 (Triage) ➔ Gate 2 (Rationale) ➔ Gate 3 (Abstraktion) ➔ Gate 4 (Vollzug) ➔ [S_&_G]
```

### Gate 1: Der Triage-Test (Oben vs. Unten / Verfassung vs. Handwerk)
Prüfe den Zielort der Anweisung:
* **Kommt es nach OBEN (`S_&_G`):**
  * Nur universelle, zeitlose Denk-, Kausalitäts-, Kommunikations- und Verhaltensregeln, die **in absolut jedem Kontext** (egal ob Gemeindeberatung, Coding, Philosophie, Finanzen oder Intimität) verbindlich gelten müssen.
* **Kommt es nach UNTEN (`.agents/skills/<skill-name>/`):**
  * Handelt es sich um eine Anleitung für ein bestimmtes Werkzeug, eine API, ein Datenformat oder einen Ablauf (z. B. YouTube-Transkripte, Docx-Export, Mail-Handling, Fotosortierung)?  
  ➔ **S_&_G-Veto!** Gehört ausnahmslos als modularer Skill in ein eigenes Verzeichnis.
* **Kommt es ins GEDÄCHTNIS (`DYNAMIC_STATE.md` oder `LangMem`):**
  * Handelt es sich um ein konkretes Projekt-Faktum, eine situative Vorliebe oder eine temporäre Priorität?  
  ➔ **S_&_G-Veto!** Gehört in den operativen Status oder LangMem.

### Gate 2: Die Kausale Begründungspflicht (Chain of Rationale)
Jede Regel in `STYLE_AND_GUARDRAILS.md` MUSS zwingend das folgende Standard-Format erfüllen:

```markdown
* **[Prägnanter Name der Regel]:** [Eindeutige, operative Handlungsanweisung]. **Begründung:** [Kausale Kette: Warum ist diese Vorschrift notwendig und welches reale Risiko bzw. welcher Fehlermechanismus tritt bei Nichteinhaltung im Modellverhalten ein?].
```

> [!CAUTION]
> **Ablehnungskriterium:** Regeln ohne explizite Kausalbegründung oder mit Scheinerklärungen (*„weil es besser ist“*) werden vom Gatekeeper abgewiesen. Modelle halten Regeln nachweislich robuster ein, wenn der Fehlermechanismus transparent ist.

### Gate 3: Das Abstraktionsgebot (Anti-Overfitting)
* **Verbot von Situations-Phrasen:** Keine Nennung temporärer Werkzeuge, konkreter Gesprächspartner, akuter Vorfälle (*„wie beim letzten YouTube-Video“*) oder tagesaktueller Bugs.
* **Zeitlose Gültigkeit:** Die Regel muss so abstrahiert formuliert sein, dass sie in 5 Jahren mit völlig neuen Modellen und Frameworks uneingeschränkt Bestand hat.

### Gate 4: Token-Hygiene & Deterministischer Vollzug
1. **Redundanz-Check:** Prüfe vor dem Hinzufügen, ob eine bestehende Regel bereits denselben Sachverhalt abdeckt und lediglich geschärft werden muss (Verhinderung von Regel-Doppelungen).
2. **Längen-Audit:** `STYLE_AND_GUARDRAILS.md` ist Teil des Session-Startup-Budgets. Die Datei soll kompakt bleiben (Richtwert: unter 75 Zeilen).
3. **Strikter Schutz manueller Edits:** Das Überschreiben der Datei via `write_to_file` ist streng verboten. Modifikationen erfolgen **ausnahmslos punktuell via `replace_file_content`**.

---

## 📋 SOP für weitere Kerndokumente

### `00_MEMORY/DYNAMIC_STATE.md`
- **Zweck:** Living Operational State – der aktive Arbeitsfokus von maximal 1–3 Brennpunkten.
- **SOP:**
  - Kein Aufgabenfriedhof: Erledigte Aufgaben wandern ins Archiv/Transkript, nicht in eine endlose Liste.
  - Nur aktive, noch offene Schleifen (*Open Loops*) und nächste konkrete Schritte.
  - Stets mit Datumsstempel und Querverweisen auf Projektordner.

### `00_FRAMEWORK/architecture/01_CORE_PRINCIPLES_AND_SSOT.md`
- **Zweck:** Architektonische Grundgesetze von Groundsole.
- **SOP:**
  - Nummerierte Prinzipien (Prinzip 1 bis 17+).
  - Jedes Prinzip definiert Axiom, Kausalität und operative Konsequenz für Mensch und Agent.
  - Änderungen hier bedürfen immer des direkten Diskurses mit Emanuel.

---

## 🚫 Typische Anti-Patterns (Was sofort gestoppt wird)

| Anti-Pattern | Warum es schädlich ist | Korrekte Lösung |
| :--- | :--- | :--- |
| **Tool-Workflow in S_&_G** (*„Nutze yt-dlp für YouTube“*) | Bläht den Systemprompt für alle Nicht-YouTube-Prompts auf. | Eigener Skill: `.agents/skills/youtube-transcript/` |
| **Verbot ohne Kausalität** (*„Fasse dich kurz“*) | Modell ignoriert das Verbot unter Kontextsättigung. | Kausalität ergänzen (*„Begründung: Schützt das Token-Budget...“*) |
| **Vollständiges Überschreiben** (`write_to_file`) | Zerstört manuelle Anpassungen und Struktur des Nutzers. | Punktuelle Modifikation mit `replace_file_content` |
| **Projektstatus in S_&_G** (*„Kunden-Angebot B ist offen“*) | S_&_G verliert Allgemeingültigkeit; Veraltet sofort. | Nach `00_MEMORY/DYNAMIC_STATE.md` verschieben |
