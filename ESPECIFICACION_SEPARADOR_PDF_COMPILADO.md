# 📋 ESPECIFICACIÓN: Separador Inteligente de PDFs Compilados

**Versión:** 1.0  
**Fecha:** 12 de Marzo 2026  
**Estado:** Análisis y Clarificación Completada  
**Responsable:** Lector V3 Team - IPSD UNAH  

---

## 🎯 OBJETIVO GENERAL

Extender la funcionalidad del **Lector de PDFs V3** para que no solo renombre archivos PDF individuales, sino que también pueda:

1. **Detectar PDFs compilados** con múltiples tipos de documentos internos
2. **Segmentar automáticamente** basándose en tipos de documentos normalizados
3. **Agrupar inteligentemente** documentos principales con sus anexos
4. **Generar múltiples PDFs** bien organizados a partir de un archivo compilado

---

## 📊 ESTADO ACTUAL vs NUEVO

### ✅ Funcionalidad Actual (Sin cambios)

```
📄 PDF Individual
   ↓
🔍 OCR + Detectar tipo/número/fecha
   ↓
📝 Renombrar
   ↓
✅ OFICIO_156_2024-03-05.pdf
```

**Características:**
- Lee PDFs individuales
- Detecta type, número y fecha
- Renombra según estándares
- Manean 4 capas de verificación (hash, fuzzy, semántica, manual)

---

### 🆕 Funcionalidad Nueva (A Agregar)

```
📄 PDF COMPILADO (múltiples documentos)
   ↓
🔍 Analizar PÁGINA POR PÁGINA
   ├─ OCR en cada página
   ├─ Detectar tipo (normalizado/no normalizado)
   ├─ Extraer: número, fecha, contenido
   └─ Clasificar como: PRINCIPAL o ANEXO
   ↓
✂️ SEGMENTAR según TIPOS NORMALIZADOS
   ├─ Identificar límites (cambio de tipo normalizado)
   ├─ Agrupar anexos con documento principal
   └─ Crear segmentos consolidados
   ↓
📄 EXTRAER Y CONSOLIDAR
   ├─ Extraer páginas de cada segmento
   ├─ Unir principales + anexos en 1 PDF
   └─ Generar nombre único
   ↓
✅ MÚLTIPLES PDFs RENOMBRADOS
```

---

## 🔑 CONCEPTO CLAVE: Tipos Normalizados vs No Normalizados

### TIPOS NORMALIZADOS (Pueden iniciar RUPTURA/SEGMENTACIÓN)

```
✅ CIRCULAR
✅ OFICIO
✅ LISTA DE ASISTENCIA        ← Forma estándar, estructura definida
✅ MEMORANDO
✅ INFORME
✅ RESOLUCIÓN
✅ ACTA
✅ Otros tipos institucionales necesarios
```

**Características:**
- Siguen estructura/formato estándar de la institución
- Están definidos en normativas
- Pueden ser documentos principales
- Si tipo cambia → RUPTURA DE SEGMENTO

### TIPOS NO NORMALIZADOS (Son ANEXOS, NO causan ruptura)

```
❌ LISTADO                     ← Tabla genérica sin código
❌ PROGRAMA DE ACTIVIDAD      ← Documento complementario
❌ DOCUMENTO (sin clasificar)  ← OCR no identificó tipo
❌ TABLA GENÉRICA
❌ FORMULARIO NO ESTÁNDAR
❌ Otros no definidos en normas
```

**Características:**
- NO siguen estructura estándar
- NO están formalmente definidos
- Son COMPLEMENTARIOS a documentos principales
- Se agrupan con documento principal anterior
- NO causan ruptura de segmento

---

## 📋 LÓGICA DE SEGMENTACIÓN

### Regla Principal:

```
RUPTURA ocurre CUANDO:
  • Página anterior: Tipo NORMALIZADO (Ej: OFICIO)
  • Página siguiente: Tipo NORMALIZADO DIFERENTE (Ej: CIRCULAR)

NO hay ruptura (es ANEXO) CUANDO:
  • Página siguiente: Tipo NO NORMALIZADO
  • Se agrupa con documento normalizado anterior
```

### Ejemplo Práctico:

```
ENTRADA: COMPILADO.pdf (15 páginas)

Página 1-2:   OFICIO_001                    [NORMALIZADO]
Página 3:     LISTADO (tabla asistentes)    [NO NORMALIZADO] → ANEXO
              └─ Unido a OFICIO_001

Página 4-5:   CIRCULAR_023                  [NORMALIZADO]
              └─ RUPTURA aquí, nuevo segmento

Página 6:     LISTA DE ASISTENCIA_001       [NORMALIZADO]
              └─ RUPTURA aquí, es tipo diferente

Página 7-9:   OFICIO_002                    [NORMALIZADO]
              └─ RUPTURA aquí

Página 10:    PROGRAMA DE ACTIVIDAD         [NO NORMALIZADO] → ANEXO
              └─ Unido a OFICIO_002

Página 11:    LISTADO (tabla genérica)      [NO NORMALIZADO] → ANEXO
              └─ Sigue unido a OFICIO_002


RESULTADO - 4 SEGMENTOS:
  ✅ SEGMENTO 1: OFICIO_001 + LISTADO (páginas 1-3)
     └─ Guardar como: OFICIO_001_2024-MM-DD.pdf (3 páginas)

  ✅ SEGMENTO 2: CIRCULAR_023 (páginas 4-5)
     └─ Guardar como: CIRCULAR_023_2024-MM-DD.pdf (2 páginas)

  ✅ SEGMENTO 3: LISTA_ASISTENCIA_001 (página 6)
     └─ Guardar como: LISTA_ASISTENCIA_001_2024-MM-DD.pdf (1 página)

  ✅ SEGMENTO 4: OFICIO_002 + PROGRAMA + LISTADO (páginas 7-11)
     └─ Guardar como: OFICIO_002_2024-MM-DD.pdf (5 páginas)
```

---

## 🔧 ARQUITECTURA TÉCNICA PROPUESTA

### Fase 1: Análisis (Página por Página)

**Función:** `analizar_pdf_compilado_paginas(ruta_pdf: Path)`

```python
Para CADA página del PDF:
  1. Convertir página → imagen (pdf2image)
  2. Ejecutar OCR (pytesseract)
  3. Detectar tipo documento:
     • Buscar en TIPOS_NORMALIZADOS
     • Si no encuentra → clasificar como NO NORMALIZADO
  4. Extraer información:
     • Número de documento
     • Fecha
     • Contenido texto
     • Confianza de detección
  5. Detectar indicadores visuales:
     • Presencia de firma/sello
     • Densidad de página
     • Patrones de encabezado
  
  Retorna: Lista de metadatos por página
  [{
    'pagina': 1,
    'tipo': 'OFICIO',
    'es_normalizado': True,
    'numero': '156',
    'fecha': '2024-03-05',
    'confianza': 0.94,
    'tiene_firma': False,
    'texto': '...',
    'hash': 'abc123...'
  }, ...]
```

### Fase 2: Segmentación (Detectar Límites)

**Función:** `detectar_segmentos_pdf(metadatos_paginas: List[Dict])`

```python
Algoritmo:
  1. Iterar por cada página
  2. Comparar tipo_normalizado actual vs anterior
  3. Si cambio de tipo normalizado → RUPTURA
  4. Si tipo NO normalizado → ANEXO (agregar a segmento anterior)
  5. Consolidar rangos de páginas por segmento
  
  Retorna: Lista de segmentos
  [{
    'numero_segmento': 1,
    'tipo_principal': 'OFICIO',
    'pagina_inicio': 1,
    'pagina_fin': 3,
    'numero_doc': '001',
    'fecha_doc': '2024-03-05',
    'anexos': [
      {'tipo': 'LISTADO', 'paginas': [3]}
    ],
    'confianza_segmentacion': 0.92,
    'nombre_salida': 'OFICIO_001_2024-03-05'
  }, ...]
```

### Fase 3: Extracción y Consolidación

**Función:** `extraer_segmentos_pdf(ruta_pdf: Path, segmentos: List[Dict])`

```python
Para CADA segmento:
  1. Extraer páginas del rango usando PyPDF2
  2. Consolidar en un solo PDF (documento + anexos unidos)
  3. Generar nombre según:
     • "{TIPO}_{NUMERO?}_{FECHA}.pdf"
     • Si no hay número: "{TIPO}_SIN_NUMERO_{FECHA}.pdf"
  4. Guardar en carpeta de salida
  5. Generar metadata
  
  Retorna: Lista de archivos generados
  [
    {
      'ruta_generada': Path('...OFICIO_001_2024-03-05.pdf'),
      'paginas': [1, 2, 3],
      'tipo_principal': 'OFICIO',
      'anexos_incluidos': ['LISTADO'],
      'tamaño': '2.3 MB'
    }, ...
  ]
```

---

## 📐 FLUJO DE PROCESAMIENTO COMPLETO

```
┌─ USUARIO SELECCIONA PDF ─────────────┐
│                                      │
├─ ¿PDF individual o compilado? ──────┤
│                                      │
├─→ Si INDIVIDUAL                     │
│   └─ Procesar con V3 actual         │
│      (Renombrar, sin separación)    │
│                                      │
├─→ Si COMPILADO (NUEVO)              │
│   ├─ Fase 1: Analizar página x pág │
│   ├─ Fase 2: Detectar segmentos    │
│   ├─ Fase 3: Mostrar vista previa  │
│   ├─ Fase 4: Confirmación usuario  │
│   └─ Fase 5: Extraer y guardar     │
│                                      │
└─→ Resultado ────────────────────────┘
   ├─ PDF(s) segmentados
   ├─ Metadata consolidada
   └─ Logs detallados
```

---

## 🎨 INTERFAZ DE USUARIO PROPUESTA

### Pantalla Principal - Selección de Modo

```
┌────────────────────────────────────────────────┐
│ LECTOR DE PDFs V3.0 - IPSD UNAH              │
├────────────────────────────────────────────────┤
│                                                │
│ 📄 Seleccionar archivo PDF:                   │
│    [Buscar...]                                │
│                                                │
│ MODO DE PROCESAMIENTO:                        │
│  ◉ PDF Individual (Renombrar solo)            │
│  ○ PDF Compilado (Segmentar + Renombrar)     │
│                                                │
│ Carpeta de salida: [...]                      │
│                                                │
│        [Procesar]  [Cancelar]                 │
└────────────────────────────────────────────────┘
```

### Pantalla Secundaria - Vista Previa de Segmentación

```
┌─────────────────────────────────────────────────────┐
│ VISTA PREVIA - SEGMENTACIÓN DETECTADA             │
├─────────────────────────────────────────────────────┤
│                                                     │
│ ✅ SEGMENTO 1 (Confianza: 94%)                     │
│    └─ OFICIO_001 (páginas 1-3)                     │
│       • Documento principal: OFICIO Nº 001         │
│       • Anexos: LISTADO (pág 3)                    │
│       • Resultado: OFICIO_001_2024-03-05.pdf       │
│                                                     │
│ ✅ SEGMENTO 2 (Confianza: 91%)                     │
│    └─ CIRCULAR_023 (páginas 4-5)                   │
│       • Documento principal: CIRCULAR Nº 023       │
│       • Sin anexos                                  │
│       • Resultado: CIRCULAR_023_2024-03-10.pdf     │
│                                                     │
│ ⚠️  SEGMENTO 3 (Confianza: 72%)                    │
│    └─ OFICIO_002 (páginas 6-11)                    │
│       • Documento principal: OFICIO Nº 002         │
│       • Anexos: PROGRAMA (pág 10), LISTADO (pág11) │
│       • [🔄 REVISAR]  [✏️ EDITAR]                 │
│                                                     │
│ 📊 Resumen:                                        │
│    • Páginas totales analizadas: 11               │
│    • Segmentos identificados: 3                   │
│    • Confianza promedio: 86%                      │
│                                                     │
│         [✓ Continuar]  [✏️ Ajustar]  [✗ Cancelar]│
└─────────────────────────────────────────────────────┘
```

---

## ⚙️ CONFIGURACIÓN INSTITUCIONAL

### Archivo de Configuración: `config_tipos_normativos.json`

```json
{
  "institucion": "IPSD UNAH",
  "fecha_actualizacion": "2026-03-12",
  "tipos_normalizados": {
    "CIRCULAR": {
      "palabras_clave": ["circular", "circ.", "ref:", "nº circ"],
      "es_principal": true,
      "puede_tener_anexos": true,
      "prioridad": 1
    },
    "OFICIO": {
      "palabras_clave": ["oficio", "of.", "ref:", "asunto:"],
      "es_principal": true,
      "puede_tener_anexos": true,
      "prioridad": 1
    },
    "LISTA_DE_ASISTENCIA": {
      "palabras_clave": ["lista de asistencia", "asistencia", "evento"],
      "es_principal": true,
      "puede_tener_anexos": false,
      "prioridad": 2
    },
    "MEMORANDO": {
      "palabras_clave": ["memorando", "mem", "memo"],
      "es_principal": true,
      "puede_tener_anexos": true,
      "prioridad": 1
    },
    "INFORME": {
      "palabras_clave": ["informe", "inf.", "reporte"],
      "es_principal": true,
      "puede_tener_anexos": true,
      "prioridad": 2
    },
    "RESOLUCIÓN": {
      "palabras_clave": ["resolución", "resol.", "resolutivo"],
      "es_principal": true,
      "puede_tener_anexos": false,
      "prioridad": 1
    },
    "ACTA": {
      "palabras_clave": ["acta", "acta de", "levantamiento de acta"],
      "es_principal": true,
      "puede_tener_anexos": true,
      "prioridad": 2
    }
  },
  "tipos_no_normalizados": [
    "LISTADO",
    "PROGRAMA",
    "FORMULARIO",
    "TABLA_GENERICA",
    "DOCUMENTO"
  ],
  "configuracion_segmentacion": {
    "min_confianza_ruptura": 0.85,
    "min_confianza_anexo": 0.70,
    "detectar_firmas": true,
    "detectar_sellos": true
  }
}
```

---

## 🔍 CASOS DE USO ESPECÍFICOS

### Caso 1: PDF Compilado Administrativo

```
Entrada: COMPILADO_MARZO_2024.pdf (15 páginas)

Contenido:
  • OFICIO_001 para convocatoria (págs 1-2)
  • LISTADO de asistentes (pág 3)
  • CIRCULAR 023 para reorganización (págs 4-5)
  • PROGRAMA de capacitación (págs 6-8)
  • OFICIO_002 respuesta (págs 9-10)
  • LISTA ASISTENCIA oficial (págs 11-12)
  • LISTA ASISTENCIA oficial (págs 13-15)

Salida:
  ✅ OFICIO_001_2024-03-01.pdf (3 páginas: oficio + listado)
  ✅ CIRCULAR_023_2024-03-05.pdf (5 páginas: circular + programa)
  ✅ OFICIO_002_2024-03-10.pdf (2 páginas: oficio)
  ✅ LISTA_ASISTENCIA_001_2024-03-12.pdf (3 páginas)
  ✅ LISTA_ASISTENCIA_002_2024-03-15.pdf (3 páginas)
```

### Caso 2: PDF Simple (Sin Cambios)

```
Entrada: OFICIO_INDIVIDUAL.pdf (2 páginas)

Contenido:
  • Documento único tipo OFICIO

Procesamiento:
  ✓ Detecta: PDF no compilado (1 tipo normalizado = 1 segmento)
  ✓ No segmenta
  ✓ Procesa como antes: Renombra y guarda

Salida:
  ✅ OFICIO_XXX_2024-MM-DD.pdf (2 páginas, sin cambios)
```

---

## 📝 PREGUNTAS PENDIENTES A RESOLVER

- [ ] ¿Tienes lista completa de tipos normalizados?
- [ ] ¿Qué pasa con réplicas selladas (mismo documento, diferentes sellos)?
  - ¿Mantener todas?
  - ¿Descartar duplicados?
  - ¿Guardar como "RESPUESTAS"?
- [ ] ¿Los anexos SIEMPRE están inmediatamente después?
- [ ] ¿Hay otros patrones específicos de tu institución a considerar?
- [ ] ¿Nivel de automatización deseado?
  - Totalmente automático
  - Semiautomático (usuario confirma propuesta)
  - Manual (usuario define segmentos)

---

## 🚀 PRÓXIMAS FASES

### ✅ Fase 1 (Completada): Análisis y Especificación
- Entender caso de uso
- Identificar patrones
- Diseñar arquitectura

### ⏳ Fase 2 (Pendiente): Implementación Core
- Crear función de análisis página por página
- Implementar lógica de segmentación
- Crear extractor de rangos de páginas

### ⏳ Fase 3 (Pendiente): Interfaz y UX
- Interfaz de selección de modo
- Vista previa de segmentación
- Dialogo de confirmación

### ⏳ Fase 4 (Pendiente): Testing y Refinamiento
- Probar con PDFs reales
- Calibrar confianzas
- Manejar casos edge

---

## 📚 REFERENCIAS Y RECURSOS

**Dependencias necesarias:**
- `PyPDF2` - Manipulación de PDFs
- `pdf2image` - Conversión página → imagen (ya existe)
- `pytesseract` - OCR (ya existe)
- `fuzzywuzzy` - Similitud textual (ya existe)

**Técnicas a implementar:**
- Análisis secuencial página por página
- Detección de patrones textuales
- Segmentación inteligente con ventanas deslizantes
- Consolidación de rangos de páginas

---

**Documento preparado para: Referencia futura y desarrollo iterativo**
