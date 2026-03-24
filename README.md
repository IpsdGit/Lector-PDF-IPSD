# Lector de PDFs V3.0 - IPSD

Sistema avanzado de lectura, clasificación y segmentación inteligente de documentos PDF para el Instituto de Profesionalización y Superación Docente (IPSD) de la UNAH.

## 🎯 Características

- ✅ **Sistema de 4 capas de verificación** (hash → fuzzy → semántica → manual)
- ✅ **UI profesional** con CustomTkinter (Material Design)
- ✅ **Sistema de metadata JSON** para auditoría completa
- ✅ **Manejo robusto de errores OCR** con Tesseract
- ✅ **Logging detallado** de todas las operaciones
- ✅ **Ventanas modales** para verificación manual de duplicados
- ✅ **Preservación de documentos** (no elimina sin confirmación)
- ✅ **Branding institucional** UNAH/VRA

## 📋 Requisitos

- Python 3.13+
- Windows 10/11
- 2GB RAM mínimo
- Tesseract-OCR (incluido)
- Poppler (incluido)

## 🚀 Instalación

### 1. Clonar el repositorio
```bash
git clone https://github.com/tu-usuario/Lector-PDF-IPSD.git
cd Lector-PDF-IPSD
```

### 2. Crear entorno virtual
```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Ejecutar la aplicación
```bash
python Cuerpo/main.py
```

O usar el script batch:
```bash
EJECUTAR_V3.bat
```

## 📁 Estructura del Proyecto

```
Lector_PDF_IPSD_V3/
├── Cuerpo/                          # Código principal
│   ├── main.py                      # Interfaz principal
│   ├── config.py                    # Configuración global
│   ├── core/
│   │   ├── pdf_logic.py             # Lógica de procesamiento PDF
│   │   └── ocr_engine.py            # Motor OCR con Tesseract
│   ├── ui/
│   │   └── modals.py                # Ventanas modales
│   ├── Tesseract-OCR/               # Motor OCR local
│   └── poppler/                     # Herramienta conversión PDF
├── Assets/                          # Logo e imágenes
├── requirements.txt                 # Dependencias Python
├── INSTALACION.md                   # Guía detallada
├── ANALISIS_FUNCIONAMIENTO_V3.md    # Análisis técnico
└── EJECUTAR_V3.bat                  # Script de ejecución
```

## 🔧 Configuración

Editar [Cuerpo/config.py](Cuerpo/config.py) para personalizar:
- Colores institucionales
- Tipos de documentos predefinidos
- Siglas administrativas
- Rutas de herramientas externas

## 💡 Uso

1. **Seleccionar carpeta** con PDFs a procesar
2. El sistema **detecta automáticamente**:
   - Tipo de documento (OFICIO, CIRCULAR, etc.)
   - Números de referencia
   - Fechas y departamentos
3. **Verifica automaticamente** duplicados en 4 capas
4. **Segmenta inteligentemente** PDFs con múltiples documentos
5. **Genera metadata JSON** para auditoría

## 📊 Flujo de Procesamiento

```
PDF Entrada
    ↓
[1] Hash MD5 (detección duplicado exacto)
    ↓
[2] Fuzzy Matching (similitud textual)
    ↓
[3] Verificación Semántica (UI manual)
    ↓
[4] OCR con Tesseract
    ↓
Clasificación + Segmentación
    ↓
Metadata JSON + PDF Procesado
```

## 🎓 Documentación Técnica

- [INSTALACION.md](INSTALACION.md) - Guía de instalación detallada
- [ANALISIS_FUNCIONAMIENTO_V3.md](ANALISIS_FUNCIONAMIENTO_V3.md) - Análisis arquitectónico
- [ANALISIS_UI_MEJORA.md](ANALISIS_UI_MEJORA.md) - Propuestas de mejora
- [ESPECIFICACION_SEPARADOR_PDF_COMPILADO.md](ESPECIFICACION_SEPARADOR_PDF_COMPILADO.md) - Especificación de separación

## 👤 Autor

Desarrollado para IPSD - Universidad Nacional Autónoma de Honduras (UNAH)
Versión 3.0 - Marzo 2026

## 📄 Licencia

[Especificar licencia - MIT, GPL, Privado, etc.]

## 📞 Soporte

Para reportar problemas o sugerencias: crear un Issue en este repositorio.

---

**⚠️ Nota Importante:** Este proyecto requiere Tesseract-OCR y Poppler. Ambos están incluidos en el paquete. Si tienes problemas, consulta [INSTALACION.md](INSTALACION.md).
