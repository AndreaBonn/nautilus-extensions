# Estensioni Nautilus - Guida Completa

**Lingua:** **Italiano** | [English](README.md)

---

Raccolta di estensioni per Nautilus (il file manager di Ubuntu/GNOME) che aggiungono funzionalità avanzate di anteprima e gestione file direttamente dal menu contestuale.

<!-- Screenshot — decommenta quando le immagini sono disponibili
<p align="center">
  <img src="assets/screenshots/csv-preview.png" width="280" alt="CSV Preview">
  <img src="assets/screenshots/git-graph.png" width="280" alt="Git Graph">
  <img src="assets/screenshots/pdf-splitter.png" width="280" alt="PDF Splitter">
</p>
-->

## Indice

- [Cosa sono le estensioni Nautilus](#cosa-sono-le-estensioni-nautilus)
- [Estensioni disponibili](#estensioni-disponibili)
- [Installazione](#installazione)
- [Configurazione](#configurazione)
- [Utilizzo](#utilizzo)
- [Risoluzione problemi](#risoluzione-problemi)
- [Disinstallazione](#disinstallazione)

---

## Cosa sono le estensioni Nautilus

Le estensioni Nautilus sono script Python che aggiungono nuove voci al menu che appare quando fai clic destro su un file o cartella. Queste estensioni ti permettono di:

- Visualizzare anteprime avanzate di file dati (CSV, Excel, JSON, Parquet)
- Unire o dividere file PDF
- Analizzare Dockerfile
- Trovare file duplicati
- Visualizzare README direttamente da Nautilus
- Integrare Git direttamente in Nautilus (blame, diff, status, graph)

---

## Estensioni disponibili

### 1. **Anteprima CSV** (`csv-preview`)
Visualizza file CSV con:
- Tabella formattata delle prime 100 righe
- Statistiche descrittive (con pandas)
- Rilevamento automatico del delimitatore
- Informazioni su colonne numeriche e valori nulli

**Formati supportati:** `.csv`, `.tsv`

**[Leggi la guida completa](csv-preview/README_IT.md)**

### 2. **Anteprima Excel** (`excel-preview`)
Visualizza file Excel/LibreOffice con:
- Tutti i fogli del documento
- Dati tabulari con tipi di colonna
- Statistiche descrittive per colonne numeriche
- Metadati del documento (autore, data creazione)

**Formati supportati:** `.xlsx`, `.xlsm`, `.xltx`, `.xltm`, `.ods`

**[Leggi la guida completa](excel-preview/README_IT.md)**

### 3. **Anteprima JSON** (`json-preview`)
Visualizza file JSON e JSONL con:
- Struttura ad albero navigabile
- Schema inferito automaticamente
- Anteprima dati per array/JSONL
- Statistiche per file JSONL
- Supporto file compressi gzip

**Formati supportati:** `.json`, `.jsonl`, `.ndjson`, `.json.gz`, `.jsonl.gz`

**[Leggi la guida completa](json-preview/README_IT.md)**

### 4. **Anteprima Parquet** (`parquet-preview`)
Visualizza file Parquet con:
- Schema completo con tipi di dato
- Metadati e row groups
- Anteprima dati
- Statistiche descrittive
- Informazioni su compressione

**Formati supportati:** `.parquet`

**[Leggi la guida completa](parquet-preview/README_IT.md)**

### 5. **Unisci PDF** (`pdf-merger`)
Unisce più file PDF in uno solo:
- Selezione multipla di PDF
- Riordino tramite drag & drop
- Anteprima numero pagine
- Scelta nome file output

**Utilizzo:** Seleziona 2 o più PDF → clic destro → "Unisci PDF"

**[Leggi la guida completa](pdf-merger/README_IT.md)**

### 6. **Dividi PDF** (`pdf-splitter`)
Divide un PDF in più file con 4 modalità:
- **Intervalli personalizzati** (es. 1-3, 5-7, 9)
- **Ogni N pagine** (es. ogni 5 pagine)
- **Una pagina per file**
- **Per segnalibri/capitoli**

**Utilizzo:** Clic destro su PDF → "Dividi PDF"

**[Leggi la guida completa](pdf-splitter/README_IT.md)**

### 7. **Analizza Dockerfile** (`dockerfile-analyzer`)
Analizza Dockerfile con:
- Struttura e istruzioni
- Multi-stage builds
- Variabili d'ambiente e argomenti
- **Best practice e suggerimenti di sicurezza**
- Rilevamento problemi comuni

**Utilizzo:** Clic destro su Dockerfile → "Analizza Dockerfile"

**[Leggi la guida completa](dockerfile-analyzer/README_IT.md)**

### 8. **Trova Duplicati** (`duplicate-finder`)
Trova file duplicati in una cartella:
- Scansione ricorsiva con hash SHA-256
- Raggruppamento per contenuto identico
- Selezione intelligente (mantiene il primo)
- Spostamento nel cestino con un clic

**Utilizzo:** Clic destro su cartella → "Trova duplicati"

**[Leggi la guida completa](duplicate-finder/README_IT.md)**

### 9. **Visualizza README** (`readme-viewer`)
Mostra il README della cartella corrente:
- Rendering Markdown (se disponibile)
- Supporto README.md, README.txt, README.rst
- Apertura rapida nell'editor

**Utilizzo:** Clic destro sullo sfondo della cartella → "Mostra README.md"

**[Leggi la guida completa](readme-viewer/README_IT.md)**

### 10. **Git Blame** (`git-blame`)
Aggiunge colonne Git nella vista lista di Nautilus:
- Autore dell'ultimo commit per ogni file
- Data relativa del commit (es. "3 hours ago")
- Messaggio del commit (troncato a 55 caratteri)
- Cache dei risultati e caricamento asincrono

**Utilizzo:** Vista Lista (`Ctrl+2`) → clic destro intestazione colonne → spunta le colonne Git

**[Leggi la guida completa](git-blame/README_IT.md)**

### 11. **Git Diff** (`git-diff`)
Visualizza le modifiche di un file con diff visuale:
- Vista side-by-side con righe affiancate
- Vista unificata con toggle
- Colorazione verde/rosso per aggiunte/rimozioni
- Supporto diff staged e working tree

**Utilizzo:** Clic destro su file modificato → "⎇ Mostra Diff Git"

**[Leggi la guida completa](git-diff/README_IT.md)**

### 12. **Git Graph** (`git-graph`)
Visualizza il grafo dei commit Git:
- Grafo visuale con nodi e curve Bézier
- Palette colori per branch distinti
- Badge branch e marcatore HEAD dorato
- Legenda interattiva e barra di stato

**Utilizzo:** Clic destro sullo sfondo → "⎇ Mostra Git Graph…"

**[Leggi la guida completa](git-graph/README_IT.md)**

### 13. **Git Status** (`git-status`)
Pannello di stato Git con aggiornamento automatico:
- Branch corrente con indicatore ahead/behind
- File staged, modificati e untracked con icone colorate
- Ultimi 10 commit con hash, autore e data
- Conteggio stash e auto-refresh ogni 3 secondi

**Utilizzo:** Clic destro sullo sfondo → "⎇ Stato Git…"

**[Leggi la guida completa](git-status/README_IT.md)**

---

## Installazione

### Prerequisiti

Prima di installare le estensioni, assicurati di avere:

1. **Ubuntu/GNOME** (o altra distribuzione con Nautilus)
2. **Python 3** (già installato su Ubuntu)
3. **nautilus-python** (il bridge tra Nautilus e Python)

### Passo 1: Installa nautilus-python

Apri il terminale (premi `Ctrl+Alt+T`) e digita:

```bash
sudo apt update
sudo apt install python3-nautilus
```

### Passo 2: Crea la cartella delle estensioni

Se non esiste già, crea la cartella dove Nautilus cerca le estensioni:

```bash
mkdir -p ~/.local/share/nautilus-python/extensions
```

### Passo 3: Installa le dipendenze Python

Alcune estensioni richiedono librerie Python aggiuntive. Installa quelle che ti servono:

#### Per TUTTE le estensioni (consigliato):
```bash
sudo apt install python3-pandas python3-openpyxl python3-pypdf python3-markdown
pip install pyarrow --break-system-packages
```

#### Oppure solo per estensioni specifiche:

**CSV Preview:**
```bash
sudo apt install python3-pandas
```

**Excel Preview:**
```bash
sudo apt install python3-pandas python3-openpyxl
```

**JSON Preview:**
```bash
sudo apt install python3-pandas  # opzionale, per statistiche JSONL
```

**Parquet Preview:**
```bash
sudo apt install python3-pandas
pip install pyarrow --break-system-packages
```

**PDF Merger/Splitter:**
```bash
sudo apt install python3-pypdf
```

**README Viewer:**
```bash
sudo apt install python3-markdown gir1.2-webkit2-4.1  # opzionale, per rendering Markdown
```

**Dockerfile Analyzer e Duplicate Finder:**
Nessuna dipendenza aggiuntiva (usano solo librerie standard)

**Git Blame, Git Diff, Git Graph e Git Status:**
Nessuna dipendenza aggiuntiva (richiedono solo `git` installato nel sistema)

### Passo 4: Copia le estensioni

Copia i file `.py` delle estensioni che vuoi usare nella cartella creata:

```bash
# Esempio: installa tutte le estensioni
cp csv-preview/csv_preview.py ~/.local/share/nautilus-python/extensions/
cp excel-preview/excel_preview.py ~/.local/share/nautilus-python/extensions/
cp json-preview/json_preview.py ~/.local/share/nautilus-python/extensions/
cp parquet-preview/parquet_preview.py ~/.local/share/nautilus-python/extensions/
cp pdf-merger/pdf_merger.py ~/.local/share/nautilus-python/extensions/
cp pdf-splitter/pdf_splitter.py ~/.local/share/nautilus-python/extensions/
cp dockerfile-analyzer/dockerfile_analyzer.py ~/.local/share/nautilus-python/extensions/
cp duplicate-finder/duplicate-finder.py ~/.local/share/nautilus-python/extensions/
cp readme-viewer/readme_preview.py ~/.local/share/nautilus-python/extensions/
cp git-blame/git_blame.py ~/.local/share/nautilus-python/extensions/
cp git-diff/git_diff.py ~/.local/share/nautilus-python/extensions/
cp git-graph/git_graph.py ~/.local/share/nautilus-python/extensions/
cp git-status/git_status.py ~/.local/share/nautilus-python/extensions/
```

**Oppure installa solo quelle che ti servono**, ad esempio solo CSV e PDF:
```bash
cp csv-preview/csv_preview.py ~/.local/share/nautilus-python/extensions/
cp pdf-merger/pdf_merger.py ~/.local/share/nautilus-python/extensions/
```

### Passo 5: Riavvia Nautilus

Per attivare le estensioni, riavvia Nautilus:

```bash
nautilus -q
```

Poi riapri Nautilus normalmente (clicca sull'icona "File" nel dock o premi `Super+E`).

---

## Configurazione

### Verifica installazione

Per verificare che le estensioni siano state caricate correttamente:

1. Apri Nautilus
2. Vai in una cartella con file CSV, PDF, JSON, ecc.
3. Fai clic destro su un file supportato
4. Dovresti vedere le nuove voci nel menu (es. "Anteprima CSV", "Dividi PDF")

### Risolvi problemi di caricamento

Se le estensioni non appaiono:

1. **Controlla i log di Nautilus:**
   ```bash
   nautilus -q
   nautilus 2>&1 | grep -i python
   ```

2. **Verifica che nautilus-python sia installato:**
   ```bash
   dpkg -l | grep nautilus-python
   ```

3. **Controlla i permessi dei file:**
   ```bash
   ls -la ~/.local/share/nautilus-python/extensions/
   ```
   I file devono essere leggibili (permessi `644` o `755`)

4. **Rendi eseguibili i file (se necessario):**
   ```bash
   chmod +x ~/.local/share/nautilus-python/extensions/*.py
   ```

---

## Utilizzo

### Anteprima file dati (CSV, Excel, JSON, Parquet)

1. Naviga fino al file che vuoi visualizzare
2. **Clic destro** sul file
3. Seleziona **"Anteprima [tipo file]"** (es. "Anteprima CSV")
4. Si aprirà una finestra con:
   - Tab "Dati": tabella con i dati
   - Tab "Schema/Colonne": informazioni sulle colonne
   - Tab "Statistiche": statistiche descrittive (se disponibili)
   - Tab "Metadati": informazioni sul file

### Unire PDF

1. **Seleziona 2 o più file PDF** (tieni premuto `Ctrl` mentre clicchi)
2. **Clic destro** sulla selezione
3. Seleziona **"Unisci [N] PDF"**
4. Nella finestra che si apre:
   - Riordina i file trascinandoli o usando i pulsanti ⬆⬇
   - Rimuovi file indesiderati con il pulsante ✕
   - Modifica il nome del file output
   - Clicca **"Unisci PDF"**
5. Il file unito verrà salvato nella stessa cartella del primo PDF

### Dividere PDF

1. **Clic destro** su un file PDF
2. Seleziona **"Dividi PDF"**
3. Scegli una delle 4 modalità:
   - **Intervalli**: inserisci "1-3, 5, 7-9" per creare 3 file
   - **Ogni N pagine**: dividi ogni 5 pagine
   - **Una per file**: ogni pagina diventa un PDF
   - **Segnalibri**: un file per ogni capitolo
4. Scegli la cartella di output
5. Clicca **"Dividi PDF"**

### Analizzare Dockerfile

1. **Clic destro** su un file Dockerfile
2. Seleziona **"Analizza Dockerfile"**
3. Esplora i tab:
   - **Overview**: immagini base, porte, variabili
   - **Best Practice**: suggerimenti di sicurezza e ottimizzazione
   - **Istruzioni**: lista completa delle istruzioni
   - **Sorgente**: codice con syntax highlighting

### Trovare duplicati

1. **Clic destro** su una cartella
2. Seleziona **"Trova duplicati"**
3. Attendi la scansione (può richiedere tempo per cartelle grandi)
4. Nella finestra dei risultati:
   - I file sono raggruppati per contenuto identico
   - Il primo file di ogni gruppo NON è selezionato (verrà mantenuto)
   - Puoi modificare la selezione manualmente
   - Clicca **"Seleziona duplicati automaticamente"** per selezionare tutti tranne il primo
   - Clicca **"Sposta nel Cestino"** per eliminare i duplicati selezionati

### Visualizzare README

1. Apri una cartella che contiene un file README
2. **Clic destro sullo sfondo** (non su un file)
3. Seleziona **"Mostra README.md"** (o README.txt, ecc.)
4. Il README verrà visualizzato con rendering Markdown (se disponibile)

---

## Risoluzione problemi

### Le estensioni non appaiono nel menu

**Causa:** nautilus-python non è installato o Nautilus non è stato riavviato

**Soluzione:**
```bash
sudo apt install python3-nautilus
nautilus -q
```

### Errore "ModuleNotFoundError: No module named 'pandas'"

**Causa:** Manca la libreria pandas

**Soluzione:**
```bash
sudo apt install python3-pandas
```

### Errore "ModuleNotFoundError: No module named 'pypdf'"

**Causa:** Manca la libreria pypdf per gestire PDF

**Soluzione:**
```bash
sudo apt install python3-pypdf
```

### Errore "ModuleNotFoundError: No module named 'pyarrow'"

**Causa:** Manca pyarrow per file Parquet

**Soluzione:**
```bash
pip install pyarrow --break-system-packages
```

### L'anteprima CSV/Excel è lenta

**Causa:** File molto grande

**Soluzione:** Le estensioni caricano solo le prime 100 righe per velocità. Per file enormi, considera di usare strumenti dedicati come LibreOffice Calc o DBeaver.

### Il rendering Markdown non funziona

**Causa:** Manca WebKit o python3-markdown

**Soluzione:**
```bash
sudo apt install python3-markdown gir1.2-webkit2-4.1
```

### Nautilus si blocca o va in crash

**Causa:** Estensione con bug o file corrotto

**Soluzione:**
1. Rimuovi temporaneamente tutte le estensioni:
   ```bash
   mv ~/.local/share/nautilus-python/extensions ~/.local/share/nautilus-python/extensions.backup
   nautilus -q
   ```
2. Reinstalla le estensioni una alla volta per identificare quella problematica

---

## Disinstallazione

### Rimuovere una singola estensione

```bash
rm ~/.local/share/nautilus-python/extensions/[nome_estensione].py
nautilus -q
```

Esempio per rimuovere l'anteprima CSV:
```bash
rm ~/.local/share/nautilus-python/extensions/csv_preview.py
nautilus -q
```

### Rimuovere tutte le estensioni

```bash
rm ~/.local/share/nautilus-python/extensions/*.py
nautilus -q
```

### Disinstallare nautilus-python (rimuove TUTTE le estensioni Python)

```bash
sudo apt remove python3-nautilus
nautilus -q
```

---

## Suggerimenti

### Prestazioni

- Le estensioni di anteprima caricano solo una parte dei file (prime 100 righe) per velocità
- Per file molto grandi (>100MB), l'apertura potrebbe richiedere qualche secondo
- La ricerca duplicati può essere lenta su cartelle con migliaia di file

### Sicurezza

- L'analizzatore Dockerfile evidenzia problemi di sicurezza comuni
- Non mettere mai password o segreti in variabili ENV nei Dockerfile
- Usa sempre tag specifici per le immagini Docker (non `:latest`)

### Personalizzazione

Puoi modificare i file `.py` per personalizzare:
- Numero di righe visualizzate (cambia `PREVIEW_ROWS`)
- Dimensioni finestre (cambia `WINDOW_W` e `WINDOW_H`)
- Colori e stili CSS (modifica la variabile `CSS`)

---

## Note tecniche

- **Versione Nautilus:** Queste estensioni sono progettate per Nautilus 43+ (GNOME 43+) con GTK 4
- **Python:** Richiede Python 3.9 o superiore
- **Thread:** Le operazioni pesanti (lettura file, calcolo hash) vengono eseguite in thread separati per non bloccare l'interfaccia
- **Architettura a file singolo:** Ogni estensione è un file `.py` autonomo — questo è un [vincolo di Nautilus](https://wiki.gnome.org/Projects/NautilusPython), non una scelta di design. Nautilus carica le estensioni scansionando una singola directory alla ricerca di file `.py`, quindi ogni estensione deve contenere UI, logica di parsing e entry point in un unico modulo. Alcune funzioni utility (es. `fmt_size`) sono intenzionalmente duplicate tra le estensioni per questa ragione.

---

## Domande frequenti (FAQ)

**D: Posso usare queste estensioni su altre distribuzioni Linux?**  
R: Sì, funzionano su qualsiasi distribuzione con Nautilus e nautilus-python (Fedora, Debian, Arch, ecc.)

**D: Funzionano con altri file manager?**  
R: No, sono specifiche per Nautilus. Per altri file manager (Dolphin, Thunar, ecc.) servono estensioni diverse.

**D: Posso modificare il codice?**  
R: Sì, i file sono script Python leggibili e modificabili.

**D: Le estensioni rallentano Nautilus?**  
R: No, vengono caricate solo quando necessario e le operazioni pesanti sono in thread separati.

**D: Dove vengono salvati i file uniti/divisi?**  
R: Nella stessa cartella del file originale, o nella cartella che scegli nella finestra di dialogo.
