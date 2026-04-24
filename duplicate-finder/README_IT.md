# Trova Duplicati - Estensione Nautilus

**Lingua:** **Italiano** | [English](README.md)

---

Estensione per Nautilus che trova file duplicati in una cartella usando hash SHA-256.

## Funzionalità

- **Scansione ricorsiva** di tutte le sottocartelle
- **Hash SHA-256** per identificare file identici
- **Raggruppamento** per contenuto
- **Selezione intelligente** (mantiene il primo file)
- **Spostamento nel cestino** con un clic
- **Progress bar** durante la scansione

## Installazione

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
cp duplicate-finder.py ~/.local/share/nautilus-python/extensions/
```

### Passo 4: Riavvia Nautilus

```bash
nautilus -q
```

**Nota:** Questa estensione non richiede dipendenze aggiuntive.

## Come usare

1. **Clic destro** su una cartella
2. Seleziona **"Trova duplicati"**
3. Attendi la scansione
4. Nella finestra:
   - Seleziona i file da eliminare
   - Clicca **"Seleziona duplicati automaticamente"**
   - Clicca **"Sposta nel Cestino"**

## Disinstallazione

```bash
rm ~/.local/share/nautilus-python/extensions/duplicate-finder.py
nautilus -q
```

---

**Torna al [README principale](../README_IT.md)**
