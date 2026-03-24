# 🐳 Analizza Dockerfile - Estensione Nautilus

**Lingua:** **🇮🇹 Italiano** | [🇬🇧 English](README.md)

---

Estensione per Nautilus che analizza Dockerfile e fornisce suggerimenti di best practice e sicurezza.

## 🎯 Funzionalità

- **Analisi struttura** Dockerfile
- **Rilevamento multi-stage builds**
- **Best practice e sicurezza** con 14+ controlli
- **Evidenziazione problemi** per severità (critici, medi, info)
- **Visualizzazione istruzioni** con syntax highlighting
- **Metadati** (ENV, ARG, EXPOSE, VOLUME, ecc.)

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
cp dockerfile_analyzer.py ~/.local/share/nautilus-python/extensions/
```

### Passo 4: Riavvia Nautilus

```bash
nautilus -q
```

**Nota:** Questa estensione non richiede dipendenze aggiuntive.

## 📖 Come usare

1. **Clic destro** su un file Dockerfile
2. Seleziona **"Analizza Dockerfile"**
3. Esplora i 4 tab:
   - **🐳 Overview**: immagini, porte, variabili
   - **⚠ Best Practice**: suggerimenti di sicurezza
   - **📋 Istruzioni**: lista completa
   - **📄 Sorgente**: codice con colori

## 🗑️ Disinstallazione

```bash
rm ~/.local/share/nautilus-python/extensions/dockerfile_analyzer.py
nautilus -q
```

---

**Torna al [README principale](../README_IT.md)**
