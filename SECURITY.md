# Security Policy

**Language:** [🇮🇹 Italiano](#politica-di-sicurezza) | **🇬🇧 English**

---

## Supported Versions

| Version | Supported |
|---------|-----------|
| Latest on `main` | Yes |
| Older commits | No |

Security fixes are applied to the latest release on the `main` branch.

## Reporting a Vulnerability

**Please do NOT open a public issue for security vulnerabilities.**

Instead, report them privately via one of these channels:

1. **GitHub Private Vulnerability Reporting** — use the [Security Advisories](https://github.com/AndreaBonn/nautilus-extensions/security/advisories/new) tab on this repository
2. **Email** — contact the maintainer directly (see GitHub profile)

### What to Include

- Description of the vulnerability
- Steps to reproduce (file names, extension involved, environment)
- Potential impact assessment
- Suggested fix (if any)

### Response Timeline

| Action | Timeframe |
|--------|-----------|
| Acknowledgement | 7 days |
| Initial assessment | 14 days |
| Fix release | 30 days (best effort) |

This is a personal open-source project maintained in spare time. Timelines are best-effort, but every report will be taken seriously.

## Scope

### In Scope

These are areas where vulnerabilities may have real impact:

- **Command injection** — Several extensions invoke external commands via `subprocess` (e.g., `git`, `xdg-open`). Maliciously crafted filenames or paths could potentially be exploited if not properly sanitized.
- **Path traversal** — Extensions read files from paths provided by Nautilus. Symlink attacks or crafted directory structures could lead to unintended file access.
- **Arbitrary code execution** — Extensions that parse complex file formats (PDF, Excel, JSON, Parquet) rely on third-party libraries. A malformed file could trigger a vulnerability in an underlying parser.
- **Denial of service** — Processing extremely large files or deeply nested structures (e.g., JSON, directory trees) could exhaust memory or CPU.

### Out of Scope

- **Local privilege escalation** — Extensions run with the same privileges as the user's Nautilus process. They do not use elevated permissions.
- **Network-based attacks** — No extension opens network connections, listens on ports, or fetches remote resources.
- **Social engineering or phishing** — Out of scope for this project.
- **Vulnerabilities in system dependencies** (GTK, Nautilus, Python, system libraries) — Please report these to the respective upstream projects.

## Security Design

### How Extensions Run

All extensions are Python scripts loaded by the Nautilus file manager process. They:

- Run **locally only**, with no network access
- Execute with **user-level permissions** (no root, no setuid)
- Are invoked **only through Nautilus context menus** (no daemon, no background service)
- Process **local files only**, selected by the user

### External Commands

Some extensions execute external commands via `subprocess`:

| Extension | Commands Used |
|-----------|---------------|
| git-blame | `git rev-parse`, `git log` |
| git-diff | `git diff`, `git rev-parse` |
| git-graph | `git log --graph` |
| git-status | `git status`, `git diff` |
| duplicate-finder | `xdg-open` |
| pdf-splitter | `xdg-open` |
| csv-preview | `xdg-open` |
| excel-preview | `xdg-open` |
| json-preview | `xdg-open` |
| pdf-merger | `xdg-open` |
| dockerfile-analyzer | `xdg-open` |
| readme-viewer | `marktext`, `xdg-open` |

All subprocess calls use **list-form arguments** (not shell strings) with `subprocess.run(check=False)`, which mitigates shell injection and prevents zombie processes. However, filenames are generally passed as-is from Nautilus.

### Security Controls

The following hardening measures are implemented across extensions:

| Control | Where | Description |
|---------|-------|-------------|
| **Content Security Policy** | readme-viewer | CSP meta tag (`default-src 'none'; style-src 'unsafe-inline'; img-src file: data:`) blocks script execution, external resource loading and form submissions |
| **HTML sanitization** | readme-viewer | Regex-based sanitizer removes `<script>`, `<iframe>`, `<svg>`, event handlers (including backtick-quoted), `javascript:`/`data:` in `href`/`src`/`srcset`, and CSS `url()` injection |
| **JavaScript disabled** | readme-viewer | `set_enable_javascript(False)` on WebKit WebView |
| **Navigation blocking** | readme-viewer | All link navigation blocked except initial `about:blank` page load (including `file://` URIs) |
| **Path traversal protection** | pdf-merger, pdf-splitter | Output paths validated with `Path.resolve().is_relative_to()` to prevent directory escape |
| **Symlink protection** | duplicate-finder | `os.path.realpath().startswith(root + os.sep)` prevents symlink-based escape |
| **GTK markup escaping** | all viewers | `GLib.markup_escape_text()` prevents GTK markup injection |
| **Subprocess timeouts** | git-blame, git-diff, git-status, git-graph | All `subprocess.run` calls include `timeout` parameter |
| **Resource limits** | duplicate-finder, json-preview | `MAX_SCAN_FILES` and `MAX_READ_BYTES` prevent DoS on large directories/files |
| **Cache invalidation** | git-blame | Cache keys include file `mtime` to prevent stale data after modifications |
| **No shell execution** | all extensions | All subprocess calls use list-form arguments, never `shell=True` |

### Third-Party Libraries

Extensions depend on these Python libraries for file parsing:

| Library | Used By |
|---------|---------|
| `pandas` | csv-preview, excel-preview, json-preview, parquet-preview |
| `openpyxl` | excel-preview |
| `pypdf` | pdf-merger, pdf-splitter |
| `pyarrow` | parquet-preview |

Keep these libraries updated to benefit from upstream security fixes.

## Best Practices for Users

1. **Keep dependencies updated** — Run `pip install --upgrade` periodically for pandas, openpyxl, pypdf, and pyarrow
2. **Be cautious with untrusted files** — As with any file previewer, avoid opening files from untrusted sources
3. **Review extensions before installing** — All code is open source; inspect it before copying to your Nautilus extensions directory

---

## Politica di Sicurezza

### Segnalare una Vulnerabilità

**NON aprire una issue pubblica per vulnerabilità di sicurezza.**

Usa invece uno di questi canali:

1. **GitHub Private Vulnerability Reporting** — usa la tab [Security Advisories](https://github.com/AndreaBonn/nautilus-extensions/security/advisories/new)
2. **Email** — contatta il maintainer direttamente (vedi profilo GitHub)

### Cosa Includere

- Descrizione della vulnerabilità
- Passaggi per riprodurla (nomi file, estensione coinvolta, ambiente)
- Valutazione dell'impatto potenziale
- Suggerimento per la correzione (se presente)

### Tempi di Risposta

| Azione | Tempistica |
|--------|------------|
| Conferma ricezione | 7 giorni |
| Valutazione iniziale | 14 giorni |
| Rilascio fix | 30 giorni (best effort) |

Questo è un progetto open-source personale mantenuto nel tempo libero. Le tempistiche sono indicative, ma ogni segnalazione verrà presa seriamente.

Per i dettagli completi su scope, design, controlli di sicurezza e best practice, consulta la sezione in inglese sopra.
