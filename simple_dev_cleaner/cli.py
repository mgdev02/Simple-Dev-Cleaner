#!/usr/bin/env python3
"""
Simple Dev Cleaner — Interactive menu, colors, loadings, persistent language (es/en).
"""

import os
import shlex
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from questionary import select, Choice
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    TaskProgressColumn,
)
from rich.prompt import Prompt, Confirm
from rich import box

from simple_dev_cleaner.cleaner import (
    Config,
    RunSummary,
    scan,
    delete_from_summary,
)
from simple_dev_cleaner.system_info import get_system_info
from simple_dev_cleaner.update_check import run_update

console = Console()

# Translations (es/en). Language persisted in config.toml.
TEXTS = {
    "es": {
        "app_subtitle": "Limpiador de dependencias",
        "menu_title": "Menú principal",
        "menu_1": "Dry run y limpiar (ver qué se borraría y luego elegir si eliminar)",
        "menu_3": "Ver información del sistema",
        "menu_4": "Ver historial de limpiezas",
        "menu_5": "Configuración (carpetas, umbral, idioma)",
        "menu_0": "Salir (Ctrl+C)",
        "prompt_option": "Elegí una opción (↑ ↓ flechas, Enter)",
        "hint_exit": "[dim](0 o q = salir)[/]",
        "first_run_tip": "[dim]Usá ↑↓ y Enter para elegir. Ctrl+C para salir.[/]",
        "bye": "Chau.",
        "press_enter": "[dim]Enter para continuar[/]",
        "dry_run_title": "Dry run y limpiar",
        "dry_run_desc": "Primero se muestra qué se borraría; después podés elegir si ejecutar la limpieza real.",
        "scanning": "Buscando carpetas...",
        "found_count": "Encontrados",
        "done": "Listo.",
        "total_found": "Total encontrados",
        "none_match": "No hay carpetas que cumplan el criterio (sin uso hace al menos {} horas).",
        "table_would_delete": "Carpetas/archivos que se borrarían al confirmar",
        "col_path": "Ruta",
        "col_type": "Tipo",
        "col_size": "Tamaño",
        "col_unused": "Sin uso",
        "type_folder": "carpeta",
        "type_file": "archivo",
        "col_name": "Nombre",
        "space_would_free": "Espacio que se liberaría",
        "dry_run_run_clean": "¿Querés ejecutar la limpieza real ahora?",
        "dry_run_yes_run": "Sí, ejecutar limpieza",
        "dry_run_no_back": "No, volver al menú",
        "clean_title": "Limpieza real",
        "clean_desc": "Se buscan carpetas y, si confirmás, se eliminan.",
        "nothing_to_clean": "No hay nada que limpiar.",
        "found_folders": "Encontradas",
        "folders": "carpetas.",
        "space_to_free": "Espacio a liberar",
        "warning_irreversible": "⚠ ADVERTENCIA: Una vez borrado no se puede recuperar.",
        "confirm_delete": "¿Estás seguro? Se eliminarán las carpetas (es irreversible)",
        "confirm_yes_no": "Escribí [bold]sí[/] o [bold]no[/]",
        "confirm_yes": "Sí, eliminar",
        "confirm_no": "No, cancelar",
        "cancelled": "Cancelado. No se borró nada.",
        "deleting": "Eliminando...",
        "result_title": "Resultado",
        "space_freed": "Espacio liberado",
        "folders_deleted": "Carpetas/archivos eliminados",
        "freed_less_note": "[dim]{} no se pudo liberar (en uso o sin permiso).[/]",
        "marker_note": "En cada carpeta padre se creó el archivo [bold]install_packages_again[/] para que sepas que tenés que reinstalar dependencias.",
        "error_deleting": "Error",
        "system_title": "Sistema",
        "system_loading": "Obteniendo información del sistema...",
        "field_chip": "Chip",
        "field_arch": "Arquitectura",
        "field_ram": "RAM",
        "field_macos": "macOS",
        "field_hostname": "Hostname",
        "field_disk_total": "Disco total",
        "field_disk_used": "Disco usado",
        "field_disk_free": "Disco libre",
        "field_disk_usage": "Uso disco",
        "history_title": "Historial",
        "history_empty": "Todavía no hay historial. Cuando hagas una limpieza o un dry run, acá va a aparecer.",
        "history_total_freed": "Total liberado",
        "history_runs": "ejecuciones",
        "col_date": "Fecha",
        "col_type_run": "Tipo",
        "col_items": "Items",
        "col_freed": "Liberado",
        "type_dry": "Dry run",
        "type_clean": "Limpieza",
        "config_title": "Configuración",
        "config_1": "Ver carpetas que se escanean",
        "config_2": "Agregar carpeta",
        "config_3": "Quitar carpeta",
        "config_4": "Cambiar umbral de horas sin uso (actual: {} h)",
        "config_5": "Cambiar idioma / Language (actual: {})",
        "config_0": "Volver al menú principal",
        "config_6": "Abrir config.toml en el editor (nano, vim, etc.)",
        "config_prompt": "Opción (↑ ↓ flechas, Enter)",
        "hint_back": "[dim](0 o q = volver)[/]",
        "folders_list": "Carpetas que se escanean",
        "exists": "existe",
        "not_exists": "no existe (no se escaneará)",
        "path_prompt": "Ruta(s). Una o varias separadas por coma o una por línea. [dim]q = cancelar[/]",
        "path_empty": "No escribiste ninguna ruta. Probá de nuevo.",
        "path_not_found": "No encontré esa carpeta. Revisá que la ruta exista y que tengas permisos de lectura.",
        "path_added": "Agregada a la lista.",
        "paths_added": "Agregadas {} carpetas a la lista.",
        "paths_skipped": " {} omitidas (ya existían o no son válidas).",
        "path_already": "Esa carpeta ya está en la lista.",
        "edit_config": "Abriendo config en el editor…",
        "edit_done": "Config guardada. Cambios aplicados.",
        "edit_fail": "No se pudo abrir el editor (probá EDITOR=nano o editar a mano ~/.config/simple-dev-cleaner/config.toml).",
        "which_remove": "¿Cuál carpeta querés quitar de la lista? (↑ ↓ flechas, Enter)",
        "which_remove_cancel": "Cancelar (volver)",
        "hint_q_cancel": "[dim](q = cancelar)[/]",
        "number_invalid": "Ese número no es válido. Elegí un número entre 1 y {}.",
        "removed_from_list": "Quitada de la lista.",
        "no_folders_configured": "Aún no hay carpetas configuradas. Agregá al menos una (opción 2).",
        "hours_prompt": "¿Cuántas horas sin uso para considerar una carpeta «abandonada»? (1–8760, ahora: {})",
        "hours_invalid": "Tiene que ser un número entre 1 y 8760 (horas).",
        "hours_saved": "Listo. A partir de ahora se consideran abandonadas las carpetas sin uso hace {} horas o más.",
        "lang_current": "Idioma actual",
        "lang_choose": "Elegí idioma",
        "lang_invalid": "Elegí 1 (Español) o 2 (English).",
        "lang_prompt": "1 o 2",
        "lang_saved_es": "Idioma guardado: Español. Se aplica desde ya.",
        "lang_saved_en": "Language saved: English. It applies from now on.",
        "interrupted": "Interrumpido. Volvé a elegir una opción.",
        "error_unexpected": "Error inesperado",
        "error_hint": "Si se repite, revisá ~/.config/simple-dev-cleaner/config.toml o borrá history.toml y probá de nuevo.",
        "check_updates": "Check updates",
        "downloading": "Downloading…",
        "updated": "Updated.",
        "update_fail": "No se pudo actualizar. Actualizá manualmente: [dim]pipx upgrade simple-dev-cleaner[/]",
    },
    "en": {
        "app_subtitle": "Dependency cleaner",
        "menu_title": "Main menu",
        "menu_1": "Dry run & clean (see what would be deleted, then choose to delete)",
        "menu_3": "System information",
        "menu_4": "Cleanup history",
        "menu_5": "Settings (folders, threshold, language)",
        "menu_0": "Exit (Ctrl+C)",
        "prompt_option": "Choose an option (↑ ↓ arrows, Enter)",
        "hint_exit": "[dim](0 or q = exit)[/]",
        "first_run_tip": "[dim]Use ↑↓ and Enter to choose. Ctrl+C to exit.[/]",
        "bye": "Bye.",
        "press_enter": "[dim]Press Enter to continue[/]",
        "dry_run_title": "Dry run & clean",
        "dry_run_desc": "First we show what would be deleted; then you can choose to run the real clean.",
        "scanning": "Scanning folders...",
        "found_count": "Found",
        "done": "Done.",
        "total_found": "Total found",
        "none_match": "No folders match the criteria (unused for at least {} hours).",
        "table_would_delete": "Folders that would be deleted if you choose «Clean»",
        "col_path": "Path",
        "col_type": "Type",
        "col_size": "Size",
        "col_unused": "Unused",
        "type_folder": "folder",
        "type_file": "file",
        "col_name": "Name",
        "space_would_free": "Space that would be freed",
        "dry_run_run_clean": "Do you want to run the real clean now?",
        "dry_run_yes_run": "Yes, run clean",
        "dry_run_no_back": "No, back to menu",
        "clean_title": "Real cleanup",
        "clean_desc": "I'll scan for folders and, if you confirm, delete them.",
        "nothing_to_clean": "Nothing to clean.",
        "found_folders": "Found",
        "folders": "folders.",
        "space_to_free": "Space to free",
        "warning_irreversible": "⚠ WARNING: Once deleted, it cannot be recovered.",
        "confirm_delete": "Are you sure? These folders will be deleted (cannot be undone)",
        "confirm_yes_no": "Type [bold]yes[/] or [bold]no[/]",
        "confirm_yes": "Yes, delete",
        "confirm_no": "No, cancel",
        "cancelled": "Cancelled. Nothing was deleted.",
        "deleting": "Deleting...",
        "result_title": "Result",
        "space_freed": "Space freed",
        "folders_deleted": "Items deleted",
        "freed_less_note": "[dim]{} could not be freed (in use or permission).[/]",
        "marker_note": "A file [bold]install_packages_again[/] was created in each parent folder so you know you need to reinstall dependencies.",
        "error_deleting": "Error",
        "system_title": "System",
        "system_loading": "Getting system information...",
        "field_chip": "Chip",
        "field_arch": "Architecture",
        "field_ram": "RAM",
        "field_macos": "macOS",
        "field_hostname": "Hostname",
        "field_disk_total": "Disk total",
        "field_disk_used": "Disk used",
        "field_disk_free": "Disk free",
        "field_disk_usage": "Disk usage",
        "history_title": "History",
        "history_empty": "No history yet. After you run a cleanup or dry run, it will show here.",
        "history_total_freed": "Total freed",
        "history_runs": "runs",
        "col_date": "Date",
        "col_type_run": "Type",
        "col_items": "Items",
        "col_freed": "Freed",
        "type_dry": "Dry run",
        "type_clean": "Cleanup",
        "config_title": "Settings",
        "config_1": "View folders being scanned",
        "config_2": "Add folder",
        "config_3": "Remove folder",
        "config_4": "Change unused-hours threshold (current: {} h)",
        "config_5": "Change language / Idioma (current: {})",
        "config_0": "Back to main menu",
        "config_6": "Open config.toml in editor (nano, vim, etc.)",
        "config_prompt": "Option (↑ ↓ arrows, Enter)",
        "hint_back": "[dim](0 or q = back)[/]",
        "folders_list": "Folders being scanned",
        "exists": "exists",
        "not_exists": "does not exist (will be skipped)",
        "path_prompt": "Path(s). One or more, comma-separated or one per line. [dim]q = cancel[/]",
        "path_empty": "You didn't enter a path. Try again.",
        "path_not_found": "That folder wasn't found. Check that the path exists and you have read permission.",
        "path_added": "Added to the list.",
        "paths_added": "{} folders added to the list.",
        "paths_skipped": " {} skipped (already in list or invalid).",
        "path_already": "That folder is already in the list.",
        "edit_config": "Opening config in editor…",
        "edit_done": "Config saved. Changes applied.",
        "edit_fail": "Could not open editor (try EDITOR=nano or edit ~/.config/simple-dev-cleaner/config.toml manually).",
        "which_remove": "Which folder do you want to remove from the list? (↑ ↓ arrows, Enter)",
        "which_remove_cancel": "Cancel (go back)",
        "hint_q_cancel": "[dim](q = cancel)[/]",
        "number_invalid": "That number isn't valid. Choose a number between 1 and {}.",
        "removed_from_list": "Removed from the list.",
        "no_folders_configured": "No folders configured yet. Add at least one (option 2).",
        "hours_prompt": "How many hours of no use to consider a folder «abandoned»? (1–8760, current: {})",
        "hours_invalid": "Must be a number between 1 and 8760 (hours).",
        "hours_saved": "Saved. Folders unused for {} hours or more will now be considered abandoned.",
        "lang_current": "Current language",
        "lang_choose": "Choose language",
        "lang_invalid": "Choose 1 (Español) or 2 (English).",
        "lang_prompt": "1 or 2",
        "lang_saved_es": "Language saved: Spanish. It applies from now on.",
        "lang_saved_en": "Language saved: English. It applies from now on.",
        "interrupted": "Interrupted. Choose an option again.",
        "error_unexpected": "Unexpected error",
        "error_hint": "If it happens again, check ~/.config/simple-dev-cleaner/config.toml or delete history.toml and try again.",
        "check_updates": "Check updates",
        "downloading": "Downloading…",
        "updated": "Updated.",
        "update_fail": "Could not update. Update manually: [dim]pipx upgrade simple-dev-cleaner[/]",
    },
}


def t(config: Config, key: str, *args: Any) -> str:
    """Return the translation for the given key in the current language."""
    lang = getattr(config, "lang", "es") or "es"
    if lang not in TEXTS:
        lang = "es"
    s = TEXTS[lang].get(key, TEXTS["es"].get(key, key))
    if args:
        s = s.format(*args)
    return s


def wait_enter(config: Config) -> None:
    """Pause until the user presses Enter (to read results)."""
    console.print()
    try:
        Prompt.ask(t(config, "press_enter"), default="", show_default=False)
    except Exception:
        pass


def _normalize_choice(raw: str, choices: list[str]) -> str:
    """Accept 0/q as exit/back. Return valid choice or '0'."""
    s = (raw or "").strip().lower()
    if s in ("q", "quit", "exit", "esc"):
        return "0"
    return s if s in choices else "0"


def format_size_mb(mb: float) -> str:
    """Format MB as 'X.X GB' if >= 1024, else 'X.X MB'."""
    if mb >= 1024:
        return f"{mb / 1024:.1f} GB"
    return f"{mb:.1f} MB"


def format_unused_hours(hours: int) -> str:
    """Format hours as 'X h', '1 day', '2 days', '1 week', etc."""
    if hours < 24:
        return f"{hours} h"
    if hours < 168:  # < 1 week
        days = hours // 24
        return "1 day" if days == 1 else f"{days} days"
    if hours < 720:  # < ~1 month
        weeks = hours // 168
        return "1 week" if weeks == 1 else f"{weeks} weeks"
    months = hours // 720
    return "~1 month" if months == 1 else f"~{months} months"


def print_banner(config: Config) -> None:
    console.print()
    date_str = datetime.now().strftime("%H:%M %d/%m/%Y")
    with console.status(f"[dim]{t(config, 'system_loading')}[/]", spinner="dots"):
        info = get_system_info()
    pct = info["disk_pct"]
    if pct >= 90:
        disk_bar = "[red]"
    elif pct >= 75:
        disk_bar = "[yellow]"
    else:
        disk_bar = "[green]"
    disk_bar += "█" * int(pct / 5) + "[/][dim]" + "░" * (20 - int(pct / 5)) + "[/] " + f"{pct:.0f}%"
    disk_line1 = f"[dim]{t(config, 'field_disk_total')}[/] {info['disk_total']}  [dim]{t(config, 'field_disk_used')}[/] {info['disk_used']}  [dim]{t(config, 'field_disk_free')}[/] {info['disk_free']}"
    disk_line2 = f"[dim]{t(config, 'field_disk_usage')}[/] {disk_bar}"
    disk_content = Group(disk_line1, disk_line2)
    header_table = Table.grid(expand=True)
    header_table.add_column(justify="left")
    header_table.add_column(justify="right")
    header_table.add_row(
        f"[bold cyan]Simple Dev Cleaner[/] [dim]— {t(config, 'app_subtitle')}[/]",
        f"[dim]{date_str}[/]",
    )
    disk_panel = Panel(
        disk_content,
        box=box.ROUNDED,
        border_style="dim",
        padding=(0, 1),
    )
    banner_content = Group(header_table, disk_panel)
    console.print(
        Panel(
            banner_content,
            box=box.ROUNDED,
            border_style="cyan",
            padding=(0, 2),
        )
    )
    console.print(f"[dim]~By mgdev02[/]", justify="right")
    console.print()


def main_menu(config: Config) -> str:
    choices = ["0", "1", "2", "3"]
    if sys.stdin.isatty():
        menu_choices = [
            Choice(t(config, "menu_1"), value="1"),   # Dry run & clean
            Choice(t(config, "menu_4"), value="2"),   # History
            Choice(t(config, "menu_5"), value="3"),   # Settings
            Choice(t(config, "menu_0"), value="0"),
        ]
        try:
            result = select(
                t(config, "prompt_option"),
                choices=menu_choices,
                use_shortcuts=False,
                instruction="",
            ).ask()
            return result if result is not None else "0"
        except (KeyboardInterrupt, EOFError):
            return "0"
    # No TTY (script/pipe): fallback to number input
    try:
        raw = (Prompt.ask(f"[bold]{t(config, 'prompt_option')}[/]", default="0") or "0").strip()
        return _normalize_choice(raw, choices)
    except Exception:
        return "0"


def run_dry_run(config: Config) -> None:
    console.print()
    console.print(f"[bold yellow]{t(config, 'dry_run_title')}[/] — {t(config, 'dry_run_desc')}")
    console.print()
    count: list[int] = [0]
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}[/]"),
        TextColumn("[dim]" + t(config, "found_count") + ": {task.fields[count]}[/]"),
        console=console,
    ) as progress:
        task = progress.add_task(t(config, "scanning"), count=0)

        def on_found(r: Any) -> None:
            count[0] += 1
            progress.update(task_id=task, fields={"count": count[0]})

        summary = scan(config, dry_run=True, progress_cb=on_found)

    total = len(summary.results)
    console.print(f"[green]{t(config, 'done')}[/] {t(config, 'total_found')}: [bold]{total}[/]")
    console.print()
    if total == 0:
        console.print(f"[dim]{t(config, 'none_match', config.unused_hours)}[/]")
        return

    table = Table(
        title=t(config, "table_would_delete"),
        box=box.ROUNDED,
        header_style="bold cyan",
        border_style="blue",
    )
    table.add_column("#", style="dim", width=4)
    table.add_column(t(config, "col_path"), overflow="fold")
    table.add_column(t(config, "col_name"), width=14)
    table.add_column(t(config, "col_type"), width=8)
    table.add_column(t(config, "col_size"), justify="right", width=10)
    table.add_column(t(config, "col_unused"), justify="right", width=12)
    for i, r in enumerate(summary.results, 1):
        short = r["path"].replace(str(Path.home()), "~")
        table.add_row(
            str(i),
            short,
            r["name"],
            t(config, "type_file") if r.get("is_file") else t(config, "type_folder"),
            format_size_mb(r["size_mb"]),
            format_unused_hours(r["unused_hours"]),
        )
    console.print(table)
    total_mb = sum(r["size_mb"] for r in summary.results)
    console.print(f"[dim]{t(config, 'space_would_free')}: [bold]{format_size_mb(total_mb)}[/][/]")
    console.print()
    # Preguntar si quiere ejecutar la limpieza real
    run_clean_now = False
    if sys.stdin.isatty():
        run_choice = select(
            t(config, "dry_run_run_clean"),
            choices=[
                Choice(t(config, "dry_run_no_back"), value=False),
                Choice(t(config, "dry_run_yes_run"), value=True),
            ],
            use_shortcuts=False,
            instruction="",
        ).ask()
        run_clean_now = run_choice if run_choice is not None else False
    if run_clean_now:
        try:
            console.print(f"[bold yellow]{t(config, 'warning_irreversible')}[/]")
            console.print()
            if sys.stdin.isatty():
                confirm_choice = select(
                    t(config, "confirm_delete"),
                    choices=[
                        Choice(t(config, "confirm_no"), value=False),
                        Choice(t(config, "confirm_yes"), value=True),
                    ],
                    use_shortcuts=False,
                    instruction="",
                ).ask()
                do_delete = confirm_choice if confirm_choice is not None else False
            else:
                do_delete = Confirm.ask(
                    f"[yellow]{t(config, 'confirm_delete')}[/]\n{t(config, 'confirm_yes_no')}",
                    default=False,
                )
            if do_delete:
                console.print()
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[bold green]{task.description}[/]"),
                    BarColumn(bar_width=40, complete_style="green", finished_style="green"),
                    TaskProgressColumn(),
                    TextColumn("[dim]{task.fields[status]}[/]"),
                    console=console,
                ) as progress:
                    task = progress.add_task(t(config, "deleting"), total=total, status="", completed=0)

                    def on_delete(current: int, total_n: int, r: dict, err: str | None) -> None:
                        pct = (current / total_n) * 100 if total_n else 0
                        status = r["path"].replace(str(Path.home()), "~")
                        if len(status) > 50:
                            status = "..." + status[-47:]
                        if err:
                            status = f"[red]{t(config, 'error_deleting')}: {status}[/]"
                        progress.update(task_id=task, completed=current, percent=pct, status=status)

                    freed = delete_from_summary(summary, progress_cb=on_delete)
                    progress.update(task_id=task, completed=total, percent=100, status="[green]✓[/]")

                summary.dry_run = False
                summary.total_freed_mb = freed
                summary.results = [{**r, "deleted": True} for r in summary.results]
                summary.save()
                console.print()
                expected_mb = sum(r["size_mb"] for r in summary.results)
                body = f"[bold green]{t(config, 'done')}[/]\n\n{t(config, 'space_freed')}: [bold]{format_size_mb(freed)}[/]\n{t(config, 'folders_deleted')}: [bold]{total}[/]"
                if freed < expected_mb - 0.1:
                    body += f"\n[dim]{t(config, 'freed_less_note', format_size_mb(expected_mb - freed))}[/]"
                console.print(
                    Panel(
                        body,
                        title=t(config, "result_title"),
                        border_style="green",
                        box=box.ROUNDED,
                    )
                )
                console.print(f"[dim]{t(config, 'marker_note')}[/]")
                wait_enter(config)
        except (KeyboardInterrupt, EOFError):
            console.print(f"[dim]{t(config, 'cancelled')}[/]")


def run_history(config: Config) -> None:
    console.print()
    runs = RunSummary.load_all()
    if not runs:
        console.print(f"[dim]{t(config, 'history_empty')}[/]")
        return
    total_freed_mb = sum(r["total_freed_mb"] for r in runs)
    run_count = len(runs)
    table = Table(
        title=f"{t(config, 'history_title')} — {t(config, 'history_total_freed')}: {format_size_mb(total_freed_mb)} ({run_count} {t(config, 'history_runs')})",
        box=box.ROUNDED,
        header_style="bold cyan",
    )
    table.add_column(t(config, "col_date"), style="dim", width=20)
    table.add_column(t(config, "col_type_run"), width=10)
    table.add_column(t(config, "col_items"), justify="right", width=8)
    table.add_column(t(config, "col_freed"), justify="right", width=12)
    for r in runs[:25]:
        run_type_label = f"[dim]{t(config, 'type_dry')}[/]" if r["dry_run"] else f"[green]{t(config, 'type_clean')}[/]"
        table.add_row(r["timestamp"], run_type_label, str(len(r["results"])), format_size_mb(r["total_freed_mb"]))
    console.print(table)


def _open_config_in_editor(config: Config) -> bool:
    """Open config.toml with $EDITOR or nano. Return True if opened."""
    from simple_dev_cleaner._config import CONFIG_FILE
    editor = os.environ.get("EDITOR", "nano").strip()
    path = str(CONFIG_FILE)
    if not CONFIG_FILE.exists():
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        Config.load().save()
    try:
        parts = shlex.split(editor) or [editor]
        subprocess.run(parts + [path], check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def run_settings(config: Config) -> None:
    n = len(config.scan_dirs)
    lang_label = "Spanish" if config.lang == "es" else "English"
    config_choices = ["0", "1", "2", "3", "4", "5", "6"]
    while True:
        console.print(f"\n[bold]{t(config, 'config_title')}[/]")
        if sys.stdin.isatty():
            config_menu_choices = [
                Choice(t(config, "config_1"), value="1"),
                Choice(t(config, "config_2"), value="2"),
                Choice(t(config, "config_3"), value="3"),
                Choice(t(config, "config_4", config.unused_hours), value="4"),
                Choice(t(config, "config_5", lang_label), value="5"),
                Choice(t(config, "config_6"), value="6"),
                Choice(t(config, "config_0"), value="0"),
            ]
            try:
                op = select(
                    t(config, "config_prompt"),
                    choices=config_menu_choices,
                    use_shortcuts=False,
                    instruction="",
                ).ask()
                op = op if op is not None else "0"
            except (KeyboardInterrupt, EOFError):
                op = "0"
        else:
            try:
                raw = (Prompt.ask(t(config, "config_prompt"), default="0") or "0").strip()
                op = _normalize_choice(raw, config_choices)
            except Exception:
                op = "0"
        if op == "0":
            break
        if op == "1":
            console.print()
            if not config.scan_dirs:
                console.print(f"[dim]{t(config, 'no_folders_configured')}[/]")
            else:
                console.print(f"[dim]{t(config, 'folders_list')}:[/]")
                for i, d in enumerate(config.scan_dirs, 1):
                    exists = (
                        f"[green]✓ {t(config, 'exists')}[/]"
                        if Path(d).is_dir()
                        else f"[red]{t(config, 'not_exists')}[/]"
                    )
                    short = d.replace(str(Path.home()), "~")
                    console.print(f"  [cyan]{i}.[/] {short}  {exists}")
            console.print()
        elif op == "2":
            path_input = (Prompt.ask(t(config, "path_prompt")) or "").strip()
            if not path_input:
                console.print(f"[yellow]{t(config, 'path_empty')}[/]")
                continue
            if path_input.lower() == "q":
                continue
            # Multiple paths separated by comma (or newline if pasting several)
            parts = [p.strip() for p in path_input.replace("\n", ",").split(",") if p.strip()]
            added = 0
            skipped = 0
            for part in parts:
                if part.lower() == "q":
                    break
                path = Path(part).expanduser().resolve()
                if not path.exists() or not path.is_dir():
                    skipped += 1
                    continue
                if str(path) in config.scan_dirs:
                    skipped += 1
                    continue
                config.scan_dirs.append(str(path))
                added += 1
            if added > 0:
                config.save()
                if added == 1 and skipped == 0:
                    console.print(f"[green]{t(config, 'path_added')}[/]")
                else:
                    console.print(f"[green]{t(config, 'paths_added', added)}[/]", end="")
                    if skipped > 0:
                        console.print(f"[dim]{t(config, 'paths_skipped', skipped)}[/]")
                    else:
                        console.print()
            elif skipped > 0:
                console.print(f"[yellow]{t(config, 'path_already')}[/]")
            else:
                console.print(f"[red]{t(config, 'path_not_found')}[/]")
        elif op == "3":
            if not config.scan_dirs:
                console.print(f"[dim]{t(config, 'no_folders_configured')}[/]")
                continue
            remove_choices = [
                Choice(
                    f"{i}. {d.replace(str(Path.home()), '~')}",
                    value=i - 1,
                )
                for i, d in enumerate(config.scan_dirs, 1)
            ]
            remove_choices.append(Choice(t(config, "which_remove_cancel"), value=-1))
            try:
                if sys.stdin.isatty():
                    idx = select(
                        t(config, "which_remove"),
                        choices=remove_choices,
                        use_shortcuts=False,
                        instruction="",
                    ).ask()
                    idx = idx if idx is not None else -1
                else:
                    console.print()
                    for i, d in enumerate(config.scan_dirs, 1):
                        short = d.replace(str(Path.home()), "~")
                        console.print(f"  [cyan]{i}.[/] {short}")
                    console.print()
                    raw = (Prompt.ask(t(config, "which_remove") + " " + t(config, "hint_q_cancel"), default="0") or "0").strip()
                    if raw.lower() == "q":
                        continue
                    idx = int(raw) - 1 if raw.isdigit() else -1
            except (KeyboardInterrupt, EOFError, ValueError):
                continue
            if 0 <= idx < len(config.scan_dirs):
                config.scan_dirs.pop(idx)
                config.save()
                n = len(config.scan_dirs)
                console.print(f"[green]{t(config, 'removed_from_list')}[/]")
        elif op == "4":
            try:
                raw = (
                    Prompt.ask(
                        t(config, "hours_prompt", config.unused_hours),
                        default=str(config.unused_hours),
                    )
                    or str(config.unused_hours)
                ).strip()
                h = int(raw)
            except ValueError:
                console.print(f"[red]{t(config, 'hours_invalid')}[/]")
                continue
            if 1 <= h <= 8760:
                config.unused_hours = h
                config.save()
                console.print(f"[green]{t(config, 'hours_saved', h)}[/]")
            else:
                console.print(f"[red]{t(config, 'hours_invalid')}[/]")
        elif op == "5":
            console.print()
            console.print(f"[dim]{t(config, 'lang_current')}: {lang_label}[/]")
            try:
                if sys.stdin.isatty():
                    choice = select(
                        t(config, "lang_choose"),
                        choices=[
                            Choice("Español", value="1"),
                            Choice("English", value="2"),
                        ],
                        use_shortcuts=False,
                        instruction="",
                    ).ask()
                    choice = choice if choice is not None else "1"
                else:
                    choice = (Prompt.ask(t(config, "lang_prompt"), default="1") or "1").strip()
            except Exception:
                choice = "1"
            if choice == "2":
                config.lang = "en"
                config.save()
                console.print(f"[green]{t(config, 'lang_saved_en')}[/]")
            else:
                config.lang = "es"
                config.save()
                console.print(f"[green]{t(config, 'lang_saved_es')}[/]")
            lang_label = "English" if config.lang == "en" else "Spanish"
        elif op == "6":
            console.print()
            console.print(f"[dim]{t(config, 'edit_config')}[/]")
            if _open_config_in_editor(config):
                try:
                    config = Config.load()
                    console.print(f"[green]{t(config, 'edit_done')}[/]")
                except Exception:
                    pass
            else:
                console.print(f"[red]{t(config, 'edit_fail')}[/]")


def main() -> None:
    from simple_dev_cleaner._config import HISTORY_FILE

    config = Config.load()
    if not getattr(config, "lang", "").strip():
        config.lang = "es"
        config.save()

    print_banner(config)

    if not HISTORY_FILE.exists():
        console.print(t(config, "first_run_tip"))
        console.print()

    # Check updates: Check → Downloading → Updated
    try:
        with console.status(f"[dim]{t(config, 'check_updates')}[/]", spinner="dots") as status:
            status.update(status=f"[dim]{t(config, 'downloading')}[/]")
            updated = run_update()
        if updated:
            console.print(f"[green]{t(config, 'updated')}[/]")
    except Exception:
        pass

    while True:
        option = main_menu(config)
        if option == "0":
            console.print(f"[dim]{t(config, 'bye')}[/]")
            break
        try:
            if option == "1":
                run_dry_run(config)
            elif option == "2":
                run_history(config)
            elif option == "3":
                run_settings(config)
                config = Config.load()
        except KeyboardInterrupt:
            console.print(f"\n[dim]{t(config, 'interrupted')}[/]")
        except Exception as e:
            console.print(f"[red]{t(config, 'error_unexpected')}: {e}[/]")
            console.print(f"[dim]{t(config, 'error_hint')}[/]")


if __name__ == "__main__":
    main()
