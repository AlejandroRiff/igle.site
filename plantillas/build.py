#!/usr/bin/env python3
"""IgleSite - arma el tema XML de Blogger de un cliente.
Uso: python3 build.py cliente.json [salida.xml]
Sin argumentos: genera las 4 plantillas de muestra en dist/.
"""
import json, re, sys, os, html, urllib.parse
from xml.dom import minidom

HERE = os.path.dirname(os.path.abspath(__file__))
CDN = "https://cdn.jsdelivr.net/gh/AlejandroRiff/igle.site@main/"
FAV = {"svg": CDN+"img/brand/favicon.svg", "32": CDN+"img/brand/favicon-32.png", "apple": CDN+"img/brand/apple-touch-icon.png"}

# ---- colores (p=principal, pd=oscuro, g=acento, gh=acento hover, ga=acento claro, bg=fondo, tx=texto, mu=texto suave, ln=lineas, ft=pie)
COLORES = {
 "azul":    dict(p="#14284B", pd="#0B1830", g="#C8963E", gh="#A87B2F", ga="#E8C98A", bg="#FBF8F2", tx="#1E2430", mu="#5E6573", ln="#E3DDD0", ft="#0B1830"),
 "verde":   dict(p="#4F6B57", pd="#3B5143", g="#A8863F", gh="#8B6E31", ga="#E4D3A6", bg="#F7F8F4", tx="#26302A", mu="#66706A", ln="#DFE4DA", ft="#26352B"),
 "bordo":   dict(p="#6E1F2B", pd="#561820", g="#B08A3E", gh="#9A7733", ga="#E8C98A", bg="#FBF7F2", tx="#2B2326", mu="#6B6064", ln="#E7DDD3", ft="#2B2326"),
 "gris":    dict(p="#2B2F36", pd="#1B1E23", g="#14877B", gh="#0F6C62", ga="#7FE0D4", bg="#F6F7F8", tx="#1F2328", mu="#646B73", ln="#E1E4E8", ft="#1B1E23"),
 "violeta": dict(p="#4B2E6F", pd="#35204F", g="#B8862F", gh="#9A6F25", ga="#E8C98A", bg="#FAF8FC", tx="#26202F", mu="#675F73", ln="#E5DFEC", ft="#2A1B3E"),
 "celeste": dict(p="#1F6FA8", pd="#164F78", g="#C77F1A", gh="#A66810", ga="#F2CD8B", bg="#F6FAFD", tx="#1B2733", mu="#5B6B7A", ln="#DDE7EF", ft="#123B5A"),
}
GF = "https://fonts.googleapis.com/css2?family=%s&amp;family=Inter:wght@400;500;600&amp;display=swap"
TIPOS = {
 "clasica": dict(h="'Merriweather',Georgia,serif", url=GF % "Merriweather:wght@700;900"),
 "serena":  dict(h="'Lora',Georgia,serif", url=GF % "Lora:wght@600;700"),
 "tradicion": dict(h="'Playfair Display',Georgia,serif", url=GF % "Playfair+Display:wght@600;700"),
 "moderna": dict(h="'Poppins',Arial,sans-serif", url=GF % "Poppins:wght@600;700"),
}
BODY = "Inter,Arial,sans-serif"
EXTRA = {
 "clasica": "",
 "tradicion": "",
 "serena": ".btn{border-radius:14px}.card{border-radius:18px;border-top-width:3px}.photo{border-radius:20px}.hd{border-bottom:0}.hero{border-bottom:0}.band{border-top:0}.hor,table.hor{border-radius:16px}.an-card,.yt-card{border-radius:18px}",
 "moderna": ".hd{border-bottom:0;text-align:left}.brand{text-align:left}.nav{justify-content:flex-start}.hero{text-align:left;border-bottom:0;padding:120px 22px}.hero h1,.hero p{margin-left:max(22px,calc(50% - 500px));margin-right:auto}.hero p{max-width:600px}.btn{border-radius:6px}.hero .btn{margin-left:max(22px,calc(50% - 500px))}.card{border-radius:6px;border-top-width:3px}.photo{border-radius:6px}.band{border-top:0;text-align:left}.band>*{margin-left:max(22px,calc(50% - 500px))}.sec-t,.sec-s{text-align:left;margin-left:0}.page-h{text-align:left}.page-h>*{max-width:956px;margin-left:auto;margin-right:auto}.an-card,.yt-card,table.hor{border-radius:6px}@media(max-width:820px){.hero h1,.hero p,.hero .btn,.band>*{margin-left:0}}",
}
PRESETS = {  # plantilla -> (color, tipografia)
 "clasica": ("azul", "clasica"), "serena": ("verde", "serena"),
 "tradicion": ("bordo", "tradicion"), "moderna": ("gris", "moderna"),
}
CRUZ = "<svg height='40' viewBox='0 0 24 24' width='40'><path d='M10 2h4v6h6v4h-6v10h-4V12H4V8h6z' fill='currentColor'/></svg>"

def e(s):  # texto/atributo seguro en XML de Blogger
    return html.escape(str(s), quote=True).replace("&#x27;", "&#39;")

def rgb(h):
    h = h.lstrip("#"); return ",".join(str(int(h[i:i+2], 16)) for i in (0, 2, 4))

def paras(x):
    if isinstance(x, str): x = [p for p in re.split(r"\n\s*\n|\n", x) if p.strip()]
    return "".join("<p>%s</p>" % e(p.strip()) for p in x)

def strip_block(xml, tag, keep):
    pat = re.compile(r"<!--\[%s\]-->(.*?)<!--\[/%s\]-->" % (tag, tag), re.S)
    return pat.sub(lambda m: m.group(1) if keep else "", xml)

CREEMOS_DEF = [
 ("La Biblia", "es la Palabra de Dios, nuestra única regla de fe y conducta."),
 ("Dios", "un solo Dios verdadero en tres personas: Padre, Hijo y Espíritu Santo."),
 ("Salvación", "es por gracia, mediante la fe en Jesucristo, quien murió y resucitó por nosotros."),
 ("La iglesia", "la comunidad de los creyentes que se reúne para adorar, aprender y servir."),
]

def build(c, plantilla=None):
    plantilla = plantilla or c.get("plantilla", "tradicion")
    col, tip = PRESETS[plantilla]
    col = c.get("color") or col; tip_k = c.get("tipografia") or tip
    P = COLORES[col]; T = TIPOS[tip_k]
    nombre = c["nombre"]; ciudad = c.get("ciudad", ""); dire = c.get("direccion", "")
    m = re.match(r"^(Iglesia(?:\s+(?:Evangélica|Bautista|Cristiana|Presbiteriana|Pentecostal|Reformada|Bíblica|Metodista|Menonita|Luterana|Anglicana))?)\s+(.+)$", nombre)
    small, brand = (m.group(1), m.group(2)) if m else ("", nombre)
    frase = c.get("frase") or "Una iglesia para toda la familia, donde se predica la Palabra de Dios. Te esperamos."
    hor = c.get("horarios", [])
    mapsq = urllib.parse.quote_plus(", ".join(x for x in (dire, ciudad) if x))
    maps = c.get("maps") or ("https://www.google.com/maps/search/?api=1&amp;query=" + mapsq)
    tel = re.sub(r"\D", "", c.get("telefono", ""))
    tel_vis = c.get("telefono_visible") or (("+" + tel) if tel else "")
    web = c.get("email", "")
    quienes = c.get("quienes") or "Somos una congregación que se reúne cada semana para adorar a Dios, escuchar su Palabra y crecer juntos en la fe."
    q1 = quienes if isinstance(quienes, str) else " ".join(quienes)
    q1 = re.split(r"\n", q1.strip())[0]
    if len(q1) > 220: q1 = q1[:217].rsplit(" ", 1)[0] + "…"
    desc = (frase if len(frase) <= 155 else frase[:152] + "…") + ((" " + ciudad) if ciudad and ciudad not in frase and len(frase) < 130 else "")

    # reuniones (portada)
    home_r = "".join("<p><b>%s %s</b><br/>%s</p>" % (e(h["dia"]), e(h["hora"]), e(h["titulo"])) for h in hor[:3]) or "<p>Consulta nuestros horarios.</p>"
    rows = "\n".join("<tr><td>%s<small>%s</small></td><td>%s%s</td></tr>" % (e(h["dia"]), e(h["hora"]), e(h["titulo"]), ("<small>%s</small>" % e(h["detalle"])) if h.get("detalle") else "") for h in hor) or "<tr><td>Consúltanos</td><td>Próximamente</td></tr>"

    # nosotros
    foto = c.get("foto_url")
    if foto:
        top = "<div class='two'><img alt='%s' class='photo' src='%s'/><div><h2>Nuestra iglesia</h2>%s</div></div>" % (e(nombre), e(foto), paras(quienes))
    else:
        top = "<div class='one'><h2>Nuestra iglesia</h2>%s</div>" % paras(quienes)
    creemos = c.get("creemos") or CREEMOS_DEF
    li = "".join("<li><b>%s:</b> %s</li>" % (e(a), e(b)) for a, b in [(x["titulo"], x["texto"]) if isinstance(x, dict) else x for x in creemos])
    creemos_html = "<div class='card' style='margin-top:34px'><h3>Lo que creemos</h3><ul class='list'>%s</ul></div>" % li
    pastores = c.get("pastores")
    pastores_html = "<div class='card' style='margin-top:20px'><h3>Nuestros pastores</h3>%s</div>" % paras(pastores) if pastores else ""

    # contacto
    lis = []
    if dire: lis.append("<li><b>Dirección:</b> %s</li>" % e(dire + (", " + ciudad if ciudad else "")))
    if tel: lis.append("<li><b>Teléfono / WhatsApp:</b> <a href='https://wa.me/%s' rel='noopener' target='_blank'>%s</a></li>" % (tel, e(tel_vis)))
    if web: lis.append("<li><b>Correo:</b> <a href='mailto:%s'>%s</a></li>" % (e(web), e(web)))
    soc = []
    for k, lab in (("facebook", "Facebook"), ("instagram", "Instagram"), ("youtube_url", "YouTube"), ("tiktok", "TikTok"), ("x", "X")):
        if c.get(k): soc.append("<a href='%s' rel='noopener' target='_blank'>%s</a>" % (e(c[k]), lab))

    # SEO schema.org
    ld = {"@context": "https://schema.org", "@type": "Church", "name": nombre, "description": desc}
    addr = {"@type": "PostalAddress", "addressCountry": c.get("pais", "AR")}
    if dire: addr["streetAddress"] = dire
    if ciudad: addr["addressLocality"] = ciudad
    ld["address"] = addr
    if tel_vis: ld["telephone"] = tel_vis
    if web: ld["email"] = web
    same = [c[k] for k in ("facebook", "instagram", "youtube_url", "tiktok", "x") if c.get(k)]
    if same: ld["sameAs"] = same
    ldjson = json.dumps(ld, ensure_ascii=False, separators=(",", ":")).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

    hero = c.get("hero_url")
    herobg = ("linear-gradient(rgba(%s,.72),rgba(%s,.72)),url(%s) center 40%%/cover" % (rgb(P["pd"]), rgb(P["pd"]), hero)) if hero else "linear-gradient(135deg,%s,%s)" % (P["pd"], P["p"])
    logo = c.get("logo_url")
    logo_html = ("<img alt='%s' src='%s'/>" % (e(nombre), e(logo))) if logo else CRUZ
    fav = dict(FAV)
    if c.get("favicon_32"): fav["32"] = c["favicon_32"]; fav["apple"] = c.get("favicon_apple", c["favicon_32"]); fav["svg"] = c["favicon_32"]

    yt_ch = c.get("youtube_canal_id", "")
    videos = bool(yt_ch)
    anuncios = bool(c.get("anuncios"))

    vals = dict(
        DESC=e(desc), P=P["p"], PD=P["pd"], G=P["g"], GH=P["gh"], GA=P["ga"], BG=P["bg"], TX=P["tx"], MU=P["mu"], LN=P["ln"], FT=P["ft"],
        FONT_H=T["h"], FONT_B=BODY, FONTS_URL=T["url"], EXTRA_CSS=EXTRA[plantilla], LDJSON=ldjson,
        FAV_SVG=fav["svg"], FAV_32=fav["32"], FAV_APPLE=fav["apple"], HERO_BG=herobg, LOGO_HTML=logo_html,
        BRAND_SMALL=("<small>%s</small>" % e(small)) if small else "", BRAND_NAME=e(brand), NOMBRE=e(nombre), FRASE=e(frase),
        SUBTITULO=e(c.get("subtitulo") or "Somos una congregación sencilla que se reúne para adorar a Dios, estudiar la Biblia y servirnos unos a otros."),
        HOME_REUNIONES=home_r, HOME_QUIENES=e(q1),
        DIRECCION_LINEAS=(e(dire) + ("<br/>" + e(ciudad) if ciudad else "")) if dire else e(ciudad), DIRECCION_INLINE=e(", ".join(x for x in (dire, ciudad) if x)),
        MAPS=maps, BAND_TEXT=e(c.get("band") or ("Si buscas una iglesia en %s, ven a visitarnos. No necesitas avisar: serás recibido con alegría." % ciudad if ciudad else "Ven a visitarnos. No necesitas avisar: serás recibido con alegría.")),
        NOSOTROS_TOP=top, CREEMOS_HTML=creemos_html, PASTORES_HTML=pastores_html, HORARIOS_ROWS=rows,
        CONTACTO_LI="".join(lis), SOCIAL="".join(soc),
        COMO_LLEGAR=e(c.get("como_llegar") or "Ábrelo en Google Maps para ver la ruta desde donde estás."),
        YT_CHANNEL=e(yt_ch), YT_URL=e(c.get("youtube_url") or ("https://www.youtube.com/channel/" + yt_ch)), SLUG=e(c.get("slug", "")),
    )
    xml = open(os.path.join(HERE, "base.xml"), encoding="utf-8").read()
    xml = strip_block(xml, "VIDEOS", videos); xml = strip_block(xml, "ANUNCIOS", anuncios)
    xml = re.sub(r"@@([A-Z_0-9]+)@@", lambda m: vals[m.group(1)], xml)
    left = re.findall(r"@@[A-Z_0-9]+@@", xml)
    assert not left, left
    minidom.parseString(xml.encode("utf-8"))  # debe ser XML bien formado
    return xml

DEMO = dict(slug="demo", nombre="Iglesia Evangélica Ejemplo", ciudad="Tu ciudad", direccion="Calle Ejemplo 123",
  telefono="5491155550000", telefono_visible="+54 9 11 5555-0000", email="contacto@ejemplo.org",
  frase="Una iglesia para toda la familia, donde se predica la Palabra de Dios. Te esperamos este domingo.",
  quienes=["Somos una congregación que se reúne cada semana para adorar a Dios, escuchar su Palabra y crecer juntos en la fe.", "Nuestro deseo es que todo el que llegue se sienta recibido."],
  horarios=[dict(dia="Domingo", hora="10:00", titulo="Culto de adoración y predicación", detalle="Con escuela dominical"), dict(dia="Miércoles", hora="19:30", titulo="Estudio bíblico"), dict(dia="Sábado", hora="18:00", titulo="Reunión de jóvenes")],
  facebook="https://www.facebook.com/", instagram="https://www.instagram.com/", youtube_url="https://www.youtube.com/", youtube_canal_id="UCK76aRorEM8KJKr5Uspr5-w", anuncios=True, pastores="Aquí se presenta al pastor y a su familia.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        c = json.load(open(sys.argv[1], encoding="utf-8"))
        out = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(sys.argv[1])[0] + "-tema.xml"
        open(out, "w", encoding="utf-8").write(build(c)); print(out)
    else:
        os.makedirs(os.path.join(HERE, "dist"), exist_ok=True)
        for k in PRESETS:
            p = os.path.join(HERE, "dist", "plantilla-%s.xml" % k)
            open(p, "w", encoding="utf-8").write(build(DEMO, k)); print(p)
