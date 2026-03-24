# 📦 Instrucciones de Instalación - Renombrador de PDFs V3

**Instituto de Profesionalización y Superación Docente (IPSD)**  
**Universidad Nacional Autónoma de Honduras**

---

## ✅ Dependencias Instaladas

Las siguientes librerías Python han sido instaladas correctamente en este proyecto:

| Librería | Versión | Propósito |
|----------|---------|-----------|
| **customtkinter** | 5.2.2 | UI moderna y profesional |
| **pytesseract** | 0.3.13 | OCR (reconocimiento de texto) |
| **pdf2image** | 1.17.0 | Conversión PDF a imágenes |
| **fuzzywuzzy** | 0.18.0 | Comparación de similitud de texto |
| **python-Levenshtein** | 0.27.3 | Acelera fuzzywuzzy |
| **Pillow** | 12.1.1 | Procesamiento de imágenes |

### Librerías Built-in (No requieren instalación)
- `hashlib` - Hash MD5/SHA256 para comparar archivos
- `json` - Metadata y auditoría
- `queue` - Cola thread-safe para decisiones
- `logging` - Sistema de logs profesional
- `threading` - Procesamiento no bloqueante
- `tkinter` - Interfaz gráfica (viene con Python)

---

## 🔧 Herramientas Externas Requeridas

### 1. **Tesseract-OCR** ✅ Incluido
- **Ubicación**: `Tesseract-OCR/`
- **Ejecutable**: `Tesseract-OCR/tesseract.exe`
- **tessdata**: `Tesseract-OCR/tessdata/`
- **Idiomas**: Español (spa), Inglés (eng)

### 2. **Poppler** ✅ Incluido
- **Ubicación**: `poppler/Library/bin/`
- **Propósito**: Procesamiento de PDFs

---

## 📁 Estructura del Proyecto

```
Renombrador_V1/
├─ Assets/                      # NUEVO: Logos e imágenes
│  ├─ LOGOS-VRA-DC-UNAH (1).png
│  ├─ Logo_App.png
│  └─ Fondo_App.jpeg (opcional)
│
├─ Cuerpo/
│  └─ renombrador_pdfs.py       # Versión 1 original
│
├─ Tesseract-OCR/               # OCR incluido
│  ├─ tesseract.exe
│  └─ tessdata/
│     ├─ spa.traineddata
│     └─ eng.traineddata
│
├─ poppler/                     # Poppler incluido
│  └─ Library/bin/
│
├─ renombrador_pdfs_2.py        # Versión 2
├─ renombrador_pdfs_v3.py       # PRÓXIMO: Versión 3
├─ requirements.txt             # Dependencias Python
└─ INSTALACION.md              # Este archivo
```

---

## 🚀 Próximos Pasos

### Para ejecutar V3 (cuando esté implementada):

```bash
python renombrador_pdfs_v3.py
```

O usando el ejecutable Python específico:

```bash
C:/Users/Carlo/.local/bin/python3.14.exe renombrador_pdfs_v3.py
```

---

## 🎨 Assets Necesarios

Necesitas copiar los siguientes archivos a la carpeta `Assets/`:

1. **LOGOS-VRA-DC-UNAH (1).png**
   - Logo institucional UNAH
   - Ubicación en header (izquierda)

2. **Logo_App.png**
   - Logo de la aplicación
   - Ubicación en header (derecha)

3. **Fondo_App.jpeg** (Opcional)
   - Fondo para efectos visuales
   - Se puede usar degradado si no está disponible

**Copiar desde:**
```
c:\Users\Carlo\Desktop\Práctica-IPSD\Herramientas\Convertidor PDF\Assets\
```

---

## 🔄 Reinstalar Dependencias (si es necesario)

Si necesitas reinstalar todas las dependencias:

```bash
C:/Users/Carlo/.local/bin/python3.14.exe -m pip install -r requirements.txt
```

---

## ✅ Verificación de Instalación

Para verificar que todo está instalado correctamente:

```bash
C:/Users/Carlo/.local/bin/python3.14.exe -c "import customtkinter; import pytesseract; import pdf2image; print('✓ Todas las dependencias instaladas correctamente')"
```

---

## 📋 Resumen de Estado

- ✅ Python 3.14.3 configurado
- ✅ CustomTkinter instalado
- ✅ Librerías de OCR y procesamiento instaladas
- ✅ Tesseract-OCR disponible
- ✅ Poppler disponible
- ✅ Carpeta Assets creada
- ⏳ Pendiente: Copiar logos a Assets/
- ⏳ Pendiente: Implementar V3

---

**Instalación completada:** 9 de Marzo de 2026
