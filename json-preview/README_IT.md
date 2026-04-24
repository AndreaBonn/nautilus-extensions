# Anteprima JSON - Estensione Nautilus

**Lingua:** **Italiano** | [English](README.md)

---

Estensione per Nautilus che aggiunge un'anteprima avanzata per file JSON e JSONL direttamente dal menu contestuale.

## Funzionalità

- **Struttura ad albero navigabile** per esplorare JSON complessi
- **Schema inferito automaticamente** con tipi di dato
- **Supporto JSONL** (JSON Lines) con statistiche
- **Anteprima dati** per array e file JSONL
- **Statistiche descrittive** per colonne numeriche (con pandas)
- **Supporto file compressi** (.json.gz, .jsonl.gz)
- **Visualizzazione raw** con formattazione

## Cosa vedrai

Quando apri l'anteprima di un file JSON, vedrai una finestra con:

**Barra superiore:**
- Formato (JSON o JSONL)
- Dimensione file
- Tipo radice (object, array, ecc.)
- Numero di elementi/righe

**Tab disponibili:**
1. **Struttura**: Albero navigabile con chiavi, tipi e valori
2. **Schema**: Schema inferito con tipi di dato e presenza campi
3. **Dati**: Tabella con i dati (per array/JSONL)
4. **Statistiche**: Statistiche descrittive (solo con pandas e colonne numeriche)
5. **{ } Raw**: Sorgente JSON formattato

## Installazione

### Passo 1: Installa nautilus-python

```bash
sudo apt update
sudo apt install python3-nautilus
```

### Passo 2: Installa le dipendenze (opzionali)

Per avere le statistiche su file JSONL:
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
cp json_preview.py ~/.local/share/nautilus-python/extensions/
```

### Passo 5: Riavvia Nautilus

```bash
nautilus -q
```

Riapri Nautilus normalmente.

## Come usare

1. Apri Nautilus e naviga fino a un file JSON o JSONL
2. **Clic destro** sul file
3. Seleziona **"Anteprima JSON"** o **"Anteprima JSONL"**
4. Si aprirà una finestra con l'anteprima del file

### Navigazione struttura ad albero

- **Espandi/Comprimi**: Clicca sulla freccia accanto a oggetti e array
- **Colori**: Ogni tipo di dato ha un colore diverso
  - Verde: stringhe
  - Blu: numeri
  - Arancione: booleani
  - Rosso: null
  - Viola: oggetti e array

### File JSONL

Per file JSONL (una riga = un oggetto JSON):
- La tab "Schema" mostra i campi comuni a tutti gli oggetti
- I campi opzionali sono marcati come tali
- La tab "Dati" mostra una tabella con le prime 100 righe

## Configurazione

Puoi personalizzare l'estensione modificando le costanti nel file `json_preview.py`:

```python
PREVIEW_ROWS = 100        # Numero di righe da mostrare (JSONL)
MAX_READ_BYTES = 50 * 1024 * 1024  # 50MB - limite lettura file
MAX_TREE_DEPTH = 8        # Profondità massima albero
WINDOW_W = 1100           # Larghezza finestra
WINDOW_H = 700            # Altezza finestra
```

## Formati supportati

- `.json` - JSON standard
- `.jsonl` - JSON Lines (una riga = un oggetto)
- `.ndjson` - Newline Delimited JSON (alias di JSONL)
- `.json.gz` - JSON compresso con gzip
- `.jsonl.gz` - JSONL compresso con gzip

L'estensione rileva automaticamente se il file è compresso analizzando i magic bytes.

## Risoluzione problemi

### L'estensione non appare nel menu

**Soluzione:**
```bash
# Verifica che nautilus-python sia installato
dpkg -l | grep nautilus-python

# Riavvia Nautilus
nautilus -q
```

### Errore "JSON non valido"

**Possibili cause:**
- File JSON malformato
- Encoding non UTF-8
- File corrotto

**Soluzione:** Verifica il file con un validatore JSON online o con:
```bash
python3 -m json.tool file.json
```

### Il file è troncato a 50MB

**Causa:** Limite di sicurezza per evitare di caricare file enormi in memoria

**Soluzione:** Modifica `MAX_READ_BYTES` nel file `json_preview.py` oppure usa strumenti da riga di comando come `jq`.

### L'albero è troppo profondo

**Causa:** JSON con struttura molto annidata

**Soluzione:** L'estensione limita la profondità a 8 livelli. Modifica `MAX_TREE_DEPTH` se necessario.

## Suggerimenti

### Prestazioni

- File JSON grandi (>50MB) vengono troncati
- File JSONL: vengono lette solo le prime 100 righe per l'anteprima
- Lo schema viene inferito dai primi 200 oggetti (per JSONL)
- File compressi (.gz) vengono decompressi automaticamente

### Schema JSONL

Per file JSONL, lo schema mostra:
- **Tipo**: tipo di dato più frequente per ogni campo
- **Presenza**: quanti oggetti contengono quel campo
- **Opzionale**: se il campo non è presente in tutti gli oggetti

### Valori nulli

Nella tab "Statistiche" (solo con pandas) puoi vedere quanti valori nulli ci sono in ogni campo.

## Dettagli tecnici

- **Versione Nautilus:** 43+ (GNOME 43+) con GTK 4
- **Python:** 3.8 o superiore
- **Dipendenze opzionali:** pandas (per statistiche JSONL)
- **Thread:** Il caricamento del file avviene in un thread separato
- **Compressione:** Supporto gzip trasparente

## Esempio di utilizzo

### JSON standard

File `config.json`:
```json
{
  "app": "MyApp",
  "version": "1.0.0",
  "settings": {
    "debug": true,
    "port": 8080
  }
}
```

**Tab Struttura:**
```
app (string): MyApp
version (string): 1.0.0
settings (object): { 3 chiavi }
  ├─ debug (boolean): true
  └─ port (number): 8080
```

### JSONL

File `events.jsonl`:
```json
{"timestamp": "2024-01-01", "user": "alice", "action": "login"}
{"timestamp": "2024-01-01", "user": "bob", "action": "logout"}
{"timestamp": "2024-01-02", "user": "alice", "action": "purchase", "amount": 99.99}
```

**Tab Schema:**
- timestamp: string (3/3, sempre presente)
- user: string (3/3, sempre presente)
- action: string (3/3, sempre presente)
- amount: number (1/3, opzionale)

**Tab Dati:**
Tabella con 3 righe e 4 colonne, colonna "amount" in blu.

## Disinstallazione

```bash
rm ~/.local/share/nautilus-python/extensions/json_preview.py
nautilus -q
```

---

**Torna al [README principale](../README_IT.md)**
