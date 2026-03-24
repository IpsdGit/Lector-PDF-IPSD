#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Verificador de Dependencias - Renombrador de PDFs V3
Instituto de Profesionalización y Superación Docente (IPSD)
Universidad Nacional Autónoma de Honduras
"""

import sys
import os

print("="*70)
print(" VERIFICACIÓN DE DEPENDENCIAS - RENOMBRADOR V3")
print("="*70)
print()

# Verificar versión de Python
print(f"✓ Python versión: {sys.version}")
print(f"✓ Ejecutable: {sys.executable}")
print()

# Lista de módulos a verificar
modulos = [
    ("customtkinter", "customtkinter", "UI moderna"),
    ("pytesseract", "pytesseract", "OCR"),
    ("pdf2image", "pdf2image", "Conversión PDF"),
    ("fuzzywuzzy", "fuzzywuzzy", "Similitud texto"),
    ("Levenshtein", "Levenshtein", "Acelera fuzzy"),
    ("PIL", "Pillow", "Procesamiento imágenes"),
    # Built-in
    ("hashlib", "hashlib (built-in)", "Hash MD5/SHA256"),
    ("json", "json (built-in)", "Metadata"),
    ("queue", "queue (built-in)", "Cola thread-safe"),
    ("logging", "logging (built-in)", "Logs"),
    ("threading", "threading (built-in)", "Threading"),
    ("tkinter", "tkinter (built-in)", "GUI base"),
]

errores = []
warnings = []

print("Verificando módulos Python:")
print("-"*70)

for modulo, nombre_completo, descripcion in modulos:
    try:
        __import__(modulo)
        print(f"  ✓ {nombre_completo:<30} → {descripcion}")
    except ImportError as e:
        print(f"  ✗ {nombre_completo:<30} → ERROR: {str(e)}")
        errores.append(nombre_completo)

print()

# Verificar Tesseract
print("Verificando herramientas externas:")
print("-"*70)

base_path = os.path.dirname(os.path.abspath(__file__))
tesseract_path = os.path.join(base_path, "Tesseract-OCR", "tesseract.exe")
poppler_path = os.path.join(base_path, "poppler", "Library", "bin")
assets_path = os.path.join(base_path, "Assets")

if os.path.exists(tesseract_path):
    print(f"  ✓ Tesseract-OCR encontrado: {tesseract_path}")
else:
    print(f"  ⚠ Tesseract-OCR NO encontrado en: {tesseract_path}")
    warnings.append("Tesseract-OCR")

if os.path.exists(poppler_path):
    print(f"  ✓ Poppler encontrado: {poppler_path}")
else:
    print(f"  ⚠ Poppler NO encontrado en: {poppler_path}")
    warnings.append("Poppler")

if os.path.exists(assets_path):
    print(f"  ✓ Carpeta Assets existe: {assets_path}")
    
    # Verificar logos
    logos = [
        "LOGOS-VRA-DC-UNAH (1).png",
        "Logo_App.png",
    ]
    
    for logo in logos:
        logo_path = os.path.join(assets_path, logo)
        if os.path.exists(logo_path):
            print(f"    ✓ Logo encontrado: {logo}")
        else:
            print(f"    ⚠ Logo NO encontrado: {logo}")
            warnings.append(f"Logo: {logo}")
else:
    print(f"  ⚠ Carpeta Assets NO existe: {assets_path}")
    warnings.append("Carpeta Assets")

print()
print("="*70)

if not errores and not warnings:
    print(" ✅ TODAS LAS DEPENDENCIAS ESTÁN CORRECTAMENTE INSTALADAS")
    print()
    print(" El proyecto está listo para ejecutar V3.")
elif errores:
    print(" ❌ HAY ERRORES CRÍTICOS")
    print()
    print(" Módulos faltantes:")
    for error in errores:
        print(f"   - {error}")
    print()
    print(" Ejecuta: python -m pip install -r requirements.txt")
else:
    print(" ⚠️  INSTALACIÓN COMPLETA CON ADVERTENCIAS")
    print()
    print(" Elementos opcionales faltantes:")
    for warning in warnings:
        print(f"   - {warning}")
    print()
    print(" La aplicación funcionará, pero algunas funcionalidades pueden estar limitadas.")

print("="*70)
print()

# Información adicional
print("📋 Información adicional:")
print(f"   Directorio de trabajo: {os.getcwd()}")
print(f"   Script ubicado en: {base_path}")
print()

sys.exit(0 if not errores else 1)
