"""Responsive regression captures and the no-clutter density measurement.

Density is characters of visible text per 1000px of page height — the same
measure used for the 2b7966c and 665fcb3 candidates, so the three are directly
comparable. Viewport is fixed so no capture can exceed 2000px in either
dimension.
"""
import json
import os
from playwright.sync_api import sync_playwright

BASE = 'http://127.0.0.1:4880'
OUT = '/var/lib/freelancer/projects/40470800/candidate-evidence-19aug'
os.makedirs(OUT, exist_ok=True)

PAGES = [
    ('home', '/'),
    ('home-level-A1', '/?level=A1'),
    ('adult-index', '/app/adult/'),
    ('adult-dashboard', '/app/adult/dashboard/'),
    ('parents-dashboard', '/app/parents/dashboard/'),
    ('studio-governance', '/app/studio/governance/'),
    ('schools-roster', '/app/schools/roster/'),
    ('studio-credits', '/app/studio/credits/'),
    ('lesson-interactions', '/preview/lesson-interactions/'),
]

VIEWPORTS = [('desktop', 1280, 800), ('tablet', 900, 800), ('mobile', 390, 780)]

DENSITY = """
() => {
  const h = Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);
  const t = (document.body.innerText || '').replace(/\\s+/g, ' ').trim();
  return { chars: t.length, height: h, per1000: Math.round(t.length / (h / 1000)) };
}
"""

density = {}
with sync_playwright() as p:
    b = p.chromium.launch()
    for vname, w, hgt in VIEWPORTS:
        pg = b.new_page(viewport={'width': w, 'height': hgt})
        for name, path in PAGES:
            pg.goto(BASE + path, wait_until='domcontentloaded', timeout=45000)
            pg.wait_for_timeout(4200)
            pg.screenshot(path=f'{OUT}/{vname}__{name}.png')
            if vname == 'desktop':
                density[name] = pg.evaluate(DENSITY)
                d = density[name]
                print(f'{name:22} {d["per1000"]:>5} chars/1000px   (page {d["height"]}px)')
        pg.close()
    b.close()

json.dump(density, open(f'{OUT}/density.json', 'w'), indent=2)
print('\ncaptures written to', OUT)
