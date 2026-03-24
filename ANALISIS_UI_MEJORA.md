# 🎨 Análisis UI: Convertidor PDF → Renombrador de PDFs V3

**Análisis Comparativo y Propuesta de Mejora Gráfica**  
Fecha: 9 de Marzo de 2026

---

## 📊 Comparando Interfaces

### **Convertidor PDF (Referencia)**

```
PANTALLA INICIAL:
- Glassmorphism con fondo difuminado
- Cards con redondeados y hover effects
- Colores institucionales (UNAH)
- Logo y diseño profesional

PANTALLA PROCESAMIENTO:
├─ Header: Azul oscuro + Logo + Badge dinámico
├─ Sección configuración: Cards blancos redondeados
├─ Step indicators: Círculos numerados (1→2→3)
├─ Progress bar: Barra animada con porcentaje
├─ Consola logs: Fondo negro (#10121a) con colores
├─ Botones: Azul + Amarillo con hover animados
├─ Toasts: Notificaciones flotantes con animación
└─ Footer: Info institucional

LIBRERÍAS USADAS:
- customtkinter (ctk): Componentes modernos
- PIL/Pillow: Procesamiento de imágenes
- threading: Procesamiento no bloqueante
```

### **Renombrador PDF V1/V2 (Actual)**

```
PANTALLA ÚNICA:
- Tkinter puro (sin estilos modernos)
- Colores básicos (grises, azules)
- Scrolledtext simple para logs
- Barra progreso estándar
- UI de una sola pantalla

PROBLEMAS:
- Sin glassmorphism
- Sin animaciones
- Logs poco legibles
- Buttons sin hover effects
- Pocos indicadores visuales
- UI poco profesional
```

---

## 🎯 Propuesta: Adaptar Estilo Convertidor al Renombrador V3

### **FASE 1: Preparación (Pantalla Selección)**

Mantener estructura actual pero mejorar visualmente:

```
ACTUAL (mantener, mejorar estilo):
┌─────────────────────────────────────┐
│ Renombrador de PDFs (portable)      │
├─────────────────────────────────────┤
│                                     │
│ Delay antes de iniciar (seg): [5]  │
│ Año para Oficios/Circulares: [202  │
│                                     │
│ [Seleccionar carpeta e iniciar]    │
│ [Cancelar]                          │
├─────────────────────────────────────┤
│ [Barra logs]                        │
└─────────────────────────────────────┘

MEJORADO (estilo Convertidor):
┌─────────────────────────────────────┐
│ ═════════════════════════════════   │ ← Header azul  
│ LOGO │ Renombrador PDFs │ Badge   │
├─────────────────────────────────────┤
│                                     │
│  Configuración de Procesamiento     │
│                                     │
│  ┌── Card 1 ──────────────────┐    │
│  │ Delay: [5 seg]            │    │
│  │ (Explicación)             │    │
│  └───────────────────────────┘    │
│                                     │
│  ┌── Card 2 ──────────────────┐    │
│  │ Año: [2026]               │    │
│  │ (Explicación)             │    │
│  └───────────────────────────┘    │
│                                     │
│  [Seleccionar Carpeta e Iniciar]   │
│  (Botón azul grande, hover)        │
│                                     │
└─ Footer (Info IPSD) ───────────────┘
```

---

### **FASE 2: Pantalla de Procesamiento (NUEVA - Separada)**

Cuando usuario inicia proceso → mostrar pantalla COMPLETAMENTE NUEVA:

```
┌─────────────────────────────────────────────────────────────┐
│ HEADER (Azul #003671)                                       │
│ Logo │ Renombrador de PDFs │ Badge "PROCESANDO"            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Step Indicators:                                           │
│    ① Preparación  ──►  ② Verificación  ──►  ③ Completado  │
│                                                              │
│  ┌─────────────────────────────────┐                        │
│  │ Carpeta: /ruta/a/documentos    │                        │
│  │ Total PDFs: 47                 │                        │
│  │ Procesados: 23/47 (49%)        │                        │
│  └─────────────────────────────────┘                        │
│                                                              │
│  ┌────────────────────────────────┐                        │
│  │ ████████████░░░░░░░░░░░░░░░   │ 49% ► PROCESANDO      │
│  └────────────────────────────────┘                        │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ >_ IPSD Renombrator Console         [⚙ Opciones]   │  │
│  ├─────────────────────────────────────────────────────┤  │
│  │ [14:32:10] ▶ Iniciando procesamiento...             │  │
│  │ [14:32:11] ✓ oficio_1.pdf → OFC123_2026.pdf       │  │
│  │ [14:32:12] ✓ documento_2.pdf → FCH_15-marzo-2026.  │  │
│  │ [14:32:13] ⚠ circular_3.pdf → Requiere verificación│  │
│  │ [14:32:14] ✗ Error: PDF corrupto en oficio_4.pdf   │  │
│  │                                                      │  │
│  │ (auto-scroll)                                        │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────██───────────────┐ │
│  │ Esperando verificación: OFC123_2026 (1).pdf          │ │
│  │                                    CENTRADO ALERTA    │ │
│  │ Similitud: 87% · Opción: [ Mantener? ] [ Ver Info ] │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                              │
│  [⏸ Pausar] [⏹ Cancelar] [✓ Generar Reporte]             │
│                                                              │
└─ FOOTER (Info IPSD) ──────────────────────────────────────┘
```

---

## 🔧 Cambios Técnicos Necesarios

### **1. Instalar CustomTkinter**

```bash
pip install customtkinter
```

**Impacto:** Una sola librería nueva (ya viene con Material Design colors)

### **2. Estructura de Archivos UI**

```
renombrador_pdfs_v3.py
├─ Imports (+ customtkinter)
├─ Colores constantes (como Convertidor)
│  ├─ COLOR_AZUL = "#003671"
│  ├─ COLOR_VERDE = "#93BE27"
│  └─ etc.
├─ Clase: PantallaSeleccion (mejora UI actual)
├─ Clase: PantallaProcesamiento (NUEVA - estilo Convertidor)
├─ Clase: VentanaVerificacionDuplicado (NUEVA - modal)
└─ App (switch entre pantallas)
```

### **3. Components del Convertidor a Usar**

| Componente | Convertidor | Renombrador | Descripción |
|-----------|---|---|---|
| **Header** | Azul + Logo + Badge | ✅ ADAPTAR | Barra superior profesional |
| **Step Indicators** | Círculos 1→2→3 | ✅ USAR | Mostrar: Preparación → Verificación → Completado |
| **Progress Bar** | Animada + % | ✅ USAR | Barra de progreso con porcentaje dinámico |
| **Consola Logs** | Fondo negro + Tags | ✅ USAR | Logs con colores (✓ éxito, ⚠ warning, ✗ error) |
| **Cards** | Redondeados blancos | ✅ ADAPTAR | Para mostrar info (carpeta, conteo, etc) |
| **Botones** | CTkButton animados | ✅ USAR | Azul/Verde con hover effects |
| **Toasts** | Notificaciones flotantes | ✅ USAR | Para alertas rápidas |
| **Drag & Drop** | TkinterDnD | ✓ OPCIONAL | Si quieres que arrastra carpeta |

---

## 📐 Layout Pantalla Procesamiento

```
GRID LAYOUT:
Row 0: ┌────────────────────────────────────┐
       │ HEADER (80px, altura fija)         │
       └────────────────────────────────────┘

Row 1: ┌────────────────────────────────────┐
       │ Step Indicators (40px)             │
       └────────────────────────────────────┘

Row 2: ┌──────────┬──────────────────────┐
       │ Card 1   │ Card 2              │
       │ Carpeta  │ Estadísticas        │
       │ (25%)    │ (75%)               │
       └──────────┴──────────────────────┘

Row 3: ┌────────────────────────────────────┐
       │ Progress Bar + % (20px)            │
       └────────────────────────────────────┘

Row 4: ┌────────────────────────────────────┐
       │ CONSOLA LOGS (peso=1, expandible)  │
       │                                    │
       │ (ocupa 60-70% del espacio)        │
       └────────────────────────────────────┘

Row 5: ┌────────────────────────────────────┐
       │ Alert/Verificación (si necesario) │
       │ ⚠️  Posible duplicado 87%          │
       │ [Mantener] [Eliminar] [Ver Info]  │
       └────────────────────────────────────┘

Row 6: ┌────────────────────────────────────┐
       │ Botones de acción (50px)          │
       │ [⏸ Pausar] [⏹ Cancelar] [✓ Info] │
       └────────────────────────────────────┘

Row 7: ┌────────────────────────────────────┐
       │ FOOTER (70px, altura fija)        │
       └────────────────────────────────────┘
```

---

## 🎨 Elementos Visuales Nuevos

### **1. Header Profesional**

```python
import customtkinter as ctk
from PIL import Image

COLOR_AZUL = "#003671"

header = ctk.CTkFrame(root, fg_color=COLOR_AZUL, height=80)
header.pack(fill="x", side="top")

# Logo (izquierda)
logo_img = Image.open("assets/logo.png")
logo_ctk = ctk.CTkImage(light_image=logo_img, size=(70, 70))
ctk.CTkLabel(header, image=logo_ctk, text="", fg_color=COLOR_AZUL).pack(side="left", padx=20)

# Título (centro)
tk.Label(header, text="Renombrador de PDFs V3", 
        font=("Segoe UI", 14, "bold"), 
        bg=COLOR_AZUL, fg="white").pack(side="left")

# Badge (derecha)
badge = ctk.CTkFrame(header, fg_color="#FF6B6B", corner_radius=15)
badge.pack(side="right", padx=20)
ctk.CTkLabel(badge, text="  ⏳ PROCESANDO  ", 
            text_color="white", font=("Segoe UI", 9, "bold"),
            fg_color="#FF6B6B").pack(padx=10, pady=5)
```

### **2. Step Indicators Mejorados**

```python
def crear_indicador_paso(parent, numero, label, estado="pending"):
    """
    estado: "pending" (gris), "active" (azul), "completed" (verde)
    """
    frame = tk.Frame(parent, bg="white")
    
    # Círculo con número
    canvas = tk.Canvas(frame, width=30, height=30, 
                      bg="white", highlightthickness=0)
    canvas.pack()
    
    if estado == "completed":
        canvas.create_oval(2, 2, 28, 28, fill="#93BE27", outline="#93BE27")
        canvas.create_text(15, 15, text="✓", font=("Arial", 14, "bold"), fill="white")
    elif estado == "active":
        canvas.create_oval(2, 2, 28, 28, fill="white", outline="#003671", width=2)
        canvas.create_text(15, 15, text=numero, font=("Arial", 10, "bold"), fill="#003671")
    else:  # pending
        canvas.create_oval(2, 2, 28, 28, fill="#F5F5F5", outline="#CCCCCC")
        canvas.create_text(15, 15, text=numero, font=("Arial", 10), fill="#999999")
    
    # Etiqueta
    tk.Label(frame, text=label, font=("Segoe UI", 8),
            bg="white", fg="#003671" if estado == "active" else "#999999").pack()
    
    return frame
```

### **3. Consola Profesional de Logs**

```python
# Consola estilo Convertidor PDF
console_frame = ctk.CTkFrame(root, fg_color="#10121a", 
                             corner_radius=10, border_width=1, 
                             border_color="#E0E0E0")

# Header de consola
header = tk.Frame(console_frame, bg="#1C1F2E", height=22)
header.pack(fill="x")
tk.Label(header, text=">_  IPSD Renombrator Console", 
        font=("Consolas", 7), bg="#1C1F2E", 
        fg="#7AADCA", padx=8).pack(side="left", fill="y")

# Separador
tk.Frame(console_frame, bg="#2A2D3E", height=1).pack(fill="x")

# Texto con scroll
log = scrolledtext.ScrolledText(
    console_frame, height=10, 
    bg="#10121a", fg="white",
    font=("Consolas", 8),
    relief="flat", bd=0, padx=10, pady=10,
    wrap="word"
)
log.pack(fill="both", expand=True)

# Tags de colores
log.tag_config("success", foreground="#93BE27")    # Verde
log.tag_config("warning", foreground="#FFC107")    # Amarillo
log.tag_config("error",   foreground="#FF5555")    # Rojo
log.tag_config("info",    foreground="#FFFFFF")    # Blanco
log.tag_config("time",    foreground="#8888AA")    # Gris azulado

# USO:
log.insert("end", "[14:32:10] ", "time")
log.insert("end", "✓ Proceso iniciado\n", "success")
```

---

## 🎬 Animaciones Necesarias

### **1. Progress Bar Animada**

```python
def animar_progreso(target, paso=0.04, delay=18):
    """Anima barra de progreso suavemente"""
    actual = progress_bar.get()
    if abs(actual - target) < 0.005:
        progress_bar.set(target)
        return
    
    if target > actual:
        progress_bar.set(actual + paso)
    else:
        progress_bar.set(actual - paso)
    
    progress_label.config(text=f"{int(progress_bar.get() * 100)}%")
    root.after(delay, lambda: animar_progreso(target, paso, delay))
```

### **2. Toasts Notificaciones**

```python
def mostrar_toast(mensaje, tipo="info", duracion=5000):
    """
    Toast similar a Convertidor PDF
    tipo: "info", "success", "warning", "error"
    """
    # (Implementación similar a Convertidor)
    # - Ventana Toplevel flotante
    # - Animación de entrada desde derecha
    # - Auto-cierre después de duracion
    # - Colores según tipo
```

---

## 📋 Comparativa: Pantalla antes/después

### **ANTES (V1/V2 - Actual)**

```
┌─────────────────────────────────────────────┐
│ Renombrador de PDFs (portable)              │
├─────────────────────────────────────────────┤
│ Delay: [5]     Año: [2026]                  │
│ [Seleccionar carpeta] [Cancelar]           │
├─────────────────────────────────────────────┤
│ ████████░░░░░░░ 45/100                      │
│ Estado: Procesando... (45/100)              │
├─────────────────────────────────────────────┤
│ LOG (texto simple):                         │
│ 14:23:45 - Procesando: doc1.pdf             │
│ 14:23:47 - Renombrado: OFC123_2026          │
│ 14:23:50 - Duplicado eliminado              │
└─────────────────────────────────────────────┘
```

### **DESPUÉS (V3 - Propuesto)**

```
┌─────────────────────────────────────────────┐
│ HEADER AZUL | Logo | Renombrador | Badge  │
├─────────────────────────────────────────────┤
│                                              │
│  ① Preparación  ──►  ② Verificación ──► ③  │
│                                              │
│  ┌─ Carpeta: /ruta ──────────┐              │
│  │ PDFs: 47 | Procesados: 23 │              │
│  └────────────────────────────┘              │
│                                              │
│  ████████████░░░░░░░░░░░░░░░░ 49%          │
│  Procesando... (23/47)                      │
│                                              │
│  ┌─ >_ IPSD Renombrator Console ────────┐  │
│  ├──────────────────────────────────────┤  │
│  │ [14:32:10] ✓ oficio_1.pdf → OFC...  │  │
│  │ [14:32:11] ✓ documento_2.pdf → FCH  │  │
│  │ [14:32:12] ⚠ circular_3 - Verificar │  │
│  │ [14:32:13] ✗ Error: oficio_4 corrupto
│  │                                     │  │
│  └──────────────────────────────────────┘  │
│                                              │
│  ⚠️  OFC123_2026(1) - Similitud 87%        │
│  Detectado posible duplicado                │
│  [✓ Ver Info] [Mantener] [Eliminar]        │
│                                              │
│  [⏸ Pausar] [⏹ Cancelar] [✓ Reporte]     │
│                                              │
└─ FOOTER (Info) ────────────────────────────┘
```

---

## ✅ Implementación por Fases

### **Fase 1: UI Base (Semana 1)**
- ✅ Instalar CustomTkinter
- ✅ Crear clase PantallaProcesamiento
- ✅ Header + Footer
- ✅ Step indicators básicos
- ✅ Progress bar animada
- ✅ Consola logs con colores

### **Fase 2: Interactividad (Semana 2)**
- ✅ Cards informativos
- ✅ Botones con hover
- ✅ Toast notifications
- ✅ Alert de verificación

### **Fase 3: Pulido (Semana 3)**
- ✅ Animaciones suaves
- ✅ Transiciones entre pantallas
- ✅ Gestos hover avanzados
- ✅ Responsive design

---

## 🔑 Conclusión

### **Ventajas de Cambiar al Estilo Convertidor**

| Aspecto | Beneficio |
|--------|-----------|
| **Profesionalismo** | UI moderna y pulida |
| **Usabilidad** | Indicadores visuales claros |
| **Feedback** | Logs detallados y legibles |
| **Consistencia** | Mismo estilo que otras herramientas IPSD |
| **Mantenibilidad** | Código organizado en clases |
| **Escalabilidad** | Fácil agregar más features |

### **Dependencias Nuevas**

- ✅ **customtkinter**: UI moderna (1 sola librería)
- ✅ Todas las otras (threading, json, queue, etc) son built-in

### **No Requiere Cambios en:**

- Lógica de procesamiento (OCR, fuzzy matching, etc)
- Sistema de detección de documentos
- Capas 1-4 de verificación
- Metadata JSON
- Threading actual

---

**RECOMENDACIÓN: Implementar cambios UI en paralelo con lógica V3**

La UI de Convertidor PDF es perfectamente adaptable y elevará significativamente la percepción profesional de la herramienta.

---

Documento preparado: 9 de Marzo de 2026  
Versión: 1.0 - Análisis Completo
