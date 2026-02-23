# Simple Dev Cleaner

**Limpiador de dependencias de desarrollo para macOS** — CLI con menú. Elimina carpetas `node_modules/`, `venv/`, `.venv/`, `env/` que no se usaron en X horas.

---

## Instalación

Una sola línea:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/mgdev02/Simple-Dev-Cleaner/main/install.sh)"
```

Para reinstalar o forzar actualización (misma línea con `--force`):

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/mgdev02/Simple-Dev-Cleaner/main/install.sh)" -- --force
```

Luego ejecutá:

```bash
sdevclean
```

---

## Desinstalar

Se desinstala por **nombre del paquete** (`simple-dev-cleaner`), no por la URL de git.

**Si instalaste con pipx:**

```bash
pipx uninstall simple-dev-cleaner
```

**Si instalaste con pip:**

```bash
pip uninstall simple-dev-cleaner
```

La configuración y el historial en `~/.config/simple-dev-cleaner/` no se borran. Si querés eliminarlos también:

```bash
rm -rf ~/.config/simple-dev-cleaner
```

---

## Configuración (TOML)

La configuración y el historial se guardan en **TOML** (formato estándar en ecosistema Python):

- **Ubicación**: `~/.config/simple-dev-cleaner/`
  - `config.toml` — carpetas a escanear, umbral de horas, idioma
  - `history.toml` — historial de ejecuciones
  - `cleaner.log` — log de operaciones

Podés editar `config.toml` a mano (o desde la app: Configuración → Abrir config en editor). Ejemplo:

```toml
[config]
scan_dirs = ["/Users/tu/Desktop", "/Users/tu/Documents", "/Users/tu/Projects"]

# Carpetas a buscar (mismo criterio: sin uso hace N horas)
target_names = ["node_modules", "venv", ".venv", "env", "ENV"]

# Archivos a buscar (por nombre o patrón glob)
target_files = [".DS_Store", "*.log", "Thumbs.db", "*.tmp"]

unused_hours = 48
lang = "es"
```

- **target_names**: carpetas que se consideran “dependencias” (node_modules, venv, etc.).
- **target_files**: archivos o patrones glob (`.DS_Store`, `*.log`) que también se escanean y se pueden eliminar si llevan más de `unused_hours` sin uso.

Conceptualmente es como tener en el editor **#FOLDERS** (node_modules, venv, …) y **#FILES** (.DS_Store, *.log, …); en `config.toml` eso es `target_names` y `target_files`.

---

## Uso

```bash
sdevclean
```

| Opción | Descripción |
|--------|-------------|
| **1** | Dry run — Ver qué carpetas se borrarían (sin borrar) |
| **2** | Limpiar — Escanear, confirmar y eliminar |
| **3** | Información del sistema (chip, RAM, disco) |
| **4** | Historial de limpiezas |
| **5** | Configuración (carpetas, umbral, idioma) |
| **0** | Salir |

En cada **carpeta** eliminada se crea el archivo `install_packages_again` para recordar reinstalar dependencias. Los archivos eliminados (p. ej. `.DS_Store`) no dejan marcador.

---

## Requisitos

- Python 3.9+
- macOS 12.0+

## Desarrollo

```bash
git clone https://github.com/mgdev02/Simple-Dev-Cleaner.git
cd Simple-Dev-Cleaner
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
sdevclean
```

## Licencia

MIT.
