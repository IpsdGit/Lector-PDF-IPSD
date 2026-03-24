"""
=============================================================================
PAQUETE CORE - Lógica de procesamiento PDF y OCR
=============================================================================

Módulo que re-exporta funciones y clases públicas de:
- pdf_logic: Funciones de bajo nivel para procesamiento de PDFs
- ocr_engine: Motor OCR para extracción de texto
"""

# Re-exportar funciones públicas de pdf_logic
from core.pdf_logic import (
    calcular_hash_md5,
    guardar_metadata,
    cargar_metadata,
    detectar_tipo_documento,
    buscar_numero_documento,
    buscar_departamento,
    buscar_fecha,
    generar_nombre_limpio,
    detectar_cambios_tipo_pdf,
    extraer_paginas_por_tipo,
)

# Re-exportar funciones públicas de ocr_engine
from core.ocr_engine import (
    extraer_texto_ocr,
    extraer_texto_ocr_pagina,
    _miniatura_pdf,
)

# Definir qué se exporta con "from core import *"
__all__ = [
    # pdf_logic
    "calcular_hash_md5",
    "guardar_metadata",
    "cargar_metadata",
    "detectar_tipo_documento",
    "buscar_numero_documento",
    "buscar_departamento",
    "buscar_fecha",
    "generar_nombre_limpio",
    "detectar_cambios_tipo_pdf",
    "extraer_paginas_por_tipo",
    # ocr_engine
    "extraer_texto_ocr",
    "extraer_texto_ocr_pagina",
    "_miniatura_pdf",
]
