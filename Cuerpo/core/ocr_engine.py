"""
=============================================================================
MOTOR OCR - Funciones de extracción de texto
=============================================================================

Módulo que contiene:
- Extracción de texto OCR de PDFs
- Generación de miniaturas para previsualización
- Funciones auxiliares para procesamiento de imágenes
"""

import logging
from pathlib import Path
from typing import Optional, Dict
from PIL import Image

import pytesseract
from pdf2image import convert_from_path

from config import POPPLER_PATH

# Caché global para miniaturas
_MINIATURA_CACHE: Dict[tuple, Optional[Image.Image]] = {}


def extraer_texto_ocr(ruta_pdf: Path, logger: logging.Logger) -> str:
    """
    Extrae texto de un PDF usando OCR (Tesseract).
    
    Args:
        ruta_pdf: Ruta del archivo PDF
        logger: Logger para registrar operaciones
        
    Returns:
        Texto extraído o string vacío en caso de error
    """
    try:
        logger.debug(f"Iniciando OCR de: {ruta_pdf.name}")
        
        # Convertir PDF a imágenes (solo primera página para rapidez)
        poppler_path_str = str(POPPLER_PATH) if POPPLER_PATH.exists() else None
        
        imagenes = convert_from_path(
            str(ruta_pdf),
            first_page=1,
            last_page=3,  # Procesar primeras 3 páginas para mayor cobertura
            poppler_path=poppler_path_str,
            dpi=280  # DPI aumentado para mejor precisión OCR
        )
        
        if not imagenes:
            logger.warning(f"No se pudo convertir PDF a imagen: {ruta_pdf.name}")
            return ""
        
        # Aplicar OCR a las imágenes disponibles (priorizando primera página)
        textos = []
        for img in imagenes:
            texto_pagina = pytesseract.image_to_string(
                img, lang='spa', config='--oem 3 --psm 6'
            )
            textos.append(texto_pagina)
        texto = "\n".join(textos)
        
        logger.debug(f"OCR completado: {len(texto)} caracteres extraídos")
        return texto
        
    except Exception as e:
        logger.error(f"❌ Error en OCR de {ruta_pdf.name}: {type(e).__name__} - {e}")
        return ""


def extraer_texto_ocr_pagina(ruta_pdf: Path, num_pagina: int, logger: logging.Logger) -> str:
    """
    Extrae texto OCR de una sola página de un PDF.

    Args:
        ruta_pdf: Ruta del archivo PDF
        num_pagina: Número de página (1-based)
        logger: Logger para registrar operaciones

    Returns:
        Texto extraído o string vacío en caso de error
    """
    try:
        poppler_path_str = str(POPPLER_PATH) if POPPLER_PATH.exists() else None
        imagenes = convert_from_path(
            str(ruta_pdf),
            first_page=num_pagina,
            last_page=num_pagina,
            poppler_path=poppler_path_str,
            dpi=280
        )
        if not imagenes:
            return ""
        
        # Intentar OCR con múltiples configuraciones
        configs = [
            '--oem 3 --psm 6',        # Default: asume texto uniforme
            '--oem 3 --psm 11',       # Sparse text
            '--oem 3 --psm 1',        # Auto segmentation
        ]
        
        for config in configs:
            try:
                texto = pytesseract.image_to_string(
                    imagenes[0], lang='spa', config=config
                )
                if texto and len(texto.strip()) > 20:  # Si extrae algo significativo
                    return texto
            except Exception:
                continue
        
        # Si ninguna configuración funcionó bien, intentar en inglés
        try:
            texto = pytesseract.image_to_string(
                imagenes[0], lang='eng', config='--oem 3 --psm 6'
            )
            if texto and len(texto.strip()) > 20:
                return texto
        except Exception:
            pass
        
        # Si aún así no hay texto, devolver lo que sea
        return pytesseract.image_to_string(
            imagenes[0], lang='spa', config='--oem 3 --psm 6'
        )
        
    except Exception as e:
        logger.error(
            f"❌ Error OCR página {num_pagina} de {ruta_pdf.name}: {type(e).__name__} - {e}"
        )
        return ""


def _miniatura_pdf(ruta_pdf: Path, num_pagina: int = 1, max_size: tuple = (380, 460)) -> Optional[Image.Image]:
    """
    Genera una miniatura de una página específica de un PDF para previsualización en UI.
    OPTIMIZADO: Usa caché para no regenerar la misma miniatura múltiples veces.
    
    Args:
        ruta_pdf: Path del PDF
        num_pagina: Número de página (1-indexed)
        max_size: Tamaño máximo de la miniatura (ancho, alto)
        
    Retorna una PIL Image redimensionada o None si falla.
    """
    # Clave para la caché
    cache_key = (str(ruta_pdf), num_pagina, max_size)
    
    # Si ya está en caché, devolverla
    if cache_key in _MINIATURA_CACHE:
        return _MINIATURA_CACHE[cache_key]
    
    try:
        poppler_path_str = str(POPPLER_PATH) if POPPLER_PATH.exists() else None
        imagenes = convert_from_path(
            str(ruta_pdf), first_page=num_pagina, last_page=num_pagina,
            poppler_path=poppler_path_str, dpi=100
        )
        if not imagenes:
            _MINIATURA_CACHE[cache_key] = None
            return None
        img = imagenes[0].copy()
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        _MINIATURA_CACHE[cache_key] = img
        return img
    except Exception:
        _MINIATURA_CACHE[cache_key] = None
        return None
