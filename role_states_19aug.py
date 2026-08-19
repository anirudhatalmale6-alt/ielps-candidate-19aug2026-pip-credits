"""Role-state behaviour and browser network evidence, 19 August 2026.

Two separate things are recorded here.

First, the network evidence: every /api request the candidate actually makes as
each surface loads, with the status the live backend returned. This is the
answer to "does the visible chip correspond to the endpoint the feature uses" —
taken from the browser rather than from the source.

Second, the role states. The account this runs under is signed out, so the real
backend answers 401 and the surfaces render the authentication state. That
proves the signed-out branch and nothing more, and it is reported as exactly
that. The role branches that cannot be reached without credentials are
exercised against the same classifier by driving the response status directly,
so the mapping from status to what a learner is shown is verified rather than
asserted: 401 -> sign in, 402 -> entitlement, 403 with an administrator message
-> "An administrator role is required", any other 403 -> permission.
"""
import json
from playwright.sync_api import sync_playwright

BASE = 'http://127.0.0.1:4880'

PAGES = [
    ('Access Panel home', '/'),
    ('Adult dashboard', '/app/adult/dashboard/'),
    ('Parent dashboard', '/app/parents/dashboard/'),
    ('School roster', '/app/schools/roster/'),
    ('School admin overview', '/app/schools/dashboard/'),
    ('Studio AI governance', '/app/studio/governance/'),
    ('Studio AI Credits', '/app/studio/credits/'),
]

# status, body message, what the learner must be shown
ROLE_CASES = [
    (401, '{"error":"unauthorized"}', 'Sign in to load this account data.'),
    (402, '{"error":"payment required"}', 'An active lesson or subscription entitlement is required.'),
    (403, '{"error":"administrator role required"}', 'An administrator role is required to view these records.'),
    (403, '{"error":"forbidden"}', 'This account does not have permission to view these records.'),
]

network = []
roles = []

with sync_playwright() as pw:
    b = pw.chromium.launch()

    # ---- network evidence, against the real backend ----------------------
    for label, path in PAGES:
        pg = b.new_page(viewport={'width': 1280, 'height': 900})
        seen = []
        pg.on('response', lambda r: seen.append((r.request.method, r.url, r.status))
              if '/api/' in r.url else None)
        pg.goto(BASE + path, wait_until='domcontentloaded', timeout=45000)
        pg.wait_for_timeout(4000)
        calls = sorted({(m, u.split(BASE)[-1].split('?')[0], s) for m, u, s in seen})
        network.append({'page': label, 'path': path,
                        'calls': [{'method': m, 'path': u, 'status': s} for m, u, s in calls]})
        print(f'{label:24} {len(calls)} api calls  ' +
              ', '.join(f'{s}' for _, _, s in calls[:8]))
        pg.close()

    # ---- role states, by driving the status the classifier receives -------
    def stub(status, body):
        # A one-argument handler: Playwright passes the Request as a second
        # positional when the handler will take one, which is not what is wanted.
        def handler(route):
            route.fulfill(status=status, content_type='application/json', body=body)
        return handler

    for status, body, expected in ROLE_CASES:
        pg = b.new_page(viewport={'width': 1280, 'height': 900})
        pg.route('**/api/**', stub(status, body))
        pg.goto(BASE + '/app/studio/governance/', wait_until='domcontentloaded', timeout=45000)
        pg.wait_for_timeout(3500)
        text = pg.inner_text('body')
        ok = expected in text
        roles.append({'status': status, 'body': body, 'expected': expected, 'shown': ok})
        print(f'{"PASS" if ok else "FAIL"}  HTTP {status} {body[:34]:36} -> {expected}')
        pg.close()

    b.close()

json.dump({'network': network, 'role_states': roles},
          open('/var/lib/freelancer/projects/40470800/role-network-19aug.json', 'w'), indent=2)
print(f'\nrole-state mappings verified: {sum(1 for r in roles if r["shown"])}/{len(roles)}')
