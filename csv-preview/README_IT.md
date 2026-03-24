# 📊 Anteprima CSV - Estensione Nautilus

**Lingua:** **🇮🇹 Italiano** | [🇬🇧 English](README.md)

---

Estensione per Nautilus che aggiunge un'anteprima avanzata per file CSV e TSV direttamente dal menu contestuale.

## 🎯 Funzionalità

- **Tabella formattata** con le prime 100 righe del file
- **Rilevamento automatico del delimitatore** (virgola, punto e virgola, tab)
- **Statistiche descrittive** per colonne numeriche (media, mediana, min, max, ecc.)
- **Evidenziazione colonne numeriche** con colore blu
- **Informazioni sui valori nulli** per ogni colonna
- **Ordinamento colonne** cliccando sull'intestazione
- **Supporto file grandi** con caricamento ottimizzato

## 📸 Cosa vedrai

Quando apri l'anteprima di un file CSV, vedrai una finestra con 3 tab:

1. **📊 Dati**: Tabella con i dati, colonne ridimensionabili e ordinabili
2. **📈 Statistiche**: Statistiche descrittive per colonne numeriche (solo con pandas)
3. **🗂 Colonne**: Informazioni su ogni colonna (nome, tipo, valori nulli)

Nella barra superiore troverai:
- Numero totale di righe e colonne
- Delimitatore rilevato
- Dimensione del file
- Avviso se il file è stato troncato (mostra solo prime 100 righe)

## 🚀 Installazione

### Passo 1: Installa nautilus-python

```bash
sudo apt update
sudo apt install python3-nautilus
```

### Passo 2: Installa le dipendenze (opzionali ma consigliate)

Per avere le statistiche descrittive:
```bash
sudo apt install python3-pandas
```

**Nota:** L'estensione funziona anche senza pandas, ma non mostrerà le statistiche.

### Passo 3: Crea la cartella delle estensioni

```bash
mkdir -p ~/.local/share/nautilus-python/extensions
```

### Passo 4: Copia il file dell'estensione

```bash
cp csv_preview.py ~/.local/share/nautilus-python/extensions/
```

### Passo 5: Riavvia Nautilus

```bash
nautilus -q
```

Riapri Nautilus normalmente.

## 📖 Come usare

1. Apri Nautilus e naviga fino a un file CSV o TSV
2. **Clic destro** sul file
3. Seleziona **"Anteprima CSV"**
4. Si aprirà una finestra con l'anteprima del file

### Funzionalità della finestra

- **Ridimensiona colonne**: Trascina il bordo dell'intestazione
- **Ordina dati**: Clicca sull'intestazione di una colonna
- **Naviga tra i tab**: Clicca su "Dati", "Statistiche" o "Colonne"
- **Apri nell'editor**: Clicca il pulsante "Apri con editor" in basso

## 🔧 Configurazione

Puoi personalizzare l'estensione modificando le costanti nel file `csv_preview.py`:

```python
PREVIEW_ROWS = 100        # Numero di righe da mostrare
MAX_COL_WIDTH = 300       # Larghezza massima colonna in pixel
MIN_COL_WIDTH = 60        # Larghezza minima colonna in pixel
WINDOW_W = 1100           # Larghezza finestra
WINDOW_H = 650            # Altezza finestra
```

## 📋 Formati supportati

- `.csv` - Comma Separated Values
- `.tsv` - Tab Separated Values

L'estensione rileva automaticamente il delimitatore analizzando il contenuto del file.

## 🐛 Risoluzione problemi

### L'estensione non appare nel menu

**Soluzione:**
```bash
# Verifica che nautilus-python sia installato
dpkg -l | grep nautilus-python

# Riavvia Nautilus
nautilus -q
```

### Errore "ModuleNotFoundError: No module named 'pandas'"

**Soluzione:**
```bash
sudo apt install python3-pandas
```

**Nota:** Questo errore non impedisce l'uso dell'estensione, ma disabilita le statistiche.

### Il file CSV non viene visualizzato correttamente

**Possibili cause:**
- Delimitatore non standard (l'estensione prova a rilevarlo automaticamente)
- Encoding del file non UTF-8
- File corrotto

**Soluzione:** Prova ad aprire il file con un editor di testo per verificare il formato.

### L'anteprima è lenta

**Causa:** File molto grande (>100MB)

**Soluzione:** L'estensione carica solo le prime 100 righe per velocità. Per file enormi, considera di usare strumenti dedicati come LibreOffice Calc.

## 💡 Suggerimenti

### Prestazioni

- L'estensione carica solo le prime 100 righe per velocità
- Il rilevamento del delimitatore analizza solo i primi 4KB del file
- Con pandas, le statistiche vengono calcolate sull'intero file (può richiedere tempo per file grandi)

### Colonne numeriche

Le colonne numeriche sono evidenziate in blu e allineate a destra per facilitare la lettura.

### Valori nulli

Nella tab "Statistiche" puoi vedere quanti valori nulli (mancanti) ci sono in ogni colonna.

## 🔍 Dettagli tecnici

- **Versione Nautilus:** 43+ (GNOME 43+) con GTK 4
- **Python:** 3.8 o superiore
- **Dipendenze opzionali:** pandas (per statistiche)
- **Thread:** Il caricamento del file avviene in un thread separato per non bloccare l'interfaccia

## 📝 Esempio di utilizzo

Supponiamo di avere un file `vendite.csv`:

```csv
data,prodotto,quantita,prezzo
2024-01-01,Laptop,5,899.99
2024-01-02,Mouse,15,29.99
2024-01-03,Tastiera,8,79.99
```

Facendo clic destro e selezionando "Anteprima CSV", vedrai:

**Tab Dati:**
- Tabella con 3 righe e 4 colonne
- Colonne "quantita" e "prezzo" evidenziate in blu

**Tab Statistiche:**
- Media, mediana, min, max per "quantita" e "prezzo"
- Nessun valore nullo

**Tab Colonne:**
- data: string
- prodotto: string
- quantita: numerico (int64)
- prezzo: numerico (float64)

## 🗑️ Disinstallazione

```bash
rm ~/.local/share/nautilus-python/extensions/csv_preview.py
nautilus -q
```

---

**Torna al [README principale](../README_IT.md)**
