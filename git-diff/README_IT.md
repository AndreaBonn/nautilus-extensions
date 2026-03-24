# ⎇ Git Diff - Estensione Nautilus

**Lingua:** **🇮🇹 Italiano** | [🇬🇧 English](README.md)

---

Estensione per Nautilus che aggiunge una vista diff visuale side-by-side dal menu contestuale per file in repository Git.

## 🎯 Funzionalità

- **Diff side-by-side** con righe affiancate vecchio/nuovo
- **Diff unificato** con toggle per passare tra le due viste
- **Colorazione sintassi** — verde per aggiunte, rosso per rimozioni
- **Numeri di riga** per entrambi i lati
- **Supporto diff staged e working tree** — mostra prima le modifiche non staged, poi quelle staged
- **Caricamento asincrono** con spinner durante il caricamento
- **Disponibile su file e cartelle** dal menu contestuale e dallo sfondo

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
cp git_diff.py ~/.local/share/nautilus-python/extensions/
```

### Passo 4: Riavvia Nautilus

```bash
nautilus -q
```

**Nota:** Questa estensione non richiede dipendenze aggiuntive (solo `git` installato nel sistema).

## 📖 Come usare

1. Apri Nautilus e naviga in un repository Git
2. **Clic destro** su un file modificato
3. Seleziona **"⎇ Mostra Diff Git"**
4. Nella finestra:
   - Usa il toggle **"Side-by-side"** / **"Unificato"** per cambiare vista
   - Scorri per navigare tra gli hunk di modifiche

Puoi anche fare clic destro sullo **sfondo** di una cartella per visualizzare il diff della cartella stessa.

## 🔍 Dettagli tecnici

- **Versione Nautilus:** 43+ (GNOME 43+) con GTK 4
- **API:** `MenuProvider`
- **Thread:** Il caricamento del diff avviene in un thread separato per non bloccare l'interfaccia
- **Parser diff:** Parsing custom dell'output di `git diff` in hunk con supporto per righe aggiunte, rimosse e di contesto

## 🗑️ Disinstallazione

```bash
rm ~/.local/share/nautilus-python/extensions/git_diff.py
nautilus -q
```

---

**Torna al [README principale](../README_IT.md)**
