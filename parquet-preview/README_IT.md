# 📦 Anteprima Parquet - Estensione Nautilus

**Lingua:** **🇮🇹 Italiano** | [🇬🇧 English](README.md)

---

Estensione per Nautilus che aggiunge un'anteprima avanzata per file Apache Parquet direttamente dal menu contestuale.

## 🎯 Funzionalità

- **Schema completo** con tipi di dato PyArrow
- **Metadati dettagliati** (row groups, compressione, codec)
- **Anteprima dati** con le prime 100 righe
- **Statistiche descrittive** per colonne numeriche
- **Informazioni sui valori nulli**
- **Evidenziazione colonne per tipo** con colori diversi
- **Dettagli row groups** con dimensioni compresse/non compresse

## 📸 Cosa vedrai

Quando apri l'anteprima di un file Parquet, vedrai una finestra con 4 tab:

1. **📊 Dati**: Tabella con i dati, colonne colorate per tipo
2. **🗂 Schema**: Informazioni su ogni colonna + dettagli row groups
3. **📈 Statistiche**: Statistiche descrittive per colonne numeriche
4. **ℹ Metadati**: Informazioni sul file (versione, codec, dimensioni)

## 🚀 Installazione

### Passo 1: Installa nautilus-python

```bash
sudo apt update
sudo apt install python3-nautilus
```

### Passo 2: Installa le dipendenze

```bash
sudo apt install python3-pandas
pip install pyarrow --break-system-packages
```

**Nota:** Entrambe le dipendenze sono necessarie.

### Passo 3: Crea la cartella delle estensioni

```bash
mkdir -p ~/.local/share/nautilus-python/extensions
```

### Passo 4: Copia il file dell'estensione

```bash
cp parquet_preview.py ~/.local/share/nautilus-python/extensions/
```

### Passo 5: Riavvia Nautilus

```bash
nautilus -q
```

## 📖 Come usare

1. Apri Nautilus e naviga fino a un file `.parquet`
2. **Clic destro** sul file
3. Seleziona **"Anteprima Parquet"**
4. Si aprirà una finestra con l'anteprima del file

## 🔧 Configurazione

Puoi personalizzare modificando le costanti in `parquet_preview.py`:

```python
PREVIEW_ROWS = 100        # Numero di righe da mostrare
MIN_COL_WIDTH = 80        # Larghezza minima colonna
MAX_COL_WIDTH = 300       # Larghezza massima colonna
WINDOW_W = 1100           # Larghezza finestra
WINDOW_H = 680            # Altezza finestra
```

## 🗑️ Disinstallazione

```bash
rm ~/.local/share/nautilus-python/extensions/parquet_preview.py
nautilus -q
```

---

**Torna al [README principale](../README_IT.md)**
