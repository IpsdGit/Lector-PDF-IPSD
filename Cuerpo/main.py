"""
=============================================================================
LECTOR DE PDFs - VERSIÓN 3.0
Instituto de Profesionalización y Superación Docente - UNAH
=============================================================================

Características V3:
- ✅ Sistema de 4 capas de verificación (hash → fuzzy → semántica → manual)
- ✅ UI profesional con CustomTkinter (Material Design)
- ✅ Sistema de metadata JSON para auditoría completa
- ✅ Manejo robusto de errores OCR
- ✅ Logging detallado de todas las operaciones
- ✅ Ventana modal para verificación manual de duplicados
- ✅ Preservación de documentos (no elimina sin confirmación)
- ✅ Branding institucional UNAH/VRA

Autor: Lector V3 Team
Fecha: Marzo 2026
"""

import os
import re
import sys
import json
import logging
import shutil
import threading
import time
import unicodedata
from datetime import datetime
from pathlib import Path
from queue import Queue
from typing import Dict, List, Tuple, Optional
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

# Importaciones para procesamiento PDF y OCR
try:
    import pytesseract
    from pdf2image import convert_from_path
    from fuzzywuzzy import fuzz
    from PIL import Image, ImageTk
    from PyPDF2 import PdfReader, PdfWriter
except ImportError as e:
    print(f"❌ ERROR: Falta instalar dependencia: {e}")
    print("   Ejecuta: .\\venv\\Scripts\\python.exe -m pip install -r requirements.txt")
    sys.exit(1)

# Importaciones para UI
try:
    import customtkinter as ctk
except ImportError as e:
    print(f"❌ ERROR: Falta instalar customtkinter: {e}")
    sys.exit(1)

# Importaciones de módulos locales
from config import (
    BASE_DIR_CUERPO, BASE_DIR_RAIZ, TESSERACT_PATH, POPPLER_PATH, ASSETS_PATH,
    COLOR_AZUL_IPSD, COLOR_VERDE_IPSD, COLOR_BLANCO, COLOR_GRIS_FONDO, COLOR_GRIS_TEXTO,
    TIPOS_PREDEFINIDOS, SIGLAS_DOCUMENTO, TIPOS_PRINCIPALES, TIPOS_ADJUNTOS
)
from core.pdf_logic import (
    calcular_hash_md5, guardar_metadata, detectar_tipo_documento,
    buscar_numero_documento, buscar_departamento, buscar_fecha,
    generar_nombre_limpio, extraer_paginas_por_tipo, detectar_cambios_tipo_pdf,
    fusionar_pdf_anexo
)
from core.ocr_engine import (
    extraer_texto_ocr, extraer_texto_ocr_pagina, _miniatura_pdf
)
from ui.modals import (
    _set_app_icon, _abrir_zoom_pdf, _abrir_calendario,
    VentanaConsultaSeparacion, VentanaVerificacion, VentanaNumDuplicado
)

# =============================================================================
# SISTEMA DE LOGGING
# =============================================================================

def configurar_logging(carpeta_salida: Path) -> logging.Logger:
    """
    Configura el sistema de logging con archivo y consola.
    
    Args:
        carpeta_salida: Carpeta donde guardar los logs
        
    Returns:
        Logger configurado
    """
    log_dir = carpeta_salida / "logs"
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"lector_{timestamp}.log"
    
    # Crear logger
    logger = logging.getLogger("LectorV3")
    logger.setLevel(logging.DEBUG)
    
    # Handler para archivo (todo)
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    
    # Handler para consola (info y superior)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    logger.info("="*70)
    logger.info("INICIO DE SESIÓN - LECTOR V3")
    logger.info(f"Log guardado en: {log_file}")
    logger.info("="*70)
    
    return logger


# =============================================================================
# CLASE: PANTALLA PROCESAMIENTO PRINCIPAL
# =============================================================================

class PantallaProcesamiento(ctk.CTk):
    """
    Ventana principal de la aplicación con UI profesional CustomTkinter.
    """
    
    def __init__(self):
        super().__init__()
        
        # Configuración ventana principal
        self.title("Lector de PDFs V3.0 - IPSD UNAH")
        self.resizable(True, True)
        self.minsize(800, 680)
        self.configure(fg_color=COLOR_GRIS_FONDO)
        
        # Centrar ventana
        _W, _H = 920, 720
        self.update_idletasks()
        _sw = self.winfo_screenwidth()
        _sh = self.winfo_screenheight()
        _px = (_sw - _W) // 2
        _py = (_sh - _H) // 2
        self.geometry(f"{_W}x{_H}+{_px}+{_py}")
        
        # Variables
        self.carpeta_entrada = None
        self.carpeta_salida = None
        self.logger = None
        self.procesando = False
        self.cola_logs = Queue()
        # StringVar para actualización dinámica de los cards
        self.var_entrada = tk.StringVar()
        self.var_salida = tk.StringVar()
        # Historial de Documentos Principales guardados en sesión actual
        self.historial_principales = []
        
        self._crear_interfaz()
        _set_app_icon(self)
    
    def _strip_bg(self, img, tolerance=45):
        """Elimina el fondo de una imagen PNG."""
        w, h = img.size
        y0, y1 = max(1, int(h * 0.05)), max(2, int(h * 0.15))
        x0, x1 = max(1, int(w * 0.05)), max(2, int(w * 0.15))
        samples = []
        for sy in range(y0, y1):
            for sx in range(x0, x1):
                px = img.getpixel((sx, sy))
                if px[3] > 200:
                    samples.append(px[:3])
        if not samples:
            flat = list(img.getdata())
            samples = [px[:3] for px in flat if px[3] > 100][:1]
        if not samples:
            return img
        br = sum(s[0] for s in samples) // len(samples)
        bg_g = sum(s[1] for s in samples) // len(samples)
        bb = sum(s[2] for s in samples) // len(samples)
        flat = list(img.getdata())
        new = []
        for r, g, b, a in flat:
            if a > 30:
                dist = ((r - br) ** 2 + (g - bg_g) ** 2 + (b - bb) ** 2) ** 0.5
                a = 0 if dist < tolerance else a
            new.append((r, g, b, a))
        out = img.copy()
        out.putdata(new)
        return out
    
    def _crear_interfaz(self):
        """Crea la interfaz completa de la aplicación."""
        
        # ===== 1. HEADER (se empaqueta primero - arriba) =====
        header_frame = ctk.CTkFrame(self, fg_color=COLOR_AZUL_IPSD, corner_radius=0, height=70)
        header_frame.pack(fill="x", padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        # Logo UNAH + VRA (a la izquierda)
        logo_unah_path = ASSETS_PATH / "LOGOS-VRA-DC-UNAH (1).png"
        if logo_unah_path.exists():
            try:
                img_unah = Image.open(logo_unah_path)
                img_unah = img_unah.resize((240, 60), Image.Resampling.LANCZOS)
                self.logo_unah = ctk.CTkImage(light_image=img_unah, dark_image=img_unah, size=(240, 60))
                logo_container = ctk.CTkFrame(header_frame, fg_color="transparent")
                logo_container.pack(side="left", padx=15, pady=5)
                ctk.CTkLabel(logo_container, image=self.logo_unah, text="").pack()
            except Exception as e:
                print(f"Error cargando logo UNAH: {e}")
        
        # Logo App (a la derecha, sin fondo)
        logo_app_path = ASSETS_PATH / "Logo_App.png"
        if logo_app_path.exists():
            try:
                pil_app = Image.open(logo_app_path).convert("RGBA")
                pil_app = self._strip_bg(pil_app, tolerance=60)
                bbox = pil_app.getchannel("A").getbbox()
                if bbox:
                    pil_app = pil_app.crop(bbox)
                ah = 55
                aw = int(ah * pil_app.width / pil_app.height)
                self.logo_app = ctk.CTkImage(light_image=pil_app, dark_image=pil_app, size=(aw, ah))
                logo_app_container = ctk.CTkFrame(header_frame, fg_color="transparent")
                logo_app_container.pack(side="right", padx=20, pady=8)
                ctk.CTkLabel(logo_app_container, image=self.logo_app, text="", fg_color="transparent").pack()
            except Exception as e:
                print(f"Error cargando logo App: {e}")
        
        # ===== 2. TÍTULO =====
        titulo_app_frame = tk.Frame(self, bg="white")
        titulo_app_frame.pack(fill="x", padx=0, pady=0)
        
        tk.Label(
            titulo_app_frame,
            text="Lector de Documentos PDF",
            font=("Segoe UI", 16, "bold"),
            bg="white",
            fg=COLOR_AZUL_IPSD
        ).pack(pady=(10, 3))
        
        tk.Label(
            titulo_app_frame,
            text="Selecciona las carpetas de entrada y salida para procesar los archivos PDF.",
            font=("Segoe UI", 9),
            bg="white",
            fg=COLOR_GRIS_TEXTO
        ).pack(pady=(0, 10))
        
        # ===== 3. FOOTER =====
        footer_frame = tk.Frame(self, bg="white", height=60)
        footer_frame.pack(fill="x", side="bottom")
        footer_frame.pack_propagate(False)
        tk.Frame(footer_frame, bg="#E0E0E0", height=1).pack(fill="x", side="top")
        footer_content = tk.Frame(footer_frame, bg="white")
        footer_content.pack(expand=True)
        tk.Label(footer_content, text="Universidad Nacional Autónoma de Honduras",
                 font=("Segoe UI", 9, "bold"), bg="white", fg="#003671").pack()
        tk.Label(footer_content, text="Vicerrectoría Académica",
                 font=("Segoe UI", 8), bg="white", fg="#888888").pack(pady=(1, 0))
        tk.Label(footer_content, text="Instituto de Profesionalización y Superación Docente",
                 font=("Segoe UI", 8), bg="white", fg="#888888").pack(pady=(1, 0))
        
        # ===== 4. ÁREA CENTRAL =====
        centro_wrapper = tk.Frame(self, bg=COLOR_GRIS_FONDO)
        centro_wrapper.pack(fill="both", expand=True)
        
        contenido_frame = ctk.CTkFrame(centro_wrapper, fg_color=COLOR_GRIS_FONDO)
        contenido_frame.pack(fill="both", expand=True, padx=15, pady=8)
        
        # Título de sección
        cfg_title_frame = tk.Frame(contenido_frame, bg=COLOR_GRIS_FONDO)
        cfg_title_frame.pack(fill="x", padx=8, pady=(0, 4))
        tk.Label(cfg_title_frame, text="📁  CONFIGURACIÓN",
                 font=("Segoe UI", 11, "bold"),
                 bg=COLOR_GRIS_FONDO, fg=COLOR_AZUL_IPSD).pack(side="left")
        tk.Label(cfg_title_frame,
                 text="Selecciona las carpetas de origen y destino para los PDFs",
                 font=("Segoe UI", 8),
                 bg=COLOR_GRIS_FONDO, fg="#888888").pack(side="left", padx=(8, 0))

        # Grid de 2 cards
        cards_frame = tk.Frame(contenido_frame, bg=COLOR_GRIS_FONDO)
        cards_frame.pack(fill="x", padx=8, pady=(0, 6))
        cards_frame.grid_columnconfigure(0, weight=1)
        cards_frame.grid_columnconfigure(1, weight=1)

        self.card_entrada = self._crear_card_carpeta(
            cards_frame, 0,
            "Carpeta de Entrada", "PDFs a procesar (originales)",
            self.var_entrada, self._seleccionar_entrada,
            lambda: setattr(self, 'carpeta_entrada', None)
        )
        self.card_salida = self._crear_card_carpeta(
            cards_frame, 1,
            "Carpeta de Salida", "Destino de PDFs renombrados",
            self.var_salida, self._seleccionar_salida,
            lambda: setattr(self, 'carpeta_salida', None)
        )
        # Animación de entrada de los cards
        self.after(120, self._animate_cards_entrance)
        
        # --- Estado del proceso ---
        estado_frame = ctk.CTkFrame(contenido_frame, fg_color="white", corner_radius=10,
                                    border_width=1, border_color="#E0E0E0")
        estado_frame.pack(fill="both", expand=True, padx=8, pady=(0, 6))
        
        ctk.CTkLabel(estado_frame, text="📊  ESTADO DEL PROCESO",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=COLOR_AZUL_IPSD, fg_color="white", anchor="w"
        ).pack(fill="x", padx=10, pady=(8, 4))
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(estado_frame, height=16,
                                               progress_color="#FFC107", fg_color="#E0E0E0")
        self.progress_bar.pack(fill="x", padx=10, pady=(0, 4))
        self.progress_bar.set(0)
        
        # Label estado
        self.estado_label = ctk.CTkLabel(estado_frame, text="Esperando configuración...",
                                         font=ctk.CTkFont(size=10), text_color=COLOR_GRIS_TEXTO,
                                         fg_color="white")
        self.estado_label.pack(padx=10, pady=(0, 6))

        # Botones
        botones_frame = tk.Frame(estado_frame, bg="white")
        botones_frame.pack(pady=(0, 8))

        self.btn_procesar = ctk.CTkButton(
            botones_frame, text="▶  Iniciar Procesamiento",
            command=self._iniciar_procesamiento,
            height=44, width=220, font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#B0B0B0", hover_color="#A0A0A0", text_color="#707070",
            corner_radius=22, border_width=0, state="disabled"
        )
        self.btn_procesar.pack(side="left", padx=6)

        self.btn_limpiar = ctk.CTkButton(
            botones_frame, text="🔄  Limpiar Campos",
            command=self._limpiar_campos,
            height=44, width=155, font=ctk.CTkFont(size=12),
            fg_color="#FFFFFF", hover_color="#EBF3FF", text_color="#003671",
            border_width=2, border_color="#003671", corner_radius=22
        )
        self.btn_limpiar.pack(side="left", padx=6)
        
        # Consola
        consola_container = ctk.CTkFrame(estado_frame, fg_color="white", corner_radius=8,
                                         border_width=1, border_color="#E0E0E0")
        consola_container.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        
        consola_header = tk.Frame(consola_container, bg="white")
        consola_header.pack(fill="x", padx=10, pady=(7, 4))
        header_left = tk.Frame(consola_header, bg="white")
        header_left.pack(side="left")
        icon_box = tk.Frame(header_left, bg="#F0F0F0", width=24, height=24)
        icon_box.pack(side="left", padx=(0, 6))
        icon_box.pack_propagate(False)
        tk.Label(icon_box, text=">", font=("Consolas", 11, "bold"), bg="#F0F0F0",
                 fg=COLOR_AZUL_IPSD).place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(header_left, text="Consola de Procesos", font=("Segoe UI", 10, "bold"),
                 bg="white", fg="#333333").pack(side="left")
        
        consola_content = tk.Frame(consola_container, bg="white")
        consola_content.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        
        console_inner = tk.Frame(consola_content, bg="#2B2B2B")
        console_inner.pack(fill="both", expand=True)
        
        console_titlebar = tk.Frame(console_inner, bg="#1C1F2E", height=18)
        console_titlebar.pack(fill="x")
        console_titlebar.pack_propagate(False)
        tk.Label(console_titlebar, text=">_  IPSD Console", font=("Consolas", 9),
                 bg="#1C1F2E", fg="#7AADCA", padx=6).pack(side="left", fill="y")
        
        tk.Frame(console_inner, bg="#2A2D3E", height=1).pack(fill="x")
        
        self.consola = scrolledtext.ScrolledText(
            console_inner, height=20, bg="#2B2B2B", fg="white",
            insertbackground=COLOR_VERDE_IPSD, font=("Consolas", 11),
            relief="flat", bd=0, padx=10, pady=10, wrap="word",
            selectbackground="#264F78", selectforeground="#FFFFFF"
        )
        self.consola.pack(fill="both", expand=True)
        
        self.consola.tag_config("timestamp", foreground="#8888AA")
        self.consola.tag_config("info", foreground="#FFFFFF")
        self.consola.tag_config("success", foreground=COLOR_VERDE_IPSD)
        self.consola.tag_config("warning", foreground="#FFC107")
        self.consola.tag_config("error", foreground="#FF5555")
        self.consola.configure(state="disabled")
        self._log_consola("Sistema listo. Selecciona las carpetas de entrada y salida.", "info")
        
        # Actualizar consola
        self._actualizar_consola()
    
    def _crear_card_carpeta(self, parent, col, titulo, subtitulo, var, browse_cmd, clear_path_cmd):
        """Crea una tarjeta de selección de carpeta con ícono, hover y display del estado."""
        outer = tk.Frame(parent, bg=COLOR_GRIS_FONDO)
        outer.grid(row=0, column=col, sticky="nsew",
                   padx=(0, 5) if col == 0 else (5, 0))
        outer.grid_columnconfigure(0, weight=1)

        card = ctk.CTkFrame(outer, fg_color="white", corner_radius=12,
                            border_width=1, border_color="#FFFFFF")
        card.pack(fill="both", expand=True)

        # Encabezado del card
        hdr = tk.Frame(card, bg="white")
        hdr.pack(fill="x", padx=14, pady=(12, 2))
        tk.Label(hdr, text=titulo, font=("Segoe UI", 10, "bold"),
                 bg="white", fg=COLOR_GRIS_TEXTO, anchor="w").pack(side="left")
        tk.Label(card, text=subtitulo, font=("Segoe UI", 8),
                 bg="white", fg="#999999", anchor="w").pack(fill="x", padx=18, pady=(0, 6))

        content = tk.Frame(card, bg="white")
        content.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        # Zona clicable (estado vacío)
        _BG_N = "#F8F9FA"
        _BG_H = "#EBF3FF"

        btn_zone = tk.Frame(content, bg=_BG_N, relief="flat", bd=0,
                            highlightbackground="#E0E0E0", highlightthickness=1,
                            cursor="hand2")
        btn_zone.pack(fill="both", expand=True)

        inner = tk.Frame(btn_zone, bg=_BG_N, cursor="hand2")
        inner.pack(padx=16, pady=20)

        icon_lbl = tk.Label(inner, text="📁", font=("Segoe UI", 28),
                            bg=_BG_N, cursor="hand2")
        icon_lbl.pack()

        text_lbl = tk.Label(inner, text="Seleccionar carpeta",
                            font=("Segoe UI", 8, "underline"),
                            bg=_BG_N, fg=COLOR_AZUL_IPSD, cursor="hand2")
        text_lbl.pack(pady=(5, 0))

        for _w in [btn_zone, inner, icon_lbl, text_lbl]:
            _w.bind("<Button-1>", lambda e: browse_cmd())

        # Hover
        def _hover_on(e):
            if not var.get():
                card.configure(border_color="#13689E", border_width=2)
                for _w in [btn_zone, inner, icon_lbl, text_lbl]:
                    _w.config(bg=_BG_H)
        def _hover_off(e):
            if not var.get():
                card.configure(border_color="#E0E0E0", border_width=1)
                for _w in [btn_zone, inner, icon_lbl, text_lbl]:
                    _w.config(bg=_BG_N)

        for _w in [outer, btn_zone, inner, icon_lbl, text_lbl]:
            _w.bind("<Enter>", _hover_on, add="+")
            _w.bind("<Leave>", _hover_off, add="+")

        # Panel de carpeta seleccionada (oculto inicialmente)
        _CFG = "#EBF3FF"
        _CBDR = "#90B4E8"

        sel_frame = tk.Frame(content, bg="white")
        folder_card = tk.Frame(sel_frame, bg=_CFG, relief="flat", bd=0,
                               highlightbackground=_CBDR, highlightthickness=1)
        folder_card.pack(fill="x", pady=(0, 4))
        folder_inner = tk.Frame(folder_card, bg=_CFG)
        folder_inner.pack(fill="x", padx=10, pady=8)

        tk.Label(folder_inner, text="📁", font=("Segoe UI", 20),
                 bg=_CFG, fg=COLOR_AZUL_IPSD).pack(side="left", padx=(0, 10))

        info_f = tk.Frame(folder_inner, bg=_CFG)
        info_f.pack(side="left", fill="both", expand=True)
        name_lbl = tk.Label(info_f, text="", font=("Segoe UI", 9, "bold"),
                            bg=_CFG, fg=COLOR_AZUL_IPSD, anchor="w", wraplength=200)
        name_lbl.pack(anchor="w")
        tk.Label(info_f, text="✓  Carpeta lista", font=("Segoe UI", 7),
                 bg=_CFG, fg="#005BBB", anchor="w").pack(anchor="w", pady=(2, 0))

        # Botones Cambiar / Quitar
        action_f = tk.Frame(content, bg="white")
        ctk.CTkButton(action_f, text="⟳  Cambiar", command=browse_cmd,
                      font=("Segoe UI", 8), fg_color=COLOR_AZUL_IPSD,
                      hover_color="#002550", text_color="white",
                      corner_radius=8, height=26, width=100).pack(side="left", padx=(0, 6))

        def _quitar():
            clear_path_cmd()
            var.set("")
            self._log_consola("🗑  Carpeta eliminada de la selección", "info")
            self._check_inputs_complete()

        ctk.CTkButton(action_f, text="✕  Quitar", command=_quitar,
                      font=("Segoe UI", 8), fg_color="#F5F5F5",
                      hover_color="#FFCDD2", text_color="#C62828",
                      border_width=1, border_color="#FFCDD2",
                      corner_radius=8, height=26, width=80).pack(side="left")

        # Actualización dinámica por StringVar
        def _update(*args):
            path = var.get()
            if path:
                name_lbl.config(text=Path(path).name)
                btn_zone.pack_forget()
                sel_frame.pack(fill="x")
                action_f.pack(pady=(6, 0))
                card.configure(border_color=COLOR_AZUL_IPSD, border_width=2)
            else:
                sel_frame.pack_forget()
                action_f.pack_forget()
                if not btn_zone.winfo_ismapped():
                    btn_zone.pack(fill="both", expand=True)
                card.configure(border_color="#E0E0E0", border_width=1)

        var.trace_add("write", _update)
        _update()
        return card

    def _animate_cards_entrance(self):
        """Animación de aparición de los cards al abrir la app."""
        steps = ["#FFFFFF", "#EAF1FB", "#D4E4F7", "#BFCFE0", "#D0D4D8", "#E0E0E0"]
        ms = 40
        for i, color in enumerate(steps):
            self.after(i * ms, lambda c=color: self.card_entrada.configure(border_color=c))
        for i, color in enumerate(steps):
            self.after(220 + i * ms, lambda c=color: self.card_salida.configure(border_color=c))

    def _seleccionar_entrada(self):
        """Selecciona la carpeta de entrada."""
        carpeta = filedialog.askdirectory(title="Seleccionar carpeta de entrada (PDFs originales)")
        if carpeta:
            self.carpeta_entrada = Path(carpeta)
            self.var_entrada.set(str(carpeta))
            self._log_consola(f"📄 Carpeta de entrada: {self.carpeta_entrada.name}", "info")
            self._check_inputs_complete()
    
    def _seleccionar_salida(self):
        """Selecciona la carpeta de salida."""
        carpeta = filedialog.askdirectory(title="Seleccionar carpeta de salida (PDFs renombrados)")
        if carpeta:
            self.carpeta_salida = Path(carpeta)
            self.var_salida.set(str(carpeta))
            self._log_consola(f"📁 Carpeta de salida: {self.carpeta_salida.name}", "info")
            # Configurar logging
            self.logger = configurar_logging(self.carpeta_salida)
            self._check_inputs_complete()
    
    def _limpiar_campos(self):
        """Limpia todos los campos y resetea la interfaz."""
        # Resetear variables
        self.carpeta_entrada = None
        self.carpeta_salida = None
        self.logger = None
        self.var_entrada.set("")
        self.var_salida.set("")

        # Limpiar consola
        self.consola.configure(state="normal")
        self.consola.delete("1.0", "end")
        self.consola.configure(state="disabled")
        
        # Resetear progress bar
        self.progress_bar.set(0)
        self.estado_label.configure(text="Esperando configuración...")
        
        self._log_consola("🔄 Campos limpiados - Listo para nueva configuración", "info")
        self._check_inputs_complete()
    
    def _check_inputs_complete(self):
        """Verifica si las carpetas están seleccionadas y habilita/deshabilita el botón."""
        ready = bool(self.carpeta_entrada and self.carpeta_salida)
        if ready:
            self.btn_procesar.configure(
                state="normal",
                fg_color="#FFC107",  # Amarillo institucional
                hover_color="#FFB300",
                text_color=COLOR_BLANCO
            )
            self.btn_limpiar.configure(state="normal")
            self._log_consola("✓ Configuración completa. Listo para procesar.", "success")
        else:
            self.btn_procesar.configure(
                state="disabled",
                fg_color="#B0B0B0",
                hover_color="#A0A0A0",
                text_color="#707070"
            )
    
    def _log_consola(self, mensaje: str, tag: str = "info"):
        """Añade un mensaje a la cola de logs para mostrar en consola con timestamp."""
        self.cola_logs.put((mensaje, tag))
    
    def _actualizar_consola(self):
        """Actualiza la consola con nuevos mensajes de la cola con timestamps."""
        try:
            while not self.cola_logs.empty():
                mensaje, tag = self.cola_logs.get_nowait()
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                self.consola.configure(state="normal")
                self.consola.insert("end", f" [{timestamp}] ", "timestamp")
                self.consola.insert("end", f"{mensaje}\n", tag)
                self.consola.see("end")
                self.consola.configure(state="disabled")
        except:
            pass
        
        # Programar siguiente actualización
        self.after(100, self._actualizar_consola)
    
    def _iniciar_procesamiento(self):
        """Inicia el procesamiento de PDFs en un hilo separado."""
        
        # Validaciones
        if not self.carpeta_entrada or not self.carpeta_salida:
            messagebox.showerror(
                "Configuración incompleta", 
                "Debes seleccionar ambas carpetas (entrada y salida)."
            )
            return
        
        # Validación: Carpetas no deben ser la misma
        if self.carpeta_entrada.resolve() == self.carpeta_salida.resolve():
            messagebox.showerror(
                "Error de configuración",
                "Las carpetas de entrada y salida no pueden ser la misma.\n\n"
                "Selecciona carpetas diferentes para evitar sobrescribir archivos."
            )
            return
        
        # Validación: Carpeta de entrada debe existir
        if not self.carpeta_entrada.exists():
            messagebox.showerror(
                "Error",
                f"La carpeta de entrada no existe:\n{self.carpeta_entrada}"
            )
            return
        
        # Validación: Verificar que haya PDFs en la carpeta de entrada
        pdfs_encontrados = list(self.carpeta_entrada.glob("*.pdf"))
        if not pdfs_encontrados:
            messagebox.showwarning(
                "Carpeta vacía",
                f"No se encontraron archivos PDF en la carpeta de entrada:\n"
                f"{self.carpeta_entrada}\n\n"
                f"Verifica que la carpeta contenga archivos .pdf"
            )
            return
        
        # Validación: Carpeta de salida - crear si no existe
        if not self.carpeta_salida.exists():
            respuesta = messagebox.askyesno(
                "Crear carpeta",
                f"La carpeta de salida no existe:\n{self.carpeta_salida}\n\n"
                f"¿Deseas crearla?"
            )
            if respuesta:
                try:
                    self.carpeta_salida.mkdir(parents=True, exist_ok=True)
                    self._log_consola(f"✓ Carpeta de salida creada: {self.carpeta_salida}")
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo crear la carpeta:\n{e}")
                    return
            else:
                return
        
        if self.procesando:
            messagebox.showwarning("Advertencia", "Ya hay un procesamiento en curso.")
            return
        
        # Confirmar inicio
        respuesta = messagebox.askyesno(
            "Confirmar procesamiento",
            f"¿Iniciar procesamiento de PDFs?\n\n"
            f"📂 Entrada: {self.carpeta_entrada}\n"
            f"📂 Salida: {self.carpeta_salida}\n\n"
            f"⚠️ IMPORTANTE:\n"
            f"• Los archivos originales NO se modificarán\n"
            f"• Se consultará antes de omitir duplicados\n"
            f"• Se generarán logs de auditoría\n\n"
            f"¿Continuar?"
        )
        
        if not respuesta:
            return
        
        # Deshabilitar botones
        self.btn_procesar.configure(
            state="disabled", 
            text="⏳ Procesando...",
            fg_color="#FFA726",
            hover_color="#FB8C00",
            text_color=COLOR_BLANCO
        )
        self.btn_limpiar.configure(state="disabled")
        self.procesando = True
        
        # Limpiar consola
        self.consola.configure(state="normal")
        self.consola.delete("1.0", "end")
        self.consola.configure(state="disabled")
        
        # Resetear progress bar
        self.progress_bar.set(0)
        
        # Iniciar procesamiento en hilo separado
        thread = threading.Thread(target=self._procesar_pdfs, daemon=True)
        thread.start()
    
    def _procesar_pdfs(self):
        """Lógica principal de procesamiento con 4 capas de verificación."""
        
        carpeta_temp_seg = None
        try:
            self._log_consola("="*70)
            self._log_consola("INICIO DE PROCESAMIENTO - LECTOR V3")
            self._log_consola("="*70)
            self.logger.info("Iniciando procesamiento...")
            
            # Obtener lista de PDFs
            pdfs_originales = list(self.carpeta_entrada.glob("*.pdf"))
            pdfs = []
            carpeta_temp_seg = self.carpeta_salida / "_temp_segmentos"

            self._log_consola(f"\n🔍 Detectando cambios de tipo en {len(pdfs_originales)} PDF(s)...")
            
            for pdf_original in pdfs_originales:
                self._log_consola(f"  📄 Analizando: {pdf_original.name}", "info")
                self.update()
                
                # Detectar cambios
                resultado = detectar_cambios_tipo_pdf(pdf_original, self.logger)
                necesita_seg = resultado.get('necesita_segmentacion', False)
                puntos_cuest = resultado.get('puntos_cuestionables', [])
                tipos_info = {
                    'tipos': resultado.get('tipos', []),
                    'numeros': resultado.get('numeros', [])
                }
                
                if necesita_seg or puntos_cuest:
                    self._log_consola(
                        f"  ✂️  {pdf_original.name} contiene varios documentos - Preparando segmentación...",
                        "info"
                    )
                    
                    # Procesar puntos cuestionables
                    decisiones_usuario = {}
                    if puntos_cuest:
                        self._log_consola(
                            f"  ❓ {len(puntos_cuest)} punto(s) requieren verificación manual",
                            "info"
                        )
                        self.update()
                        
                        for idx, punto in enumerate(puntos_cuest, 1):
                            self._log_consola(
                                f"    Mostrando ventana de decisión {idx}/{len(puntos_cuest)}...",
                                "info"
                            )
                            self.update()
                            
                            try:
                                pag_ant = punto['pag_anterior'] + 1
                                pag_act = punto['pag_actual'] + 1
                                
                                ventana = VentanaConsultaSeparacion(
                                    self,
                                    pdf_original,
                                    punto['tipo'],
                                    pag_ant,
                                    pag_act,
                                    modo_lista=bool(punto.get('es_caso_lista'))
                                )
                                decision = ventana.obtener_decision()
                                
                                if decision:
                                    key = (punto['pag_anterior'], punto['pag_actual'])
                                    decisiones_usuario[key] = decision
                                    decision_txt = {
                                        'diferente': 'SEPARAR',
                                        'mismo': 'MANTENER',
                                        'anexar_anterior': 'ANEXAR AL ANTERIOR',
                                        'nueva_lista': 'NUEVA LISTA',
                                        'unir_lista_anterior': 'UNIR A LISTA ANTERIOR',
                                    }.get(decision, decision.upper())
                                    self._log_consola(f"      → {decision_txt}", "info")
                                else:
                                    key = (punto['pag_anterior'], punto['pag_actual'])
                                    if punto.get('es_caso_lista'):
                                        decisiones_usuario[key] = "nueva_lista"
                                    else:
                                        decisiones_usuario[key] = "mismo"
                                    self._log_consola(f"      → Predeterminado aplicado", "info")
                            except Exception as e:
                                self.logger.error(f"❌ Error en ventana de consulta: {e}")
                                self._log_consola(f"      ❌ Error: {e}", "error")
                                continue
                    
                    # Segmentar
                    segmentos = extraer_paginas_por_tipo(
                        pdf_original, self.logger, carpeta_temp_seg,
                        tipos_info=tipos_info,
                        decisiones_usuario=decisiones_usuario
                    )
                    self._log_consola(f"  ✅ Se crearon {len(segmentos)} segmento(s)", "info")
                    pdfs.extend(segmentos)
                else:
                    self._log_consola(f"  ⏭️  Tipo uniforme - Sin segmentación necesaria", "info")
                    pdfs.append(pdf_original)

            total_pdfs = len(pdfs)
            
            self._log_consola(f"\n📄 {total_pdfs} archivos PDF encontrados")
            self.logger.info(f"Archivos encontrados: {total_pdfs}")
            
            if total_pdfs == 0:
                self._log_consola("⚠️  No se encontraron archivos PDF en la carpeta de entrada.")
                self.logger.warning("No se encontraron PDFs")
                return
            
            self.estado_label.configure(text=f"Procesando {total_pdfs} archivos...")
            
            # Diccionarios para tracking
            archivos_procesados = {}
            numeros_vistos = {}
            archivos_renombrados = 0
            
            # Procesar cada PDF
            for idx, pdf in enumerate(pdfs, 1):
                progreso = idx / total_pdfs
                self.progress_bar.set(progreso)
                
                self._log_consola(f"\n[{idx}/{total_pdfs}] Procesando: {pdf.name}")
                self.logger.info(f"Procesando [{idx}/{total_pdfs}]: {pdf.name}")
                
                # PASO 1: Extraer texto con OCR
                texto = extraer_texto_ocr(pdf, self.logger)
                
                if not texto or len(texto.strip()) < 50:
                    self._log_consola(f"  ⚠️  OCR sin resultado útil")
                    self.logger.warning(f"OCR insuficiente para {pdf.name}")
                    
                    # Calcular hash para detectar duplicados incluso sin texto
                    hash_md5 = calcular_hash_md5(pdf)
                    
                    # Verificar si es duplicado exacto por hash
                    duplicado_hash = None
                    for nombre, info in archivos_procesados.items():
                        if info['hash'] == hash_md5:
                            duplicado_hash = nombre
                            break
                    
                    if duplicado_hash:
                        self._log_consola(f"  🔍 DUPLICADO EXACTO detectado (mismo archivo, sin OCR)")
                        self._log_consola(f"     Original: {duplicado_hash}")
                        self.logger.warning(f"Duplicado sin texto: {pdf.name} = {duplicado_hash}")
                        
                        respuesta = self._preguntar_ui(
                            "Duplicado sin texto",
                            f"Archivo duplicado detectado (mismo contenido binario):\n\n"
                            f"Original: {duplicado_hash}\n"
                            f"Nuevo: {pdf.name}\n\n"
                            f"¿Deseas copiar este archivo de todas formas?"
                        )
                        
                        if not respuesta:
                            self._log_consola(f"  🗑️  OMITIDO (duplicado sin texto)")
                            self.logger.info(f"Omitido duplicado sin texto: {pdf.name}")
                            continue
                    
                    # Copiar sin renombrar
                    ruta_destino = self.carpeta_salida / pdf.name
                    
                    # Manejar colisión de nombres
                    contador = 1
                    _base_stem = Path(pdf.name).stem
                    _base_ext = Path(pdf.name).suffix
                    while ruta_destino.exists():
                        ruta_destino = self.carpeta_salida / f"{_base_stem}_{contador:02d}{_base_ext}"
                        contador += 1
                    
                    self._copiar_archivo(pdf, ruta_destino)
                    self._log_consola(f"  ✅ Copiado sin renombrar: {ruta_destino.name}")
                    
                    # Registrar en tracking
                    archivos_procesados[ruta_destino.name] = {
                        'hash': hash_md5,
                        'texto': '',
                        'ruta': ruta_destino,
                        'metadata': {'nombre_original': pdf.name, 'hash_md5': hash_md5, 'sin_ocr': True}
                    }
                    
                    archivos_renombrados += 1
                    continue
                
                # PASO 2: Calcular hash MD5
                hash_md5 = calcular_hash_md5(pdf)
                
                # PASO 3: Detectar metadatos
                tipo_doc = detectar_tipo_documento(texto)
                fecha = buscar_fecha(texto)
                numero_doc = buscar_numero_documento(texto, tipo_doc)
                depto = buscar_departamento(texto)

                self._log_consola(
                    f"  ℹ️  Tipo: {tipo_doc} | Nº: {numero_doc or '—'} "
                    f"| Depto: {depto or '—'} | Fecha: {fecha or 'No detectada'}"
                )
                self.logger.info(
                    f"  Tipo: {tipo_doc}, Nº: {numero_doc}, Depto: {depto}, Fecha: {fecha}, Hash: {hash_md5[:8]}..."
                )
                
                # Debug si tipo quedó genérico
                if tipo_doc == "DOCUMENTO":
                    primeras_lineas = [l.strip() for l in texto.splitlines() if l.strip()][:6]
                    self._log_consola(f"  ⚙️  OCR (primeras líneas):", "warning")
                    for linea in primeras_lineas:
                        self._log_consola(f"      {linea[:100]}", "warning")
                    self.logger.debug(f"  OCR sin tipo reconocido.")
                
                # Verificar si el número ya fue procesado
                es_original = True
                clave_numero = (tipo_doc, numero_doc) if numero_doc else None
                if clave_numero and clave_numero in numeros_vistos:
                    nombre_previo = numeros_vistos[clave_numero]
                    self._log_consola(f"  ⚠️  Número '{numero_doc}' ({tipo_doc}) ya registrado → {nombre_previo}", "warning")
                    self.logger.warning(f"Número duplicado: {numero_doc} en {pdf.name}, previo: {nombre_previo}")
                    _ruta_previo = archivos_procesados.get(nombre_previo, {}).get('ruta')
                    guardar_como_respuesta = self._preguntar_numero_duplicado_ui(
                        numero_doc, tipo_doc, nombre_previo, pdf.name,
                        ruta_previo=_ruta_previo, ruta_nuevo=pdf
                    )
                    if guardar_como_respuesta is None:
                        self._log_consola(f"  ⏭️  OMITIDO (número duplicado, descartado por usuario)")
                        self.logger.info(f"Omitido por número duplicado: {pdf.name}")
                        continue
                    es_original = False

                # Generar nombre nuevo
                sufijo_final = "OR" if es_original else None
                nombre_nuevo = generar_nombre_limpio(
                    tipo_doc, fecha, numero_doc, depto, sufijo_final, texto_contexto=texto
                )
                
                # CAPA 1: Verificación por HASH
                duplicado_hash = None
                for nombre, info in archivos_procesados.items():
                    if info['hash'] == hash_md5:
                        duplicado_hash = nombre
                        break
                
                if duplicado_hash:
                    self._log_consola(f"  🔍 DUPLICADO EXACTO detectado (hash idéntico)")
                    self._log_consola(f"     Original: {duplicado_hash}")
                    self.logger.warning(f"Duplicado exacto: {pdf.name} = {duplicado_hash}")
                    
                    decision = self._verificar_duplicado_ui(
                        archivos_procesados[duplicado_hash]['ruta'],
                        pdf,
                        archivos_procesados[duplicado_hash]['texto'],
                        texto,
                        100.0
                    )
                    
                    if decision == "eliminar_2":
                        self._log_consola(f"  🗑️  ELIMINADO (duplicado confirmado)")
                        self.logger.info(f"Eliminado: {pdf.name}")
                        continue
                    elif decision == "renombrar_2":
                        sufijo_final = "RESPUESTA"
                        nombre_nuevo = generar_nombre_limpio(
                            tipo_doc, fecha, numero_doc, depto, "RESPUESTA", texto_contexto=texto
                        )
                        es_original = False
                        self._log_consola(f"  ✏️  Renombrado como RESPUESTA")
                    else:
                        self._log_consola(f"  ✅ Manteniendo ambos (confirmado diferente)")
                
                # CAPA 2: Verificación FUZZY
                else:
                    similitud_maxima = 0
                    mas_similar = None
                    
                    for nombre, info in archivos_procesados.items():
                        similitud = fuzz.ratio(texto[:1000], info['texto'][:1000])
                        if similitud > similitud_maxima:
                            similitud_maxima = similitud
                            mas_similar = nombre
                    
                    if similitud_maxima > 70:
                        self._log_consola(f"  🔍 SIMILITUD ALTA detectada: {similitud_maxima:.1f}%")
                        self._log_consola(f"     Similar a: {mas_similar}")
                        self.logger.warning(f"Similitud {similitud_maxima:.1f}%: {pdf.name} ~ {mas_similar}")
                        
                        decision = self._verificar_duplicado_ui(
                            archivos_procesados[mas_similar]['ruta'],
                            pdf,
                            archivos_procesados[mas_similar]['texto'],
                            texto,
                            similitud_maxima
                        )
                        
                        if decision == "eliminar_2":
                            self._log_consola(f"  🗑️  ELIMINADO (duplicado confirmado)")
                            self.logger.info(f"Eliminado: {pdf.name}")
                            continue
                        elif decision == "renombrar_2":
                            sufijo_final = "ANEXO"
                            nombre_nuevo = generar_nombre_limpio(
                                tipo_doc, fecha, numero_doc, depto, "ANEXO", texto_contexto=texto
                            )
                            es_original = False
                            self._log_consola(f"  ✏️  Renombrado como ANEXO")
                
                # Completar/editar nombre
                self._tipo_doc_editado = tipo_doc
                nombre_editado = self._editar_nombre_ui(
                    tipo_doc, fecha, numero_doc, depto, sufijo_final, texto, pdf
                )
                
                # Obtener información de adjunto desde la UI
                es_adjunto = getattr(self, "_es_adjunto_editado", False)
                principal_seleccionado = getattr(self, "_principal_editado", None)
                
                if nombre_editado:
                    nombre_nuevo = nombre_editado
                    tipo_doc = getattr(self, "_tipo_doc_editado", tipo_doc)
                
                # ===== LÓGICA DE ADJUNTO VS PRINCIPAL =====
                if es_adjunto and principal_seleccionado:
                    # Es ADJUNTO: FUSIONAR con el PDF principal seleccionado
                    ruta_principal = principal_seleccionado
                    
                    if not ruta_principal.exists():
                        self._log_consola(f"  ❌ ARCHIVO PRINCIPAL NO ENCONTRADO: {ruta_principal.name}")
                        self.logger.error(f"Archivo principal no encontrado: {ruta_principal}")
                        continue
                    
                    # Fusionar usando PyPDF2
                    exito_fusion = fusionar_pdf_anexo(ruta_principal, pdf, self.logger)
                    
                    if exito_fusion:
                        # Actualizar metadata del documento principal
                        metadata_principal = {
                            'nombre_original': ruta_principal.name,
                            'tipo_documento': tipo_doc,
                            'numero_documento': numero_doc,
                            'fecha_documento': fecha,
                            'tiene_anexos': True,
                            'annexo_procesado': pdf.name,
                            'anexo_timestamp': datetime.now().isoformat(),
                            'procesado_timestamp': datetime.now().isoformat()
                        }
                        guardar_metadata(ruta_principal, metadata_principal, self.carpeta_salida)
                        
                        self._log_consola(f"  📎 ANEXADO a: {ruta_principal.name}")
                        self.logger.info(f"Anexo fusionado: {pdf.name} → {ruta_principal.name}")
                        archivos_renombrados += 1
                    else:
                        self._log_consola(f"  ❌ ERROR al fusionar anexo")
                        self.logger.error(f"Error fusionando anexo {pdf.name}")
                        continue
                
                else:
                    # Es DOCUMENT PRINCIPAL: CREAR como nuevo archivo
                    ruta_destino = self.carpeta_salida / nombre_nuevo
                    
                    # Manejar colisiones
                    contador = 1
                    base_stem = ruta_destino.stem
                    base_ext = ruta_destino.suffix
                    while ruta_destino.exists():
                        ruta_destino = ruta_destino.parent / f"{base_stem}_{contador:02d}{base_ext}"
                        contador += 1
                    
                    self._copiar_archivo(pdf, ruta_destino)
                    self._log_consola(f"  ✅ Guardado como: {ruta_destino.name}")
                    self.logger.info(f"Guardado: {ruta_destino.name}")
                    
                    # Guardar metadata
                    metadata = {
                        'nombre_original': pdf.name,
                        'hash_md5': hash_md5,
                        'tipo_documento': tipo_doc,
                        'numero_documento': numero_doc,
                        'fecha_documento': fecha,
                        'longitud_texto': len(texto),
                        'tiene_anexos': False,
                        'procesado_timestamp': datetime.now().isoformat()
                    }
                    guardar_metadata(ruta_destino, metadata, self.carpeta_salida)
                    
                    # Registrar en tracking
                    archivos_procesados[ruta_destino.name] = {
                        'hash': hash_md5,
                        'texto': texto,
                        'ruta': ruta_destino,
                        'metadata': metadata
                    }
                    
                    # Agregar a historial de principales
                    self.historial_principales.append(str(ruta_destino))

                    if clave_numero and es_original:
                        numeros_vistos[clave_numero] = ruta_destino.name

                    archivos_renombrados += 1
                
                # Actualizar estado
                self.estado_label.configure(
                    text=f"Procesados: {idx}/{total_pdfs} | Renombrados: {archivos_renombrados}"
                )
            
            # FINALIZACIÓN
            self.progress_bar.set(1.0)
            self._log_consola("\n" + "="*70)
            self._log_consola("✅ PROCESAMIENTO COMPLETADO")
            self._log_consola("="*70)
            self._log_consola(f"\n📊 RESUMEN:")
            self._log_consola(f"   • Total archivos: {total_pdfs}")
            self._log_consola(f"   • Renombrados: {archivos_renombrados}")
            self._log_consola(f"   • Eliminados/Omitidos: {total_pdfs - archivos_renombrados}")
            
            self.logger.info("="*70)
            self.logger.info(f"PROCESAMIENTO COMPLETADO - {archivos_renombrados}/{total_pdfs} archivos")
            self.logger.info("="*70)
            
            self.estado_label.configure(
                text=f"✅ Completado: {archivos_renombrados} archivos procesados"
            )
            
            # Mostrar mensaje de éxito (thread-safe)
            _msg = (
                f"✅ Procesamiento finalizado exitosamente\n\n"
                f"Archivos procesados: {archivos_renombrados}/{total_pdfs}\n"
                f"Carpeta de salida: {self.carpeta_salida}\n\n"
                f"Revisa los logs para más detalles."
            )
            self.after(0, lambda: messagebox.showinfo("Procesamiento completado", _msg))
            
        except Exception as e:
            error_msg = f"❌ Error crítico: {type(e).__name__} - {e}"
            self._log_consola(f"\n{error_msg}")
            self.logger.exception("Error crítico en procesamiento")
            self.after(0, lambda m=error_msg: messagebox.showerror("Error", m))
        
        finally:
            if carpeta_temp_seg and carpeta_temp_seg.exists():
                shutil.rmtree(carpeta_temp_seg, ignore_errors=True)
            # Deshabilitar botón procesar al terminar
            self.btn_procesar.configure(
                state="disabled",
                text="▶  Iniciar Procesamiento",
                fg_color="#B0B0B0",
                hover_color="#A0A0A0",
                text_color="#707070"
            )
            self.btn_limpiar.configure(state="normal")
            self.procesando = False
    
    def _copiar_archivo(self, origen: Path, destino: Path):
        """Copia un archivo de origen a destino."""
        try:
            shutil.copy2(origen, destino)
        except Exception as e:
            error_msg = f"Error copiando {origen.name} → {destino.name}: {e}"
            self.logger.error(error_msg)
            self._log_consola(f"  ❌ {error_msg}")
            raise
    
    def _editar_nombre_ui(
        self,
        tipo_doc: str,
        fecha: Optional[str],
        numero_doc: Optional[str],
        depto: Optional[str],
        sufijo: Optional[str],
        texto_ocr: str,
        ruta_pdf: Path,
    ) -> str:
        """
        Ventana modal para editar el nombre del archivo.
        Retorna el nombre final generado con los valores confirmados por el usuario.
        """
        sigla = SIGLAS_DOCUMENTO.get(tipo_doc, tipo_doc[:3].upper())
        resultado = [
            generar_nombre_limpio(tipo_doc, fecha, numero_doc, depto, sufijo, texto_contexto=texto_ocr)
        ]
        evento = threading.Event()

        # Extraer candidatos OCR para sugerencias
        def _cands_numero() -> list:
            lineas_texto = "\n".join(texto_ocr.splitlines()[:35])
            encontrados, vistos = [], set()
            for m in re.finditer(r'\b(\d{2,6}(?:[/\-]\d{2,4})?)\b', lineas_texto):
                v = m.group(1)
                if v not in vistos:
                    vistos.add(v)
                    encontrados.append(v)
                if len(encontrados) == 6:
                    break
            return encontrados

        def _cands_depto() -> list:
            NOISE_D = {
                "NO", "DE", "EL", "LA", "LOS", "LAS", "UN", "UNA", "DEL", "AL",
                "NRO", "NUM", "POR", "CON", "QUE", "SE", "EN", "A", "Y", "O",
            }
            cands, seen = [], set()
            for linea in texto_ocr.splitlines()[:30]:
                for m in re.finditer(r'\b([A-ZÁÉÍÓÚÑ]{2,12})\b', linea.upper()):
                    c = m.group(1)
                    if c not in NOISE_D and c not in seen:
                        seen.add(c)
                        cands.append(c)
                    if len(cands) == 6:
                        return cands
            return cands

        def _mostrar():
            _vars: dict = {}
            tipos_disponibles = sorted(list(TIPOS_PREDEFINIDOS | {"DOCUMENTO"}))

            ventana = ctk.CTkToplevel(self)
            ventana.title("Completar/Revisar nombre del archivo - Lector V3")
            ventana.resizable(True, True)
            ventana.minsize(860, 540)
            ventana.configure(fg_color=COLOR_GRIS_FONDO)
            ventana.transient(self)
            ventana.grab_set()

            w, h = 1050, 710
            ventana.update_idletasks()
            sw, sh = ventana.winfo_screenwidth(), ventana.winfo_screenheight()
            ventana.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

            # Helpers internos
            def _construir_nombre() -> str:
                n = (_vars["v_num"].get().strip() or None)
                d = (_vars["v_dep"].get().strip() or None)
                f = (_vars["v_fec"].get().strip() or None)
                tipo_sel = _vars["v_tipo"].get().strip() or tipo_doc
                return generar_nombre_limpio(tipo_sel, f, n, d, sufijo, texto_contexto=texto_ocr)

            def _actualizar_preview(*_):
                nombre = _construir_nombre()
                _vars["lbl_preview"].configure(text=nombre)

            def _confirmar():
                # Validar según tipo de documento
                es_adjunto = _vars["v_es_adjunto"].get()
                
                if es_adjunto:
                    # Si es adjunto, no necesita fecha
                    principal = combo_principal.get()
                    if not principal or principal == "(Sin documentos anteriores)":
                        _vars["lbl_err"].configure(
                            text="⚠️  Debes seleccionar un documento principal para anexar."
                        )
                        return
                    # Guardar información del adjunto
                    self._es_adjunto_editado = True
                    # Buscar la ruta completa del principal seleccionado
                    for ruta_p in self.historial_principales:
                        if Path(ruta_p).stem == principal:
                            self._principal_editado = Path(ruta_p)
                            break
                else:
                    # Si es documento principal, REQUIERE FECHA
                    f = _vars["v_fec"].get().strip()
                    if not f:
                        _vars["lbl_err"].configure(
                            text="⚠️  La fecha es obligatoria para documentos principales."
                        )
                        return
                    self._es_adjunto_editado = False
                    self._principal_editado = None
                
                self._tipo_doc_editado = _vars["v_tipo"].get().strip() or tipo_doc
                resultado[0] = _construir_nombre()
                ventana.destroy()

            def _cancelar():
                self._tipo_doc_editado = tipo_doc
                ventana.destroy()

            # HEADER
            # Los campos requeridos dependen del tipo (principal vs adjunto)
            es_adj_inicial = tipo_doc in TIPOS_ADJUNTOS
            
            if es_adj_inicial:
                campos_vacios = []  # Los adjuntos no requieren campos específicos
            else:
                campos_vacios = [
                    n for n, v in [("Número", numero_doc), ("Departamento", depto), ("Fecha", fecha)]
                    if not v
                ]
            
            hay_incompletos = bool(campos_vacios)
            header_color = "#C0392B" if hay_incompletos else COLOR_AZUL_IPSD
            titulo = (
                f"⚠️  DOCUMENTO PRINCIPAL INCOMPLETO — Campos: {', '.join(campos_vacios)}"
                if hay_incompletos
                else "✏️  REVISAR NOMBRE DEL ARCHIVO"
            )
            header = ctk.CTkFrame(ventana, fg_color=header_color, corner_radius=0)
            header.pack(fill="x")
            ctk.CTkLabel(
                header, text=titulo,
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color=COLOR_BLANCO,
            ).pack(pady=11)

            # BOTONES (bottom)
            bframe = ctk.CTkFrame(ventana, fg_color="white", corner_radius=0)
            bframe.pack(fill="x", side="bottom")
            tk.Frame(bframe, bg="#E0E0E0", height=1).pack(fill="x")
            ctk.CTkLabel(
                bframe,
                text=f"Formato: {sigla}-NÚMERO_DEPARTAMENTO_FECHA_{sufijo or ''}.pdf",
                font=ctk.CTkFont(size=10), text_color="#888888",
            ).pack(pady=(6, 2))
            brow = ctk.CTkFrame(bframe, fg_color="transparent")
            brow.pack(pady=(0, 12))
            ctk.CTkButton(
                brow, text="✅ Confirmar nombre", command=_confirmar,
                fg_color=COLOR_VERDE_IPSD, hover_color="#7AA020",
                width=200, height=52, corner_radius=10,
                font=ctk.CTkFont(size=11, weight="bold"),
            ).pack(side="left", padx=6)
            ctk.CTkButton(
                brow, text="↩️ Usar nombre actual", command=_cancelar,
                fg_color="white", hover_color="#EBF3FF",
                text_color=COLOR_AZUL_IPSD, border_width=2, border_color=COLOR_AZUL_IPSD,
                width=200, height=52, corner_radius=10,
                font=ctk.CTkFont(size=11, weight="bold"),
            ).pack(side="left", padx=6)

            # CUERPO
            body = ctk.CTkFrame(ventana, fg_color=COLOR_GRIS_FONDO)
            body.pack(fill="both", expand=True, padx=14, pady=8)

            # Panel izquierdo: miniatura
            left = ctk.CTkFrame(body)
            left.pack(side="left", fill="both", expand=True, padx=(0, 6))
            ctk.CTkLabel(
                left, text="📄 Vista previa",
                font=ctk.CTkFont(size=13, weight="bold"), text_color=COLOR_AZUL_IPSD,
            ).pack(pady=(10, 2))
            ctk.CTkLabel(
                left, text=ruta_pdf.name, font=ctk.CTkFont(size=10),
                wraplength=380, text_color=COLOR_GRIS_TEXTO,
            ).pack(pady=(0, 4))
            img_prev = _miniatura_pdf(ruta_pdf, max_size=(390, 430))
            if img_prev:
                ventana._ctk_img_e = ctk.CTkImage(
                    light_image=img_prev, dark_image=img_prev,
                    size=(img_prev.width, img_prev.height),
                )
                lbl_prev_img = ctk.CTkLabel(left, image=ventana._ctk_img_e, text="",
                                            cursor="hand2")
                lbl_prev_img.pack(expand=True, pady=(0, 2))
                lbl_prev_img.bind("<Button-1>", lambda e: _abrir_zoom_pdf(ventana, ruta_pdf))
                ctk.CTkLabel(left, text="🔍 Clic para zoom",
                             font=ctk.CTkFont(size=9), text_color="#999999"
                             ).pack(pady=(0, 6))
            else:
                ctk.CTkLabel(
                    left, text="Vista previa no disponible", text_color="#999999",
                ).pack(expand=True)

            # Panel derecho: formulario
            right = ctk.CTkFrame(body, fg_color="white")
            right.pack(side="right", fill="both", expand=True, padx=(6, 0))

            # Preview nombre
            ctk.CTkLabel(
                right, text="📝 Nombre resultante:",
                font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_GRIS_TEXTO,
            ).pack(padx=14, pady=(12, 1), anchor="w")
            lbl_preview = ctk.CTkLabel(
                right,
                text=generar_nombre_limpio(tipo_doc, fecha, numero_doc, depto, sufijo, texto_contexto=texto_ocr),
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=COLOR_AZUL_IPSD, wraplength=400,
            )
            lbl_preview.pack(padx=14, pady=(0, 4), anchor="w")
            _vars["lbl_preview"] = lbl_preview

            lbl_err = ctk.CTkLabel(right, text="", font=ctk.CTkFont(size=10),
                                   text_color="#CC0000")
            lbl_err.pack(padx=14, anchor="w")
            _vars["lbl_err"] = lbl_err

            tk.Frame(right, bg="#E0E0E0", height=1).pack(fill="x", padx=14, pady=(4, 0))

            # Helper para crear campos
            def _campo(label: str, valor_inicial, candidates: list, var_key: str,
                       readonly: bool = False, is_date: bool = False):
                tiene = bool(valor_inicial and str(valor_inicial).strip())
                ic = "\u2705" if tiene else "⚠️"
                if tiene:
                    cc = COLOR_AZUL_IPSD
                    bc = COLOR_AZUL_IPSD
                elif is_date:
                    cc = "#CC0000"
                    bc = "#CC0000"
                else:
                    cc = "#E65100"
                    bc = "#E65100"

                fila = ctk.CTkFrame(right, fg_color="transparent")
                fila.pack(fill="x", padx=14, pady=(7, 1))
                ctk.CTkLabel(
                    fila, text=f"{ic} {label}",
                    font=ctk.CTkFont(size=11, weight="bold"),
                    text_color=cc, width=160, anchor="w",
                ).pack(side="left")

                if readonly:
                    ctk.CTkLabel(
                        fila,
                        text=str(valor_inicial),
                        font=ctk.CTkFont(size=11), text_color=COLOR_GRIS_TEXTO,
                    ).pack(side="left")
                    return

                var = ctk.StringVar(value=str(valor_inicial) if valor_inicial else "")
                var.trace_add("write", _actualizar_preview)
                _vars[var_key] = var
                entry = ctk.CTkEntry(
                    fila, textvariable=var,
                    font=ctk.CTkFont(size=12), height=32, border_color=bc,
                )
                entry.pack(side="left", fill="x", expand=True)

                if is_date:
                    ctk.CTkButton(
                        fila, text="📅",
                        command=lambda v=var: _abrir_calendario(ventana, v, _actualizar_preview),
                        width=36, height=32, corner_radius=6,
                        font=ctk.CTkFont(size=14),
                        fg_color=COLOR_AZUL_IPSD, hover_color="#13689E",
                    ).pack(side="left", padx=(4, 0))

                if candidates:
                    cf = ctk.CTkFrame(right, fg_color="transparent")
                    cf.pack(fill="x", padx=30, pady=(1, 0))
                    ctk.CTkLabel(
                        cf, text="Sugerencias: ",
                        font=ctk.CTkFont(size=9), text_color="#888888",
                    ).pack(side="left")
                    for c in candidates[:6]:
                        ctk.CTkButton(
                            cf, text=c,
                            command=lambda v=c, vr=var: vr.set(v),
                            width=0, height=20, corner_radius=8,
                            font=ctk.CTkFont(size=9),
                            fg_color="#EBF3FF", hover_color="#D0E8FF",
                            text_color=COLOR_AZUL_IPSD,
                            border_width=1, border_color="#BBCCE8",
                        ).pack(side="left", padx=2)

            # Fila de tipo
            fila_tipo = ctk.CTkFrame(right, fg_color="transparent")
            fila_tipo.pack(fill="x", padx=14, pady=(7, 1))
            ctk.CTkLabel(
                fila_tipo, text="✅ Tipo de archivo",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=COLOR_AZUL_IPSD, width=160, anchor="w",
            ).pack(side="left")
            var_tipo = ctk.StringVar(value=tipo_doc if tipo_doc in tipos_disponibles else "DOCUMENTO")
            var_tipo.trace_add("write", _actualizar_preview)
            _vars["v_tipo"] = var_tipo
            ctk.CTkOptionMenu(
                fila_tipo,
                values=tipos_disponibles,
                variable=var_tipo,
                width=230,
                height=32,
                fg_color=COLOR_AZUL_IPSD,
                button_color="#13689E",
                button_hover_color="#0F5178",
                dropdown_fg_color="#FFFFFF",
                dropdown_hover_color="#EBF3FF",
                dropdown_text_color=COLOR_AZUL_IPSD,
                text_color="#FFFFFF",
            ).pack(side="left")

            # ===== SECCIÓN DE ADJUNTOS =====
            var_es_adjunto = ctk.BooleanVar(value=tipo_doc in TIPOS_ADJUNTOS)
            _vars["v_es_adjunto"] = var_es_adjunto
            
            def _toggle_adjunto():
                es_adj = var_es_adjunto.get()
                combo_principal.configure(state="normal" if es_adj else "disabled")
                # Ocultar/mostrar campos de renombrado
                for widget in campo_num_frame, campo_depto_frame, campo_fec_frame:
                    if widget and widget.winfo_exists():
                        if es_adj:
                            widget.pack_forget()
                        else:
                            widget.pack(fill="x", padx=14, pady=(7, 1))
                _actualizar_preview()
            
            fila_adjunto = ctk.CTkFrame(right, fg_color="transparent")
            fila_adjunto.pack(fill="x", padx=14, pady=(10, 2))
            
            checkbox_adjunto = ctk.CTkCheckBox(
                fila_adjunto,
                text="📎 Es un adjunto/anexo",
                variable=var_es_adjunto,
                command=_toggle_adjunto,
                font=ctk.CTkFont(size=11),
                checkbox_width=20,
                checkbox_height=20,
            )
            checkbox_adjunto.pack(side="left", padx=0)
            
            # ComboBox para seleccionar documento principal
            ctk.CTkLabel(
                fila_adjunto,
                text="Anexar a:",
                font=ctk.CTkFont(size=10),
                text_color=COLOR_GRIS_TEXTO,
            ).pack(side="left", padx=(20, 6))
            
            # Obtener lista de nombres del historial
            lista_principales = [Path(ruta).stem for ruta in self.historial_principales]
            
            combo_principal = ctk.CTkComboBox(
                fila_adjunto,
                values=lista_principales if lista_principales else ["(Sin documentos anteriores)"],
                state="disabled",
                width=200,
                height=28,
                border_color=COLOR_AZUL_IPSD,
            )
            combo_principal.pack(side="left", padx=6)
            if lista_principales:
                combo_principal.set(lista_principales[0])
            _vars["v_principal"] = combo_principal

            # Filas de campos (las guardaremos para poder ocultarlas/mostrarlas)
            campo_num_frame = None
            campo_depto_frame = None
            campo_fec_frame = None
            
            # Filas de campos
            def _crear_campo_num():
                global campo_num_frame
                campo_num_frame = ctk.CTkFrame(right, fg_color="transparent")
                if not var_es_adjunto.get():
                    campo_num_frame.pack(fill="x", padx=14, pady=(7, 1))
                _campo_impl("Número", numero_doc, _cands_numero(), "v_num", False, False, campo_num_frame)
            
            def _crear_campo_depto():
                global campo_depto_frame
                campo_depto_frame = ctk.CTkFrame(right, fg_color="transparent")
                if not var_es_adjunto.get():
                    campo_depto_frame.pack(fill="x", padx=14, pady=(7, 1))
                _campo_impl("Departamento", depto, _cands_depto(), "v_dep", False, False, campo_depto_frame)
            
            def _crear_campo_fec():
                global campo_fec_frame
                campo_fec_frame = ctk.CTkFrame(right, fg_color="transparent")
                if not var_es_adjunto.get():
                    campo_fec_frame.pack(fill="x", padx=14, pady=(7, 1))
                _campo_impl("Fecha", fecha, [], "v_fec", False, True, campo_fec_frame)
            
            # Helper para crear campos con frame parámetro
            def _campo_impl(label: str, valor_inicial, candidates: list, var_key: str,
                           readonly: bool = False, is_date: bool = False, parent_frame=None):
                if parent_frame is None:
                    parent_frame = right
                    
                tiene = bool(valor_inicial and str(valor_inicial).strip())
                ic = "\u2705" if tiene else "⚠️"
                if tiene:
                    cc = COLOR_AZUL_IPSD
                    bc = COLOR_AZUL_IPSD
                elif is_date:
                    cc = "#CC0000"
                    bc = "#CC0000"
                else:
                    cc = "#E65100"
                    bc = "#E65100"

                fila = ctk.CTkFrame(parent_frame, fg_color="transparent")
                fila.pack(fill="x")
                
                ctk.CTkLabel(
                    fila, text=f"{ic} {label}",
                    font=ctk.CTkFont(size=11, weight="bold"),
                    text_color=cc, width=160, anchor="w",
                ).pack(side="left")

                if readonly:
                    ctk.CTkLabel(
                        fila,
                        text=str(valor_inicial),
                        font=ctk.CTkFont(size=11), text_color=COLOR_GRIS_TEXTO,
                    ).pack(side="left")
                    return

                var = ctk.StringVar(value=str(valor_inicial) if valor_inicial else "")
                var.trace_add("write", _actualizar_preview)
                _vars[var_key] = var
                entry = ctk.CTkEntry(
                    fila, textvariable=var,
                    font=ctk.CTkFont(size=12), height=32, border_color=bc,
                )
                entry.pack(side="left", fill="x", expand=True)

                if is_date:
                    ctk.CTkButton(
                        fila, text="📅",
                        command=lambda v=var: _abrir_calendario(ventana, v, _actualizar_preview),
                        width=36, height=32, corner_radius=6,
                        font=ctk.CTkFont(size=14),
                        fg_color=COLOR_AZUL_IPSD, hover_color="#13689E",
                    ).pack(side="left", padx=(4, 0))

                if candidates:
                    cf = ctk.CTkFrame(parent_frame, fg_color="transparent")
                    cf.pack(fill="x", padx=30, pady=(1, 0))
                    ctk.CTkLabel(
                        cf, text="Sugerencias: ",
                        font=ctk.CTkFont(size=9), text_color="#888888",
                    ).pack(side="left")
                    for c in candidates[:6]:
                        ctk.CTkButton(
                            cf, text=c,
                            command=lambda v=c, vr=var: vr.set(v),
                            width=0, height=20, corner_radius=8,
                            font=ctk.CTkFont(size=9),
                            fg_color="#EBF3FF", hover_color="#D0E8FF",
                            text_color=COLOR_AZUL_IPSD,
                            border_width=1, border_color="#BBCCE8",
                        ).pack(side="left", padx=2)
            
            _crear_campo_num()
            _crear_campo_depto()
            _crear_campo_fec()
            
            if sufijo:
                fila_sufijo = ctk.CTkFrame(right, fg_color="transparent")
                if not var_es_adjunto.get():
                    fila_sufijo.pack(fill="x", padx=14, pady=(7, 1))
                _campo_impl("Sufijo", sufijo, [], "v_sfx", readonly=True, parent_frame=fila_sufijo)

            ventana.protocol("WM_DELETE_WINDOW", _cancelar)
            ventana.wait_window()
            evento.set()

        self.after(0, _mostrar)
        evento.wait()
        return resultado[0]

    def _preguntar_numero_duplicado_ui(self, numero: str, tipo: str,
                                        archivo_previo: str, archivo_nuevo: str,
                                        ruta_previo: Optional[Path] = None,
                                        ruta_nuevo: Optional[Path] = None):
        """
        Muestra ventana visual para manejar un número de documento duplicado.
        Retorna: True guardar como RESPUESTA, None omitir
        """
        resultado = [True]
        evento = threading.Event()

        def _mostrar():
            ventana = VentanaNumDuplicado(
                self, numero, tipo,
                archivo_previo, ruta_previo,
                archivo_nuevo, ruta_nuevo
            )
            decision = ventana.obtener_decision()
            resultado[0] = None if decision == "omitir" else True
            evento.set()

        self.after(0, _mostrar)
        evento.wait()
        return resultado[0]

    def _verificar_duplicado_ui(self, archivo1: Path, archivo2: Path, 
                                 texto1: str, texto2: str, similitud: float) -> str:
        """
        Muestra ventana de verificación y retorna la decisión del usuario.
        Thread-safe.
        """
        resultado = [None]
        evento = threading.Event()

        def _mostrar_en_hilo_principal():
            ventana = VentanaVerificacion(self, archivo1, archivo2, texto1, texto2, similitud)
            resultado[0] = ventana.obtener_decision()
            evento.set()

        self.after(0, _mostrar_en_hilo_principal)
        evento.wait()

        return resultado[0] or "mantener_ambos"

    def _preguntar_ui(self, titulo: str, mensaje: str) -> bool:
        """
        Muestra messagebox.askyesno de forma thread-safe.
        Retorna: True si el usuario confirmó, False si canceló.
        """
        resultado = [None]
        evento = threading.Event()

        def _ask():
            resultado[0] = messagebox.askyesno(titulo, mensaje)
            evento.set()

        self.after(0, _ask)
        evento.wait()
        return bool(resultado[0])


# =============================================================================
# PUNTO DE ENTRADA PRINCIPAL
# =============================================================================

def main():
    """Función principal de la aplicación."""
    
    print("="*70)
    print("LECTOR DE PDFs V3.0")
    print("Instituto de Profesionalización y Superación Docente (IPSD) - UNAH")
    print("="*70)
    print()
    
    # Verificar dependencias críticas
    if not TESSERACT_PATH.exists():
        print(f"⚠️  ADVERTENCIA: Tesseract no encontrado en:")
        print(f"   {TESSERACT_PATH}")
        print(f"   El OCR puede no funcionar correctamente.")
        print()
    
    if not POPPLER_PATH.exists():
        print(f"⚠️  ADVERTENCIA: Poppler no encontrado en:")
        print(f"   {POPPLER_PATH}")
        print(f"   La conversión PDF→Imagen puede fallar.")
        print()
    
    # Iniciar aplicación
    app = PantallaProcesamiento()
    app.mainloop()


if __name__ == "__main__":
    main()
