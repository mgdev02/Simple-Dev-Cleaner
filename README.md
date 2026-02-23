# Simple Dev Cleaner

**Limpiador de dependencias de desarrollo para macOS** — CLI con menú. Elimina carpetas `node_modules/`, `venv/`, `.venv/`, `env/` que no se usaron en X horas.

---

## Instalación global (recomendada)

Para tener el comando **`sdevclean`** disponible en cualquier terminal:

### Con pipx (recomendado)

[pipx](https://pypa.github.io/pipx/) instala la herramienta en un entorno aislado y añade el ejecutable al PATH:

```bash
pipx install git+https://github.com/mgdev02/Simple-Dev-Cleaner.git
```

Si no tenés pipx:

```bash
brew install pipx
pipx ensurepath   # añade ~/.local/bin al PATH
pipx install git+https://github.com/mgdev02/Simple-Dev-Cleaner.git
```

Luego, en cualquier carpeta:

```bash
sdevclean
```

### Con pip (instalación de usuario)

```bash
pip install --user git+https://github.com/mgdev02/Simple-Dev-Cleaner.git
```

El ejecutable queda en un directorio que debe estar en tu PATH. En macOS suele ser:

- `~/Library/Python/3.12/bin` (o la versión de Python que uses)

Si `sdevclean` no se encuentra, añadí ese directorio a tu shell. Por ejemplo en `~/.zshrc`:

```bash
export PATH="$HOME/Library/Python/3.12/bin:$PATH"
```

---

## Configuración (TOML)

La configuración y el historial se guardan en **TOML** (formato estándar en ecosistema Python):

- **Ubicación**: `~/.config/simple-dev-cleaner/`
  - `config.toml` — carpetas a escanear, umbral de horas, idioma
  - `history.toml` — historial de ejecuciones
  - `cleaner.log` — log de operaciones

Podés editar `config.toml` a mano. Ejemplo:

```toml
[config]
scan_dirs = ["/Users/tu/Desktop", "/Users/tu/Documents", "/Users/tu/Projects"]
target_names = ["node_modules", "venv", ".venv", "env", "ENV"]
unused_hours = 48
lang = "es"
```

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

En cada carpeta eliminada se crea el archivo `install_packages_again` para recordar reinstalar dependencias.

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
