# 🔗 Unisci PDF - Estensione Nautilus

**Lingua:** **🇮🇹 Italiano** | [🇬🇧 English](README.md)

---

Estensione per Nautilus che permette di unire più file PDF in uno solo con interfaccia grafica.

## 🎯 Funzionalità

- **Selezione multipla** di file PDF
- **Riordino tramite drag & drop** o pulsanti ⬆⬇
- **Rimozione file** dalla lista
- **Anteprima numero pagine** per ogni PDF
- **Conteggio pagine totali** del file risultante
- **Scelta nome file output**
- **Apertura automatica** della cartella di destinazione

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
cp pdf_merger.py ~/.local/share/nautilus-python/extensions/
```

### Passo 5: Riavvia Nautilus

```bash
nautilus -q
```

## 📖 Come usare

1. **Seleziona 2 o più file PDF** (tieni premuto `Ctrl` mentre clicchi)
2. **Clic destro** sulla selezione
3. Seleziona **"Unisci [N] PDF"**
4. Nella finestra:
   - Riordina i file trascinandoli o con ⬆⬇
   - Rimuovi file con ✕
   - Modifica il nome output
   - Clicca **"🔗 Unisci PDF"**

Il file unito verrà salvato nella cartella del primo PDF.

## 🗑️ Disinstallazione

```bash
rm ~/.local/share/nautilus-python/extensions/pdf_merger.py
nautilus -q
```

---

**Torna al [README principale](../README_IT.md)**
