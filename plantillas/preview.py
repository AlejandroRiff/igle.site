import re, sys, os, asyncio
from playwright.async_api import async_playwright
PAGES = ["home","Nosotros","Horarios","Contacto","Últimos videos","Anuncios"]
def render(xml, page):
    css = re.search(r"<b:skin><!\[CDATA\[(.*?)\]\]></b:skin>", xml, re.S).group(1)
    fonts = re.search(r"<link href='(https://fonts[^']+)'", xml).group(1).replace("&amp;","&")
    hd = re.search(r"<header class='hd'>(.*?)</header>", xml, re.S).group(1).replace("expr:href='data:blog.homepageUrl'","href='/'")
    main = re.search(r"<main>(.*?)</main>", xml, re.S).group(1)
    parts = re.split(r"<b:elseif cond='[^']*pageName == &quot;([^&]*)&quot;'/>", main)
    first = parts[0].split("<b:if cond='data:view.isHomepage'>")[1]
    branches = {"home": first}
    for i in range(1, len(parts), 2): branches[parts[i]] = parts[i+1]
    body = branches[page].replace("</b:if>","")
    ft = re.search(r"<footer class='ft'>.*?</footer>", xml, re.S).group(0)
    return f"<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'><link rel=stylesheet href='{fonts}'><style>{css}</style><header class=hd>{hd}</header><main>{body}</main>{ft}"
async def main(files):
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        for f in files:
            xml = open(f, encoding="utf-8").read(); name = os.path.basename(f)[:-4]
            ctx = await b.new_context(viewport={"width":390,"height":844}, device_scale_factor=1)
            pg = await ctx.new_page()
            for page in PAGES:
                if page not in ("home",) and f"/p/" and False: pass
                try: html = render(xml, page)
                except KeyError: print(name, page, "(no existe)"); continue
                await pg.set_content(html); await pg.wait_for_timeout(300)
                sw = await pg.evaluate("document.documentElement.scrollWidth")
                print(name, page, "scrollWidth", sw, "OK" if sw<=390 else "DESBORDA")
                if page in ("home","Nosotros"): await pg.screenshot(path=f"/tmp/prev-{name}-{page}.png", full_page=True)
            await ctx.close()
        await b.close()
asyncio.run(main(sys.argv[1:]))
