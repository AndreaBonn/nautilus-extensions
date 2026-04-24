# Contribuire alle Estensioni Nautilus

**Lingua:** **Italiano** | [English](CONTRIBUTING.md)

## Come Contribuire

### Segnalare Bug

Apri una issue con:
- Una descrizione chiara del problema
- Passaggi per riprodurlo
- Comportamento atteso vs comportamento effettivo
- Informazioni sul tuo sistema (OS, versione Nautilus, versione Python)

### Suggerire Funzionalità

Apri una issue descrivendo:
- La funzionalità che vorresti vedere
- Perché sarebbe utile
- Come potrebbe funzionare

## Setup Sviluppo

Il progetto usa [uv](https://docs.astral.sh/uv/) per la gestione delle dipendenze.

```bash
# Clona il repository
git clone https://github.com/AndreaBonn/nautilus-extensions.git
cd nautilus-extensions

# Installa le dipendenze (inclusi i tool di sviluppo)
uv sync --all-extras

# Verifica che tutto funzioni
make check
```

### Comandi Disponibili

```bash
make lint       # Esegue il linter ruff
make format     # Formatta il codice con ruff
make test       # Esegue la test suite
make security   # Esegue i check di sicurezza (ruff-S + bandit + pip-audit)
make check      # Esegue lint + test + security
make install    # Installa le estensioni in Nautilus
make restart    # Riavvia Nautilus per caricare le modifiche
```

## Inviare Codice

1. Fai un fork del repository
2. Crea un nuovo branch (`git checkout -b feature/tua-funzionalita`)
3. Fai le tue modifiche
4. Esegui `make check` — lint e test devono passare tutti
5. Fai commit con messaggi nel formato: `tipo(scope): descrizione`
   - Tipi: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `perf`
6. Pusha sul tuo fork (`git push origin feature/tua-funzionalita`)
7. Apri una Pull Request

### Stile del Codice

- Il codice è lintato e formattato con [ruff](https://docs.astral.sh/ruff/) — esegui `make lint` prima del commit
- Usa type annotation su tutti i parametri e valori di ritorno delle funzioni
- Escapa tutte le stringhe GTK markup con `GLib.markup_escape_text()`
- Tutte le chiamate `subprocess` devono usare argomenti in forma lista (mai `shell=True`)

### Nota Architetturale

Ogni estensione Nautilus **deve essere un singolo file `.py`** — è un vincolo di Nautilus, non una scelta di design. Il file viene copiato direttamente in `~/.local/share/nautilus-python/extensions/`. Questo significa che alcune funzioni utility (es. `fmt_size`) sono duplicate tra le estensioni per necessità.

### Testing

Ogni nuova funzione o bug fix deve includere test corrispondenti:

```bash
uv run pytest tests/ -v          # Esegui tutti i test
uv run pytest tests/test_X.py -v # Esegui un file specifico
```

- I test sono in `tests/` e rispecchiano la struttura delle estensioni
- Usa assert comportamentali (testa cosa fa la funzione, non solo che esegue)
- Naming test: `test_<funzione>_<scenario>_<risultato_atteso>`

## Domande?

Apri una issue per qualsiasi domanda.
