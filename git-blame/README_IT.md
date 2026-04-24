# Git Blame - Estensione Nautilus

**Lingua:** **Italiano** | [English](README.md)

---

Estensione per Nautilus che aggiunge colonne Git blame nella vista lista, mostrando autore, data e messaggio dell'ultimo commit per ogni file.

## Funzionalità

- **Colonna "Git: Autore"** — chi ha fatto l'ultimo commit sul file
- **Colonna "Git: Data"** — quando (es. "3 hours ago")
- **Colonna "Git: Messaggio"** — messaggio del commit (troncato a 55 caratteri)
- **Caricamento asincrono** con thread in background per non bloccare Nautilus
- **Cache dei risultati** per evitare chiamate git ripetute
- **Rilevamento automatico** se il file è in un repository git

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
cp git_blame.py ~/.local/share/nautilus-python/extensions/
```

### Passo 4: Riavvia Nautilus

```bash
nautilus -q
```

**Nota:** Questa estensione non richiede dipendenze aggiuntive (solo `git` installato nel sistema).

## Come usare

1. Apri Nautilus e naviga in una cartella all'interno di un repository Git
2. Passa alla **Vista Lista** con `Ctrl+2`
3. **Clic destro** sull'intestazione delle colonne
4. Spunta **"Git: Autore"**, **"Git: Data"**, **"Git: Messaggio"**

Le colonne mostreranno le informazioni dell'ultimo commit per ogni file.

## Dettagli tecnici

- **Versione Nautilus:** 43+ (GNOME 43+) con GTK 4
- **API:** `ColumnProvider` + `InfoProvider`
- **Thread:** Il caricamento delle informazioni git avviene in thread separati per non bloccare l'interfaccia
- **Cache:** I risultati vengono memorizzati in cache per evitare chiamate ripetute a `git log`

## Disinstallazione

```bash
rm ~/.local/share/nautilus-python/extensions/git_blame.py
nautilus -q
```

---

**Torna al [README principale](../README_IT.md)**
