"""
=============================================================================
LÓGICA DE PROCESAMIENTO PDF - Funciones de bajo nivel
=============================================================================

Módulo que contiene todas las funciones para:
- Cálculo de hashes MD5
- Detección de tipo de documento
- Búsqueda de metadatos (número, departamento, fecha)
- Segmentación inteligente de PDFs
- Gestión de metadata JSON
"""

import re
import json
import hashlib
import logging
import unicodedata
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime

from PyPDF2 import PdfReader, PdfWriter

from config import TIPOS_PREDEFINIDOS, SIGLAS_DOCUMENTO
from core.ocr_engine import extraer_texto_ocr_pagina

# =============================================================================
# FUNCIONES HELPER - HASH Y METADATA
# =============================================================================

def calcular_hash_md5(ruta_archivo: Path) -> str:
    """
    Calcula el hash MD5 de un archivo para detectar duplicados exactos.
    
    Args:
        ruta_archivo: Ruta del archivo PDF
        
    Returns:
        Hash MD5 como string hexadecimal
    """
    hash_md5 = hashlib.md5()
    try:
        with open(ruta_archivo, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        logging.error(f"Error calculando hash de {ruta_archivo.name}: {e}")
        return ""


def guardar_metadata(ruta_pdf: Path, metadata: Dict, carpeta_salida: Path) -> bool:
    """
    Guarda metadata de un archivo PDF en formato JSON en carpeta separada.
    
    Args:
        ruta_pdf: Ruta del archivo PDF
        metadata: Diccionario con metadata a guardar
        carpeta_salida: Carpeta de salida base donde crear subcarpeta metadata
        
    Returns:
        True si se guardó exitosamente, False en caso contrario
    """
    try:
        # Crear carpeta metadata si no existe
        metadata_dir = carpeta_salida / "metadata"
        metadata_dir.mkdir(exist_ok=True)
        
        # Guardar con mismo nombre que PDF pero con extensión .json
        metadata_file = metadata_dir / f"{ruta_pdf.stem}.json"
        metadata['timestamp'] = datetime.now().isoformat()
        metadata['version'] = '3.0'
        metadata['pdf_filename'] = ruta_pdf.name
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, indent=2, ensure_ascii=False, fp=f)
        
        return True
    except Exception as e:
        logging.error(f"Error guardando metadata de {ruta_pdf.name}: {e}")
        return False


def cargar_metadata(ruta_pdf: Path, carpeta_salida: Path) -> Optional[Dict]:
    """
    Carga metadata de un archivo PDF desde la carpeta metadata.
    
    Args:
        ruta_pdf: Ruta del archivo PDF
        carpeta_salida: Carpeta de salida base donde buscar subcarpeta metadata
        
    Returns:
        Diccionario con metadata o None si no existe
    """
    try:
        metadata_dir = carpeta_salida / "metadata"
        metadata_file = metadata_dir / f"{ruta_pdf.stem}.json"
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    except Exception as e:
        logging.error(f"Error cargando metadata de {ruta_pdf.name}: {e}")
        return None


def fusionar_pdf_anexo(pdf_principal: Path, pdf_anexo: Path, logger: logging.Logger) -> bool:
    """
    Fusiona un PDF anexo al final de un PDF principal usando PyPDF2.
    El PDF principal se sobrescribe con el contenido fusionado.
    
    Args:
        pdf_principal: Ruta del PDF principal (será modificado)
        pdf_anexo: Ruta del PDF anexo (será anexado)
        logger: Logger para registrar operaciones
        
    Returns:
        True si la fusión fue exitosa, False en caso contrario
    """
    try:
        # Leer el PDF principal
        reader_principal = PdfReader(str(pdf_principal))
        writer = PdfWriter()
        
        # Copiar todas las páginas del principal
        for page_num in range(len(reader_principal.pages)):
            page = reader_principal.pages[page_num]
            writer.add_page(page)
        
        # Leer el PDF anexo
        reader_anexo = PdfReader(str(pdf_anexo))
        
        # Agregar todas las páginas del anexo al final
        for page_num in range(len(reader_anexo.pages)):
            page = reader_anexo.pages[page_num]
            writer.add_page(page)
        
        # Escribir el resultado al archivo principal
        with open(pdf_principal, 'wb') as f:
            writer.write(f)
        
        logger.info(f"✅ Fusión exitosa: {len(reader_anexo.pages)} páginas anexadas a {pdf_principal.name}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error fusionando PDF {pdf_anexo.name} al principal: {e}")
        return False


# =============================================================================
# FUNCIONES HELPER - DETECCIÓN Y EXTRACCIÓN
# =============================================================================

def detectar_tipo_documento(texto: str) -> str:
    """
    Detecta el tipo de documento basándose en palabras clave.
    IMPORTANTE: Solo clasificará como tipo predefinido (OFICIO, CIRCULAR, etc.)
    si la palabra clave está acompañada de un número identificador.
    Sin número → se clasifica como DOCUMENTO genérico.
    
    EXCEPCIÓN: LISTA_ASISTENCIA no requiere número (se identifica directamente).
    
    NOTA: DIPLOMA y CONSTANCIA se excluyen (se manejan en aplicación aparte).
    Se tratarán como DOCUMENTO genérico.
    
    Args:
        texto: Texto extraído del PDF
        
    Returns:
        Tipo de documento detectado (OFICIO, CIRCULAR, MEMORANDUM, etc.) o DOCUMENTO
    """
    # Limitar búsqueda a las primeras 15 líneas (el tipo siempre está en el encabezado)
    primeras_lineas = texto.split('\n')[:15]
    texto_upper = ' '.join(primeras_lineas).upper()

    # Normalizar tildes para búsqueda robusta
    texto_norm = ''.join(
        c for c in unicodedata.normalize('NFD', texto_upper)
        if unicodedata.category(c) != 'Mn'
    )

    # Regla especial: LISTA/LISTAS/LISTADO acompañado de ASISTENCIA
    # en cualquier orden (antes o después), case/acento-insensitive.
    patron_lista_asistencia = re.compile(
        r'\b(?:'
        r'(?:LISTA|LISTAS|LISTADO)(?:\W+\w+){0,3}\W+ASISTENCIA'
        r'|ASISTENCIA(?:\W+\w+){0,3}\W+(?:LISTA|LISTAS|LISTADO)'
        r')\b',
        re.IGNORECASE
    )
    if patron_lista_asistencia.search(texto_norm):
        return "LISTA_ASISTENCIA"
    
    # Palabras clave priorizadas (orden importa)
    # NOTA: DIPLOMA, CONSTANCIA, CERTIFICACION excluidas deliberadamente
    tipos = [
        ("OFICIO", ["OFICIO", "OF."]),
        ("CIRCULAR", ["CIRCULAR", "CIRC."]),
        ("TIKET", ["TIKET", "TICKET", "TIC."]),
        ("DICTAMEN", ["DICTAMEN", "OPINIÓN TÉCNICA", "OPINION TECNICA"]),
        ("RECIBO", ["RECIBO", "RBO."]),
        ("MEMORANDUM", ["MEMORÁNDUM", "MEMORANDUM", "MEMO"]),
        ("ACUERDO_COMPROMISO", ["ACUERDO DE COMPROMISO", "ACUERDOS DE COMPROMISO"]),
        ("ACUERDO_INTERNACIONAL", ["ACUERDO INTERNACIONAL", "ACUERDOS INTERNACIONALES"]),
        ("RESOLUCION", ["RESOLUCIÓN", "RESOLUCION", "ACUERDO"]),
        ("ACTA", ["ACTA", "ACTA DE"]),
        ("INFORME", ["INFORME", "REPORTE"]),
        ("SOLICITUD", ["SOLICITUD", "PETICIÓN", "PETICION"]),
        ("CONTRATO", ["CONTRATO", "CONVENIO"]),
    ]
    
    # Primero: detectar si hay un número en el documento (indicador de tipo oficial)
    numero_encontrado = bool(re.search(r'N[O°º]?\.?\s*\d+|\d{2,6}(?:[/-]\d{2,4})?', texto_upper))
    
    for tipo, palabras_clave in tipos:
        if any(palabra in texto_upper for palabra in palabras_clave):
            # Los tipos predefinidos de este bloque requieren número
            if numero_encontrado:
                return tipo
            else:
                # Tiene palabra clave pero sin número → es documento genérico
                return "DOCUMENTO"
    
    return "DOCUMENTO"  # Genérico por defecto


def buscar_numero_documento(texto: str, tipo_doc: str) -> Optional[str]:
    """
    Extrae el número identificador del documento (ej: 045, 2026-001).
    
    Args:
        texto: Texto extraído del PDF
        tipo_doc: Tipo ya detectado (OFICIO, CIRCULAR, etc.)
        
    Returns:
        Número como string o None si no se encuentra
    """
    texto_upper = texto.upper()
    
    # Patrones según tipo de documento
    # Busca formas como: OFICIO No. 045, OFICIO N°045, OFICIO-2026-001, OFICIO 045/2026
    patrones = [
        # Explicit "N" indicator: No., N°, Nº, N.
        r'(?:OFICIO|CIRCULAR|MEMORANDUM|MEMO|RESOLUCI[OÓ]N|ACTA|INFORME|SOLICITUD|DICTAMEN)'
        r'[^\d]{0,20}N[O°º]?\.?\s*(\d{2,6}(?:[/-]\d{2,4})?)',
        # Direct number after keyword with no indicator
        r'(?:OFICIO|CIRCULAR|MEMORANDUM|MEMO|RESOLUCI[OÓ]N|ACTA|INFORME|SOLICITUD|DICTAMEN)'
        r'[\s\-_]{1,5}(\d{2,6}(?:[/-]\d{2,4})?)',
    ]
    for patron in patrones:
        match = re.search(patron, texto_upper)
        if match:
            return match.group(1).replace("/", "-")
    
    return None


def buscar_departamento(texto: str) -> Optional[str]:
    """
    Busca el nombre corto del departamento/oficina emisora en el texto OCR.

    Estrategias (en orden de prioridad):
    1. Misma línea del tipo de documento: "CIRCULAR SEDP No. 029"
    2. Líneas inmediatamente después del tipo de documento
    3. Patrones explícitos: DEPARTAMENTO DE X, DIRECCIóN DE X, etc.

    Returns:
        Abreviatura/nombre corto (máx 12 chars) o None
    """
    NOISE = {
        "NO", "DE", "EL", "LA", "LOS", "LAS", "UN", "UNA", "DEL", "AL",
        "NRO", "NUM", "POR", "CON", "QUE", "SE", "EN", "A", "Y", "O",
        "SU", "SUS", "AND", "THE", "TO", "IN",
    }
    TIPOS_RE = (
        r"OFICIO|CIRCULAR|TIKET|TICKET|DICTAMEN|RECIBO|MEMORANDUM|MEMORÁNDUM|"
        r"CONSTANCIA|ACUERDO|DIPLOMA|RESOLUCIÓN|RESOLUCION|ACTA|INFORME|"
        r"SOLICITUD|CONTRATO"
    )

    lineas = [l.strip() for l in texto.splitlines() if l.strip()]
    tipo_idx = None

    for i, linea in enumerate(lineas[:25]):
        if re.search(TIPOS_RE, linea.upper()):
            tipo_idx = i
            # Estrategia 1: misma línea — quitar keyword, número y signos
            linea_upper = linea.upper()
            linea_limpia = re.sub(TIPOS_RE, "", linea_upper)
            linea_limpia = re.sub(r"N[O°º]?\.?\s*\d[\d\-/]*", "", linea_limpia)
            linea_limpia = re.sub(r"\d[\d\-/]*", "", linea_limpia)
            for m in re.finditer(r"\b([A-ZÁÉÍÓÚÑÜ]{2,12})\b", linea_limpia):
                cand = m.group(1)
                if cand not in NOISE:
                    return cand
            break

    # Estrategia 2: líneas siguientes (sin números largos ni relleno)
    if tipo_idx is not None:
        for linea in lineas[tipo_idx + 1: tipo_idx + 6]:
            if re.search(r"\d{3,}", linea):           # fecha o número largo
                continue
            if re.search(r"[.]{3,}|\t", linea):       # relleno
                continue
            linea_upper = linea.upper().strip()
            # Línea que es solo una abreviatura
            m = re.match(r"^([A-ZÁÉÍÓÚÑÜ]{2,12})$", linea_upper)
            if m and m.group(1) not in NOISE:
                return m.group(1)
            # Primera palabra en mayúsculas corta de la línea
            m2 = re.search(r"\b([A-ZÁÉÍÓÚÑÜ]{2,10})\b", linea_upper)
            if m2 and m2.group(1) not in NOISE:
                return m2.group(1)[:12]

    # Estrategia 3: patrones organizacionales explícitos
    texto_upper = texto.upper()
    patrones_org = [
        r"(?:DEPARTAMENTO|DPTO\.?)\s+(?:DE\s+)?([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s]{1,30}?)(?:\n|,|\.)",
        r"(?:DIRECCI[OÓ]N)\s+(?:DE\s+)?([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s]{1,30}?)(?:\n|,|\.)",
        r"(?:SECRETAR[IÍ]A|UNIDAD|VICERRECTOR[IÍ]A|RECTOR[IÍ]A|DECANATO|FACULTAD)\s+(?:DE\s+)?([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s]{1,30}?)(?:\n|,|\.)",
    ]
    for patron in patrones_org:
        m = re.search(patron, texto_upper)
        if m:
            nombre = m.group(1).strip()
            palabras = [p for p in nombre.split() if p not in NOISE and len(p) > 2]
            if palabras:
                if len(palabras) > 1:
                    return "".join(p[0] for p in palabras)[:12]
                return palabras[0][:12]

    return None


def buscar_fecha(texto: str) -> Optional[str]:
    """
    Busca fechas en el texto y retorna la primera encontrada.
    
    Formatos soportados:
    - DD/MM/YYYY
    - DD-MM-YYYY
    - DD de MMMM de YYYY
    
    Args:
        texto: Texto donde buscar la fecha
        
    Returns:
        Fecha en formato YYYY-MM-DD o None si no se encuentra
    """
    # Patrón DD/MM/YYYY o DD-MM-YYYY
    patron_numerico = r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b'
    match = re.search(patron_numerico, texto)
    if match:
        dia, mes, año = match.groups()
        try:
            # Validar fecha
            fecha = datetime(int(año), int(mes), int(dia))
            return fecha.strftime("%Y-%m-%d")
        except ValueError:
            pass
    
    # Patrón con nombre de mes
    meses = {
        'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
        'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
        'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
    }
    
    patron_texto = r'\b(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})\b'
    match = re.search(patron_texto, texto, re.IGNORECASE)
    if match:
        dia, mes_texto, año = match.groups()
        mes_numero = meses.get(mes_texto.lower())
        if mes_numero:
            try:
                fecha = datetime(int(año), int(mes_numero), int(dia))
                return fecha.strftime("%Y-%m-%d")
            except ValueError:
                pass
    
    return None


def generar_nombre_limpio(tipo_doc: str, fecha: Optional[str],
                          numero_doc: Optional[str],
                          depto: Optional[str] = None,
                          sufijo: Optional[str] = None,
                          texto_contexto: Optional[str] = None) -> str:
    """
    Genera un nombre de archivo limpio y semántico.

    Formato: SIGLA-NUM_DEPTO_FECHA[_sufijo].pdf
    Ejemplos:
      CIR-029_SEDP_2023-06-28_OR.pdf
      OF-045_VRAC_2026-03-10_OR.pdf
      CIR_2026-03-10_OR.pdf          (sin número ni departamento)

    Args:
        tipo_doc:  Tipo de documento (OFICIO, CIRCULAR, etc.)
        fecha:     Fecha en formato YYYY-MM-DD o None
        numero_doc: Número del documento o None
        depto:     Departamento/oficina emisora o None
        sufijo:    Sufijo adicional (OR, RESPUESTA, ANEXO) o None

    Returns:
        Nombre de archivo con extensión .pdf
    """
    sigla = SIGLAS_DOCUMENTO.get(tipo_doc, tipo_doc[:3].upper())

    if numero_doc:
        num_limpio = re.sub(r'[^\w\-]', '', numero_doc)
        base = f"{sigla}-{num_limpio}"
    else:
        base = sigla

    # LISTA_ASISTENCIA standalone: priorizar EVENTO/ACTIVIDAD como descriptor
    if tipo_doc == "LISTA_ASISTENCIA" and texto_contexto and not depto and sufijo in (None, "OR"):
        texto_norm = ''.join(
            c for c in unicodedata.normalize('NFD', texto_contexto.upper())
            if unicodedata.category(c) != 'Mn'
        )
        m_evento = re.search(
            r'\b(?:EVENTO|ACTIVIDAD)\b[\s:.-]*([A-Z0-9 ]{4,60})',
            texto_norm
        )
        if m_evento:
            sugerido = re.sub(r'[^A-Z0-9 ]', ' ', m_evento.group(1))
            sugerido = re.sub(r'\s+', ' ', sugerido).strip()
            if sugerido:
                depto = sugerido[:20]

    partes = [base]
    if depto:
        depto_limpio = re.sub(r'[^\w]', '', depto).upper()[:12]
        if depto_limpio:
            partes.append(depto_limpio)
    if fecha:
        partes.append(fecha)
    if sufijo:
        partes.append(sufijo)
    return "_".join(partes) + ".pdf"


def _detectar_tipos_por_pagina(ruta_pdf: Path, logger: logging.Logger) -> List[str]:
    """Retorna el tipo detectado para cada página del PDF."""
    try:
        reader = PdfReader(str(ruta_pdf))
    except Exception as e:
        logger.error(f"❌ Error leyendo PDF {ruta_pdf.name}: {type(e).__name__} - {e}")
        return []

    total_paginas = len(reader.pages)
    tipos: List[str] = []
    
    logger.debug(f"🔍 Analizando {total_paginas} páginas de {ruta_pdf.name}")
    
    # Extracto texto de cada página
    textos_paginas = []
    for num_pagina in range(1, total_paginas + 1):
        texto = extraer_texto_ocr_pagina(ruta_pdf, num_pagina, logger)
        textos_paginas.append(texto)
    
    # Detectar tipos con estrategia inteligente
    for num_pagina in range(1, total_paginas + 1):
        texto = textos_paginas[num_pagina - 1]
        
        # Si la página tiene poco texto, combinar con páginas adyacentes
        if len(texto.strip()) < 50:
            contexto = ""
            # Agregar página anterior
            if num_pagina > 1:
                contexto += textos_paginas[num_pagina - 2] + "\n"
            # Agregar página actual
            contexto += texto
            # Agregar página siguiente
            if num_pagina < total_paginas:
                contexto += "\n" + textos_paginas[num_pagina]
            texto = contexto
        
        tipo = detectar_tipo_documento(texto) if texto else "DOCUMENTO"
        tipos.append(tipo)
        logger.debug(f"  Página {num_pagina}: {tipo} ({len(textos_paginas[num_pagina-1])} chars)")
    
    # Log del resultado final
    cambios = []
    for i in range(len(tipos) - 1):
        if tipos[i] != tipos[i + 1]:
            cambios.append(f"{tipos[i]}->{tipos[i+1]} (pág {i+1} a {i+2})")
    
    if cambios:
        logger.debug(f"📋 Cambios detectados: {', '.join(cambios)}")
    else:
        logger.debug(f"📋 Tipo uniforme: {tipos[0] if tipos else 'DESCONOCIDO'}")
    
    return tipos


def detectar_cambios_tipo_pdf(ruta_pdf: Path, logger: logging.Logger) -> dict:
    """
    Detecta cambios en un PDF y retorna información detallada.
    
    Returns:
        dict con:
        - 'necesita_segmentacion': bool (hay cambios entre tipos predefinidos)
        - 'puntos_cuestionables': list[(pag_anterior, pag_actual, tipo)]
        - 'tipos': list de tipos por página
        - 'numeros': list de números por página
    """
    try:
        reader = PdfReader(str(ruta_pdf))
    except Exception as e:
        logger.error(f"❌ Error leyendo PDF {ruta_pdf.name}: {type(e).__name__} - {e}")
        return {
            'necesita_segmentacion': False,
            'puntos_cuestionables': [],
            'tipos': [],
            'numeros': []
        }

    total_paginas = len(reader.pages)
    if total_paginas <= 1:
        return {
            'necesita_segmentacion': False,
            'puntos_cuestionables': [],
            'tipos': [],
            'numeros': []
        }
    
    tipos = []
    numeros = []
    necesita_segmentacion = False
    puntos_cuestionables = []
    
    logger.debug(f"🔍 Detectando cambios en {total_paginas} páginas de {ruta_pdf.name}")
    
    # Extraer tipo y número de cada página
    for num_pagina in range(1, total_paginas + 1):
        texto = extraer_texto_ocr_pagina(ruta_pdf, num_pagina, logger)
        tipo = detectar_tipo_documento(texto) if texto else "DOCUMENTO"
        numero = buscar_numero_documento(texto, tipo) if texto else None
        tipos.append(tipo)
        numeros.append(numero)
    
    # Verificar cambios significativos
    for i in range(len(tipos) - 1):
        tipo_actual = tipos[i]
        tipo_siguiente = tipos[i + 1]

        # Caso especial LISTA_ASISTENCIA: siempre manual para evitar anexión automática
        if tipo_siguiente == "LISTA_ASISTENCIA":
            logger.debug(f"❓ Punto cuestionable LISTA pág {i+1}: {tipo_actual} → LISTA_ASISTENCIA")
            puntos_cuestionables.append({
                'pag_anterior': i,
                'pag_actual': i + 1,
                'tipo': "LISTA_ASISTENCIA",
                'tipo_anterior': tipo_actual,
                'tipo_actual': tipo_siguiente,
                'es_caso_lista': True
            })
            continue

        # OCR puede degradar una página de lista a DOCUMENTO (sin encabezado claro).
        # También se fuerza decisión manual para evitar unir listas distintas por error.
        if tipo_actual == "LISTA_ASISTENCIA" and tipo_siguiente == "DOCUMENTO":
            logger.debug(f"❓ Punto cuestionable LISTA pág {i+1}: LISTA_ASISTENCIA → DOCUMENTO")
            puntos_cuestionables.append({
                'pag_anterior': i,
                'pag_actual': i + 1,
                'tipo': "LISTA_ASISTENCIA",
                'tipo_anterior': tipo_actual,
                'tipo_actual': tipo_siguiente,
                'es_caso_lista': True
            })
            continue
        
        # Caso 1: Cambio entre TIPOS PREDEFINIDOS diferentes
        if (tipo_actual in TIPOS_PREDEFINIDOS and 
            tipo_siguiente in TIPOS_PREDEFINIDOS and 
            tipo_actual != tipo_siguiente):
            logger.debug(f"📋 Cambio de tipo predefinido en pág {i+1}: {tipo_actual} → {tipo_siguiente}")
            necesita_segmentacion = True
        
        # Caso 2: MISMO tipo predefinido pero NÚMERO diferente
        elif (tipo_actual in TIPOS_PREDEFINIDOS and 
              tipo_siguiente in TIPOS_PREDEFINIDOS and
              tipo_actual == tipo_siguiente):
            num_actual = numeros[i]
            num_siguiente = numeros[i + 1]
            if num_actual and num_siguiente and num_actual != num_siguiente:
                logger.debug(f"📋 Cambio de número en pág {i+1}: {tipo_actual} #{num_actual} → #{num_siguiente}")
                necesita_segmentacion = True
            else:
                # MISMO tipo, NO hay criterio de número → Punto cuestionable (consultar usuario)
                logger.debug(f"❓ Punto cuestionable pág {i+1}: ¿{tipo_actual} #{num_actual} vs #{num_siguiente}?")
                puntos_cuestionables.append({
                    'pag_anterior': i,
                    'pag_actual': i + 1,
                    'tipo': tipo_actual
                })
        
        # Caso 3: DOCUMENTO genérico seguido de TIPO PREDEFINIDO
        # (El DOCUMENTO fue anexo, ahora comienza uno nuevo)
        elif (tipo_actual == "DOCUMENTO" and 
              tipo_siguiente in TIPOS_PREDEFINIDOS):
            logger.debug(f"📋 Ruptura en pág {i+1}: DOCUMENTO anexo → {tipo_siguiente} (nuevo tipo predefinido)")
            necesita_segmentacion = True
        
        # Caso 4: TIPO PREDEFINIDO → DOCUMENTO
        # El DOCUMENTO podría ser anexo o documento independiente
        # Consultar usuario para decidir
        elif (tipo_actual in TIPOS_PREDEFINIDOS and 
              tipo_siguiente == "DOCUMENTO"):
            logger.debug(f"❓ Punto cuestionable pág {i+1}: {tipo_actual} #{numeros[i]} seguido de DOCUMENTO desconocido")
            puntos_cuestionables.append({
                'pag_anterior': i,
                'pag_actual': i + 1,
                'tipo': f"DOCUMENTO_ANEXO_A_{tipo_actual}"
            })
    
    return {
        'necesita_segmentacion': necesita_segmentacion,
        'puntos_cuestionables': puntos_cuestionables,
        'tipos': tipos,
        'numeros': numeros
    }


def extraer_paginas_por_tipo(ruta_pdf: Path, logger: logging.Logger, carpeta_temp: Path,
                             tipos_info: Optional[dict] = None, decisiones_usuario: Optional[dict] = None) -> List[Path]:
    """
    Separa un PDF en segmentos usando lógica inteligente.
    
    Args:
        ruta_pdf: Ruta del PDF a segmentar
        logger: Logger para registrar operaciones
        carpeta_temp: Carpeta para archivos temporales
        tipos_info: Dict con 'tipos' y 'numeros' (si ya se calculó)
        decisiones_usuario: Dict con decisiones para puntos cuestionables
                           {(pag_anterior, pag_actual): 'mismo'/'diferente'}
    
    Returns:
        Lista con PDFs segmentados o PDF original si no hay cambios
    """
    try:
        reader = PdfReader(str(ruta_pdf))
    except Exception as e:
        logger.error(f"❌ Error leyendo PDF {ruta_pdf.name}: {type(e).__name__} - {e}")
        return [ruta_pdf]
    
    total_paginas = len(reader.pages)
    if total_paginas <= 1:
        return [ruta_pdf]
    
    # Si no vinieron tipos calcula
    if tipos_info is None:
        tipos = []
        numeros = []
        logger.debug(f"Analizando tipos en {total_paginas} páginas...")
        for num_pagina in range(1, total_paginas + 1):
            texto = extraer_texto_ocr_pagina(ruta_pdf, num_pagina, logger)
            tipo = detectar_tipo_documento(texto) if texto else "DOCUMENTO"
            numero = buscar_numero_documento(texto, tipo) if texto else None
            tipos.append(tipo)
            numeros.append(numero)
    else:
        tipos = tipos_info.get('tipos', [])
        numeros = tipos_info.get('numeros', [])
    
    if decisiones_usuario is None:
        decisiones_usuario = {}
    
    # Detectar límites de segmentación
    limites_segmentacion = set()
    
    for i in range(len(tipos) - 1):
        tipo_actual = tipos[i]
        tipo_siguiente = tipos[i + 1]

        # Caso especial LISTA_ASISTENCIA: decisiones 100% manuales
        if tipo_siguiente == "LISTA_ASISTENCIA" or (
            tipo_actual == "LISTA_ASISTENCIA" and tipo_siguiente == "DOCUMENTO"
        ):
            key = (i, i + 1)
            decision = decisiones_usuario.get(key)

            if decision == 'anexar_anterior':
                logger.debug(f"  Sin ruptura en pág {i+1}: usuario decidió ANEXAR al anterior")
            elif decision == 'unir_lista_anterior':
                if tipo_actual == "LISTA_ASISTENCIA":
                    logger.debug(f"  Sin ruptura en pág {i+1}: usuario decidió UNIR a lista anterior")
                else:
                    limites_segmentacion.add(i + 1)
                    logger.debug(f"  Ruptura en pág {i+1}: inicia bloque LISTA_ASISTENCIA separado")
            elif decision == 'nueva_lista':
                limites_segmentacion.add(i + 1)
                logger.debug(f"  Ruptura en pág {i+1}: usuario decidió NUEVA LISTA")
            else:
                # Fallback conservador: separar para no anexar automáticamente listas.
                limites_segmentacion.add(i + 1)
                logger.debug(f"  Ruptura en pág {i+1}: sin decisión de lista, se separa por seguridad")
            continue
        
        # Caso 1: Cambio entre TIPOS PREDEFINIDOS diferentes
        if (tipo_actual in TIPOS_PREDEFINIDOS and 
            tipo_siguiente in TIPOS_PREDEFINIDOS and 
            tipo_actual != tipo_siguiente):
            limites_segmentacion.add(i + 1)
            logger.debug(f"  Ruptura en pág {i+1}: tipo {tipo_actual} → {tipo_siguiente}")
        
        # Caso 2: MISMO tipo predefinido pero NÚMERO diferente
        elif (tipo_actual in TIPOS_PREDEFINIDOS and 
              tipo_siguiente in TIPOS_PREDEFINIDOS and
              tipo_actual == tipo_siguiente):
            num_actual = numeros[i]
            num_siguiente = numeros[i + 1]
            if num_actual and num_siguiente and num_actual != num_siguiente:
                limites_segmentacion.add(i + 1)
                logger.debug(f"  Ruptura en pág {i+1}: #número {num_actual} → #{num_siguiente} ({tipo_actual})")
            else:
                # Punto cuestionable - revisar decisión del usuario
                key = (i, i + 1)
                if key in decisiones_usuario:
                    decision = decisiones_usuario[key]
                    if decision == 'diferente':
                        limites_segmentacion.add(i + 1)
                        logger.debug(f"  Ruptura en pág {i+1}: usuario decidió DOCUMENTO NUEVO")
                    else:
                        logger.debug(f"  Sin ruptura en pág {i+1}: usuario decidió MISMO documento")
        
        # Caso 3: DOCUMENTO genérico seguido de TIPO PREDEFINIDO
        # (El DOCUMENTO fue anexo al anterior, ahora comienza uno nuevo)
        elif (tipo_actual == "DOCUMENTO" and 
              tipo_siguiente in TIPOS_PREDEFINIDOS):
            limites_segmentacion.add(i + 1)
            logger.debug(f"  Ruptura en pág {i+1}: DOCUMENTO anexo → {tipo_siguiente} (nuevo tipo predefinido)")
    
    # Si no hay límites, devolver PDF original
    if not limites_segmentacion:
        logger.debug(f"  PDF sin cambios significativos - no necesita segmentación")
        return [ruta_pdf]
    
    # Crear segmentos
    limites_ordenados = sorted([0] + list(limites_segmentacion) + [total_paginas])
    segmentos: List[Tuple[int, int]] = []
    
    for i in range(len(limites_ordenados) - 1):
        inicio = limites_ordenados[i]
        fin = limites_ordenados[i + 1] - 1
        if inicio <= fin:
            segmentos.append((inicio, fin))
    
    # Extraer y guardar segmentos
    try:
        carpeta_temp.mkdir(parents=True, exist_ok=True)
        salidas: List[Path] = []
        
        for idx, (ini, fin) in enumerate(segmentos, 1):
            writer = PdfWriter()
            for p in range(ini, fin + 1):
                writer.add_page(reader.pages[p])
            
            # Nombre descriptivo del segmento
            tipo_principal = tipos[ini] if ini < len(tipos) else "UNKNOWN"
            num_principal = numeros[ini] if ini < len(numeros) else None
            
            nombre_seg = f"{ruta_pdf.stem}__SEG{idx:02d}_{tipo_principal}"
            if num_principal:
                nombre_seg += f"_{num_principal.replace('/', '-')}"
            
            # Info de anexos
            pags_anexadas = []
            for p in range(ini, fin + 1):
                if tipos[p] == "DOCUMENTO":
                    pags_anexadas.append(str(p + 1))
            
            if pags_anexadas:
                nombre_seg += f"_ANEXOS"
            
            nombre_seg += ".pdf"
            
            ruta_seg = carpeta_temp / nombre_seg
            with open(ruta_seg, "wb") as f:
                writer.write(f)
            
            pags_info = f"págs {ini+1}-{fin+1}"
            anexo_info = f" (+anexos págs {','.join(pags_anexadas)})" if pags_anexadas else ""
            logger.info(f"  Segmento {idx}: {pags_info}{anexo_info} - {tipo_principal}#{num_principal if num_principal else 'N/A'}")
            salidas.append(ruta_seg)
        
        return salidas
    except Exception as e:
        logger.error(f"❌ Error segmentando {ruta_pdf.name}: {type(e).__name__} - {e}")
        return [ruta_pdf]
