# ✂️ Dividi PDF - Estensione Nautilus

**Lingua:** **🇮🇹 Italiano** | [🇬🇧 English](README.md)

---

Estensione per Nautilus che permette di dividere un file PDF in più file con 4 modalità diverse.

## 🎯 Funzionalità

- **4 modalità di divisione:**
  1. Intervalli personalizzati (es. 1-3, 5-7, 9)
  2. Ogni N pagine
  3. Una pagina per file
  4. Per segnalibri/capitoli
- **Anteprima file** che verranno creati
- **Scelta cartella output**
- **Progress bar** durante la divisione

## 🚀 Installazione

### Passo 1: Installa nautilus-python

```bash
sudo apt update
sudo apt install python3-nautilus
```

### Passo 2: Installa le dipendenze

```bash
sudo apt install python3-pypdf
```

### Passo 3: Crea la cartella delle estensioni

```bash
mkdir -p ~/.local/share/nautilus-python/extensions
```

### Passo 4: Copia il file dell'estensione

```bash
cp pdf_splitter.py ~/.local/share/nautilus-python/extensions/
```

### Passo 5: Riavvia Nautilus

```bash
nautilus -q
```

## 📖 Come usare

1. **Clic destro** su un file PDF
2. Seleziona **"Dividi PDF"**
3. Scegli una modalità:
   - **Intervalli**: inserisci "1-3, 5, 7-9"
   - **Ogni N pagine**: scegli il numero
   - **Una per file**: automatico
   - **Segnalibri**: automatico (se presenti)
4. Scegli la cartella output
5. Clicca **"✂ Dividi PDF"**

## 🗑️ Disinstallazione

```bash
rm ~/.local/share/nautilus-python/extensions/pdf_splitter.py
nautilus -q
```

---

**Torna al [README principale](../README_IT.md)**
