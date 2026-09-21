#!/usr/bin/env python3
"""
Genera las mini-páginas de cada auto (autos/<auto>.html) con las etiquetas
que WhatsApp usa para mostrar la FOTO junto al enlace, y activa el enlace
del auto dentro de los mensajes de WhatsApp de index.html.

Uso (después de publicar la página y saber su enlace):
    python3 generar_autos.py https://tu-sitio.netlify.app

Vuelve a ejecutarlo cada vez que cambies un auto, precio o foto en index.html.
"""
import html
import pathlib
import re
import sys

AQUI = pathlib.Path(__file__).resolve().parent
INDEX = AQUI / 'index.html'


def main():
    if len(sys.argv) != 2 or not sys.argv[1].startswith(('http://', 'https://')):
        sys.exit('Uso: python3 generar_autos.py https://tu-sitio.netlify.app')
    site = sys.argv[1].rstrip('/')
    src = INDEX.read_text(encoding='utf-8')

    autos = []
    for art in re.findall(r'<article[^>]*class="car-card.*?</article>', src, re.S):
        if re.match(r'<article[^>]*data-oculto', art):
            continue  # auto no disponible: no se crea su página
        slug = re.search(r'data-photos="fotos/(.*?)-1\.jpg', art).group(1)
        tags = [re.sub(r'<svg.*?</svg>', '', t, flags=re.S).strip()
                for t in re.findall(r'<span class="tag">(.*?)</span>', art, re.S)]
        autos.append(dict(
            slug=slug,
            name=re.search(r'<h3[^>]*>(.*?)</h3>', art).group(1).strip(),
            sub=re.search(r'</h3>\s*<p[^>]*>(.*?)</p>', art, re.S).group(1).strip(),
            price=re.search(r'text-3xl[^>]*>\s*(\$[\d,]+)', art).group(1),
            year=tags[0],
            km=next((x for x in tags[1:] if 'km' in x.lower()), ''),
            trans=next((x for x in tags[1:] if 'km' not in x.lower()), ''),
        ))

    out = AQUI / 'autos'
    out.mkdir(exist_ok=True)
    for a in autos:
        titulo = f"{a['name']} {a['year']} · {a['price']} MXN | Seminuevos Miguel Ángel"
        datos = ' · '.join(x for x in (a['year'], a['km'], a['trans']) if x)
        desc = f"{datos}. {a['sub']}. Pregunta por WhatsApp."
        (out / f"{a['slug']}.html").write_text(f'''<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{html.escape(titulo)}</title>
  <meta name="description" content="{html.escape(desc, quote=True)}" />
  <meta property="og:type" content="website" />
  <meta property="og:site_name" content="Seminuevos Miguel Ángel" />
  <meta property="og:title" content="{html.escape(a['name'] + ' ' + a['year'] + ' · ' + a['price'] + ' MXN', quote=True)}" />
  <meta property="og:description" content="{html.escape(desc, quote=True)}" />
  <meta property="og:url" content="{site}/autos/{a['slug']}.html" />
  <meta property="og:image" content="{site}/fotos/{a['slug']}-portada.jpg" />
  <meta property="og:image:width" content="1000" />
  <meta property="og:image:height" content="750" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta http-equiv="refresh" content="0; url=../index.html#{a['slug']}" />
  <style>body{{margin:0;min-height:100vh;display:grid;place-items:center;background:#09090b;color:#fff;font:16px system-ui,sans-serif}}a{{color:#f87171}}</style>
</head>
<body>
  <p>Abriendo {html.escape(a['name'])}… <a href="../index.html#{a['slug']}">Ver el auto</a></p>
  <script>location.replace('../index.html#{a['slug']}');</script>
</body>
</html>
''', encoding='utf-8')

    # etiquetas de vista previa de la página principal (usa la foto del primer auto)
    og = f'''<!-- OG:INICIO (lo escribe generar_autos.py) -->
  <meta property="og:type" content="website" />
  <meta property="og:site_name" content="Seminuevos Miguel Ángel" />
  <meta property="og:title" content="Seminuevos Miguel Ángel | Autos seminuevos de confianza" />
  <meta property="og:description" content="Encuentra tu próximo auto con la confianza que mereces. Escríbenos por WhatsApp." />
  <meta property="og:url" content="{site}/" />
  <meta property="og:image" content="{site}/fotos/{autos[0]['slug']}-portada.jpg" />
  <meta name="twitter:card" content="summary_large_image" />
  <!-- OG:FIN -->'''
    src = re.sub(r'<!-- OG:INICIO.*?<!-- OG:FIN -->', lambda m: og, src, flags=re.S)
    src = re.sub(r"const SITE_URL = '.*?';", f"const SITE_URL = '{site}';", src)
    INDEX.write_text(src, encoding='utf-8')
    print(f'Listo: {len(autos)} páginas en autos/ y enlace {site} activado en index.html')


main()
