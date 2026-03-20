# ⎇ Git Status - Estensione Nautilus

**Lingua:** **🇮🇹 Italiano** | [🇬🇧 English](README_EN.md)

---

Estensione per Nautilus che aggiunge un pannello di stato Git con aggiornamento automatico dal menu contestuale.

## 🎯 Funzionalità

- **Branch corrente** con indicatore ahead/behind rispetto al remote
- **File staged** pronti per il commit
- **File modificati** nel working tree
- **File untracked** nuovi e non tracciati
- **Ultimi 10 commit** con hash, autore, data e messaggio
- **Conteggio stash** salvati
- **Aggiornamento automatico** ogni 3 secondi
- **Pulsante refresh** manuale nella barra del titolo
- **Icone colorate** per tipo di modifica (aggiunto, modificato, eliminato)

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
cp git_status.py ~/.local/share/nautilus-python/extensions/
```

### Passo 4: Riavvia Nautilus

```bash
nautilus -q
```

**Nota:** Questa estensione non richiede dipendenze aggiuntive (solo `git` installato nel sistema).

## 📖 Come usare

1. Apri Nautilus e naviga in una cartella all'interno di un repository Git
2. **Clic destro** sullo sfondo della cartella
3. Seleziona **"⎇ Stato Git…"**
4. Nella finestra vedrai:
   - **Header:** nome del branch con indicatori ↑↓ per commit ahead/behind
   - **Staged:** file pronti per il commit (verde)
   - **Modificati:** file con modifiche non staged (giallo)
   - **Nuovi/Untracked:** file non tracciati (blu)
   - **Ultimi commit:** cronologia degli ultimi 10 commit
   - **Stash:** numero di stash salvati

La finestra si aggiorna automaticamente ogni 3 secondi. Puoi anche cliccare **↻** per un refresh immediato.

## 🔍 Dettagli tecnici

- **Versione Nautilus:** 43+ (GNOME 43+) con GTK 4
- **API:** `MenuProvider`
- **Thread:** L'aggiornamento dei dati git avviene in thread separati per non bloccare l'interfaccia
- **Auto-refresh:** Timer con `GLib.timeout_add()` ogni 3000ms
- **Riuso finestra:** Se la finestra è già aperta, viene riutilizzata aggiornando il path

## 🗑️ Disinstallazione

```bash
rm ~/.local/share/nautilus-python/extensions/git_status.py
nautilus -q
```

---

**Torna al [README principale](../README.md)**
