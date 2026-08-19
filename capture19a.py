"""Evidence screenshots for the 19 August correction pass.

Every shot is taken after the page has stopped moving and PiP has settled,
because the settled state is what the rule is about. Viewport-sized only.
"""
import os
from playwright.sync_api import sync_playwright

OUT = '/var/lib/freelancer/projects/40470800/candidate-evidence-19aug'
os.makedirs(OUT, exist_ok=True)

BASE = 'http://127.0.0.1:4880'

# name, width, height, path, scroll fraction of the full page height
SHOTS = [
    ('reading-answers-mobile-settled', 390, 780, '/preview/lesson-interactions/', 0.42),
    ('reading-answers-mobile-bottom', 390, 780, '/preview/lesson-interactions/', 1.0),
    ('adult-index-mobile-tucked', 390, 780, '/app/adult/', 1.0),
    ('adult-index-tablet-tucked', 900, 800, '/app/adult/', 1.0),
    ('adult-index-desktop-cleared', 1280, 800, '/app/adult/', 1.0),
    ('studio-governance-desktop', 1280, 800, '/app/studio/governance/', 0.0),
    ('studio-governance-mobile', 390, 780, '/app/studio/governance/', 0.0),
    ('studio-credits-desktop', 1280, 800, '/app/studio/credits/', 0.0),
    ('studio-credits-mobile', 390, 780, '/app/studio/credits/', 0.0),
    ('access-panel-home-desktop', 1280, 800, '/', 0.0),
    ('access-panel-level-band-desktop', 1280, 800, '/?level=A1', 0.0),
    ('schools-card-parameter-required', 1280, 800, '/', 0.55),
]

with sync_playwright() as pw:
    b = pw.chromium.launch()
    for name, w, h, path, frac in SHOTS:
        pg = b.new_page(viewport={'width': w, 'height': h})
        pg.goto(BASE + path, wait_until='domcontentloaded', timeout=45000)
        pg.wait_for_timeout(3200)
        pg.evaluate(
            f'() => window.scrollTo(0, {frac} * Math.max(0, document.body.scrollHeight - innerHeight))'
        )
        pg.wait_for_timeout(1400)  # past PiP's idle threshold and its settle
        pg.screenshot(path=f'{OUT}/{name}.png')
        print('captured', name, f'{w}x{h}')
        pg.close()
    b.close()
