# Public Image Collector

> A simple, responsible desktop GUI to collect public images from web pages.
> Una GUI de escritorio simple y responsable para recopilar imágenes públicas desde páginas web.

[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![PySide6](https://img.shields.io/badge/built%20with-PySide6-41CD52.svg)](https://wiki.qt.io/Qt_for_Python)
[![Status](https://img.shields.io/badge/status-v0.1-brightgreen.svg)]()

[English below](#english)

---

## Español

### Qué es

**Public Image Collector** es una herramienta local con interfaz gráfica para analizar páginas web públicas, detectar imágenes disponibles y descargarlas de forma ordenada.

Está pensada para:
- Organizar referencias visuales personales
- Recopilar recursos propios o de páginas donde tienes permiso
- Proyectos de investigación visual legítimos

### Qué NO hace

- No salta logins ni paywalls
- No rompe DRM
- No evade anti-bot ni usa proxies rotativos
- No descarga contenido privado
- No ignora deliberadamente `robots.txt`

### Cómo empezar

#### 1. Instalar dependencias

```bash
# Crear entorno virtual (recomendado)
python -m venv .venv

# Activar (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Instalar
pip install -r requirements.txt
```

#### 2. Ejecutar

```bash
python main.py
```

#### 3. Usar

1. Pega una **URL pública** en el campo superior.
2. Pulsa **Analizar**.
3. Selecciona las imágenes que quieres descargar (usa el checkbox maestro para todas).
4. Elige una **carpeta de destino** (por defecto: `~/Downloads/public-image-collector`).
5. Pulsa **Descargar seleccionadas**.

Las imágenes se guardan en una subcarpeta con el formato:
```
descargas/ejemplo.com_2026-05-05/
```

### Medidas de uso responsable

- **Límite de velocidad**: espera 0.5 segundos entre descargas
- **Límite de imágenes**: máximo 50 por análisis
- **User-Agent claro**: se identifica como `PublicImageCollector/0.1`
- **Verificación de `robots.txt`**: se comprueba antes de analizar
- **Sin duplicados**: detecta archivos idénticos por hash
- **Cancelable**: puedes detener el proceso en cualquier momento

### Requisitos

- Python 3.10+
- Windows, macOS o Linux

### Licencia

MIT. Úsala bajo tu propia responsabilidad.

---

## English

### What it is

**Public Image Collector** is a local desktop GUI tool to analyze public web pages, detect available images, and download them in an organized way.

Designed for:
- Organizing personal visual references
- Collecting your own resources or pages where you have permission
- Legitimate visual research projects

### What it does NOT do

- Does not bypass logins or paywalls
- Does not break DRM
- Does not evade anti-bot or use rotating proxies
- Does not download private content
- Does not deliberately ignore `robots.txt`

### Getting started

#### 1. Install dependencies

```bash
# Create virtual environment (recommended)
python -m venv .venv

# Activate (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Install
pip install -r requirements.txt
```

#### 2. Run

```bash
python main.py
```

#### 3. Use

1. Paste a **public URL** in the top field.
2. Click **Analyze**.
3. Select the images you want to download (use the master checkbox for all).
4. Choose a **destination folder** (default: `~/Downloads/public-image-collector`).
5. Click **Download selected**.

Images are saved in a subfolder like:
```
downloads/example.com_2026-05-05/
```

### Responsible use measures

- **Rate limiting**: waits 0.5 seconds between downloads
- **Image limit**: maximum 50 per analysis
- **Clear User-Agent**: identifies as `PublicImageCollector/0.1`
- **`robots.txt` check**: verified before analyzing
- **No duplicates**: detects identical files by hash
- **Cancellable**: you can stop the process at any time

### Requirements

- Python 3.10+
- Windows, macOS or Linux

### License

MIT. Use at your own responsibility.
