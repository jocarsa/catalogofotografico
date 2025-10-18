#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Genera un ÚNICO index.html (HTML+CSS+JS embebidos) en la carpeta raíz,
con vistas: Carpetas (árbol + grid principal), Cronología, Búsqueda y visor modal.
Muestra barras de progreso y estadísticas “bonitas” en consola (Rich).

USO:
    python generate_photo_catalog_single.py [--root RUTA_RAIZ] [--outfile NOMBRE_HTML]

Requisitos:
    pip install pillow rich
"""

import os
import sys
import argparse
import json
import webbrowser
from datetime import datetime
from collections import defaultdict, Counter

from PIL import Image, ExifTags

# --- Opcional/bonito: Rich para progreso/estadísticas ---
RICH_AVAILABLE = True
try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn, TaskProgressColumn, MofNCompleteColumn
    from rich.table import Table
    from rich.panel import Panel
    from rich import box
except Exception:
    RICH_AVAILABLE = False

console = Console() if RICH_AVAILABLE else None

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.heic', '.tif', '.tiff', '.bmp'}
EXIF_TAGS = {v: k for k, v in ExifTags.TAGS.items()}

def is_image(path: str) -> bool:
    return os.path.splitext(path)[1].lower() in IMAGE_EXTS

def get_exif_datetime(img_path: str):
    try:
        with Image.open(img_path) as im:
            info = im._getexif()
            if not info:
                return None
            dto = info.get(EXIF_TAGS.get('DateTimeOriginal')) or info.get(EXIF_TAGS.get('DateTime'))
            if not dto:
                return None
            return datetime.strptime(dto, '%Y:%m:%d %H:%M:%S')
    except Exception:
        return None

def get_fs_datetime(img_path: str):
    ts = os.path.getmtime(img_path)
    return datetime.fromtimestamp(ts)

def walk_all(root_dir: str):
    """Devuelve (folders, files) donde files son rutas absolutas."""
    folders = []
    files = []
    for base, _, fnames in os.walk(root_dir):
        folders.append(base)
        for fname in fnames:
            files.append(os.path.join(base, fname))
    return folders, files

def scan_images(root_dir: str, html_dir: str):
    """
    Recorre root_dir y devuelve lista de fotos con metadatos.
    Muestra progreso y stats en consola si Rich está disponible.
    """
    stats = {
        "folders_total": 0,
        "files_total": 0,
        "images_found": 0,
        "exif_ok": 0,
        "exif_fallback": 0,
        "errors": 0
    }
    per_year = Counter()
    per_folder_count = Counter()

    folders, files = walk_all(root_dir)
    stats["folders_total"] = len(folders)
    stats["files_total"] = len(files)

    records = []

    if RICH_AVAILABLE:
        console.print(Panel.fit(f"[bold]📷 Generando catálogo[/bold]\n[dim]{root_dir}[/dim]", border_style="cyan"))
        progress = Progress(
            SpinnerColumn(style="cyan"),
            TextColumn("[bold]{task.fields[title]}[/bold]"),
            BarColumn(),
            TaskProgressColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            expand=True,
            transient=False
        )
        task_files = progress.add_task("", total=len(files), title="Escaneando ficheros")
        task_imgs  = progress.add_task("", total=0, title="Indexando imágenes (dinámico)")
        with progress:
            for fpath in files:
                progress.update(task_files, advance=1)
                if not is_image(fpath):
                    continue
                # Al ver la primera imagen, ajustamos total dinámico si procede
                progress.update(task_imgs, total=progress.tasks[task_imgs].total + 1, advance=0)

                try:
                    dt = get_exif_datetime(fpath)
                    if dt:
                        stats["exif_ok"] += 1
                    else:
                        dt = get_fs_datetime(fpath)
                        stats["exif_fallback"] += 1

                    rel_src = os.path.relpath(fpath, start=html_dir).replace('\\', '/')
                    folder_rel = os.path.relpath(os.path.dirname(fpath), start=root_dir).replace('\\', '/')
                    if folder_rel == '.':
                        folder_rel = ''
                    fname = os.path.basename(fpath)
                    name_composite = (folder_rel + '/' if folder_rel else '') + fname

                    rec = {
                        "src": rel_src,
                        "folder": folder_rel,
                        "filename": fname,
                        "name": name_composite,
                        "date_iso": dt.isoformat(),
                        "year": dt.year, "month": dt.month, "day": dt.day,
                        "hour": dt.hour, "minute": dt.minute, "second": dt.second
                    }
                    records.append(rec)
                    stats["images_found"] += 1
                    per_year[dt.year] += 1
                    per_folder_count[folder_rel] += 1
                    progress.update(task_imgs, advance=1)
                except Exception:
                    stats["errors"] += 1
    else:
        print(f"[1/2] Escaneando en: {root_dir}  (carpetas: {len(folders)}, ficheros: {len(files)})")
        for idx, fpath in enumerate(files, 1):
            if idx % 500 == 0:
                print(f"  … {idx}/{len(files)} ficheros")
            if not is_image(fpath):
                continue
            try:
                dt = get_exif_datetime(fpath) or get_fs_datetime(fpath)
                if get_exif_datetime(fpath):
                    stats["exif_ok"] += 1
                else:
                    stats["exif_fallback"] += 1
                rel_src = os.path.relpath(fpath, start=html_dir).replace('\\', '/')
                folder_rel = os.path.relpath(os.path.dirname(fpath), start=root_dir).replace('\\', '/')
                if folder_rel == '.': folder_rel = ''
                fname = os.path.basename(fpath)
                name_composite = (folder_rel + '/' if folder_rel else '') + fname
                records.append({
                    "src": rel_src, "folder": folder_rel, "filename": fname, "name": name_composite,
                    "date_iso": dt.isoformat(),
                    "year": dt.year, "month": dt.month, "day": dt.day,
                    "hour": dt.hour, "minute": dt.minute, "second": dt.second
                })
                stats["images_found"] += 1
                per_year[dt.year] += 1
                per_folder_count[folder_rel] += 1
            except Exception:
                stats["errors"] += 1

    records.sort(key=lambda r: r["date_iso"])

    # Resumen bonito
    if RICH_AVAILABLE:
        table = Table(title="Resumen de indexación", box=box.SIMPLE_HEAVY)
        table.add_column("Métrica", style="bold cyan")
        table.add_column("Valor", justify="right")
        table.add_row("Carpetas", str(stats["folders_total"]))
        table.add_row("Ficheros totales", str(stats["files_total"]))
        table.add_row("Imágenes indexadas", str(stats["images_found"]))
        table.add_row("EXIF OK", str(stats["exif_ok"]))
        table.add_row("EXIF fallback (mtime)", str(stats["exif_fallback"]))
        table.add_row("Errores", f"[red]{stats['errors']}[/red]" if stats["errors"] else "0")
        console.print(table)

        if per_year:
            # Mostrar distribución por años (top 12)
            top_years = sorted(per_year.items(), key=lambda x: (x[0]))  # orden cronológico
            bar_max = max(c for _, c in top_years)
            console.print("\n[bold]Distribución por años[/bold]")
            for year, cnt in top_years:
                bar = "█" * max(1, int((cnt / bar_max) * 30))
                console.print(f"[dim]{year}[/dim] {bar} [bold]{cnt}[/bold]")

        if per_folder_count:
            console.print("\n[bold]Top 10 carpetas por nº de fotos[/bold]")
            t2 = Table(box=box.MINIMAL_DOUBLE_HEAD)
            t2.add_column("Carpeta")
            t2.add_column("Fotos", justify="right")
            for folder, cnt in per_folder_count.most_common(10):
                t2.add_row(folder or "(raíz)", str(cnt))
            console.print(t2)
    else:
        print(f"[OK] Imágenes: {stats['images_found']} | EXIF OK: {stats['exif_ok']} | Fallback: {stats['exif_fallback']} | Errores: {stats['errors']}")

    return records

def build_html(photos_json: str, title: str = "Catálogo de Fotos"):
    """Devuelve el HTML completo (CSS/JS inline) como string."""
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
:root{{ --bg:#0e0f12; --bg-elev:#15171c; --panel:#1b1e25; --text:#e8e8ea; --muted:#a1a6b3; --accent:#7aa2ff; --accent-2:#78f1d8; --border:#262a33; --chip:#232734; --shadow:0 10px 30px rgba(0,0,0,.35); }}
*{{box-sizing:border-box}} html,body{{margin:0;padding:0;background:var(--bg);color:var(--text);font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Cantarell,"Noto Sans",sans-serif}}
img{{display:block;max-width:100%;height:auto}}
.topbar{{position:sticky;top:0;z-index:50;display:flex;align-items:center;justify-content:space-between;padding:12px 18px;background:linear-gradient(180deg,var(--bg-elev),rgba(14,15,18,.6));border-bottom:1px solid var(--border);backdrop-filter:saturate(1.2) blur(8px)}}
.brand{{font-weight:700;letter-spacing:.2px}}
.views{{display:flex;gap:8px}}
.view-btn{{background:var(--chip);color:var(--text);border:1px solid var(--border);padding:8px 12px;border-radius:10px;cursor:pointer}}
.view-btn[aria-pressed="true"]{{outline:2px solid var(--accent);background:linear-gradient(180deg,#202434,#181b25)}}
.view-btn:hover{{transform:translateY(-1px)}}
.toolbar{{padding:10px 18px;border-bottom:1px solid var(--border);background:var(--bg)}}
.search-inline{{display:flex;gap:8px;align-items:center}}
.search-inline input,.search-inline button{{background:var(--chip);color:var(--text);border:1px solid var(--border);padding:8px 10px;border-radius:10px}}
#btnSearch{{background:linear-gradient(180deg,#2a334d,#232a3f);border-color:#2e3650}}
#btnClear{{background:linear-gradient(180deg,#3a2430,#2c1b25);border-color:#412534}}
#content{{padding:18px}}
.folders-layout{{display:grid;grid-template-columns:260px 1fr;gap:16px}}
.sidebar{{background:var(--panel);border:1px solid var(--border);border-radius:14px;padding:12px;max-height:calc(100vh - 130px);overflow:auto}}
.sidebar h3{{margin:6px 6px 10px;font-size:1rem;color:var(--muted)}}
.tree{{list-style:none;margin:0;padding:0}}
.tree li{{margin:0;padding:4px 6px}}
.tree button{{width:100%;text-align:left;background:transparent;color:var(--text);border:1px solid transparent;border-radius:8px;padding:6px 8px;cursor:pointer}}
.tree button.active{{background:linear-gradient(180deg,#243148,#1d2638);border-color:#31405f}}
.tree button:hover{{background:#20242f}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:14px}}
.card{{background:var(--panel);border:1px solid var(--border);border-radius:14px;overflow:hidden;box-shadow:var(--shadow);transition:transform .12s ease,box-shadow .12s ease}}
.card:hover{{transform:translateY(-2px);box-shadow:0 16px 40px rgba(0,0,0,.45)}}
.card .thumb{{aspect-ratio:4/3;object-fit:cover;background:#0a0b0d}}
.card .title{{padding:10px 12px;font-size:.9rem;color:var(--muted);border-top:1px solid var(--border);display:flex;justify-content:space-between;gap:10px}}
.badge{{font-size:.72rem;background:var(--chip);padding:2px 8px;border-radius:999px;border:1px solid var(--border);color:var(--muted)}}
.folder-tile{{cursor:pointer}}
.folder-name{{font-weight:600}}
.folder-count{{font-size:.78rem}}
.timeline{{display:flex;flex-direction:column;gap:18px}}
.group{{background:var(--panel);border:1px solid var(--border);border-radius:14px;padding:12px}}
.group h4{{margin:0 0 10px 0;color:var(--accent)}}
.group .subgrid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:10px}}
.modal{{position:fixed;inset:0;background:rgba(0,0,0,.78);display:none;align-items:center;justify-content:center;padding:30px;z-index:100}}
.modal[aria-hidden="false"]{{display:flex}}
.modal-body{{background:var(--bg-elev);border:1px solid var(--border);border-radius:16px;max-width:min(92vw,1600px);max-height:86vh;display:flex;flex-direction:column;overflow:hidden;box-shadow:var(--shadow)}}
.modal-body img{{max-width:min(92vw,1600px);max-height:74vh;object-fit:contain;background:#050608}}
.modal .meta{{display:flex;justify-content:space-between;gap:10px;padding:10px 12px;border-top:1px solid var(--border);color:var(--muted)}}
.modal-close,.modal-nav{{background:var(--chip);border:1px solid var(--border);color:var(--text)}}
.modal-close{{position:absolute;top:16px;right:16px;border-radius:10px;padding:8px 10px;cursor:pointer}}
.modal-nav{{position:absolute;top:50%;transform:translateY(-50%);border-radius:12px;padding:10px 14px;font-size:1.1rem;cursor:pointer}}
.modal-nav.prev{{left:18px}} .modal-nav.next{{right:18px}}
.hidden{{display:none}} .muted{{color:var(--muted)}}
</style>
</head>
<body>
<header class="topbar">
  <div class="brand">📷 Catálogo de Fotos</div>
  <nav class="views">
    <button class="view-btn" data-view="folders" aria-pressed="true">Carpetas</button>
    <button class="view-btn" data-view="chronology">Cronología</button>
    <button class="view-btn" data-view="search">Buscar</button>
  </nav>
</header>
<section class="toolbar">
  <div class="search-inline" data-view-only="search">
    <input id="q" type="search" placeholder="Buscar por nombre (carpeta/archivo)…" />
    <input id="dateFrom" type="date" />
    <input id="dateTo" type="date" />
    <button id="btnSearch">Buscar</button>
    <button id="btnClear">Limpiar</button>
  </div>
</section>
<main id="content"></main>
<div id="modal" class="modal" aria-hidden="true">
  <button class="modal-close" id="modalClose" aria-label="Cerrar">✕</button>
  <button class="modal-nav prev" id="modalPrev" aria-label="Anterior">←</button>
  <div class="modal-body">
    <img id="modalImg" alt="">
    <div class="meta">
      <div id="modalName" class="meta-name"></div>
      <div id="modalDate" class="meta-date"></div>
    </div>
  </div>
  <button class="modal-nav next" id="modalNext" aria-label="Siguiente">→</button>
</div>
<script>
// Dataset embebido
window.PHOTOS = {photos_json};

// --- Estado y refs ---
const state = {{ view:'folders', currentList:[], currentIndex:-1 }};
const elContent = document.getElementById('content');
const modal = document.getElementById('modal');
const modalImg = document.getElementById('modalImg');
const modalName = document.getElementById('modalName');
const modalDate = document.getElementById('modalDate');
const modalClose = document.getElementById('modalClose');
const modalPrev = document.getElementById('modalPrev');
const modalNext = document.getElementById('modalNext');
const byDate = (a,b)=>a.date_iso.localeCompare(b.date_iso);

// --- Botones de vista ---
document.querySelectorAll('.view-btn').forEach(b => b.addEventListener('click', () => {{
  document.querySelectorAll('.view-btn').forEach(x => x.setAttribute('aria-pressed','false'));
  b.setAttribute('aria-pressed','true');
  switchView(b.dataset.view);
}}));
function switchView(v){{
  state.view = v;
  document.querySelectorAll('[data-view-only]').forEach(n => {{
    n.classList.toggle('hidden', n.getAttribute('data-view-only') !== v);
  }});
  if(v==='folders') renderFolders();
  if(v==='chronology') renderChronology();
  if(v==='search') renderSearch();
}}
function escapeHtml(s){{ return (s||'').replace(/[&<>\"']/g, m => ({{'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',\"'\":'&#039;'}})[m]); }}
function createPhotoCard(photo, listForModal){{
  const card = document.createElement('div'); card.className = 'card';
  const img = document.createElement('img'); img.className='thumb'; img.loading='lazy'; img.src=photo.src; img.alt=photo.name; card.appendChild(img);
  const title = document.createElement('div'); title.className='title';
  title.innerHTML = `<span class="muted">{{name}}</span> <span class="badge">{{date}}</span>`
    .replace('{{name}}', escapeHtml(photo.filename))
    .replace('{{date}}', escapeHtml(photo.date_iso.replace('T',' ').substring(0,19)));
  card.appendChild(title);
  card.addEventListener('click', ()=>openModal(listForModal, listForModal.indexOf(photo)));
  return card;
}}
function buildFolderIndex(){{
  const idx = new Map();
  for(const p of window.PHOTOS){{
    const f = p.folder || '';
    if(!idx.has(f)) idx.set(f, {{count:0, first:p}});
    idx.get(f).count += 1;
  }}
  return idx;
}}
function buildFolderTree(){{
  const set = new Set(window.PHOTOS.map(p => p.folder || ''));
  const root = {{}};
  set.forEach(path => {{
    const parts = path===''?[]:path.split('/');
    let cur = root;
    for(const seg of parts){{
      cur.children = cur.children || {{}};
      cur.children[seg] = cur.children[seg] || {{}};
      cur = cur.children[seg];
    }}
  }});
  return root;
}}
// ---- Vista: Carpetas ----
function renderFolders(){{
  elContent.innerHTML='';
  const layout = document.createElement('div'); layout.className='folders-layout';
  const sidebar = document.createElement('aside'); sidebar.className='sidebar'; sidebar.innerHTML='<h3>Carpetas</h3>';
  const treeUl = document.createElement('ul'); treeUl.className='tree'; sidebar.appendChild(treeUl);
  const main = document.createElement('div');
  layout.appendChild(sidebar); layout.appendChild(main); elContent.appendChild(layout);

  const tree = buildFolderTree();
  const folderIndex = buildFolderIndex();

  function renderNode(ul,node,basePath){{
    const names = Object.keys(node.children||{{}}).sort();
    if(basePath===undefined) basePath='';
    if(ul===treeUl && basePath===''){{
      const li=document.createElement('li'); const btn=document.createElement('button');
      btn.textContent='• (todas)'; btn.addEventListener('click', ()=>showFolder('')); li.appendChild(btn); ul.appendChild(li);
    }}
    for(const name of names){{
      const li=document.createElement('li'); const btn=document.createElement('button');
      const full = basePath? basePath+'/'+name : name;
      btn.textContent=name; btn.addEventListener('click', ()=>showFolder(full));
      li.appendChild(btn);
      const childUl=document.createElement('ul'); childUl.className='tree'; li.appendChild(childUl); ul.appendChild(li);
      renderNode(childUl, node.children[name], full);
    }}
  }} renderNode(treeUl, tree, '');

  function renderFolderTiles(){{
    main.innerHTML='';
    const grid = document.createElement('div'); grid.className='grid';
    const folders = Array.from(folderIndex.keys()).sort();
    for(const folder of folders){{
      const meta = folderIndex.get(folder); const first = meta.first;
      const card=document.createElement('div'); card.className='card folder-tile';
      const img=document.createElement('img'); img.className='thumb'; img.loading='lazy'; img.src=first.src; img.alt=folder||'(raíz)'; card.appendChild(img);
      const title=document.createElement('div'); title.className='title';
      title.innerHTML = `<span class="folder-name">{{name}}</span><span class="badge">{{count}} foto(s)</span>`
         .replace('{{name}}', escapeHtml(folder||'(raíz)'))
         .replace('{{count}}', String(meta.count));
      card.appendChild(title);
      card.addEventListener('click', ()=>showFolder(folder));
      grid.appendChild(card);
    }}
    main.appendChild(grid);
  }}

  function showFolder(path){{
    treeUl.querySelectorAll('button').forEach(b=>b.classList.remove('active'));
    const btn = Array.from(treeUl.querySelectorAll('button')).find(b=>b.textContent === (path||'• (todas)'));
    if(btn) btn.classList.add('active');

    if(!path){{ renderFolderTiles(); return; }}
    main.innerHTML='';
    const grid=document.createElement('div'); grid.className='grid';
    const list = window.PHOTOS.filter(p => (p.folder||'') === path).sort(byDate);
    state.currentList = list.slice();
    for(const p of list) grid.appendChild(createPhotoCard(p, state.currentList));
    main.appendChild(grid);
  }}

  showFolder('');
}}
// ---- Vista: Cronología ----
function renderChronology(){{
  elContent.innerHTML=''; const container=document.createElement('div'); container.className='timeline';
  const groups={{}};
  for(const p of window.PHOTOS){{
    const Y=String(p.year), M=String(p.month).padStart(2,'0'), D=String(p.day).padStart(2,'0');
    groups[Y]=groups[Y]||{{}}; groups[Y][M]=groups[Y][M]||{{}}; groups[Y][M][D]=groups[Y][M][D]||[]; groups[Y][M][D].push(p);
  }}
  for(const Y of Object.keys(groups).sort()){{
    const yWrap=document.createElement('div'); yWrap.className='group';
    const yTitle=document.createElement('h4'); yTitle.textContent=Y; yWrap.appendChild(yTitle);
    for(const M of Object.keys(groups[Y]).sort()){{
      const mWrap=document.createElement('div'); mWrap.style.marginBottom='10px';
      const mTitle=document.createElement('div'); mTitle.className='badge'; mTitle.textContent=Y+'-'+M; mWrap.appendChild(mTitle);
      for(const D of Object.keys(groups[Y][M]).sort()){{
        const dTitle=document.createElement('div'); dTitle.className='muted'; dTitle.style.margin='8px 0 6px'; dTitle.textContent=Y+'-'+M+'-'+D; mWrap.appendChild(dTitle);
        const sub=document.createElement('div'); sub.className='subgrid';
        const list=groups[Y][M][D].slice().sort(byDate); const listForModal=list.slice();
        for(const p of list) sub.appendChild(createPhotoCard(p, listForModal));
        mWrap.appendChild(sub);
      }}
      yWrap.appendChild(mWrap);
    }}
    container.appendChild(yWrap);
  }} elContent.appendChild(container);
}}
// ---- Vista: Búsqueda ----
function renderSearch(){{
  elContent.innerHTML='';
  const grid=document.createElement('div'); grid.className='grid'; elContent.appendChild(grid);
  const q=document.getElementById('q'); const dateFrom=document.getElementById('dateFrom'); const dateTo=document.getElementById('dateTo');
  const btnSearch=document.getElementById('btnSearch'); const btnClear=document.getElementById('btnClear');

  function run(){{
    const text=(q.value||'').trim().toLowerCase();
    const from = dateFrom.value ? new Date(dateFrom.value+'T00:00:00') : null;
    const to   = dateTo.value   ? new Date(dateTo.value  +'T23:59:59') : null;
    let list = window.PHOTOS.filter(p=>{{
      let ok=true;
      if(text) ok=ok && (p.name||'').toLowerCase().includes(text);
      if(from) ok=ok && (new Date(p.date_iso) >= from);
      if(to)   ok=ok && (new Date(p.date_iso) <= to);
      return ok;
    }}).sort(byDate);
    grid.innerHTML=''; state.currentList = list.slice();
    for(const p of list) grid.appendChild(createPhotoCard(p, state.currentList));
  }}
  btnSearch.onclick=run; btnClear.onclick=()=>{{ q.value=''; dateFrom.value=''; dateTo.value=''; run(); }};
  q.onkeydown=(e)=>{{ if(e.key==='Enter') run(); }};
  run();
}}
// ---- Modal ----
function openModal(list, index){{
  if(!list || index<0) return; state.currentList=list; state.currentIndex=index;
  const p=list[index]; modalImg.src=p.src; modalImg.alt=p.name;
  modalName.textContent=p.name; modalDate.textContent=p.date_iso.replace('T',' ').substring(0,19);
  modal.setAttribute('aria-hidden','false');
}}
function closeModal(){{ modal.setAttribute('aria-hidden','true'); state.currentIndex=-1; }}
function nav(delta){{
  if(state.currentIndex<0) return;
  let i=state.currentIndex + delta; if(i<0) i=state.currentList.length-1; if(i>=state.currentList.length) i=0;
  openModal(state.currentList, i);
}}
document.getElementById('modalClose').addEventListener('click', closeModal);
document.getElementById('modalPrev').addEventListener('click', ()=>nav(-1));
document.getElementById('modalNext').addEventListener('click', ()=>nav(1));
modal.addEventListener('click', (e)=>{{ if(e.target===modal) closeModal(); }});
window.addEventListener('keydown', (e)=>{{ if(modal.getAttribute('aria-hidden')==='true') return; if(e.key==='Escape') closeModal(); if(e.key==='ArrowLeft') nav(-1); if(e.key==='ArrowRight') nav(1); }});
// Inicial
switchView('folders');
</script>
</body>
</html>""".replace("{photos_json}", photos_json)

def main():
    ap = argparse.ArgumentParser(description="Genera un único index.html con catálogo fotográfico y progreso en consola.")
    ap.add_argument("--root", default=".", help="Carpeta raíz que contiene las fotos (por defecto, .)")
    ap.add_argument("--outfile", default="index.html", help="Nombre del archivo HTML de salida (por defecto, index.html)")
    args = ap.parse_args()

    root_dir = os.path.abspath(args.root)
    out_html = os.path.abspath(os.path.join(root_dir, args.outfile))

    # 1) Escanear + estadísticas con progreso
    photos = scan_images(root_dir, os.path.dirname(out_html))
    if not photos:
        print("No se encontraron imágenes. Extensiones soportadas:", ", ".join(sorted(IMAGE_EXTS)))
        sys.exit(0)

    # 2) Generar HTML
    if RICH_AVAILABLE:
        console.rule("[bold]Generando HTML[/bold]")
    photos_json = json.dumps(photos, ensure_ascii=False)
    html = build_html(photos_json)
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(html)

    # 3) Abrir navegador
    if RICH_AVAILABLE:
        console.print(Panel.fit(f"[green]Listo[/green] ✅ {len(photos)} imágenes indexadas\n[dim]{out_html}[/dim]", border_style="green"))
    else:
        print(f"[OK] Generado: {out_html}")

    try:
        url = "file://" + out_html
        webbrowser.open(url, new=2)
        if RICH_AVAILABLE:
            console.print("[cyan]Abriendo navegador…[/cyan]")
        else:
            print("Abriendo navegador…")
    except Exception as e:
        if RICH_AVAILABLE:
            console.print(f"[red]No se pudo abrir el navegador automáticamente[/red]: {e}")
        else:
            print("No se pudo abrir el navegador automáticamente:", e)
            print("Abre manualmente:", out_html)

if __name__ == "__main__":
    main()

