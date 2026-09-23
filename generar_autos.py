#!/usr/bin/env python3
"""
Genera las mini-páginas de cada auto (autos/<auto>.html) con las etiquetas
que WhatsApp usa para mostrar la FOTO junto al enlace, y activa el enlace
del auto dentro de los mensajes de WhatsApp de index.html.

Uso (después de publicar la página y saber su enlace):
    python3 generar_autos.py https://tu-sitio.netlify.app

Vuelve a ejecutarlo cada vez que cambies un auto, precio o foto en index.html.
"""
import datetime
import html
import json
import pathlib
import re
import sys

AQUI = pathlib.Path(__file__).resolve().parent
INDEX = AQUI / 'index.html'

# Datos del negocio para Google (datos estructurados). Cambia aquí si algo cambia.
NEGOCIO = {
    'name': 'Seminuevos Miguel Ángel',
    'telephone': '+52 33 1072 1299',
    'facebook': 'https://www.facebook.com/profile.php?id=100083828928209',
    # Horario: lunes a viernes 9:00-19:00, sábados 9:00-14:00
    'horario': [
        {'@type': 'OpeningHoursSpecification',
         'dayOfWeek': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
         'opens': '09:00', 'closes': '19:00'},
        {'@type': 'OpeningHoursSpecification',
         'dayOfWeek': 'Saturday', 'opens': '09:00', 'closes': '14:00'},
    ],
    # Cuando decidas publicar la dirección, agrégala aquí como:
    # 'address': {'@type': 'PostalAddress', 'streetAddress': '...', 'addressLocality': '...',
    #             'addressRegion': 'Jalisco', 'addressCountry': 'MX'}
}


def ld_json(obj):
    """JSON-LD seguro para incrustar en <script>."""
    return json.dumps(obj, ensure_ascii=False, indent=2).replace('</', '<\\/')


def main():
    # Solo se acepta un enlace normal (http/https + dominio + ruta opcional): se inserta dentro del código.
    if len(sys.argv) != 2 or not re.fullmatch(r'https?://[A-Za-z0-9.-]+(:\d+)?(/[A-Za-z0-9._~/-]*)?', sys.argv[1]):
        sys.exit('Uso: python3 generar_autos.py https://tu-sitio.pages.dev')
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
            brand=re.search(r'data-brand="([^"]*)"', art).group(1),
            price_num=int(re.search(r'data-price="(\d+)"', art).group(1)),
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
        # Datos estructurados del auto (Google los usa para entender qué se vende y a qué precio)
        coche = {
            '@context': 'https://schema.org', '@type': 'Car',
            'name': f"{a['name']} {a['year']}",
            'brand': {'@type': 'Brand', 'name': a['brand']},
            'image': f"{site}/fotos/{a['slug']}-portada.jpg",
            'url': f"{site}/autos/{a['slug']}",
            'vehicleModelDate': a['year'],
            'itemCondition': 'https://schema.org/UsedCondition',
            'vehicleTransmission': a['trans'],
            'offers': {'@type': 'Offer', 'price': a['price_num'], 'priceCurrency': 'MXN',
                       'availability': 'https://schema.org/InStock',
                       'url': f"{site}/autos/{a['slug']}"},
        }
        km_num = re.sub(r'\D', '', a['km'])
        if km_num:
            coche['mileageFromOdometer'] = {'@type': 'QuantitativeValue', 'value': int(km_num), 'unitCode': 'KMT'}
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
  <meta property="og:url" content="{site}/autos/{a['slug']}" />
  <meta property="og:image" content="{site}/fotos/{a['slug']}-portada.jpg" />
  <meta property="og:image:width" content="1000" />
  <meta property="og:image:height" content="750" />
  <meta name="twitter:card" content="summary_large_image" />
  <script type="application/ld+json">
{ld_json(coche)}
  </script>
  <meta http-equiv="refresh" content="0; url=../index.html#{a['slug']}" />
  <style>body{{margin:0;min-height:100vh;display:grid;place-items:center;background:#09090b;color:#fff;font:16px system-ui,sans-serif}}a{{color:#f87171}}</style>
</head>
<body>
  <p>Abriendo {html.escape(a['name'])}… <a href="../index.html#{a['slug']}">Ver el auto</a></p>
  <script>location.replace('../index.html#{a['slug']}');</script>
</body>
</html>
''', encoding='utf-8')

    # datos estructurados del negocio (sin dirección hasta que decidas publicarla)
    negocio = {
        '@context': 'https://schema.org', '@type': 'AutoDealer',
        'name': NEGOCIO['name'], 'url': f'{site}/', 'image': f'{site}/img/logo.png',
        'telephone': NEGOCIO['telephone'], 'sameAs': [NEGOCIO['facebook']],
        'openingHoursSpecification': NEGOCIO['horario'],
    }
    if 'address' in NEGOCIO:
        negocio['address'] = NEGOCIO['address']

    # etiquetas de vista previa + canónica + datos estructurados de la página principal
    og = f'''<!-- OG:INICIO (lo escribe generar_autos.py) -->
  <link rel="canonical" href="{site}/" />
  <meta property="og:type" content="website" />
  <meta property="og:site_name" content="Seminuevos Miguel Ángel" />
  <meta property="og:title" content="Seminuevos Miguel Ángel | Autos seminuevos de confianza" />
  <meta property="og:description" content="Catálogo de autos seminuevos con fotos, precio y contacto directo por WhatsApp." />
  <meta property="og:url" content="{site}/" />
  <meta property="og:image" content="{site}/fotos/{autos[0]['slug']}-portada.jpg" />
  <meta name="twitter:card" content="summary_large_image" />
  <script type="application/ld+json">
{ld_json(negocio)}
  </script>
  <!-- OG:FIN -->'''
    src = re.sub(r'<!-- OG:INICIO.*?<!-- OG:FIN -->', lambda m: og, src, flags=re.S)
    src = re.sub(r"const SITE_URL = '.*?';", f"const SITE_URL = '{site}';", src)
    INDEX.write_text(src, encoding='utf-8')

    # robots.txt y sitemap.xml (las páginas de cada auto solo redirigen, así que no se listan)
    (AQUI / 'robots.txt').write_text(f'User-agent: *\nAllow: /\n\nSitemap: {site}/sitemap.xml\n', encoding='utf-8')
    hoy = datetime.date.today().isoformat()
    (AQUI / 'sitemap.xml').write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f'  <url><loc>{site}/</loc><lastmod>{hoy}</lastmod></url>\n'
        '</urlset>\n', encoding='utf-8')
    print(f'Listo: {len(autos)} páginas en autos/, robots.txt, sitemap.xml y enlace {site} activado en index.html')


main()
