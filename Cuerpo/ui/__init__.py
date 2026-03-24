"""
=============================================================================
PAQUETE UI - Interfaces gráficas y componentes visuales
=============================================================================

Módulo que re-exporta clases y funciones públicas de:
- modals: Ventanas modales y utilidades de interfaz usuario
"""

# Re-exportar clases de ventanas modales
from ui.modals import (
    VentanaConsultaSeparacion,
    VentanaVerificacion,
    VentanaNumDuplicado,
)

# Re-exportar funciones auxiliares
from ui.modals import (
    _preparar_icono,
    _set_app_icon,
    _abrir_zoom_pdf,
    _abrir_calendario,
)

# Definir qué se exporta con "from ui import *"
__all__ = [
    # Clases modales
    "VentanaConsultaSeparacion",
    "VentanaVerificacion",
    "VentanaNumDuplicado",
    # Funciones helper
    "_preparar_icono",
    "_set_app_icon",
    "_abrir_zoom_pdf",
    "_abrir_calendario",
]
