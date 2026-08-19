"""The settled-state PiP acceptance test, 19 August 2026.

The rule being tested is the revised one: PiP may float over anything while the
learner is actively scrolling, and the acceptance condition is what happens once
the page is still. So every measurement here is taken after scrolling has
stopped and PiP has been given time to settle — never during motion.

For each surface and width the page is walked in viewport steps. At each stop
the script waits past PiP's idle threshold, then compares PiP's rectangle
against every control a learner needs to be able to press: buttons, answer
options, form inputs, links, and anything with a button/link/tab role. A card
that is itself a link counts, because that link is the card's Open action.

A stop FAILS if any such control is overlapped by more than 2px on both axes
once the page is still. Nothing is excused as "only a card".
"""
import json
import sys
from playwright.sync_api import sync_playwright

BASE = 'http://127.0.0.1:4880'

PAGES = [
    ('Access Panel home', '/'),
    ('Access Panel, level chosen', '/?level=A1'),
    ('Adult mini-app index', '/app/adult/'),
    ('Adult dashboard', '/app/adult/dashboard/'),
    ('Adult learner (gated)', '/app/adult/learner/'),
    ('Parent dashboard', '/app/parents/dashboard/'),
    ('School roster', '/app/schools/roster/'),
    ('School admin overview', '/app/schools/dashboard/'),
    ('Studio AI governance', '/app/studio/governance/'),
    ('Studio AI Credits', '/app/studio/credits/'),
    ('Lesson Player / Reading', '/preview/lesson-interactions/'),
]

VIEWPORTS = [('desktop', 1280, 800), ('tablet', 900, 800), ('mobile', 390, 780)]

PROBE = """
() => {
  const root = document.querySelector('.ielps-pip-agent');
  const pip = document.querySelector('.ielps-pip-launcher, .ielps-pip-panel');
  if (!pip) return null;
  const p = pip.getBoundingClientRect();
  const sel = 'a[href],button,input,select,textarea,[role="button"],[role="link"],[role="tab"],[role="checkbox"],[role="radio"]';
  const reachable = (e) => {
    if (e.getAttribute('aria-hidden') === 'true') return false;
    if (e.disabled) return false;
    const c = getComputedStyle(e);
    if (c.visibility === 'hidden' || c.display === 'none') return false;
    if (parseFloat(c.opacity) === 0 || c.pointerEvents === 'none') return false;
    const r = e.getBoundingClientRect();
    return r.width > 0 && r.height > 0 && r.bottom > 0 && r.top < innerHeight
        && r.right > 0 && r.left < innerWidth;
  };
  const hits = [];
  document.querySelectorAll(sel).forEach((e) => {
    if (root && root.contains(e)) return;
    if (!reachable(e)) return;
    const r = e.getBoundingClientRect();
    const ox = Math.min(p.right, r.right) - Math.max(p.left, r.left);
    const oy = Math.min(p.bottom, r.bottom) - Math.max(p.top, r.top);
    if (ox <= 2 || oy <= 2) return;
    hits.push({
      text: (e.innerText || e.getAttribute('aria-label') || e.tagName).trim().slice(0, 48),
      tag: e.tagName.toLowerCase(),
      overlapX: Math.round(ox), overlapY: Math.round(oy),
    });
  });
  return {
    pip: { w: Math.round(p.width), h: Math.round(p.height),
           x: Math.round(p.left), y: Math.round(p.top) },
    placement: root ? root.dataset.pipPlacement : null,
    motion: root ? root.dataset.pipMotion : null,
    obstructed: root ? root.dataset.pipObstructed === 'true' : false,
    controls: document.querySelectorAll(sel).length,
    hits,
  };
}
"""

report = []
fail_stops = 0
total_stops = 0

with sync_playwright() as pw:
    browser = pw.chromium.launch()
    for vname, w, h in VIEWPORTS:
        page = browser.new_page(viewport={'width': w, 'height': h})
        for label, path in PAGES:
            page.goto(BASE + path, wait_until='domcontentloaded', timeout=45000)
            page.wait_for_timeout(3500)

            steps = page.evaluate(
                '() => Math.max(1, Math.min(10, Math.ceil(document.body.scrollHeight / innerHeight)))'
            )
            stops = []
            for s in range(steps):
                page.evaluate(f'() => window.scrollTo(0, {s} * innerHeight * 0.9)')
                # Past the 180ms idle threshold, plus the settle transition.
                page.wait_for_timeout(900)
                out = page.evaluate(PROBE)
                if out is None:
                    continue
                total_stops += 1
                if out['hits']:
                    fail_stops += 1
                stops.append({'stop': s, **out})

            worst = [s for s in stops if s['hits']]
            moved = [s for s in stops if s['placement'] == 'cleared']
            report.append({
                'viewport': vname, 'page': label, 'path': path,
                'stops': len(stops), 'stops_with_blocked_controls': len(worst),
                'stops_where_pip_moved': len(moved),
                'obstructed_stops': len([s for s in stops if s['obstructed']]),
                'detail': stops,
            })
            flag = 'FAIL' if worst else 'pass'
            note = ''
            if worst:
                note = f"  <- {worst[0]['hits'][0]['text'][:34]!r}"
            print(f"{flag} {vname:8} {label:28} stops {len(stops):2}  "
                  f"moved {len(moved):2}  blocked {len(worst)}{note}")
        page.close()
    browser.close()

print(f"\nstops measured at rest: {total_stops}")
print(f"stops where a control was blocked at rest: {fail_stops}")
json.dump(report, open('/var/lib/freelancer/projects/40470800/pip-settled-19aug.json', 'w'), indent=2)
sys.exit(1 if fail_stops else 0)
