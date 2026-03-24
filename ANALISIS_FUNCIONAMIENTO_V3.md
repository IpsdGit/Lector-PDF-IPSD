# Análisis Funcional y Arquitectónico - Lector PDF IPSD V3

He revisado a profundidad la lógica interna de los archivos `main.py`, `core/pdf_logic.py`, `core/ocr_engine.py` y `ui/modals.py`. A continuación, se detalla cómo opera el sistema actualmente y se proponen mejoras técnicas para futuras iteraciones.

## 1. Funcionamiento Actual (Capa por Capa)

### A. Extracción y Segmentación
1. **OCR Selectivo:** Se utiliza `pdf2image` y `pytesseract` para extraer el texto (`dpi=280` para precisión). Se analizan las primeras 3 páginas de entrada.
2. **Detección Inteligente:** Si un PDF tiene múltiples páginas, se analiza cada una. Si la heurística detecta un cambio en el "Tipo de Documento" (ej. de OFICIO a CIRCULAR) o un cambio en el "Número" dentro del mismo tipo, marca posibles puntos de ruptura.
3. **Intervención Humana Dinámica:** Cuando la heurística no está segura (ej. una Lista de Asistencia seguida de un documento genérico), lanza una ventana modal (`VentanaConsultaSeparacion`) suspendiendo el hilo de procesamiento hasta que el usuario decida si *separar* o *anexar* las páginas.

### B. Sistema Estricto de Verificación (4 Capas)
1. **Integridad Binaria (Hash MD5):** Evita el procesamiento doble del mismo archivo exacto.
2. **Colisión de Números:** Si ya se indexó un "OFICIO 045", y llega otro distinto pero con el mismo número, alerta al usuario (`VentanaNumDuplicado`) asumiendo que el nuevo es un "ANEXO" o "RESPUESTA".
3. **Similitud Semántica (Fuzzy):** Usa `fuzz.ratio` para comparar los primeros 1000 caracteres del documento actual contra *todos* los procesados previamente. Si la similitud supera el 70%, lanza `VentanaVerificacion` permitiendo discriminar falsos positivos de copias con diferente resolución limitando la basura virtual.
4. **Verificación Visual:** La UI precarga miniaturas de caché (generadas con `poppler`) permitiendo al humano validar sin salir de la app usando herramientas de Zoom (`_abrir_zoom_pdf`).

### C. Concurrencia y UI Seguro
El procesamiento pesado se lanza en un `threading.Thread`. Tkinter/CustomTkinter no es thread-safe, pero la implementación actual utiliza el patrón de comunicación por colas (`Queue`) para los logs, y usa `self.after(0, _mostrar)` junto con `threading.Event().wait()` para invocar modales desde el hilo secundario hacia el hilo principal sin "congelar" la app ni causar fallos de segmentación. Es una implementación **sobresaliente**.

---

## 2. Puntos Fuertes Detectados
- **Manejo de estados:** La variables como `es_original` y los diccionarios de seguimiento `archivos_procesados` y `numeros_vistos` aseguran que la integridad referencial se mantenga en la sesión.
- **Auditoría (Metadata):** La generación de los JSON vinculados a los archivos resultantes facilita la búsqueda cruzada posterior en bases de datos (ElasticSearch, MongoDB).
- **Manejo de Colisiones en SO:** El ciclo `while ruta_destino.exists():` con sufijos numéricos (`_01`, `_02`) es a prueba de balas para no sobrescribir datos.

---

## 3. Oportunidades de Mejora (Roadmap Sugerido)

### Mejora 1: Extracción de Texto Híbrida (Gran Impacto en Rendimiento)
Actualmente *todos* los documentos pasan por OCR (Tesseract). Esto es lento computacionalmente. 
**Propuesta:** Intentar extraer la capa de texto nativa del PDF primero usando una librería como `PyMuPDF` (`fitz`) o `PyPDF2`.
- Si `len(texto_nativo) > 50` y tiene coherencia, se usa ese texto (Procesamiento ~0.1s por PDF).
- Si el documento es un escaneo plano (imágenes), el texto nativo será `""`, y solo entonces se activa el OCR como plan de contingencia (Procesamiento ~3s por PDF).

### Mejora 2: Optimización del Motor Fuzzy (Escalabilidad)
El bloque que compara la similitud de texto itera sobre `archivos_procesados.items()`. Si en una sesión procesas 2,000 archivos, el archivo 2001 realizará 2,000 comparaciones de `fuzz.ratio`.
**Propuesta:** Implementar una pre-condición rápida. Por ejemplo, solo usar `fuzz.ratio` si la longitud del texto (`len(texto)`) de ambos documentos tiene un margen de diferencia menor a ±15%. Esto corta el 90% de evaluaciones innecesarias.

### Mejora 3: Soft-Coding de Variables de Entorno
En `core/pdf_logic.py`, listas como `NOISE` y reglas semánticas están "quemadas" (hardcoded) en el código.
**Propuesta:** Migrar esas listas a un archivo `reglas_semanticas.json` o dentro del mismo `config.py` para que los administradores del IPSD puedan agregar nuevas abreviaturas (ej. nuevas facultades) sin que un programador deba editar el código fuente.

### Mejora 4: Robustez en la Segmentación PDF
`PyPDF2.PdfWriter` funciona excelente el 95% de las veces, pero puede perder anotaciones o romper firmas digitales al recomponer páginas.
**Propuesta:** En futuras versiones, evaluar `PyMuPDF` (`import fitz`) para las divisiones/segmentaciones, ya que preserva mucho mejor la integridad de las estructuras complejas del estándar PDF.
