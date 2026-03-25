"""
=============================================================================
VENTANAS MODALES - Componentes de interfaz para verificación
=============================================================================

Módulo que contiene:
- Clase VentanaConsultaSeparacion: Consulta al usuario sobre separación de documentos
- Clase VentanaVerificacion: Verificación de duplicados
- Clase VentanaNumDuplicado: Manejo de números duplicados
- Funciones auxiliares: Zoom PDF, Calendario, Icono de aplicación
"""

import tkinter as tk
from pathlib import Path
from typing import Optional
from datetime import datetime
import calendar as _cal

import customtkinter as ctk
from PIL import Image, ImageTk

from config import (
    COLOR_AZUL_IPSD, COLOR_VERDE_IPSD, COLOR_BLANCO, 
    COLOR_GRIS_FONDO, COLOR_GRIS_TEXTO, ASSETS_PATH
)
from core.ocr_engine import _miniatura_pdf

# ═════════════════════════════════════════════════════════════════════════════
# HELPER - ÍCONO DE APLICACIÓN
# ═════════════════════════════════════════════════════════════════════════════

_ICO_PATH: Optional[Path] = None
_ICON_REF = None   # PhotoImage global para iconphoto (evita GC)


def _preparar_icono() -> Optional[Path]:
    """
    Genera Assets/Logo_App.ico a partir del PNG sin alterarlo (mantiene transparencia y proporciones).
    Solo redimensiona a diferentes tamaños manteniendo la relación de aspecto.
    """
    global _ICO_PATH
    if _ICO_PATH is not None:
        return _ICO_PATH
    try:
        src = ASSETS_PATH / "Logo_App.png"
        dst = ASSETS_PATH / "Logo_App.ico"
        if not src.exists():
            return None
        
        # Cargar imagen sin modificar (conserva transparencia)
        img = Image.open(src).convert("RGBA")
        
        # Generar versiones redimensionadas manteniendo proporción
        # Usar un canvas cuadrado para mantener las proporciones
        sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        imgs_ico = []
        
        for size in sizes:
            # Crear canvas cuadrado con fondo blanco/transparente
            canvas = Image.new("RGBA", size, (255, 255, 255, 0))
            
            # Calcular tamaño máximo que cabe en el canvas manteniendo proporción
            aspect = img.width / img.height
            if aspect > 1:  # Ancho > Alto
                new_w = int(size[0] * 0.9)
                new_h = int(new_w / aspect)
            else:  # Alto >= Ancho
                new_h = int(size[1] * 0.9)
                new_w = int(new_h * aspect)
            
            # Redimensionar con alta calidad
            img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            
            # Centrar en el canvas
            offset_x = (size[0] - new_w) // 2
            offset_y = (size[1] - new_h) // 2
            canvas.paste(img_resized, (offset_x, offset_y), img_resized)
            
            imgs_ico.append(canvas)
        
        # Guardar como ICO con múltiples resoluciones
        imgs_ico[0].save(str(dst), format="ICO", sizes=sizes,
                         append_images=imgs_ico[1:])
        _ICO_PATH = dst
        _ICO_PATH = dst
    except Exception:
        pass
    return _ICO_PATH


def _set_app_icon(window, delay: int = 0):
    """
    Establece el icono de la aplicación en cualquier ventana tk/ctk.
    Usa delay (ms) para CTkToplevel donde el wm puede sobreescribir el icono.
    """
    ico = _preparar_icono()
    if not ico:
        return

    def _apply():
        try:
            window.iconbitmap(str(ico))
        except Exception:
            pass

    if delay:
        window.after(delay, _apply)
    else:
        _apply()


# ═════════════════════════════════════════════════════════════════════════════
# HELPER - ZOOM PDF
# ═════════════════════════════════════════════════════════════════════════════

def _abrir_zoom_pdf(parent, ruta_pdf: Path, num_pagina: int = 1):
    """
    Abre una ventana modal con el PDF renderizado a alta calidad (200 DPI).
    Soporta zoom con rueda del ratón (± 15%) y botones +/-/100%.
    Permite arrastrar la imagen para navegar.
    Cierre con botón × o tecla Escape.
    """
    ventana = ctk.CTkToplevel(parent)
    ventana.title(f"Zoom — {ruta_pdf.name} (pág {num_pagina})")
    ventana.configure(fg_color="#2B2B2B")
    ventana.transient(parent)
    ventana.grab_set()
    ventana.resizable(True, True)
    ventana.minsize(480, 500)
    ventana.bind("<Escape>", lambda e: ventana.destroy())
    _set_app_icon(ventana, delay=150)

    w, h = 700, 820
    ventana.update_idletasks()
    sw, sh = ventana.winfo_screenwidth(), ventana.winfo_screenheight()
    ventana.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

    # --- Renderizar a 200 DPI ---
    try:
        from config import POPPLER_PATH
        from pdf2image import convert_from_path
        
        if POPPLER_PATH.exists():
            imgs = convert_from_path(
                str(ruta_pdf), first_page=num_pagina, last_page=num_pagina,
                poppler_path=str(POPPLER_PATH), dpi=200
            )
        else:
            imgs = convert_from_path(
                str(ruta_pdf), first_page=num_pagina, last_page=num_pagina,
                dpi=200
            )
        img_orig = imgs[0] if imgs else None
    except Exception:
        img_orig = None

    if not img_orig:
        ctk.CTkLabel(ventana, text="No se pudo cargar la imagen.",
                     text_color="#999999").pack(expand=True)
        return

    estado = {"escala": 1.0}

    # --- Toolbar ---
    toolbar = tk.Frame(ventana, bg="#1C1F2E", height=40)
    toolbar.pack(fill="x")
    toolbar.pack_propagate(False)

    lbl_escala = tk.Label(toolbar, text="100%", font=("Segoe UI", 10),
                          bg="#1C1F2E", fg="#AAAAAA", width=5)
    lbl_escala.pack(side="left", padx=6)

    def _zoom(factor):
        estado["escala"] = max(0.25, min(4.0, estado["escala"] * factor))
        _render()

    def _zoom_reset():
        estado["escala"] = 1.0
        _render()

    tk.Button(toolbar, text=" + ", command=lambda: _zoom(1.2),
              font=("Segoe UI", 12, "bold"), bg="#003671", fg="white",
              relief="flat", padx=4).pack(side="left", padx=3, pady=5)
    tk.Button(toolbar, text=" − ", command=lambda: _zoom(1 / 1.2),
              font=("Segoe UI", 12, "bold"), bg="#003671", fg="white",
              relief="flat", padx=4).pack(side="left", padx=3, pady=5)
    tk.Button(toolbar, text="100%", command=_zoom_reset,
              font=("Segoe UI", 9), bg="#555555", fg="white",
              relief="flat", padx=4).pack(side="left", padx=3, pady=5)
    tk.Label(toolbar,
             text="🖱 Rueda: zoom   │   Clic+arrastrar: mover",
             font=("Segoe UI", 9), bg="#1C1F2E", fg="#7AADCA"
             ).pack(side="right", padx=(0, 6))
    tk.Button(toolbar, text=" ✕ Cerrar ", command=ventana.destroy,
              font=("Segoe UI", 9, "bold"), bg="#8B1A1A", fg="white",
              activebackground="#CC2222", activeforeground="white",
              relief="flat", padx=6).pack(side="right", padx=6, pady=5)

    # --- Canvas scrollable ---
    canvas_frame = tk.Frame(ventana, bg="#2B2B2B")
    canvas_frame.pack(fill="both", expand=True)

    canvas = tk.Canvas(canvas_frame, bg="#2B2B2B", highlightthickness=0)
    vbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
    hbar = tk.Scrollbar(canvas_frame, orient="horizontal", command=canvas.xview)
    canvas.configure(yscrollcommand=vbar.set, xscrollcommand=hbar.set)
    vbar.pack(side="right", fill="y")
    hbar.pack(side="bottom", fill="x")
    canvas.pack(fill="both", expand=True)

    # Keep reference to prevent GC
    tk_img_zoom: list = [None]

    def _render():
        escala = estado["escala"]
        lbl_escala.configure(text=f"{int(escala * 100)}%")
        nw = max(1, int(img_orig.width * escala))
        nh = max(1, int(img_orig.height * escala))
        resized = img_orig.resize((nw, nh), Image.Resampling.LANCZOS)
        tk_img_zoom[0] = ImageTk.PhotoImage(resized)
        canvas.delete("all")
        canvas.create_image(0, 0, anchor="nw", image=tk_img_zoom[0])
        canvas.configure(scrollregion=(0, 0, nw, nh))

    _render()

    # Scroll wheel zoom
    def _on_wheel(event):
        _zoom(1.15 if event.delta > 0 else 1 / 1.15)
    canvas.bind("<MouseWheel>", _on_wheel)

    # Drag to pan
    drag = {"x": 0, "y": 0}
    def _drag_start(e): drag["x"], drag["y"] = e.x, e.y
    def _drag_move(e):
        canvas.xview_scroll(-(e.x - drag["x"]) // 3, "units")
        canvas.yview_scroll(-(e.y - drag["y"]) // 3, "units")
        drag["x"], drag["y"] = e.x, e.y
    canvas.bind("<ButtonPress-1>", _drag_start)
    canvas.bind("<B1-Motion>", _drag_move)
    canvas.configure(cursor="fleur")


# ═════════════════════════════════════════════════════════════════════════════
# HELPER - CALENDARIO
# ═════════════════════════════════════════════════════════════════════════════

def _abrir_calendario(parent, var_fecha: "ctk.StringVar", on_change=None):
    """
    Abre un popup calendario minimalista (puro tkinter, sin dependencias extra).
    Al seleccionar un día actualiza var_fecha con formato YYYY-MM-DD y llama on_change.
    """
    # Parsear fecha inicial
    try:
        d0 = datetime.strptime(var_fecha.get().strip(), "%Y-%m-%d")
    except ValueError:
        d0 = datetime.now()

    estado = {"year": d0.year, "month": d0.month}

    popup = tk.Toplevel(parent)
    popup.title("Seleccionar fecha")
    popup.resizable(False, False)
    popup.grab_set()
    popup.configure(bg="white")
    _set_app_icon(popup, delay=100)

    popup.update_idletasks()
    sw, sh = popup.winfo_screenwidth(), popup.winfo_screenheight()
    w, h = 330, 290
    popup.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

    MESES = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
             "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
    DIAS  = ["Lu", "Ma", "Mi", "Ju", "Vi", "Sa", "Do"]

    contenedor = tk.Frame(popup, bg="white")
    contenedor.pack(fill="both", expand=True, padx=6, pady=6)

    def _render():
        for w2 in contenedor.winfo_children():
            w2.destroy()

        # Nav header: « ‹  Mes Año  › »
        nav = tk.Frame(contenedor, bg=COLOR_AZUL_IPSD)
        nav.pack(fill="x", pady=(0, 4))
        # Año anterior
        tk.Button(nav, text="«", font=("Segoe UI", 12, "bold"),
                  bg=COLOR_AZUL_IPSD, fg="white", relief="flat", bd=0,
                  command=lambda: _cambiar_anio(-1)).pack(side="left", padx=2)
        # Mes anterior
        tk.Button(nav, text="‹", font=("Segoe UI", 14, "bold"),
                  bg=COLOR_AZUL_IPSD, fg="white", relief="flat", bd=0,
                  command=lambda: _cambiar(-1)).pack(side="left", padx=2)
        tk.Label(nav,
                 text=f"{MESES[estado['month'] - 1]}  {estado['year']}",
                 font=("Segoe UI", 11, "bold"),
                 bg=COLOR_AZUL_IPSD, fg="white"
                 ).pack(side="left", expand=True)
        # Mes siguiente
        tk.Button(nav, text="›", font=("Segoe UI", 14, "bold"),
                  bg=COLOR_AZUL_IPSD, fg="white", relief="flat", bd=0,
                  command=lambda: _cambiar(1)).pack(side="right", padx=2)
        # Año siguiente
        tk.Button(nav, text="»", font=("Segoe UI", 12, "bold"),
                  bg=COLOR_AZUL_IPSD, fg="white", relief="flat", bd=0,
                  command=lambda: _cambiar_anio(1)).pack(side="right", padx=2)

        # Day headers
        hdr = tk.Frame(contenedor, bg="white")
        hdr.pack(fill="x")
        for d in DIAS:
            tk.Label(hdr, text=d, width=3, font=("Segoe UI", 9, "bold"),
                     bg="white", fg=COLOR_AZUL_IPSD).pack(side="left", padx=1)

        # Weeks
        semanas = _cal.monthcalendar(estado["year"], estado["month"])
        hoy = datetime.now()
        sel_str = var_fecha.get().strip()
        for sem in semanas:
            fila = tk.Frame(contenedor, bg="white")
            fila.pack(fill="x", pady=1)
            for dia in sem:
                if dia == 0:
                    tk.Label(fila, text="", width=3, bg="white").pack(side="left", padx=1)
                else:
                    es_hoy = (dia == hoy.day and estado["month"] == hoy.month
                              and estado["year"] == hoy.year)
                    es_sel = (sel_str ==
                              f"{estado['year']:04d}-{estado['month']:02d}-{dia:02d}")
                    bg_d = COLOR_AZUL_IPSD if es_sel else ("#E6F0FA" if es_hoy else "#F5F5F5")
                    fg_d = "white" if es_sel else COLOR_AZUL_IPSD
                    tk.Button(
                        fila, text=str(dia), width=3,
                        font=("Segoe UI", 9),
                        bg=bg_d, fg=fg_d, relief="flat", bd=0,
                        activebackground="#13689E", activeforeground="white",
                        command=lambda d2=dia: _seleccionar(d2)
                    ).pack(side="left", padx=1)

        # Footer: botón "Hoy"
        tk.Button(contenedor, text="Hoy",
                  font=("Segoe UI", 9), bg="#EEEEEE", fg=COLOR_AZUL_IPSD,
                  relief="flat", bd=0,
                  command=lambda: _seleccionar(datetime.now().day,
                                               datetime.now().month,
                                               datetime.now().year)
                  ).pack(pady=(4, 0))

    def _cambiar(delta):
        estado["month"] += delta
        if estado["month"] > 12:
            estado["month"] = 1
            estado["year"] += 1
        elif estado["month"] < 1:
            estado["month"] = 12
            estado["year"] -= 1
        _render()

    def _cambiar_anio(delta):
        estado["year"] += delta
        _render()

    def _seleccionar(dia, mes=None, year=None):
        m = mes or estado["month"]
        y = year or estado["year"]
        var_fecha.set(f"{y:04d}-{m:02d}-{dia:02d}")
        if on_change:
            on_change()
        popup.destroy()

    _render()


# ═════════════════════════════════════════════════════════════════════════════
# CLASE: VENTANA CONSULTA SEPARACIÓN DE DOCUMENTOS
# ═════════════════════════════════════════════════════════════════════════════

class VentanaConsultaSeparacion(ctk.CTkToplevel):
    """
    Ventana modal para consultar si dos documentos del mismo tipo deben separarse.
    
    Muestra comparación lado a lado (ej: LISTA_ASISTENCIA vs LISTA_ASISTENCIA)
    y permite al usuario decidir si son el MISMO documento o DOCUMENTOS DIFERENTES.
    """
    
    def __init__(self, parent, pdf_ruta: Path, tipo_doc: str,
                 num_pagina_anterior: int, num_pagina_actual: int,
                 modo_lista: bool = False):
        super().__init__(parent)
        
        self.pdf_ruta = pdf_ruta
        self.tipo_doc = tipo_doc
        self.num_pagina_anterior = num_pagina_anterior
        self.num_pagina_actual = num_pagina_actual
        self.modo_lista = modo_lista
        self.decision = None  # "mismo" o "diferente"
        
        # Configuración ventana
        if self.modo_lista:
            self.title("Consulta de Agrupación: LISTA_ASISTENCIA - Lector V3")
        else:
            self.title(f"Consulta: ¿Son el MISMO {tipo_doc}? - Lector V3")
        self.resizable(True, True)
        self.minsize(800, 650)
        self.configure(fg_color=COLOR_GRIS_FONDO)
        
        # Centrar ventana
        _W, _H = 1000, 750
        self.update_idletasks()
        _sw = self.winfo_screenwidth()
        _sh = self.winfo_screenheight()
        _px = (_sw - _W) // 2
        _py = (_sh - _H) // 2
        self.geometry(f"{_W}x{_H}+{_px}+{_py}")
        
        # Modal
        self.transient(parent)
        self.grab_set()
        _set_app_icon(self, delay=150)
        
        self._crear_interfaz()
    
    def _crear_interfaz(self):
        """Crea la interfaz de la ventana."""
        
        # ===== HEADER =====
        header_frame = ctk.CTkFrame(self, fg_color=COLOR_AZUL_IPSD, corner_radius=0)
        header_frame.pack(fill="x", padx=0, pady=0)
        
        ctk.CTkLabel(
            header_frame,
            text=(
                "❓ ¿Cómo deseas agrupar esta LISTA_ASISTENCIA?"
                if self.modo_lista else f"❓ ¿Son el MISMO {self.tipo_doc}?"
            ),
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLOR_BLANCO
        ).pack(pady=12)
        
        # ===== INFO =====
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(fill="x", padx=20, pady=(8, 0))
        
        ctk.CTkLabel(
            info_frame,
            text=f"Página {self.num_pagina_anterior} vs página {self.num_pagina_actual}",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLOR_AZUL_IPSD
        ).pack()
        
        # ===== BOTONES (ABAJO) =====
        botones_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=0)
        botones_frame.pack(fill="x", side="bottom", padx=0, pady=0)
        
        tk.Frame(botones_frame, bg="#E0E0E0", height=1).pack(fill="x")
        
        ctk.CTkLabel(
            botones_frame,
            text=(
                f"¿Qué hacer con la página {self.num_pagina_actual} de asistencia?"
                if self.modo_lista else
                f"¿Es la página {self.num_pagina_actual} parte del MISMO {self.tipo_doc} o es NUEVO?"
            ),
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLOR_GRIS_TEXTO
        ).pack(pady=(10, 6))
        
        botones_accion = ctk.CTkFrame(botones_frame, fg_color="transparent")
        botones_accion.pack(pady=(0, 12))
        
        if self.modo_lista:
            ctk.CTkButton(
                botones_accion,
                text="📎 Anexar al anterior",
                command=lambda: self._tomar_decision("anexar_anterior"),
                fg_color=COLOR_VERDE_IPSD,
                hover_color="#7AA020",
                width=200,
                height=55,
                corner_radius=10,
                font=ctk.CTkFont(size=11, weight="bold")
            ).pack(side="left", padx=6)

            ctk.CTkButton(
                botones_accion,
                text="� Añadir en archivo nuevo",
                command=lambda: self._tomar_decision("nueva_lista"),
                fg_color="#FF6B00",
                hover_color="#CC5500",
                width=220,
                height=55,
                corner_radius=10,
                font=ctk.CTkFont(size=11, weight="bold")
            ).pack(side="left", padx=6)

            ctk.CTkButton(
                botones_accion,
                text="➕ Unir a la Lista Anterior",
                command=lambda: self._tomar_decision("unir_lista_anterior"),
                fg_color=COLOR_AZUL_IPSD,
                hover_color="#002550",
                width=210,
                height=55,
                corner_radius=10,
                font=ctk.CTkFont(size=11, weight="bold")
            ).pack(side="left", padx=6)
        else:
            ctk.CTkButton(
                botones_accion,
                text="✅ Es el MISMO\n(Parte del documento)",
                command=lambda: self._tomar_decision("mismo"),
                fg_color=COLOR_VERDE_IPSD,
                hover_color="#7AA020",
                width=195,
                height=55,
                corner_radius=10,
                font=ctk.CTkFont(size=11, weight="bold")
            ).pack(side="left", padx=6)

            ctk.CTkButton(
                botones_accion,
                text="🆕 Es DIFERENTE\n(Nuevo documento)",
                command=lambda: self._tomar_decision("diferente"),
                fg_color="#FF6B00",
                hover_color="#CC5500",
                width=195,
                height=55,
                corner_radius=10,
                font=ctk.CTkFont(size=11, weight="bold")
            ).pack(side="left", padx=6)
        
        # ===== COMPARACIÓN (CENTRO) =====
        comparacion_frame = ctk.CTkFrame(self)
        comparacion_frame.pack(fill="both", expand=True, padx=15, pady=8)
        
        # Anterior (izquierda)
        doc_ant_frame = ctk.CTkFrame(comparacion_frame)
        doc_ant_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        ctk.CTkLabel(
            doc_ant_frame,
            text="📄 ANTERIOR",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLOR_AZUL_IPSD
        ).pack(pady=(8, 2))
        
        ctk.CTkLabel(
            doc_ant_frame,
            text=f"Página {self.num_pagina_anterior}",
            font=ctk.CTkFont(size=10),
            text_color=COLOR_GRIS_TEXTO
        ).pack(pady=(0, 5))
        
        # Miniatura anterior
        img_ant = _miniatura_pdf(self.pdf_ruta, self.num_pagina_anterior, max_size=(400, 430))
        if img_ant:
            self._ctk_img_ant = ctk.CTkImage(light_image=img_ant, dark_image=img_ant,
                                              size=(img_ant.width, img_ant.height))
            lbl_ant = ctk.CTkLabel(doc_ant_frame, image=self._ctk_img_ant, text="",
                                    cursor="hand2")
            lbl_ant.pack(expand=True, pady=(4, 2))
            lbl_ant.bind("<Button-1>", lambda e: _abrir_zoom_pdf(self, self.pdf_ruta, self.num_pagina_anterior))
            ctk.CTkLabel(doc_ant_frame, text="🔍 Clic para zoom",
                         font=ctk.CTkFont(size=9), text_color="#999999"
                         ).pack(pady=(0, 6))
        else:
            ctk.CTkLabel(doc_ant_frame, text="Vista previa no disponible",
                         text_color="#999999", font=ctk.CTkFont(size=11)
                         ).pack(expand=True)
        
        # Actual (derecha)
        doc_act_frame = ctk.CTkFrame(comparacion_frame)
        doc_act_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        ctk.CTkLabel(
            doc_act_frame,
            text="📄 ACTUAL",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#FF6B00"
        ).pack(pady=(8, 2))
        
        ctk.CTkLabel(
            doc_act_frame,
            text=f"Página {self.num_pagina_actual}",
            font=ctk.CTkFont(size=10),
            text_color=COLOR_GRIS_TEXTO
        ).pack(pady=(0, 5))
        
        # Miniatura actual
        img_act = _miniatura_pdf(self.pdf_ruta, self.num_pagina_actual, max_size=(400, 430))
        if img_act:
            self._ctk_img_act = ctk.CTkImage(light_image=img_act, dark_image=img_act,
                                              size=(img_act.width, img_act.height))
            lbl_act = ctk.CTkLabel(doc_act_frame, image=self._ctk_img_act, text="",
                                    cursor="hand2")
            lbl_act.pack(expand=True, pady=(4, 2))
            lbl_act.bind("<Button-1>", lambda e: _abrir_zoom_pdf(self, self.pdf_ruta, self.num_pagina_actual))
            ctk.CTkLabel(doc_act_frame, text="🔍 Clic para zoom",
                         font=ctk.CTkFont(size=9), text_color="#999999"
                         ).pack(pady=(0, 6))
        else:
            ctk.CTkLabel(doc_act_frame, text="Vista previa no disponible",
                         text_color="#999999", font=ctk.CTkFont(size=11)
                         ).pack(expand=True)
    
    def _tomar_decision(self, decision: str):
        """Registra la decisión y cierra la ventana."""
        self.decision = decision
        self.destroy()

    def obtener_decision(self) -> Optional[str]:
        """Espera a que el usuario tome una decisión."""
        self.wait_window()
        return self.decision


# ═════════════════════════════════════════════════════════════════════════════
# CLASE: VENTANA VERIFICACIÓN DUPLICADOS
# ═════════════════════════════════════════════════════════════════════════════

class VentanaVerificacion(ctk.CTkToplevel):
    """
    Ventana modal para verificación manual de duplicados.
    
    Muestra comparación lado a lado de dos documentos y permite al usuario
    decidir si son duplicados y qué acción tomar.
    """
    
    def __init__(self, parent, archivo1: Path, archivo2: Path, 
                 texto1: str, texto2: str, similitud: float):
        super().__init__(parent)
        
        self.archivo1 = archivo1
        self.archivo2 = archivo2
        self.texto1 = texto1
        self.texto2 = texto2
        self.similitud = similitud
        self.decision = None  # "mantener_ambos", "eliminar_2", "renombrar_2"
        
        # Configuración ventana
        self.title("Verificación de Duplicados - Lector V3")
        self.resizable(True, True)
        self.minsize(800, 650)
        self.configure(fg_color=COLOR_GRIS_FONDO)
        
        # Centrar ventana (calcular posición ANTES de construir la UI)
        _W, _H = 1000, 750
        self.update_idletasks()
        _sw = self.winfo_screenwidth()
        _sh = self.winfo_screenheight()
        _px = (_sw - _W) // 2
        _py = (_sh - _H) // 2
        self.geometry(f"{_W}x{_H}+{_px}+{_py}")
        
        # Modal
        self.transient(parent)
        self.grab_set()
        _set_app_icon(self, delay=150)
        
        self._crear_interfaz()
    
    def _crear_interfaz(self):
        """Crea la interfaz de la ventana."""
        
        # ===== 1. HEADER (arriba) =====
        header_frame = ctk.CTkFrame(self, fg_color=COLOR_AZUL_IPSD, corner_radius=0)
        header_frame.pack(fill="x", padx=0, pady=0)
        
        ctk.CTkLabel(
            header_frame,
            text="⚠️  POSIBLE DUPLICADO DETECTADO",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLOR_BLANCO
        ).pack(pady=12)
        
        # ===== 2. INFO SIMILITUD (arriba) =====
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(fill="x", padx=20, pady=(8, 0))
        
        ctk.CTkLabel(
            info_frame,
            text=f"Similitud detectada: {self.similitud:.1f}%",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLOR_AZUL_IPSD
        ).pack()
        
        # ===== 3. BOTONES (abajo, ANTES del frame con expand=True) =====
        # REGLA CRÍTICA: empaquetar side="bottom" ANTES del elemento expand=True
        botones_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=0)
        botones_frame.pack(fill="x", side="bottom", padx=0, pady=0)
        
        tk.Frame(botones_frame, bg="#E0E0E0", height=1).pack(fill="x")
        
        ctk.CTkLabel(
            botones_frame,
            text="¿Qué deseas hacer con el DOCUMENTO 2?",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLOR_GRIS_TEXTO
        ).pack(pady=(10, 6))
        
        botones_accion = ctk.CTkFrame(botones_frame, fg_color="transparent")
        botones_accion.pack(pady=(0, 12))
        
        ctk.CTkButton(
            botones_accion,
            text="✅ Mantener ambos\n(Son diferentes)",
            command=lambda: self._tomar_decision("mantener_ambos"),
            fg_color=COLOR_VERDE_IPSD,
            hover_color="#7AA020",
            width=195,
            height=55,
            corner_radius=10,
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(side="left", padx=6)
        
        ctk.CTkButton(
            botones_accion,
            text="🗑️ Eliminar Doc 2\n(Es duplicado exacto)",
            command=lambda: self._tomar_decision("eliminar_2"),
            fg_color="#DC3545",
            hover_color="#A02830",
            width=195,
            height=55,
            corner_radius=10,
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(side="left", padx=6)
        
        ctk.CTkButton(
            botones_accion,
            text="✏️ Renombrar Doc 2\n(Es respuesta/anexo)",
            command=lambda: self._tomar_decision("renombrar_2"),
            fg_color=COLOR_AZUL_IPSD,
            hover_color="#002550",
            width=195,
            height=55,
            corner_radius=10,
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(side="left", padx=6)
        
        # ===== 4. COMPARACIÓN (centro, expande para llenar el espacio restante) =====
        comparacion_frame = ctk.CTkFrame(self)
        comparacion_frame.pack(fill="both", expand=True, padx=15, pady=8)
        
        # Documento 1 (izquierda)
        doc1_frame = ctk.CTkFrame(comparacion_frame)
        doc1_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        ctk.CTkLabel(
            doc1_frame,
            text="📄 DOCUMENTO 1 (Original)",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLOR_AZUL_IPSD
        ).pack(pady=(8, 2))
        
        ctk.CTkLabel(
            doc1_frame,
            text=self.archivo1.name,
            font=ctk.CTkFont(size=10),
            wraplength=440,
            text_color=COLOR_GRIS_TEXTO
        ).pack(pady=(0, 5))
        
        # --- Miniatura Documento 1 ---
        img1 = _miniatura_pdf(self.archivo1, max_size=(400, 430))
        if img1:
            self._ctk_img1 = ctk.CTkImage(light_image=img1, dark_image=img1,
                                           size=(img1.width, img1.height))
            lbl1 = ctk.CTkLabel(doc1_frame, image=self._ctk_img1, text="",
                                 cursor="hand2")
            lbl1.pack(expand=True, pady=(4, 2))
            lbl1.bind("<Button-1>", lambda e: _abrir_zoom_pdf(self, self.archivo1))
            ctk.CTkLabel(doc1_frame, text="🔍 Clic para zoom",
                         font=ctk.CTkFont(size=9), text_color="#999999"
                         ).pack(pady=(0, 6))
        else:
            ctk.CTkLabel(doc1_frame, text="Vista previa no disponible",
                         text_color="#999999", font=ctk.CTkFont(size=11)
                         ).pack(expand=True)

        # Documento 2 (derecha)
        doc2_frame = ctk.CTkFrame(comparacion_frame)
        doc2_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))

        ctk.CTkLabel(
            doc2_frame,
            text="📄 DOCUMENTO 2 (Posible duplicado)",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#FF6B00"
        ).pack(pady=(8, 2))

        ctk.CTkLabel(
            doc2_frame,
            text=self.archivo2.name,
            font=ctk.CTkFont(size=10),
            wraplength=440,
            text_color=COLOR_GRIS_TEXTO
        ).pack(pady=(0, 5))

        # --- Miniatura Documento 2 ---
        img2 = _miniatura_pdf(self.archivo2, max_size=(400, 430))
        if img2:
            self._ctk_img2 = ctk.CTkImage(light_image=img2, dark_image=img2,
                                           size=(img2.width, img2.height))
            lbl2 = ctk.CTkLabel(doc2_frame, image=self._ctk_img2, text="",
                                 cursor="hand2")
            lbl2.pack(expand=True, pady=(4, 2))
            lbl2.bind("<Button-1>", lambda e: _abrir_zoom_pdf(self, self.archivo2))
            ctk.CTkLabel(doc2_frame, text="🔍 Clic para zoom",
                         font=ctk.CTkFont(size=9), text_color="#999999"
                         ).pack(pady=(0, 6))
        else:
            ctk.CTkLabel(doc2_frame, text="Vista previa no disponible",
                         text_color="#999999", font=ctk.CTkFont(size=11)
                         ).pack(expand=True)
    
    def _tomar_decision(self, decision: str):
        """Registra la decisión del usuario y cierra la ventana."""
        self.decision = decision
        self.destroy()
    
    def obtener_decision(self) -> Optional[str]:
        """
        Espera a que el usuario tome una decisión.
        
        Returns:
            Decisión del usuario o None si cerró la ventana
        """
        self.wait_window()
        return self.decision


# ═════════════════════════════════════════════════════════════════════════════
# CLASE: VENTANA NÚMERO DUPLICADO
# ═════════════════════════════════════════════════════════════════════════════

class VentanaNumDuplicado(ctk.CTkToplevel):
    """
    Ventana modal para archivos con el mismo número de documento.
    Muestra previsualización lado a lado y permite decidir cómo proceder.
    """

    def __init__(self, parent, numero: str, tipo: str,
                 archivo_previo: str, ruta_previo: Optional[Path],
                 archivo_nuevo: str, ruta_nuevo: Optional[Path]):
        super().__init__(parent)

        self.numero       = numero
        self.tipo         = tipo
        self.archivo_previo = archivo_previo
        self.ruta_previo  = ruta_previo
        self.archivo_nuevo = archivo_nuevo
        self.ruta_nuevo   = ruta_nuevo
        self.decision     = "respuesta"  # Default al cerrar con X

        self.title("Número de documento duplicado")
        self.resizable(True, True)
        self.minsize(800, 580)
        self.configure(fg_color=COLOR_GRIS_FONDO)

        _W, _H = 1000, 700
        self.update_idletasks()
        _sw = self.winfo_screenwidth()
        _sh = self.winfo_screenheight()
        self.geometry(f"{_W}x{_H}+{(_sw - _W) // 2}+{(_sh - _H) // 2}")

        self.transient(parent)
        self.grab_set()
        _set_app_icon(self, delay=150)

        self._crear_interfaz()

    def _crear_interfaz(self):
        # ===== HEADER =====
        header = ctk.CTkFrame(self, fg_color=COLOR_AZUL_IPSD, corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(
            header,
            text="⚠️  NÚMERO DE DOCUMENTO DUPLICADO",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLOR_BLANCO
        ).pack(pady=12)

        # ===== INFO =====
        info = ctk.CTkFrame(self, fg_color="transparent")
        info.pack(fill="x", padx=20, pady=(10, 0))
        ctk.CTkLabel(
            info,
            text=f"El número  '{self.numero}'  ({self.tipo})  ya fue registrado anteriormente.",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLOR_AZUL_IPSD
        ).pack()
        ctk.CTkLabel(
            info,
            text="¿El archivo nuevo es una RESPUESTA o ANEXO del anterior?",
            font=ctk.CTkFont(size=12),
            text_color=COLOR_GRIS_TEXTO
        ).pack(pady=(4, 0))

        # ===== BOTONES (side=bottom, ANTES del expand) =====
        botones_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=0)
        botones_frame.pack(fill="x", side="bottom")
        tk.Frame(botones_frame, bg="#E0E0E0", height=1).pack(fill="x")
        ctk.CTkLabel(
            botones_frame,
            text="¿Qué deseas hacer con el ARCHIVO NUEVO?",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLOR_GRIS_TEXTO
        ).pack(pady=(10, 6))

        btns = ctk.CTkFrame(botones_frame, fg_color="transparent")
        btns.pack(pady=(0, 12))

        ctk.CTkButton(
            btns,
            text="✏️ Guardar como RESPUESTA/ANEXO",
            command=lambda: self._tomar_decision("respuesta"),
            fg_color=COLOR_AZUL_IPSD,
            hover_color="#002550",
            width=260, height=55, corner_radius=10,
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btns,
            text="⏭️ Omitir este archivo",
            command=lambda: self._tomar_decision("omitir"),
            fg_color="#DC3545",
            hover_color="#A02830",
            width=220, height=55, corner_radius=10,
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(side="left", padx=10)

        # ===== COMPARACIÓN (centro, expande) =====
        comp = ctk.CTkFrame(self)
        comp.pack(fill="both", expand=True, padx=15, pady=8)

        # --- Archivo previo (izquierda) ---
        f1 = ctk.CTkFrame(comp)
        f1.pack(side="left", fill="both", expand=True, padx=(0, 5))
        ctk.CTkLabel(
            f1, text="📄 ARCHIVO PREVIO (Ya registrado)",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLOR_AZUL_IPSD
        ).pack(pady=(8, 2))
        ctk.CTkLabel(
            f1, text=self.archivo_previo,
            font=ctk.CTkFont(size=10), wraplength=440,
            text_color=COLOR_GRIS_TEXTO
        ).pack(pady=(0, 5))
        if self.ruta_previo and self.ruta_previo.exists():
            img1 = _miniatura_pdf(self.ruta_previo, max_size=(400, 380))
            if img1:
                self._ctk_img1 = ctk.CTkImage(light_image=img1, dark_image=img1,
                                               size=(img1.width, img1.height))
                lbl1 = ctk.CTkLabel(f1, image=self._ctk_img1, text="", cursor="hand2")
                lbl1.pack(expand=True, pady=(4, 2))
                # Usar variable local para asegurar que no es None en el lambda
                ruta_p1 = self.ruta_previo
                lbl1.bind("<Button-1>", lambda e: _abrir_zoom_pdf(self, ruta_p1))
                ctk.CTkLabel(f1, text="🔍 Clic para zoom",
                             font=ctk.CTkFont(size=9), text_color="#999999").pack(pady=(0, 6))
            else:
                ctk.CTkLabel(f1, text="Vista previa no disponible",
                             text_color="#999999", font=ctk.CTkFont(size=11)).pack(expand=True)
        else:
            ctk.CTkLabel(f1, text="Vista previa no disponible",
                         text_color="#999999", font=ctk.CTkFont(size=11)).pack(expand=True)

        # --- Archivo nuevo (derecha) ---
        f2 = ctk.CTkFrame(comp)
        f2.pack(side="right", fill="both", expand=True, padx=(5, 0))
        ctk.CTkLabel(
            f2, text="📄 ARCHIVO NUEVO (Ingresado ahora)",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#FF6B00"
        ).pack(pady=(8, 2))
        ctk.CTkLabel(
            f2, text=self.archivo_nuevo,
            font=ctk.CTkFont(size=10), wraplength=440,
            text_color=COLOR_GRIS_TEXTO
        ).pack(pady=(0, 5))
        if self.ruta_nuevo and self.ruta_nuevo.exists():
            img2 = _miniatura_pdf(self.ruta_nuevo, max_size=(400, 380))
            if img2:
                self._ctk_img2 = ctk.CTkImage(light_image=img2, dark_image=img2,
                                               size=(img2.width, img2.height))
                lbl2 = ctk.CTkLabel(f2, image=self._ctk_img2, text="", cursor="hand2")
                lbl2.pack(expand=True, pady=(4, 2))
                # Usar variable local para asegurar que no es None en el lambda
                ruta_p2 = self.ruta_nuevo
                lbl2.bind("<Button-1>", lambda e: _abrir_zoom_pdf(self, ruta_p2))
                ctk.CTkLabel(f2, text="🔍 Clic para zoom",
                             font=ctk.CTkFont(size=9), text_color="#999999").pack(pady=(0, 6))
            else:
                ctk.CTkLabel(f2, text="Vista previa no disponible",
                             text_color="#999999", font=ctk.CTkFont(size=11)).pack(expand=True)
        else:
            ctk.CTkLabel(f2, text="Vista previa no disponible",
                         text_color="#999999", font=ctk.CTkFont(size=11)).pack(expand=True)

    def _tomar_decision(self, decision: str):
        self.decision = decision
        self.destroy()

    def obtener_decision(self) -> str:
        self.wait_window()
        return self.decision
