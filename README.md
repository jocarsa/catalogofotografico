Aquí tienes el contenido para `index.md` (README) de tu repositorio. Está pensado para `https://github.com/jocarsa/catalogofotografico` y describe el script de una sola pasada con estadísticas en consola y un único `index.html` embebido.

---

# Catálogo Fotográfico — HTML único + Progreso en consola

[![Repo](https://img.shields.io/badge/GitHub-jocarsa%2Fcatalogofotografico-24292e?logo=github)](https://github.com/jocarsa/catalogofotografico)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Pillow](https://img.shields.io/badge/Pillow-required-orange)
![Rich](https://img.shields.io/badge/Rich-optional-purple)

Genera una **galería fotográfica** en un **único archivo `index.html`** (con HTML+CSS+JS embebidos) a partir de una carpeta raíz con fotos (y subcarpetas). Incluye:

* **Vista Carpetas**: árbol lateral + **rejilla de carpetas** en el panel principal (cuando no hay carpeta seleccionada).
* **Vista Cronología**: agrupación **Año → Mes → Día** (orden por hora/min/seg).
* **Vista Búsqueda**: por **fecha** (rango) y por **nombre compuesto** (carpeta/archivo).
* **Visor modal** con navegación **Anterior/Siguiente** (+ atajos ← → y **Esc**).
* **Tema oscuro** elegante, orientado a fotografía.
* **Estadísticas y barras de progreso** en consola (usa `rich` si está disponible).
* **Apertura automática del navegador** al finalizar la generación (si el sistema lo permite).

---

## Capturas

> (Opcional) Añade aquí tus capturas reales cuando generes el catálogo.

* Vista carpetas (rejilla principal):
  `docs/capturas/vista-carpetas.png`
* Vista cronología:
  `docs/capturas/vista-cronologia.png`
* Búsqueda + modal:
  `docs/capturas/vista-busqueda-modal.png`
* Progreso en consola (Rich):
  `docs/capturas/console-rich.png`

---

## Requisitos

* **Python 3.9+**

* Librerías:

  ```bash
  pip install pillow rich
  ```

  > `rich` es opcional (solo mejora la salida en consola). `pillow` es necesaria para leer EXIF cuando exista.

* Extensiones soportadas por defecto:
  `.jpg, .jpeg, .png, .gif, .webp, .heic, .tif, .tiff, .bmp`

  > Nota: Para **HEIC/HEIF** puede requerirse soporte adicional en la instalación del sistema/librerías.

---

## Uso rápido

Coloca el script en la **carpeta raíz** donde están tus fotos (con subcarpetas), y ejecuta:

```bash
python generate_photo_catalog_single.py --root . --outfile index.html
```

* Crea **`index.html`** en la carpeta indicada por `--root` (por defecto, la actual).
* Inserta **todas las rutas de imágenes de forma relativa** a `index.html`.
* Intenta **abrir el navegador** automáticamente al terminar.

Si prefieres ejecutar desde otra ruta:

```bash
python path/al/script/generate_photo_catalog_single.py --root /ruta/a/fotos --outfile index.html
```

Abre manualmente el resultado si no se abre solo:

```
file:///ruta/a/fotos/index.html
```

---

## Estadísticas en consola

Durante el escaneo se muestran (si `rich` está disponible):

* **Barras de progreso** para ficheros escaneados e **imágenes indexadas**.
* Contadores: **EXIF OK**, **fallback a mtime**, **errores**.
* **Tabla resumen** al final.
* Distribución por **años** y **Top 10 carpetas** por número de fotos.

Ejemplo de instalación + ejecución:

```bash
pip install pillow rich
python generate_photo_catalog_single.py --root . --outfile index.html
```

---

## Características clave

* **Un solo archivo**: no genera carpetas auxiliares; todo el CSS/JS va embebido en `index.html`.
* **Carpetas**: árbol lateral y **rejilla de carpetas** con miniatura (primera foto) y contador.
* **Cronología**: agrupación por año/mes/día, orden temporal fino.
* **Búsqueda**: por texto (coincide con `carpeta/archivo`) y por rango de fechas (usa EXIF si existe y, si no, mtime).
* **Visor modal**: navegación con clics y teclado (← →, Esc).
* **Tema oscuro**: estética “galería fotográfica” profesional.

---

## Parámetros

```
--root     Carpeta raíz con las fotos.   (por defecto: .)
--outfile  Nombre del HTML de salida.    (por defecto: index.html)
```

---

## Notas y limitaciones

* **Fechas**: Se prioriza `DateTimeOriginal`/`DateTime` de EXIF. Si no existe, se usa **mtime del fichero** (fecha de modificación).
* **Rutas**: El script calcula rutas **relativas** a `index.html`, por lo que puedes abrirlo directamente con `file://` sin servidor.
* **Rendimiento**: Para colecciones muy grandes, abrir un HTML con decenas de miles de entradas puede ser exigente para el navegador.

  * Sugerencias: dividir por años, generar varios `index.html` por secciones, o servir con un pequeño HTTP server.
* **Miniaturas**: Actualmente se muestran las imágenes **originales** (con `loading="lazy"`). Para catálogos masivos, considera un pipeline previo de **thumbnails**.
* **Vídeo**: Este repositorio está centrado en **imágenes**. Extender a vídeo es posible, pero no está incluido de serie.
* **HEIC/HEIF**: En algunos sistemas, Pillow necesita dependencias extra para leer metadatos/formato.

---

## Estructura del repo (sugerida)

```
catalogofotografico/
├─ generate_photo_catalog_single.py   # Script principal
├─ index.md                           # Este README principal
└─ docs/
   └─ capturas/                       # Imágenes de ejemplo para el README
```

---

## Solución de problemas

* **No se abre el navegador automáticamente**
  Algunos entornos de escritorio/servidor lo bloquean. Abre manualmente el archivo `index.html`.

* **No se detecta la fecha EXIF**
  El archivo podría no tener metadatos o Pillow no pudo leerlos. Se usará mtime.

* **HEIC no carga / no hay miniatura**
  Asegúrate de que tu instalación de Pillow soporta HEIC/HEIF o convierte previamente a JPG/PNG.

* **Rendimiento lento en el navegador**
  Divide el catálogo en varias ejecuciones por carpeta/año o añade un paso de generación de miniaturas.

---

## Contribuir

¡Contribuciones bienvenidas! Ideas útiles:

* Opción para **generar miniaturas**.
* **Soporte de vídeo** (mp4, mov) con poster frame.
* **Paginación** o **carga incremental**.
* **Filtro avanzado** por extensión/Carpeta/EXIF (ISO, modelo de cámara, etc.).

1. Haz un fork del repositorio
2. Crea una rama para tu feature/fix
3. Envía un Pull Request con una descripción clara

---

## Licencia

Este proyecto se distribuye bajo la licencia **MIT**. Consulta `LICENSE` para más detalles.

---

## Autor

**Jose Vicente Carratalá (JOCARSA)**
Repositorio: [https://github.com/jocarsa/catalogofotografico](https://github.com/jocarsa/catalogofotografico)

---

### Comando “one-liner” de ejemplo

```bash
pip install pillow rich && python generate_photo_catalog_single.py --root . --outfile index.html
```

> Sugerencia: añade `generate_photo_catalog_single.py` a tu carpeta raíz de fotos y ejecútalo cada vez que añadas nuevas imágenes. El HTML resultante es estático y portable.
