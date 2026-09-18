# Groundsole Master Bootstrap

> **ANWEISUNG FÜR DEN KI-ASSISTENTEN (Antigravity, Hermes, Claude, Codex etc.):**  
> Wenn der Nutzer den Befehl gibt:  
> **„Lies bootstrap.md und richte mein System ein“** (oder diese Datei / URL übergibt),  
> führe die folgende Einrichtung Schritt für Schritt autonom aus.  
> **WICHTIGE REGEL FÜR DIE SPRACHE:**  
> Sprich mit dem Nutzer in einer **einfachen, warmen, verständlichen Alltagssprache**.  
> Verwende **keinerlei Entwickler-Jargon** (keine Begriffe wie *„FastEmbed“*, *„ONNX Runtime“*, *„Scaffolding“*, *„Sharding“* oder *„relationale Knotendatenbank“*).  
> Erkläre alle Schritte so, dass sie auch ein Schüler (wie Alex) oder ein Nicht-Techniker sofort versteht.

---

## Schritt 1: Begrüßung & Profil-Auswahl

Begrüße den Nutzer freundlich und frage ihn kurz, wofür er sein neues Cockpit nutzen möchte:

> *„Hallo! Ich bin dein neuer persönlicher KI-Koprozessor. Schön, dass wir zusammenarbeiten!  
> Damit ich perfekt zu deinem Alltag passe: Wofür möchtest du diesen Bereich hauptsächlich nutzen?  
>  
> 🎒 **1. Schule & Lernen (Empfohlen für Schüler & Studenten):**  
> Fächer, Hausaufgaben, Prüfungsvorbereitung, Zusammenfassungen und Lern-Sparring.  
>  
> 💼 **2. Beruf & Projekte:**  
> Projekte, Aufgaben, Arbeitsdokumente, Kunden und Finanzen.  
>  
> 🧠 **3. Persönlicher Wissensraum:**  
> Notizen, Gedanken, Ideen und private Organisation.  
>  
> ✨ **4. Entscheide du für mich:**  
> Ich richte dir automatisch die optimale Basis ein.“*

---

## Schritt 2: Sichere Umgebung einrichten (Außerhalb der Cloud)

> [!CRITICAL]
> **Cloud-Schutz (iCloud / OneDrive / Google Drive / Dropbox):**  
> Installiere Python-Pakete und virtuelle Umgebungen **niemals** in Cloud-synchronisierten Ordnern!

Führe abhängig vom Betriebssystem folgende Befehle im Hintergrund aus:

### Auf macOS / Linux (Terminal / Bash):
```bash
# 1. Virtuelle Umgebung außerhalb der Cloud anlegen
VENV_DIR="$HOME/.local/venv"
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi

# 2. Werkzeuge für Gedächtnis, Word und PDF installieren
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install fastembed numpy python-docx
```

### Auf Windows (PowerShell):
```powershell
# 1. Virtuelle Umgebung außerhalb von OneDrive anlegen
$VenvDir = Join-Path $env:USERPROFILE ".local\venv"
if (-not (Test-Path $VenvDir)) {
    New-Item -ItemType Directory -Path (Split-Path $VenvDir) -Force | Out-Null
    py -3 -m venv $VenvDir
}

# 2. Werkzeuge für Gedächtnis, Word und PDF installieren
$PipExe = Join-Path $VenvDir "Scripts\pip.exe"
& $PipExe install --upgrade pip
& $PipExe install fastembed numpy python-docx
```

---

## Schritt 3: Arbeitsbereich und Werkzeuge aufbauen

Lade die Vorlagen herunter und richte das gewählte Profil ein:

### Auf macOS / Linux (Bash):
```bash
git clone --depth 1 https://github.com/gentlemani85/groundsole.git .temp_groundsole
"$HOME/.local/venv/bin/python3" .temp_groundsole/tools/init_instance.py --target . --profile <school|organization|personal> --user "<Nutzername>"
rm -rf .temp_groundsole
```

### Auf Windows (PowerShell):
```powershell
git clone --depth 1 https://github.com/gentlemani85/groundsole.git .temp_groundsole
& "$env:USERPROFILE\.local\venv\Scripts\python.exe" .temp_groundsole\tools\init_instance.py --target . --profile <school|organization|personal> --user "<Nutzername>"
Remove-Item -Recurse -Force .temp_groundsole
```

*(Hinweis: Falls Git nicht installiert ist, lade das ZIP-Archiv von `https://github.com/gentlemani85/groundsole/archive/refs/heads/main.zip` herunter und entpacke es kurz).*

---

## Schritt 4: Was damit bereitsteht

Nach diesem Schritt verfügt der Nutzer über:
1. **Dauerhaftes Gedächtnis:** Kann sich an frühere Gespräche, Notizen und Vereinbarungen erinnern (`memory.py`, `memory_retriever.py`).
2. **Dokumenten-Export:** Erstellt auf Zuruf saubere **Word-Dokumente (`.docx`)** und druckreife **PDF-Dateien (`.pdf`)** (`document_exporter.py`).
3. **E-Mail-Verbindung:** Kann bei Bedarf mit Gmail oder dem eigenen Postfach verbunden werden (`mail_helper.py`).
4. **Schulfach- / Projekt-Cockpit:** Übersicht über Fächer, Aufgaben und Ziele (`00_MEMORY/modules/`).

---

## Schritt 5: Freundliche Begrüßung & Start

Bestätige die erfolgreiche Einrichtung in herzlicher, einfacher Sprache:

> *„🎉 Dein persönliches Cockpit ist fertig eingerichtet und einsatzbereit!  
>  
> **Was wir ab sofort tun können:**  
> • **Lernen & Üben:** Frag mich einfach nach Erklärungen zu deinen Schulfächern oder Themen.  
> • **Dokumente erstellen:** Sag mir einfach: *„Erstelle mir ein PDF aus...“* oder *„Mache daraus ein Word-Dokument“*.  
> • **Erinnern:** Ich merke mir wichtige Fakten und Vereinbarungen automatisch.  
>  
> Womit möchtest du starten?“*
