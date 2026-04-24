# Visualizza README - Estensione Nautilus

**Lingua:** **Italiano** | [English](README.md)

---

Estensione per Nautilus che mostra il file README della cartella corrente con rendering Markdown.

## Funzionalità

- **Rilevamento automatico** di README.md, README.txt, README.rst
- **Rendering Markdown** (se WebKit è disponibile)
- **Apertura rapida** nell'editor
- **Supporto formati** multipli

## Installazione

### Passo 1: Installa nautilus-python

```bash
sudo apt update
sudo apt install python3-nautilus
```

### Passo 2: Installa le dipendenze (opzionali)

Per il rendering Markdown:
```bash
sudo apt install python3-markdown gir1.2-webkit2-4.1
```

### Passo 3: Crea la cartella delle estensioni

```bash
mkdir -p ~/.local/share/nautilus-python/extensions
```

### Passo 4: Copia il file dell'estensione

```bash
cp readme_preview.py ~/.local/share/nautilus-python/extensions/
```

### Passo 5: Riavvia Nautilus

```bash
nautilus -q
```

## Come usare

1. Apri una cartella con un README
2. **Clic destro sullo sfondo** (non su un file)
3. Seleziona **"Mostra README.md"**
4. Il README verrà visualizzato

## Disinstallazione

```bash
rm ~/.local/share/nautilus-python/extensions/readme_preview.py
nautilus -q
```

---

**Torna al [README principale](../README_IT.md)**
