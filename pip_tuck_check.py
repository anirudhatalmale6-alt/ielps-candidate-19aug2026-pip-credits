"""Two things the tuck must not break.

A fixed element parked partly past the right edge could add horizontal scroll
to the page, which would be a worse bug than the one it fixes. And a handle a
learner cannot press is not a handle. Both are checked here rather than assumed:
the page is measured for overflow, then PiP is clicked at the visible sliver and
the panel must actually open.
"""
from playwright.sync_api import sync_playwright

CASES = [
    ('mobile', 390, 780, '/app/adult/'),
    ('tablet', 900, 800, '/app/adult/'),
    ('mobile', 390, 780, '/preview/lesson-interactions/'),
]

STATE = """
() => {
  const root = document.querySelector('.ielps-pip-agent');
  const el = document.querySelector('.ielps-pip-launcher');
  const r = el ? el.getBoundingClientRect() : null;
  return {
    placement: root?.dataset.pipPlacement,
    rect: r ? { l: Math.round(r.left), t: Math.round(r.top),
                r: Math.round(r.right), b: Math.round(r.bottom) } : null,
    innerWidth,
    docScrollW: document.documentElement.scrollWidth,
    bodyScrollW: document.body.scrollWidth,
  };
}
"""

with sync_playwright() as pw:
    b = pw.chromium.launch()
    for name, w, h, path in CASES:
        pg = b.new_page(viewport={'width': w, 'height': h})
        pg.goto('http://127.0.0.1:4880' + path, wait_until='domcontentloaded')
        pg.wait_for_timeout(3000)
        # Scroll to the position that forced the tuck, then stop and settle.
        pg.evaluate('() => window.scrollTo(0, document.body.scrollHeight)')
        pg.wait_for_timeout(1200)
        s = pg.evaluate(STATE)

        overflow = max(s['docScrollW'], s['bodyScrollW']) - s['innerWidth']
        visible = s['innerWidth'] - s['rect']['l'] if s['rect'] else 0

        # Press the part still on screen and confirm the panel opens.
        opened = False
        if s['rect']:
            x = min(s['rect']['r'], s['innerWidth']) - 4
            y = (s['rect']['t'] + s['rect']['b']) // 2
            pg.mouse.click(x, y)
            pg.wait_for_timeout(900)
            opened = pg.evaluate("() => Boolean(document.querySelector('.ielps-pip-panel'))")

        print(f"{name:7} {path:32} placement={s['placement']:8} "
              f"visible={visible:3}px  h-overflow={overflow:3}px  opens={opened}")
        pg.close()
    b.close()
