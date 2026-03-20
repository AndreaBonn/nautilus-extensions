# ⎇ Git Graph - Estensione Nautilus

**Lingua:** **🇮🇹 Italiano** | [🇬🇧 English](README_EN.md)

---

Estensione per Nautilus che visualizza il grafo dei commit Git con branch, merge e legenda colorata in una finestra grafica interattiva.

## 🎯 Funzionalità

- **Grafo visuale dei commit** disegnato con Cairo su DrawingArea GTK 4
- **Palette colori per branch** — ogni branch ha un colore distinto dalla palette
- **Marcatore HEAD** con anello dorato sul commit corrente
- **Badge branch** con sfondo colorato accanto ai commit con ref
- **Legenda interattiva** nella parte superiore con tutti i branch
- **Curve Bézier** per connessioni tra commit di branch diversi
- **Fino a 60 commit** visualizzati con hash, autore, data e messaggio
- **Barra di stato** con conteggio commit e branch
- **Caricamento asincrono** con spinner durante il caricamento

## 🚀 Installazione

### Passo 1: Installa nautilus-python

```bash
sudo apt update
sudo apt install python3-nautilus
```

### Passo 2: Crea la cartella delle estensioni

```bash
mkdir -p ~/.local/share/nautilus-python/extensions
```

### Passo 3: Copia il file dell'estensione

```bash
cp git_graph.py ~/.local/share/nautilus-python/extensions/
```

### Passo 4: Riavvia Nautilus

```bash
nautilus -q
```

**Nota:** Questa estensione non richiede dipendenze aggiuntive (solo `git` installato nel sistema).

## 📖 Come usare

1. Apri Nautilus e naviga in una cartella all'interno di un repository Git
2. **Clic destro** sullo sfondo della cartella
3. Seleziona **"⎇ Mostra Git Graph…"**
4. Nella finestra vedrai:
   - **Legenda** in alto con i branch e i rispettivi colori
   - **Grafo** con nodi commit collegati da linee/curve
   - **Badge** colorati per branch associati ai commit
   - **Hash + messaggio** per ogni commit
   - **Autore e data** allineati a destra
   - **Barra di stato** con il conteggio totale di commit e branch

Puoi anche fare clic destro su una **cartella** per aprire il grafo del repository contenuto.

## 🔧 Configurazione

Puoi personalizzare l'estensione modificando le costanti nel file `git_graph.py`:

```python
BRANCH_COLORS = [...]    # Palette colori per i branch
HEAD_COLOR = "#FFD700"    # Colore del marcatore HEAD
MERGE_COLOR = "#FF6B9D"   # Colore per merge commits
max_commits = 60           # Numero massimo di commit visualizzati
```

Nella classe `GitGraphWidget`:
```python
ROW_H = 52     # Altezza di ogni riga commit
COL_W = 22     # Larghezza colonna per branch paralleli
NODE_R = 7     # Raggio del nodo commit
LEFT_PAD = 16  # Padding sinistro
```

## 🔍 Dettagli tecnici

- **Versione Nautilus:** 43+ (GNOME 43+) con GTK 4
- **API:** `MenuProvider`
- **Rendering:** Cairo drawing su `Gtk.DrawingArea` con `set_draw_func`
- **Thread:** Il caricamento dei dati git avviene in un thread separato per non bloccare l'interfaccia
- **Layout:** Euristica di assegnazione colonne basata su branch attivi per evitare sovrapposizioni

## 🗑️ Disinstallazione

```bash
rm ~/.local/share/nautilus-python/extensions/git_graph.py
nautilus -q
```

---

**Torna al [README principale](../README.md)**
