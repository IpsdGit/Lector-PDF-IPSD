# 🎬 EJEMPLOS PRÁCTICOS DE FUNCIONAMIENTO

Escenarios reales de cómo el usuario ve y experimenta el sistema.

---

## ESCENARIO 1: Documento Simple (1 PDF, sin duplicados)

### Entrada
```
Carpeta_entrada/
  └─ OFICIO_045_2024.pdf (1 página)
```

### Proceso (Usuario ve)

```
1️⃣ Usuario hace clic en PROCESAR
   └─ Consola muestra:
   
   ======================================================================
   INICIO DE PROCESAMIENTO - LECTOR V3
   ======================================================================
   
   🔍 Detectando cambios de tipo en 1 PDF(s)...
   📄 Analizando: OFICIO_045_2024.pdf
   ⏭️  Tipo uniforme - Sin segmentación necesaria
   
   📄 1 archivos PDF encontrados
   
   [Progress: 100%, Barra avanzo en verde]
   
   [1/1] Procesando: OFICIO_045_2024.pdf
   🔤 OCR: Extrayendo texto...
   ℹ️  Tipo: OFICIO | Nº: 045 | Depto: ARQUITECTURA | Fecha: 2024-03-15
   
   [VentanaEdicionNombre se abre en segundo plano]
```

### Ventana Modal: Edición
```
╔════════════════════════════════════╗
║ EDITAR NOMBRE DEL DOCUMENTO        ║
╠════════════════════════════════════╣
║                                    ║
║  Tipo:         [OFICIO ▼]          ║
║  Número:       [045_____________]  ║
║  Fecha:        [2024-03-15] [📅]  ║
║  Depto:        [ARQUITECTURA ▼]    ║
║                                    ║
║  ☐ Marcar como ADJUNTO            ║
║                                    ║
║  PREVIEW: OFI-045_ARQUITECTURA_2024-03-15.pdf ║
║                                    ║
║  [GUARDAR]  [CANCELAR]             ║
╚════════════════════════════════════╝
```

El usuario:
- **Ve el preview automáticamente** mientras edita
- **TODO está OK**, no toca nada
- **Hace clic GUARDAR**

```
2️⃣ Usuario hace clic GUARDAR

   ✅ Guardado como: OFI-045_ARQUITECTURA_2024-03-15.pdf
   
   [Progress: 100%]
   
   ======================================================================
   RESUMEN FINAL
   ======================================================================
   
   Total procesados:        1
   Total renombrados:       1
   Total duplicados:        0
   Total anexados:          0
   
   ✅ Procesamiento finalizado exitosamente
```

### Salida
```
Carpeta_salida/
  ├─ OFI-045_ARQUITECTURA_2024-03-15.pdf  [1 página]
  └─ metadata/
      └─ OFI-045_ARQUITECTURA_2024-03-15.json
        {
          "tipo_documento": "OFICIO",
          "numero_documento": "045",
          "fecha_documento": "2024-03-15",
          "departamento": "ARQUITECTURA",
          "nombre_original": "OFICIO_045_2024.pdf",
          "hash_md5": "abc123def456...",
          "tiene_anexos": false,
          "timestamp": "2024-03-15T10:30:45.123456"
        }
```

---

## ESCENARIO 2: PDF con Múltiples Documentos (Segmentación)

### Entrada
```
Carpeta_entrada/
  └─ reporte_completo.pdf (5 páginas)
      ├─ Páginas 1-2: OFICIO 045
      ├─ Página 3: LISTA_ASISTENCIA 
      ├─ Páginas 4-5: OFICIO 046
```

### Proceso (Usuario ve)

```
1️⃣ Consola muestra:

   🔍 Detectando cambios de tipo en 1 PDF(s)...
   📄 Analizando: reporte_completo.pdf
   ✂️  Contiene varios documentos - Preparando segmentación...
   ❓ 2 punto(s) requieren verificación manual
   
   Mostrando ventana de decisión 1/2...
```

### Primera Ventana Modal: Separar pág 2→3?

```
╔═══════════════════════════════════════════════════════╗
║  ¿Separar OFICIO de LISTA_ASISTENCIA?               ║
╠═══════════════════════════════════════════════════════╣
║                                                       ║
║  Página 2: OFICIO 045                                ║
║  Página 3: LISTA_ASISTENCIA                          ║
║                                                       ║
║  [Ver Página 2] [ZOOM]                              ║
║  Muestra miniatura de pág 2                          ║
║                                                       ║
║  [Ver Página 3] [ZOOM]                              ║
║  Muestra miniatura de pág 3                          ║
║                                                       ║
║  ¿Son el mismo documento o diferentes?               ║
║  ○ Son el MISMO documento (MANTENER juntas)         ║
║  ◉ Son DOCUMENTOS DIFERENTES (SEPARAR)              ║
║  ○ ANEXAR página 3 al anterior                      ║
║                                                       ║
║  [ACEPTAR]  [CANCELAR]                              ║
╚═══════════════════════════════════════════════════════╝
```

Usuario selecciona: **"Son DOCUMENTOS DIFERENTES"**  
Luego hace clic ACEPTAR

```
   Consola muestra:
   → SEPARAR
   
   Mostrando ventana de decisión 2/2...
```

### Segunda Ventana Modal: Separar pág 3→4?

Usuario hace ZOOM en la página 3:

```
╔═══════════════════════════════════════════════════════════╗
║  [Barra de ZOOM]         [100%]  [↺ Resetear Zoom]     ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║  ┌─────────────────────────────────────────────────────┐ ║
║  │ [Canvas zoomeable]                                  │ ║
║  │ Muestra página 3 (LISTA_ASISTENCIA)                │ ║
║  │ ┌─────────────────────────────────────────┐        │ ║
║  │ │ LISTA DE ASISTENCIA                     │        │ ║
║  │ │ Reunión de Presupuestos 2024            │        │ ║
║  │ │                                         │        │ ║
║  │ │ Presentes:                              │        │ ║
║  │ │ 1. Juan García                          │ ← ZOOM ║
║  │ │ 2. María López                          │ IN →   ║
║  │ │ 3. Roberto Martínez                     │        │ ║
║  │ │ ...                                     │        │ ║
║  │ └─────────────────────────────────────────┘        │ ║
║  │                                                     │ ║
║  │ [Scroll wheel = zoom] [Click+drag = pan]           │ ║
║  └─────────────────────────────────────────────────────┘ ║
║                                                           ║
║  [CERRAR ZOOM]                                           ║
╚═══════════════════════════════════════════════════════════╝
```

Usuario cierra zoom, vuelve a la ventana anterior:

```
╔═══════════════════════════════════════════════════════╗
║  ¿Separar LISTA_ASISTENCIA de OFICIO 046?           ║
╠═══════════════════════════════════════════════════════╣
║                                                       ║
║  Página 3: LISTA_ASISTENCIA                          ║
║  Página 4: OFICIO 046                                ║
║                                                       ║
║  ○ Son el MISMO documento (MANTENER juntas)         ║
║  ◉ Son DOCUMENTOS DIFERENTES (SEPARAR)              ║
║  ○ ANEXAR página 4 al anterior                      ║
║                                                       ║
║  [ACEPTAR]  [CANCELAR]                              ║
╚═══════════════════════════════════════════════════════╝
```

Usuario selecciona: **"Son DOCUMENTOS DIFERENTES"** y hace ACEPTAR

```
   Consola muestra:
   → SEPARAR
   
   ✂️  Se crearon 3 segmento(s)
   
   📄 3 archivos PDF encontrados
```

Ahora en lugar de 1 PDF original, hay 3 segmentos:
- `reporte_completo_seg1.pdf` (Páginas 1-2: OFICIO 045)
- `reporte_completo_seg2.pdf` (Página 3: LISTA_ASISTENCIA)
- `reporte_completo_seg3.pdf` (Páginas 4-5: OFICIO 046)

```
2️⃣ Constructor procesando 3 PDFs

   [Progress: 33%]
   [1/3] Procesando: reporte_completo_seg1.pdf
   ℹ️  Tipo: OFICIO | Nº: 045 | Depto: ARQUITECTURA | Fecha: 2024-03-15
   [VentanaEdicionNombre se abre]
   ... Usuario edita ... [GUARDAR]
   ✅ Guardado como: OFI-045_ARQUITECTURA_2024-03-15.pdf
   
   [Progress: 66%]
   [2/3] Procesando: reporte_completo_seg2.pdf
   ℹ️  Tipo: LISTA_ASISTENCIA | Nº: — | Depto: — | Fecha: 2024-03-15
   [VentanaEdicionNombre se abre]
   ... Usuario edita tipo a "LISTA_ASISTENCIA", elige depto "REUNIÓN" ...
   ... [GUARDAR] ...
   ✅ Guardado como: LIS_REUNION_2024-03-15.pdf
   
   [Progress: 100%]
   [3/3] Procesando: reporte_completo_seg3.pdf
   ℹ️  Tipo: OFICIO | Nº: 046 | Depto: ARQUITECTURA | Fecha: 2024-03-15
   [VentanaEdicionNombre se abre]
   ... Usuario edita ... [GUARDAR] ...
   ✅ Guardado como: OFI-046_ARQUITECTURA_2024-03-15.pdf
```

### Salida
```
Carpeta_salida/
  ├─ OFI-045_ARQUITECTURA_2024-03-15.pdf
  ├─ LIS_REUNION_2024-03-15.pdf
  ├─ OFI-046_ARQUITECTURA_2024-03-15.pdf
  └─ metadata/
      ├─ OFI-045_ARQUITECTURA_2024-03-15.json
      ├─ LIS_REUNION_2024-03-15.json
      └─ OFI-046_ARQUITECTURA_2024-03-15.json
```

---

## ESCENARIO 3: Duplicados (Hash + Fuzzy + Número)

### Entrada
```
Carpeta_entrada/
  ├─ OFICIO_045_v1.pdf  ← Original (procesado primero)
  ├─ OFICIO_045_v2.pdf  ← Mismo archivo (cambiado de nombre)
  ├─ OFICIO_045_rev.pdf ← Similar (70%+ contenido)
  └─ OFICIO_046.pdf     ← Diferente número
```

### Proceso (Usuario ve)

```
[Progress: 25%]
[1/4] Procesando: OFICIO_045_v1.pdf
ℹ️  Tipo: OFICIO | Nº: 045 | ...
[VentanaEdicionNombre] Usuario edita, guarda
✅ Guardado como: OFI-045.pdf
```

```
[Progress: 50%]
[2/4] Procesando: OFICIO_045_v2.pdf
ℹ️  Tipo: OFICIO | Nº: 045 | ...

🔍 DUPLICADO EXACTO detectado (hash idéntico)
   Original: OFI-045.pdf
```

### Ventana Modal: ¿Es realmente duplicado?

```
╔═══════════════════════════════════════════════════════╗
║  VERIFICACIÓN DE DUPLICADO                          ║
║  Similitud detectada: 100% (HASH IDÉNTICO)           ║
╠═══════════════════════════════════════════════════════╣
║                                                       ║
║  ┌───────────────────┐  ┌───────────────────┐       ║
║  │ANTERIOR           │  │NUEVO              │       ║
║  │ [Miniatura PDF]   │  │ [Miniatura PDF]   │       ║
║  │ OFI-045.pdf       │  │ OFICIO_045_v2.pdf │       ║
║  │ [ZOOM]            │  │ [ZOOM]            │       ║
║  │ Hash: abc123...   │  │ Hash: abc123...   │       ║
║  │                   │  │ (IDÉNTICO)        │       ║
║  └───────────────────┘  └───────────────────┘       ║
║                                                       ║
║  Son exactamente el MISMO archivo                    ║
║                                                       ║
║  ¿Qué hacer?                                        ║
║  [Son IGUALES]    [Son DIFERENTES]    [ES RESPUESTA]║
║                                                       ║
╚═══════════════════════════════════════════════════════╝
```

Usuario hace clic: **"Son IGUALES"** (Descartar duplicado)

```
   Consola muestra:
   🗑️  ELIMINADO (duplicado confirmado)
```

```
[Progress: 75%]
[3/4] Procesando: OFICIO_045_rev.pdf
ℹ️  Tipo: OFICIO | Nº: 045 | ...

🔍 SIMILITUD ALTA detectada: 72.5%
   Similar a: OFI-045.pdf
```

### Ventana Modal: ¿Es similar?

```
╔═══════════════════════════════════════════════════════╗
║  VERIFICACIÓN DE DUPLICADO                          ║
║  Similitud detectada: 72.5% (CONTENIDO PARECIDO)     ║
╠═══════════════════════════════════════════════════════╣
║                                                       ║
║  ┌───────────────────┐  ┌───────────────────┐       ║
║  │ANTERIOR           │  │NUEVO              │       ║
║  │ [Miniatura PDF]   │  │ [Miniatura PDF]   │       ║
║  │ OFI-045.pdf       │  │ OFICIO_045_rev.pdf        ║
║  │ [ZOOM]            │  │ [ZOOM]            │       ║
║  │                   │  │                   │       ║
║  └───────────────────┘  └───────────────────┘       ║
║                                                       ║
║  Primeros 300 caracteres:                           ║
║  "OFICIO Nº 045/2024, San Salvador, 15 de marzo...  ║
║                                                       ║
║  ¿Son el mismo documento?                            ║
║  [Son IGUALES]    [Son DIFERENTES]    [ES RESPUESTA]║
║                                                       ║
╚═══════════════════════════════════════════════════════╝
```

Usuario hace clic: **"Son DIFERENTES"** (Mantener ambos)

```
   Consola muestra:
   ✅ Manteniendo ambos (confirmado diferente)
   
   [VentanaEdicionNombre se abre]
   Usuario ve preview: OFI-045_..._RESPUESTA.pdf 
   (El sistema automáticamente le agregó sufijo?)
   ¿O usuario edita manualmente?
```

Depende de la lógica. Aquí asumimos que el usuario lo edita:

```
   Usuario edita:
   - Cambia número a: 045-REV
   - O cambia nombre completamente
   
   [GUARDAR]
   ✅ Guardado como: OFI-045-REV_ARQUITECTURA_2024-03-15.pdf
```

```
[Progress: 100%]
[4/4] Procesando: OFICIO_046.pdf
ℹ️  Tipo: OFICIO | Nº: 046 | ...

⚠️  Número '046' nuevo
[VentanaEdicionNombre]
[GUARDAR]
✅ Guardado como: OFI-046_ARQUITECTURA_2024-03-15.pdf
```

### Salida
```
Carpeta_salida/
  ├─ OFI-045_ARQUITECTURA_2024-03-15.pdf        ✅ Original
  ├─ OFI-045-REV_ARQUITECTURA_2024-03-15.pdf   ✅ Similar (70%)
  └─ OFI-046_ARQUITECTURA_2024-03-15.pdf       ✅ Diferente
```

---

## ESCENARIO 4: ADJUNTOS Y FUSIÓN (Lo MÁS IMPORTANTE)

### Entrada
```
Carpeta_entrada/
  ├─ OFICIO_045.pdf (2 páginas) ← Documento Principal
  └─ ANEXO_045.pdf  (3 páginas) ← Anexo del mismo oficio
```

### Proceso (Usuario ve)

```
[1/2] Procesando: OFICIO_045.pdf
...
[VentanaEdicionNombre]
User guarda
✅ Guardado como: OFI-045_RRHH_2024-03-15.pdf
[Agregado a historial_principales]
```

```
[2/2] Procesando: ANEXO_045.pdf
ℹ️  Tipo: DOCUMENTO | Nº: — | ...

[VentanaEdicionNombre se abre]
```

### Ventana Modal: Editar ANEXO_045

```
╔════════════════════════════════════════════════════╗
║ EDITAR NOMBRE DEL DOCUMENTO                        ║
╠════════════════════════════════════════════════════╣
║                                                    ║
║  Tipo:         [DOCUMENTO ▼]                       ║
║  Número:       [_________________]                 ║
║  Fecha:        [2024-03-15] [📅]                  ║
║  Depto:        [RRHH ▼]                            ║
║                                                    ║
║  ☑ Marcar como ADJUNTO de:                        ║
║     [OFI-045_RRHH_2024-03-15.pdf ▼]              ║
║                                                    ║
║  PREVIEW: DOCUMENTO_RRHH_2024-03-15.pdf          ║
║                                                    ║
║  [GUARDAR]  [CANCELAR]                            ║
╚════════════════════════════════════════════════════╝
```

Usuario:
1. **Marca el checkbox** ☑ "Marcar como ADJUNTO"
2. El dropdown se **activa automáticamente** mostrando:
   ```
   - OFI-045_RRHH_2024-03-15.pdf  ← PDF guardado anteriormente
   ```
3. Usuario **selecciona** ese PDF
4. **Preview se actualiza** (aunque no cambia nombre, solo se marca)
5. Hace clic **GUARDAR**

### Backend: Fusión de PDFs

```
   [Validación] ¿OFI-045_RRHH_2024-03-15.pdf existe?
   SÍ → Continuar
   
   ✓ Fusionando ANEXO_045.pdf → OFI-045_RRHH_2024-03-15.pdf
```

Internamente:

```python
# fusionar_pdf_anexo()
reader_principal = PdfReader("OFI-045_RRHH_2024-03-15.pdf")  # 2 páginas
reader_anexo = PdfReader("ANEXO_045.pdf")                    # 3 páginas
writer = PdfWriter()

# Agregar páginas del principal
for page in reader_principal.pages:  # 2 iteraciones
    writer.add_page(page)

# Agregar páginas del anexo
for page in reader_anexo.pages:      # 3 iteraciones
    writer.add_page(page)

# Sobrescribir
writer.write("OFI-045_RRHH_2024-03-15.pdf")
# Ahora: 5 páginas en total!
```

Consola:

```
📎 ANEXADO a: OFI-045_RRHH_2024-03-15.pdf

✅ Procesamiento finalizado exitosamente

======================================================================
RESUMEN FINAL
======================================================================

Total procesados:        2
Total renombrados:       1
Total duplicados:        0
Total anexados:          1
```

### Salida

```
Carpeta_salida/
  ├─ OFI-045_RRHH_2024-03-15.pdf  [5 páginas: 2 originales + 3 anexo]
  └─ metadata/
      └─ OFI-045_RRHH_2024-03-15.json
        {
          "tipo_documento": "OFICIO",
          "numero_documento": "045",
          "fecha_documento": "2024-03-15",
          "departamento": "RRHH",
          "tiene_anexos": true,              ← IMPORTANTE
          "anexo_procesado": "ANEXO_045.pdf",
          "anexo_timestamp": "2024-03-15T10:35:12.456789",
          ...
        }
```

**¡NÓTALO!**
- PDF original no existe más como archivo separado
- Fue **fusionado dentro** del principal
- Metadata del principal **marca que tiene anexos**
- La información del anexo está **registrada para auditoría**

---

## ESCENARIO 5: Múltiples Adjuntos (Caso Avanzado)

### Entrada
```
OFICIO_045.pdf (2 páginas)
├─ ANEXO_A_045.pdf (1 página)
├─ ANEXO_B_045.pdf (2 páginas)  
└─ DOCUMENTO_RESPUESTA_045.pdf (3 páginas)
```

### Flujo

```
1️⃣ OFICIO_045.pdf
   → ✅ Guardado como: OFI-045_RRHH_2024-03-15.pdf (2 pág)
   → Agregado a historial

2️⃣ ANEXO_A_045.pdf
   → Usuario marca: ☑ Adjunto de OFI-045_RRHH_...
   → ✓ Se fusiona → OFI-045 ahora tiene 3 pág
   → 📎 ANEXADO

3️⃣ ANEXO_B_045.pdf
   → Usuario marca: ☑ Adjunto de OFI-045_RRHH_...
   → ✓ Se fusiona → OFI-045 ahora tiene 5 pág
   → 📎 ANEXADO

4️⃣ DOCUMENTO_RESPUESTA_045.pdf
   → Usuario marca: ☑ Adjunto de OFI-045_RRHH_...
   → ✓ Se fusiona → OFI-045 ahora tiene 8 pág!!!!
   → 📎 ANEXADO
```

### Salida Final

```
Carpeta_salida/
  └─ OFI-045_RRHH_2024-03-15.pdf [8 páginas TOTALES]
     └─ Pages 1-2:   Original OFICIO
     └─ Páginas 3:   ANEXO_A
     └─ Pages 4-5:   ANEXO_B
     └─ Páginas 6-8: RESPUESTA
```

Metadata:

```json
{
  "tiene_anexos": true,
  "anexos_procesados": [
    {
      "nombre": "ANEXO_A_045.pdf",
      "timestamp": "2024-03-15T10:35:00"
    },
    {
      "nombre": "ANEXO_B_045.pdf",
      "timestamp": "2024-03-15T10:35:15"
    },
    {
      "nombre": "DOCUMENTO_RESPUESTA_045.pdf",
      "timestamp": "2024-03-15T10:35:30"
    }
  ]
}
```

---

## 📊 TABLA DE DECISIONES RÁPIDA

Cuando el usuario **VE** una ventana, ¿qué puede **HACER**?

### VentanaConsultaSeparacion
| Botón | Resultado | Significa |
|-------|-----------|----------|
| MISMO | Mantener páginas juntas | Las considero 1 solo documento |
| DIFERENTES | Crear nueva segmentación | Son docs separados, cortaré aquí |
| ANEXAR | Fusionar ahora | Página siguiente es anexo de esta |
| NUEVA_LISTA | Es lista nueva | En caso LISTA_ASISTENCIA |

### VentanaVerificacion (Duplicados)
| Botón | Resultado | Significa |
|-------|-----------|----------|
| Son IGUALES | Descartar nuevo | Borra el archivo duplicado |
| Son DIFERENTES | Guardar ambos | No son el mismo, mantén los dos |
| ES RESPUESTA | Guardar con sufijo | Agregue "_RESPUESTA" al nuevo |

### VentanaNumDuplicado
| Botón | Resultado | Significa |
|-------|-----------|----------|
| RESPUESTA | Guardar como "_RESPUESTA" | Número existe, pero es respuesta |
| ANEXO | Marcar para fusión | Será anexo del principal |
| DESCARTAR | Omitir archivo | No guardarlo |

### VentanaEdicionNombre
| Acción | Resultado | Significa |
|--------|-----------|----------|
| Editar campos + GUARDAR | Usa nombre editado | Usuario customizó metadatos |
| Marcar ☑ ADJUNTO | Seleccionar principal | Será fusionado con ese PDF |
| Click CANCELAR | Saltar PDF | No procesar este archivo ahora |

---

## 💡 TIPS DE USO PARA EL USUARIO

1. **Checkbox de ADJUNTO está DESMARCADO por defecto**
   - Si no lo marcas → PDF se guarda por separado
   - Si lo marcas → PDF se fusiona con otro

2. **El historial de principales se llena durante procesamiento**
   - Solo puedes anexar a PDFs que ya fueron guardados como PRINCIPALES en esta sesión
   - El siguiente PDF que guardes será disponible para anexar PDFs posteriores

3. **VentanaVerificacion puede aparecer en 2 momentos**
   - CAPA 1: Hash exacto (100% idéntico)
   - CAPA 3: Fuzzy (70%+ similitud)
   - En ambos casos: tienes opción de guardar como RESPUESTA

4. **Preview actualiza en TIEMPO REAL**
   - Mientras editas campos → Preview se recalcula automáticamente
   - Ver el nombre final antes de guardar → Evita sorpresas

5. **El ZOOM es muy útil**
   - Úsalo cuando no estés seguro si dos documentos son iguales o no
   - Scroll rueda = zoom in/out
   - Click+drag = mover página (pan)

---

Ahora sí, **¿qué quieres implementar o mejorar?** 🚀
