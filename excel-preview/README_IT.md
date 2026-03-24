# 📗 Anteprima Excel - Estensione Nautilus

**Lingua:** **🇮🇹 Italiano** | [🇬🇧 English](README.md)

---

Estensione per Nautilus che aggiunge un'anteprima avanzata per file Excel e LibreOffice Calc direttamente dal menu contestuale.

## 🎯 Funzionalità

- **Visualizzazione di tutti i fogli** del documento
- **Tabella formattata** con le prime 100 righe per foglio
- **Statistiche descrittive** per colonne numeriche
- **Metadati del documento** (autore, data creazione/modifica)
- **Informazioni sui valori nulli** per ogni colonna
- **Evidenziazione colonne numeriche** con colore blu
- **Supporto multi-stage** per documenti con molti fogli

## 📸 Cosa vedrai

Quando apri l'anteprima di un file Excel, vedrai una finestra con:

**Barra superiore:**
- Numero di fogli
- Righe totali (somma di tutti i fogli)
- Dimensione file
- Autore e data ultima modifica

**Per ogni foglio, 3 tab:**
1. **📊 Dati**: Tabella con i dati, intestazioni con tipo di colonna
2. **📈 Statistiche**: Statistiche descrittive per colonne numeriche
3. **🗂 Colonne**: Informazioni dettagliate su ogni colonna

## 🚀 Installazione

### Passo 1: Installa nautilus-python

```bash
sudo apt update
sudo apt install python3-nautilus
```

### Passo 2: Installa le dipendenze

```bash
sudo apt install python3-pandas python3-openpyxl
```

**Nota:** Entrambe le dipendenze sono necessarie per questa estensione.

### Passo 3: Crea la cartella delle estensioni

```bash
mkdir -p ~/.local/share/nautilus-python/extensions
```

### Passo 4: Copia il file dell'estensione

```bash
cp excel_preview.py ~/.local/share/nautilus-python/extensions/
```

### Passo 5: Riavvia Nautilus

```bash
nautilus -q
```

Riapri Nautilus normalmente.

## 📖 Come usare

1. Apri Nautilus e naviga fino a un file Excel o ODS
2. **Clic destro** sul file
3. Seleziona **"Anteprima Excel"**
4. Si aprirà una finestra con l'anteprima del file

### Navigazione multi-foglio

- Se il file ha **un solo foglio**, vedrai direttamente i tab Dati/Statistiche/Colonne
- Se il file ha **più fogli**, vedrai prima i tab dei fogli (sulla sinistra), poi i tab interni per ogni foglio

### Funzionalità della finestra

- **Cambia foglio**: Clicca sui tab laterali (se ci sono più fogli)
- **Ridimensiona colonne**: Trascina il bordo dell'intestazione
- **Ordina dati**: Clicca sull'intestazione di una colonna
- **Apri con LibreOffice**: Clicca il pulsante in basso

## 🔧 Configurazione

Puoi personalizzare l'estensione modificando le costanti nel file `excel_preview.py`:

```python
PREVIEW_ROWS = 100        # Numero di righe da mostrare per foglio
MIN_COL_WIDTH = 80        # Larghezza minima colonna in pixel
MAX_COL_WIDTH = 300       # Larghezza massima colonna in pixel
WINDOW_W = 1150           # Larghezza finestra
WINDOW_H = 700            # Altezza finestra
```

## 📋 Formati supportati

- `.xlsx` - Excel 2007+ (Office Open XML)
- `.xlsm` - Excel con macro
- `.xltx` - Template Excel
- `.xltm` - Template Excel con macro
- `.ods` - OpenDocument Spreadsheet (LibreOffice/OpenOffice)

## 🐛 Risoluzione problemi

### L'estensione non appare nel menu

**Soluzione:**
```bash
# Verifica che nautilus-python sia installato
dpkg -l | grep nautilus-python

# Riavvia Nautilus
nautilus -q
```

### Errore "ModuleNotFoundError: No module named 'openpyxl'"

**Soluzione:**
```bash
sudo apt install python3-openpyxl
```

### Errore "ModuleNotFoundError: No module named 'pandas'"

**Soluzione:**
```bash
sudo apt install python3-pandas
```

### Il file Excel non viene visualizzato correttamente

**Possibili cause:**
- File corrotto
- Formato non supportato (es. vecchi file .xls di Excel 97-2003)
- File protetto da password

**Soluzione per file .xls vecchi:**
Apri il file con LibreOffice e salvalo come `.xlsx`

### L'anteprima è lenta

**Causa:** File con molti fogli o molte righe

**Soluzione:** L'estensione carica solo le prime 100 righe per foglio. Per file enormi, usa LibreOffice Calc.

### Errore "File protetto da password"

**Soluzione:** L'estensione non supporta file protetti. Rimuovi la protezione con LibreOffice.

## 💡 Suggerimenti

### Prestazioni

- L'estensione carica tutti i fogli ma solo le prime 100 righe per foglio
- Il conteggio delle righe totali è veloce (usa metadati del file)
- Le statistiche vengono calcolate sull'intero foglio (può richiedere tempo per fogli grandi)

### Metadati

Nella barra superiore puoi vedere:
- **Autore**: Chi ha creato il file
- **Creato**: Data di creazione
- **Modificato**: Data ultima modifica
- **Fogli**: Numero di fogli nel documento

### Colonne numeriche

Le colonne numeriche sono evidenziate in blu e mostrano:
- Tipo di dato (int64, float64, ecc.)
- Statistiche descrittive (media, mediana, min, max, ecc.)
- Valori nulli

## 🔍 Dettagli tecnici

- **Versione Nautilus:** 43+ (GNOME 43+) con GTK 4
- **Python:** 3.8 o superiore
- **Dipendenze:** pandas, openpyxl
- **Thread:** Il caricamento del file avviene in un thread separato per non bloccare l'interfaccia
- **Ottimizzazione:** Tutti i fogli vengono letti in una sola chiamata pandas per velocità

## 📝 Esempio di utilizzo

Supponiamo di avere un file `budget.xlsx` con 2 fogli:

**Foglio "Entrate":**
```
mese,importo,categoria
Gennaio,5000,Vendite
Febbraio,5500,Vendite
```

**Foglio "Uscite":**
```
mese,importo,categoria
Gennaio,3000,Stipendi
Febbraio,3200,Stipendi
```

Facendo clic destro e selezionando "Anteprima Excel", vedrai:

**Barra superiore:**
- 2 fogli, 4 righe totali, dimensione file

**Tab laterali:**
- Entrate
- Uscite

**Per ogni foglio:**
- Tab Dati: tabella con colonna "importo" in blu
- Tab Statistiche: media, min, max per "importo"
- Tab Colonne: mese (string), importo (int64), categoria (string)

## 🗑️ Disinstallazione

```bash
rm ~/.local/share/nautilus-python/extensions/excel_preview.py
nautilus -q
```

## 🤝 Contributi

Hai trovato un bug o vuoi migliorare l'estensione? Sentiti libero di modificare il codice!

---

**Torna al [README principale](../README_IT.md)**
