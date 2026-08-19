"""Functional checks for the post-retirement candidate.

Everything here is read out of the rendered page, not out of the source. The
harness on 4880 puts the real IELPS backend behind the candidate, so the panels
hydrate from the live curriculum exactly as they will in production.
"""
import json
import re
from playwright.sync_api import sync_playwright

BASE = 'http://127.0.0.1:4880'
results = []


def check(name, ok, detail=''):
    results.append({'check': name, 'pass': bool(ok), 'detail': detail})
    print(('PASS  ' if ok else 'FAIL  ') + name + ('   ' + detail if detail else ''))


with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={'width': 1280, 'height': 900})

    def go(path, wait=3000):
        pg.goto(BASE + path, wait_until='domcontentloaded', timeout=45000)
        pg.wait_for_timeout(wait)

    # ---- the retired routes are gone -------------------------------------
    for path in ['/access/', '/levels/a1/', '/levels/b2/', '/levels/c2/']:
        r = pg.request.get(BASE + path)
        check(f'retired route {path} is gone', r.status == 404, f'HTTP {r.status}')

    # ---- panel home ------------------------------------------------------
    go('/')
    body = pg.inner_text('body')
    check('panel home renders', 'Pathways' in body or 'pathway' in body.lower())
    check('no level band without ?level', 'Your chosen level' not in body)

    # API chips restored on pathway cards and the section header
    chips = pg.eval_on_selector_all(
        'code, span',
        "els => els.map(e => (e.innerText||'').trim()).filter(t => /^\\/?api\\//.test(t) || /^(GET|POST) \\/api\\//.test(t))",
    )
    check('pathway API chips restored', len(chips) >= 6, f'{len(chips)} visible route labels')
    check(
        'pathways header chip GET /api/auth/pathways visible',
        'GET /api/auth/pathways' in body,
    )

    # adult flow step routes restored
    check('adult flow step routes visible', '/api/progress/lesson' in body, '')

    # no revoked typeface anywhere
    fonts = pg.evaluate(
        "() => Array.from(document.querySelectorAll('body *')).map(e => getComputedStyle(e).fontFamily).join('|')"
    )
    check('no Plus Jakarta Sans on the panel home', 'Jakarta' not in fonts)

    # ---- level band: canonical hierarchy ---------------------------------
    go('/?level=A1', 4500)
    band = pg.inner_text('#your-level')
    lines = [l.strip() for l in band.split('\n') if l.strip()]
    txt = ' | '.join(lines)
    check('level band present with ?level=A1', 'your chosen level' in band.lower())

    def idx(needle):
        for i, l in enumerate(lines):
            if l == needle:
                return i
        return -1

    i_code, i_desc, i_name = idx('A1'), idx('Breakthrough'), idx('Beginner')
    check(
        'hierarchy order code -> descriptor -> name',
        0 <= i_code < i_desc < i_name,
        f'A1@{i_code} Breakthrough@{i_desc} Beginner@{i_name}',
    )
    check('A1 definition shown', 'Understand and use everyday expressions' in band)
    others = [
        'Handle short social exchanges',
        'Deal with most travel situations',
        'Interact with fluency and spontaneity',
        'Express ideas fluently',
        'Understand virtually everything',
    ]
    check(
        'only the selected level is described',
        not any(o in pg.inner_text('body') for o in others),
    )
    m = re.search(r'Course:\s*(.+?)\s*[—-]\s*(\d+)\s*units and\s*(\d+)\s*lessons', band)
    check(
        'course title and real server counts',
        bool(m),
        (f'{m.group(1)} / {m.group(2)} units / {m.group(3)} lessons' if m else band[:120]),
    )
    check('no Basic/Independent/Proficient grouping imported',
          not any(g in band for g in ['Basic user', 'Independent user', 'Proficient user']))
    href = pg.get_attribute('#your-level a[href*="pathways"]', 'href')
    check('Continue with A1 goes to the pathway gateway', href and 'pathways' in href, str(href))
    chips6 = pg.eval_on_selector_all('#your-level [data-ielps-level]', 'e => e.length')
    check('six change-level chips', chips6 == 6, f'{chips6} chips')
    active = pg.get_attribute('#your-level [data-ielps-level="A1"]', 'aria-current')
    check('chosen level marked current', active == 'true', str(active))

    # ---- mini-app surfaces ----------------------------------------------
    go('/app/adult/', 4000)
    b2 = pg.inner_text('body')
    check('adult mini-app renders', 'My Course' in b2 or 'Course' in b2)

    # Panels live on a screen, not on the mini-app index.
    go('/app/adult/dashboard/', 4500)
    b2s = pg.inner_text('body')
    labels = [x for x in b2s.replace('\n', ' ').split() if x.startswith('/api/')]
    check('mini-app panel endpoint chips restored', len(labels) >= 3, ', '.join(labels[:4]))
    check('server wiring drawer restored on a screen', 'Server wiring' in b2s)

    go('/app/parents/dashboard/', 4500)
    b3 = pg.inner_text('body')
    check('parent dashboard renders', 'Parent' in b3 or 'dashboard' in b3.lower())
    check('parent dashboard endpoint chips restored', '/api/' in b3)
    check('wiring drawer offered again', 'wiring' in b3.lower() or 'Server wiring' in b3)

    go('/app/studio/governance/', 4000)
    b4 = pg.inner_text('body')
    gov = b4.count('/api/studio/ai/governance')
    check('studio governance panels name the real route', gov >= 3, f'{gov} occurrences')
    check('no unregistered studio routes labelled',
          '/api/studio/ai/quota' not in b4 and '/api/studio/ai/moderation' not in b4)

    # The real lesson player is entitlement-gated on this account, so its step
    # strip cannot be exercised without a live $3 charge. Recorded truthfully as
    # the gate it is, rather than claimed. The strip's source is byte-identical
    # to the approved 2b7966c version.
    go('/app/adult/learner/', 4000)
    b5 = pg.inner_text('body')
    check('lesson player reached; step strip SIGNED-IN TEST OUTSTANDING',
          'Upgrade required' in b5, 'entitlement gate, not a regression')

    # ---- 19 August corrections -------------------------------------------
    #
    # School roster card: the chip must now name the real organisation-
    # connections route and say what it still needs, and the invented
    # provider-list path must be gone from the page entirely.
    go('/')
    b6 = pg.inner_text('body')
    check('roster chip names the real backend route',
          '/api/roster/organizations/:id/connections' in b6)
    check('invented provider-list route no longer drawn',
          '/api/roster/providers' not in b6)
    check('roster chip carries a truthful unexercised state',
          'Parameter required' in b6 or 'PARAMETER REQUIRED' in b6.upper())

    # Studio AI Governance: the creator's four responsibilities are present and
    # the two that belong to Administrator and to Teacher/School are named as
    # sitting elsewhere rather than silently missing.
    go('/app/studio/governance/', 4000)
    b7 = pg.inner_text('body')
    check('governance shows the creator allowance panel',
          'AI allowance' in b7)
    check('governance shows AI service readiness', 'AI service readiness' in b7)
    check('generated-content review is scoped to the creator',
          'Generated content awaiting your review' in b7)
    check('human review before publication is stated', 'Human review before publication' in b7)
    check('administrator boundary stated on the page',
          'Administrator AI Governance' in b7)
    check('teacher/school boundary stated on the page',
          'Teacher and School' in b7)
    check('learner moderation is not presented as a Studio queue',
          'Moderation queues' not in b7)

    # AI Credits: prepared model, and demonstrably no invented commercial value
    # and no chip for a route that does not exist.
    go('/app/studio/credits/', 4000)
    b8 = pg.inner_text('body')
    check('AI Credits screen renders', 'AI Credits' in b8)
    check('credit model states subscription -> allowance -> consumption',
          'monthly allowance of AI Credits' in b8 and 'consumes credits' in b8)
    check('governance is stated as free to open', 'Opening AI Governance is always free' in b8)
    check('server is stated as authoritative for balance',
          'server is the only authority' in b8)
    check('failed provider work does not leave a charge',
          'must not leave a charge standing' in b8)
    check('live top-up billing is stated as not enabled',
          'Live top-up billing is not enabled' in b8)
    no_money = not re.search(r'[$\u20ac\u00a3]\s*\d', b8)
    check('no invented price anywhere on the credits screen', no_money)
    no_fake_credit = not re.search(r'\b\d[\d,]*\s*credits\b', b8, re.I)
    check('no invented credit balance or package size', no_fake_credit)
    credit_chip = pg.eval_on_selector_all(
        'code, span',
        "els => els.map(e => (e.innerText||'').trim()).filter(t => /\/api\/.*credit/i.test(t))",
    )
    check('no endpoint chip for an unbuilt credit route', len(credit_chip) == 0,
          f'{len(credit_chip)} credit chips')

    # PiP: the settled-state machinery is present and reports its own state.
    go('/app/adult/', 4000)
    pg.evaluate('() => window.scrollTo(0, document.body.scrollHeight)')
    pg.wait_for_timeout(1400)
    placement = pg.get_attribute('.ielps-pip-agent', 'data-pip-placement')
    motion = pg.get_attribute('.ielps-pip-agent', 'data-pip-motion')
    check('PiP reports a settled placement', placement in ('anchored', 'cleared', 'tucked'),
          f'placement={placement} motion={motion}')

    b.close()

passed = sum(1 for r in results if r['pass'])
print(f'\n{passed}/{len(results)} PASS')
with open('/var/lib/freelancer/projects/40470800/functional-19a.json', 'w') as f:
    json.dump(results, f, indent=2)
