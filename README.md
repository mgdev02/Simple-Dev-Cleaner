# Simple Dev Cleaner

**Limpiador de dependencias de desarrollo para macOS — CLI con menú.**

Elimina carpetas `node_modules/`, `venv/`, `.venv/`, `env/` que no se usaron en X horas. Todo manual: menú, colores, loadings, porcentajes y contadores.

---

## Instalación en una línea

Con **pip** (el comando `sdevclean` se agrega al PATH del entorno donde instales):

```bash
pip install git+https://github.com/mgdev02/Simple-Dev-Cleaner.git
```

Si usás **pipx** (recomendado: entorno aislado y el binario en PATH):

```bash
pipx install git+https://github.com/mgdev02/Simple-Dev-Cleaner.git
```

Si instalaste con `pip install --user` y no tenés `sdevclean` en el PATH, añadí el directorio de scripts. En macOS con Python de Homebrew o oficial:

```bash
# Ejemplo: Python 3.12
echo 'export PATH="$HOME/Library/Python/3.12/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

Luego ejecutá desde cualquier terminal:

```bash
sdevclean
```

---

## Características

- **CLI con menú**: opciones numeradas, todo manual en el momento
- **Colores y tablas**: salida con [rich](https://github.com/Textualize/rich)
- **Loadings**: spinner mientras escanea
- **Contadores**: "Encontrados: 0, 1, 2..." en tiempo real
- **Porcentajes**: barra de progreso al eliminar (ej. 3/7 — 43%)
- **Dry run**: ver qué se borraría sin borrar nada
- **Info del sistema**: chip, RAM, disco, barra de uso
- **Historial**: ver ejecuciones anteriores y MB liberados
- **Configuración**: carpetas a monitorear y umbral de horas sin uso

## Requisitos

- Python 3.9+
- macOS 12.0+

## Desarrollo (clonar y correr en local)

```bash
git clone https://github.com/mgdev02/Simple-Dev-Cleaner.git
cd Simple-Dev-Cleaner
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
sdevclean
```

## Uso

```bash
sdevclean
```

### Menú

| Opción | Descripción |
|--------|-------------|
| **1** | Dry run — Escanea y muestra qué carpetas se borrarían (sin borrar) |
| **2** | Limpiar — Escanea, pide confirmación y elimina. Barra de progreso con % |
| **3** | Ver información del sistema (chip, RAM, disco, barra de uso) |
| **4** | Ver historial de limpiezas (fechas, items, MB liberados) |
| **5** | Configurar — Carpetas a monitorear y umbral de horas sin uso |
| **0** | Salir |

En cada carpeta eliminada se deja un archivo `install_packages_again` (sin extensión) para recordar reinstalar dependencias.

## Estructura

```
DevCleaner/
├── cli.py           # CLI principal (menú, rich)
├── cleaner.py       # Motor de limpieza
├── system_info.py   # Info del sistema macOS
├── config.json      # Configuración (se crea al usar)
├── history.json     # Historial de ejecuciones
├── requirements.txt # rich
└── README.md
```

## Configuración

Al ejecutar por primera vez se crea la configuración en:
- **Instalado con pip**: `~/.config/simple-dev-cleaner/config.json`
- **Desde fuente**: `config.json` en la carpeta del proyecto

- **scan_dirs**: carpetas a escanear (Desktop, Documents, etc.)
- **unused_hours**: horas sin uso para considerar una carpeta abandonada (default 48)

No hay programación ni agentes: todo se ejecuta cuando corrés el menú.

## Licencia

Uso personal.
