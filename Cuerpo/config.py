"""
=============================================================================
CONFIGURACIÓN GLOBAL - LECTOR DE PDFs V3.0
Instituto de Profesionalización y Superación Docente - UNAH
=============================================================================

Módulo centralizado para:
- Rutas de herramientas externas (Tesseract, Poppler)
- Colores institucionales
- Tipos de documentos predefinidos
- Mapeos de siglas
- Configuración de CustomTkinter
"""

import pytesseract
from pathlib import Path

# =============================================================================
# RUTAS DE HERRAMIENTAS EXTERNAS
# =============================================================================

# Rutas relativas al script (carpeta Cuerpo/)
BASE_DIR_CUERPO = Path(__file__).parent  # Carpeta Cuerpo/
BASE_DIR_RAIZ = BASE_DIR_CUERPO.parent    # Carpeta Renombrador_V1/
TESSERACT_PATH = BASE_DIR_CUERPO / "Tesseract-OCR" / "tesseract.exe"
POPPLER_PATH = BASE_DIR_CUERPO / "poppler" / "Library" / "bin"
ASSETS_PATH = BASE_DIR_RAIZ / "Assets"

# Configurar Tesseract
if TESSERACT_PATH.exists():
    pytesseract.pytesseract.tesseract_cmd = str(TESSERACT_PATH)
else:
    print(f"⚠️  ADVERTENCIA: Tesseract no encontrado en {TESSERACT_PATH}")
    print("   OCR puede no funcionar correctamente.")

# =============================================================================
# COLORES INSTITUCIONALES IPSD
# =============================================================================

COLOR_AZUL_IPSD = "#003671"
COLOR_VERDE_IPSD = "#93BE27"
COLOR_BLANCO = "#FFFFFF"
COLOR_GRIS_FONDO = "#F0F0F0"
COLOR_GRIS_TEXTO = "#333333"

# =============================================================================
# TIPOS DE DOCUMENTO PREDEFINIDOS - CLASIFICACIÓN V3
# =============================================================================
# Clasificación dual: PRINCIPALES vs ADJUNTOS
# Solo cambios ENTRE estos tipos causan segmentación de PDF compilado.
# Los documentos sin tipo (genéricos) se anexan al anterior.

TIPOS_PRINCIPALES = [
    "OFICIO",
    "CIRCULAR",
    "MEMORANDUM",
    "COMUNICADO",
    "INFORME",
    "SOLICITUD",
]

TIPOS_ADJUNTOS = [
    "LISTA_ASISTENCIA",
    "CRONOGRAMA",
    "PERMISO",
    "PROPUESTA",
    "CALENDARIO",
    "PROGRAMA",
    "OTROS",
]

# Conjunto para compatibilidad hacia atrás
TIPOS_PREDEFINIDOS = {
    "OFICIO",
    "CIRCULAR",
    "DICTAMEN",
    "MEMORANDUM",
    "ACUERDO_COMPROMISO",
    "LISTA_ASISTENCIA",
    "ACUERDO_INTERNACIONAL",
    "RESOLUCION",
    "ACTA",
    "INFORME",
    "SOLICITUD",
    "CONTRATO",
    "COMUNICADO",
    "CRONOGRAMA",
    "PERMISO",
    "PROPUESTA",
    "CALENDARIO",
    "PROGRAMA",
    "OTROS",
}

# =============================================================================
# MAPEO DE TIPO DE DOCUMENTO A SIGLAS ADMINISTRATIVAS
# =============================================================================

SIGLAS_DOCUMENTO = {
    "OFICIO": "OF",
    "CIRCULAR": "CIR",
    "DICTAMEN": "DIC",
    "MEMORANDUM": "MEMO",
    "ACUERDO_COMPROMISO": "AC",
    "LISTA_ASISTENCIA": "LA",
    "ACUERDO_INTERNACIONAL": "ACI",
    "RESOLUCION": "RES",
    "ACTA": "ACT",
    "INFORME": "INF",
    "SOLICITUD": "SOL",
    "CONTRATO": "CONT",
    "COMUNICADO": "COM",
    "CRONOGRAMA": "CRO",
    "PERMISO": "PRM",
    "PROPUESTA": "PROP",
    "CALENDARIO": "CAL",
    "PROGRAMA": "PROG",
    "OTROS": "OTR",
    "DOCUMENTO": "DOC",
}

# =============================================================================
# CONFIGURACIÓN DE CUSTOMTKINTER
# =============================================================================

import customtkinter as ctk

ctk.set_appearance_mode("light")  # light, dark, system
ctk.set_default_color_theme("blue")
