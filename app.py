"""DevCleaner — GUI principal."""

import json
import os
import shutil
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from cleaner import (
    Config, RunSummary, scan,
    install_agent, uninstall_agent, is_agent_installed,
)
from system_info import get_system_info

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

APP_DIR = Path(__file__).parent
WIDGET_SRC = APP_DIR / "widget" / "DevCleaner.widget"
UBERSICHT_DIR = Path.home() / "Library" / "Application Support" / "Übersicht" / "widgets"


class DevCleanerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("DevCleaner")
        self.geometry("920x700")
        self.minsize(800, 600)

        self.config = Config.load()
        self.sysinfo = {}

        self._build_ui()
        self._load_sysinfo_async()
        self._refresh_last_run()
        self._refresh_agent_status()

    # ── Layout ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()

        self.tabview = ctk.CTkTabview(self, corner_radius=12)
        self.tabview.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="nsew")

        self._build_tab_dashboard()
        self._build_tab_settings()
        self._build_tab_history()

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header, text="DevCleaner", font=ctk.CTkFont(size=28, weight="bold")
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            header, text="Limpiador automático de dependencias",
            font=ctk.CTkFont(size=13), text_color="gray"
        ).grid(row=1, column=0, sticky="w")

        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.grid(row=0, column=2, rowspan=2, sticky="e")

        self.btn_scan = ctk.CTkButton(
            btn_frame, text="⏱ Dry Run", width=120,
            fg_color="#2d5a27", hover_color="#3d7a37",
            command=lambda: self._run_clean(dry_run=True)
        )
        self.btn_scan.pack(side="left", padx=4)

        self.btn_clean = ctk.CTkButton(
            btn_frame, text="🧹 Limpiar", width=120,
            fg_color="#8b2020", hover_color="#a83232",
            command=lambda: self._run_clean(dry_run=False)
        )
        self.btn_clean.pack(side="left", padx=4)

    # ── Tab: Dashboard ──────────────────────────────────────────────────────

    def _build_tab_dashboard(self):
        tab = self.tabview.add("Dashboard")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=1)

        # System info card
        self.sys_frame = ctk.CTkFrame(tab, corner_radius=12)
        self.sys_frame.grid(row=0, column=0, padx=8, pady=8, sticky="nsew")

        ctk.CTkLabel(
            self.sys_frame, text="Sistema",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(padx=16, pady=(12, 4), anchor="w")

        self.sys_labels: dict[str, ctk.CTkLabel] = {}
        for key, label in [
            ("chip", "Chip"), ("arch", "Arquitectura"), ("ram", "RAM"),
            ("macos", "macOS"), ("hostname", "Hostname"),
            ("disk_total", "Disco Total"), ("disk_used", "Usado"),
            ("disk_free", "Libre"),
        ]:
            row = ctk.CTkFrame(self.sys_frame, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=1)
            ctk.CTkLabel(row, text=f"{label}:", width=100, anchor="w",
                         text_color="gray").pack(side="left")
            lbl = ctk.CTkLabel(row, text="...", anchor="w")
            lbl.pack(side="left", fill="x", expand=True)
            self.sys_labels[key] = lbl

        self.disk_progress = ctk.CTkProgressBar(self.sys_frame, height=8)
        self.disk_progress.pack(padx=16, pady=(4, 12), fill="x")
        self.disk_progress.set(0)

        # Last run card
        self.last_frame = ctk.CTkFrame(tab, corner_radius=12)
        self.last_frame.grid(row=0, column=1, padx=8, pady=8, sticky="nsew")

        ctk.CTkLabel(
            self.last_frame, text="Última limpieza",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(padx=16, pady=(12, 4), anchor="w")

        self.last_info = ctk.CTkLabel(
            self.last_frame, text="Sin datos aún", anchor="nw",
            justify="left", wraplength=350
        )
        self.last_info.pack(padx=16, pady=4, fill="both", expand=True, anchor="nw")

        # Results area
        self.results_frame = ctk.CTkFrame(tab, corner_radius=12)
        self.results_frame.grid(row=1, column=0, columnspan=2, padx=8, pady=8, sticky="nsew")
        tab.grid_rowconfigure(1, weight=1)

        results_header = ctk.CTkFrame(self.results_frame, fg_color="transparent")
        results_header.pack(fill="x", padx=16, pady=(12, 4))

        ctk.CTkLabel(
            results_header, text="Resultados",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")

        self.status_label = ctk.CTkLabel(
            results_header, text="", text_color="gray",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(side="right")

        self.results_text = ctk.CTkTextbox(
            self.results_frame, corner_radius=8, font=ctk.CTkFont(family="SF Mono", size=12),
            state="disabled", height=200
        )
        self.results_text.pack(padx=16, pady=(0, 12), fill="both", expand=True)

    # ── Tab: Settings ───────────────────────────────────────────────────────

    def _build_tab_settings(self):
        tab = self.tabview.add("Configuración")
        tab.grid_columnconfigure(0, weight=1)

        # Scan dirs
        dirs_frame = ctk.CTkFrame(tab, corner_radius=12)
        dirs_frame.grid(row=0, column=0, padx=8, pady=8, sticky="nsew")
        tab.grid_rowconfigure(0, weight=1)

        dirs_header = ctk.CTkFrame(dirs_frame, fg_color="transparent")
        dirs_header.pack(fill="x", padx=16, pady=(12, 4))

        ctk.CTkLabel(
            dirs_header, text="Carpetas a monitorear",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")

        ctk.CTkButton(
            dirs_header, text="+ Agregar", width=100, height=28,
            font=ctk.CTkFont(size=12), command=self._add_dir
        ).pack(side="right")

        self.dirs_list_frame = ctk.CTkScrollableFrame(dirs_frame, corner_radius=8)
        self.dirs_list_frame.pack(padx=16, pady=(4, 12), fill="both", expand=True)

        self._refresh_dirs_list()

        # Timing
        timing_frame = ctk.CTkFrame(tab, corner_radius=12)
        timing_frame.grid(row=1, column=0, padx=8, pady=8, sticky="ew")

        ctk.CTkLabel(
            timing_frame, text="Temporización",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(padx=16, pady=(12, 8), anchor="w")

        sliders_frame = ctk.CTkFrame(timing_frame, fg_color="transparent")
        sliders_frame.pack(padx=16, pady=(0, 12), fill="x")
        sliders_frame.grid_columnconfigure(1, weight=1)

        # Interval
        ctk.CTkLabel(sliders_frame, text="Intervalo de limpieza:").grid(row=0, column=0, sticky="w", pady=4)
        self.interval_var = tk.IntVar(value=self.config.interval_hours)
        self.interval_label = ctk.CTkLabel(sliders_frame, text=f"{self.config.interval_hours}h")
        self.interval_label.grid(row=0, column=2, padx=(8, 0))

        interval_slider = ctk.CTkSlider(
            sliders_frame, from_=1, to=72, number_of_steps=71,
            variable=self.interval_var, command=self._on_interval_change
        )
        interval_slider.grid(row=0, column=1, sticky="ew", padx=8)

        # Unused threshold
        ctk.CTkLabel(sliders_frame, text="Umbral sin uso:").grid(row=1, column=0, sticky="w", pady=4)
        self.unused_var = tk.IntVar(value=self.config.unused_hours)
        self.unused_label = ctk.CTkLabel(sliders_frame, text=f"{self.config.unused_hours}h")
        self.unused_label.grid(row=1, column=2, padx=(8, 0))

        unused_slider = ctk.CTkSlider(
            sliders_frame, from_=6, to=168, number_of_steps=162,
            variable=self.unused_var, command=self._on_unused_change
        )
        unused_slider.grid(row=1, column=1, sticky="ew", padx=8)

        # Agent + Widget buttons
        actions_frame = ctk.CTkFrame(tab, corner_radius=12)
        actions_frame.grid(row=2, column=0, padx=8, pady=8, sticky="ew")

        ctk.CTkLabel(
            actions_frame, text="Acciones",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(padx=16, pady=(12, 8), anchor="w")

        btns = ctk.CTkFrame(actions_frame, fg_color="transparent")
        btns.pack(padx=16, pady=(0, 12), fill="x")

        self.agent_btn = ctk.CTkButton(
            btns, text="...", width=200, command=self._toggle_agent
        )
        self.agent_btn.pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btns, text="📌 Instalar Widget", width=200,
            fg_color="#4a4a8a", hover_color="#5a5a9a",
            command=self._install_widget
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btns, text="💾 Guardar Config", width=160,
            fg_color="#2d5a27", hover_color="#3d7a37",
            command=self._save_config
        ).pack(side="right")

    # ── Tab: History ────────────────────────────────────────────────────────

    def _build_tab_history(self):
        tab = self.tabview.add("Historial")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        self.history_text = ctk.CTkTextbox(
            tab, corner_radius=8, font=ctk.CTkFont(family="SF Mono", size=12),
            state="disabled"
        )
        self.history_text.grid(row=0, column=0, padx=8, pady=8, sticky="nsew")

        ctk.CTkButton(
            tab, text="Refrescar", width=120, command=self._refresh_history
        ).grid(row=1, column=0, pady=(0, 8))

        self._refresh_history()

    # ── Actions ─────────────────────────────────────────────────────────────

    def _run_clean(self, dry_run: bool):
        self.btn_scan.configure(state="disabled")
        self.btn_clean.configure(state="disabled")
        mode = "Escaneando..." if dry_run else "Limpiando..."
        self.status_label.configure(text=mode)

        self.results_text.configure(state="normal")
        self.results_text.delete("1.0", "end")
        self.results_text.configure(state="disabled")

        def worker():
            def on_progress(result):
                status = "SIMULADO" if dry_run else ("OK" if result.deleted else "ERROR")
                line = f"[{status}] {result.path}  ({result.size_mb}MB, {result.unused_hours}h sin uso)\n"
                self.after(0, lambda l=line: self._append_result(l))

            summary = scan(self.config, dry_run=dry_run, progress_cb=on_progress)

            def finish():
                mode_str = "Dry Run" if dry_run else "Limpieza"
                freed = f"{summary.total_freed_mb:.1f}MB" if not dry_run else "0MB (simulación)"
                self.status_label.configure(
                    text=f"{mode_str} completado — {len(summary.results)} items, {freed} liberados"
                )
                if not summary.results:
                    self._append_result("✅ No se encontraron dependencias abandonadas.\n")
                self.btn_scan.configure(state="normal")
                self.btn_clean.configure(state="normal")
                self._refresh_last_run()
                self._refresh_history()
                self._load_sysinfo_async()

            self.after(0, finish)

        threading.Thread(target=worker, daemon=True).start()

    def _append_result(self, text: str):
        self.results_text.configure(state="normal")
        self.results_text.insert("end", text)
        self.results_text.see("end")
        self.results_text.configure(state="disabled")

    def _load_sysinfo_async(self):
        def worker():
            info = get_system_info()
            self.after(0, lambda: self._update_sysinfo(info))
        threading.Thread(target=worker, daemon=True).start()

    def _update_sysinfo(self, info: dict):
        self.sysinfo = info
        for key, lbl in self.sys_labels.items():
            lbl.configure(text=info.get(key, "N/A"))
        self.disk_progress.set(info.get("disk_pct", 0) / 100)

        pct = info.get("disk_pct", 0)
        if pct > 90:
            self.disk_progress.configure(progress_color="#cc3333")
        elif pct > 75:
            self.disk_progress.configure(progress_color="#cc9933")
        else:
            self.disk_progress.configure(progress_color="#33aa55")

    def _refresh_last_run(self):
        last = RunSummary.load_last()
        if not last:
            self.last_info.configure(text="Sin datos aún.\nEjecutá un Dry Run o Limpieza.")
            return

        mode = "🔍 Dry Run" if last["dry_run"] else "🧹 Limpieza"
        n = len(last["results"])
        freed = last["total_freed_mb"]
        ts = last["timestamp"]

        details = [f"{mode}  •  {ts}", f"Items: {n}  •  Liberado: {freed}MB", ""]
        for r in last["results"][:8]:
            icon = "✅" if r["deleted"] else "👁"
            short = r["path"].replace(str(Path.home()), "~")
            details.append(f"{icon} {short}")
            details.append(f"   {r['size_mb']}MB · {r['unused_hours']}h sin uso")
        if n > 8:
            details.append(f"   ... y {n - 8} más")

        self.last_info.configure(text="\n".join(details))

    def _refresh_history(self):
        runs = RunSummary.load_all()
        self.history_text.configure(state="normal")
        self.history_text.delete("1.0", "end")

        if not runs:
            self.history_text.insert("1.0", "Sin historial aún.")
        else:
            total_all = sum(r["total_freed_mb"] for r in runs)
            self.history_text.insert("end", f"Total histórico liberado: {total_all:.1f}MB\n")
            self.history_text.insert("end", f"Total de ejecuciones: {len(runs)}\n")
            self.history_text.insert("end", "─" * 60 + "\n\n")

            for run in runs[:20]:
                mode = "DRY-RUN" if run["dry_run"] else "LIMPIEZA"
                self.history_text.insert(
                    "end",
                    f"[{run['timestamp']}] {mode} — "
                    f"{len(run['results'])} items, {run['total_freed_mb']}MB liberados\n"
                )
                for r in run["results"]:
                    short = r["path"].replace(str(Path.home()), "~")
                    self.history_text.insert(
                        "end", f"  • {short} ({r['size_mb']}MB, {r['unused_hours']}h)\n"
                    )
                self.history_text.insert("end", "\n")

        self.history_text.configure(state="disabled")

    # ── Settings actions ────────────────────────────────────────────────────

    def _refresh_dirs_list(self):
        for widget in self.dirs_list_frame.winfo_children():
            widget.destroy()

        for i, d in enumerate(self.config.scan_dirs):
            row = ctk.CTkFrame(self.dirs_list_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)
            row.grid_columnconfigure(0, weight=1)

            short = d.replace(str(Path.home()), "~")
            exists = Path(d).is_dir()
            color = "white" if exists else "#aa5555"

            ctk.CTkLabel(
                row, text=f"📁 {short}", anchor="w", text_color=color
            ).grid(row=0, column=0, sticky="ew")

            if not exists:
                ctk.CTkLabel(
                    row, text="(no existe)", text_color="#aa5555",
                    font=ctk.CTkFont(size=11)
                ).grid(row=0, column=1, padx=4)

            ctk.CTkButton(
                row, text="✕", width=28, height=28, fg_color="#662222",
                hover_color="#883333", font=ctk.CTkFont(size=12),
                command=lambda idx=i: self._remove_dir(idx)
            ).grid(row=0, column=2, padx=(4, 0))

    def _add_dir(self):
        path = filedialog.askdirectory(title="Seleccionar carpeta a monitorear")
        if path and path not in self.config.scan_dirs:
            self.config.scan_dirs.append(path)
            self._refresh_dirs_list()

    def _remove_dir(self, index: int):
        if 0 <= index < len(self.config.scan_dirs):
            self.config.scan_dirs.pop(index)
            self._refresh_dirs_list()

    def _on_interval_change(self, value):
        v = int(value)
        self.interval_label.configure(text=f"{v}h")
        self.config.interval_hours = v

    def _on_unused_change(self, value):
        v = int(value)
        self.unused_label.configure(text=f"{v}h")
        self.config.unused_hours = v

    def _save_config(self):
        self.config.save()
        if is_agent_installed():
            install_agent(self.config)
        messagebox.showinfo("DevCleaner", "Configuración guardada.")

    def _toggle_agent(self):
        if is_agent_installed():
            uninstall_agent()
        else:
            install_agent(self.config)
            self.config.save()
        self._refresh_agent_status()

    def _refresh_agent_status(self):
        if is_agent_installed():
            self.agent_btn.configure(
                text="⏹ Desinstalar Agente",
                fg_color="#8b2020", hover_color="#a83232"
            )
        else:
            self.agent_btn.configure(
                text="▶ Instalar Agente",
                fg_color="#2d5a27", hover_color="#3d7a37"
            )

    # ── Widget ──────────────────────────────────────────────────────────────

    def _install_widget(self):
        if not UBERSICHT_DIR.parent.exists():
            answer = messagebox.askyesno(
                "Übersicht no encontrado",
                "Übersicht no está instalado.\n\n"
                "Es necesario para mostrar widgets en el escritorio.\n"
                "¿Querés instalarlo con Homebrew?\n\n"
                "  brew install --cask ubersicht"
            )
            if answer:
                os.system("brew install --cask ubersicht &")
                messagebox.showinfo(
                    "Instalando",
                    "Se está instalando Übersicht en segundo plano.\n"
                    "Cuando termine, volvé a hacer clic en 'Instalar Widget'."
                )
            return

        dest = UBERSICHT_DIR / "DevCleaner.widget"
        try:
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(WIDGET_SRC, dest)
            messagebox.showinfo(
                "Widget instalado",
                "Widget instalado correctamente.\n"
                "Abrí Übersicht para verlo en el escritorio."
            )
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo instalar el widget:\n{e}")


if __name__ == "__main__":
    app = DevCleanerApp()
    app.mainloop()
