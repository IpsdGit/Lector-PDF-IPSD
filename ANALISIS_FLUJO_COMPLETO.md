# 📊 ANÁLISIS COMPLETO DEL FLUJO DE PROCESAMIENTO - Lector PDF V3

> Análisis en profundidad de cómo funciona el sistema cuando se selecciona un archivo, cómo se analiza, qué ventanas se abren, cómo se renombra y qué ocurre con adjuntos.

## 🎯 ÍNDICE
1. [Flujo General de Procesamiento](#1-flujo-general-de-procesamiento)
2. [Análisis por Etapa](#2-análisis-por-etapa)
3. [Definición de Textos y Mensajes](#3-definición-de-textos-y-mensajes)
4. [Sistema de Ventanas Modales](#4-sistema-de-ventanas-modales)
5. [Lógica de Renombrado](#5-lógica-de-renombrado)
6. [Manejo de Adjuntos vs Principales](#6-manejo-de-adjuntos-vs-principales)
7. [Puntos de Quiebre y Decisiones](#7-puntos-de-quiebre-y-decisiones)

---

## 1. FLUJO GENERAL DE PROCESAMIENTO

### 🔄 Vista Macroestructura (Orden de Ejecución)

```
┌─────────────────────────────────────────────────────────────┐
│ 1. USUARIO SELECCIONA CARPETAS DE ENTRADA Y SALIDA         │
│    (Carpeta → archivos PDF de entrada)                      │
│    (Carpeta → destino de archivos procesados)               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. USUARIO HACE CLIC EN "PROCESAR"                          │
│    - Se valida que ambas carpetas existan                   │
│    - Se pide confirmación final                             │
│    - Se inicia HILO SECUNDARIO para procesamiento           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. ETAPA PREVIA: DETECCIÓN DE SEGMENTACIÓN                 │
│    Para CADA PDF original:                                  │
│    - Detectar si contiene múltiples documentos              │
│    - Si sí → Preguntar al usuario DÓNDE SEPARAR           │
│    - Si no → Pasar al siguiente sin cambios                │
│                                                              │
│    SALIDA: Lista de PDFs (algunos serán segmentos nuevos)  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. PROCESAMIENTO INDIVIDUAL (Por cada PDF)                 │
│    ┌──────────────────────────────────────────────────┐    │
│    │ A) EXTRACCIÓN OCR                               │    │
│    │    - Leer PDF → Convertir a imagen              │    │
│    │    - OCR con Tesseract                          │    │
│    │    - Resultado: texto plano                     │    │
│    └──────────────────────────────────────────────────┘    │
│                     ↓                                        │
│    ┌──────────────────────────────────────────────────┐    │
│    │ B) ANÁLISIS DE METADATOS                         │    │
│    │    - Tipo documento (OFICIO, CIRCULAR, etc)    │    │
│    │    - Número del documento                       │    │
│    │    - Fecha                                      │    │
│    │    - Departamento                               │    │
│    │    - Hash MD5 (para duplicados)                │    │
│    └──────────────────────────────────────────────────┘    │
│                     ↓                                        │
│    ┌──────────────────────────────────────────────────┐    │
│    │ C) 4 CAPAS DE VERIFICACIÓN                       │    │
│    │                                                  │    │
│    │ CAPA 1: Hash Exacto (¿Mismo archivo binario?)  │    │
│    │ CAPA 2: Número Duplicado (¿Mismo nº procesado?)│    │
│    │ CAPA 3: Fuzzy (¿Similitud > 70% con anterior?) │    │
│    │ CAPA 4: Visual (Zoom + Decisión manual)        │    │
│    │                                                  │    │
│    │ Si algo coincide → Abrir ventana MODAL          │    │
│    └──────────────────────────────────────────────────┘    │
│                     ↓                                        │
│    ┌──────────────────────────────────────────────────┐    │
│    │ D) EDICIÓN UI INTERACTIVA                        │    │
│    │    - Ventana para editar tipo/número/fecha...   │    │
│    │    - Decidir si es ADJUNTO o PRINCIPAL          │    │
│    └──────────────────────────────────────────────────┘    │
│                     ↓                                        │
│    ┌──────────────────────────────────────────────────┐    │
│    │ E) ACCIÓN FINAL                                 │    │
│    │    SI es ADJUNTO:                               │    │
│    │      → FUSIONAR con PDF principal (PyPDF2)     │    │
│    │    SI es PRINCIPAL:                             │    │
│    │      → COPIAR a carpeta salida con nuevo nombre │    │
│    │      → Guardar JSON metadata                    │    │
│    └──────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. RESUMEN FINAL                                            │
│    - Total procesados                                       │
│    - Total duplicados omitidos                              │
│    - Total renombrados                                      │
│    - Botón para copiar LOG                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. ANÁLISIS POR ETAPA

### ETAPA 0: Interfaz Principal (main.py - __init__)

**Archivos clave:** `Cuerpo/main.py` líneas 155-180

```python
# Variables de clase críticas:
self.carpeta_entrada: Optional[Path] = None       # Ruta donde estan PDFs originales
self.carpeta_salida: Optional[Path] = None        # Ruta donde salen PDFs renombrados
self.historial_principales = []                   # Lista de PDFs principales guardados
self._es_adjunto_editado: bool = False            # Flag: ¿El usuario marcó como ADJUNTO?
self._principal_editado: Optional[Path] = None    # Si es adjunto, ¿A cuál PDF se anexa?
```

**UI Elementos:**
- 2 **CARDS** (campos de selección) con botones para elegir carpetas
- 1 **BOTÓN PROCESAR** que valida y lanza el hilo de procesamiento
- 1 **PROGRESS BAR** que sube según avanzan los archivos
- 1 **CONSOLA** (ScrolledText) que muestra logs en tiempo real

---

### ETAPA 1: PRE-PROCESAMIENTO - Detección de Segmentación

**Ubicación:** `Cuerpo/main.py` líneas 770-820

**Qué hace:**
- Para **CADA PDF original**, llama a `detectar_cambios_tipo_pdf()` 
- Respuesta: ¿Necesita separación? ¿Puntos dudosos?

**Ejemplo práctico:**
```
Archivo: reporte_completo.pdf (5 páginas)
├─ Página 1-2: OFICIO 045 (Confirmación de reunión)
├─ Página 3: LISTA_ASISTENCIA (Asistieron 24 personal)
│  └─> CAMBIO DETECTADO → Mostrar VentanaConsultaSeparacion
├─ Página 4-5: OFICIO 046 (Continuación?)
│  └─> CAMBIO DETECTADO → Mostrar VentanaConsultaSeparacion

RESULT: 2 Puntos cuestionables
        Usuario debe decidir 2 veces si SEPARAR o MANTENER
        → Puede resultar en 3 PDFs segmentados
```

**Función clave:**
```python
def detectar_cambios_tipo_pdf(ruta_pdf: Path, logger: logging.Logger) -> dict:
    # Analiza TODAS las páginas
    # Retorna: {'necesita_segmentacion': bool, 'puntos_cuestionables': [...]}
```

**Si necesita segmentación:**
- Para cada punto cuestionable → Abre `VentanaConsultaSeparacion`
- Usuario elige: "SEPARAR" | "MANTENER" | "ANEXAR" | "NUEVA LISTA"
- Las decisiones se guardan en `decisiones_usuario = {}`
- Luego se llama a `extraer_paginas_por_tipo()` que crea los segmentos

---

### ETAPA 2: EXTRACCIÓN OCR Y ANÁLISIS

**Ubicación:** `Cuerpo/main.py` líneas 850-880

Para cada PDF (incluyendo los segmentados):

#### A) Extracción de Texto
```python
texto = extraer_texto_ocr(pdf, self.logger)
```

**Ubicación:** `Cuerpo/core/ocr_engine.py`

- Convierte 1ª página a imagen (280 DPI para precisión)
- Usa pytesseract para OCR
- Si la imagen es muy clara → También intenta extraer texto nativo de PDF
- **Resultado:** String con todo el texto legible

#### B) Análisis de Metadatos
```python
tipo_doc = detectar_tipo_documento(texto)      # "OFICIO", "CIRCULAR", etc
fecha = buscar_fecha(texto)                    # "2024-03-15"
numero_doc = buscar_numero_documento(texto)    # "045", "DOC-2024-001", etc
depto = buscar_departamento(texto)             # "RECURSOS HUMANOS", etc
hash_md5 = calcular_hash_md5(pdf)              # Hash para duplicados exactos
```

**Ubicación:** `Cuerpo/core/pdf_logic.py` líneas 150-280

**Cómo funcionan:**

| Función | Qué busca | Ejemplo |
|---------|-----------|---------|
| `detectar_tipo_documento()` | Palabra clave en texto | Si dice "OFICIO" → OFICIO; si dice "CIRCULAR" → CIRCULAR |
| `buscar_numero_documento()` | Patrón de número | "OFICIO Nº 045/2024" → Extrae "045" |
| `buscar_fecha()` | Patrón de fecha | "San Salvador, 15 de marzo de 2024" → "2024-03-15" |
| `buscar_departamento()` | Menciona oficina | "Depto. de RR.HH" → "RECURSOS HUMANOS" |
| `calcular_hash_md5()` | Lee archivo binario | Génera hash único del archivo |

**Log de consola en esta etapa:**
```
ℹ️ Tipo: OFICIO | Nº: 045 | Depto: RECURSOS HUMANOS | Fecha: 2024-03-15
```

---

### ETAPA 3: 4 CAPAS DE VERIFICACIÓN

**Ubicación:** `Cuerpo/main.py` líneas 880-1050

#### CAPA 1: Hash Exacto (¿Archivo duplicado binario?)

```python
duplicado_hash = None
for nombre, info in archivos_procesados.items():
    if info['hash'] == hash_md5:
        duplicado_hash = nombre
        break

if duplicado_hash:
    # VENTANA MODAL: VentanaVerificacion
    decision = self._verificar_duplicado_ui(...)
    # Usuario elige: "ELIMINAR el nuevo" | "ELIMINAR el antiguo" | "MANTENER ambos"
```

**Caso:** Mismo archivo duplicado (byte a byte idéntico)  
**Acción:** Abrir modal con vista previa visual

---

#### CAPA 2: Número Duplicado (¿Ya procesamos ese número?)

```python
clave_numero = (tipo_doc, numero_doc)
if clave_numero in numeros_vistos:
    nombre_previo = numeros_vistos[clave_numero]
    # VENTANA MODAL: VentanaNumDuplicado
    decision = self._preguntar_numero_duplicado_ui(...)
    # Usuario elige: "Marcar como RESPUESTA" | "Marcar como ANEXO" | "DESCARTAR"
```

**Caso:** OFICIO 045 ya existe, llega otro OFICIO 045  
**Acción:** Probablemente es una respuesta o anexo  
**Resultado:** Archivo se guarda con sufijo "RESPUESTA" o "ANEXO"

---

#### CAPA 3: Fuzzy Matching (¿Similitud > 70%?)

```python
similitud_maxima = 0
for nombre, info in archivos_procesados.items():
    similitud = fuzz.ratio(texto[:1000], info['texto'][:1000])
    if similitud > similitud_maxima:
        similitud_maxima = similitud

if similitud_maxima > 70:
    # VENTANA MODAL: VentanaVerificacion
    decision = self._verificar_duplicado_ui(...)
    # "Este documento es muy similar a uno anterior (75%)"
```

**Caso:** Mismo contenido pero diferente resolución/escaneo  
**Acción:** Comparación visual lado a lado con ZOOM

---

#### CAPA 4: Verificación Visual (Zoom + Decisión)

```python
def _verificar_duplicado_ui(ruta_anterior, ruta_nuevo, texto_anterior, texto_nuevo, similitud):
    # Abre ventana modal
    # LADO IZQUIERDO: Miniatura de anterior + botón ZOOM
    # LADO DERECHO: Miniatura de nuevo + botón ZOOM
    # Usuario puede hacer ZOOM (scroll con rueda, pan con arrastrar)
    # Botones finales: "Mismo (Descartar nuevo)" | "Diferente (Mantener ambos)" | "Es Respuesta"
```

**Ubicación:** `Cuerpo/ui/modals.py` - Clase `VentanaVerificacion`

---

### ETAPA 4: EDICIÓN INTERACTIVA (Renombrado Manual)

**Ubicación:** `Cuerpo/main.py` líneas 1050-1080

```python
self._tipo_doc_editado = tipo_doc
nombre_editado = self._editar_nombre_ui(
    tipo_doc, fecha, numero_doc, depto, sufijo_final, texto, pdf
)

if nombre_editado:
    nombre_nuevo = nombre_editado
    tipo_doc = self._tipo_doc_editado
```

**¿Cuándo se abre esta ventana?**
- Siempre, después de todas las validaciones de duplicados
- Permite al usuario EDITAR manualmente el nombre

**¿Qué muestra la ventana?**
- **Campo Tipo:** Dropdown con [OFICIO, CIRCULAR, LISTA_ASISTENCIA, etc]
- **Campo Número:** TextBox con el número extraído (editable)
- **Campo Fecha:** TextBox con fecha + botón CALENDARIO
- **Campo Depto:** Dropdown o texto libre
- **Preview:** Muestra cómo quedará el nombre final
- **Checkbox "Marcar como ADJUNTO":** ← **CRÍTICO**

**Preview de nombre (actualiza en tiempo real):**
```
Tipo: OFICIO
Número: 045
Fecha: 2024-03-15
Depto: RRHH
Sufijo: (ninguno)

PREVIEW: OFI-045_RRHH_2024-03-15.pdf
```

---

### ETAPA 5: DECISIÓN ADJUNTO vs PRINCIPAL

**Ubicación:** `Cuerpo/main.py` líneas 1080-1150

**Esta es la parte MÁS IMPORTANTE para lo que pediste analizar.**

#### Si el archivo es PRINCIPAL (sin marcar como adjunto):
```python
else:
    # Crear como nuevo archivo independiente
    ruta_destino = self.carpeta_salida / nombre_nuevo
    
    # Manejar colisiones de nombres
    contador = 1
    while ruta_destino.exists():
        ruta_destino = parent / f"{base_stem}_{contador:02d}{base_ext}"
    
    self._copiar_archivo(pdf, ruta_destino)  # Copiar archivo
    guardar_metadata(ruta_destino, metadata, self.carpeta_salida)  # Guardar JSON
```

**Log de consola:**
```
✅ Guardado como: OFI-045_RRHH_2024-03-15.pdf
```

#### Si el archivo es ADJUNTO (checkbox marcado):
```python
if es_adjunto and principal_seleccionado:
    # FUSIONAR con el PDF principal seleccionado
    ruta_principal = principal_seleccionado
    
    exito_fusion = fusionar_pdf_anexo(ruta_principal, pdf, self.logger)
    
    if exito_fusion:
        # Actualizar metadata del documento principal
        metadata_principal = {
            'tiene_anexos': True,
            'annexo_procesado': pdf.name,
            'anexo_timestamp': datetime.now().isoformat(),
            ...
        }
        guardar_metadata(ruta_principal, metadata_principal, ...)
```

**Log de consola:**
```
📎 ANEXADO a: OFI-045_RRHH_2024-03-15.pdf
```

**¿Cómo se fusionan?**  
Ubicación: `Cuerpo/core/pdf_logic.py` - Función `fusionar_pdf_anexo()`

```python
def fusionar_pdf_anexo(ruta_principal: Path, ruta_anexo: Path, logger: logging.Logger) -> bool:
    """Fusiona ruta_anexo dentro de ruta_principal usando PyPDF2."""
    try:
        reader_principal = PdfReader(str(ruta_principal))
        reader_anexo = PdfReader(str(ruta_anexo))
        writer = PdfWriter()
        
        # Copiar todas las páginas del principal
        for pagina in reader_principal.pages:
            writer.add_page(pagina)
        
        # Agregar todas las páginas del anexo
        for pagina in reader_anexo.pages:
            writer.add_page(pagina)
        
        # Sobrescribir el principal con la versión fusionada
        with open(ruta_principal, 'wb') as f:
            writer.write(f)
        
        return True
    except Exception as e:
        logger.error(f"Error fusionando: {e}")
        return False
```

---

## 3. DEFINICIÓN DE TEXTOS Y MENSAJES

### A. Textos de Consola (ScrolledText)

**Archivo:** `Cuerpo/main.py` - Método `_log_consola()`

```python
def _log_consola(self, texto: str, tipo: str = "normal"):
    """
    Agrega texto a la consola con colores según tipo.
    
    Tipos:
    - "normal":  gris (procesamiento general)
    - "info":    blanco (información importante)
    - "warning": amarillo (advertencias)
    - "error":   rojo (errores)
    - "success": verde (confirmaciones)
    """
```

**Ejemplos de textos mostrados:**

| Texto | Cuándo | Tipo | Ubicación código |
|-------|--------|------|-----------------|
| `="="*70` | Inicio procesamiento | normal | L780 |
| `📍 Detectando cambios de tipo en N PDF(s)...` | Antes de segmentar | info | L790 |
| `📄 Analizando: archivo.pdf` | Analizar cada PDF | info | L795 |
| `✂️ Contiene varios documentos - Preparando segmentación...` | Si necesita segmentar | info | L810 |
| `❓ N punto(s) requieren verificación manual` | Si hay dudas | info | L825 |
| `✅ Se crearon N segmento(s)` | Post-segmentación | info | L860 |
| `📄 N archivos PDF encontrados` | Después de segmentar | info | L875 |
| `[1/50] Procesando: archivo.pdf` | Inicio de cada PDF | normal | L900 |
| `ℹ️ Tipo: OFICIO \| Nº: 045 \| ...` | Metadatos extraídos | normal | L920 |
| `🔍 DUPLICADO EXACTO detectado (hash idéntico)` | Hash coincide | warning | L950 |
| `⚠️ Número 'XXX' ya registrado → archivo_anterior.pdf` | Número duplicado | warning | L980 |
| `🔍 SIMILITUD ALTA detectada: 75%` | Fuzzy > 70% | warning | L1010 |
| `✏️ Renombrado como RESPUESTA` | Decision en modal | info | L1000 |
| `📎 ANEXADO a: archivo_principal.pdf` | ZIP con principal | info | L1130 |
| `✅ Guardado como: OFI-045_RRHH_2024-03-15.pdf` | Archivo guardado | success | L1120 |
| `🗑️ OMITIDO (duplicado)` | Descartado | warning | L960 |

### B. Títulos y Mensajes de Ventanas Modales

| Ventana | Título | Descripción | Ubicación |
|---------|--------|-------------|-----------|
| `VentanaConsultaSeparacion` | Título dinámico según modo | Pregunta si separar documentos | `modals.py` L450-500 |
| `VentanaVerificacion` | "Verificación de Duplicado" | Muestra 2 PDFs lado a lado con zoom | `modals.py` L600-700 |
| `VentanaNumDuplicado` | "Número Duplicado Detectado" | Explica que el nº ya existe, ofrece opciones | `modals.py` L800-900 |
| Edición nombre | "Editar Nombre del Documento" | Permitir editar tipo/nº/fecha/depto | `main.py` L1050-1080 |

---

## 4. SISTEMA DE VENTANAS MODALES

### 🪟 VentanaConsultaSeparacion
**Cuándo aparece:** Cuando se detecta un cambio de tipo entre páginas  
**Cómo funciona:**

```
┌─────────────────────────────────────────────┐
│  ¿Separar estas páginas del documento?     │
│                                             │
│  Página X: OFICIO 045                       │
│  Página Y: LISTA_ASISTENCIA                 │
│                                             │
│  [Ver PDF] [Zoom] [Decidir]               │
│                                             │
│  ○ Son el MISMO documento                  │
│  ○ Son DOCUMENTOS DIFERENTES               │
│  ○ ANEXAR al anterior                      │
│  ○ Crear NUEVA LISTA                       │
│                                             │
│  [ACEPTAR] [CANCELAR]                     │
└─────────────────────────────────────────────┘
```

**Código:**
```python
class VentanaConsultaSeparacion(ctk.CTkToplevel):
    def __init__(self, parent, pdf_ruta, tipo_doc, pag_anterior, pag_actual, modo_lista=False):
        # Carga miniaturas de ambas páginas
        # Ofrece botón ZOOM para ver a detalle
        # 4 opciones de decisión (radio buttons)
        pass
    
    def obtener_decision(self) -> Optional[str]:
        # return: 'mismo'|'diferente'|'anexar_anterior'|'nueva_lista'|None
        pass
```

**Ubicación:** `Cuerpo/ui/modals.py` líneas 450-550

---

### 🪟 VentanaVerificacion
**Cuándo aparece:** Cuando Hash coincide o Fuzzy > 70%  
**Cómo funciona:**

```
┌──────────────────────────────────────────────────┐
│  VERIFICACIÓN DE DUPLICADO                      │
│  Similitud detectada: 75.3%                      │
│                                                  │
│  ┌─────────────────┐   ┌─────────────────┐     │
│  │  ANTERIOR       │   │  NUEVO          │     │
│  │ [Miniatura PDF] │   │ [Miniatura PDF] │     │
│  │ [ZOOM]          │   │ [ZOOM]          │     │
│  │ Nombre: XXX     │   │ Nombre: YYY     │     │
│  │ Hash: ...       │   │ Hash: ...       │     │
│  └─────────────────┘   └─────────────────┘     │
│                                                  │
│  Primeros 200 chars texto:                      │
│  "OFICIO Nº 045/2024..."                        │
│                                                  │
│  [Son IGUALES] [Son DIFERENTES] [ES RESPUESTA] │
└──────────────────────────────────────────────────┘
```

**Zoom (ventana separada):**
```python
def _abrir_zoom_pdf():
    """Abre ventana con canvas zoomeable + pan interactivo."""
    # Canvas con imagen del PDF
    # Scroll con rueda = zoom in/out
    # Click + drag = pan (arrastrar)
    # Botón "Hoy" para volver a zoom normal
```

**Ubicación:** `Cuerpo/ui/modals.py` líneas 100-200

---

### 🪟 VentanaNumDuplicado
**Cuándo aparece:** Cuando el número del documento ya existe  
**Cómo funciona:**

```
┌────────────────────────────────────────────┐
│  NÚMERO DUPLICADO DETECTADO               │
│                                            │
│  El OFICIO Nº 045 ya fue procesado       │
│                                            │
│  Anterior: OFI-045_2024-03-10.pdf         │
│  Nuevo:    OFICIO_045_2024-03-15.pdf     │
│  Similitud: 45% (diferente contenido)     │
│                                            │
│  ¿Qué hacer con el archivo nuevo?         │
│                                            │
│  [Preview: OFI-045_RESPUESTA_2024-03-15] │
│                                            │
│  ○ Guardar como RESPUESTA (sufijo)       │
│  ○ Guardar como ANEXO (fusionar)         │
│  ○ DESCARTAR este archivo                │
│                                            │
│  [ACEPTAR] [CANCELAR]                    │
└────────────────────────────────────────────┘
```

---

### 🪟 Edición de Nombre (Custom Modal)

**Cuándo aparece:** Después de todas las validaciones  
**Cómo funciona:**

```
┌─────────────────────────────────────────────────────┐
│  EDITAR NOMBRE DEL DOCUMENTO                        │
│                                                      │
│  Tipo:         [OFICIO ▼]                           │
│  Número:       [045_____________]                   │
│  Fecha:        [2024-03-15] [📅 Calendario]        │
│  Depto:        [RRHH ▼]                             │
│  Sufijo:       ninguno                              │
│                                                      │
│  ☐ Marcar como ADJUNTO de:  [OFI-045_RRHH]        │
│                                                      │
│  PREVIEW: OFI-045_RRHH_2024-03-15.pdf              │
│                                                      │
│  [GUARDAR] [CANCELAR]                               │
└─────────────────────────────────────────────────────┘
```

**Campos editables:**
- **Tipo:** Dropdown con todos los tipos predefinidos
- **Número:** TextBox libre (puede dejar vacío)
- **Fecha:** TextBox con formato YYYY-MM-DD + botón calendario
- **Depto:** Dropdown o TextBox libre
- **Sufijo:** Mostrado solo si aplica (RESPUESTA, ANEXO, OR)
- **Checkbox Adjunto:** Si está marcado, muestra dropdown para seleccionar a qué principal anexar

**Calendario (Helper):**
```python
def _abrir_calendario(parent, var_fecha: StringVar, on_change=None):
    """Popup calendario interactivo con navegación mes/año."""
    # Canvas 7x7 con los días del mes
    # Botones: « ‹ Mes Año › »
    # Seleccionar día → actualizar var_fecha
    # Botón "Hoy" para ir al día actual
```

---

## 5. LÓGICA DE RENOMBRADO

### Generación del Nombre Nuevo

**Función:** `generar_nombre_limpio()` en `Cuerpo/core/pdf_logic.py` líneas 300-360

```python
def generar_nombre_limpio(tipo_doc, fecha, numero_doc, depto, sufijo, texto_contexto):
    """
    Genera nombre basado en:
    1. Sigla del tipo (OFICIO → OFI)
    2. Número del documento
    3. Departamento
    4. Fecha
    5. Sufijo (OR, RESPUESTA, ANEXO)
    
    Returns: "OFI-045_RRHH_2024-03-15.pdf"
    """
```

**Lógica:**

1. **Obtener sigla** del tipo de documento:
   ```python
   sigla = SIGLAS_DOCUMENTO.get(tipo_doc, tipo_doc[:3].upper())
   # OFICIO → OFI
   # CIRCULAR → CIR
   # LISTA_ASISTENCIA → LIS
   ```

2. **Base del nombre:**
   ```python
   if numero_doc:
       num_limpio = re.sub(r'[^\w\-]', '', numero_doc)
       base = f"{sigla}-{num_limpio}"  # OFI-045
   else:
       base = sigla  # LIS
   ```

3. **Agregar depto (opcional):**
   ```python
   if depto:
       depto_limpio = re.sub(r'[^\w]', '', depto).upper()[:12]
       partes.append(depto_limpio)  # RRHH
   ```

4. **Agregar fecha (opcional):**
   ```python
   if fecha:
       partes.append(fecha)  # 2024-03-15
   ```

5. **Agregar sufijo:**
   ```python
   if sufijo:
       partes.append(sufijo)  # OR, RESPUESTA, ANEXO
   ```

6. **Resultado final:**
   ```python
   return "_".join(partes) + ".pdf"
   # OFI-045_RRHH_2024-03-15.pdf
   # OFI-046_RRHH_2024-03-16_RESPUESTA.pdf
   # LIS_REUNION_2024-03-01.pdf
   ```

### Caso Especial: LISTA_ASISTENCIA

Si el tipo es LISTA_ASISTENCIA y no tiene departamento, intenta extraer el nombre del evento/actividad del texto:

```python
if tipo_doc == "LISTA_ASISTENCIA" and not depto:
    # Buscar línea como: "EVENTO: Reunión de Presupuestos"
    m_evento = re.search(r'\b(?:EVENTO|ACTIVIDAD)\b[\s:.-]*([A-Z0-9 ]{4,60})', texto_norm)
    if m_evento:
        depto = sugerido  # Usar nombre del evento como "departamento"
```

**Ejemplo:**
```
Tipo: LISTA_ASISTENCIA
Evento encontrado: "Reunión de Presupuestos"
Fecha: 2024-03-15

Nombre: LIS_REUNION DE PRESUPUESTOS_2024-03-15.pdf
```

### Manejo de Colisiones (Sufijos numéricos)

Si el nombre YA EXISTE en la carpeta de salida:

```python
ruta_destino = self.carpeta_salida / nombre_nuevo
contador = 1
while ruta_destino.exists():
    ruta_destino = parent / f"{base_stem}_{contador:02d}{base_ext}"
    contador += 1

# Si OFI-045_RRHH_2024-03-15.pdf existe
# → OFI-045_RRHH_2024-03-15_01.pdf
# → OFI-045_RRHH_2024-03-15_02.pdf
```

---

## 6. MANEJO DE ADJUNTOS VS PRINCIPALES

### Decisión en la UI

En la ventana de edición, hay un **CHECKBOX:**
```
☐ Marcar como ADJUNTO de: [Dropdown con PDFs principales de esta sesión]
```

Si está **DESMARCADO** (por defecto):
- El archivo se guarda como **DOCUMENTO PRINCIPAL** independiente

Si está **MARCADO:**
- El usuario debe elegir de la lista cuál es el PDF principal
- El archivo se **FUSIONA** dentro del PDF principal elegido

### Variables que controlan esto

```python
# En Cuerpo/main.py __init__:
self._es_adjunto_editado: bool = False
self._principal_editado: Optional[Path] = None

# Después de la ventana de edición:
es_adjunto = getattr(self, "_es_adjunto_editado", False)
principal_seleccionado = getattr(self, "_principal_editado", None)
```

### Flujo si es ADJUNTO

```
1. Usuario marca checkbox ☑ "Es adjunto"
2. Usuario selecciona de lista: "OFI-045_RRHH_2024-03-15.pdf"
3. Usuario hace clic GUARDAR

BACKEND:
  └─ Cargar ruta_principal = OFI-045_RRHH_2024-03-15.pdf
  └─ Llamar fusionar_pdf_anexo(ruta_principal, pdf_nuevo)
        └─ PdfReader(principal)
        └─ PdfReader(nuevo)
        └─ PdfWriter()
        └─ writer.add_page(página_principal) x N
        └─ writer.add_page(página_anexo) x M
        └─ writer.write(ruta_principal)  ← SOBRESCRIBE
  └─ Actualizar metadata del principal:
        'tiene_anexos': True,
        'anexo_procesado': nombre_nuevo,
        'anexo_timestamp': datetime.now()
  └─ Log: "📎 ANEXADO a: OFI-045_RRHH_2024-03-15.pdf"

RESULTADO:
  - PDF principal ahora tiene X+Y páginas
  - archivo_nuevo.pdf NO se guarda por separado
  - Metadata marca que tiene anexos
```

### Flujo si es PRINCIPAL

```
1. Usuario DEJA SIN MARCAR el checkbox (por defecto)
2. Usuario hace clic GUARDAR

BACKEND:
  └─ nombre_nuevo = generar_nombre_limpio(...)
  └─ ruta_destino = carpeta_salida / nombre_nuevo
  └─ self._copiar_archivo(pdf, ruta_destino)
  └─ guardar_metadata(ruta_destino, {...})
  └─ Agregar a self.historial_principales.append(ruta_destino)
  └─ Log: "✅ Guardado como: nombre_nuevo.pdf"

RESULTADO:
  - Nuevo archivo en carpeta_salida
  - JSON metadata en carpeta_salida/metadata/
  - Ahora está disponible como opción para futuras anexiones
```

### Historial de Principales (Sesión Actual)

```python
self.historial_principales = []  # Se llena durante procesamiento

for cada_pdf_principal_guardado:
    self.historial_principales.append(ruta_destino)

# En ventana de edición, los adjuntos pueden elegir de:
nombre_adjuntos_disponibles = {
    "OFI-045_RRHH_2024-03-15.pdf": ruta_completa,
    "OFI-046_RRHH_2024-03-16.pdf": ruta_completa,
    "CIR-012_ADMIN_2024-03-14.pdf": ruta_completa,
}
```

---

## 7. PUNTOS DE QUIEBRE Y DECISIONES

### Árbol de Decisión Completo

```
START
 │
 ├─ ¿Carpetas válidas? 
 │   NO → Error modal, volver a seleccionar
 │   SÍ ↓
 │
 ├─ SEGMENTACIÓN (Pre-procesamiento)
 │   Para cada PDF:
 │   ├─ ¿Múltiples tipos detectados?
 │   │   NO → Pasar al siguiente PDF
 │   │   SÍ ↓
 │   │   └─ Para cada punto cuestionable:
 │   │       [VentanaConsultaSeparacion] → Usuario decide
 │   │       ├─ SEPARAR → Crear nuevo segmento
 │   │       ├─ MANTENER → Dejar juntas páginas
 │   │       ├─ ANEXAR → Marcar para fusión posterior
 │   │       └─ NUEVA_LISTA → Tratarlas como doc nuevo
 │   │
 │   └─ Resultado: Lista expandida de PDFs (algunos segmentados)
 │
 ├─ PROCESAMIENTO INDIVIDUAL
 │   Para cada PDF en la lista:
 │   │
 │   ├─ EXTRACCIÓN DE DATOS
 │   │   ├─ OCR + Análisis metadatos
 │   │   ├─ Generar Hash MD5
 │   │   └─ Extraer: Tipo, Número, Fecha, Depto
 │   │
 │   ├─ ¿OCR sin resultado útil?
 │   │   SÍ ├─ ¿Hash duplicado exacto?
 │   │      │   SÍ → [Dialog] Preguntar si copiar
 │   │      │   NO → Copiar sin renombrar
 │   │      └─ Continuar siguiente PDF
 │   │   NO ↓
 │   │
 │   ├─ CAPA 1: ¿Hash idéntico a anterior?
 │   │   SÍ → [VentanaVerificacion] Usuario decide
 │   │       ├─ ELIMINAR nuevo → Omitir este PDF
 │   │       ├─ RENOMBRAR como RESPUESTA → Guardar con sufijo
 │   │       └─ MANTENER AMBOS → Continuar
 │   │   NO ↓
 │   │
 │   ├─ CAPA 2: ¿Número ya procesado?
 │   │   SÍ → [VentanaNumDuplicado] Usuario decide
 │   │       ├─ RESPUESTA → Guardar con sufijo OR
 │   │       ├─ ANEXO → Marcar para fusión después
 │   │       └─ DESCARTAR → Omitir
 │   │   NO ↓
 │   │
 │   ├─ CAPA 3: ¿Similitud Fuzzy > 70%?
 │   │   SÍ → [VentanaVerificacion] Usuario decide (igual que Capa 1)
 │   │   NO ↓
 │   │
 │   ├─ EDICIÓN INTERACTIVA
 │   │   [VentanaEdicionNombre]
 │   │   │
 │   │   ├─ Usuario puede cambiar: Tipo, Número, Fecha, Depto
 │   │   ├─ Usuario puede ver PREVIEW del nombre final
 │   │   ├─ ¿Marcar como ADJUNTO?
 │   │   │   SÍ → Seleccionar PDF principal del historial
 │   │   │   NO → Será documento principal
 │   │   └─ [GUARDAR] o [CANCELAR]
 │   │
 │   ├─ ¿Usuario hizo clic CANCELAR?
 │   │   SÍ → Saltar este PDF, continuar siguiente
 │   │   NO ↓
 │   │
 │   ├─ ¿Es ADJUNTO?
 │   │   SÍ ├─ Validar que ruta_principal existe
 │   │      ├─ fusionar_pdf_anexo(ruta_principal, pdf_nuevo)
 │   │      ├─ Actualizar metadata del principal
 │   │      └─ Log: "📎 ANEXADO"
 │   │   NO ├─ Copiar archivo a carpeta_salida
 │   │      ├─ Guardar JSON metadata
 │   │      ├─ Agregar a historial_principales
 │   │      └─ Log: "✅ GUARDADO"
 │   │
 │   └─ Continuar siguiente PDF
 │
 └─ RESUMEN FINAL
    Mostrar:
    - Total procesados
    - Total renombrados
    - Total duplicados omitidos
    - Total anexos fusionados
    - Log completo copiable
```

---

## 📋 RESUMEN RÁPIDO DE COMPONENTES

| Componente | Archivo | Responsabilidad |
|-----------|---------|-----------------|
| **PantallaProcesamiento** | main.py | UI principal, validaciones, flujo |
| **_procesar_pdfs()** | main.py | Lógica principal de procesamiento |
| **detectar_cambios_tipo_pdf()** | pdf_logic.py | Detectar si PDF necesita segmentación |
| **extraer_paginas_por_tipo()** | pdf_logic.py | Crear segmentos PDF nuevos |
| **detectar_tipo_documento()** | pdf_logic.py | Clasificar documento (OFICIO, CIRCULAR, etc) |
| **buscar_numero_documento()** | pdf_logic.py | Extraer número |
| **buscar_fecha()** | pdf_logic.py | Extraer fecha |
| **buscar_departamento()** | pdf_logic.py | Extraer departamento |
| **calcular_hash_md5()** | pdf_logic.py | Detectar duplicados exactos |
| **generar_nombre_limpio()** | pdf_logic.py | Crear nombre final |
| **fusionar_pdf_anexo()** | pdf_logic.py | Unir anexo al principal |
| **extraer_texto_ocr()** | ocr_engine.py | OCR de PDF |
| **_miniatura_pdf()** | ocr_engine.py | Generar miniaturas |
| **VentanaConsultaSeparacion** | modals.py | ¿Separar páginas? |
| **VentanaVerificacion** | modals.py | ¿Es duplicado? |
| **VentanaNumDuplicado** | modals.py | ¿Número ya existe? |
| **_abrir_zoom_pdf()** | modals.py | Visualizador interactivo |
| **_abrir_calendario()** | modals.py | Selector de fechas |

---

## ✅ CONCLUSIÓN

Ahora comprendes:
1. ✅ Cómo se **selecciona** el archivo
2. ✅ Cómo se **analiza** (OCR + metadatos)
3. ✅ Las **4 capas de verificación** y sus ventanas
4. ✅ Los **textos** y dónde está cada uno
5. ✅ La fórmula de **renombrado**
6. ✅ La diferencia entre **ADJUNTO vs PRINCIPAL**
7. ✅ El **árbol de decisiones** completo

**Ahora está listo para decirme: ¿Qué quieres implementar o mejorar?**
